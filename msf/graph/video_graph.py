"""MSF LangGraph StateGraph Orchestrator (v3.0).

Provides a structured, state-driven multi-agent workflow for generating
remotion-based videos with fail-closed QA and self-correction repair loop.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from msf.spec import Scene, build_spec, frames_for, validate_spec, FPS, WIDTH, HEIGHT
from msf.orchestrators.remotion_runner import (
    _split_into_scenes,
    _synthesize_cloned_audio,
    render_remotion_video,
)
from msf.engines.audio.mastering import master_video_audio

REPO_ROOT = Path(__file__).resolve().parents[2]
REMOTION_DIR = REPO_ROOT / "remotion"
PUBLIC_DIR = REMOTION_DIR / "public"
DEFAULT_OUTPUT = REPO_ROOT / "output" / "remotion"

# Presets a low-capability agent may request. Must stay in sync with
# SAFE_PRESETS in remotion/src/VideoSpec.schema.ts.
def _read_registry_presets() -> set:
    """Preset names the TypeScript registry actually ships.

    WHY THIS IS PARSED FROM SOURCE INSTEAD OF LISTED HERE
    -----------------------------------------------------
    This used to be a hand-written set of 11 names. The library grew to 26 and
    nobody updated it, so `node_gate_check` silently rewrote 15 perfectly valid
    presets — TgChat, DonutFill, PhoneMockup, every media scene — to
    HeroKinetic for any agent at level <= 2. The low-level agents that depend on
    presets most were the ones locked out of over half the library, which is the
    exact opposite of the intent: the gate exists to stop weak agents writing
    untested React, NOT to stop them USING finished scenes.

    Reading the registry files makes the allow-list self-maintaining: a new pack
    is available to level-1 agents the moment it is registered, with no second
    list to forget. Parsed with a regex rather than executed because this is
    Python and the registry is TypeScript.

    Only files that `presets.ts` actually merges are read. Globbing the whole
    directory pulled in effects_*.ts and transitions.ts too, which share the
    same entry shape, and produced 134 "presets" — Bloom and CrossFade among
    them. That would let a level-1 agent name an effect as a scene and get an
    error card.
    """
    import re
    from pathlib import Path

    registry_dir = Path(__file__).resolve().parents[2] / "remotion" / "src" / "registry"
    index = registry_dir / "presets.ts"
    if not index.is_file():
        return set()

    try:
        index_text = index.read_text(encoding="utf-8")
    except OSError:
        return set()

    # Which modules does presets.ts import its registries from?
    modules = re.findall(r"^import\s*\{[^}]*\}\s*from\s*'\./([A-Za-z0-9_]+)'", index_text, re.M)

    names: set = set()
    # Registry entries look like `  PresetName: {` followed by `component:`.
    entry = re.compile(r"^\s{2}([A-Z][A-Za-z0-9_]*):\s*\{", re.M)
    for module in modules:
        if module == "types":
            continue
        path = registry_dir / f"{module}.ts"
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in entry.finditer(text):
            block = text[match.end() : match.end() + 400]
            if "component:" in block:
                names.add(match.group(1))
    return names


# Presets a level<=2 agent may name. Derived from the registry, with a small
# hardcoded fallback so a packaging problem degrades to "typography works"
# instead of rewriting every scene to HeroKinetic.
_FALLBACK_PRESETS = {
    "HeroKinetic",
    "StatCounter",
    "GridGridFloor",
    "SwipePanels",
    "TypewriterSub",
    "CompareSplit",
    "FlowDiagram",
    "CodeReveal",
    "QuoteCard",
    "TokenCloud3D",
    "LayerStack3D",
}

ALLOWED_PRESETS = _read_registry_presets() or set(_FALLBACK_PRESETS)


class VideoState(TypedDict, total=False):
    text: str
    storyboard: Optional[List[Dict[str, Any]]]
    preset: str
    accent: Optional[str]
    reference_audio: Optional[str]
    voice: Optional[str]
    video_format: Optional[str]
    theme: Optional[str]
    agent_level: Optional[int]
    output_path: Optional[str]
    scenes: Optional[List[Dict[str, Any]]]
    audio_paths: Optional[List[str]]
    spec_path: Optional[str]
    spec_dict: Optional[Dict[str, Any]]
    raw_mp4: Optional[str]
    final_mp4: Optional[str]
    retry_count: int
    qa_passed: bool
    qa_report: Optional[Dict[str, Any]]
    error: Optional[str]
    # ---- soundtrack (voice + music bed + SFX, mixed and ducked)
    music: Optional[bool]
    music_bed: Optional[str]
    sfx: Optional[bool]
    sfx_names: Optional[List[str]]
    soundtrack_path: Optional[str]
    soundtrack_report: Optional[Dict[str, Any]]
    # ---- deep research (fail-closed; opt-in via `research` or `research_query`)
    # ---- LLM script generation
    use_llm_script: Optional[bool]  # True (default) → ScriptAgent via LLM; False → mechanical split
    topic: Optional[str]            # topic for ScriptAgent when text is a raw topic, not full narration
    style: Optional[str]            # style hint for ScriptAgent ("modern_tech", "funny", etc.)
    duration_range: Optional[List[int]]  # [min_sec, max_sec] for ScriptAgent
    research: Optional[bool]
    research_query: Optional[str]
    research_detailed: Optional[bool]
    research_iters: Optional[int]
    research_qpi: Optional[int]
    research_results: Optional[int]
    research_min_sources: Optional[int]
    research_timeout: Optional[float]
    research_scenes: Optional[int]
    research_facts: Optional[Dict[str, Any]]
    # Short operator-authored editorial directions for supported nodes. They are
    # surfaced in the local dashboard and never replace system safety rules.
    operator_overrides: Optional[Dict[str, str]]
    research_summary: Optional[str]
    research_sources: Optional[List[str]]
    # Run-scoped typed resource views. They contain public URLs/relative Remotion
    # paths only; internal project storage paths never enter LangGraph state.
    project_id: Optional[str]
    project_media: Optional[List[Dict[str, Any]]]
    pinned_sources: Optional[List[Dict[str, Any]]]
    media_assignments: Optional[List[Dict[str, Any]]]


def node_gate_check(state: VideoState) -> VideoState:
    """Check agent level and validate allowed capabilities.

    Guards BOTH places a preset can be named: the top-level `preset` and every
    scene inside a `storyboard`. Checking only the top-level field was a hole —
    a level-1 agent that passed a storyboard could name any preset at all,
    including a custom one that does not exist, and the gate reported nothing.
    Since storyboards are the recommended way to drive data presets, the hole
    covered the common path rather than an edge case.
    """
    level = state.get("agent_level", 1)
    preset = state.get("preset", "HeroKinetic")

    state["retry_count"] = state.get("retry_count", 0)

    if level > 2:
        return state

    rejected: List[str] = []

    if preset not in ALLOWED_PRESETS:
        rejected.append(preset)
        state["preset"] = "HeroKinetic"

    storyboard = state.get("storyboard")
    if storyboard:
        patched = []
        for scene in storyboard:
            scene = dict(scene)
            scene_preset = scene.get("preset")
            if scene_preset and scene_preset not in ALLOWED_PRESETS:
                rejected.append(scene_preset)
                # Drop the key rather than forcing HeroKinetic: the rotation in
                # node_script_split then picks a real, varied preset instead of
                # turning the whole video into one repeated title card.
                scene.pop("preset", None)
            patched.append(scene)
        state["storyboard"] = patched

    if rejected:
        state["error"] = (
            f"Agent level={level} attempted unsupported preset(s) "
            f"({', '.join(sorted(set(rejected)))}). "
            f"Allowed: {len(ALLOWED_PRESETS)} registered presets."
        )

    return state


def node_deep_research(state: VideoState) -> VideoState:
    """Gather real, cited facts before any script exists. FAIL-CLOSED.

    OPT-IN: does nothing unless `research` is truthy or `research_query` is set.
    Once enabled it can only succeed or raise — there is no degraded mode, and
    that is the entire design.

    WHY FAIL-CLOSED MATTERS HERE SPECIFICALLY
    -----------------------------------------
    This graph makes videos about fast-moving subjects (model releases,
    benchmarks, prices). A model answering from memory does not say "I am not
    sure" — it invents a plausible model name and a plausible benchmark score,
    and the pipeline renders them as confident on-screen statistics. A silent
    zero-source research run is therefore WORSE than a crash: the crash costs
    minutes, the invented fact ships.

    `msf.skills_bridge.deep_research` raises unless it can prove real sources
    were fetched. This node adds nothing to that contract; it just refuses to
    catch it.
    """
    if not (state.get("research") or state.get("research_query")):
        return state

    query = state.get("research_query") or state.get("text") or ""
    research_direction = (state.get("operator_overrides") or {}).get("deep_research", "").strip()
    if research_direction:
        query = f"{query}\n\nРедакторский фокус: {research_direction}"
    if not query.strip():
        raise ValueError(
            "research was requested but there is no `research_query` and no `text` "
            "to derive one from."
        )

    # When the operator pins sources, switch to the native evidence-first Studio
    # workflow. Required URLs are extracted before open-web candidates and fail
    # closed when unavailable; the validated storyboard then becomes graph input.
    pinned_payload = state.get("pinned_sources") or []
    if pinned_payload:
        from msf.studio.contracts import PinnedResearchSource, ResearchToScriptRequest
        from msf.studio.research_to_script import ResearchToScriptWorkflow

        request = ResearchToScriptRequest(
            topic=query[:400],
            project_id=state.get("project_id") or "default",
            style_family=state.get("style") or "llm_hubs_neon",
            pinned_sources=[PinnedResearchSource.model_validate(item) for item in pinned_payload],
        )
        result = ResearchToScriptWorkflow().run(request)
        state["storyboard"] = [scene.model_dump(mode="json") for scene in result.storyboard.scenes]
        state["text"] = " ".join(scene.text for scene in result.storyboard.scenes)
        state["research_summary"] = result.research.summary
        state["research_sources"] = [source.url for source in result.research.sources]
        state["research_facts"] = {
            "facts": [claim.statement for claim in result.research.claims],
            "key_points": [result.script.hook, result.script.takeaway],
            "statistics": [],
        }
        print(f"[research] native evidence-first workflow: {len(result.research.sources)} sources, "
              f"{len(request.pinned_sources)} pinned, {len(result.storyboard.scenes)} scenes")
        return state

    from msf.skills_bridge.deep_research import research as run_research
    facts = run_research(
        query,
        detailed=bool(state.get("research_detailed")),
        iters=int(state.get("research_iters") or 2),
        qpi=int(state.get("research_qpi") or 3),
        results=int(state.get("research_results") or 8),
        min_sources=int(state.get("research_min_sources") or 1),
        timeout=float(state.get("research_timeout") or 1800.0),
    )

    state["research_facts"] = facts.to_dict()
    state["research_summary"] = facts.summary
    state["research_sources"] = facts.urls()

    # A storyboard supplied by the caller is authoritative — research then serves
    # as verification material for whoever wrote it, not as a rewrite mandate.
    if state.get("storyboard"):
        print(f"[research] storyboard supplied; keeping it. "
              f"{facts.source_count} sources attached for verification.")
        return state

    state["text"] = _script_from_facts(facts, state)
    return state


def _script_from_facts(facts: Any, state: VideoState) -> str:
    """Turn a cited research summary into narration.

    Grounding rule in the prompt is deliberately blunt: the summary is the ONLY
    permitted source of numbers and names. The point of the research step is
    defeated if the script-writing model tops up the facts from memory, which is
    exactly what a softer instruction invites.
    """
    from msf.agents.llm_client import LLMClient
    from msf.config import MSFConfig

    n_scenes = int(state.get("research_scenes") or 5)
    cfg = MSFConfig()
    llm = LLMClient(cfg.llm)

    system = (
        "Ты сценарист коротких вертикальных видео (Shorts/Reels). "
        "Пиши по-русски, живо и без канцелярита."
    )
    script_direction = (state.get("operator_overrides") or {}).get("script_split", "").strip()
    direction_block = f"\nРЕДАКТОРСКОЕ НАПРАВЛЕНИЕ: {script_direction}\n" if script_direction else ""
    user = (
        f"Ниже — результат исследования с источниками. Напиши закадровый текст "
        f"для видео из {n_scenes} сцен.\n\n"
        "ЖЁСТКИЕ ПРАВИЛА:\n"
        "1. Все факты, цифры, названия и версии бери ТОЛЬКО из исследования ниже. "
        "Ничего не добавляй по памяти. Если чего-то нет в тексте — не упоминай.\n"
        "2. Одна сцена — одно предложение, 8-16 слов, произносимое вслух.\n"
        f"3. Ровно {n_scenes} предложений, каждое с новой строки, без нумерации "
        "и без markdown.\n"
        "4. Первое предложение — цепляющее, последнее — вывод.\n\n"
        f"ИССЛЕДОВАНИЕ:\n{facts.summary[:6000]}\n"
        f"{direction_block}"
    )

    text = llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.6,
    ).strip()

    lines = [
        ln.strip(" -•*\t")
        for ln in text.splitlines()
        if ln.strip(" -•*\t")
    ]
    if not lines:
        raise RuntimeError(
            "the script model returned nothing usable from a successful research run."
        )

    print(f"[research] script: {len(lines)} lines from {facts.source_count} sources")
    return " ".join(lines)


def _apply_project_media(scenes: List[Dict[str, Any]], state: VideoState) -> List[Dict[str, Any]]:
    """Assign registered media to compatible renderer presets by explicit role.

    This is deterministic placement, not a free-form model file-system tool. Every
    ``src`` was materialized by the worker into this run's Remotion public tree.
    Unsupported kinds remain available as research/context resources but are not
    silently faked as a visual scene.
    """
    assets = state.get("project_media") or []
    visual_assets = [item for item in assets if item.get("kind") in {"image", "video"} and item.get("src")]
    if not scenes or not visual_assets:
        state["media_assignments"] = []
        return scenes
    mapping = {
        "screen_recording": "ScreenGuide",
        "video_insert": "VideoEmbed",
        "telegram_round": "TelegramVoiceRound",
        "hero_image": "ImageSpotlight",
        "supporting_image": "ImageSpotlight",
        "channel_avatar": "ImageSpotlight",
    }
    assignments: List[Dict[str, Any]] = []
    # Keep the first hook readable. Assets enter body scenes first, then continue
    # cyclically only if the project contains more media than body beats.
    start = 1 if len(scenes) > 1 else 0
    for offset, asset in enumerate(visual_assets):
        index = (start + offset) % len(scenes)
        scene = scenes[index]
        if scene.get("src") or scene.get("images"):
            continue
        role = str(asset.get("role") or "supporting_image")
        preset = mapping.get(role, "ImageSpotlight")
        src = str(asset["src"])
        scene.update({
            "preset": preset,
            "src": src,
            "images": [src] if asset.get("kind") == "image" else None,
            "title": scene.get("title") or str(asset.get("caption") or "Материал проекта")[:120],
        })
        if preset == "ScreenGuide":
            scene.setdefault("guide_text", str(asset.get("caption") or "Смотрите на ключевой шаг"))
            scene.setdefault("show_rec", asset.get("kind") == "video")
        if preset == "VideoEmbed":
            scene.setdefault("muted", True)
            scene.setdefault("show_controls", True)
        if preset == "TelegramVoiceRound":
            scene.setdefault("contact_name", "Сообщение")
        assignments.append({"asset_id": asset.get("asset_id"), "scene_index": index, "preset": preset, "role": role})
    state["media_assignments"] = assignments
    if assignments:
        print(f"[media] assigned {len(assignments)} project asset(s) to compatible scenes")
    return scenes


def _storyboard_scene_to_graph(scene: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten validated StoryboardScene props for the renderer Scene contract."""
    row = dict(scene)
    props = row.pop("props", {})
    if isinstance(props, dict):
        for key, value in props.items():
            row.setdefault(key, value)
    row.pop("scene_id", None)
    row.pop("effects", None)
    row.pop("style_kit", None)
    row.pop("audio", None)
    row.pop("evidence_claim_ids", None)
    return row


