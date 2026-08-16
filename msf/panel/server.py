"""MSF Control Panel — HTTP API over the pipeline's real registries.

WHY A PANEL EXISTS
------------------
Everything this serves was already in the repo and invisible. The library holds
38 scene presets, 96 effects, 12 transitions, 38 SFX and 12 music beds, and the
only way to know that was to read TypeScript. Which is how the pipeline shipped
for weeks using five presets and a voice nobody chose: nothing showed what was
available or what was actually being used.

So the panel is deliberately a VIEW OVER THE SOURCE, not a second catalogue:
every list comes from msf.registry (which parses the same TS the renderer
imports), msf.audio.sfx/music (the same dicts the mixer renders from) and
assets/voices/voices.json (the same file resolve_voice reads). There is no
duplicated inventory to drift. If the panel shows it, the renderer can render it.

WHAT IT DOES NOT DO
-------------------
No authentication. It binds 127.0.0.1 by default and MUST NOT be exposed: the
preview endpoints run node and ffmpeg subprocesses, and /api/graph/run starts a
full render. Binding this to 0.0.0.0 hands anyone on the network a code-execution
surface. `--host` is accepted for local debugging only and warns loudly.

RUN
---
    python -m msf.panel.server            # http://127.0.0.1:8765
    python -m msf.panel.server --port 9000
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

REPO = Path(__file__).resolve().parents[2]
REMOTION = REPO / "remotion"
PANEL_DIR = Path(__file__).resolve().parent
STATIC_DIR = PANEL_DIR / "static"

# Preview artefacts. Kept out of output/ so a cleanup of renders cannot delete
# the cache and vice versa.
CACHE = REPO / "output" / "_panel_cache"
CACHE.mkdir(parents=True, exist_ok=True)

log = logging.getLogger("msf.panel")

app = FastAPI(title="MSF Control Panel", version="1.0")

# Same-origin in normal use; permissive only for localhost dev tooling.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- catalogue

@app.get("/api/scenes")
def api_scenes() -> Dict[str, Any]:
    """Every scene preset, with the flags that decide whether agents can use it.

    `rotation_safe` and `rotation_used` are DIFFERENT and the distinction is the
    whole point of this view: a preset can be safe for rotation yet still be
    excluded because it renders invented content (ScoreHud's PLAYER 1 / 9750).
    Showing only one flag is what let eight usable presets sit unnoticed.
    """
    from msf import registry
    from msf.graph import video_graph

    used = set(video_graph._TEXT_SAFE_PRESETS)
    blocked = set(getattr(video_graph, "_ROTATION_BLOCKLIST", frozenset()))

    items = []
    for info in sorted(registry.load_registry().values(), key=lambda p: p.name):
        items.append({
            "name": info.name,
            "category": info.category,
            "summary": info.summary,
            "fields": list(info.fields),
            "data_driven": info.data_driven,
            "three": info.three,
            "pack": info.pack,
            "rotation_safe": info.rotation_safe,
            "rotation_used": info.name in used,
            "rotation_blocked": info.name in blocked,
        })
    return {
        "total": len(items),
        "rotation_used": sorted(used),
        "categories": registry.by_category(),
        "items": items,
    }


@app.get("/api/effects")
def api_effects() -> Dict[str, Any]:
    """Effects and transitions, kept apart because they are not interchangeable.

    A transition name in a scene's `effects` list is skipped with a console
    warning — EffectStack only resolves the three effect registries.

    `transitions` USED TO SERVE registry.transition_names(), which is the
    `TRANSITIONS` export in src/registry/effects_scene.ts — and every one of those
    12 names ('CrossFade', 'WipeLinear', ...) is REJECTED by the Zod enum for
    `scene.transition.type`. The export is dead: nothing in the React tree imports
    it, the real implementation lives in src/lib/transitions.ts, and its enum uses
    entirely different names ('fade', 'wipe', 'pushCut', ...). So the panel was
    listing 12 names that fail validation while hiding the 18 that work. It now
    serves the Zod-accepted list; the dead export is exposed separately as
    `legacy_unused_transitions` so the discrepancy stays visible instead of
    silently reappearing.
    """
    from msf import registry

    accepted = registry.scene_transition_types()
    legacy = registry.transition_names()
    return {
        "effects": [
            {
                "name": e.name,
                "family": e.family,
                "summary": e.summary,
                "stochastic": e.stochastic,
                "pack": e.pack,
            }
            for e in sorted(registry.load_effects().values(), key=lambda x: x.name)
        ],
        "by_family": registry.effects_by_family(),
        "transitions": accepted,
        "legacy_unused_transitions": sorted(set(legacy) - set(accepted)),
    }


def _local_voice_catalog() -> tuple[str, list[Dict[str, Any]]]:
    """Read the portable voice registry without importing the optional TTS runtime.

    Catalogue management and transcript review should work on a machine before a
    GPU/TTS environment is configured. Actual synthesis remains a separate runtime
    check in the preview endpoint.
    """
    import soundfile as sf

    from msf.config import MSFConfig

    default_voice = MSFConfig().tts.speaker
    voices_path = REPO / "assets" / "voices" / "voices.json"
    entries = json.loads(voices_path.read_text(encoding="utf-8")) if voices_path.is_file() else {}
    items: list[Dict[str, Any]] = []
    for key, entry in sorted(entries.items()):
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        ref_audio = REPO / str(entry.get("ref_audio", ""))
        exists = ref_audio.is_file()
        duration, sample_rate = None, None
        if exists:
            try:
                meta = sf.info(str(ref_audio))
                duration, sample_rate = round(meta.duration, 2), meta.samplerate
            except Exception:
                exists = False
        has_text = bool(str(entry.get("ref_text") or "").strip())
        items.append({
            "key": key, "ref_audio": str(entry.get("ref_audio") or ""), "exists": exists,
            "duration_sec": duration, "sample_rate": sample_rate, "has_ref_text": has_text,
            "mode": "icl" if has_text else "x_vector_only", "icl": has_text,
            "lang": entry.get("lang"), "notes": entry.get("notes"), "ref_text": entry.get("ref_text"),
            "is_default": key == default_voice, "usable": exists and has_text,
        })
    return default_voice, items


@app.get("/api/voices")
def api_voices() -> Dict[str, Any]:
    """Voice catalogue available even before optional synthesis dependencies are installed."""
    from msf.config import MSFConfig

    default_voice, voices = _local_voice_catalog()
    for item in voices:
        if item.get("exists"):
            item["reference_preview_url"] = f"/api/preview/voice-reference/{item['key']}"
    cfg = MSFConfig()
    return {"default": default_voice, "configured": cfg.tts.speaker, "configured_is_valid": any(v["key"] == cfg.tts.speaker for v in voices), "items": voices}


@app.get("/api/preview/voice-reference/{key}")
def api_preview_voice_reference(key: str) -> FileResponse:
    """Play a registered source reference without loading a TTS model."""
    _, voices = _local_voice_catalog()
    item = next((voice for voice in voices if voice["key"] == key), None)
    if not item or not item.get("exists"):
        raise HTTPException(404, "voice reference not available")
    root = (REPO / "assets" / "voices" / "refs").resolve()
    candidate = (REPO / str(item["ref_audio"])).resolve()
    if root not in candidate.parents or not candidate.is_file():
        raise HTTPException(404, "voice reference not available")
    return FileResponse(candidate, media_type="audio/wav")


@app.get("/api/audio")
def api_audio() -> Dict[str, Any]:
    """SFX and music beds, read from the same registries the mixer renders from."""
    from msf.audio import music as music_mod
    from msf.audio import sfx as sfx_mod

    sfx_items = [
        {
            "name": s.name,
            "family": s.family,
            "max_ms": s.max_ms,
            "summary": s.summary,
            "loop": s.loop,
            "peak_db": s.peak_db,
        }
        for s in sorted(sfx_mod.SFX_REGISTRY.values(), key=lambda x: (x.family, x.name))
    ]
    # BedSpec carries bpm/key/character/use — not `summary`. Reading a field that
    # does not exist would silently render every bed with an empty description.
    beds = [
        {
            "name": b.name,
            "bpm": b.bpm,
            "key": b.key,
            "character": b.character,
            "use": b.use,
            "peak_db": b.peak_db,
        }
        for b in sorted(music_mod.MUSIC_REGISTRY.values(), key=lambda x: x.name)
    ]
    return {"sfx": sfx_items, "music": beds}


@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    """One place to see whether the moving parts are actually reachable.

    Every check reports what was verified. A panel that says "OK" without probing
    is worse than no panel — the whole reason the pipeline shipped with a broken
    voice reference is that nothing checked the file existed.
    """
    import importlib.util

    from msf import registry
    from msf.config import MSFConfig

    cfg = MSFConfig()
    checks: List[Dict[str, Any]] = []

    presets = registry.load_registry()
    checks.append({
        "name": "scene registry",
        "ok": len(presets) > 20,
        "detail": f"{len(presets)} presets parsed from remotion/src/registry",
    })

    effects = registry.load_effects()
    checks.append({
        "name": "effect registry",
        "ok": len(effects) > 50,
        "detail": f"{len(effects)} effects, {len(registry.scene_transition_types())} transitions",
    })

    default_voice, voices = _local_voice_catalog()
    info = next((item for item in voices if item["key"] == default_voice), None)
    checks.append({
        "name": f"default voice ({default_voice})",
        "ok": bool(info and info.get("exists") and info.get("has_ref_text")),
        "detail": f"{info.get('mode') if info else 'missing'} — {Path(str(info.get('ref_audio') if info else '')).name}",
    })
    has_tts_runtime = bool(importlib.util.find_spec("torch")) and bool(importlib.util.find_spec("qwen_tts"))
    checks.append({
        "name": "Qwen TTS runtime",
        "ok": has_tts_runtime,
        "detail": "torch + qwen_tts installed" if has_tts_runtime else "torch and/or qwen_tts unavailable; Voice Lab management still works",
    })

    checks.append({
        "name": "configured speaker",
        "ok": True,
        "detail": f"tts.speaker={cfg.tts.speaker}",
    })

    checks.append({
        "name": "node + remotion",
        "ok": bool(shutil.which("node")) and (REMOTION / "node_modules").is_dir(),
        "detail": f"node={shutil.which('node') or 'MISSING'}; "
                  f"node_modules={'present' if (REMOTION / 'node_modules').is_dir() else 'MISSING'}",
    })

    checks.append({
        "name": "ffmpeg",
        "ok": bool(shutil.which("ffmpeg")),
        "detail": shutil.which("ffmpeg") or "MISSING — audio mastering will fail",
    })

    # LDR is fail-closed by design: report it, do not run a query here.
    from msf.skills_bridge import deep_research as dr

    checks.append({
        "name": "LDR work dir",
        "ok": dr.LDR_WORK.is_dir(),
        "detail": f"{dr.LDR_WORK} ({'exists' if dr.LDR_WORK.is_dir() else 'MISSING'})",
    })
    checks.append({
        "name": "LDR python",
        "ok": Path(dr.LDR_PYTHON).is_file(),
        "detail": f"{dr.LDR_PYTHON} ({'exists' if Path(dr.LDR_PYTHON).is_file() else 'MISSING'})",
    })

    return {
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "llm": {"base_url": cfg.llm.base_url, "model": cfg.llm.model},
        "render": {"fps": cfg.render.fps, "width": cfg.render.width, "height": cfg.render.height},
    }


# ---------------------------------------------------------------- previews
#
# Every preview renders through the SAME code path the pipeline uses — the panel
# must not have its own renderer, or "it looked fine in the panel" stops meaning
# anything. Scene stills and clips go through msf.panel.render_client (a resident
# node process holding the real Remotion bundle), audio through msf.audio.sfx/
# music, voice through synthesize_voice_clone.
#
# WHY NOT stress.mjs ANY MORE
# ---------------------------
# It shelled out `node scripts/stress.mjs` per preview, which re-bundles the whole
# composition every time: 19.7s cold, ~14s warm, measured. The resident server
# bundles once and answers a still in ~7s / a clip in ~4s, and it reports the real
# `durationInFrames` from calculateMetadata, which stress.mjs could not — so a
# frame percentage now resolves against the composition's true length instead of
# the pre-transition guess.


class ScenePreviewRequest(BaseModel):
    preset: str
    props: Dict[str, Any] = Field(default_factory=dict)
    frame_pct: float = Field(0.9, ge=0.0, le=1.0)
    # None means "size the scene to its own text" via demo_props.suggested_duration.
    # A fixed 180 was inventing readability warnings on seven presets whose demo
    # copy cannot be read in 3s, burying the real ones.
    duration_frames: Optional[int] = Field(None, ge=30, le=1800)
    style: str = "pop"
    # Fill unspecified props from the demo set so a bare {"preset": X} renders
    # something representative instead of an empty card.
    demo_props: bool = True
    # 0.5 halves render time and is plenty for layout review; 1.0 for pixel checks.
    scale: float = Field(1.0, gt=0.0, le=1.0)


def _preview_scene_and_spec(req: ScenePreviewRequest) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Build + validate the one-scene spec shared by the still and clip routes."""
    from msf import registry
    from msf.panel import demo_props as dp
    from msf.spec import validate_spec

    if req.preset not in registry.load_registry():
        raise HTTPException(404, f"unknown preset {req.preset!r}")

    if req.demo_props:
        scene = dp.scene_for(
            req.preset, duration_in_frames=req.duration_frames, overrides=req.props
        )
    else:
        scene = {"id": "preview", "preset": req.preset, **req.props}
        scene["durationInFrames"] = (
            req.duration_frames
            if req.duration_frames is not None
            else dp.suggested_duration(scene)
        )

    spec = {
        "width": 1080, "height": 1920, "fps": 60,
        "durationInFrames": scene["durationInFrames"],
        "style": req.style, "scenes": [scene],
    }
    try:
        validate_spec(spec)
    except ValueError as exc:
        # A real validation failure is the useful answer, not a red ERROR card
        # rendered as if it were a working preview.
        raise HTTPException(422, str(exc)) from exc
    return scene, spec


def _thumbnail_cache_entry(req: ScenePreviewRequest) -> tuple[Dict[str, Any], Dict[str, Any], Path, str]:
    """Return a stable thumbnail path derived from the exact validated scene spec.

    Unlike the ad-hoc review preview, the catalogue thumbnail must not mint a new
    file on every page visit. The spec includes demo props and duration, so a
    component change or a changed demo scene produces a new cache key naturally.
    """
    scene, spec = _preview_scene_and_spec(req)
    canonical = json.dumps(
        {"spec": spec, "frame_pct": req.frame_pct, "scale": req.scale},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:16]
    safe_preset = "".join(ch for ch in req.preset if ch.isalnum() or ch in "-_")
    filename = f"{safe_preset}-{digest}.png"
    path = CACHE / "thumbnails" / filename
    return scene, spec, path, filename


class SceneThumbnailRequest(ScenePreviewRequest):
    """Catalogue-size still. Rendered only on cache miss through the resident client."""

    scale: float = Field(0.18, gt=0.0, le=0.5)
    frame_pct: float = Field(0.76, ge=0.0, le=1.0)


def _thumbnail_payload(req: SceneThumbnailRequest, render_on_miss: bool) -> Dict[str, Any]:
    from msf.panel.render_client import RenderServerError, get_client

    _, spec, png, filename = _thumbnail_cache_entry(req)
    if png.is_file():
        return {"url": f"/preview/thumbnails/{filename}", "preset": req.preset, "cached": True, "bytes": png.stat().st_size}
    if not render_on_miss:
        raise HTTPException(404, "thumbnail not cached")
    png.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    try:
        result = get_client().still(spec, png, frame_pct=req.frame_pct, scale=req.scale)
    except RenderServerError as exc:
        raise HTTPException(503, f"render server: {exc}") from exc
    if not png.is_file():
        raise HTTPException(500, "render server reported success but wrote no thumbnail")
    return {"url": f"/preview/thumbnails/{filename}", "preset": req.preset, "cached": False, "bytes": png.stat().st_size, "frame": result.get("frame"), "render_ms": result.get("ms"), "wall_sec": round(time.time() - started, 2)}


@app.get("/api/preview/thumbnail/{preset}")
def api_cached_thumbnail(preset: str) -> Dict[str, Any]:
    """Return a cached catalogue thumbnail without starting a renderer job."""
    return _thumbnail_payload(SceneThumbnailRequest(preset=preset), render_on_miss=False)


@app.post("/api/preview/thumbnail")
def api_preview_thumbnail(req: SceneThumbnailRequest) -> Dict[str, Any]:
    """Render a small catalogue thumbnail exactly once per deterministic cache key."""
    return _thumbnail_payload(req, render_on_miss=True)


@app.post("/api/preview/scene")
def api_preview_scene(req: ScenePreviewRequest) -> Dict[str, Any]:
    """Render one still of a preset and return a URL to the PNG."""
    from msf.panel.render_client import RenderServerError, get_client

    scene, spec = _preview_scene_and_spec(req)

    token = uuid.uuid4().hex[:12]
    out_dir = CACHE / "scenes"
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"{token}.png"

    started = time.time()
    try:
        res = get_client().still(spec, png, frame_pct=req.frame_pct, scale=req.scale)
    except RenderServerError as exc:
        raise HTTPException(503, f"render server: {exc}") from exc
    if not png.is_file():
        raise HTTPException(500, "render server reported success but wrote no file")

    return {
        "url": f"/preview/scenes/{token}.png",
        "preset": req.preset,
        "frame": res.get("frame"),
        "frame_pct": req.frame_pct,
        "duration_frames": res.get("durationInFrames"),
        "scale": req.scale,
        "bytes": res.get("bytes"),
        "render_ms": res.get("ms"),
        "wall_sec": round(time.time() - started, 2),
        "warnings": [],
    }


class SceneClipRequest(ScenePreviewRequest):
    """A short MP4 instead of a still — the only way to review MOTION.

    Stills cannot show whether a reveal settles before the scene ends, which is
    the defect class the pacing contract exists to prevent.
    """

    from_frame: int = Field(0, ge=0)
    to_frame: Optional[int] = Field(None, ge=1)
    scale: float = Field(0.5, gt=0.0, le=1.0)
    crf: int = Field(26, ge=1, le=51)


@app.post("/api/preview/clip")
def api_preview_clip(req: SceneClipRequest) -> Dict[str, Any]:
    """Render a frame range of a preset to MP4 and return a URL."""
    from msf.panel.render_client import RenderServerError, get_client

    scene, spec = _preview_scene_and_spec(req)
    if req.to_frame is not None and req.to_frame <= req.from_frame:
        raise HTTPException(400, "to_frame must be greater than from_frame")

    # The metadata resolver may return an odd effective composition width for a
    # vertical preset. Half/full scales are the portable integer dimensions for
    # every supported preset; arbitrary fractions are suitable for stills only.
    effective_scale = 0.5 if req.scale <= 0.75 else 1.0
    token = uuid.uuid4().hex[:12]
    out_dir = CACHE / "clips"
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4 = out_dir / f"{token}.mp4"

    started = time.time()
    try:
        res = get_client().clip(
            spec, mp4, frm=req.from_frame, to=req.to_frame,
            scale=effective_scale, crf=req.crf,
        )
    except RenderServerError as exc:
        raise HTTPException(503, f"render server: {exc}") from exc
    if not mp4.is_file():
        raise HTTPException(500, "render server reported success but wrote no file")

    return {
        "url": f"/preview/clips/{token}.mp4",
        "preset": req.preset,
        "from": res.get("from"),
        "to": res.get("to"),
        "duration_frames": res.get("durationInFrames"),
        "scale": effective_scale,
        "bytes": res.get("bytes"),
        "render_ms": res.get("ms"),
        "wall_sec": round(time.time() - started, 2),
    }


class TransitionPreviewRequest(BaseModel):
    """Render one production transition over the same known readable scene pair."""

    transition: str
    style: str = "llm_hubs_neon"
    scale: float = Field(0.25, gt=0.0, le=1.0)
    duration_frames: int = Field(28, ge=8, le=120)


@app.post("/api/preview/transition")
def api_preview_transition(req: TransitionPreviewRequest) -> Dict[str, Any]:
    """Create a deterministic two-scene MP4 which isolates transition motion."""
    from msf import registry
    from msf.panel import demo_props as dp
    from msf.panel.render_client import RenderServerError, get_client
    from msf.spec import validate_spec

    if req.transition not in registry.scene_transition_types():
        raise HTTPException(404, f"unknown transition {req.transition!r}")
    # Remotion derives both dimensions from `scale`; 1080x1920 has gcd 120,
    # so snap arbitrary UI values to n/120 and avoid fractional ffmpeg frames.
    effective_scale = max(1 / 120, min(1.0, round(req.scale * 120) / 120))
    left = dp.scene_for("HeroKinetic", duration_in_frames=150, overrides={
        "title": "ПЕРВЫЙ КАДР", "subtitle": "Одинаковая базовая сцена",
    })
    right = dp.scene_for("ProviderChat", duration_in_frames=170, overrides={
        "provider": "SECOND SCENE", "avatarText": "02",
    })
    right["transition"] = {
        "type": req.transition,
        "durationInFrames": req.duration_frames,
        "timing": "spring",
    }
    spec = {
        "width": 1080, "height": 1920, "fps": 60,
        "style": req.style, "scenes": [left, right],
    }
    try:
        validate_spec(spec)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    # Keep the exact preview window stable in both rendered and cache-hit API
    # responses so the client can reason about timeline semantics either way.
    transition_start = left["durationInFrames"] - req.duration_frames
    from_frame = max(0, transition_start - 48)
    to_frame = min(left["durationInFrames"] + right["durationInFrames"] - req.duration_frames, transition_start + 72)
    canonical = json.dumps(
        {"transition": req.transition, "style": req.style, "scale": effective_scale,
         "duration": req.duration_frames, "window": "transition-centered-v2"}, ensure_ascii=False, sort_keys=True,
         separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:16]
    safe_name = "".join(ch for ch in req.transition if ch.isalnum() or ch in "-_")
    out_dir = CACHE / "clips"
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4 = out_dir / f"transition-{safe_name}-{digest}.mp4"
    if mp4.is_file():
        return {"url": f"/preview/clips/{mp4.name}", "transition": req.transition,
                "style": req.style, "cached": True, "bytes": mp4.stat().st_size,
                "scale": effective_scale, "from_frame": from_frame, "to_frame": to_frame}
    started = time.time()
    # Render only a 2.0s window centred around the overlap. It begins with a
    # visible established first scene and reaches the transition quickly, which is
    # materially more useful in a catalog card than a full five-second sequence.
    try:
        result = get_client().clip(spec, mp4, frm=from_frame, to=to_frame, scale=effective_scale, crf=27)
    except RenderServerError as exc:
        raise HTTPException(503, f"render server: {exc}") from exc
    if not mp4.is_file():
        raise HTTPException(500, "render server reported success but wrote no transition preview")
    return {"url": f"/preview/clips/{mp4.name}", "transition": req.transition,
            "style": req.style, "cached": False, "bytes": mp4.stat().st_size,
            "duration_frames": result.get("durationInFrames"), "scale": effective_scale,
            "from_frame": from_frame, "to_frame": to_frame,
            "render_ms": result.get("ms"), "wall_sec": round(time.time() - started, 2)}


class BuilderTransitionRecipeRequest(BaseModel):
    name: str = Field(min_length=2, max_length=48, pattern=r"^[A-Za-z][A-Za-z0-9_-]+$")
    base_transition: str = Field(min_length=2, max_length=80)
    style_id: str = Field(default="llm_hubs_neon", min_length=2, max_length=80)
    summary: str = Field(min_length=12, max_length=180)


class BuilderOverlayRequest(BaseModel):
    name: str = Field(min_length=2, max_length=48, pattern=r"^[A-Za-z][A-Za-z0-9_-]+$")
    overlay_type: str = Field(min_length=2, max_length=32)
    label: str = Field(min_length=1, max_length=80)
    style_id: str = Field(default="llm_hubs_neon", min_length=2, max_length=80)


_ELEMENT_BUILDER_ROOT = REPO / "output" / "studio" / "element_builder"
_TRANSITION_RECIPES = _ELEMENT_BUILDER_ROOT / "transition_recipes.json"
_OVERLAY_RECIPES = _ELEMENT_BUILDER_ROOT / "overlay_recipes.json"
_TRANSITION_SCAFFOLD_DIR = REPO / "remotion" / "src" / "transitions" / "generated"
_OVERLAY_TYPES = {"timer", "notification", "money", "cursor", "focus", "badge"}


def _recipe_store(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except json.JSONDecodeError:
        loaded = {}
    return loaded if isinstance(loaded, dict) else {}


def _save_recipe(path: Path, name: str, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _recipe_store(path)
    data[name] = payload
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _builder_overlay_spec(req: BuilderOverlayRequest) -> dict[str, Any]:
    if req.overlay_type not in _OVERLAY_TYPES:
        raise HTTPException(422, f"unknown overlay type {req.overlay_type!r}")
    overlay: dict[str, Any] = {"type": req.overlay_type, "at": 0.12, "hold": 2.2, "position": "top"}
    if req.overlay_type == "notification":
        overlay.update({"appName": "Telegram", "title": req.label, "text": "Новый элемент поверх сцены", "position": "top"})
    elif req.overlay_type == "cursor":
        overlay.update({"x": 0.57, "y": 0.58, "targetLabel": req.label})
    elif req.overlay_type == "focus":
        overlay.update({"x": 0.5, "y": 0.56, "w": 0.46, "h": 0.16, "targetLabel": req.label})
    elif req.overlay_type == "badge":
        overlay.update({"badgeText": req.label, "position": "bottom"})
    elif req.overlay_type == "timer":
        overlay.update({"seconds": 10, "label": req.label, "position": "top-right"})
    else:
        overlay.update({"amount": 9.99, "currency": "USD", "sender": req.label, "position": "top"})
    return overlay


@app.post("/api/studio/element-builder/transition/preview")
def api_builder_transition_preview(req: BuilderTransitionRecipeRequest) -> Dict[str, Any]:
    _require_style_ids([req.style_id])
    # Delegates to the same centred two-scene preview used by the Elements catalog.
    payload = api_preview_transition(TransitionPreviewRequest(transition=req.base_transition, style=req.style_id, scale=0.32))
    payload.update({"name": req.name, "summary": req.summary, "mode": "production_transition_preview"})
    return payload


@app.post("/api/studio/element-builder/transition/scaffold")
def api_builder_transition_scaffold(req: BuilderTransitionRecipeRequest) -> Dict[str, Any]:
    _require_style_ids([req.style_id])
    from msf import registry
    if req.base_transition not in registry.scene_transition_types():
        raise HTTPException(422, f"unknown transition {req.base_transition!r}")
    safe_name = req.name.replace("-", "_")
    target = _TRANSITION_SCAFFOLD_DIR / f"{safe_name}.ts"
    if target.exists():
        raise HTTPException(409, f"transition scaffold already exists: {target.relative_to(REPO)}")
    _TRANSITION_SCAFFOLD_DIR.mkdir(parents=True, exist_ok=True)
    source = f"""/**\n * {req.name} — {req.summary.strip()}\n *\n * Element Builder scaffold. This is intentionally not part of the production\n * transition enum until its author wires it into remotion/src/lib/transitions.ts\n * and passes the normal TypeScript/render verification.\n */\nexport const {safe_name}Recipe = {{\n  name: {req.name!r},\n  baseTransition: {req.base_transition!r},\n  style: {req.style_id!r},\n}} as const;\n"""
    target.write_text(source, encoding="utf-8")
    component_path = str(target.relative_to(REPO)) if target.is_relative_to(REPO) else str(target)
    recipe = {"kind": "transition_recipe", "name": req.name, "base_transition": req.base_transition, "style_id": req.style_id, "summary": req.summary.strip(), "component_path": component_path, "created_at": datetime.now(timezone.utc).isoformat()}
    _save_recipe(_TRANSITION_RECIPES, req.name, recipe)
    recipe_path = str(_TRANSITION_RECIPES.relative_to(REPO)) if _TRANSITION_RECIPES.is_relative_to(REPO) else str(_TRANSITION_RECIPES)
    return {"recipe": recipe, "path": recipe_path, "component_path": recipe["component_path"], "verification": ["Preview the base transition in Element Builder", "Implement shader/TypeScript in remotion/src/lib/transitions.ts", "cd remotion && npx tsc --noEmit", "python tools/msf_add.py verify"]}


@app.get("/api/studio/overlays")
def api_studio_overlays() -> Dict[str, Any]:
    recipes = _recipe_store(_OVERLAY_RECIPES)
    builtin = [{"name": name, "kind": "builtin", "summary": {"notification": "Notification / Telegram banner over any scene.", "cursor": "Cursor and click target for screen guides.", "focus": "Focus box around a target area.", "badge": "CTA, like or subscribe badge.", "timer": "Countdown / urgency timer.", "money": "Price, saving or payment toast."}[name]} for name in sorted(_OVERLAY_TYPES)]
    custom = [{"name": name, "kind": "recipe", "summary": str(recipe.get("overlay", {}).get("type", "overlay")), "style_id": recipe.get("style_id"), "overlay": recipe.get("overlay")} for name, recipe in recipes.items() if isinstance(recipe, dict)]
    return {"items": [*builtin, *custom]}


@app.get("/api/studio/element-builder/transition-recipes")
def api_builder_transition_recipes() -> Dict[str, Any]:
    recipes = _recipe_store(_TRANSITION_RECIPES)
    return {"items": [recipe for recipe in recipes.values() if isinstance(recipe, dict)]}


@app.post("/api/studio/element-builder/overlay/preview")
def api_builder_overlay_preview(req: BuilderOverlayRequest) -> Dict[str, Any]:
    _require_style_ids([req.style_id])
    overlay = _builder_overlay_spec(req)
    preview = ScenePreviewRequest(preset="HeroKinetic", style=req.style_id, duration_frames=180, demo_props=True, scale=0.42, frame_pct=0.52, props={"title": "БАЗОВАЯ СЦЕНА", "subtitle": "Проверка overlay recipe", "overlays": [overlay]})
    payload = api_preview_scene(preview)
    payload.update({"overlay": overlay, "mode": "overlay_still_preview"})
    return payload


@app.post("/api/studio/element-builder/overlay/motion")
def api_builder_overlay_motion(req: BuilderOverlayRequest) -> Dict[str, Any]:
    _require_style_ids([req.style_id])
    overlay = _builder_overlay_spec(req)
    preview = SceneClipRequest(preset="HeroKinetic", style=req.style_id, duration_frames=180, demo_props=True, scale=0.36, to_frame=150, props={"title": "БАЗОВАЯ СЦЕНА", "subtitle": "Проверка overlay recipe", "overlays": [overlay]})
    payload = api_preview_clip(preview)
    payload.update({"overlay": overlay, "mode": "overlay_motion_preview"})
    return payload


@app.post("/api/studio/element-builder/overlay/register")
def api_builder_overlay_register(req: BuilderOverlayRequest) -> Dict[str, Any]:
    _require_style_ids([req.style_id])
    overlay = _builder_overlay_spec(req)
    recipe = {"kind": "overlay_recipe", "name": req.name, "style_id": req.style_id, "overlay": overlay, "created_at": datetime.now(timezone.utc).isoformat()}
    _save_recipe(_OVERLAY_RECIPES, req.name, recipe)
    return {"recipe": recipe, "path": str(_OVERLAY_RECIPES.relative_to(REPO)), "verification": ["Preview still and motion in Element Builder", "Attach the recipe to a scene overlays array", "Render the affected VideoSpec before publishing"]}


class BuilderStyleDraftRequest(BaseModel):
    style_id: str = Field(min_length=3, max_length=48, pattern=r"^[a-z][a-z0-9_]+$")
    label: str = Field(min_length=3, max_length=64)
    base_style: str = Field(min_length=2, max_length=80)
    neon: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    summary: str = Field(min_length=12, max_length=180)
    scenes: list[str] = Field(default_factory=list, max_length=24)


_STYLE_DRAFTS = _ELEMENT_BUILDER_ROOT / "style_drafts.json"


def _style_draft_payload(req: BuilderStyleDraftRequest) -> dict[str, Any]:
    _require_style_ids([req.base_style])
    scene_names = [name for name in req.scenes if re.fullmatch(r"[A-Za-z][A-Za-z0-9]+", name)]
    return {"kind": "style_draft", "id": req.style_id, "label": req.label.strip(), "base_style": req.base_style, "summary": req.summary.strip(), "recommended_scenes": scene_names, "safe_config": {"palette": {"neon": req.neon.upper()}}, "created_at": datetime.now(timezone.utc).isoformat()}


@app.post("/api/studio/element-builder/style/preview")
def api_builder_style_preview(req: BuilderStyleDraftRequest) -> Dict[str, Any]:
    draft = _style_draft_payload(req)
    preset = draft["recommended_scenes"][0] if draft["recommended_scenes"] else "HeroKinetic"
    preview = SceneThumbnailRequest(preset=preset, style=draft["base_style"], demo_props=True, scale=0.32, frame_pct=0.78, props={"styleConfig": draft["safe_config"]})
    payload = _thumbnail_payload(preview, render_on_miss=True)
    payload.update({"draft": draft, "preset": preset, "mode": "style_draft_scene_preview"})
    return payload


@app.post("/api/studio/element-builder/style/register")
def api_builder_style_register(req: BuilderStyleDraftRequest) -> Dict[str, Any]:
    draft = _style_draft_payload(req)
    _save_recipe(_STYLE_DRAFTS, req.style_id, draft)
    return {"draft": draft, "path": str(_STYLE_DRAFTS.relative_to(REPO)), "verification": ["Review the canonical scene preview", "Use the base family plus safe_config in a VideoSpec styleConfig", "Run a representative render with dense text before promotion"]}


class SceneBuilderPreviewRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64, pattern=r"^[A-Z][A-Za-z0-9]+$")
    summary: str = Field(min_length=12, max_length=180)
    style_id: str = Field(default="llm_hubs_neon", min_length=2, max_length=80)


class SceneBuilderScaffoldRequest(SceneBuilderPreviewRequest):
    category: str = Field(default="typography")
    fields: List[str] = Field(default_factory=lambda: ["title", "subtitle"], max_length=12)
    style_ids: List[str] = Field(default_factory=list, max_length=16)


_SCENE_BUILDER_CATEGORIES = {
    "typography", "data", "diagram", "code", "ui-mock", "device", "three", "narrative", "transition-aid",
}
_SCENE_BUILDER_PROFILES = REPO / "output" / "studio" / "scene_builder" / "scene_profiles.json"


def _valid_builder_fields(fields: List[str]) -> list[str]:
    clean: list[str] = []
    for field_name in fields:
        value = str(field_name).strip()
        if not value or not value.replace("_", "").isalnum() or not value[0].isalpha():
            raise HTTPException(422, "scene fields must be simple identifier names")
        if value not in clean:
            clean.append(value)
    return clean or ["title", "subtitle"]


def _require_style_ids(style_ids: List[str]) -> list[str]:
    from msf.studio.style_catalog import STYLE_FAMILIES

    available = {str(item["id"]) for item in STYLE_FAMILIES}
    unknown = sorted(set(style_ids) - available)
    if unknown:
        raise HTTPException(422, f"unknown style family: {', '.join(unknown)}")
    return list(dict.fromkeys(style_ids))


class Universal3DGraphRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64, pattern=r"^[A-Z][A-Za-z0-9]+$")
    summary: str = Field(min_length=12, max_length=240)
    style_id: str = Field(default="llm_hubs_neon", min_length=2, max_length=80)
    graph: Dict[str, Any]


_UNIVERSAL_3D_RECIPES = _ELEMENT_BUILDER_ROOT / "universal_3d_recipes.json"
_UNIVERSAL_3D_TYPES = {"box", "sphere", "torus", "cylinder", "cone", "plane", "octahedron", "icosahedron", "line", "asset", "group"}
_UNIVERSAL_3D_MAX_NODES = 128
_UNIVERSAL_3D_MAX_DEPTH = 8


def _validate_universal_3d_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    if graph.get("version") != 1:
        raise HTTPException(422, "3D graph version must be 1")
    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise HTTPException(422, "3D graph requires at least one node")
    count = 0
    ids: set[str] = set()
    def visit(items: Any, depth: int) -> None:
        nonlocal count
        if depth > _UNIVERSAL_3D_MAX_DEPTH:
            raise HTTPException(422, "3D graph nesting is too deep")
        if not isinstance(items, list):
            raise HTTPException(422, "3D children must be arrays")
        for node in items:
            if not isinstance(node, dict):
                raise HTTPException(422, "3D nodes must be objects")
            count += 1
            if count > _UNIVERSAL_3D_MAX_NODES:
                raise HTTPException(422, "3D graph exceeds 128 nodes")
            node_id = str(node.get("id", ""))
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", node_id) or node_id in ids:
                raise HTTPException(422, "3D node ids must be unique simple identifiers")
            ids.add(node_id)
            if node.get("type") not in _UNIVERSAL_3D_TYPES:
                raise HTTPException(422, f"unsupported 3D node type: {node.get('type')}")
            for key in ("position", "rotation", "scale"):
                if key in node and (not isinstance(node[key], list) or len(node[key]) != 3 or not all(isinstance(x, (int, float)) for x in node[key])):
                    raise HTTPException(422, f"3D {key} must be a numeric Vec3")
            if node.get("type") == "asset" and not isinstance(node.get("assetUrl"), str):
                raise HTTPException(422, "asset node requires assetUrl")
            visit(node.get("children", []), depth + 1)
    visit(nodes, 0)
    clean = dict(graph)
    clean["nodes"] = nodes
    return clean


@app.post("/api/studio/element-builder/3d/preview")
def api_builder_3d_preview(req: Universal3DGraphRequest) -> Dict[str, Any]:
    _require_style_ids([req.style_id])
    graph = _validate_universal_3d_graph(req.graph)
    preview = ScenePreviewRequest(preset="Universal3DGraph", style=req.style_id, demo_props=False, scale=0.36, duration_frames=180, props={"title": req.name, "graph": graph})
    payload = api_preview_scene(preview)
    payload.update({"mode": "universal_3d_graph_preview", "name": req.name, "summary": req.summary, "node_count": len(graph["nodes"])})
    return payload


@app.post("/api/studio/element-builder/3d/motion")
def api_builder_3d_motion(req: Universal3DGraphRequest) -> Dict[str, Any]:
    _require_style_ids([req.style_id])
    graph = _validate_universal_3d_graph(req.graph)
    preview = SceneClipRequest(preset="Universal3DGraph", style=req.style_id, demo_props=False, scale=0.36, duration_frames=180, to_frame=150, props={"title": req.name, "graph": graph})
    payload = api_preview_clip(preview)
    payload.update({"mode": "universal_3d_graph_motion", "name": req.name, "node_count": len(graph["nodes"])})
    return payload


@app.post("/api/studio/element-builder/3d/register")
def api_builder_3d_register(req: Universal3DGraphRequest) -> Dict[str, Any]:
    graph = _validate_universal_3d_graph(req.graph)
    _require_style_ids([req.style_id])
    recipe = {"kind": "universal_3d_graph", "name": req.name, "summary": req.summary.strip(), "style_id": req.style_id, "graph": graph, "verification": ["Review still and MP4 previews", "Run Remotion TypeScript and representative render QA", "Promote only after asset licenses and safe-area checks"]}
    _save_recipe(_UNIVERSAL_3D_RECIPES, req.name, recipe)
    try:
        recipe_path = str(_UNIVERSAL_3D_RECIPES.relative_to(REPO))
    except ValueError:
        recipe_path = str(_UNIVERSAL_3D_RECIPES)
    return {"recipe": recipe, "path": recipe_path, "status": "registered_recipe"}


@app.post("/api/studio/scene-builder/preview")
def api_scene_builder_preview(req: SceneBuilderPreviewRequest) -> Dict[str, Any]:
    """Render the stable scaffold shell before authoring a new preset.

    It deliberately previews a standard safe layout rather than evaluating user
    TypeScript from the browser. The actual scaffold remains an explicit second
    action and must pass the normal TypeScript/registry verification afterwards.
    """
    _require_style_ids([req.style_id])
    preview = ScenePreviewRequest(
        preset="HeroKinetic", style=req.style_id, demo_props=True, scale=0.42,
        props={"title": req.name.upper(), "subtitle": req.summary},
    )
    payload = api_preview_scene(preview)
    payload.update({"mode": "safe_design_shell", "requested_name": req.name, "style_id": req.style_id})
    return payload


@app.post("/api/studio/scene-builder/scaffold")
def api_scene_builder_scaffold(req: SceneBuilderScaffoldRequest) -> Dict[str, Any]:
    """Create a registered TypeScript scene scaffold only after explicit operator intent."""
    if req.category not in _SCENE_BUILDER_CATEGORIES:
        raise HTTPException(422, "unknown scene category")
    fields = _valid_builder_fields(req.fields)
    style_ids = _require_style_ids(req.style_ids or [req.style_id])
    command = [
        sys.executable, str(REPO / "tools" / "msf_add.py"), "scene", req.name,
        "--category", req.category, "--summary", req.summary.strip(),
        "--fields", ",".join(fields),
    ]
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        detail = " | ".join((result.stderr or result.stdout or "scene scaffold failed").strip().splitlines()[-5:])
        raise HTTPException(422, detail)
    _SCENE_BUILDER_PROFILES.parent.mkdir(parents=True, exist_ok=True)
    try:
        profiles = json.loads(_SCENE_BUILDER_PROFILES.read_text(encoding="utf-8")) if _SCENE_BUILDER_PROFILES.is_file() else {}
    except json.JSONDecodeError:
        profiles = {}
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[req.name] = style_ids
    temporary = _SCENE_BUILDER_PROFILES.with_suffix(".tmp")
    temporary.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(_SCENE_BUILDER_PROFILES)
    from msf.studio.catalog import clear_catalog_cache
    clear_catalog_cache()
    relative = "remotion/src/presets/three" if req.category == "three" else "remotion/src/presets"
    return {
        "name": req.name, "styles": style_ids, "fields": fields,
        "component_path": f"{relative}/{req.name}.tsx",
        "registry_path": "remotion/src/registry/generated.ts",
        "verification": ["cd remotion && npx tsc --noEmit", "cd remotion && npx tsx audit/registry_probe.ts", f"python tools/msf_add.py verify --only {req.name}"],
        "generator_output": result.stdout.strip(),
    }


@app.get("/api/demo/props/{preset}")
def api_demo_props(preset: str) -> Dict[str, Any]:
    """The demo props the preview would use, so the UI can prefill its editor.

    Served from msf.panel.demo_props — the same source the preview renders from,
    so what you see in the form is what gets rendered.
    """
    from msf import registry
    from msf.panel import demo_props as dp

    if preset not in registry.load_registry():
        raise HTTPException(404, f"unknown preset {preset!r}")
    scene = dp.scene_for(preset)
    return {
        "preset": preset,
        "props": dp.props_for(preset),
        "scene": scene,
        "suggested_duration_frames": scene["durationInFrames"],
        "generic": preset not in dp.DEMO_PROPS,
    }


@app.get("/api/render-server")
def api_render_server() -> Dict[str, Any]:
    """Whether the resident renderer is up, and how long it has been."""
    from msf.panel.render_client import get_client

    return get_client().status


@app.post("/api/render-server/restart")
def api_render_server_restart() -> Dict[str, Any]:
    """Drop the render process so the next preview re-bundles.

    Needed because the bundle is held in memory: editing a .tsx preset has no
    effect on previews until the server restarts.
    """
    from msf.panel import render_client

    render_client.shutdown()
    return {"ok": True, "detail": "render server stopped; next preview will re-bundle"}


class VoicePreviewRequest(BaseModel):
    voice: Optional[str] = None
    text: str = Field(
        "Открытые модели догнали закрытые по длине контекста и по цене.",
        min_length=1, max_length=400,
    )


@app.post("/api/preview/voice")
def api_preview_voice(req: VoicePreviewRequest) -> Dict[str, Any]:
    """Synthesize a line so a voice can be HEARD before a 3-minute render uses it.

    This is the check that was missing: the pipeline ran for weeks on a fallback
    female voice because nothing ever played a sample.
    """
    from msf.skills_bridge.qwen3_tts import (
        describe_reference,
        synthesize_voice_clone,
        voice_prompt_cache_stats,
    )

    try:
        info = describe_reference(req.voice)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    if not info.get("exists"):
        raise HTTPException(422, f"reference audio missing: {info.get('ref_audio')}")

    out_dir = CACHE / "voice"
    out_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex[:12]
    dst = out_dir / f"{token}.wav"
    started = time.time()
    try:
        _, duration = synthesize_voice_clone(
            text=req.text, voice=req.voice, output_path=str(dst)
        )
    except Exception as exc:
        raise HTTPException(500, f"synthesis failed: {exc}") from exc

    return {
        "url": f"/preview/voice/{token}.wav",
        "voice": req.voice or "(registry default)",
        "mode": info.get("mode"),
        "icl": bool(info.get("has_ref_text")),
        "duration_sec": round(duration, 2),
        "synth_sec": round(time.time() - started, 1),
        "prompt_cache": voice_prompt_cache_stats() if info.get("has_ref_text") else None,
    }


@app.get("/api/preview/sfx/{name}")
def api_preview_sfx(name: str) -> Dict[str, Any]:
    """Render one SFX to a wav. Same synth the mixer uses, so it sounds identical."""
    from msf.audio import sfx as sfx_mod

    if name not in sfx_mod.SFX_REGISTRY:
        raise HTTPException(404, f"unknown sfx {name!r}")
    out_dir = CACHE / "sfx"
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{name}.wav"
    if not dst.is_file():
        wav = sfx_mod.render(name)
        _write_wav(dst, wav, sfx_mod.SR)
    return {"url": f"/preview/sfx/{name}.wav", "name": name}


@app.get("/api/preview/music/{name}")
def api_preview_music(name: str, seconds: float = 8.0) -> Dict[str, Any]:
    """Render a short excerpt of a music bed.

    Uses loop_bed(), the same function node_soundtrack uses to fill a timeline.
    render_bed() alone would produce the bed's natural length (often a couple of
    bars) and its decaying tail, which is not what a viewer hears under a video.
    """
    from msf.audio import music as music_mod

    if name not in music_mod.MUSIC_REGISTRY:
        raise HTTPException(404, f"unknown bed {name!r}")
    seconds = max(2.0, min(30.0, seconds))
    out_dir = CACHE / "music"
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{name}_{int(seconds)}s.wav"
    if not dst.is_file():
        wav = music_mod.loop_bed(name, seconds)
        _write_wav(dst, wav, music_mod.SR)
    return {"url": f"/preview/music/{dst.name}", "name": name, "seconds": seconds}


def _write_wav(path: Path, wav, sr: int) -> None:
    """Write float32 mono to 16-bit PCM."""
    import wave as wave_mod

    import numpy as np

    a = np.asarray(wav, dtype="float32")
    if a.ndim > 1:
        a = a.mean(axis=1)
    peak = float(abs(a).max()) if a.size else 0.0
    if peak > 1.0:
        a = a / peak
    pcm = (a * 32767).astype("int16")
    with wave_mod.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


@app.get("/preview/{kind}/{filename}")
def serve_preview(kind: str, filename: str) -> FileResponse:
    """Serve a cached preview artefact.

    Both components are validated against a whitelist and checked to resolve
    INSIDE the cache: `kind`/`filename` come from the network, and a naive join
    would let `../../..` read any file the process can reach.
    """
    if kind not in ("scenes", "clips", "thumbnails", "voice", "sfx", "music"):
        raise HTTPException(404, "unknown preview kind")
    candidate = (CACHE / kind / filename).resolve()
    root = (CACHE / kind).resolve()
    if root not in candidate.parents or not candidate.is_file():
        raise HTTPException(404, "not found")
    # Explicit for .mp4: without a media type the browser downloads the clip
    # instead of playing it inline, which defeats the point of a motion preview.
    media = "video/mp4" if candidate.suffix == ".mp4" else None
    return FileResponse(candidate, media_type=media)


# ---------------------------------------------------------------- LDR / graph


@app.get("/api/ldr")
def api_ldr() -> Dict[str, Any]:
    """LDR wiring, reported without running a query.

    LDR is fail-closed: node_deep_research raises rather than inventing facts. So
    the useful thing to show is whether it COULD run, and the last raw result.
    """
    from msf.skills_bridge import deep_research as dr

    last = dr.LDR_WORK / "ldr_last_raw.json"
    info: Dict[str, Any] = {
        "work_dir": str(dr.LDR_WORK),
        "work_dir_exists": dr.LDR_WORK.is_dir(),
        "python": str(dr.LDR_PYTHON),
        "python_exists": Path(dr.LDR_PYTHON).is_file(),
        "runner": dr.LDR_RUNNER,
        "runner_exists": (dr.LDR_WORK / dr.LDR_RUNNER).is_file(),
        "searxng_url": dr.SEARXNG_URL,
        "last_result_at": None,
        "last_result_preview": None,
    }
    if last.is_file():
        info["last_result_at"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(last.stat().st_mtime)
        )
        try:
            info["last_result_preview"] = json.loads(last.read_text(encoding="utf-8"))
        except Exception as exc:
            info["last_result_preview"] = {"parse_error": str(exc)}
    try:
        dr.check_searxng()
        info["searxng_ok"] = True
        info["searxng_detail"] = "reachable"
    except Exception as exc:
        info["searxng_ok"] = False
        info["searxng_detail"] = str(exc)[:200]
    return info


@dataclass
class Run:
    """One pipeline run, tracked so the panel can show progress instead of a spinner."""

    run_id: str
    topic: str
    started: float
    status: str = "running"
    node: Optional[str] = None
    log: List[str] = field(default_factory=list)
    error: Optional[str] = None
    output_path: Optional[str] = None
    proc: Optional[subprocess.Popen] = None
    reader: Optional[threading.Thread] = None
    lock: threading.Lock = field(default_factory=threading.Lock)


RUNS: Dict[str, Run] = {}


def _start_reader(r: Run) -> None:
    """Drain the child's stdout on a thread.

    NOT in the request handler. `proc.stdout.readline()` on a blocking pipe waits
    until a line arrives, so polling from /api/runs would hang the HTTP request for
    as long as the child is quiet — and during a Remotion render that is minutes.
    The panel would look frozen at exactly the moment it is most needed.
    """

    def pump() -> None:
        assert r.proc is not None and r.proc.stdout is not None
        for raw in r.proc.stdout:
            line = raw.rstrip()
            with r.lock:
                r.log.append(line)
                # The runner prints `[<node>] done` per node, `OUTPUT: <path>` on
                # success and `ERROR: ...` on failure — see msf/panel/run_job.py.
                if line.startswith("[") and "]" in line:
                    name = line[1:line.index("]")]
                    if name in _node_names() or name == "start":
                        r.node = name
                elif line.startswith("OUTPUT: "):
                    r.output_path = line[len("OUTPUT: "):].strip()
                elif line.startswith("ERROR: "):
                    r.error = line[len("ERROR: "):].strip()
        rc = r.proc.wait()
        with r.lock:
            if r.status == "running":
                r.status = "done" if rc == 0 else "failed"
            if rc != 0 and not r.error:
                r.error = f"exit code {rc}; last log: " + " | ".join(r.log[-3:])

    r.reader = threading.Thread(target=pump, daemon=True, name=f"run-{r.run_id}")
    r.reader.start()


def _snapshot(r: Run) -> Dict[str, Any]:
    with r.lock:
        return {
            "run_id": r.run_id,
            "topic": r.topic,
            "status": r.status,
            "node": r.node,
            "started": time.strftime("%H:%M:%S", time.localtime(r.started)),
            "elapsed_sec": round(time.time() - r.started, 1),
            "error": r.error,
            "output_path": r.output_path,
            "log_lines": len(r.log),
        }


@app.get("/api/runs")
def api_runs() -> Dict[str, Any]:
    """Every run this server started, newest first."""
    return {"runs": [_snapshot(r) for r in sorted(RUNS.values(), key=lambda x: -x.started)]}


@app.get("/api/runs/{run_id}")
def api_run_detail(run_id: str, tail: int = 200) -> Dict[str, Any]:
    r = RUNS.get(run_id)
    if not r:
        raise HTTPException(404, "unknown run")
    out = _snapshot(r)
    with r.lock:
        out["log"] = r.log[-max(1, min(tail, 2000)):]
    return out


# Graph node names, in execution order, so the UI can show a real progress trail
# rather than a spinner.
#
# DERIVED, NOT LISTED. A hardcoded list drifted immediately: the graph registers
# "build_spec" -> node_build_remotion_spec and "render" -> node_remotion_render,
# so a `hasattr(video_graph, "node_build_spec")` check reported both as MISSING
# while they were present and working. Reading the add_node() calls gives the
# registered names AND their order from the one place that defines them.
#
# The builder is `build_msf_graph`. Guessing `build_video_graph` from the module
# name returned an empty node list and flagged all ten node functions as unwired —
# a "helpful" try/except turned a typo into a plausible-looking wrong answer, so
# the candidates are explicit and an empty result is reported as an error.
_GRAPH_BUILDERS = ("build_msf_graph", "build_video_graph")


def _graph_nodes() -> List[Dict[str, str]]:
    import inspect
    import re as _re

    from msf.graph import video_graph

    for builder_name in _GRAPH_BUILDERS:
        builder = getattr(video_graph, builder_name, None)
        if builder is None:
            continue
        try:
            src = inspect.getsource(builder)
        except (OSError, TypeError):
            continue
        nodes = [
            {"name": m.group(1), "fn": m.group(2)}
            for m in _re.finditer(
                r'add_node\(\s*"([^"]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)', src
            )
        ]
        if nodes:
            return nodes
    return []


@app.get("/api/graph")
def api_graph() -> Dict[str, Any]:
    """The pipeline's shape, read from the graph builder rather than duplicated."""
    from msf.graph import video_graph

    nodes = _graph_nodes()
    if not nodes:
        # Do not pretend the pipeline has no nodes.
        raise HTTPException(
            500,
            "could not read the graph: none of "
            f"{_GRAPH_BUILDERS} yielded add_node() calls in msf/graph/video_graph.py",
        )
    wired = {n["fn"] for n in nodes}
    orphans = [
        name for name in dir(video_graph)
        if name.startswith("node_") and name not in wired
    ]
    return {
        "nodes": [n["name"] for n in nodes],
        "node_functions": nodes,
        "unwired_functions": sorted(orphans),
        "rotation_presets": video_graph._TEXT_SAFE_PRESETS,
        "data_driven_count": len(video_graph._DATA_DRIVEN_PRESETS),
        "allowed_presets": len(video_graph.ALLOWED_PRESETS),
    }


@lru_cache(maxsize=1)
def _node_names() -> tuple:
    return tuple(n["name"] for n in _graph_nodes())


class VoiceAddRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=48)
    ref_audio: str = Field(..., description="Path to a wav on this machine")
    ref_text: str = Field(
        ..., min_length=10,
        description="VERBATIM transcript of ref_audio. Required — without it ICL is off.",
    )
    lang: str = "ru"
    notes: str = ""


