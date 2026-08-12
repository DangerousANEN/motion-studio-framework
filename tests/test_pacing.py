"""Pacing contract: reveals must leave time to read, at any scene length.

WHY THIS TEST EXISTS
--------------------
The defect it guards is invisible to every other check. A preset that schedules
its reveals as fractions of durationInFrames renders correctly, overflows
nothing, throws nothing, and still leaves the viewer 0.3s to read the payload —
because a fraction gives reading time proportional to the SCENE, not to the text.

Measured on DefinitionCard at 180 frames before the fix: the definition finished
typing at 2.68s of a 3.0s scene. At 600 frames it would finish at 8.9s of 10s.
Same bug, both times, and a still frame at 90% shows a perfectly composed card.

So the contract is asserted in absolute seconds, and asserted across a range of
scene lengths — a pacing helper that only works at one duration is the original
bug wearing a helper's clothes.

The probe (tools/timing_probe.py) verifies the rendered pixels. This verifies the
arithmetic that decides when to draw them, which is fast enough to run always.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
REMOTION = REPO / "remotion"
PACING_TS = REMOTION / "src" / "lib" / "pacing.ts"

FPS = 60
# Scene lengths to check, in frames: 1.5s (a hard cut), 3s (typical), 10s (long
# explainer), 30s (a whole short in one scene).
DURATIONS = [90, 180, 600, 1800]


def _run_pacing(script: str) -> dict:
    """Evaluate an expression against the real pacing module via esbuild+node."""
    entry = REMOTION / ".test_pacing.entry.ts"
    bundle = REMOTION / ".test_pacing.js"
    entry.write_text(
        "import { settleBy, paceSequence, readingSec, MIN_DWELL_SEC, REVEAL_TAIL_SEC }"
        " from './src/lib/pacing';\n" + script,
        encoding="utf-8",
    )
    try:
        subprocess.run(
            ["npx", "esbuild", str(entry), "--bundle", f"--outfile={bundle}",
             "--platform=node", "--format=cjs", "--log-level=error"],
            cwd=REMOTION, check=True, capture_output=True, shell=True, timeout=180,
        )
        proc = subprocess.run(
            ["node", str(bundle)], cwd=REMOTION, check=True,
            capture_output=True, text=True, shell=True, timeout=120,
        )
        return json.loads(proc.stdout)
    finally:
        entry.unlink(missing_ok=True)
        bundle.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def pacing() -> dict:
    """settleBy / paceSequence outputs for every duration under test."""
    script = f"""
