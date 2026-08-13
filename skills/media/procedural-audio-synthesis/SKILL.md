---
name: procedural-audio-synthesis
description: "Synthesize SFX/music in numpy; verify by measurement."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [audio, dsp, synthesis, sfx, music, numpy, scipy, loudness, ducking, mixing]
    related_skills: [remotion-video-engineering, video-render-pipeline, seamless-video-audio-stitching, songsee]
---

# Procedural Audio Synthesis

Generating sound effects, music beds, ambience and mixes **in code** (numpy +
scipy) rather than sourcing sample libraries — and proving the result is correct
by measuring it, because almost every failure here is inaudible in a waveform
screenshot and obvious in a number.

> Runnable probe patterns live in `scripts/audio_probe_patterns.py`.
> Placing cues on a video timeline (transition overlap, the silent name-fallback
> trap, the duration oracle) lives in
> `references/audio-timeline-and-cue-placement.md`.

---

## When to use

- Building a library of UI/transition/impact SFX for a video or app pipeline.
- Generating music beds that must sit under narration.
- Mixing voice + music + effects with ducking and a loudness target.
- Debugging "the reverb sounds dry", "the loop clicks", "the music buries the VO".

## When *not* to use

- Speech synthesis — that's TTS (`qwen3-tts`, `cosyvoice-tts`).
- Simple clip concatenation with fades — `seamless-video-audio-stitching`.
- Whole-video mux and ffmpeg `sidechaincompress` — `video-render-pipeline`.
  This skill is for the sample-level layer *feeding* those.

---

## Rule 1 — Synthesize when the renders must be reproducible

Choose synthesis over a CC0/sample library when any of these hold, and say why
in the commit rather than treating it as taste:

- **Reproducibility.** A pure function of `(params, seed)` yields identical
  samples forever; a downloaded asset can move, change, or 404 mid-project.
- **Licence surface.** 112 sourced files is 112 licence checks. Zero synthesized.
- **Parametric retuning.** "Same click, 20 % brighter, 50 ms shorter" is an
  argument change, not a re-sourcing task.
- **Offline.** No network in the render path.

The cost is realism. For anything that must sound like a real room, instrument
or voice, sample beats synthesis — be honest about which side of that line the
job sits on.

---

## Rule 2 — Register sounds by name, with declared budgets

Address sounds by string from the scene/spec layer; never import the function.
That indirection is what lets a JSON spec or CLI flag name a sound.

Each registration declares, at minimum:

| Field | Why it exists |
|---|---|
| `max_ms` | A sound that overruns its budget bleeds into the next scene. The usual way a mix turns to mud. |
| `peak_db` | The level it is *supposed* to hit, checked per effect (see Rule 4). |
| `family` | Groups for level policy and for reporting coverage. |
| `loop` | Whether it is a bed (tiled) or a one-shot. |

A practical level policy: foreground hits at **−18 dBFS**, transition whooshes
**−20**, music beds **−26 LUFS**, ambience 20–30 dB below the foreground.
Normalise per effect at author time so the mixer receives predictable material.

---

## Rule 3 — Primitives worth getting right once

- **Sweeps must integrate frequency.** `sin(2π·f(t)·t)` with varying `f` steps
  audibly. Use `phase = 2π·cumsum(f)/sr`. Verify: max sample-to-sample step stays
  under `2π·f_max/sr`.
- **Biquads via `scipy.signal.lfilter`, never a per-sample Python loop.** Same
  difference equation, ~1000× faster; a hand-rolled loop makes filtering a
  100-sound library impractical (measured: 20 passes over 1 s of audio, 8 ms).
- **Noise colour matters.** White reads as hiss; most physical sources (wind,
  rain, room tone) fall off with frequency. Provide white/pink/brown and assert
  the tilt ordering rather than assuming it.
- **A `place(canvas, sig, at)` helper.** Hand-written
  `canvas[pos:] += sig[:len(canvas)-pos]` only aligns when the signal happens to
  fit, and raises a broadcast error otherwise. Clip once, correctly, in one
  place — this removes an entire class of crash.
- **Fade every boundary.** A hard start/stop is a click. But see Rule 5: the
  fade that fixes a one-shot breaks a loop.

### Reverb: parallel combs, summed once

The classic mistake is to loop over delay lines and rescale the whole signal by
`(1 - amount)` on each pass — every pass then shrinks the previous pass's tail.
Measured result of that bug: a tail at **−132 dBFS with RT40 of 12 ms** —
arithmetically present, completely inaudible. Correct shape is Schroeder:
parallel comb filters summed **once**, then series allpasses to diffuse.
After the fix: **−46.8 dBFS, RT40 445 ms**.

Assert the tail in dB against an audibility threshold (`> −60 dBFS`) and assert
RT40 is a real decay (`> 80 ms`). Never assert "wet ≠ dry".

---

## Rule 4 — Check against the *declared* target, not a global floor

A single global "is it audible" threshold is wrong in both directions. A −40 dB
floor flagged all 14 ambience beds as broken (they are quiet **by design** —
room tone belongs ~30 dB under a UI click) and would equally have passed a
foreground hit that came out 20 dB too soft.

```python
if peak_db < -80:                                   # genuinely dead
    issues.append("SILENT")
elif abs(peak_db - spec.peak_db) > 1.5:             # wrong vs its own contract
    issues.append(f"LEVEL {peak_db:.0f} want {spec.peak_db:.0f}")
```

Same principle for **edge-click detection: measure relative to the signal's own
peak.** An absolute `0.02` threshold passed a quiet sound ending at `0.0188` —
15.6 % of its own peak, an obvious click. Use `edge / peak > 0.02`.

The general lesson: thresholds that ignore the item's own declared scale are
noise generators at one end and blind at the other.

---

