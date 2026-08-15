"""Declarative background-music and SFX choices for Studio scene manifests.

The module names only synthesizers already registered by ``msf.audio.music`` and
``msf.audio.sfx``.  It does not bundle third-party media, so a local-first install
remains reproducible and does not inherit unknown audio licenses.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class SfxCue:
    """A semantic cue placed relative to one scene's progress."""

    role: str
    sfx_id: str
    at_progress: float
    gain_db: float = -8.0


@dataclass(frozen=True)
class SoundDesignRecipe:
    scene_name: str
    music_bed: str
    music_gain_db: float
    cues: Tuple[SfxCue, ...]


DEFAULT_RECIPE = SoundDesignRecipe(
    scene_name="default",
    music_bed="minimal_pulse",
    music_gain_db=-28.0,
    cues=(SfxCue("scene_enter", "whoosh_short", 0.03, -12.0),),
)


RECIPES: Dict[str, SoundDesignRecipe] = {
    "HeroKinetic": SoundDesignRecipe(
        "HeroKinetic", "cinematic_build", -27.0,
        (SfxCue("intro_hit", "impact_soft", 0.08, -10.0), SfxCue("riser", "riser_short", 0.64, -15.0)),
    ),
    "QuoteCard": SoundDesignRecipe(
        "QuoteCard", "warm_keys", -30.0,
        (SfxCue("quote_reveal", "paper_slide", 0.12, -14.0),),
    ),
    "DecisionGrid": SoundDesignRecipe(
        "DecisionGrid", "focus_loop", -30.0,
        (SfxCue("choice_enter", "node_ping", 0.20, -16.0), SfxCue("choice_confirm", "success_chime", 0.76, -14.0)),
    ),
    "LlmHubsCTA": SoundDesignRecipe(
        "LlmHubsCTA", "hopeful_rise", -28.0,
        (SfxCue("brand_reveal", "impact_soft", 0.16, -14.0), SfxCue("subscribe", "success_chime", 0.72, -12.0)),
    ),
    "StepList": SoundDesignRecipe(
        "StepList", "clarity_steps", -29.0,
        (SfxCue("step_tick", "counter_tick", 0.19, -15.0), SfxCue("step_tick", "counter_tick", 0.43, -15.0), SfxCue("success_chime", "success_chime", 0.83, -13.0)),
    ),
    "BeforeAfter": SoundDesignRecipe(
        "BeforeAfter", "corporate_calm", -28.0,
        (SfxCue("before_enter", "whoosh_reverse", 0.09, -15.0), SfxCue("transformation", "whoosh_long", 0.48, -13.0), SfxCue("after_reveal", "success_chime", 0.66, -11.0)),
    ),
    "MetricTrend": SoundDesignRecipe(
        "MetricTrend", "data_spark", -28.0,
        (SfxCue("data_tick", "counter_tick", 0.28, -16.0), SfxCue("data_tick", "counter_tick", 0.48, -16.0), SfxCue("milestone_hit", "sting_up_major", 0.75, -12.0)),
    ),
    "TgChat": SoundDesignRecipe(
        "TgChat", "lofi_soft", -32.0,
        (SfxCue("message", "notify_ding", 0.26, -16.0), SfxCue("message", "send_swoosh", 0.60, -17.0)),
    ),
    "CodeReveal": SoundDesignRecipe(
        "CodeReveal", "tech_drift", -31.0,
        (SfxCue("typing", "keyboard_run", 0.20, -18.0), SfxCue("completion", "success_chime", 0.84, -14.0)),
    ),
    "StatCounter": SoundDesignRecipe(
        "StatCounter", "upbeat_clean", -29.0,
        (SfxCue("count_up", "counter_run", 0.28, -17.0), SfxCue("result", "impact_soft", 0.80, -12.0)),
    ),
    "FlowDiagram": SoundDesignRecipe(
        "FlowDiagram", "percussive_tick", -30.0,
        (SfxCue("node_ping", "node_ping", 0.24, -16.0), SfxCue("node_ping", "node_ping", 0.51, -16.0), SfxCue("node_ping", "node_ping", 0.77, -16.0)),
    ),
}


def recipe_for(scene_name: str) -> SoundDesignRecipe:
    """Return a stable default when a newly authored scene lacks a recipe."""
    return RECIPES.get(scene_name, DEFAULT_RECIPE)


def all_recipes() -> Iterable[SoundDesignRecipe]:
    return tuple(RECIPES[name] for name in sorted(RECIPES))