const fps = {FPS};
const durations = {json.dumps(DURATIONS)};
const out = {{ MIN_DWELL_SEC, REVEAL_TAIL_SEC, cases: {{}} }};
for (const d of durations) {{
  const settle = settleBy(d, fps);
  out.cases[d] = {{
    settle,
    chain: paceSequence(Math.round(fps * 0.15), settle, [1, 6, 2, 1]),
    zeroWeights: paceSequence(0, settle, [0, 0]),
    tinyWindow: paceSequence(d, settle, [1, 1]),
  }};
}}
out.reading = {{ short: readingSec('да'), long: readingSec('x'.repeat(240)) }};
console.log(JSON.stringify(out));
"""
    return _run_pacing(script)


def test_pacing_module_exists() -> None:
    assert PACING_TS.exists(), f"missing {PACING_TS}"


def test_settle_leaves_dwell_plus_animation(pacing: dict) -> None:
    """The chain must end early enough for dwell AND the reveal's own animation.

    Scheduling the last reveal to START at duration - dwell leaves dwell minus
    the animation time; that is how a 1.0s request measured 0.77s on screen.
    """
    min_dwell = pacing["MIN_DWELL_SEC"]
    tail = pacing["REVEAL_TAIL_SEC"]
    for dur_s, case in pacing["cases"].items():
        dur = int(dur_s)
        remaining_sec = (dur - case["settle"]) / FPS
        assert remaining_sec >= min_dwell + tail - 0.02, (
            f"{dur}f scene: only {remaining_sec:.2f}s after settle, "
            f"need {min_dwell + tail:.2f}s"
        )


def test_chain_lands_exactly_on_settle(pacing: dict) -> None:
    """No rounding drift: the last step ends ON the settle frame, not past it."""
    for dur_s, case in pacing["cases"].items():
        chain = case["chain"]
        assert chain[-1]["end"] == case["settle"], (
            f"{dur_s}f: chain ends at {chain[-1]['end']}, settle is {case['settle']}"
        )


def test_chain_is_monotonic_and_non_overlapping(pacing: dict) -> None:
    for dur_s, case in pacing["cases"].items():
        chain = case["chain"]
        for a, b in zip(chain, chain[1:]):
            assert a["end"] <= b["start"], f"{dur_s}f: steps overlap: {a} then {b}"


def test_weights_are_proportional(pacing: dict) -> None:
    """Weight 6 must actually get ~6x the frames of weight 1.

    Guards against a helper that distributes evenly and only looks right because
    the totals add up.
    """
    for dur_s, case in pacing["cases"].items():
        f = [s["frames"] for s in case["chain"]]
        if sum(f) < 40:
            continue  # too short to resolve ratios meaningfully
        assert f[1] > f[2] > f[3], f"{dur_s}f: definition/example/source not ordered: {f}"
        ratio = f[1] / max(1, f[0])
        assert 4.0 <= ratio <= 8.0, f"{dur_s}f: weight-6 step is {ratio:.1f}x weight-1"


def test_impossible_window_collapses_to_frame_zero(pacing: dict) -> None:
    """When there is no room, show everything immediately.

    The alternative — silently shrinking the dwell — is the bug this whole module
    exists to prevent.
    """
    for dur_s, case in pacing["cases"].items():
        for step in case["tinyWindow"]:
            assert step == {"start": 0, "end": 0, "frames": 0}, (
                f"{dur_s}f: impossible window produced {step}"
            )


def test_zero_weights_do_not_divide_by_zero(pacing: dict) -> None:
    for dur_s, case in pacing["cases"].items():
        for step in case["zeroWeights"]:
            assert step["frames"] == 0, f"{dur_s}f: zero weights produced {step}"


def test_reading_budget_scales_with_text_and_has_a_floor(pacing: dict) -> None:
    r = pacing["reading"]
    assert r["short"] == pytest.approx(pacing["MIN_DWELL_SEC"]), (
        "a two-character string must still get the minimum dwell"
    )
    assert r["long"] >= 15.0, f"240 chars should need >=15s, got {r['long']}"


def test_probe_and_preset_agree_on_the_contract() -> None:
    """tools/timing_probe.py grades against the same numbers pacing.ts targets.

    If these drift, the probe passes presets that are actually too fast (or fails
    ones that are fine) and the whole measurement is worthless.
    """
    import re

    ts = PACING_TS.read_text(encoding="utf-8")
    py = (REPO / "tools" / "timing_probe.py").read_text(encoding="utf-8")

    def num(pattern: str, text: str) -> float:
        m = re.search(pattern, text)
        assert m, f"cannot find {pattern}"
        return float(m.group(1))

    assert num(r"MIN_DWELL_SEC = ([\d.]+)", ts) == num(r"MIN_DWELL_SEC = ([\d.]+)", py)
    assert num(r"REVEAL_TAIL_SEC = ([\d.]+)", ts) == num(r"REVEAL_TAIL_SEC = ([\d.]+)", py)
    assert num(r"READ_CHARS_PER_SEC = ([\d.]+)", ts) == num(r"CHARS_PER_SEC = ([\d.]+)", py)

    # msf/spec.py warns the author before a render is ever attempted, using the
    # same reading speed.
    spec_py = (REPO / "msf" / "spec.py").read_text(encoding="utf-8")
    assert num(r"READ_CHARS_PER_SEC = ([\d.]+)", ts) == num(
        r"READ_CHARS_PER_SEC = ([\d.]+)", spec_py
    )
