"""Prove a rendered video actually contains its subject, and that it moves.

Written because every cheaper check passed on a broken render:
  * exit code 0, valid mp4, correct duration and file size
  * YMAX=235 -- satisfied entirely by the text overlay
  * an "OBJECT PRESENT" reading that was 100% a gridHelper floor, model absent
  * 8 sampled frames of a "360 orbit" where two were byte-identical (frozen camera)

So this does four things no single check does:
  1. container facts, and the frame-count oracle (sum(durations) - sum(transitions))
  2. TransitionSeries span math, so you never sample inside an overlap by accident
  3. per-frame subject detection in the centre band (ink % + distinct colours)
  4. sha1 across samples, proving motion survived the ENCODE

Usage
-----
    # spans + which frames are safe to sample
    python verify_render.py spans --durations 150,120,120 --transitions 18,18

    # full check against a rendered file
    python verify_render.py check out.mp4 --durations 150,120,120 --transitions 18,18

    # just probe some PNGs you already have
    python verify_render.py probe frame_a.png frame_b.png

Exit code is non-zero when a check fails, so it works in a QA gate.

Requires: ffmpeg/ffprobe on PATH, Pillow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow required: pip install pillow", file=sys.stderr)
    raise SystemExit(2)


# Centre band of a 1080x1920 vertical frame: below the title block, above the
# subtitle card. Override with --band for other layouts.
DEFAULT_BAND = (140, 620, 940, 1300)  # left, top, right, bottom

# A pixel is "ink" when it differs from the sampled background by more than this
# (summed over RGB). Tuned so soft gradients and glows do not trip it.
INK_THRESHOLD = 34

# A shaded PBR mesh yields hundreds of quantised colours; flat UI yields a
# handful. This is what distinguishes a real 3D subject from a text overlay.
MIN_COLOURS_FOR_MESH = 12
MIN_INK_RATIO = 0.02


# --------------------------------------------------------------------------
# 1. timeline arithmetic
# --------------------------------------------------------------------------
def scene_spans(durations: list[int], transitions: list[int]) -> list[tuple[int, int, int]]:
    """Frame span of each scene under TransitionSeries overlap semantics.

    A transition of N frames makes the outgoing scene's last N frames SHARED
    with the incoming scene, so scene starts are not cumulative durations.
    """
    spans, start = [], 0
    for i, dur in enumerate(durations):
        if i > 0:
            start -= transitions[i - 1]
        spans.append((i + 1, start, start + dur))
        start += dur
    return spans


def total_frames(durations: list[int], transitions: list[int]) -> int:
    return sum(durations) - sum(transitions)


def safe_sample_frames(spans, transitions, margin_extra: int = 4) -> dict[int, int]:
    """A frame per scene that is NOT inside any transition overlap."""
    picks = {}
    for idx, (scene, a, b) in enumerate(spans):
        lead = transitions[idx - 1] if idx > 0 else 0
        tail = transitions[idx] if idx < len(transitions) else 0
        lo = a + lead + margin_extra
        hi = b - tail - margin_extra
        picks[scene] = (lo + hi) // 2 if lo < hi else (a + b) // 2
    return picks


# --------------------------------------------------------------------------
# 2. frame extraction from the ENCODED file
# --------------------------------------------------------------------------
def extract_frame(video: Path, frame: int, out: Path) -> bool:
    """Pull one frame out of the encoded video.

    -vsync 0 is required: without it ffmpeg re-times the single output frame and
    can return frame 0 regardless of the select expression.
    """
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(video),
        "-vf", f"select=eq(n\\,{frame})", "-vsync", "0",
        "-frames:v", "1", str(out),
    ]
    subprocess.run(cmd, check=False, capture_output=True)
    return out.exists() and out.stat().st_size > 0


def probe_container(video: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
        "-of", "json", str(video),
    ]
    r = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(r.stdout)["streams"][0]


# --------------------------------------------------------------------------
# 3. subject detection
# --------------------------------------------------------------------------
def analyse(path: Path, band=DEFAULT_BAND) -> dict:
    left, top, right, bottom = band
    img = Image.open(path).convert("RGB")
    px = img.load()
    bg = px[4, 4]

    ink, colours = 0, set()
    sampled = 0
    for y in range(top, min(bottom, img.height), 3):
        for x in range(left, min(right, img.width), 3):
            sampled += 1
            r, g, b = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > INK_THRESHOLD:
                ink += 1
                colours.add((r >> 4, g >> 4, b >> 4))

    ratio = ink / sampled if sampled else 0.0
    if ratio < MIN_INK_RATIO:
        verdict = "EMPTY -- no subject"
    elif len(colours) < MIN_COLOURS_FOR_MESH:
        verdict = f"FLAT -- {len(colours)} colours, likely UI not a shaded mesh"
    else:
        verdict = "SUBJECT PRESENT"
    return {"ink_ratio": ratio, "colours": len(colours), "verdict": verdict, "bg": bg}


def sha(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:12]


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def cmd_spans(args) -> int:
    d = [int(x) for x in args.durations.split(",")]
    t = [int(x) for x in args.transitions.split(",")] if args.transitions else []
    if len(t) != max(0, len(d) - 1):
        print(f"expected {len(d)-1} transitions, got {len(t)}", file=sys.stderr)
        return 2

    spans = scene_spans(d, t)
    print("scene spans (TransitionSeries overlaps neighbours):")
    for scene, a, b in spans:
        print(f"  scene {scene}: frames {a:5d} .. {b:5d}")
    print(f"\ntotal frames = sum(d) - sum(t) = {total_frames(d, t)}")

    print("\noverlap windows -- do NOT assert per-scene content here:")
    for i, tr in enumerate(t):
        s = spans[i + 1][1]
        print(f"  frames {s:5d} .. {s + tr:5d}  (scene {i+1} -> {i+2}, {tr}f)")

    print("\nsafe frames to sample:")
    for scene, f in safe_sample_frames(spans, t).items():
        print(f"  scene {scene}: frame {f}")
    return 0


def cmd_probe(args) -> int:
    failed = 0
    print(f"{'frame':<26}{'ink%':>7}{'colours':>9}  verdict")
    print("-" * 68)
    for p in args.frames:
        path = Path(p)
        if not path.exists():
            print(f"{path.name:<26}{'-':>7}{'-':>9}  MISSING")
            failed += 1
            continue
        r = analyse(path)
        if "PRESENT" not in r["verdict"]:
            failed += 1
        print(f"{path.name:<26}{r['ink_ratio']*100:>6.1f}%{r['colours']:>9}  {r['verdict']}")
    return 1 if failed else 0


def cmd_check(args) -> int:
    video = Path(args.video)
    if not video.exists():
        print(f"no such file: {video}", file=sys.stderr)
        return 2

    d = [int(x) for x in args.durations.split(",")]
    t = [int(x) for x in args.transitions.split(",")] if args.transitions else []

    info = probe_container(video)
    nb = int(info.get("nb_frames") or 0)
    expected = total_frames(d, t)
    print("=== CONTAINER ===")
    print(f"  {info['width']}x{info['height']}  fps={info['r_frame_rate']}  "
          f"frames={nb}  dur={float(info['duration']):.2f}s")
    print(f"  expected {expected} -> {'MATCH' if nb == expected else 'MISMATCH'}")
    ok = nb == expected

    spans = scene_spans(d, t)
    picks = safe_sample_frames(spans, t)

    print("\n=== SUBJECT PER SCENE (sampled outside transition overlaps) ===")
    with tempfile.TemporaryDirectory() as tmp:
        hashes = {}
        for scene, frame in picks.items():
            out = Path(tmp) / f"s{scene}_{frame}.png"
            if not extract_frame(video, frame, out):
                print(f"  scene {scene} frame {frame}: EXTRACTION FAILED")
                ok = False
                continue
            r = analyse(out)
            hashes[f"s{scene}"] = sha(out)
            if "PRESENT" not in r["verdict"]:
                ok = False
            print(f"  scene {scene} frame {frame:5d}: {r['ink_ratio']*100:5.1f}% ink, "
                  f"{r['colours']:4d} colours  {r['verdict']}")

        # motion: several frames within the FIRST scene must differ
        print("\n=== MOTION (frames must differ inside the encode) ===")
        _, a, b = spans[0]
        tail = t[0] if t else 0
        lo, hi = a + 4, b - tail - 4
        motion_frames = [lo, (lo + hi) // 2, hi] if lo < hi else [a, (a + b) // 2, b - 1]
        mh = []
        for f in motion_frames:
            out = Path(tmp) / f"m{f}.png"
            if extract_frame(video, f, out):
                h = sha(out)
                mh.append(h)
                print(f"  frame {f:5d}: {h}")
        distinct = len(set(mh))
        print(f"  distinct: {distinct}/{len(mh)} -> "
              f"{'MOVING' if distinct == len(mh) else 'STATIC OR FROZEN'}")
        if mh and distinct != len(mh):
            ok = False

    print("\n" + ("ALL CHECKS PASSED" if ok else "FAILED -- see above"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("spans", help="scene spans + safe sample frames")
    sp.add_argument("--durations", required=True, help="comma list, e.g. 150,120,120")
    sp.add_argument("--transitions", default="", help="comma list, e.g. 18,18")
    sp.set_defaults(func=cmd_spans)

    pr = sub.add_parser("probe", help="subject detection on PNGs")
    pr.add_argument("frames", nargs="+")
    pr.set_defaults(func=cmd_probe)

    ck = sub.add_parser("check", help="full check on a rendered video")
    ck.add_argument("video")
    ck.add_argument("--durations", required=True)
    ck.add_argument("--transitions", default="")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