def node_script_split(state: VideoState) -> VideoState:
    """Generate or split narration into scenes.

    Priority order:
      1. ``storyboard`` — hand-authored scene list (data presets, custom layouts).
      2. ``use_llm_script=True`` (default) — call ScriptAgent via LLM to write a
         structured viral script with hook → narrative arc → CTA.
      3. ``use_llm_script=False`` — mechanical split by sentence boundaries
         (legacy fallback, useful when the caller provides finished narration).
    """
    # ── 1. Hand-authored storyboard wins ─────────────────────────────────
    storyboard = state.get("storyboard")
    if storyboard:
        scenes = [_storyboard_scene_to_graph(sc) for sc in storyboard]
        for i, sc in enumerate(scenes):
            if not sc.get("text"):
                raise ValueError(
                    f"storyboard[{i}] has no 'text' — every scene needs narration to voice."
                )
        state["scenes"] = _apply_project_media(scenes, state)
        return state

    # ── 2. LLM-powered script generation (default) ───────────────────────
    use_llm = state.get("use_llm_script", True)
    text = state.get("text", "")

    if use_llm:
        try:
            from msf.agents.script_agent import ScriptAgent
            from msf.agents.llm_client import LLMClient
            from msf.config import MSFConfig, LLMConfig
            from msf.contracts.models import ProjectBrief, ResearchResult

            cfg = MSFConfig()
            llm_cfg = cfg.llm if hasattr(cfg, "llm") and cfg.llm else LLMConfig(
                base_url="http://localhost:20128/v1",
                model="antigravity/gemini-2.5-flash",
                api_key="not-needed",
                temperature=0.7,
                max_tokens=2048,
            )
            llm = LLMClient(config=llm_cfg)
            agent = ScriptAgent(config=cfg, llm=llm)

            # Build brief from state
            topic = state.get("topic") or text or "General"
            script_direction = (state.get("operator_overrides") or {}).get("script_split", "").strip()
            if script_direction:
                topic = f"{topic}\nРедакторское направление: {script_direction}"
            style = state.get("style", "modern_tech")
            dur_range = state.get("duration_range") or [30, 60]

            brief = ProjectBrief(
                topic=topic,
                style=style,
                duration_range=tuple(dur_range),
            )

            # Use research results if available from deep_research node
            research = ResearchResult(
                facts=list((state.get("research_facts") or {}).get("facts", [])),
                key_points=list((state.get("research_facts") or {}).get("key_points", [])),
                statistics=list((state.get("research_facts") or {}).get("statistics", [])),
                sources=state.get("research_sources") or [],
            )

            script = agent.execute({"brief": brief, "research": research})

            # Validate and warn (non-blocking — we still use the script)
            review = agent.validate(script)
            if review.issues:
                print(f"[script] ⚠ validation issues ({len(review.issues)}):")
                for issue in review.issues:
                    print(f"  - {issue}")

            # Convert Script → scenes list for downstream nodes
            scenes = []
            # Hook is always the first scene
            if script.hook and script.hook.strip():
                scenes.append({"text": script.hook.strip()})

            for scene_text in (script.scenes_text or []):
                if scene_text and scene_text.strip():
                    scenes.append({"text": scene_text.strip()})

            # CTA is always the last scene
            if script.cta and script.cta.strip():
                scenes.append({"text": script.cta.strip()})

            if not scenes:
                print("[script] LLM returned empty script — falling back to mechanical split")
                state["scenes"] = _split_into_scenes(text)
            else:
                state["scenes"] = _apply_project_media(scenes, state)
                print(f"[script] LLM script: {len(scenes)} scenes "
                      f"(hook + {len(script.scenes_text or [])} body + CTA), "
                      f"~{script.total_duration:.0f}s")

            return state

        except Exception as e:
            print(f"[script] LLM script generation failed: {e}")
            print("[script] falling back to mechanical split")

    # ── 3. Mechanical fallback ───────────────────────────────────────────
    state["scenes"] = _apply_project_media(_split_into_scenes(text), state)
    return state


