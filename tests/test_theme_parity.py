"""Theme parity between the Python spec builder and the Remotion renderer.

WHY THIS EXISTS
---------------
`theme` used to be an unvalidated free-form string in build_spec(). A typo such
as "midnight" passed every Python check, reached Root.tsx, failed Zod parsing
there, and silently degraded the whole render into a 2-second red ERROR card.
The MP4 still appeared and the exit code was still 0 -- only the pixels were
wrong, which is the worst kind of failure.

Two guards:
  1. build_spec() rejects unknown themes with a message naming the valid set.
  2. This test asserts msf.spec.THEMES matches THEMES in brand.ts, so adding a
     theme on one side without the other fails here instead of at render time.

Uses unittest to match the rest of tests/ (this project has no pytest).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from msf.spec import DEFAULT_THEME, THEMES, Scene, build_spec

BRAND_TS = (
    Path(__file__).resolve().parents[1] / "remotion" / "src" / "presets" / "brand.ts"
)


def _themes_from_brand_ts() -> set:
    """Parse the theme names out of the `THEMES` record in brand.ts."""
    source = BRAND_TS.read_text(encoding="utf-8")
    match = re.search(
        r"export\s+const\s+THEMES\s*:\s*Record<[^>]*>\s*=\s*\{([^}]*)\}", source
    )
    if not match:
        raise AssertionError(f"Could not find the THEMES record in {BRAND_TS}")

    body = match.group(1)
    # Entries are shorthand (`pop, noir, glass`) or `name: value` pairs.
    return {part.split(":")[0].strip() for part in body.split(",") if part.strip()}


def _scene() -> Scene:
    return Scene(
        id="s0",
        duration_in_frames=60,
        preset="HeroKinetic",
        title="Заголовок",
    )


class ThemeParityTest(unittest.TestCase):
    def test_python_themes_match_brand_ts(self) -> None:
        """The two sources of truth must not drift apart."""
        ts_themes = _themes_from_brand_ts()
        py_themes = set(THEMES)
        self.assertEqual(
            py_themes,
            ts_themes,
            "Theme lists have drifted.\n"
            f"  only in msf/spec.py : {sorted(py_themes - ts_themes)}\n"
            f"  only in brand.ts    : {sorted(ts_themes - py_themes)}",
        )

    def test_default_theme_is_valid(self) -> None:
        self.assertIn(DEFAULT_THEME, THEMES)

    def test_every_declared_theme_is_accepted(self) -> None:
        for theme in THEMES:
            with self.subTest(theme=theme):
                spec = build_spec([_scene()], theme=theme)
                self.assertEqual(spec["theme"], theme)

    def test_unknown_theme_is_rejected(self) -> None:
        """The regression: 'midnight' must not reach the renderer."""
        with self.assertRaises(ValueError) as ctx:
            build_spec([_scene()], theme="midnight")

        message = str(ctx.exception)
        self.assertIn("midnight", message, "error should name the offending value")
        # The message must list the valid options, otherwise the caller has to
        # go read the source to find out what to use instead.
        for theme in THEMES:
            self.assertIn(theme, message, f"error should list valid theme {theme!r}")

    def test_case_mismatch_is_rejected(self) -> None:
        """'Pop' is not 'pop' -- Zod is case-sensitive, so we must be too."""
        with self.assertRaises(ValueError):
            build_spec([_scene()], theme="Pop")

    def test_empty_theme_is_rejected(self) -> None:
        """An empty string is a bug in the caller, not a request for defaults."""
        with self.assertRaises(ValueError):
            build_spec([_scene()], theme="")

    def test_omitted_theme_falls_back_to_default(self) -> None:
        spec = build_spec([_scene()])
        self.assertEqual(spec["theme"], DEFAULT_THEME)

    def test_none_theme_falls_back_to_default(self) -> None:
        """None means 'unset', which is different from an invalid value."""
        spec = build_spec([_scene()], theme=None)
        self.assertEqual(spec["theme"], DEFAULT_THEME)


if __name__ == "__main__":
    unittest.main()
