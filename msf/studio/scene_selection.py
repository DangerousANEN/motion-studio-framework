"""Deterministic, explainable scene selection for MSF storyboards.

The selector intentionally treats semantic fit as a constraint, not an excuse to
repeat the same visual grammar. It keeps weak agents inside catalog contracts
while giving strong agents a readable score breakdown for every chosen preset.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Iterable, Literal, Mapping

from .contracts import CapabilityTier, SceneManifest, StoryboardDraft

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_STORYBOARD_ROOT = _REPO / "output" / "studio" / "storyboards"

_ROLE_TAGS: dict[str, tuple[str, ...]] = {
    "hook": ("hook", "headline", "announcement", "retention", "chapter"),
    "evidence": ("evidence", "research", "sources", "quote", "metric", "result", "proof"),
    "proof": ("proof", "comparison", "benchmark", "metric", "result", "evidence"),
    "explanation": ("explainer", "explain", "definition", "workflow", "feature", "product"),
    "takeaway": ("decision", "routing", "tradeoff", "problem_solution", "how_to", "process", "checklist"),
    "cta": ("cta", "conversion", "channel_post", "telegram", "distribution", "social"),
}


@dataclass(frozen=True)
class SceneSelectionPolicy:
    """Tunable guardrails for catalog-first preset selection."""

    diversity: Literal["balanced", "high", "strict"] = "high"
    avoid_recent: bool = True
    recent_window: int = 4
    max_three_scenes: int = 1
    max_same_category: int = 2

    @property
    def novelty_weight(self) -> int:
        return {"balanced": 6, "high": 12, "strict": 18}[self.diversity]

    @property
    def recent_penalty(self) -> int:
        return {"balanced": 18, "high": 42, "strict": 80}[self.diversity]


@dataclass(frozen=True)
class SelectionDecision:
    role: str
    preset: str
    category: str
    score: int
    reasons: tuple[str, ...]


@dataclass
class SceneSelectionLedger:
    policy: SceneSelectionPolicy
    recent_presets: set[str] = field(default_factory=set)
    used_presets: set[str] = field(default_factory=set)
    category_counts: Counter[str] = field(default_factory=Counter)
    decisions: list[SelectionDecision] = field(default_factory=list)

    def _score(self, manifest: SceneManifest, role: str) -> tuple[int, list[str]]:
        if manifest.name in self.used_presets:
            return (-10_000, ["already used in this storyboard"])
        if self.policy.avoid_recent and manifest.name in self.recent_presets:
            return (-self.policy.recent_penalty, ["used in recent project storyboard"])
        if manifest.category == "three" and self.category_counts["three"] >= self.policy.max_three_scenes:
            return (-1_000, ["3D budget reached"])
        if self.category_counts[manifest.category] >= self.policy.max_same_category:
            return (-900, ["category budget reached"])

        tags = {item.lower() for item in manifest.intent_tags}
        expected = set(_ROLE_TAGS.get(role, _ROLE_TAGS["explanation"]))
        matching = tags & expected
        score = len(matching) * 18
        reasons = [f"semantic tags: {', '.join(sorted(matching))}"] if matching else ["safe explainer fallback"]

        if self.category_counts[manifest.category] == 0:
            score += self.policy.novelty_weight
            reasons.append("new visual category")
        else:
            score -= self.category_counts[manifest.category] * 5
            reasons.append(f"category already used {self.category_counts[manifest.category]}×")

        # A non-data-driven scene is usable with plain copy. Data-driven scenes
        # without required fields have a renderer fallback and are deliberately
        # eligible to prevent the catalog collapsing to typography/narrative only.
        if manifest.data_driven and manifest.required_data_hints:
            score -= 4
            reasons.append("structured props required")
        if manifest.three:
            score += 2
            reasons.append("3D novelty")
        return score, reasons

    def choose(self, role: str, candidates: Iterable[SceneManifest]) -> str:
        ranked: list[tuple[int, str, SceneManifest, list[str]]] = []
        for manifest in candidates:
            score, reasons = self._score(manifest, role)
            if score > -900:
                ranked.append((score, manifest.name.lower(), manifest, reasons))
        if not ranked:
            # Controlled fallback: preserve uniqueness and semantic fit when every
            # category/recent budget is exhausted, but never reuse within a draft.
            for manifest in candidates:
                if manifest.name in self.used_presets:
                    continue
                score, reasons = self._score(manifest, role)
                if score > -10_000:
                    ranked.append((score, manifest.name.lower(), manifest, reasons + ["controlled budget fallback"]))
        if not ranked:
            raise ValueError(f"no catalog candidate for role {role!r}")
        ranked.sort(key=lambda item: (-item[0], item[1]))
        score, _, winner, reasons = ranked[0]
        self.used_presets.add(winner.name)
        self.category_counts[winner.category] += 1
        self.decisions.append(SelectionDecision(role=role, preset=winner.name, category=winner.category, score=score, reasons=tuple(reasons)))
        return winner.name

    def summary(self) -> str:
        categories = ", ".join(f"{key}:{value}" for key, value in sorted(self.category_counts.items())) or "none"
        picks = ", ".join(decision.preset for decision in self.decisions)
        return f"scene diversity={self.policy.diversity}; categories={categories}; presets={picks}"


def recent_project_presets(project_id: str, *, window: int = 4, root: Path | None = None) -> set[str]:
    """Read the newest persisted drafts for a project without raising on old/corrupt files."""
    base = Path(root or _DEFAULT_STORYBOARD_ROOT)
    if window <= 0 or not base.exists():
        return set()
    drafts: list[StoryboardDraft] = []
    for path in base.glob("sb_*.json"):
        try:
            draft = StoryboardDraft.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if draft.project_id == project_id:
            drafts.append(draft)
    drafts.sort(key=lambda draft: draft.updated_at, reverse=True)
    return {scene.preset for draft in drafts[:window] for scene in draft.scenes}


def policy_from_request(request: object) -> SceneSelectionPolicy:
    return SceneSelectionPolicy(
        diversity=getattr(request, "scene_diversity", "high"),
        avoid_recent=getattr(request, "avoid_recent_scenes", True),
        recent_window=getattr(request, "recent_scene_window", 4),
    )


__all__ = [
    "SceneSelectionLedger",
    "SceneSelectionPolicy",
    "SelectionDecision",
    "policy_from_request",
    "recent_project_presets",
]
