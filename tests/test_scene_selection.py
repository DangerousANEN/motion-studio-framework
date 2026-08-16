from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from msf.studio.contracts import StoryboardDraft, StoryboardScene
from msf.studio.scene_selection import (
    SceneSelectionLedger,
    SceneSelectionPolicy,
    recent_project_presets,
)


def _scene(name: str, category: str, tags: list[str], *, three: bool = False):
    """A minimal catalog-compatible manifest for deterministic scoring tests."""
    return SimpleNamespace(
        name=name,
        category=category,
        intent_tags=tags,
        required_data_hints=[],
        data_driven=False,
        three=three,
    )


def test_diversity_selector_prefers_semantic_fit_without_repeating_visual_grammar() -> None:
    candidates = [
        _scene("FlowDiagram", "diagram", ["explainer", "workflow"]),
        _scene("QuoteCard", "narrative", ["evidence", "research"]),
        _scene("VideoEmbed", "media", ["explainer"]),
        _scene("LogoSculpture3D", "three", ["explainer"], three=True),
        _scene("TelegramChannelPost", "ui-mock", ["telegram", "cta"]),
    ]
    ledger = SceneSelectionLedger(policy=SceneSelectionPolicy(diversity="high"))

    picks = [ledger.choose(role, candidates) for role in ("explanation", "evidence", "explanation", "cta")]

    assert len(picks) == len(set(picks))
    assert ledger.category_counts["diagram"] == 1
    assert ledger.category_counts["narrative"] == 1
    assert len(ledger.category_counts) >= 3
    assert "scene diversity=high" in ledger.summary()


def test_recent_scene_history_penalizes_otherwise_exact_preset_match() -> None:
    candidates = [
        _scene("FlowDiagram", "diagram", ["explainer"]),
        _scene("VideoEmbed", "media", ["explainer"]),
    ]
    ledger = SceneSelectionLedger(
        policy=SceneSelectionPolicy(diversity="high", avoid_recent=True),
        recent_presets={"FlowDiagram"},
    )

    assert ledger.choose("explanation", candidates) == "VideoEmbed"


def test_recent_project_presets_reads_newest_matching_drafts_only(tmp_path: Path) -> None:
    older = StoryboardDraft(project_id="alpha", scenes=[StoryboardScene(preset="QuoteCard")])
    newer = StoryboardDraft(project_id="alpha", scenes=[StoryboardScene(preset="FlowDiagram")])
    other_project = StoryboardDraft(project_id="beta", scenes=[StoryboardScene(preset="VideoEmbed")])
    for index, draft in enumerate((older, newer, other_project)):
        (tmp_path / f"sb_{index}.json").write_text(draft.model_dump_json(), encoding="utf-8")

    # Files are sorted by their persisted timestamps. Window=2 includes both alpha
    # drafts and excludes another project regardless of its timestamp.
    assert recent_project_presets("alpha", window=2, root=tmp_path) == {"QuoteCard", "FlowDiagram"}
    assert recent_project_presets("beta", window=2, root=tmp_path) == {"VideoEmbed"}
