"""Unit tests for MSF Phase 2 Design Libraries."""

import unittest
from msf.contracts.models import AnimationType, MovementType
from msf.libraries import (
    CameraLibrary,
    LayoutLibrary,
    MotionLibrary,
    TypographyLibrary,
    TypographyPreset,
)


class TestMotionLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = MotionLibrary()

    def test_preset_count(self):
        presets = self.lib.list_all()
        self.assertGreaterEqual(len(presets), 15)

    def test_required_presets_exist(self):
        required_ids = [
            "fade_in",
            "fade_out",
            "slide_left",
            "slide_right",
            "slide_up",
            "slide_down",
            "pop_in",
            "pop_out",
            "spring_bounce",
            "typewriter",
            "counter_roll",
            "wipe_left",
            "wipe_right",
            "parallax_shift",
            "zoom_pulse",
            "rotate_in",
            "blur_reveal",
        ]
        for pid in required_ids:
            preset = self.lib.get(pid)
            self.assertIsNotNone(preset)
            self.assertEqual(preset.preset_id, pid)
            self.assertIn("css_keyframes", preset.params)
            self.assertTrue(preset.params["css_keyframes"].startswith("@keyframes"))

    def test_get_by_type(self):
        fade_presets = self.lib.get_by_type(AnimationType.FADE_IN)
        self.assertTrue(any(p.preset_id == "fade_in" for p in fade_presets))

    def test_get_invalid(self):
        with self.assertRaises(KeyError):
            self.lib.get("non_existent_preset")


class TestLayoutLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = LayoutLibrary()

    def test_layout_count(self):
        layouts = self.lib.list_all()
        self.assertGreaterEqual(len(layouts), 10)

    def test_required_layouts_exist(self):
        required_ids = [
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
        for lid in required_ids:
            layout = self.lib.get(lid)
            self.assertEqual(layout.layout_id, lid)
            self.assertIn("grid_template_areas", layout.grid_areas)
            self.assertIn("top", layout.safe_zones)

    def test_filter_by_max_blocks(self):
        quad = self.lib.get_by_max_blocks(4)
        self.assertTrue(any(l.layout_id == "quad_grid" for l in quad))


class TestCameraLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = CameraLibrary()

    def test_preset_count(self):
        presets = self.lib.list_all()
        self.assertGreaterEqual(len(presets), 10)

    def test_required_presets_exist(self):
        required_ids = [
            "static",
            "slow_push_in",
            "slow_pull_out",
            "pan_left",
            "pan_right",
            "parallax_depth",
            "orbit_around",
            "shake_subtle",
            "crane_up",
            "crane_down",
            "whip_pan",
            "dolly_zoom",
        ]
        for cid in required_ids:
            camera = self.lib.get(cid)
            self.assertEqual(camera.preset_id, cid)
            self.assertTrue(camera.css_transform.startswith("@keyframes"))

    def test_get_compatible(self):
        compatible = self.lib.get_compatible("centered_single")
        self.assertTrue(any(c.preset_id == "static" for c in compatible))


class TestTypographyLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = TypographyLibrary()

    def test_required_presets_exist(self):
        required_ids = [
            "heading",
            "subheading",
            "body",
            "caption",
            "accent",
            "kpi_number",
            "subtitle_word",
            "tag",
        ]
        for tid in required_ids:
            typo = self.lib.get(tid)
            self.assertEqual(typo.preset_id, tid)
            css = self.lib.get_css(tid)
            self.assertIn("font-family:", css)
            self.assertIn("font-size:", css)

    test_to_spec = lambda self: self.assertIsNotNone(self.lib.get("heading").to_typography_spec())


if __name__ == "__main__":
    unittest.main()
