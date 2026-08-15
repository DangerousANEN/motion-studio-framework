"""Convert validated evidence-backed scripts into constrained Studio storyboards."""
from __future__ import annotations

from .contracts import AudioPolicy, ResearchPack, ScriptPlan, StoryboardDraft, StoryboardScene
from .script_planner import validate_script_plan


_INTENT_TO_PRESET = {
    "hook": "HeroKinetic",
    "explainer": "TypewriterSub",
    "evidence": "QuoteCard",
    "metric": "MetricTrend",
    "how_to": "StepList",
    "cta": "LlmHubsCTA",
}


def _scene_for_line(line_index: int, line, total: int) -> StoryboardScene:
    """Use only stable presets with an explicit safe fallback for weak agents."""
    preset = _INTENT_TO_PRESET.get(line.scene_intent, "TypewriterSub")
    if line.kind == "hook":
        preset = "HeroKinetic"
    elif line.kind == "cta":
        preset = "LlmHubsCTA"
    elif line.kind == "fact":
        # Numeric/data-driven presets require separately structured data. A bare
        # research sentence must stay on a text-safe evidence scene.
        preset = "QuoteCard"

    props: dict = {}
    if preset == "QuoteCard":
        props = {"text": line.narration, "author": "Источник — в описании"}
    elif preset == "TypewriterSub":
        props = {"text": line.narration}
    else:
        props = {"title": line.on_screen_text or line.narration}
    scene_title = (line.on_screen_text or line.narration[:80]) if preset == "HeroKinetic" else None
    scene_text = "" if preset == "HeroKinetic" else line.narration
    readable_chars = len(scene_title or "") + len(scene_text)
    return StoryboardScene(
        preset=preset,
        title=scene_title,
        text=scene_text,
        props=props,
        audio=AudioPolicy(mode="suggest"),
        evidence_claim_ids=line.evidence_claim_ids,
        duration_in_frames=max(120, min(720, readable_chars * 5 + 24)),
    )


def storyboard_from_script(plan: ScriptPlan, research: ResearchPack, project_id: str = "default") -> StoryboardDraft:
    """Create a conservative preset-only draft after evidence/script validation."""
    validate_script_plan(plan, research)
    scenes = [_scene_for_line(index, line, len(plan.lines)) for index, line in enumerate(plan.lines)]
    return StoryboardDraft(
        project_id=project_id,
        title=plan.title,
        language=plan.language,
        scenes=scenes,
        research_id=research.research_id,
        script_id=plan.script_id,
    )
