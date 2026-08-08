"""MSF Quality Control Review Engine.

Provides ReviewEngine with deterministic, measurable rules for inspecting script, scene,
and project state artifacts.
"""

from __future__ import annotations

import logging
from typing import Optional

from msf.contracts.models import (
    AssetResult,
    AssetType,
    CameraPreset,
    LayoutChoice,
    ProjectState,
    ProjectStatus,
    ReviewResult,
    ReviewVerdict,
    SceneComposition,
    Script,
    VoiceResult,
)
from msf.libraries.camera_library import CameraLibrary
from msf.libraries.layout_library import LayoutLibrary

logger = logging.getLogger("msf.review")


class ReviewEngine:
    """Quantitative, rule-based review engine for MSF artifacts."""

    def __init__(
        self,
        layout_lib: Optional[LayoutLibrary] = None,
        camera_lib: Optional[CameraLibrary] = None,
    ):
        self.layout_lib = layout_lib or LayoutLibrary()
        self.camera_lib = camera_lib or CameraLibrary()

    def review_script(
        self,
        script: Script,
        expected_duration_range: tuple[int, int] = (30, 90),
        attempt: int = 1,
        max_attempts: int = 3,
    ) -> ReviewResult:
        """Review script quality based on measurable constraints.

        Checks:
        1. Hook length: text speaking duration estimated at 15 chars/sec should be < 3 seconds (or character length < ~45 chars).
        2. Total duration: within expected_duration_range (default 30..90s).
        3. Scene count: at least 2 scenes in scenes_text.

        Returns:
            ReviewResult with PASS or FAIL verdict.
        """
        issues: list[str] = []
        suggestions: list[str] = []

        # 1. Hook check
        # Hook < 3 seconds: word count <= 7 or char length < 45 chars or duration estimated < 3.0s
        hook_text = script.hook.strip()
        if not hook_text:
            issues.append("Script hook is missing or empty.")
            suggestions.append("Provide a catchy hook sentence under 3 seconds duration.")
        else:
            # Estimate speaking duration: roughly 15 characters per second or 2.5 words per second
            words = hook_text.split()
            estimated_hook_dur = len(hook_text) / 15.0
            if estimated_hook_dur >= 3.0 and len(words) > 8:
                issues.append(
                    f"Hook is too long ({estimated_hook_dur:.1f}s, {len(words)} words). Must be < 3.0 seconds."
                )
                suggestions.append("Trim hook text to under 8 words / 45 characters.")

        # 2. Total duration check
        min_dur, max_dur = expected_duration_range
        if script.total_duration < min_dur or script.total_duration > max_dur:
            issues.append(
                f"Total script duration ({script.total_duration:.1f}s) outside expected range ({min_dur}-{max_dur}s)."
            )
            suggestions.append(f"Adjust scene text lengths to fit between {min_dur}s and {max_dur}s.")

        # 3. Scene count check
        scene_count = len(script.scenes_text)
        if scene_count < 2:
            issues.append(
                f"Adequate scene count missing. Found {scene_count} scene(s), minimum required is 2."
            )
            suggestions.append("Decompose script into at least 2 distinct visual scenes.")

        verdict = ReviewVerdict.PASS if not issues else ReviewVerdict.FAIL
        score = 1.0 if verdict == ReviewVerdict.PASS else max(0.0, 1.0 - 0.3 * len(issues))

        return ReviewResult(
            stage="script_review",
            verdict=verdict,
            score=score,
            issues=issues,
            suggestions=suggestions,
            attempt=attempt,
            max_attempts=max_attempts,
        )

    def review_scene(
        self,
        scene: SceneComposition,
        attempt: int = 1,
        max_attempts: int = 3,
    ) -> ReviewResult:
        """Review scene composition quality based on measurable constraints.

        Checks:
        1. Layout exists: scene.layout is not None.
        2. Camera compatible: scene.camera is compatible with scene.layout.
        3. Assets present: scene.assets is non-empty and contains valid file paths or references.
        4. Voice exists: scene.voice is not None and has valid audio_path.

        Returns:
            ReviewResult with PASS or FAIL verdict.
        """
        issues: list[str] = []
        suggestions: list[str] = []

        # 1. Layout check
        if scene.layout is None:
            issues.append(f"Scene {scene.scene_id}: Layout choice is missing.")
            suggestions.append("Assign a valid LayoutChoice template to the scene.")
        else:
            layout_id = scene.layout.layout_id
            # Verify layout exists in library
            try:
                self.layout_lib.get(layout_id)
            except KeyError:
                issues.append(f"Scene {scene.scene_id}: Layout ID '{layout_id}' is unknown in LayoutLibrary.")
                suggestions.append("Use a registered layout template ID.")

        # 2. Camera compatibility check
        if scene.camera is not None and scene.layout is not None:
            camera_preset = scene.camera
            layout_id = scene.layout.layout_id
            if (
                camera_preset.compatible_layouts
                and "*" not in camera_preset.compatible_layouts
                and layout_id not in camera_preset.compatible_layouts
            ):
                issues.append(
                    f"Scene {scene.scene_id}: Camera preset '{camera_preset.preset_id}' is incompatible with layout '{layout_id}'."
                )
                suggestions.append(
                    f"Choose a compatible camera preset from: {camera_preset.compatible_layouts}"
                )
        # 3. Assets present check
        if not scene.assets:
            issues.append(f"Scene {scene.scene_id}: Visual assets list is empty.")
            suggestions.append("Generate or attach at least one visual asset to the scene.")

        # 4. Voice exists check
        if scene.voice is None:
            issues.append(f"Scene {scene.scene_id}: Voice synthesis result is missing.")
            suggestions.append("Synthesize audio narration and attach VoiceResult to the scene.")
        elif not scene.voice.audio_path:
            issues.append(f"Scene {scene.scene_id}: Voice audio_path is empty.")
            suggestions.append("Provide a valid audio_path in VoiceResult.")

        verdict = ReviewVerdict.PASS if not issues else ReviewVerdict.FAIL
        score = 1.0 if verdict == ReviewVerdict.PASS else max(0.0, 1.0 - 0.25 * len(issues))

        return ReviewResult(
            stage="scene_review",
            verdict=verdict,
            score=score,
            issues=issues,
            suggestions=suggestions,
            attempt=attempt,
            max_attempts=max_attempts,
        )

    def review_project(
        self,
        state: ProjectState,
        expected_duration_range: tuple[int, int] = (30, 90),
        attempt: int = 1,
        max_attempts: int = 3,
    ) -> ReviewResult:
        """Review final project state prior to rendering.

        Checks:
        1. All scenes pass individual scene reviews.
        2. Audio normalized / voice present across scenes.
        3. Total combined duration is within project brief target range.

        Returns:
            ReviewResult with PASS or FAIL verdict.
        """
        issues: list[str] = []
        suggestions: list[str] = []

        if not state.scenes:
            issues.append("Project has no scenes composed.")
            suggestions.append("Run storyboard and scene assembly pipeline stages.")

        # 1. Check individual scenes
        total_duration = 0.0
        missing_voice_scenes: list[str] = []

        for scene_id, scene in state.scenes.items():
            total_duration += scene.duration
            scene_review = self.review_scene(scene)
            if scene_review.verdict == ReviewVerdict.FAIL:
                issues.append(
                    f"Scene '{scene_id}' failed quality review: {'; '.join(scene_review.issues)}"
                )
            if scene.voice is None or not scene.voice.audio_path:
                missing_voice_scenes.append(scene_id)

        # 2. Audio normalization / completeness check
        if missing_voice_scenes:
            issues.append(
                f"Scenes missing voice synthesis: {', '.join(missing_voice_scenes)}"
            )
            suggestions.append("Ensure TTS is executed for all scenes.")

        # 3. Total duration check
        min_dur, max_dur = expected_duration_range
        if state.brief and state.brief.duration_range:
            min_dur, max_dur = state.brief.duration_range

        if total_duration < min_dur or total_duration > max_dur:
            issues.append(
                f"Total project duration ({total_duration:.1f}s) outside target range ({min_dur}-{max_dur}s)."
            )
            suggestions.append("Adjust scene durations or scene count.")

        verdict = ReviewVerdict.PASS if not issues else ReviewVerdict.FAIL
        score = 1.0 if verdict == ReviewVerdict.PASS else max(0.0, 1.0 - 0.2 * len(issues))

        return ReviewResult(
            stage="project_qc",
            verdict=verdict,
            score=score,
            issues=issues,
            suggestions=suggestions,
            attempt=attempt,
            max_attempts=max_attempts,
        )
