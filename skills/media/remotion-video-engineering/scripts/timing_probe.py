"""Measure WHEN each element appears and HOW LONG it stays readable.

WHY THIS EXISTS
---------------
Layout probes answer "is it inside the frame". They cannot answer "was it on
screen long enough to read", which is a real and systematic defect class: an
element legitimately revealed at 78% of a scene sits there for half a second and
gets cut. Nothing overflows, nothing errors, tsc is clean, and a still frame at
90% looks perfectly composed. See references/reveal-pacing-and-dwell-time.md.

INPUT
-----
A rendered frame SEQUENCE, produced by one bundle pass:

    npx remotion render src/index.ts Main out/timing/<name> \
        --sequence --props=<spec>.json --scale=0.5 --log=error

plus a sibling `<name>.meta.json` carrying {name, fps, durationInFrames, every,
text}. Two pitfalls in that render step:
  * --sequence needs an output DIRECTORY and refuses a non-empty one; rm it first.
  * Remotion writes element-000.jpeg (JPEG, not PNG). Filtering on .png reports
    "0 frames" while the render actually succeeded.

WHAT IT MEASURES
----------------
Per horizontal band of the frame:
  * first frame the band has content (differs from the first frame)
  * first frame it STOPS changing meaningfully (its reveal is done)
  * how long it stays settled before the sequence ends

Dwell is measured from SETTLE, not from appear. A typewriter reveal "appears" at
frame 24 and is still spelling itself out at frame 140; the viewer can only read
it from the settle point on.

USAGE
    python timing_probe.py out/timing/<name> [more dirs...]

Prints one JSON object per directory. `pacing` is a preset bug (fix the reveal
schedule); `duration` is a spec bug (the script asks for more text than the clock
allows — fix it upstream, do not touch the preset).

KEEP THE CONSTANTS IN SYNC with whatever the presets target (e.g. a pacing.ts
exporting MIN_DWELL_SEC / REVEAL_TAIL_SEC / READ_CHARS_PER_SEC) and assert the
match in a test. If the grader and the target drift, this probe passes presets
that are actually too fast.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Reading speed used for the dwell budget (characters per second). Deliberately
# generous — a viewer re-reads a headline rather than parsing it once.
CHARS_PER_SEC = 12.0
# No element should be readable for less than this, however short its text.
MIN_DWELL_SEC = 1.0
# A reveal animation's own duration. A schedule that merely STARTS at
# `duration - dwell` delivers `dwell` minus this; asking 1.0s measured 0.77s.
REVEAL_TAIL_SEC = 0.25
# Bands: the frame is split into this many horizontal strips.
BANDS = 12
# A band "has content" when this fraction of its pixels differ from the baseline.
CONTENT_FRAC = 0.0015
# Absolute floor on "stopped changing", below the peak-relative floor.
SETTLE_FRAC = 0.0008
# Sequences are normally rendered at 0.5 scale; y values are reported x this.
SCALE_BACK = 2


def load_sequence(d: Path) -> tuple[list[int], np.ndarray]:
    """Frame numbers and a stacked greyscale array, ordered by frame number."""
    files = sorted(
        (p for p in d.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"}),
        key=lambda p: int(re.sub(r"\D", "", p.stem) or 0),
    )
    if not files:
        raise SystemExit(f"no frames in {d} (did you filter on .png? Remotion writes .jpeg)")
    nums = [int(re.sub(r"\D", "", p.stem) or 0) for p in files]
    stack = np.stack([np.asarray(Image.open(p).convert("L"), dtype=np.int16) for p in files])
    return nums, stack


def band_slices(height: int, bands: int) -> list[tuple[int, int]]:
    edges = np.linspace(0, height, bands + 1).astype(int)
    return [(edges[i], edges[i + 1]) for i in range(bands)]


def analyse(seq_dir: Path) -> dict:
    meta_path = seq_dir.parent / f"{seq_dir.name}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    fps = float(meta.get("fps", 60))
    total = int(meta.get("durationInFrames", 0))
    every = int(meta.get("every", 1)) or 1

    nums, stack = load_sequence(seq_dir)
    n_frames, h, _w = stack.shape
    baseline = stack[0]

    rows = []
    for bi, (y0, y1) in enumerate(band_slices(h, BANDS)):
        band = stack[:, y0:y1, :]
        base = baseline[y0:y1, :]

        # Content: differs from the first frame by a visible margin.
        diff_base = (np.abs(band - base) > 12).reshape(n_frames, -1).mean(1)
        has = diff_base > CONTENT_FRAC
        appear_i = int(np.argmax(has)) if has.any() else None

        if appear_i is None:
            rows.append({"band": bi, "y": [int(y0) * SCALE_BACK, int(y1) * SCALE_BACK],
                         "empty": True})
            continue

        # Settled: consecutive frames stop changing MEANINGFULLY.
        #
        # An absolute threshold is wrong. Presets pulse "current" markers with an
        # endless sine, and a perpetual small wobble never drops below a fixed
        # floor — those bands measure "never settles, dwell 0.00s" and look like
        # catastrophic late reveals when nothing is wrong. So the floor is
        # relative to the band's OWN peak motion: once change drops under 8% of
        # the largest change this band ever saw, the reveal is done and what
        # remains is decoration.
        step = (np.abs(np.diff(band, axis=0)) > 10).reshape(n_frames - 1, -1).mean(1)
        peak = float(step[appear_i:].max()) if appear_i < len(step) else 0.0
        floor = max(SETTLE_FRAC, peak * 0.08)
        quiet = step < floor

        settle_i = None
        for i in range(appear_i, len(quiet)):
            if quiet[i:].all():
                settle_i = i
                break

        perpetual = False
        if settle_i is None:
            settle_i = n_frames - 1
            # Never settles. Two very different causes, and conflating them sends
            # you hunting a bug that does not exist:
            #   a) a genuinely late reveal — motion RAMPS and ends near the cut
            #   b) perpetual decoration — e.g. sparks reseeded from `frame`, so
            #      hundreds of pixels change every frame, first to last, forever.
            # The peak-relative floor cannot catch (b): the change is large, not
            # subtle.
            #
            # THE THRESHOLD MATTERS. At `last/first > 0.5` a real score-roll
            # defect (measured ratio 0.54, cv 1.37) was classified as perpetual,
            # so the probe reported OK while the number was still counting at
            # 99.4% of the scene — the carve-out masked the very defect it was
            # written to distinguish itself from, by UPGRADING a verdict.
            # True shimmer measured ratio 1.02, cv 0.43. So require BOTH
            # near-constant energy and low variability; a decaying or bursty
            # profile is a reveal.
            tail = step[appear_i:]
            if len(tail) >= 6:
                third = max(2, len(tail) // 3)
                first_mean = float(tail[:third].mean())
                last_mean = float(tail[-third:].mean())
                mean = float(tail.mean())
                cv = float(tail.std()) / mean if mean > 0 else 99.0
                ratio = last_mean / first_mean if first_mean > 0 else 0.0
                perpetual = ratio >= 0.8 and cv < 0.8

        appear_f = int(nums[appear_i])
        settle_f = int(nums[min(settle_i, n_frames - 1)])
        last_f = int(nums[-1]) + every - 1
        dwell_frames = max(0, last_f - settle_f)
        rows.append(
            {
                "band": bi,
                "y": [int(y0) * SCALE_BACK, int(y1) * SCALE_BACK],
                "empty": False,
                "appear_frame": appear_f,
                "appear_sec": round(appear_f / fps, 2),
                "settle_frame": settle_f,
                "settle_sec": round(settle_f / fps, 2),
                "dwell_frames": dwell_frames,
                "dwell_sec": round(dwell_frames / fps, 2),
                "settle_pct": round(100 * settle_f / max(1, total), 1),
                "perpetual": perpetual,
            }
        )

    # Reading budget from the scene's own text.
    text = " ".join(meta.get("text", []))
    chars = len(text)
    need_sec = max(MIN_DWELL_SEC, chars / CHARS_PER_SEC)

    # Perpetually animated bands are excluded from the dwell verdict: decoration
    # has no settle point by design and is not a late reveal. ALWAYS re-grade a
    # known-BAD render after touching this exclusion — see the note above.
    filled = [r for r in rows if not r["empty"]]
    judged = [r for r in filled if not r.get("perpetual")]
    worst = min(judged, key=lambda r: r["dwell_sec"]) if judged else None

    # Two independent failures with different owners. Collapsing them into one
    # "TOO_FAST" verdict sends you editing a preset when the real problem is 176
    # characters in a 3-second scene.
    paced_ok = bool(worst) and worst["dwell_sec"] >= MIN_DWELL_SEC - 0.05
    fits_reading = total / fps >= need_sec
    return {
        "scene": seq_dir.name,
        "fps": fps,
        "duration_frames": total,
        "duration_sec": round(total / fps, 2),
        "chars_on_screen": chars,
        "reading_budget_sec": round(need_sec, 2),
        "bands": rows,
        "worst_band_dwell_sec": worst["dwell_sec"] if worst else None,
        "perpetual_bands": [r["band"] for r in filled if r.get("perpetual")],
        "pacing": "OK" if paced_ok else "REVEALS_TOO_LATE",
        "duration": "OK" if fits_reading else "SCENE_TOO_SHORT_FOR_TEXT",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    for arg in sys.argv[1:]:
        print(json.dumps(analyse(Path(arg)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
