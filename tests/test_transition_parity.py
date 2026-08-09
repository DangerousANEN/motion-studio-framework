"""Transition parity: Python and TypeScript must agree.

Three lists describe the same closed set of transitions:
  - TRANSITIONS in msf/spec.py
  - TRANSITION_NAMES in remotion/src/lib/transitions.ts
  - TransitionTypeSchema in remotion/src/VideoSpec.schema.ts

And two implementations compute the same composition length:
  - compute_total_frames() in msf/spec.py
  - getTransitionPlan() in remotion/src/lib/transitions.ts

If either pair drifts, videos break in ways that are expensive to notice:
an unknown name renders a red ERROR card, and a wrong frame count desyncs the
voice-over from the picture. These tests make the drift fail here instead.

stdlib unittest — the project has no pytest and no virtualenv.
Run: python tests/test_transition_parity.py
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from msf.spec import (  # noqa: E402
    DEFAULT_TRANSITION_FRAMES,
    TRANSITIONS,
    compute_total_frames,
)

TRANSITIONS_TS = ROOT / "remotion" / "src" / "lib" / "transitions.ts"
SCHEMA_TS = ROOT / "remotion" / "src" / "VideoSpec.schema.ts"

# Shared fixtures. Each case is (label, scenes). Chosen to cover the edge cases
# that actually bite: no transitions, defaults, explicit lengths, 'none',
# a transition longer than its neighbour (must clamp), and a transition
# illegally declared on scene 0 (must be ignored, not subtracted).
CASES = [
    (
        "no transitions",
        [{"durationInFrames": 120}, {"durationInFrames": 90}],
    ),
    (
        "default duration",
        [{"durationInFrames": 120}, {"durationInFrames": 90, "transition": {"type": "fade"}}],
    ),
    (
        "explicit duration",
        [
            {"durationInFrames": 120},
            {"durationInFrames": 90, "transition": {"type": "wipe", "durationInFrames": 30}},
        ],
    ),
    (
        "type none is free",
        [{"durationInFrames": 120}, {"durationInFrames": 90, "transition": {"type": "none"}}],
    ),
    (
        "clamped to short neighbour",
        [
            {"durationInFrames": 10},
            {"durationInFrames": 90, "transition": {"type": "fade", "durationInFrames": 60}},
        ],
    ),
    (
        "transition on scene 0 ignored",
        [
            {"durationInFrames": 120, "transition": {"type": "fade"}},
            {"durationInFrames": 90},
        ],
    ),
    (
        "many scenes mixed",
        [
            {"durationInFrames": 150},
            {"durationInFrames": 120, "transition": {"type": "slide", "durationInFrames": 20}},
            {"durationInFrames": 100, "transition": {"type": "none"}},
            {"durationInFrames": 90, "transition": {"type": "iris"}},
            {"durationInFrames": 60, "transition": {"type": "zoomBlur", "durationInFrames": 12}},
        ],
    ),
    (
        "single scene",
        [{"durationInFrames": 90}],
    ),
]


def ts_list(path: Path, start_marker: str) -> list:
    """Pull a string-literal array out of a TS source file."""
    text = path.read_text(encoding="utf-8")
    idx = text.index(start_marker)
    block = text[idx : text.index("]", idx)]
    return re.findall(r"'([a-zA-Z]+)'", block)


class TestTransitionNameParity(unittest.TestCase):
    def test_transitions_ts_matches_python(self):
        ts_names = ts_list(TRANSITIONS_TS, "export const TRANSITION_NAMES")
        self.assertEqual(
            sorted(ts_names),
            sorted(TRANSITIONS),
            "TRANSITION_NAMES in transitions.ts has drifted from TRANSITIONS in msf/spec.py.",
        )

    def test_schema_ts_matches_python(self):
        ts_names = ts_list(SCHEMA_TS, "export const TransitionTypeSchema")
        self.assertEqual(
            sorted(ts_names),
            sorted(TRANSITIONS),
            "TransitionTypeSchema in VideoSpec.schema.ts has drifted from msf/spec.py.",
        )

    def test_default_frames_match(self):
        text = TRANSITIONS_TS.read_text(encoding="utf-8")
        m = re.search(r"DEFAULT_TRANSITION_FRAMES\s*=\s*(\d+)", text)
        self.assertIsNotNone(m, "DEFAULT_TRANSITION_FRAMES not found in transitions.ts")
        self.assertEqual(
            int(m.group(1)),
            DEFAULT_TRANSITION_FRAMES,
            "Default transition length differs between Python and TypeScript.",
        )


class TestFrameMathParity(unittest.TestCase):
    """Run the real TS getTransitionPlan and compare to Python, case by case."""

    @classmethod
    def setUpClass(cls):
        cls.ts_results = cls._run_ts()

    @staticmethod
    def _run_ts():
        """Execute getTransitionPlan() via esbuild+node and return its numbers.

        Uses the project's own esbuild (already a Remotion dependency) to strip
        types, so this exercises the actual shipped implementation rather than a
        hand-copied version of it.
        """
        remotion_dir = ROOT / "remotion"
        esbuild = remotion_dir / "node_modules" / ".bin" / "esbuild.cmd"
        if not esbuild.exists():
            esbuild = remotion_dir / "node_modules" / ".bin" / "esbuild"
        if not esbuild.exists():
            raise unittest.SkipTest("esbuild not available in remotion/node_modules")

        cases_json = json.dumps([scenes for _, scenes in CASES])
        entry = remotion_dir / ".transition_parity_probe.ts"
        # Import only the pure planner. Pulling in buildPresentation would drag
        # React and the whole transitions package into a plain node process.
        entry.write_text(
            "import { getTransitionPlan } from './src/lib/transitions';\n"
            f"const cases = {cases_json};\n"
            "const out = cases.map((scenes: any) => {\n"
            "  const p = getTransitionPlan(scenes);\n"
            "  return { total: p.totalDurationInFrames, overlap: p.overlapFrames,\n"
            "           count: p.transitions.length };\n"
            "});\n"
            "console.log(JSON.stringify(out));\n",
            encoding="utf-8",
        )
        bundle = remotion_dir / ".transition_parity_probe.js"
        try:
            subprocess.run(
                [str(esbuild), str(entry), "--bundle", "--platform=node",
                 "--format=cjs", f"--outfile={bundle}", "--log-level=error"],
                cwd=str(remotion_dir), check=True, capture_output=True, timeout=180,
            )
            proc = subprocess.run(
                ["node", str(bundle)],
                cwd=str(remotion_dir), check=True, capture_output=True,
                text=True, timeout=120,
            )
            return json.loads(proc.stdout.strip())
        finally:
            entry.unlink(missing_ok=True)
            bundle.unlink(missing_ok=True)

    def test_totals_match_typescript(self):
        self.assertEqual(len(self.ts_results), len(CASES))
        for (label, scenes), ts in zip(CASES, self.ts_results):
            with self.subTest(case=label):
                py_total = compute_total_frames(scenes)
                self.assertEqual(
                    py_total,
                    ts["total"],
                    f"[{label}] Python says {py_total} frames, TypeScript says "
                    f"{ts['total']}. A mismatch desyncs audio from video.",
                )

    def test_known_values(self):
        """Pin the arithmetic so a coordinated change to both sides still fails."""
        # 120 + 90, one 18-frame default overlap.
        self.assertEqual(compute_total_frames(CASES[1][1]), 120 + 90 - 18)
        # explicit 30-frame overlap
        self.assertEqual(compute_total_frames(CASES[2][1]), 120 + 90 - 30)
        # 'none' costs nothing
        self.assertEqual(compute_total_frames(CASES[3][1]), 120 + 90)
        # clamp: neighbour is 10 frames, so overlap is 9, not the requested 60
        self.assertEqual(compute_total_frames(CASES[4][1]), 10 + 90 - 9)
        # scene 0 transition contributes nothing
        self.assertEqual(compute_total_frames(CASES[5][1]), 120 + 90)


class TestTransitionValidation(unittest.TestCase):
    def test_unknown_transition_rejected(self):
        from msf.spec import validate_spec
        spec = {
            "fps": 60, "width": 1080, "height": 1920,
            "scenes": [
                {"durationInFrames": 90, "preset": "HeroKinetic", "title": "A"},
                {"durationInFrames": 90, "preset": "HeroKinetic", "title": "B",
                 "transition": {"type": "fadey"}},
            ],
        }
        with self.assertRaises(ValueError) as ctx:
            validate_spec(spec)
        self.assertIn("unknown transition", str(ctx.exception))

    def test_all_known_transitions_accepted(self):
        from msf.spec import validate_spec
        for name in TRANSITIONS:
            spec = {
                "fps": 60, "width": 1080, "height": 1920,
                "scenes": [
                    {"durationInFrames": 90, "preset": "HeroKinetic", "title": "A"},
                    {"durationInFrames": 90, "preset": "HeroKinetic", "title": "B",
                     "transition": {"type": name}},
                ],
            }
            with self.subTest(transition=name):
                validate_spec(spec)

    def test_transition_on_first_scene_rejected(self):
        from msf.spec import validate_spec
        spec = {
            "fps": 60, "width": 1080, "height": 1920,
            "scenes": [
                {"durationInFrames": 90, "preset": "HeroKinetic", "title": "A",
                 "transition": {"type": "fade"}},
            ],
        }
        with self.assertRaises(ValueError) as ctx:
            validate_spec(spec)
        self.assertIn("scene[0]", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
