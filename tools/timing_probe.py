"""Measure WHEN each element appears and HOW LONG it stays readable.

WHY THIS EXISTS
---------------
Layout probes answer "is it inside the frame". They cannot answer "was it on
screen long enough to read", which is the defect the channel actually suffers
from: an element legitimately revealed at 78% of a scene sits there for half a
second and gets cut. Nothing overflows, nothing errors, and the viewer misses it.

WHAT IT MEASURES
----------------
For a rendered frame sequence (scripts/timing.mjs), per horizontal band of the
frame:
  * first frame the band has content (differs from the empty/first frame)
  * first frame the band STOPS changing (settled — its reveal animation is done)
  * how many frames it stays settled before the sequence ends

The settle point matters more than the appear point. A typewriter reveal "appears"
at frame 24 and is still spelling itself out at frame 140; the viewer can only
read it from the settle point on. Dwell is therefore measured from settle, not
from appear.

READING BUDGET
--------------
Russian prose reads at roughly 900-1100 characters per minute on a phone, so
~16 chars/sec. A band holding N characters needs N/16 seconds AFTER it settles.
The check is deliberately generous (12 chars/sec, floor of 0.8s) because a
viewer re-reads a headline rather than parsing it once.

USAGE
    python tools/timing_probe.py remotion/out/timing/definition
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Reading speed used for the dwell budget (characters per second).
CHARS_PER_SEC = 12.0
# No element should be readable for less than this, however short its text.
MIN_DWELL_SEC = 1.0
# Mirrors REVEAL_TAIL_SEC in remotion/src/lib/pacing.ts. The two must agree or
# the probe grades a preset against a different contract than the preset targets.
REVEAL_TAIL_SEC = 0.25
# Bands: the frame is split into this many horizontal strips.
BANDS = 12
# A band "has content" when this fraction of its pixels differ from the baseline.
CONTENT_FRAC = 0.0015
# A band is "settled" when consecutive frames differ by less than this fraction.
SETTLE_FRAC = 0.0008


def load_sequence(d: Path) -> tuple[list[int], np.ndarray]:
    """Frame numbers and a stacked greyscale array, ordered by frame number."""
    files = sorted(
        (p for p in d.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"}),
        key=lambda p: int(re.sub(r"\D", "", p.stem) or 0),
    )
    if not files:
        raise SystemExit(f"no frames in {d}")
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
    n_frames, h, w = stack.shape
    baseline = stack[0]
    px_per_band = (h // BANDS) * w

    rows = []
    for bi, (y0, y1) in enumerate(band_slices(h, BANDS)):
        band = stack[:, y0:y1, :]
        base = baseline[y0:y1, :]

        # Content: differs from the first frame by a visible margin.
        diff_base = (np.abs(band - base) > 12).reshape(n_frames, -1).mean(1)
        has = diff_base > CONTENT_FRAC
        appear_i = int(np.argmax(has)) if has.any() else None

        # Settled: consecutive frames stop changing MEANINGFULLY.
        #
        # An absolute threshold is wrong here. ProgressPath pulses its current dot
        # with an endless sine, TimelineReveal pulses its active dot, and a
        # perpetual 12%-scale wobble on a 56px dot never falls below a fixed
        # floor — so those bands measured "never settles" (dwell 0.00s) and looked
        # like catastrophic late reveals when nothing was wrong. A viewer reads
        # straight through a subtle pulse.
        #
        # So settle is relative to the band's OWN peak motion: once change drops
        # under 8% of the largest change this band ever saw, the reveal is done and
        # what remains is decoration.
        step = (np.abs(np.diff(band, axis=0)) > 10).reshape(n_frames - 1, -1).mean(1)
        settle_i = None
        if appear_i is not None:
            peak = float(step[appear_i:].max()) if appear_i < len(step) else 0.0
            floor = max(SETTLE_FRAC, peak * 0.08)
            quiet = step < floor
            # First frame from which it stays quiet to the end.
            for i in range(appear_i, len(quiet)):
                if quiet[i:].all():
                    settle_i = i
                    break
            if settle_i is None:
                settle_i = n_frames - 1

        if appear_i is None:
            rows.append({"band": bi, "y": [int(y0) * 2, int(y1) * 2], "empty": True})
            continue

        appear_f = int(nums[appear_i])
        settle_f = int(nums[min(settle_i, n_frames - 1)])
        last_f = int(nums[-1]) + every - 1
        dwell_frames = max(0, last_f - settle_f)
        rows.append(
            {
                "band": bi,
                "y": [int(y0) * 2, int(y1) * 2],  # x2: sequence rendered at 0.5 scale
                "empty": False,
                "appear_frame": appear_f,
                "appear_sec": round(appear_f / fps, 2),
                "settle_frame": settle_f,
                "settle_sec": round(settle_f / fps, 2),
                "dwell_frames": dwell_frames,
                "dwell_sec": round(dwell_frames / fps, 2),
                "settle_pct": round(100 * settle_f / max(1, total), 1),
            }
        )

    # Reading budget from the scene's own text.
    text = " ".join(meta.get("text", []))
    chars = len(text)
    need_sec = max(MIN_DWELL_SEC, chars / CHARS_PER_SEC)

    filled = [r for r in rows if not r["empty"]]
    worst = min(filled, key=lambda r: r["dwell_sec"]) if filled else None

    # Two independent failures, kept separate because they are fixed in different
    # places. A preset that reveals too late is a preset bug. A scene too short
    # for the text it carries is a SPEC bug — the pipeline sizes duration from the
    # narration, so the script is asking for more than the clock allows.
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
        "pacing": "OK" if paced_ok else "REVEALS_TOO_LATE",
        "duration": "OK" if fits_reading else "SCENE_TOO_SHORT_FOR_TEXT",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    for arg in sys.argv[1:]:
        res = analyse(Path(arg))
        print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
