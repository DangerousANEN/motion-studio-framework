"""MSF Motion Library.

Provides a registry of production-quality motion presets with CSS keyframes,
durations, easing curves, and configurable parameters.
"""

from __future__ import annotations

from typing import Any, Optional

from msf.contracts.models import AnimationType, MotionPreset


class MotionLibrary:
    """Registry and query interface for static motion animation presets."""

    def __init__(self) -> None:
        self._presets: dict[str, MotionPreset] = {}
        self._register_default_presets()

    def _register(self, preset: MotionPreset) -> None:
        self._presets[preset.preset_id] = preset

    def get(self, preset_id: str) -> MotionPreset:
        """Retrieve a MotionPreset by its preset_id.

        Raises:
            KeyError: If preset_id is not found in the registry.
        """
        if preset_id not in self._presets:
            raise KeyError(f"MotionPreset with id '{preset_id}' not found in registry.")
        return self._presets[preset_id]

    def list_all(self) -> list[MotionPreset]:
        """Return all registered MotionPresets."""
        return list(self._presets.values())

    def get_by_type(self, animation_type: AnimationType | str) -> list[MotionPreset]:
        """Filter and return MotionPresets matching the specified AnimationType."""
        if isinstance(animation_type, str):
            try:
                anim_enum = AnimationType(animation_type)
            except ValueError:
                anim_enum = None
        else:
            anim_enum = animation_type

        result: list[MotionPreset] = []
        for preset in self._presets.values():
            if preset.animation_type == anim_enum or str(preset.animation_type) == str(animation_type):
                result.append(preset)
        return result

    def _register_default_presets(self) -> None:
        """Populate registry with 15+ production-quality motion presets for 1080x1920 viewport."""

        # 1. Fade In
        self._register(
            MotionPreset(
                preset_id="fade_in",
                name="Fade In",
                animation_type=AnimationType.FADE_IN,
                duration=0.6,
                easing="cubic-bezier(0.25, 0.1, 0.25, 1.0)",
                params={
                    "css_keyframes": (
                        "@keyframes fade_in {\n"
                        "  0% { opacity: 0; }\n"
                        "  100% { opacity: 1; }\n"
                        "}"
                    ),
                    "initial_opacity": 0.0,
                    "target_opacity": 1.0,
                },
            )
        )

        # 2. Fade Out
        self._register(
            MotionPreset(
                preset_id="fade_out",
                name="Fade Out",
                animation_type=AnimationType.FADE_OUT,
                duration=0.6,
                easing="cubic-bezier(0.25, 0.1, 0.25, 1.0)",
                params={
                    "css_keyframes": (
                        "@keyframes fade_out {\n"
                        "  0% { opacity: 1; }\n"
                        "  100% { opacity: 0; }\n"
                        "}"
                    ),
                    "initial_opacity": 1.0,
                    "target_opacity": 0.0,
                },
            )
        )

        # 3. Slide Left
        self._register(
            MotionPreset(
                preset_id="slide_left",
                name="Slide Left",
                animation_type=AnimationType.SLIDE_IN,
                duration=0.8,
                easing="cubic-bezier(0.16, 1, 0.3, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes slide_left {\n"
                        "  0% { transform: translateX(100%); opacity: 0; }\n"
                        "  100% { transform: translateX(0); opacity: 1; }\n"
                        "}"
                    ),
                    "direction": "left",
                    "distance": "100%",
                },
            )
        )

        # 4. Slide Right
        self._register(
            MotionPreset(
                preset_id="slide_right",
                name="Slide Right",
                animation_type=AnimationType.SLIDE_IN,
                duration=0.8,
                easing="cubic-bezier(0.16, 1, 0.3, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes slide_right {\n"
                        "  0% { transform: translateX(-100%); opacity: 0; }\n"
                        "  100% { transform: translateX(0); opacity: 1; }\n"
                        "}"
                    ),
                    "direction": "right",
                    "distance": "-100%",
                },
            )
        )

        # 5. Slide Up
        self._register(
            MotionPreset(
                preset_id="slide_up",
                name="Slide Up",
                animation_type=AnimationType.SLIDE_IN,
                duration=0.8,
                easing="cubic-bezier(0.16, 1, 0.3, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes slide_up {\n"
                        "  0% { transform: translateY(120px); opacity: 0; }\n"
                        "  100% { transform: translateY(0); opacity: 1; }\n"
                        "}"
                    ),
                    "direction": "up",
                    "distance": "120px",
                },
            )
        )

        # 6. Slide Down
        self._register(
            MotionPreset(
                preset_id="slide_down",
                name="Slide Down",
                animation_type=AnimationType.SLIDE_IN,
                duration=0.8,
                easing="cubic-bezier(0.16, 1, 0.3, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes slide_down {\n"
                        "  0% { transform: translateY(-120px); opacity: 0; }\n"
                        "  100% { transform: translateY(0); opacity: 1; }\n"
                        "}"
                    ),
                    "direction": "down",
                    "distance": "-120px",
                },
            )
        )

        # 7. Pop In (scale 0 -> 1 with overshoot)
        self._register(
            MotionPreset(
                preset_id="pop_in",
                name="Pop In",
                animation_type=AnimationType.SCALE_UP,
                duration=0.7,
                easing="cubic-bezier(0.34, 1.56, 0.64, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes pop_in {\n"
                        "  0% { transform: scale(0); opacity: 0; }\n"
                        "  70% { transform: scale(1.08); opacity: 1; }\n"
                        "  100% { transform: scale(1); opacity: 1; }\n"
                        "}"
                    ),
                    "initial_scale": 0.0,
                    "overshoot_scale": 1.08,
                    "final_scale": 1.0,
                },
            )
        )

        # 8. Pop Out
        self._register(
            MotionPreset(
                preset_id="pop_out",
                name="Pop Out",
                animation_type=AnimationType.ZOOM_OUT,
                duration=0.5,
                easing="cubic-bezier(0.36, 0, 0.66, -0.56)",
                params={
                    "css_keyframes": (
                        "@keyframes pop_out {\n"
                        "  0% { transform: scale(1); opacity: 1; }\n"
                        "  30% { transform: scale(1.05); opacity: 1; }\n"
                        "  100% { transform: scale(0); opacity: 0; }\n"
                        "}"
                    ),
                    "initial_scale": 1.0,
                    "final_scale": 0.0,
                },
            )
        )

        # 9. Spring Bounce
        self._register(
            MotionPreset(
                preset_id="spring_bounce",
                name="Spring Bounce",
                animation_type=AnimationType.BOUNCE,
                duration=1.0,
                easing="cubic-bezier(0.28, 0.84, 0.42, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes spring_bounce {\n"
                        "  0% { transform: translateY(-200px); opacity: 0; }\n"
                        "  40% { transform: translateY(0); opacity: 1; }\n"
                        "  65% { transform: translateY(-30px); }\n"
                        "  82% { transform: translateY(0); }\n"
                        "  92% { transform: translateY(-8px); }\n"
                        "  100% { transform: translateY(0); }\n"
                        "}"
                    ),
                    "bounce_height": "200px",
                },
            )
        )

        # 10. Typewriter
        self._register(
            MotionPreset(
                preset_id="typewriter",
                name="Typewriter",
                animation_type=AnimationType.TYPEWRITER,
                duration=1.5,
                easing="steps(40, end)",
                params={
                    "css_keyframes": (
                        "@keyframes typewriter {\n"
                        "  from { width: 0; }\n"
                        "  to { width: 100%; }\n"
                        "}"
                    ),
                    "steps": 40,
                    "overflow": "hidden",
                    "white_space": "nowrap",
                },
            )
        )

        # 11. Counter Roll (number counting animation)
        self._register(
            MotionPreset(
                preset_id="counter_roll",
                name="Counter Roll",
                animation_type=AnimationType.STAGGER,
                duration=1.2,
                easing="cubic-bezier(0.12, 0, 0.39, 0)",
                params={
                    "css_keyframes": (
                        "@keyframes counter_roll {\n"
                        "  0% { transform: translateY(100%); opacity: 0; filter: blur(4px); }\n"
                        "  50% { opacity: 0.8; filter: blur(1px); }\n"
                        "  100% { transform: translateY(0); opacity: 1; filter: blur(0); }\n"
                        "}"
                    ),
                    "blur_amount": "4px",
                },
            )
        )

        # 12. Wipe Left
        self._register(
            MotionPreset(
                preset_id="wipe_left",
                name="Wipe Left",
                animation_type=AnimationType.SLIDE_IN,
                duration=0.75,
                easing="cubic-bezier(0.65, 0, 0.35, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes wipe_left {\n"
                        "  0% { clip-path: inset(0 0 0 100%); }\n"
                        "  100% { clip-path: inset(0 0 0 0); }\n"
                        "}"
                    ),
                    "clip_direction": "left_to_right",
                },
            )
        )

        # 13. Wipe Right
        self._register(
            MotionPreset(
                preset_id="wipe_right",
                name="Wipe Right",
                animation_type=AnimationType.SLIDE_IN,
                duration=0.75,
                easing="cubic-bezier(0.65, 0, 0.35, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes wipe_right {\n"
                        "  0% { clip-path: inset(0 100% 0 0); }\n"
                        "  100% { clip-path: inset(0 0 0 0); }\n"
                        "}"
                    ),
                    "clip_direction": "right_to_left",
                },
            )
        )

        # 14. Parallax Shift
        self._register(
            MotionPreset(
                preset_id="parallax_shift",
                name="Parallax Shift",
                animation_type=AnimationType.SLIDE_IN,
                duration=1.2,
                easing="cubic-bezier(0.25, 1, 0.5, 1)",
                params={
                    "css_keyframes": (
                        "@keyframes parallax_shift {\n"
                        "  0% { transform: translateY(60px) scale(0.95); opacity: 0.3; }\n"
                        "  100% { transform: translateY(0) scale(1.0); opacity: 1; }\n"
                        "}"
                    ),
                    "offset_y": "60px",
                    "scale_start": 0.95,
                },
            )
        )

        # 15. Zoom Pulse
        self._register(
            MotionPreset(
                preset_id="zoom_pulse",
                name="Zoom Pulse",
                animation_type=AnimationType.PULSE,
                duration=1.0,
                easing="ease-in-out",
                params={
                    "css_keyframes": (
                        "@keyframes zoom_pulse {\n"
                        "  0% { transform: scale(1); }\n"
                        "  50% { transform: scale(1.06); }\n"
                        "  100% { transform: scale(1); }\n"
                        "}"
                    ),
                    "pulse_scale": 1.06,
                },
            )
        )

        # 16. Rotate In
        self._register(
            MotionPreset(
                preset_id="rotate_in",
                name="Rotate In",
                animation_type=AnimationType.ROTATE,
                duration=0.8,
                easing="cubic-bezier(0.175, 0.885, 0.32, 1.275)",
                params={
                    "css_keyframes": (
                        "@keyframes rotate_in {\n"
                        "  0% { transform: rotate(-15deg) scale(0.8); opacity: 0; }\n"
                        "  100% { transform: rotate(0deg) scale(1); opacity: 1; }\n"
                        "}"
                    ),
                    "initial_angle": "-15deg",
                },
            )
        )

        # 17. Blur Reveal
        self._register(
            MotionPreset(
                preset_id="blur_reveal",
                name="Blur Reveal",
                animation_type=AnimationType.FADE_IN,
                duration=0.9,
                easing="cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                params={
                    "css_keyframes": (
                        "@keyframes blur_reveal {\n"
                        "  0% { filter: blur(20px); opacity: 0; transform: scale(1.03); }\n"
                        "  100% { filter: blur(0px); opacity: 1; transform: scale(1); }\n"
                        "}"
                    ),
                    "initial_blur": "20px",
                },
            )
        )
