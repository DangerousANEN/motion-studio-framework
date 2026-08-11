"""Render the demo soundtrack: music bed + SFX hits, ducked and mastered.

Timed against remotion/public/demo_spec.json — the scene boundaries here must
match the spec's durationInFrames, otherwise hits land in the wrong scene.
Transitions overlap scenes, so cue times are approximate by design; they are
placed on scene starts, which stay stable regardless of overlap.

Writes remotion/public/audio/demo_mix.wav and prints the measurements that
prove the mix is correct rather than merely produced.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from msf.audio.mixer import Timeline, measure_lufs, write_wav, SR  # noqa: E402
from msf.audio.sfx import SFX_REGISTRY  # noqa: E402
import msf.audio.sfx_extra  # noqa: F401,E402  (registers the extra 60-odd sounds)
from msf.audio.music import MUSIC_REGISTRY  # noqa: E402

SPEC = ROOT / "remotion" / "public" / "demo_spec.json"
OUT = ROOT / "remotion" / "public" / "audio" / "demo_mix.wav"


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    fps = spec["fps"]

    # Scene start times in seconds.
    #
    # Transitions OVERLAP their neighbours: a 20-frame transition before scene N
    # means scene N starts 20 frames earlier than the running sum of durations
    # suggests. Summing durationInFrames naively put the last cue 2.57s late on
    # this spec and stretched the track 2.5s past the picture. This mirrors
    # getTransitionPlan() in lib/transitions.ts — if that changes, this must too.
    starts, t = [], 0.0
    for scene in spec["scenes"]:
        tr = scene.get("transition")
        if tr:
            t -= tr.get("durationInFrames", 30) / fps
        starts.append(max(0.0, t))
        t += scene["durationInFrames"] / fps
    total = t

    print(f"spec: {len(spec['scenes'])} scenes, {total:.2f}s at {fps}fps")
    print(f"sfx registered: {len(SFX_REGISTRY)}   beds: {len(MUSIC_REGISTRY)}\n")

    # One bed under the whole piece. `tech_pulse`-style beds sit low and leave
    # the mid-range clear, which is what the spectral check in music_probe is for.
    bed = "minimal_pulse" if "minimal_pulse" in MUSIC_REGISTRY else sorted(MUSIC_REGISTRY)[0]
    tl = Timeline().add_music(bed, 0.0, total)

    # One hit per scene start, chosen to match what the scene is doing.
    # Names verified against SFX_REGISTRY, not guessed: hero riser, chat send,
    # AI sweep, wallet coins, card swipe, donut tap, quote chime, stat impact.
    wanted = [
        "riser_short", "send_swoosh", "sync_sweep", "coin_stack",
        "card_swipe", "glass_tap", "success_chime", "impact_hard",
    ]
    available = [w for w in wanted if w in SFX_REGISTRY]
    if len(available) < len(wanted):
        # Fall back to whatever exists rather than crashing on a name guess.
        pool = sorted(SFX_REGISTRY)
        available = (available + [p for p in pool if p not in available])[: len(starts)]

    placed = []
    for i, start in enumerate(starts):
        name = available[i % len(available)]
        # A hair before the cut reads as causing it, rather than reacting to it.
        at = max(0.0, start - 0.04)
        tl.add_sfx(name, at, gain_db=-3.0)
        placed.append((name, at))

    for name, at in placed:
        print(f"  sfx {name:<14} @ {at:6.2f}s")

    result = tl.render(total)
    mix = result["mix"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_wav(str(OUT), mix)

    peak = float(np.max(np.abs(mix)))
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print(f"  duration   {len(mix)/SR:.2f}s")
    print(f"  loudness   {measure_lufs(mix):.2f} LUFS")
    print(f"  true peak  {20*np.log10(peak):.2f} dBFS")
    print(f"  clipping   {'YES' if peak >= 1.0 else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