# Rotating presets for multi-scene videos.
#
# BOTH LISTS COME FROM THE REGISTRY NOW
# -------------------------------------
# These were hand-written and had drifted badly. Measured against
# remotion/src/registry at the time of the fix:
#
#   _TEXT_SAFE_PRESETS held 5 names; the registry marks 13 as rotation-safe.
#   ScoreHud, SubscribeCTA, MusicPlayer, VinylRecord, VoiceMemo, BankCard,
#   CountdownHero and ModelOrbit3D could therefore NEVER appear in a generated
#   video — every narration-only render cycled the same five typography cards.
#
#   _DATA_DRIVEN_PRESETS held 11 of the registry's 25. The 14 it omitted
#   (Leaderboard, QuizCard, TimelineReveal, PostCard, CommentWall, ...) were
#   eligible for blind rotation, which hands a data preset a scene carrying only
#   narration and renders its ⚠ placeholder.
#
# msf/registry.py parses the same TypeScript the renderer imports, so neither
# list can drift again. See tests/test_registry_parity.py.
#
# ROTATION IS FILTERED FURTHER THAN "rotation_safe"
# -------------------------------------------------
# `rotation_safe` only means "not data-driven" — it does NOT mean the preset shows
# the narration. Rendering all 13 and reading the frames showed three groups:
#
#   uses title AND text   QuoteCard, TypewriterSub
#   uses title only       HeroKinetic, GridGridFloor, TokenCloud3D, MusicPlayer,
#                         VinylRecord, VoiceMemo, ModelOrbit3D
#   ignores both, shows   CountdownHero ("СТАРТ"), ScoreHud (PLAYER 1 / 9750),
#   its own demo data     SubscribeCTA (TechChannel / 142.0K), BankCard (VISA
#                         4242 / ALEXEY NIKITIN)
#
# The third group is why "rotation-safe" is not the right filter on its own: those
# four render believable but FICTIONAL content — a fake cardholder name, an
# invented subscriber count — with no relation to the script. Rotating them in
# would put invented facts on screen, which is exactly what node_deep_research
# exists to prevent. They stay available when a caller names them explicitly with
# data; they are not substituted automatically.
_ROTATION_BLOCKLIST = frozenset({
    "CountdownHero",   # renders "СТАРТ", ignores title and text
    "ScoreHud",        # PLAYER 1 / СЧЁТ 9750 / КОМБО x3 — invented game stats
    "SubscribeCTA",    # TechChannel / 142.0K подписчиков — invented channel
    "BankCard",        # VISA ···· 4242 / ALEXEY NIKITIN — invented cardholder
    "ModelOrbit3D",    # needs modelUrl; without an asset there is nothing to orbit
})


