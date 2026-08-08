"""MSF Camera Library.

Provides predefined camera movement presets (pan, zoom, orbit, parallax, crane, etc.)
with CSS transform keyframe strings, speeds, and layout compatibility rules.
"""

from __future__ import annotations

from typing import Any, Optional

from msf.contracts.models import CameraPreset, MovementType


class CameraLibrary:
    """Registry and query interface for static camera movement presets."""

    def __init__(self) -> None:
        self._presets: dict[str, CameraPreset] = {}
        self._register_default_presets()

    def _register(self, preset: CameraPreset) -> None:
        self._presets[preset.preset_id] = preset

    def get(self, preset_id: str) -> CameraPreset:
        """Retrieve a CameraPreset by its preset_id.

        Raises:
            KeyError: If preset_id is not found in the registry.
        """
        if preset_id not in self._presets:
            raise KeyError(f"CameraPreset with id '{preset_id}' not found in registry.")
        return self._presets[preset_id]

    def list_all(self) -> list[CameraPreset]:
        """Return all registered CameraPresets."""
        return list(self._presets.values())

    def get_compatible(self, layout_id: str) -> list[CameraPreset]:
        """Return CameraPresets compatible with the specified layout_id."""
        compatible: list[CameraPreset] = []
        for preset in self._presets.values():
            if "*" in preset.compatible_layouts or layout_id in preset.compatible_layouts:
                compatible.append(preset)
        return compatible

    def _register_default_presets(self) -> None:
        """Populate registry with 10+ camera movement presets."""

        all_layouts = [
            "centered_single",
            "title_body",
            "split_horizontal",
            "split_vertical",
            "thirds_grid",
            "quad_grid",
            "sidebar_main",
            "full_bleed",
            "bottom_bar",
            "dashboard",
            "timeline_vertical",
        ]

        # 1. Static
        self._register(
            CameraPreset(
                preset_id="static",
                movement_type=MovementType.NONE,
                css_transform=(
                    "@keyframes camera_static {\n"
                    "  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }\n"
                    "}"
                ),
                duration=5.0,
                easing="linear",
                speed=1.0,
                compatible_layouts=["*"],
            )
        )

        # 2. Slow Push In
        self._register(
            CameraPreset(
                preset_id="slow_push_in",
                movement_type=MovementType.ZOOM_IN,
                css_transform=(
                    "@keyframes camera_slow_push_in {\n"
                    "  0% { transform: scale(1.0); }\n"
                    "  100% { transform: scale(1.12); }\n"
                    "}"
                ),
                duration=5.0,
                easing="cubic-bezier(0.25, 0.1, 0.25, 1.0)",
                speed=0.5,
                compatible_layouts=all_layouts,
            )
        )

        # 3. Slow Pull Out
        self._register(
            CameraPreset(
                preset_id="slow_pull_out",
                movement_type=MovementType.ZOOM_OUT,
                css_transform=(
                    "@keyframes camera_slow_pull_out {\n"
                    "  0% { transform: scale(1.15); }\n"
                    "  100% { transform: scale(1.0); }\n"
                    "}"
                ),
                duration=5.0,
                easing="cubic-bezier(0.25, 0.1, 0.25, 1.0)",
                speed=0.5,
                compatible_layouts=[
                    "centered_single",
                    "title_body",
                    "full_bleed",
                    "split_horizontal",
                    "dashboard",
                ],
            )
        )

        # 4. Pan Left
        self._register(
            CameraPreset(
                preset_id="pan_left",
                movement_type=MovementType.PAN_LEFT,
                css_transform=(
                    "@keyframes camera_pan_left {\n"
                    "  0% { transform: translateX(40px); }\n"
                    "  100% { transform: translateX(-40px); }\n"
                    "}"
                ),
                duration=4.0,
                easing="ease-in-out",
                speed=1.0,
                compatible_layouts=["split_vertical", "quad_grid", "sidebar_main", "full_bleed"],
            )
        )

        # 5. Pan Right
        self._register(
            CameraPreset(
                preset_id="pan_right",
                movement_type=MovementType.PAN_RIGHT,
                css_transform=(
                    "@keyframes camera_pan_right {\n"
                    "  0% { transform: translateX(-40px); }\n"
                    "  100% { transform: translateX(40px); }\n"
                    "}"
                ),
                duration=4.0,
                easing="ease-in-out",
                speed=1.0,
                compatible_layouts=["split_vertical", "quad_grid", "sidebar_main", "full_bleed"],
            )
        )

        # 6. Parallax Depth
        self._register(
            CameraPreset(
                preset_id="parallax_depth",
                movement_type=MovementType.PARALLAX,
                css_transform=(
                    "@keyframes camera_parallax_depth {\n"
                    "  0% { transform: perspective(1000px) translateZ(0px) rotateX(0deg); }\n"
                    "  100% { transform: perspective(1000px) translateZ(80px) rotateX(2deg); }\n"
                    "}"
                ),
                duration=6.0,
                easing="cubic-bezier(0.16, 1, 0.3, 1)",
                speed=0.8,
                compatible_layouts=["centered_single", "full_bleed", "title_body", "dashboard"],
            )
        )

        # 7. Orbit Around
        self._register(
            CameraPreset(
                preset_id="orbit_around",
                movement_type=MovementType.ORBIT,
                css_transform=(
                    "@keyframes camera_orbit_around {\n"
                    "  0% { transform: perspective(1200px) rotateY(-5deg) rotateX(2deg); }\n"
                    "  50% { transform: perspective(1200px) rotateY(5deg) rotateX(-2deg); }\n"
                    "  100% { transform: perspective(1200px) rotateY(-5deg) rotateX(2deg); }\n"
                    "}"
                ),
                duration=7.0,
                easing="ease-in-out",
                speed=0.6,
                compatible_layouts=["centered_single", "quad_grid", "dashboard"],
            )
        )

        # 8. Shake Subtle
        self._register(
            CameraPreset(
                preset_id="shake_subtle",
                movement_type=MovementType.SHAKE,
                css_transform=(
                    "@keyframes camera_shake_subtle {\n"
                    "  0%, 100% { transform: translate(0, 0); }\n"
                    "  20% { transform: translate(-3px, 2px); }\n"
                    "  40% { transform: translate(3px, -1px); }\n"
                    "  60% { transform: translate(-2px, -2px); }\n"
                    "  80% { transform: translate(2px, 1px); }\n"
                    "}"
                ),
                duration=0.5,
                easing="ease-in-out",
                speed=1.5,
                compatible_layouts=["centered_single", "full_bleed", "title_body"],
            )
        )

        # 9. Crane Up
        self._register(
            CameraPreset(
                preset_id="crane_up",
                movement_type=MovementType.CRANE_UP,
                css_transform=(
                    "@keyframes camera_crane_up {\n"
                    "  0% { transform: translateY(60px) scale(0.98); }\n"
                    "  100% { transform: translateY(-40px) scale(1.02); }\n"
                    "}"
                ),
                duration=5.0,
                easing="cubic-bezier(0.25, 0.1, 0.25, 1.0)",
                speed=1.0,
                compatible_layouts=[
                    "title_body",
                    "thirds_grid",
                    "timeline_vertical",
                    "split_horizontal",
                ],
            )
        )

        # 10. Crane Down
        self._register(
            CameraPreset(
                preset_id="crane_down",
                movement_type=MovementType.CRANE_DOWN,
                css_transform=(
                    "@keyframes camera_crane_down {\n"
                    "  0% { transform: translateY(-50px) scale(1.02); }\n"
                    "  100% { transform: translateY(50px) scale(0.98); }\n"
                    "}"
                ),
                duration=5.0,
                easing="cubic-bezier(0.25, 0.1, 0.25, 1.0)",
                speed=1.0,
                compatible_layouts=[
                    "title_body",
                    "thirds_grid",
                    "timeline_vertical",
                    "split_horizontal",
                ],
            )
        )

        # 11. Whip Pan
        self._register(
            CameraPreset(
                preset_id="whip_pan",
                movement_type=MovementType.WHIP_PAN,
                css_transform=(
                    "@keyframes camera_whip_pan {\n"
                    "  0% { transform: translateX(-100%) scaleX(1.4); filter: blur(12px); }\n"
                    "  70% { filter: blur(2px); }\n"
                    "  100% { transform: translateX(0) scaleX(1); filter: blur(0); }\n"
                    "}"
                ),
                duration=0.6,
                easing="cubic-bezier(0.7, 0, 0.84, 0)",
                speed=2.0,
                compatible_layouts=[
                    "centered_single",
                    "full_bleed",
                    "split_horizontal",
                    "split_vertical",
                ],
            )
        )

        # 12. Dolly Zoom
        self._register(
            CameraPreset(
                preset_id="dolly_zoom",
                movement_type=MovementType.DOLLY_ZOOM,
                css_transform=(
                    "@keyframes camera_dolly_zoom {\n"
                    "  0% { transform: scale(1.3); }\n"
                    "  100% { transform: scale(0.95); }\n"
                    "}"
                ),
                duration=3.5,
                easing="cubic-bezier(0.45, 0, 0.55, 1)",
                speed=1.0,
                compatible_layouts=["centered_single", "full_bleed", "title_body"],
            )
        )
