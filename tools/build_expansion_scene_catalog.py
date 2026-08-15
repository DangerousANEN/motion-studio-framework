"""Build one standalone Remotion input spec per MSF Studio v2.3 expansion scene.

The catalog is a visual inspection artifact, not a new production path. It reuses
panel demo fixtures so every still uses the same Python-side contract that the
dashboard and smoke checks validate.

Run from the repository root:
    PYTHONPATH=. python3 tools/build_expansion_scene_catalog.py
"""
from __future__ import annotations

import json
from pathlib import Path

from msf.panel.demo_props import scene_for
from msf.spec import validate_spec

OUT = Path(__file__).resolve().parents[1] / "remotion" / "out" / "expansion-catalog"

# The style is intentionally selected by the visual job, so the delivered catalog
# demonstrates that scenes are portable rather than all inheriting one neon look.
SCENES: tuple[tuple[str, str], ...] = (
    ("HookStack", "kinetic_poster"),
    ("KineticPhrase", "kinetic_poster"),
    ("ProblemSolution", "porcelain"),
    ("FeatureSpotlight", "liquid_chrome"),
    ("CaseStudyBoard", "violet_luxe"),
    ("MythFact", "porcelain"),
    ("QuoteEvidence", "violet_luxe"),
    ("StatsBand", "cobalt_command"),
    ("SourceStack", "midnight_orbit"),
    ("CountdownRing", "infrared_alert"),
    ("PromptComposer", "pixel_arcade"),
    ("ProviderChat", "coral_creator"),
    ("NotificationStack", "infrared_alert"),
    ("CommentThread", "coral_creator"),
    ("PollResult", "pixel_arcade"),
    ("BrowserTour", "cobalt_command"),
    ("ScreenMagnifier", "liquid_chrome"),
    ("DeviceShowcase", "aurora_flux"),
    ("VoiceWave", "violet_luxe"),
    ("VideoFrame", "coral_creator"),
)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for number, (preset, style) in enumerate(SCENES, start=1):
        # Reuse the dashboard's readability-aware duration policy. A still is
        # sampled during a stable dwell, but the complete input spec remains valid
        # if the user later renders the individual preview as motion.
        scene = scene_for(preset)
        scene["style"] = style
        duration = int(scene["durationInFrames"])
        spec = {
            "width": 1080,
            "height": 1920,
            "fps": 60,
            "durationInFrames": duration,
            "style": style,
            "scenes": [scene],
        }
        validate_spec(spec)
        stem = f"{number:02d}-{preset}"
        (OUT / f"{stem}.json").write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest.append(
            {
                "number": number,
                "preset": preset,
                "style": style,
                "spec": f"{stem}.json",
                "preview": f"{stem}.png",
                "frame": min(duration - 30, max(90, round(duration * 0.58))),
            }
        )

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"scene_specs={len(manifest)} out={OUT}")


if __name__ == "__main__":
    main()