def _text_safe_presets() -> List[str]:
    """Presets rotation may substitute into a narration-only scene."""
    from msf import registry

    safe = [p for p in registry.rotation_safe_presets() if p not in _ROTATION_BLOCKLIST]
    # An empty registry means the parse failed. Falling back to a short hardcoded
    # list is what produced the original bug, so prefer a loud, obviously-degraded
    # single preset over silently shrinking the library again.
    return safe or ["HeroKinetic"]


def _data_driven_presets() -> frozenset:
    from msf import registry

    return registry.data_driven_presets() or frozenset({"StatCounter", "TgChat"})


# Kept as module-level names because callers and tests import them. Computed once
# at import; the registry is a file on disk that does not change mid-run.
_TEXT_SAFE_PRESETS = _text_safe_presets()
_DATA_DRIVEN_PRESETS = _data_driven_presets()


ACCENT_NAMES = {
    "gold": "#E6C475",
    "neon": "#00FF88",
    "cyan": "#00D4FF",
}


def _resolve_accent(requested: Optional[str]) -> str:
    """Turn a documented accent name into hex; pass a raw #RRGGBB through.

    Callers are told they may pass "gold" | "neon" | "cyan". Only "gold" used to
    be special-cased, so accent="neon" reached the renderer as the literal string
    "neon" — an invalid CSS colour that the browser drops, leaving each scene on
    its own default instead of the requested palette. Failure was silent: the spec
    validated and the render exited 0.
    """
    if not requested:
        return ACCENT_NAMES["gold"]
    return ACCENT_NAMES.get(requested, requested)


