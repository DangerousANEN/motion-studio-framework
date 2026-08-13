#!/usr/bin/env python3
"""Prove the effect no-op contract by rendering and byte-comparing PNGs.

THE PROPERTY UNDER TEST
An effect at intensity=0 must produce pixels identical to not applying it at
all. Anything less means a caller cannot switch the effect off, and "subtle at
zero" compounds across a stack of them. At intensity=1 the output must differ,
which is what proves the effect reaches the pixels rather than merely compiling.

WHY THIS IS A SCRIPT AND NOT THREE SHELL LINES
Four things make the render call fussy, and each one produces a MISLEADING error:

  1. Root.tsx typically gates probe compositions behind a spec-schema parse of
     --props. An invalid spec silently leaves only `Main` registered, and the
     failure reads "Could not find composition with ID X" -- which looks like a
     missing composition, not a rejected spec. So BASE_SPEC below must stay a
     genuinely valid spec (real preset name included) with probe fields merged
     alongside it.
  2. --props must be a path Node can parse. An MSYS path (/c/Users/...) is
     rejected as "neither valid JSON nor a file path"; a path relative to the
     Remotion project directory works.
  3. `npx remotion still` exits 0 when a component throws, rendering an error
     card instead. Exit codes prove nothing here; only pixels do. Note also that
     `sha(x) if exists else None` makes two missing files compare EQUAL, so a
     bogus "no-op confirmed" is easy to print. Existence is asserted first.
  4. A component imported in Root.tsx but never wrapped in <Composition> cannot
     be caught by tsc -- the import IS used. If a composition "doesn't exist",
     grep for `<Composition id=` before debugging anything else.

SAMPLING FRAMES MATTER AS MUCH AS THE EFFECT
An animation that has finished is back at its resting state and looks identical
to bare. Entrance effects are sampled mid-animation, exit effects inside their
exit window (which starts at durationInFrames - EFFECT_FRAMES), loops anywhere.
Six effects "failing" at once is the signature of a wrong sample frame, not six
broken effects.

USAGE
    python effect_noop_proof.py                 # all suites
    python effect_noop_proof.py --list          # show what would run

Adjust ROOT/REMOTION, the probe composition ids, and the prop key to match the
project. Exits non-zero on any failure so it can gate CI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

# --- project layout -------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
REMOTION = ROOT / "remotion"
OUT_REL = "out/pxproof"          # relative on purpose; see trap 2
OUT = REMOTION / "out" / "pxproof"
ENTRY = "src/index.ts"

# A spec that PASSES the project's schema. The probe's own fields ride
# alongside it, because the same object becomes the component's props.
# The preset name must exist in the registry or the whole root fails to
# register its probes (trap 1).
BASE_SPEC = {
    "width": 1080,
    "height": 1920,
    "fps": 60,
    "scenes": [
        {"id": "s", "durationInFrames": 90, "preset": "HeroKinetic", "title": "T"}
    ],
}

# Effects animate over this many frames in the library under test; exit
# effects start at durationInFrames - EFFECT_FRAMES.
EFFECT_FRAMES = 24
SCENE_FRAMES = 90

SUITES = [
    {
        "label": "visual (camera / grade / distortion)",
        "probe": "VisualEffectProbe",
        "bare": "VisualEffectProbeBare",
        "key": "effect",
        "frame": 30,
        "effects": ["ZoomPunch", "PanLeft", "Vignette", "Duotone", "ScanLines", "WaveWarp"],
    },
    {
        "label": "entrance / emphasis",
        "probe": "EffectProbe",
        "bare": "EffectProbeBare",
        # The probe's prop name is not guaranteed to be `name`; read the probe
        # component. Passing the wrong key falls through to the bare branch and
        # every effect looks like a no-op at BOTH intensities.
        "key": "effect",
        "frame": 8,
        "effects": ["FadeIn", "ScaleIn", "Pulse", "Shake", "Breathe", "Bounce", "Glow"],
    },
    {
        # Exit effects start at SCENE_FRAMES - EFFECT_FRAMES = 66 of 90.
        # Sampled any earlier they are correctly doing nothing, which is
        # indistinguishable from being broken.
        "label": "exit (sampled inside the exit window)",
        "probe": "EffectProbe",
        "bare": "EffectProbeBare",
        "key": "effect",
        "frame": SCENE_FRAMES - EFFECT_FRAMES + 12,
        "effects": ["FadeOut", "SlideOutLeft", "ScaleOut", "BlurOut"],
    },
]


def render(comp: str, extra: dict, name: str, frame: int) -> str | None:
    """Render one still. Returns None on success, else a short error string."""
    spec = {**BASE_SPEC, **extra}
    (OUT / "_p.json").write_text(json.dumps(spec), encoding="utf-8")
    r = subprocess.run(
        ["npx", "remotion", "still", ENTRY, comp, f"{OUT_REL}/{name}",
         f"--props={OUT_REL}/_p.json", f"--frame={frame}", "--log=error"],
        cwd=REMOTION, capture_output=True, text=True, shell=True,
    )
    # Exit code is not evidence (trap 3) -- the file is.
    if not (OUT / name).exists():
        tail = [l for l in (r.stdout + r.stderr).splitlines()
                if l.strip() and "puppeteer" not in l.lower()]
        return " | ".join(tail[-2:])[:160] or "no output file"
    return None


def sha(name: str) -> str | None:
    p = OUT / name
    return hashlib.sha1(p.read_bytes()).hexdigest()[:12] if p.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="print the plan and exit")
    args = ap.parse_args()

    if args.list:
        for s in SUITES:
            print(f"{s['label']}: frame {s['frame']}, {len(s['effects'])} effects")
            print("   " + ", ".join(s["effects"]))
        return 0

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    failures: list[str] = []

    for suite in SUITES:
        fr = suite["frame"]
        print(f"\n=== {suite['label']} ===")

        # Bare control is per (probe, frame): sharing one filename across
        # suites overwrites it and compares against the wrong baseline.
        bare_name = f"bare_{suite['probe']}_f{fr}.png"
        err = render(suite["bare"], {}, bare_name, fr)
        if err:
            print(f"  bare control FAILED: {err}")
            failures.append(f"{suite['label']}: bare control")
            continue
        bare = sha(bare_name)
        print(f"  bare control sha={bare}   (sampled at frame {fr})\n")
        print(f"  {'effect':<16}{'i=0 sha':>14}{'no-op?':>9}{'i=1 sha':>14}{'changes?':>10}")
        print("  " + "-" * 64)

        for eff in suite["effects"]:
            n0, n1 = f"{eff}_f{fr}_0.png", f"{eff}_f{fr}_1.png"
            e0 = render(suite["probe"], {suite["key"]: eff, "intensity": 0, "seed": 42}, n0, fr)
            e1 = render(suite["probe"], {suite["key"]: eff, "intensity": 1, "seed": 42}, n1, fr)
            if e0 or e1:
                print(f"  {eff:<16} RENDER FAILED  {e0 or e1}")
                failures.append(f"{eff}: render failed")
                continue

            s0, s1 = sha(n0), sha(n1)
            # Guard against None == None reading as a match (trap 3).
            noop = s0 is not None and s0 == bare
            changes = s1 is not None and s1 != bare
            if not noop:
                failures.append(f"{eff}: not a no-op at intensity 0")
            if not changes:
                failures.append(f"{eff}: intensity 1 changes nothing")
            print(f"  {eff:<16}{str(s0):>14}{'YES' if noop else 'NO':>9}"
                  f"{str(s1):>14}{'YES' if changes else 'NO':>10}")

    print()
    if failures:
        print(f"{len(failures)} PROBLEM(S):")
        for f in failures:
            print(f"  - {f}")
        print("\nBefore blaming the library: an effect failing at EVERY frame is a "
              "wiring/compositing bug; a whole family failing at once is usually a "
              "wrong sample frame or a wrong prop key.")
    else:
        print("ALL PASS - intensity=0 is byte-identical to bare, intensity=1 differs")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
