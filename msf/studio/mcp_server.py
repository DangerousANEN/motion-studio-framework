"""MSF Studio local MCP server.

The server exposes catalog discovery and safe application-layer operations to
agent clients. It deliberately does not expose arbitrary shell commands,
filesystem paths, model prompts, hidden reasoning, or an unaudited render
button. Rendering remains an explicit approved action in the Studio run service.

Run locally over stdio:
    python -m msf.studio.mcp_server
"""
from __future__ import annotations

import json
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from .catalog import all_scenes, get_scene, search_scenes
from .contracts import CapabilityTier, ResearchPack, RunRequest, StoryboardDraft
from .research import validate_research_pack
from .runs import RunNotFoundError, StudioRunService
from .sound_design import all_recipes, recipe_for
from .style_catalog import style_catalog_payload
from .storyboard import StoryboardStore, StoryboardValidator
from .tracing import TraceStore

MAX_JSON_CHARS = 250_000


def _tier(value: str) -> CapabilityTier:
    try:
        return CapabilityTier(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in CapabilityTier)
        raise ValueError(f"Unknown capability tier {value!r}. Choose one of: {allowed}.") from exc


def _decode_object(payload: str, label: str) -> dict[str, Any]:
    if not isinstance(payload, str) or not payload.strip():
        raise ValueError(f"{label} must be a non-empty JSON object string.")
    if len(payload) > MAX_JSON_CHARS:
        raise ValueError(f"{label} exceeds the {MAX_JSON_CHARS} character limit.")
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc.msg}.") from exc
    if not isinstance(decoded, dict):
        raise ValueError(f"{label} must decode to an object.")
    return decoded


