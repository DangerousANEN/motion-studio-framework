"""Smoke-check theme-adaptive VideoSpec wiring and new tutorial/media presets."""
from __future__ import annotations

from msf.spec import Scene, build_spec, validate_spec


def main() -> None:
    scene = Scene(
        id="guide",
        preset="ScreenGuide",
        duration_in_frames=180,
        title="Гайд",
        images=["panel_preview_still_1.png"],
        focus_x=0.6,
        focus_y=0.5,
        focus_scale=1.2,
        cursor_steps=[{"x": 0.6, "y": 0.5, "at": 0.3, "label": "Клик"}],
        overlays=[{"type": "cursor", "x": 0.6, "y": 0.5, "at": 0.3, "hold": 1}],
    )
    spec = build_spec(
        [scene],
        style="product_tutorial",
        style_config={"palette": {"neon": "#37D9FF"}, "effects": {"bloom": 0.3}},
    )
    validate_spec(spec)
    if spec["scenes"][0]["focusScale"] != 1.2:
        raise RuntimeError("ScreenGuide focusScale was not serialized to camelCase")
    if spec["styleConfig"]["palette"]["neon"] != "#37D9FF":
        raise RuntimeError("Video styleConfig was not preserved")
    print("style_media_wire=ok style=product_tutorial overlay=cursor")


if __name__ == "__main__":
    main()