## Rule 5 — Loop seams: overlap must exceed the release time

Two traps, in order of discovery:

1. **Don't double-fade.** Beds are usually edge-faded for standalone playback.
   Tiling them then crossfades already-faded material — attenuating twice. Render
   loop material with edge fades **off** (a `raw_render()` context manager beats
   threading a flag through every generator signature).
2. **The overlap must be longer than the longest release.** Each pad note has an
   ADSR release of ~0.3 of a bar, so the *final* bar decays to near-silence
   purely because no bar follows it — measured **−67 dBFS** in the last 100 ms. A
   250 ms crossfade splices copies exactly where one has faded to nothing,
   digging an **11 dB hole once per repetition**. Overlapping by 0.9 s (longer
   than the release) lets the decaying tail sum with the next copy's attack, as
   it would have if the bed had continued. Worst dip: −11.0 dB → **−0.4 dB**.

Use **equal-power (sqrt) curves**, not linear — linear dips at the midpoint,
which on a repeating bed is an audible pulse every loop.

**Measure the seam on a TILED loop, never on a single bed.** Comparing
`sig[0]` to `sig[-1]` is vacuous for an edge-faded bed: it is 0 by construction
and prints a perfect score whether or not looping works. Tile past one bed
length, then compare RMS in a window at each join against a window 0.6 s earlier.

---

## Rule 6 — Ducking needs look-ahead, and voice needs levelling

**Look-ahead is not optional.** A duck computed causally from voice RMS with a
120 ms attack means the first 120 ms of every sentence competes with music at
full level — exactly when the first consonant lands. Shift the key signal forward
by the attack time so the gain has already travelled when speech starts.
Measured: **66 % of full travel at onset, crossing 50 % ~47 ms before it.**

Envelope shape: fast down, slow up (asymmetric one-pole), e.g. 120 ms attack /
400 ms release, keyed off short-window RMS with a threshold gate.

**Level the voice on the way in.** TTS engines, recordings and test fixtures all
arrive at different levels, and a quiet voice track silently *inverts* the whole
design: it still keys the duck, so the music dips — for a voice nobody can hear
over it. A probe's synthetic voice landed at −26.5 LUFS, the same as the bed, and
sat **2.7 dB below** the music it was meant to lead. Normalise voice to a fixed
target (e.g. −16 LUFS against a −26 LUFS bed).

**Measure loudness properly.** Implement ITU-R BS.1770 (K-weighting + gated mean
square) or shell out to ffmpeg `ebur128`. Do not estimate LUFS from peaks.

**Return stems alongside the mix.** A mix is not verifiable from its output
alone: proving the duck works requires the music stem measured inside *and*
outside voice windows, which is impossible once everything is summed.

---

## Rule 7 — Mutation-test every probe before believing it

`ALL PASS` over 112 sounds is a claim about the probe, not about the sounds.
Inject known defects one at a time, confirm each is caught, restore, re-verify:

| Mutation | Should trigger |
|---|---|
| return zeros | SILENT |
| return a 2 s buffer for a 300 ms budget | TOO LONG |
| return `ones * 3.0` | CLIPS |
| drop the fade | EDGE CLICK |
| `default_rng()` with no seed | NONDETERMINISTIC |
| render a hit 12 dB soft / a bed 20 dB loud | LEVEL |
| duck depth 0 dB / attack 2 s with no look-ahead | duck depth / duck timing |

A real run caught 4 of 5 and exposed one blind spot (the edge-click check).
`PROBE HAS BLIND SPOTS` is a far more useful outcome than a green tick. Always
restore the original file and re-run to confirm the restore — a mutation harness
that dies mid-run leaves the codebase broken.

---

## Common pitfalls

- **Determinism is a testability requirement, not a nicety.** Seed every RNG
  (`np.random.default_rng(seed)`); assert `np.array_equal` across two renders.
  Without it no regression is provable.
- **Detune and jitter repeated events.** Summing identical copies gives one loud
  copy, not a pile of coins. Randomise pitch/gain/timing per instance from the
  seeded RNG.
- **Evenly spaced events read as a machine.** Add small timing jitter to typing,
  ticks and footsteps; ease the spacing of a counter so it decelerates onto its
  final value like the animation does.
- **Inharmonic partials make metal sound like metal.** Harmonic stacks read as
  bells; offset the partials for coins, pings and impacts.
- **Comparing rounded RMS values hides everything.** A test printing
  `0.000000 -> 0.000000` reported a broken reverb as a pass. Assert in dB.
- **Guard `x if exists else None` comparisons.** Two missing files compare equal
  and print a bogus match. Assert existence before comparing.
- **Music under speech is a measurement, not a vibe.** Keep beds sparse in the
  200 Hz–2 kHz vocal band and low above 4 kHz (assert HF-to-mid ≤ −12 dB); route
  every bed through one shared lowpass so the rule cannot be forgotten.
- **A registry lookup must raise on an unknown name.** A fallback that quietly
  substitutes (especially from a *sorted* registry dump) turns a typo into a
  plausible-sounding artifact that passes every level, length and clipping check
  while matching nothing on screen — 6 of 8 requested names were invented in one
  run and none of the measurements noticed. Raise `KeyError` listing the misses,
  or at minimum log the substitution table.
- **Cue times are not cumulative scene durations** when the video uses
  overlapping transitions. See `references/audio-timeline-and-cue-placement.md`;
  compare audio and video duration with `ffprobe` as a free oracle on every run.

---

## Reference

- `scripts/audio_probe_patterns.py` — copy-paste probe bodies: registry sweep
  (length/peak/clip/edge/determinism vs declared budgets), reverb tail RT40,
  tiled-loop seam RMS, BS.1770 loudness, duck depth and timing, and the mutation
  harness that validates the probe itself.