def _dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(
        "MSF Studio",
        instructions=(
            "Use catalog tools before composing a video. Preset-tier agents must use "
            "only stable scenes returned by discovery. Validate a storyboard before a "
            "render run. Trace and event tools show observable progress only; they never "
            "contain hidden model reasoning or raw prompts."
        ),
    )
    run_service = StudioRunService()
    draft_store = StoryboardStore()

    @mcp.resource("msf://catalog/{tier}")
    def catalog_resource(tier: str = "preset") -> str:
        """Expose the live, capability-filtered scene catalog as JSON."""
        selected = _tier(tier)
        return json.dumps([_dump(scene) for scene in all_scenes(tier=selected)], ensure_ascii=False, indent=2)

    @mcp.resource("msf://sound-design")
    def sound_design_resource() -> str:
        """Expose declarative music/SFX recipes without downloading external audio."""
        return json.dumps([_dump(recipe) for recipe in all_recipes()], ensure_ascii=False, indent=2)

    @mcp.resource("msf://styles")
    def styles_resource() -> str:
        """Expose named visual families and allowlisted styleConfig controls."""
        return json.dumps(style_catalog_payload(), ensure_ascii=False, indent=2)

    @mcp.tool()
    def search_scene_catalog(
        query: str = "",
        intent_tags: Optional[list[str]] = None,
        category: Optional[str] = None,
        tier: str = "preset",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search stable scenes. Use it instead of guessing preset names or fields."""
        result = search_scenes(query, intent_tags=intent_tags, category=category, tier=_tier(tier), limit=limit)
        return _dump(result)

    @mcp.tool()
    def describe_scene(name: str, tier: str = "preset") -> dict[str, Any]:
        """Return a single live scene manifest, including required fields and audio roles."""
        try:
            return _dump(get_scene(name, tier=_tier(tier)))
        except KeyError as exc:
            return {"ok": False, "error": "scene.not_found", "message": f"Scene {name!r} is unavailable at this tier."}

    @mcp.tool()
    def list_style_families() -> dict[str, Any]:
        """Return visual families plus safe palette/background/glow/motion controls. Never invent CSS."""
        return style_catalog_payload()

    @mcp.tool()
    def suggest_sound_design(preset: str) -> dict[str, Any]:
        """Return a local procedural music/SFX recipe for a selected scene preset."""
        return _dump(recipe_for(preset))

    @mcp.tool()
    def validate_research_evidence(research_json: str) -> dict[str, Any]:
        """Fail closed on unsupported, stale, or improperly linked factual claims."""
        try:
            pack = ResearchPack.model_validate(_decode_object(research_json, "research_json"))
            warnings = validate_research_pack(pack)
            return {"ok": not warnings, "research_id": pack.research_id, "warnings": warnings}
        except (ValidationError, ValueError) as exc:
            return {"ok": False, "error": "research.invalid", "message": str(exc)}

    @mcp.tool()
    def validate_storyboard(
        storyboard_json: str,
        research_json: Optional[str] = None,
        tier: str = "preset",
    ) -> dict[str, Any]:
        """Validate a versioned storyboard against live catalog, readability and evidence gates."""
        try:
            draft = StoryboardDraft.model_validate(_decode_object(storyboard_json, "storyboard_json"))
            research = ResearchPack.model_validate(_decode_object(research_json, "research_json")) if research_json else None
            return _dump(StoryboardValidator(tier=_tier(tier)).validate(draft, research=research))
        except (ValidationError, ValueError) as exc:
            return {"draft_id": None, "valid": False, "error": "storyboard.invalid", "message": str(exc)}

    @mcp.tool()
    def save_storyboard_draft(storyboard_json: str, tier: str = "preset") -> dict[str, Any]:
        """Persist a local draft after catalog/readability validation. Does not start rendering."""
        try:
            draft = StoryboardDraft.model_validate(_decode_object(storyboard_json, "storyboard_json"))
            validator = StoryboardValidator(tier=_tier(tier))
            result = validator.validate(draft)
            if not result.valid:
                return {"ok": False, "saved": False, "validation": _dump(result)}
            saved = draft_store.create(draft) if draft.revision == 1 else draft_store.save(draft)
            return {"ok": True, "saved": True, "storyboard": _dump(saved), "validation": _dump(result)}
        except (ValidationError, ValueError, FileExistsError) as exc:
            return {"ok": False, "saved": False, "error": "storyboard.save_failed", "message": str(exc)}

    @mcp.tool()
    def prepare_render_run(
        topic: str,
        preset: str = "HeroKinetic",
        project_id: str = "default",
        storyboard_id: Optional[str] = None,
        research: bool = False,
        style: Optional[str] = None,
        style_config_json: Optional[str] = None,
        voice: Optional[str] = None,
        agent_level: int = 3,
    ) -> dict[str, Any]:
        """Create a render draft only. The service cannot start a worker without separate explicit approval."""
        try:
            # A preset-tier caller cannot create a run for a scene it cannot discover.
            get_scene(preset, tier=CapabilityTier.PRESET)
            style_config = _decode_object(style_config_json, "style_config_json") if style_config_json else None
            request = RunRequest(
                project_id=project_id,
                storyboard_id=storyboard_id,
                topic=topic,
                preset=preset,
                style=style,
                style_config=style_config,
                research=research,
                voice=voice,
                agent_level=agent_level,
                approved=False,
            )
            snapshot = run_service.create_run(request)
            return {"ok": True, "request": _dump(request), "run": _dump(snapshot), "next_step": "Validate in the Studio application, then approve and queue through a human-controlled surface."}
        except (ValidationError, ValueError, KeyError) as exc:
            return {"ok": False, "error": "run.prepare_failed", "message": str(exc)}

    @mcp.tool()
    def inspect_run(run_id: str, after_sequence: int = 0, limit: int = 100) -> dict[str, Any]:
        """Read a run snapshot and cursor-based operational events; no prompts or hidden thoughts are returned."""
        try:
            snapshot = run_service.get_snapshot(run_id)
            events = run_service.events(run_id, after_sequence=after_sequence, limit=max(1, min(limit, 500)))
            run_dir = run_service._run_dir(run_id)  # validated by get_snapshot; no client path enters this API.
            traces = TraceStore(run_dir, run_id).read(limit=max(1, min(limit, 500)))
            return {"ok": True, "snapshot": _dump(snapshot), "events": [_dump(event) for event in events], "traces": [_dump(span) for span in traces]}
        except RunNotFoundError:
            return {"ok": False, "error": "run.not_found", "message": "Unknown or invalid run ID."}

    @mcp.prompt()
    def preset_video_brief(topic: str, audience: str = "широкая русскоязычная аудитория") -> str:
        """Generate a catalog-first prompt template for a restricted preset-tier agent."""
        return (
            "Собери короткий видео-проект для аудитории: " + audience + ".\n"
            "Тема: " + topic + ".\n\n"
            "Сначала вызови search_scene_catalog, list_style_families и suggest_sound_design. Затем используй только "
            "manifest-driven stable presets. Если добавляешь факты, сначала представь ResearchPack "
            "и вызови validate_research_evidence; затем свяжи каждую factual сцену с evidence claim. "
            "Сохраняй только валидный storyboard и не вызывай непроверенный renderer-код."
        )

    return mcp


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run()