def _scene_kwargs(
    scene: Dict[str, Any],
    accent_color: str,
    index: int,
    default_preset: str = "HeroKinetic",
) -> Dict[str, Any]:
    """Map one incoming scene dict onto Scene(**kwargs).

    Accepts BOTH spellings for every field. Scenes arrive in the wire format the
    presets and docs use (camelCase: statValue, pointCount) while the dataclass is
    snake_case, so a plain `k in scene_fields` filter silently dropped camelCase
    keys: a scene carrying statValue produced a StatCounter with no number, and
    validate_spec then blamed the caller for a key they had in fact supplied.

    Shared by build_spec and repair — repair rebuilds scenes from the same dicts,
    so without this it would drop the very fields QA is trying to preserve.
    """
    wire_to_snake = {v: k for k, v in Scene._CAMEL.items()}
    scene_fields = {f.name for f in dataclasses.fields(Scene)}

    normalised: Dict[str, Any] = {}
    for key, value in scene.items():
        normalised[wire_to_snake.get(key, key)] = value

    kwargs = {k: v for k, v in normalised.items() if k in scene_fields and v is not None}
    kwargs.update(
        id=scene.get("id", f"scene-{index+1}"),
        duration_in_frames=normalised.get("duration_in_frames", 90),
        preset=normalised.get("preset", default_preset),
        accent_color=normalised.get("accent_color") or accent_color,
        # A scene may carry its own voice-over file (node_voice_synthesis writes
        # one per scene, and a hand-authored storyboard can name an existing wav).
        # This used to be an unconditional f-string, which silently overwrote any
        # supplied path: the only reachable audio was scene_NN.wav, and a spec
        # pointing at its own asset rendered against the wrong track — or against
        # a file that did not exist, which Remotion turns into pure silence.
        audio_url=normalised.get("audio_url") or f"scene_{index:02d}.wav",
    )
    return kwargs


def _rotated_preset(base: str, index: int) -> str:
    """Vary the visual template across scenes so a long short isn't one static card.

    The requested preset always leads scene 0; later scenes cycle through the
    text-safe presets (which accept plain narration) to keep the video moving.

    A data-driven base (StatCounter, TgChat, ...) is never rotated away from:
    the caller supplied the data for it, and swapping it for a typography card
    would silently drop that data from the video.
    """
    if base in _DATA_DRIVEN_PRESETS:
        return base
    if base in _TEXT_SAFE_PRESETS:
        cycle = [base] + [p for p in _TEXT_SAFE_PRESETS if p != base]
        return cycle[index % len(cycle)]
    return base


