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
  2. This test asserts msf.spec.THEMES matches the ThemeSchema Zod enum, so
     adding a theme on one side without the other fails here instead of at
     render time.

WHY NOT `THEMES` IN brand.ts (this test used to, and failed)
------------------------------------------------------------
brand.ts declares 15 palettes; the spec root accepts only 5. The comparison
against brand.ts therefore failed permanently with 10 "missing" themes, and it was
the TEST that was wrong, not the code:

    theme: "broadcast"  -> red RENDER ERROR card (verified by rendering a still)
    style: "news"       -> renders correctly, and news's kit uses the broadcast
                           palette

So the other 10 palettes are real and reachable — through a STYLE KIT, not through
`theme`. The contract that binds build_spec() is ThemeSchema, and that is what is
compared here. Style kits get their own parity test below.

Uses unittest to match the rest of tests/ (this project has no pytest).
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

# Allow `python tests/test_theme_parity.py` as well as `python -m unittest`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from msf import registry
from msf.spec import DEFAULT_THEME, THEMES, Scene, build_spec

REPO = Path(__file__).resolve().parents[1]
SCHEMA_TS = REPO / "remotion" / "src" / "VideoSpec.schema.ts"
BRAND_TS = REPO / "remotion" / "src" / "presets" / "brand.ts"


def _themes_from_schema_ts() -> set:
    """Parse the ThemeSchema enum — the values the renderer actually accepts."""
    source = SCHEMA_TS.read_text(encoding="utf-8")
    match = re.search(r"ThemeSchema\s*=\s*z\.enum\(\[(.*?)\]\)", source, re.S)
    if not match:
        raise AssertionError(f"Could not find ThemeSchema in {SCHEMA_TS}")
    return set(re.findall(r"'([^']+)'", match.group(1)))


def _palettes_from_brand_ts() -> set:
    """Every palette defined in brand.ts, reachable via `theme` OR a style kit."""
    source = BRAND_TS.read_text(encoding="utf-8")
    match = re.search(
        r"export\s+const\s+THEMES\s*:\s*Record<[^>]*>\s*=\s*\{([^}]*)\}", source
    )
    if not match:
        raise AssertionError(f"Could not find the THEMES record in {BRAND_TS}")
    return {part.split(":")[0].strip() for part in match.group(1).split(",") if part.strip()}


def _scene() -> Scene:
    return Scene(
        id="s0",
        duration_in_frames=60,
        preset="HeroKinetic",
        title="Заголовок",
    )