@app.post("/api/voices")
def api_add_voice(req: VoiceAddRequest) -> Dict[str, Any]:
    """Register a new cloning reference in assets/voices/voices.json.

    The transcript is MANDATORY, not optional. resolve_voice() returns ref_text=None
    for an entry without one, which flips the model to x_vector_only_mode: timbre
    copied, prosody flat. That failure is inaudible until you hear the render, so
    the API refuses to create an entry that would silently degrade.

    The wav is copied into assets/voices/refs/ and the registry stores a
    repo-relative path, so the project stays portable — an absolute path into a
    cache directory is exactly what broke voice synthesis before.
    """
    import re as _re

    import soundfile as sf

    if not _re.fullmatch(r"[A-Za-z0-9_-]+", req.key):
        raise HTTPException(422, "key must be [A-Za-z0-9_-]+")
    if req.key.startswith("_"):
        raise HTTPException(422, "keys starting with _ are reserved for metadata")

    src = Path(req.ref_audio).expanduser()
    if not src.is_file():
        raise HTTPException(404, f"reference audio not found: {src}")

    try:
        meta = sf.info(str(src))
    except Exception as exc:
        raise HTTPException(422, f"not a readable audio file: {exc}") from exc
    # Qwen3-TTS clones from a few seconds of speech. Too short and the timbre is
    # unstable; report it rather than let the user discover it in a render.
    if meta.duration < 4.0:
        raise HTTPException(
            422,
            f"reference is {meta.duration:.1f}s — too short for stable cloning "
            "(use at least 4s, ideally 8-20s of clean speech)",
        )

    voices_path = REPO / "assets" / "voices" / "voices.json"
    registry_data: Dict[str, Any] = {}
    if voices_path.is_file():
        registry_data = json.loads(voices_path.read_text(encoding="utf-8"))
    if req.key in registry_data:
        raise HTTPException(409, f"voice {req.key!r} already exists")

    refs_dir = REPO / "assets" / "voices" / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)
    dst = refs_dir / f"{req.key}_{int(meta.samplerate / 1000)}k{src.suffix}"
    if dst.resolve() != src.resolve():
        shutil.copy2(src, dst)

    registry_data[req.key] = {
        "ref_audio": str(dst.relative_to(REPO)).replace("\\", "/"),
        "ref_text": req.ref_text.strip(),
        "lang": req.lang,
        "notes": req.notes or f"added via panel ({meta.duration:.1f}s, {meta.samplerate}Hz)",
    }
    voices_path.write_text(
        json.dumps(registry_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # If a synthesis runtime is loaded in this process, refresh its lazy registry;
    # voice management itself must remain available when that optional runtime is off.
    loaded_tts = sys.modules.get("msf.skills_bridge.qwen3_tts")
    if loaded_tts is not None:
        loaded_tts._VOICES_CACHE = None
    return {
        "key": req.key,
        "ref_audio": registry_data[req.key]["ref_audio"],
        "duration_sec": round(meta.duration, 2),
        "sample_rate": meta.samplerate,
        "mode": "icl",
        "icl": True,
    }


_VOICE_UPLOAD_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"}
_VOICE_UPLOAD_MAX_BYTES = 48 * 1024 * 1024


@app.post("/api/voices/upload")
async def api_upload_voice_reference(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Stage one local audio file for the Voice Lab workflow.

    The panel is explicitly localhost-only. The endpoint still stores uploads only
    in panel cache, applies a size and extension gate, and never auto-registers a
    voice; quality measurement, transcript review and explicit registration remain
    separate operator actions.
    """
    original_name = Path(file.filename or "reference.wav").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in _VOICE_UPLOAD_EXTENSIONS:
        raise HTTPException(422, f"unsupported audio format {suffix or '(none)'}")
    upload_dir = CACHE / "voice_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    staged = upload_dir / f"{uuid.uuid4().hex}{suffix}"
    total = 0
    try:
        with staged.open("wb") as handle:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > _VOICE_UPLOAD_MAX_BYTES:
                    raise HTTPException(413, "audio file exceeds 48 MB limit")
                handle.write(chunk)
    except HTTPException:
        staged.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    if total == 0:
        staged.unlink(missing_ok=True)
        raise HTTPException(422, "empty audio file")
    return {
        "path": str(staged),
        "original_name": original_name,
        "bytes": total,
        "next_step": "measure the staged file before preparation or registration",
    }


@app.get("/api/studio/projects/{project_id}/media")
def api_list_project_media(project_id: str) -> Dict[str, Any]:
    """Typed project media available for deliberate storyboard binding."""
    from msf.studio.project_resources import ProjectResourceError, list_media

    try:
        items = list_media(project_id)
    except ProjectResourceError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"project_id": project_id, "items": [item.model_dump(mode="json") for item in items]}


@app.post("/api/studio/projects/{project_id}/media/upload")
async def api_upload_project_media(
    project_id: str,
    file: UploadFile = File(...),
    role: str = Form("supporting_image"),
    caption: str = Form(""),
) -> Dict[str, Any]:
    """Stage one media file then register it as a typed local project asset.

    Drag-and-drop uses this route too. A selected role is required at upload time so
    the agent receives an editorial instruction rather than a mystery filename.
    """
    from msf.studio.project_resources import (
        ProjectResourceError,
        media_kind,
        prepare_staged_audio,
        register_staged_media,
    )

    original_name = Path(file.filename or "media.bin").name
    try:
        media_kind(original_name)
    except ProjectResourceError as exc:
        await file.close()
        raise HTTPException(422, str(exc)) from exc
    staged_dir = CACHE / "project_media_uploads"
    staged = staged_dir / f"{uuid.uuid4().hex}{Path(original_name).suffix.lower()}"
    total = 0
    try:
        staged_dir.mkdir(parents=True, exist_ok=True)
        with staged.open("wb") as handle:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > 250 * 1024 * 1024:
                    raise HTTPException(413, "media file exceeds 250 MB limit")
                handle.write(chunk)
        if total == 0:
            raise HTTPException(422, "media file is empty")
        staged, stored_name, audio_report = prepare_staged_audio(staged, original_name, role)
        asset = register_staged_media(project_id, staged, stored_name, role, caption)
    except HTTPException:
        staged.unlink(missing_ok=True)
        raise
    except ProjectResourceError as exc:
        staged.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc
    finally:
        await file.close()
    return {"asset": asset.model_dump(mode="json"), "audio_standardisation": audio_report, "next_step": "Assign this resource to a compatible scene before approving the run."}


@app.get("/api/studio/projects/{project_id}/media/{asset_id}")
def api_project_media_file(project_id: str, asset_id: str) -> FileResponse:
    """Serve one asset only after project/id validation; never accepts a file path."""
    from msf.studio.project_resources import ProjectResourceError, find_media

    try:
        asset, path = find_media(project_id, asset_id)
    except ProjectResourceError as exc:
        raise HTTPException(404, str(exc)) from exc
    return FileResponse(path, media_type=asset.mime_type, filename=asset.display_name)


@app.delete("/api/studio/projects/{project_id}/media/{asset_id}")
def api_delete_project_media(project_id: str, asset_id: str) -> Dict[str, Any]:
    from msf.studio.project_resources import ProjectResourceError, remove_media

    try:
        remove_media(project_id, asset_id)
    except ProjectResourceError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"removed": asset_id}


class PinnedSourcePayload(BaseModel):
    url: str = Field(..., min_length=12, max_length=2048)
    mode: str = Field("required", max_length=32)
    reason: str = Field(..., min_length=3, max_length=240)


@app.get("/api/studio/projects/{project_id}/sources")
def api_list_pinned_sources(project_id: str) -> Dict[str, Any]:
    from msf.studio.project_resources import ProjectResourceError, list_pinned_sources

    try:
        sources = list_pinned_sources(project_id)
    except ProjectResourceError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"project_id": project_id, "items": [item.model_dump(mode="json") for item in sources]}


@app.post("/api/studio/projects/{project_id}/sources")
def api_add_pinned_source(project_id: str, payload: PinnedSourcePayload) -> Dict[str, Any]:
    from msf.studio.project_resources import ProjectResourceError, add_pinned_source

    try:
        source = add_pinned_source(project_id, payload.url, payload.mode, payload.reason)
    except ProjectResourceError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"source": source.model_dump(mode="json")}


@app.delete("/api/studio/projects/{project_id}/sources/{source_id}")
def api_delete_pinned_source(project_id: str, source_id: str) -> Dict[str, Any]:
    from msf.studio.project_resources import ProjectResourceError, remove_pinned_source

    try:
        remove_pinned_source(project_id, source_id)
    except ProjectResourceError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"removed": source_id}


class VoiceSourceRequest(BaseModel):
    """An operator-provided local path or a path staged through Voice Lab upload."""

    path: str = Field(..., min_length=1)


@app.post("/api/voices/measure")
def api_voice_measure(req: VoiceSourceRequest) -> Dict[str, Any]:
    """Measure a candidate reference and report findings — no modification.

    Runs before anything is registered so a bad reference is caught here rather
    than in a finished render. Every finding is derived from a measured number
    (SNR, clipping, silence, sample rate), not from a guess about the file.
    """
    from msf.audio import voice_prep

    src = Path(req.path).expanduser()
    if not src.is_file():
        raise HTTPException(404, f"no such audio file: {src}")
    try:
        stats = voice_prep.measure(src)
    except Exception as exc:
        raise HTTPException(422, f"cannot measure {src.name}: {exc}") from exc

    findings = voice_prep.review(stats)
    return {
        "path": str(src),
        "stats": stats.to_dict(),
        "findings": findings,
        # "usable" means no error-level finding. Warnings are reported and allowed:
        # a reference can be imperfect and still work, and refusing everything short
        # of a studio booth would just push the operator to bypass the check.
        "usable": not any(f["level"] == "error" for f in findings),
        "recommend_denoise": stats.snr_db < 40,
        "recommend_trim": max(stats.silence_lead_sec, stats.silence_tail_sec) > 0.5,
    }


class VoicePrepareRequest(VoiceSourceRequest):
    denoise: bool = False
    trim_silence: bool = True
    normalize: bool = True
    # Hard cap 24: past nr=20 the measured sibilant energy drops below the clean
    # source (s/sh get eaten) while SNR keeps "improving", so a higher number would
    # look better on paper and sound worse.
    denoise_strength: int = Field(14, ge=1, le=24)
    # Where to write. None = alongside the source as <stem>_prepped24k.wav.
    out_path: Optional[str] = None


@app.post("/api/voices/prepare")
def api_voice_prepare(req: VoicePrepareRequest) -> Dict[str, Any]:
    """Clean a reference to 24 kHz mono and report before/after numbers.

    Chain is highpass -> afftdn -> trim -> normalize, with the denoiser's noise
    floor MEASURED from the clip rather than hardcoded (a fixed nf made the
    strength control a no-op). Returns both measurements so the operator can see
    what changed instead of trusting the word "prepared".
    """
    from msf.audio import voice_prep

    src = Path(req.path).expanduser()
    if not src.is_file():
        raise HTTPException(404, f"no such audio file: {src}")
    if not shutil.which("ffmpeg"):
        raise HTTPException(503, "ffmpeg not found — cannot process audio")

    if req.out_path:
        dst = Path(req.out_path).expanduser()
    else:
        dst = src.with_name(f"{src.stem}_prepped{voice_prep.TARGET_SR // 1000}k.wav")
    if dst.resolve() == src.resolve():
        raise HTTPException(422, "out_path must differ from the source file")

    try:
        res = voice_prep.prepare(
            src, dst,
            denoise=req.denoise,
            trim_silence=req.trim_silence,
            normalize=req.normalize,
            denoise_strength=req.denoise_strength,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc:
        # Includes the guard that refuses to return a clip the silence threshold
        # ate — that must not be reported as a success.
        raise HTTPException(500, str(exc)) from exc

    return {
        "out_path": res.out_path,
        "applied": res.applied,
        "before": res.before,
        "after": res.after,
        "findings": res.findings,
        "snr_gain_db": round(res.after["snr_db"] - res.before["snr_db"], 1),
        "next_step": "POST /api/voices/transcribe, proofread, then POST /api/voices",
    }


class VoiceTranscribeRequest(VoiceSourceRequest):
    language: str = "ru"


@app.post("/api/voices/transcribe")
def api_voice_transcribe(req: VoiceTranscribeRequest) -> Dict[str, Any]:
    """Transcribe a reference with Whisper so ref_text can be filled in.

    The transcript is returned for EDITING, never auto-saved: measured word
    agreement against a human transcript was 97.7%, which is excellent and still
    not exact, and ICL aligns the audio to whatever text it is handed. A wrong
    ref_text degrades cloning silently.
    """
    from msf.audio import voice_prep

    src = Path(req.path).expanduser()
    if not src.is_file():
        raise HTTPException(404, f"no such audio file: {src}")
    try:
        res = voice_prep.transcribe(src, language=req.language)
    except ImportError as exc:
        raise HTTPException(503, f"faster-whisper unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(500, f"transcription failed: {exc}") from exc
    return {"path": str(src), **res}


@app.delete("/api/voices/{key}")
def api_delete_voice(key: str) -> Dict[str, Any]:
    """Remove a voice from the registry. The wav file is left on disk."""
    from msf.config import MSFConfig

    if key == MSFConfig().tts.speaker:
        raise HTTPException(409, f"{key!r} is the configured default voice and cannot be removed here.")
    voices_path = REPO / "assets" / "voices" / "voices.json"
    data = json.loads(voices_path.read_text(encoding="utf-8")) if voices_path.is_file() else {}
    if key not in data:
        raise HTTPException(404, f"unknown voice {key!r}")
    data.pop(key)
    voices_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    loaded_tts = sys.modules.get("msf.skills_bridge.qwen3_tts")
    if loaded_tts is not None:
        loaded_tts._VOICES_CACHE = None
    return {"removed": key}


class RunRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=400)
    text: Optional[str] = None
    preset: str = "HeroKinetic"
    voice: Optional[str] = None
    scenes: int = Field(4, ge=1, le=20)
    agent_level: int = Field(3, ge=1, le=5)
    research: bool = False


@app.post("/api/graph/run")
def api_graph_run(req: RunRequest) -> Dict[str, Any]:
    """Start a pipeline run as a subprocess and return its id.

    A SUBPROCESS, not a thread: the graph loads a 1.7B TTS model onto CUDA and
    shells out to Remotion and ffmpeg. In-process it would block the event loop
    for minutes and a crash would take the panel down with it.
    """
    from msf import registry

    if req.preset not in registry.load_registry():
        raise HTTPException(404, f"unknown preset {req.preset!r}")
    if req.voice:
        from msf.skills_bridge.qwen3_tts import load_voices

        if req.voice not in load_voices():
            raise HTTPException(404, f"unknown voice {req.voice!r}")

    run_id = uuid.uuid4().hex[:12]
    payload = {
        "topic": req.topic,
        "text": req.text,
        "preset": req.preset,
        "voice": req.voice,
        "scenes": req.scenes,
        "agent_level": req.agent_level,
        "research": req.research,
        "run_id": run_id,
    }
    job = CACHE / "runs"
    job.mkdir(parents=True, exist_ok=True)
    job_file = job / f"{run_id}.json"
    job_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    runner = PANEL_DIR / "run_job.py"
    proc = subprocess.Popen(
        [sys.executable, str(runner), str(job_file)],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    RUNS[run_id] = Run(run_id=run_id, topic=req.topic, started=time.time(), proc=proc)
    _start_reader(RUNS[run_id])
    return {"run_id": run_id, "status": "running"}


@app.post("/api/runs/{run_id}/kill")
def api_kill_run(run_id: str) -> Dict[str, Any]:
    r = RUNS.get(run_id)
    if not r:
        raise HTTPException(404, "unknown run")
    if r.proc and r.proc.poll() is None:
        r.proc.terminate()
        with r.lock:
            r.status = "killed"
    return {"run_id": run_id, "status": r.status}


# -------------------------------------------------------------- Studio v2 API
# These endpoints use the same application-layer contracts as MCP. They are
# deliberately local-only because a render approval can consume GPU/CPU and the
# legacy panel has no authentication. The UI must not bypass these gates.
class StudioResearchPayload(BaseModel):
    research: Dict[str, Any]


class StudioStoryboardPayload(BaseModel):
    storyboard: Dict[str, Any]
    research: Optional[Dict[str, Any]] = None
    tier: str = "preset"


class StudioResearchToScriptPayload(BaseModel):
    topic: str = Field(..., min_length=3, max_length=400)
    audience: str = Field("широкая русскоязычная аудитория", min_length=3, max_length=180)
    cta_handle: str = Field("@llm_hubs", min_length=2, max_length=80)
    cta_asset: str = Field("готовый чек-лист и ссылки на источники", min_length=3, max_length=240)
    style_family: Optional[str] = Field(None, max_length=80)
    release_topic: bool = False
    content_archetype: str = "auto"
    community_proof_mode: str = "off"
    community_platforms: list[str] = Field(default_factory=lambda: ["youtube", "x", "reddit"], max_length=3)
    max_community_leads: int = Field(3, ge=0, le=5)
    provider: str = "duckduckgo"
    max_queries: int = Field(4, ge=1, le=4)
    max_sources: int = Field(8, ge=2, le=12)
    project_id: str = Field("default", min_length=1, max_length=120)
    pinned_source_ids: list[str] = Field(default_factory=list, max_length=12)
    comparison_mode: str = "none"
    comparison_models: list[str] = Field(default_factory=list, max_length=3)
    visual_evidence_mode: Optional[str] = None
    require_observed_comparison: bool = False


_CONTROL_ROOM_NODES = [
    {"id": "gate_check", "label": "Input gate", "title": "Проверка входа", "description": "Проверяет ограничения запуска и обязательные параметры.", "editable_instruction": False},
    {"id": "deep_research", "label": "Research", "title": "Исследование", "description": "Собирает и проверяет публичные источники перед factual narration.", "editable_instruction": True},
    {"id": "script_split", "label": "Script", "title": "Сценарий", "description": "Собирает hook, narrative arc и CTA из проверенного brief.", "editable_instruction": True},
    {"id": "voice_synthesis", "label": "Voice", "title": "Озвучка", "description": "Готовит голосовые дорожки готовых сцен.", "editable_instruction": False},
    {"id": "soundtrack", "label": "Sound", "title": "Звук", "description": "Сводит музыку, SFX и ducking.", "editable_instruction": False},
    {"id": "build_spec", "label": "Spec", "title": "VideoSpec", "description": "Проверяет сцены, style contract и renderer inputs.", "editable_instruction": False},
    {"id": "render", "label": "Render", "title": "Render", "description": "Remotion рендерит цельную композицию.", "editable_instruction": False},
    {"id": "master_audio", "label": "Master", "title": "Мастеринг", "description": "Нормализует и финализирует аудио.", "editable_instruction": False},
    {"id": "qa", "label": "QA", "title": "QA", "description": "Проверяет длительность, кадры, звук и итоговый файл.", "editable_instruction": False},
    {"id": "repair", "label": "Repair", "title": "Repair", "description": "Разрешённая repair-ветка после неуспешного QA.", "editable_instruction": False},
]
_CONTROL_ROOM_EDGES = [
    ["gate_check", "deep_research"], ["deep_research", "script_split"], ["script_split", "voice_synthesis"],
    ["voice_synthesis", "soundtrack"], ["soundtrack", "build_spec"], ["build_spec", "render"],
    ["render", "master_audio"], ["master_audio", "qa"], ["qa", "repair"], ["repair", "render"],
]


class StudioDraftPatchPayload(BaseModel):
    request_patch: Dict[str, Any] = Field(default_factory=dict)
    operator_overrides: Dict[str, str] = Field(default_factory=dict, max_length=2)


class StudioRunPayload(BaseModel):
    topic: str = Field(..., min_length=3, max_length=400)
    preset: str = "HeroKinetic"
    style: Optional[str] = None
    style_config: Optional[Dict[str, Any]] = None
    project_id: str = "default"
    storyboard_id: Optional[str] = None
    # Browser clients submit project IDs only. API resolves them to immutable
    # ProjectMedia/PinnedResearchSource snapshots before the draft is persisted.
    media_asset_ids: list[str] = Field(default_factory=list, max_length=24)
    pinned_source_ids: list[str] = Field(default_factory=list, max_length=12)
    research: bool = False
    music: bool = True
    sfx: bool = True
    voice: Optional[str] = None
    agent_level: int = Field(3, ge=1, le=5)


class StudioApprovalPayload(BaseModel):
    approved: bool = False


class StudioSettingsPatchPayload(BaseModel):
    """Safe defaults for drafts; these never override an approved run."""

    default_voice: Optional[str] = Field(default=None, max_length=120)
    default_style: Optional[str] = Field(default=None, max_length=120)
    default_agent_level: Optional[int] = Field(default=None, ge=1, le=5)
    default_research: Optional[bool] = None
    default_music: Optional[bool] = None
    default_sfx: Optional[bool] = None
    default_content_archetype: Optional[str] = Field(default=None, pattern=r"^(auto|release|comparison|how_to|case_study|cost_saving|incident|myth_fact|explainer|trend)$")
    default_audience: Optional[str] = Field(default=None, min_length=3, max_length=180)
    default_cta_handle: Optional[str] = Field(default=None, min_length=2, max_length=80)
    default_cta_asset: Optional[str] = Field(default=None, min_length=3, max_length=240)
    default_research_provider: Optional[str] = Field(default=None, pattern=r"^(duckduckgo|searxng)$")
    default_max_queries: Optional[int] = Field(default=None, ge=1, le=4)
    default_max_sources: Optional[int] = Field(default=None, ge=2, le=12)
    default_community_proof_mode: Optional[str] = Field(default=None, pattern=r"^(off|discover)$")
    default_comparison_mode: Optional[str] = Field(default=None, pattern=r"^(none|observed|proposed)$")
    default_comparison_models: Optional[list[str]] = Field(default=None, max_length=3)
    default_visual_evidence_mode: Optional[str] = Field(default=None, pattern=r"^(code_test|ui_build|game_build|data_viz|research_answer|incident|safety_failure)$")
    default_require_observed_comparison: Optional[bool] = None
    default_duration_seconds: Optional[int] = Field(default=None, ge=10, le=180)
    default_fps: Optional[Literal[24, 25, 30, 60]] = None
    default_music_volume: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    default_sfx_volume: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    default_auto_subtitles: Optional[bool] = None


def _studio_tier(value: str):
    from msf.studio.contracts import CapabilityTier
    try:
        return CapabilityTier(value)
    except ValueError as exc:
        raise HTTPException(422, f"unknown Studio capability tier: {value!r}") from exc


@app.get("/api/studio/settings")
def api_studio_settings() -> Dict[str, Any]:
    """Operator defaults and safe runtime facts for the Studio Settings screen."""
    from msf.config import MSFConfig
    from msf.studio.operator_settings import load

    settings = load()
    voices = _local_voice_catalog()[1]
    usable_voice_keys = {item["key"] for item in voices if item.get("usable")}
    if settings["default_voice"] is None or settings["default_voice"] not in usable_voice_keys:
        settings["default_voice"] = MSFConfig().tts.speaker
    return {
        "settings": settings,
        "available_voice_keys": [item["key"] for item in voices],
        "runtime": {
            "render": {"width": MSFConfig().render.width, "height": MSFConfig().render.height, "fps": MSFConfig().render.fps},
            "audio": {"target_lufs": MSFConfig().audio.target_lufs, "sample_rate": MSFConfig().audio.sample_rate},
            "storage": "local disk + SQLite run index",
        },
    }


@app.patch("/api/studio/settings")
def api_patch_studio_settings(payload: StudioSettingsPatchPayload) -> Dict[str, Any]:
    """Update only non-secret defaults that are applied to future run drafts."""
    from msf.studio.operator_settings import save

    patch = payload.model_dump(exclude_unset=True)
    if "default_voice" in patch and patch["default_voice"] is not None:
        if patch["default_voice"] not in {item["key"] for item in _local_voice_catalog()[1]}:
            raise HTTPException(422, "default_voice must be an existing voice key")
    try:
        return {"settings": save(patch)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/studio/catalog")
def api_studio_catalog(
    query: str = "",
    intents: str = "",
    category: Optional[str] = None,
    tier: str = "preset",
    limit: int = 30,
    offset: int = 0,
) -> Dict[str, Any]:
    """Live capability-filtered scene discovery for the Studio dashboard."""
    from msf.studio.catalog import search_scenes
    selected = _studio_tier(tier)
    tags = [item.strip() for item in intents.split(",") if item.strip()]
    result = search_scenes(
        query, intent_tags=tags or None, category=category, tier=selected,
        limit=limit, offset=offset,
    )
    return result.model_dump(mode="json")


@app.get("/api/studio/styles")
def api_studio_styles() -> Dict[str, Any]:
    """Named visual families plus safe operator customisation tokens."""
    from msf.studio.style_catalog import style_catalog_payload
    return style_catalog_payload()


@app.get("/api/studio/sound-design")
def api_studio_sound_design() -> Dict[str, Any]:
    """Stable semantic audio recipes; the UI never invents SFX identifiers."""
    from msf.studio.sound_design import all_recipes
    return {"items": [item.__dict__ for item in all_recipes()]}


@app.post("/api/studio/research-to-script")
def api_studio_research_to_script(payload: StudioResearchToScriptPayload) -> Dict[str, Any]:
    """Research a topic, validate linked evidence and return a Russian editable storyboard.

    This endpoint is deliberately separate from render preparation: the caller
    receives the evidence, topic plan, review-only community leads and script first,
    then can edit/validate/approve a render through the existing controlled lifecycle.
    """
    from pydantic import ValidationError
    from msf.studio.contracts import ResearchToScriptRequest
    from msf.studio.project_resources import ProjectResourceError, list_pinned_sources
    from msf.studio.research_to_script import ResearchToScriptError, ResearchToScriptWorkflow
    try:
        source_by_id = {item.source_id: item for item in list_pinned_sources(payload.project_id)}
        missing = [source_id for source_id in payload.pinned_source_ids if source_id not in source_by_id]
        if missing:
            raise ValueError(f"unknown pinned source IDs: {', '.join(missing)}")
        request_payload = payload.model_dump(exclude={"pinned_source_ids"})
        request_payload["pinned_sources"] = [source_by_id[source_id].model_dump(mode="json") for source_id in payload.pinned_source_ids]
        request = ResearchToScriptRequest.model_validate(request_payload)
        result = ResearchToScriptWorkflow().run(request)
    except (ValidationError, ResearchToScriptError, ProjectResourceError, ValueError) as exc:
        raise HTTPException(422, f"research-to-script failed: {exc}") from exc
    return result.model_dump(mode="json")


@app.post("/api/studio/research/validate")
def api_studio_validate_research(payload: StudioResearchPayload) -> Dict[str, Any]:
    from pydantic import ValidationError
    from msf.studio.contracts import ResearchPack
    from msf.studio.research import ResearchQualityError, validate_research_pack
    try:
        research = ResearchPack.model_validate(payload.research)
        warnings = validate_research_pack(research)
    except (ValidationError, ResearchQualityError, ValueError) as exc:
        raise HTTPException(422, f"research validation failed: {exc}") from exc
    return {"valid": not warnings, "research_id": research.research_id, "warnings": warnings}


@app.post("/api/studio/storyboards/validate")
def api_studio_validate_storyboard(payload: StudioStoryboardPayload) -> Dict[str, Any]:
    from pydantic import ValidationError
    from msf.studio.contracts import ResearchPack, StoryboardDraft
    from msf.studio.storyboard import StoryboardValidator
    try:
        draft = StoryboardDraft.model_validate(payload.storyboard)
        research = ResearchPack.model_validate(payload.research) if payload.research else None
    except ValidationError as exc:
        raise HTTPException(422, f"invalid Studio contract: {exc}") from exc
    result = StoryboardValidator(tier=_studio_tier(payload.tier)).validate(draft, research=research)
    return result.model_dump(mode="json")


@app.post("/api/studio/storyboards/save")
def api_studio_save_storyboard(payload: StudioStoryboardPayload) -> Dict[str, Any]:
    """Save only a validated local storyboard; no render is started here."""
    from pydantic import ValidationError
    from msf.studio.contracts import ResearchPack, StoryboardDraft
    from msf.studio.storyboard import StoryboardNotFoundError, StoryboardStore, StoryboardValidator
    try:
        draft = StoryboardDraft.model_validate(payload.storyboard)
        research = ResearchPack.model_validate(payload.research) if payload.research else None
    except ValidationError as exc:
        raise HTTPException(422, f"invalid Studio contract: {exc}") from exc
    validation = StoryboardValidator(tier=_studio_tier(payload.tier)).validate(draft, research=research)
    if not validation.valid:
        raise HTTPException(422, detail={"message": "storyboard validation failed", "validation": validation.model_dump(mode="json")})
    store = StoryboardStore()
    try:
        stored = store.get(draft.draft_id)
    except StoryboardNotFoundError:
        saved = store.create(draft)
    else:
        saved = store.save(draft.model_copy(update={"revision": stored.revision + 1}))
    return {"saved": True, "storyboard": saved.model_dump(mode="json"), "validation": validation.model_dump(mode="json")}


@app.post("/api/studio/runs/prepare")
def api_studio_prepare_run(payload: StudioRunPayload) -> Dict[str, Any]:
    """Create a non-approved run draft. A separate explicit action must start it."""
    from pydantic import ValidationError
    from msf.studio.catalog import get_scene
    from msf.studio.contracts import CapabilityTier, RunRequest
    from msf.studio.project_resources import ProjectResourceError, find_media, list_pinned_sources
    from msf.studio.runs import StudioRunService
    try:
        get_scene(payload.preset, tier=CapabilityTier.PRESET)
        media_assets = [find_media(payload.project_id, asset_id)[0] for asset_id in payload.media_asset_ids]
        all_sources = {item.source_id: item for item in list_pinned_sources(payload.project_id)}
        missing_sources = [source_id for source_id in payload.pinned_source_ids if source_id not in all_sources]
        if missing_sources:
            raise ValueError(f"unknown pinned source IDs: {', '.join(missing_sources)}")
        request = RunRequest(
            project_id=payload.project_id,
            storyboard_id=payload.storyboard_id,
            topic=payload.topic,
            preset=payload.preset,
            style=payload.style,
            style_config=payload.style_config,
            media_assets=media_assets,
            pinned_sources=[all_sources[source_id] for source_id in payload.pinned_source_ids],
            research=payload.research,
            music=payload.music,
            sfx=payload.sfx,
            voice=payload.voice,
            agent_level=payload.agent_level,
            approved=False,
        )
    except (ValidationError, KeyError, ValueError, ProjectResourceError) as exc:
        raise HTTPException(422, f"cannot prepare Studio run: {exc}") from exc
    snapshot = StudioRunService().create_run(request)
    return {"request": request.model_dump(mode="json"), "run": snapshot.model_dump(mode="json"), "next_step": "Validate and explicitly approve through the local operator dashboard."}


@app.get("/api/studio/control-room/graph")
def api_studio_control_room_graph() -> Dict[str, Any]:
    """Return the exact canonical worker graph used by the local Control Room."""
    return {"nodes": _CONTROL_ROOM_NODES, "edges": _CONTROL_ROOM_EDGES, "transport": "cursor_polling", "policy": "operational telemetry only"}


@app.get("/api/studio/runs")
def api_studio_runs(limit: int = 80, status: Optional[str] = None) -> Dict[str, Any]:
    """Return the persistent local run archive, optionally filtered by lifecycle status."""
    from msf.studio.contracts import RunStatus
    from msf.studio.runs import StudioRunService

    if status and status not in {item.value for item in RunStatus}:
        raise HTTPException(422, f"unknown Studio run status: {status!r}")
    items = StudioRunService().list_runs(limit=limit, status=status)
    return {"items": items, "total": len(items), "storage": "sqlite index + per-run files"}


@app.get("/api/studio/runs/{run_id}/control")
def api_studio_run_control(run_id: str) -> Dict[str, Any]:
    """Return snapshot plus editable draft inputs; never includes hidden reasoning."""
    from msf.studio.runs import RunNotFoundError, StudioRunService
    service = StudioRunService()
    try:
        return {"snapshot": service.get_snapshot(run_id).model_dump(mode="json"), "request": service.get_request(run_id).model_dump(mode="json")}
    except RunNotFoundError as exc:
        raise HTTPException(404, "Studio run not found") from exc


@app.patch("/api/studio/runs/{run_id}/draft")
def api_studio_patch_draft(run_id: str, payload: StudioDraftPatchPayload) -> Dict[str, Any]:
    """Apply whitelisted brief/instruction changes only before explicit approval."""
    from msf.studio.runs import RunNotFoundError, RunStateError, StudioRunService
    try:
        snapshot, request = StudioRunService().patch_draft(
            run_id, request_patch=payload.request_patch, operator_overrides=payload.operator_overrides,
        )
        return {"snapshot": snapshot.model_dump(mode="json"), "request": request.model_dump(mode="json")}
    except RunNotFoundError as exc:
        raise HTTPException(404, "Studio run not found") from exc
    except (RunStateError, ValueError) as exc:
        raise HTTPException(409, f"cannot edit Studio draft: {exc}") from exc


@app.post("/api/studio/runs/{run_id}/cancel")
def api_studio_cancel_run(run_id: str) -> Dict[str, Any]:
    """Cancel an active local worker; completed runs remain immutable."""
    from msf.studio.runs import RunNotFoundError, StudioRunService
    try:
        snapshot = StudioRunService().cancel(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(404, "Studio run not found") from exc
    return {"run": snapshot.model_dump(mode="json")}


@app.get("/api/studio/runs/{run_id}")
def api_studio_run_snapshot(run_id: str) -> Dict[str, Any]:
    from msf.studio.runs import RunNotFoundError, StudioRunService
    try:
        snapshot = StudioRunService().get_snapshot(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(404, "Studio run not found") from exc
    return snapshot.model_dump(mode="json")


@app.get("/api/studio/runs/{run_id}/timeline")
def api_studio_run_timeline(run_id: str, after_sequence: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Return operational timeline only; TraceStore redacts prompts and hidden reasoning."""
    from msf.studio.runs import RunNotFoundError, StudioRunService
    from msf.studio.tracing import TraceStore
    service = StudioRunService()
    try:
        snapshot = service.get_snapshot(run_id)
        events = service.events(run_id, after_sequence=max(0, after_sequence), limit=max(1, min(limit, 500)))
        traces = TraceStore(service._run_dir(run_id), run_id).read(limit=max(1, min(limit, 500)))
    except RunNotFoundError as exc:
        raise HTTPException(404, "Studio run not found") from exc
    return {"snapshot": snapshot.model_dump(mode="json"), "events": [item.model_dump(mode="json") for item in events], "traces": [item.model_dump(mode="json") for item in traces]}


@app.post("/api/studio/runs/{run_id}/approve-and-start")
def api_studio_approve_and_start(run_id: str, payload: StudioApprovalPayload) -> Dict[str, Any]:
    """Human-controlled launch endpoint. The UI must pass approved=true deliberately."""
    if not payload.approved:
        raise HTTPException(422, "set approved=true to start a Studio render worker")
    from msf.studio.contracts import RunRequest
    from msf.studio.runs import RunNotFoundError, RunStateError, StudioRunService
    service = StudioRunService()
    try:
        current = service.get_snapshot(run_id)
        request_path = service._request_path(run_id)
        request = RunRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
        # Preserve the original request fields while making the operator approval
        # explicit in the immutable request snapshot consumed by the worker.
        service._write_json(request_path, request.model_copy(update={"approved": True}).model_dump(mode="json"))
        validated = service.validate(run_id, valid=True)
        queued = service.queue(validated.run_id)
        started = service.start(queued.run_id)
    except (RunNotFoundError, RunStateError, ValueError) as exc:
        raise HTTPException(409, f"cannot start Studio run: {exc}") from exc
    return {"previous": current.model_dump(mode="json"), "run": started.model_dump(mode="json")}


# ---------------------------------------------------------------- static UI
@app.get("/studio", response_class=HTMLResponse)
def studio_dashboard() -> HTMLResponse:
    html = STATIC_DIR / "studio.html"
    if not html.is_file():
        raise HTTPException(500, f"Studio UI missing: {html}")
    return HTMLResponse(html.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)

def index() -> HTMLResponse:
    html = STATIC_DIR / "index.html"
    if not html.is_file():
        raise HTTPException(500, f"UI missing: {html}")
    return HTMLResponse(html.read_text(encoding="utf-8"))


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="MSF control panel")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    if args.host not in ("127.0.0.1", "localhost"):
        log.warning(
            "Binding %s exposes unauthenticated endpoints that run node/ffmpeg "
            "subprocesses and start renders. Do not do this on a shared network.",
            args.host,
        )

    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