def node_voice_synthesis(state: VideoState) -> VideoState:
    """Synthesize voice cloning for all scenes using Qwen3 1.7B-Base.

    Voice selection goes through the registry (`voice` key or wav path) so the
    transcript travels with the audio and ICL prosody transfer stays on. An
    explicit `reference_audio` path still wins for one-off overrides.
    """
    from msf.skills_bridge.qwen3_tts import describe_reference, resolve_voice

    override = state.get("reference_audio")
    ref_audio, ref_text = resolve_voice(override or state.get("voice"))
    ref_info = describe_reference(override or state.get("voice"))
    print(f"[voice] {ref_info['mode']} ref={Path(ref_audio).name} "
          f"dur={ref_info['duration_sec']}s sr={ref_info['sample_rate']}")
    if ref_text is None:
        print("[voice] WARNING: no transcript for this reference — "
              "falling back to x-vector timbre copy without prosody transfer.")

    scenes = state.get("scenes", [])
    audio_paths = []

    output_dir = (
        Path(state["output_path"]).parent
        if state.get("output_path")
        else DEFAULT_OUTPUT
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    base_preset = state.get("preset", "HeroKinetic")

    for i, sc in enumerate(scenes):
        wav_path, dur = _synthesize_cloned_audio(sc["text"], ref_audio, ref_text)
        scene_wav_name = f"scene_{i:02d}.wav"
        dst_wav = audio_dir / scene_wav_name
        shutil.copy(wav_path, str(dst_wav))

        # Copy into Remotion public directory
        pub_wav = PUBLIC_DIR / scene_wav_name
        shutil.copy(str(dst_wav), str(pub_wav))

        audio_paths.append(str(dst_wav))
        sc["duration_in_frames"] = frames_for(dur, FPS)
        # MUST be `audio_url`: that is the Scene dataclass field name, and
        # _scene_kwargs normalises wire keys onto dataclass fields. Writing
        # `audio_file` here left the key unread by anything — the render only
        # worked because _scene_kwargs happened to rebuild the same filename
        # from the index. Any change to the naming scheme silently desynced
        # the two and produced a spec pointing at a nonexistent wav.
        sc["audio_url"] = scene_wav_name
        # A storyboard scene names its own preset; only auto-rotate when it didn't.
        if not sc.get("preset"):
            sc["preset"] = _rotated_preset(base_preset, i)
        sc["accent"] = state.get("accent", "gold")

    state["audio_paths"] = audio_paths
    return state


def node_soundtrack(state: VideoState) -> VideoState:
    """Mix the per-scene voice clips with a music bed and SFX accents.

    WHY THIS NODE EXISTS
    --------------------
    `msf/audio/` ships a ducking mixer, ten music beds and ~70 SFX, and the graph
    imported NONE of it: every video was dry narration over silence. This node is
    the bridge.

    WHY IT REPLACES THE PER-SCENE AUDIO INSTEAD OF ADDING TO IT
    ----------------------------------------------------------
    Mixing cannot be per scene — a bed that restarts on every cut is audibly
    wrong, and the duck envelope needs the whole voice track to know where to dip.
    So the mix is ONE wav for the whole video, mounted as the spec's root
    `audioUrl`, and each scene's `audio_url` is cleared. Leaving both would make
    Remotion mount `<Audio>` twice for the same speech (root + scene), playing it
    against a copy of itself; `validate_spec` rejects that outright.

    Opt out with `music: False` and `sfx: False`, which falls back to the old
    per-scene voice-only behaviour.
    """
    want_music = state.get("music", True)
    want_sfx = state.get("sfx", True)
    if not want_music and not want_sfx:
        print("[audio] music and sfx both disabled — keeping per-scene voice only")
        return state

    scenes = state.get("scenes") or []
    voice_wavs = state.get("audio_paths") or []
    if not scenes or not voice_wavs:
        print("[audio] no scenes or no voice clips — skipping soundtrack")
        return state

    from msf.audio.soundtrack import SOUNDTRACK_NAME, build_soundtrack

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    out_wav = PUBLIC_DIR / SOUNDTRACK_NAME

    report = build_soundtrack(
        scenes=scenes,
        voice_wavs=voice_wavs,
        fps=FPS,
        out_path=out_wav,
        music_bed=state.get("music_bed"),
        sfx_names=state.get("sfx_names"),
        music=bool(want_music),
        sfx=bool(want_sfx),
    )

    # The mix now owns the audio; per-scene clips must not play alongside it.
    for sc in scenes:
        sc.pop("audio_url", None)
        sc.pop("audioUrl", None)

    state["soundtrack_path"] = SOUNDTRACK_NAME
    state["soundtrack_report"] = report

    print(f"[audio] soundtrack {report['duration_sec']}s  "
          f"{report['lufs']} LUFS  peak {report['true_peak_dbfs']} dBFS  "
          f"bed={report['music_bed']}  sfx={len(report['sfx'])}  "
          f"duck={report['duck_depth_db']} dB")
    if report["clipping"]:
        raise RuntimeError(
            "Soundtrack clips (true peak >= 0 dBFS). Refusing to ship distorted "
            "audio; lower sfx_gain_db or the bed level."
        )
    return state


def node_build_remotion_spec(state: VideoState) -> VideoState:
    """Generate VideoSpec via single source of truth msf.spec."""
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    accent_color = _resolve_accent(state.get("accent"))

    # Field mapping (including camelCase → snake_case) lives in _scene_kwargs so
    # this node and the repair node cannot drift apart.
    default_preset = state.get("preset", "HeroKinetic")
    scenes_objs: List[Scene] = [
        Scene(**_scene_kwargs(sc, accent_color, i, default_preset))
        for i, sc in enumerate(state.get("scenes", []))
    ]

    spec_dict = build_spec(
        scenes_objs,
        fps=FPS,
        video_format=state.get("video_format"),
        theme=state.get("theme"),
        # The mixed soundtrack (voice + bed + SFX) is mounted at the ROOT, and
        # node_soundtrack has already cleared the per-scene urls. When the mix is
        # disabled this is None and the per-scene voice clips play as before.
        audio_url=state.get("soundtrack_path"),
    )

    # Fail fast at the graph level too: never persist or render an unusable spec.
    validate_spec(spec_dict)

    state["spec_dict"] = spec_dict

    spec_path = PUBLIC_DIR / "video-spec.json"
    props_path = PUBLIC_DIR / "props.json"
    json_str = json.dumps(spec_dict, ensure_ascii=False, indent=2)
    spec_path.write_text(json_str, encoding="utf-8")
    props_path.write_text(json_str, encoding="utf-8")

    state["spec_path"] = str(spec_path)
    return state


def _resolve_output_paths(state: VideoState) -> tuple[str, str]:
    """Return (raw_mp4, final_mp4) — always DISTINCT paths.

    ffmpeg cannot edit a file in place, so the mastering step must never be handed
    the same path for input and output. The raw render always gets a `.raw.mp4`
    suffix; `output_path` (when supplied) names the FINAL mastered artifact.
    """
    out_param = state.get("output_path")
    preset_name = (state.get("preset") or "HeroKinetic").lower()

    if out_param:
        final_path = Path(out_param)
        out_dir = final_path.parent
    else:
        out_dir = DEFAULT_OUTPUT
        final_path = out_dir / f"msf_{preset_name}.mp4"

    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = final_path.with_suffix(".raw.mp4")
    return str(raw_path), str(final_path)


def node_remotion_render(state: VideoState) -> VideoState:
    """Invoke Remotion render via remotion_runner."""
    raw_mp4, _ = _resolve_output_paths(state)

    render_remotion_video(state["spec_dict"], raw_mp4)
    state["raw_mp4"] = raw_mp4
    return state


def node_master_audio(state: VideoState) -> VideoState:
    """Master output video audio using loudnorm."""
    raw_mp4, final_mp4 = _resolve_output_paths(state)

    if Path(raw_mp4).resolve() == Path(final_mp4).resolve():
        raise RuntimeError(
            f"Refusing to master in place: raw and final paths are identical ({final_mp4})."
        )

    master_video_audio(state.get("raw_mp4") or raw_mp4, final_mp4)
    state["final_mp4"] = final_mp4
    return state


def _check_mp4_size(mp4_path: str) -> tuple[bool, int]:
    p = Path(mp4_path)
    if not p.exists():
        return False, 0
    size = p.stat().st_size
    return size > 100 * 1024, size


def _check_duration(mp4_path: str, expected_sec: float) -> tuple[bool, float]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        mp4_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if res.returncode != 0 or not res.stdout.strip():
        return False, 0.0
    actual_sec = float(res.stdout.strip())
    diff = abs(actual_sec - expected_sec)
    passed = diff <= (0.15 * expected_sec) if expected_sec > 0 else False
    return passed, actual_sec


def _check_volume(mp4_path: str) -> tuple[bool, float]:
    devnull = "NUL" if os.name == "nt" else "/dev/null"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        mp4_path,
        "-af",
        "volumedetect",
        "-vn",
        "-sn",
        "-dn",
        "-f",
        "null",
        devnull,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    match = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", res.stderr)
    if match:
        vol = float(match.group(1))
        return vol > -50.0, vol
    return False, -99.0


def _get_frame_stddev(image_path: str) -> float:
    try:
        from PIL import Image, ImageStat
        with Image.open(image_path) as img:
            gray = img.convert("L").resize((108, 192))
            stat = ImageStat.Stat(gray)
            return float(stat.stddev[0])
    except Exception:
        cmd = ["ffmpeg", "-i", image_path, "-vf", "signalstats", "-f", "null", "-"]
        res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        match = re.search(r"YSTD=([\d.]+)", res.stderr)
        if match:
            return float(match.group(1))
        return 0.0


def _extract_midpoint_frames(
    mp4_path: str, spec_dict: dict, out_dir: Path
) -> tuple[list[str], list[float]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    scenes = spec_dict.get("scenes", [])

    frame_paths = []
    stddevs = []

    cumulative_frames = 0
    for idx, sc in enumerate(scenes):
        dur_frames = sc.get("durationInFrames", 90)
        mid_frame = cumulative_frames + (dur_frames // 2)
        cumulative_frames += dur_frames

        frame_file = out_dir / f"scene_{idx:02d}_mid.png"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            mp4_path,
            "-vf",
            f"select='eq(n\\,{mid_frame})'",
            "-vframes",
            "1",
            str(frame_file),
        ]
        subprocess.run(cmd, capture_output=True, text=True, errors="replace")

        if frame_file.exists():
            frame_paths.append(str(frame_file))
            sd = _get_frame_stddev(str(frame_file))
            stddevs.append(sd)

    return frame_paths, stddevs


def node_qa(state: VideoState) -> VideoState:
    """Fail-closed QA node checking size, duration, audio volume, midpoint frames, and diversity."""
    report: Dict[str, Any] = {}
    try:
        mp4_path = state.get("final_mp4") or state.get("raw_mp4")
        if not mp4_path:
            state["qa_passed"] = False
            state["qa_report"] = {"error": "No output mp4 path found"}
            return state

        # 1. Size check (> 100 KB)
        size_pass, size_bytes = _check_mp4_size(mp4_path)
        report["check_1_size"] = {"pass": size_pass, "bytes": size_bytes}

        # 2. Duration check
        spec_dict = state.get("spec_dict", {})
        fps = spec_dict.get("fps", FPS)
        scenes = spec_dict.get("scenes", [])
        # Transitions overlap, so the video is shorter than the sum. Use the
        # same logic spec.py uses to set durationInFrames, or this check will
        # fail on every video that has crossfades.
        from msf.spec import compute_total_frames
        expected_frames = compute_total_frames(scenes)
        expected_sec = expected_frames / fps
        dur_pass, actual_sec = _check_duration(mp4_path, expected_sec)
        report["check_2_duration"] = {
            "pass": dur_pass,
            "actual_sec": actual_sec,
            "expected_sec": expected_sec,
        }

        # 3. Volume check (> -50 dB)
        vol_pass, mean_vol = _check_volume(mp4_path)
        report["check_3_volume"] = {"pass": vol_pass, "mean_volume_db": mean_vol}

        # 4 & 5. Frame luminance check (stddev >= 3)
        qa_frames_dir = Path(mp4_path).parent / "qa_frames"
        frame_paths, stddevs = _extract_midpoint_frames(mp4_path, spec_dict, qa_frames_dir)
        lum_pass = len(stddevs) > 0 and all(sd >= 3.0 for sd in stddevs)
        report["check_4_5_luminance"] = {
            "pass": lum_pass,
            "stddevs": stddevs,
            "frame_paths": frame_paths,
        }

        # 6. Diversity check if > 1 scene
        if len(frame_paths) > 1:
            hashes = [
                hashlib.md5(Path(p).read_bytes()).hexdigest()
                for p in frame_paths
                if Path(p).exists()
            ]
            div_pass = len(set(hashes)) > 1
        else:
            div_pass = True
        report["check_6_diversity"] = {"pass": div_pass}

        all_passed = size_pass and dur_pass and vol_pass and lum_pass and div_pass
        report["all_passed"] = all_passed
        state["qa_passed"] = all_passed
        state["qa_report"] = report

    except Exception as exc:
        report["all_passed"] = False
        report["exception"] = str(exc)
        state["qa_passed"] = False
        state["qa_report"] = report

    return state


def node_repair(state: VideoState) -> VideoState:
    """Self-correction repair node. Modifies spec/assets based on failure reason."""
    retry_count = state.get("retry_count", 0)
    report = state.get("qa_report") or {}

    if retry_count >= 2:
        raise RuntimeError(
            f"Video QA failed after 2 repairs. Pipeline failed closed.\n"
            f"QA Report: {json.dumps(report, indent=2, ensure_ascii=False)}"
        )

    remotion_public = PUBLIC_DIR
    remotion_public.mkdir(parents=True, exist_ok=True)
    audio_paths = state.get("audio_paths") or []

    # 1. If audio failure: re-copy wavs into remotion/public
    vol_check = report.get("check_3_volume", {})
    if not vol_check.get("pass", True):
        for audio_path in audio_paths:
            if os.path.exists(audio_path):
                shutil.copy(audio_path, remotion_public / Path(audio_path).name)

    # 2. If blank frames or non-diverse: fall back to a preset that can render the
    #    scene's own data. StatCounter/SwipePanels scenes carry structured fields
    #    (statValue/cards) that HeroKinetic cannot show, so only text-driven scenes
    #    are downgraded — otherwise the repair would destroy the storyboard.
    lum_check = report.get("check_4_5_luminance", {})
    div_check = report.get("check_6_diversity", {})
    if not lum_check.get("pass", True) or not div_check.get("pass", True):
        scenes = state.get("scenes") or []
        for sc in scenes:
            if sc.get("stat_value") is not None or sc.get("cards"):
                continue
            sc["preset"] = "HeroKinetic"

    # 3. If duration mismatch: recompute duration from actual wav files
    dur_check = report.get("check_2_duration", {})
    if not dur_check.get("pass", True):
        scenes = state.get("scenes") or []
        for i, sc in enumerate(scenes):
            if i < len(audio_paths) and os.path.exists(audio_paths[i]):
                cmd = [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    audio_paths[i],
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
                if res.returncode == 0 and res.stdout.strip():
                    dur = float(res.stdout.strip())
                    sc["duration_in_frames"] = frames_for(dur, FPS)

    state["retry_count"] = retry_count + 1

    # Rebuild spec_dict with updated scene properties, preserving every field the
    # Scene dataclass knows about (3D layers, code, quote attribution, ...).
    # Uses the same mapper as the build node: this path previously filtered keys
    # without camelCase normalisation, so a QA repair pass would strip the very
    # preset data (statValue, messages, walletBalance) it was meant to keep.
    accent_color = _resolve_accent(state.get("accent"))
    scenes_objs: List[Scene] = [
        Scene(**_scene_kwargs(sc, accent_color, i))
        for i, sc in enumerate(state.get("scenes", []))
    ]

    spec_dict = build_spec(
        scenes_objs,
        fps=FPS,
        video_format=state.get("video_format"),
        theme=state.get("theme"),
        # Repair must preserve the soundtrack too, or a QA retry silently ships
        # the video with no audio at all.
        audio_url=state.get("soundtrack_path"),
    )
    state["spec_dict"] = spec_dict

    props_path = remotion_public / "props.json"
    spec_json_path = remotion_public / "video-spec.json"
    json_str = json.dumps(spec_dict, ensure_ascii=False, indent=2)
    props_path.write_text(json_str, encoding="utf-8")
    spec_json_path.write_text(json_str, encoding="utf-8")

    return state


def check_qa_decision(state: VideoState) -> str:
    """Conditional Edge: proceed to END if QA passed, else retry repair."""
    if state.get("qa_passed") is True:
        return "end"
    return "repair"


def build_msf_graph():
    """Build and compile the MSF LangGraph workflow with Vision QA loop."""
    workflow = StateGraph(VideoState)

    workflow.add_node("gate_check", node_gate_check)
    workflow.add_node("deep_research", node_deep_research)
    workflow.add_node("script_split", node_script_split)
    workflow.add_node("voice_synthesis", node_voice_synthesis)
    workflow.add_node("soundtrack", node_soundtrack)
    workflow.add_node("build_spec", node_build_remotion_spec)
    workflow.add_node("render", node_remotion_render)
    workflow.add_node("master_audio", node_master_audio)
    workflow.add_node("qa", node_qa)
    workflow.add_node("repair", node_repair)

    workflow.set_entry_point("gate_check")
    # Research sits between the gate and the split: it can REPLACE `text`, so it
    # must run before the text is cut into scenes. It is a no-op unless asked for.
    workflow.add_edge("gate_check", "deep_research")
    workflow.add_edge("deep_research", "script_split")
    workflow.add_edge("script_split", "voice_synthesis")
    workflow.add_edge("voice_synthesis", "soundtrack")
    workflow.add_edge("soundtrack", "build_spec")
    workflow.add_edge("build_spec", "render")
    workflow.add_edge("render", "master_audio")
    workflow.add_edge("master_audio", "qa")

    workflow.add_conditional_edges(
        "qa",
        check_qa_decision,
        {
            "repair": "repair",
            "end": END,
        },
    )

    workflow.add_edge("repair", "render")

    return workflow.compile()


if __name__ == "__main__":
    app = build_msf_graph()
    print("✅ LangGraph MSF Workflow (v3.0 with fail-closed QA & Self-Correction) compiled successfully!")