class ThemeParityTest(unittest.TestCase):
    def test_python_themes_match_schema_enum(self) -> None:
        """msf.spec.THEMES must equal the Zod enum the renderer validates with."""
        ts_themes = _themes_from_schema_ts()
        py_themes = set(THEMES)
        self.assertEqual(
            py_themes,
            ts_themes,
            "Theme lists have drifted.\n"
            f"  only in msf/spec.py        : {sorted(py_themes - ts_themes)}\n"
            f"  only in ThemeSchema (TS)   : {sorted(ts_themes - py_themes)}",
        )

    def test_registry_reads_the_same_enum(self) -> None:
        """registry.theme_names() feeds the panel's picker; it must not differ."""
        self.assertEqual(set(registry.theme_names()), set(THEMES))

    def test_root_themes_are_a_subset_of_brand_palettes(self) -> None:
        """Every accepted theme must resolve to a real palette.

        A name in the enum with no palette behind it falls back to THEMES.pop at
        render time — accepted, rendered, and the wrong colours.
        """
        palettes = _palettes_from_brand_ts()
        self.assertTrue(
            set(THEMES) <= palettes,
            f"themes with no palette in brand.ts: {sorted(set(THEMES) - palettes)}",
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

    def test_style_only_palette_is_rejected_as_a_theme(self) -> None:
        """`broadcast` is a real palette but NOT a valid root theme.

        Verified against the renderer: theme:"broadcast" produced a red RENDER
        ERROR card naming the five accepted values. build_spec must refuse it here
        rather than let it become an mp4.
        """
        palettes = _palettes_from_brand_ts()
        style_only = sorted(palettes - set(THEMES))
        self.assertTrue(style_only, "expected brand.ts to define palettes beyond the enum")
        for name in style_only:
            with self.subTest(palette=name), self.assertRaises(ValueError):
                build_spec([_scene()], theme=name)

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


class StyleKitParityTest(unittest.TestCase):
    """Style kits are the OTHER half of the look, and unvalidated.

    `style` is z.string() with no enum and getStyleKit() falls back to `pop` for
    anything unknown, so a typo silently renders the default look. These tests pin
    the parsed set so the panel can offer a picker instead of free text.
    """

    def test_kits_parse(self) -> None:
        kits = registry.load_style_kits()
        self.assertGreaterEqual(len(kits), 14, f"parsed only {len(kits)} style kits")

    def test_every_kit_points_at_a_real_palette(self) -> None:
        """A kit naming a missing palette silently renders in `pop`."""
        palettes = _palettes_from_brand_ts()
        for name, kit in registry.load_style_kits().items():
            with self.subTest(kit=name):
                self.assertIn(kit.theme, palettes, f"kit {name!r} -> unknown palette")

    def test_every_kit_has_an_effect_profile(self) -> None:
        """An empty profile means the parser missed it — `clean` uses `NO_FX`.

        That alias returned {} before the parser resolved const references, which
        would have shown "no effects" for a kit that has a real all-zero profile.
        """
        for name, kit in registry.load_style_kits().items():
            with self.subTest(kit=name):
                self.assertEqual(
                    set(kit.effects),
                    {"grain", "vignette", "bloom", "chromatic", "scanlines"},
                    f"kit {name!r} effect profile did not parse: {kit.effects}",
                )

    def test_kit_transitions_are_real_transitions(self) -> None:
        """A kit's default transition must be a name Zod actually accepts.

        This test used to compare kits against `TRANSITIONS` in
        registry/effects_scene.ts, lowercasing the first letter to bridge
        PascalCase to camelCase. Every kit failed, and the lowercasing hid why:
        the two sets are unrelated, not differently-cased. `steel` uses 'wipe',
        which has no PascalCase counterpart in that registry at all.

        Style kits feed `scene.transition.type`, which is validated by
        TransitionTypeSchema. That enum is the only authority here.
        """
        allowed = set(registry.scene_transition_types())
        self.assertTrue(allowed, "TransitionTypeSchema did not parse")
        for name, kit in registry.load_style_kits().items():
            with self.subTest(kit=name):
                self.assertIn(
                    kit.transition,
                    allowed,
                    f"kit {name!r} -> {kit.transition!r} is not in TransitionTypeSchema; "
                    "Zod would reject a spec built from this kit",
                )

    def test_the_two_transition_sets_are_disjoint(self) -> None:
        """Guard the distinction the previous test conflated.

        registry/effects_scene.ts exports 12 PascalCase transition COMPONENTS
        that nothing on the render path imports (only src/audit/
        EffectProbeComps.tsx does). lib/transitions.ts + TransitionTypeSchema
        define the 18 camelCase transition NAMES that getPresentation() switches
        on. If these ever start overlapping, someone has begun wiring the dead
        registry into the render path and the panel's picker must be revisited.
        """
        components = set(registry.transition_names())
        schema_names = set(registry.scene_transition_types())
        self.assertEqual(len(components), 12, sorted(components))
        self.assertEqual(len(schema_names), 18, sorted(schema_names))
        self.assertEqual(
            components & schema_names,
            set(),
            "the component registry and the Zod enum now share names",
        )

    def test_scene_transition_types_match_lib_transitions(self) -> None:
        """The Zod enum must mirror TRANSITION_NAMES in lib/transitions.ts.

        getPresentation() has an exhaustiveness guard, so a name in the Zod enum
        with no case arm is a compile error — but a name in lib/transitions.ts
        MISSING from the Zod enum is silent, and produces a transition that is
        implemented yet unreachable from any valid spec.
        """
        lib = REPO / "remotion" / "src" / "lib" / "transitions.ts"
        text = lib.read_text(encoding="utf-8")
        m = re.search(r"TRANSITION_NAMES\s*=\s*\[(.*?)\]\s*as const", text, re.S)
        self.assertIsNotNone(m, "TRANSITION_NAMES not found in lib/transitions.ts")
        assert m is not None
        self.assertEqual(
            sorted(re.findall(r"'([^']+)'", m.group(1))),
            registry.scene_transition_types(),
        )


if __name__ == "__main__":
    unittest.main()
