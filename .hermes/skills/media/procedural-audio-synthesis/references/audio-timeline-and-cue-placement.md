# Audio timeline & cue placement

Placing SFX and music cues on a video timeline **without guessing the timeline** —
the recurring failure mode of a soundtrack generator that reads a scene list.

Companion to Rule 6 (ducking) and Rule 7 (mutation-test every probe).

---

## 1. Cue times must come from the video's own transition planner

A `TransitionSeries` (Remotion) overlaps neighbours: every transition's frames are
shared between the outgoing and incoming scene, so the picture is **shorter** than
the sum of scene durations. A generator that walks the scene list accumulating
`durationInFrames` places every cue after the first transition too late, and
renders a track longer than the picture.

Measured on an 8-scene demo with 7 transitions totalling 154 overlap frames:

| | naive sum | after fix |
|---|---|---|
| audio track | 22.50 s | 19.93 s |
| video (`ffprobe`) | 19.99 s | 19.99 s |
| last SFX hit | **+2.57 s late** | on the cut |

Drift is cumulative, so the first scene looks perfect and the problem is only
obvious at the end — exactly the part a quick listen skips.

Mirror the composition's planner instead of re-deriving starts:

```python
starts, t = [], 0.0
for scene in spec["scenes"]:
    tr = scene.get("transition")
    if tr:
        t -= tr.get("durationInFrames", 30) / fps   # overlap pulls this scene earlier
    starts.append(max(0.0, t))
    t += scene["durationInFrames"] / fps
total = t
```

If the video side changes its planner, this must change with it — leave a comment
naming the file it mirrors (`lib/transitions.ts :: getTransitionPlan`).

**Two free oracles, both one command:**

- `ffprobe -v error -show_entries format=duration` on the audio and on the video.
  A gap larger than one frame means the layers disagree about the timeline.
- Assert every cue lands inside its scene's span *outside* the overlap window.
  A cue inside a crossfade fires against the wrong picture even when the totals
  happen to match.

A hit reads as *causing* the cut when placed ~40 ms before it, not on it.

---

## 2. Verify sound names against the registry — a silent fallback hides typos

Requesting names from memory gets most of them wrong. In one run 6 of 8 were
invented (`whoosh_soft`, `ui_tap`, `coin_drop`, `card_flip`, `pop_soft`,
`chime_soft`), and a "helpfully" permissive fallback substituted alphabetically
sorted registry entries — yielding `riser_short, arp_down, arp_up, atm_dispense,
balance_down…`, a soundtrack whose hits matched nothing on screen. Every
measurement still passed: correct length, `−14.00 LUFS`, no clipping. Nothing
surfaced the mismatch because nothing was *wrong*, only meaningless.

Make the fallback fail loudly:

```python
missing = [w for w in wanted if w not in SFX_REGISTRY]
if missing:
    raise KeyError(f"unknown sfx {missing}; {len(SFX_REGISTRY)} registered")
```

If a graceful degrade is genuinely needed, print the substitution table so it
appears in the run log. Silent substitution converts a loud `KeyError` into a
plausible-sounding artifact, which is strictly worse.

Cheap discovery of real names before writing the generator:

```python
for kw in ["whoosh", "riser", "impact", "click", "card", "coin", "chime"]:
    print(kw, [n for n in sorted(SFX_REGISTRY) if kw in n][:6])
```

---

## 3. One spec drives both layers

Generate the soundtrack from the **same JSON** the video renders from — never
from a parallel copy of the scene list. `fps`, `durationInFrames`, `transition`
all come from the spec, so the two cannot drift; when they do, §1's duration
oracle catches it first.

Re-measure after *any* edit to the generator. A mix is not "still fine" because
the change looked unrelated: re-assert track length, loudness (`−14.00 LUFS`),
true peak (`−0.69 dBFS`) and no clipping, and print them.
