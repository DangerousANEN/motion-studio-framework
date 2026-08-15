"""Storyboard drafts and strict pre-render validation for Studio v2."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from msf import registry
from msf.spec import FPS, READ_CHARS_PER_SEC

# The renderer parity contract fixes this lower bound at one second; the legacy
# spec keeps it as an invariant in validation code rather than a public constant.
MIN_DWELL_SECONDS = 1.0

from .catalog import get_scene
from .research import ResearchQualityError, allowed_claims
from .contracts import (
    CapabilityTier,
    Severity,
    ResearchPack,
    StoryboardDraft,
    ValidationDiagnostic,
    ValidationResult,
    utc_now,
)


_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_ROOT = _REPO / "output" / "studio" / "storyboards"


class StoryboardNotFoundError(KeyError):
    pass


class StoryboardStore:
    """Local-first versioned draft persistence with opaque IDs."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root or _DEFAULT_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, draft_id: str) -> Path:
        if not draft_id.startswith("sb_"):
            raise StoryboardNotFoundError(draft_id)
        return self.root / f"{draft_id}.json"

    def save(self, draft: StoryboardDraft) -> StoryboardDraft:
        draft = draft.model_copy(update={"updated_at": utc_now()})
        path = self._path(draft.draft_id)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(draft.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)
        return draft

    def create(self, draft: StoryboardDraft) -> StoryboardDraft:
        path = self._path(draft.draft_id)
        if path.exists():
            raise FileExistsError(draft.draft_id)
        return self.save(draft)

    def get(self, draft_id: str) -> StoryboardDraft:
        path = self._path(draft_id)
        if not path.exists():
            raise StoryboardNotFoundError(draft_id)
        return StoryboardDraft.model_validate_json(path.read_text(encoding="utf-8"))


class StoryboardValidator:
    """Validate an editable storyboard before it can become a costly render job."""

    def __init__(self, tier: CapabilityTier = CapabilityTier.PRESET) -> None:
        self.tier = tier

    @staticmethod
    def _diagnostic(
        code: str,
        severity: Severity,
        message: str,
        scene_index: int | None = None,
        suggested_presets: Optional[list[str]] = None,
    ) -> ValidationDiagnostic:
        return ValidationDiagnostic(
            code=code,
            severity=severity,
            message=message,
            scene_index=scene_index,
            suggested_presets=suggested_presets or [],
        )

    def validate(self, draft: StoryboardDraft, research: Optional[ResearchPack] = None) -> ValidationResult:
        diagnostics: list[ValidationDiagnostic] = []
        claims: dict[str, object] = {}
        if research is not None:
            try:
                claims = allowed_claims(research)
            except ResearchQualityError as exc:
                diagnostics.append(self._diagnostic("research.invalid", Severity.ERROR, str(exc)))
        elif draft.research_id:
            diagnostics.append(self._diagnostic("research.missing", Severity.ERROR, "Storyboard declares research_id but no ResearchPack was supplied for validation."))
        if not draft.scenes:
            diagnostics.append(self._diagnostic("storyboard.empty", Severity.ERROR, "Storyboard needs at least one scene."))
        known_effects = registry.load_effects()
        known_kits = set(registry.style_kit_names())
        for index, scene in enumerate(draft.scenes):
            if scene.evidence_claim_ids:
                missing_claims = set(scene.evidence_claim_ids) - set(claims)
                if missing_claims:
                    diagnostics.append(
                        self._diagnostic(
                            "research.claim_missing",
                            Severity.ERROR,
                            f"Scene references unavailable evidence claims: {sorted(missing_claims)}.",
                            index,
                        )
                    )
            try:
                manifest = get_scene(scene.preset, tier=self.tier)
            except KeyError:
                diagnostics.append(
                    self._diagnostic(
                        "scene.unknown",
                        Severity.ERROR,
                        f"Unknown or unavailable scene preset {scene.preset!r}.",
                        index,
                    )
                )
                continue
            if manifest.data_driven and manifest.required_data_hints:
                missing = [field for field in manifest.required_data_hints if field not in scene.props]
                if missing:
                    diagnostics.append(
                        self._diagnostic(
                            "scene.data_missing",
                            Severity.ERROR,
                            f"{scene.preset} requires structured data fields: {', '.join(missing)}.",
                            index,
                            ["HeroKinetic", "QuoteCard", "TypewriterSub"],
                        )
                    )
            for effect in scene.effects:
                if effect not in known_effects:
                    diagnostics.append(
                        self._diagnostic(
                            "effect.unknown",
                            Severity.ERROR,
                            f"Unknown scene effect {effect!r}. Use only entries from the live effect catalog.",
                            index,
                        )
                    )
            style = scene.style_kit or draft.default_style_kit
            if style and style not in known_kits:
                diagnostics.append(
                    self._diagnostic(
                        "style.unknown",
                        Severity.ERROR,
                        f"Unknown style kit {style!r}; renderer would silently fall back to a default.",
                        index,
                    )
                )
            text_len = len((scene.title or "") + scene.text)
            min_frames = int(max(MIN_DWELL_SECONDS, text_len / READ_CHARS_PER_SEC) * FPS)
            if scene.duration_in_frames is not None and scene.duration_in_frames < min_frames:
                diagnostics.append(
                    self._diagnostic(
                        "readability.duration_short",
                        Severity.ERROR,
                        f"Scene needs at least {min_frames} frames for its text at {FPS} fps.",
                        index,
                    )
                )
            if text_len > 320:
                diagnostics.append(
                    self._diagnostic(
                        "readability.dense_text",
                        Severity.WARNING,
                        "Scene text is dense; split it or use a data-driven explainer scene.",
                        index,
                        ["StepList", "BeforeAfter", "MetricTrend"],
                    )
                )
            if scene.audio.mode == "manual" and not (scene.audio.music_asset_id or scene.audio.sfx_asset_ids):
                diagnostics.append(
                    self._diagnostic(
                        "audio.manual_empty",
                        Severity.WARNING,
                        "Manual audio policy is selected without any audio asset identifiers.",
                        index,
                    )
                )
        valid = not any(item.severity == Severity.ERROR for item in diagnostics)
        return ValidationResult(draft_id=draft.draft_id, valid=valid, diagnostics=diagnostics)
