# Soundtrack Mixing — voice + music bed + SFX (shipped `b489c2b`)

`msf/audio/soundtrack.py` + `node_soundtrack`, sitting between `voice_synthesis` and
`build_spec`. Read this before touching anything audio in MSF.

## The finding that started it

`msf/audio/` had shipped a ducking mixer, 10 music beds and ~70 SFX since Phase 5 — and
**`grep -rn "msf.audio" msf/graph/` returned nothing**. The modules were written and never
wired. Every video was dry narration over silence, while the mixer sat there fully tested.

Lesson that generalises: when a subsystem "exists but does nothing", grep for its import
from the orchestrator before assuming it's connected. Presence of a module is not evidence
of a call site.

## ONE root wav, not per-scene

The mix is a single wav for the whole video, mounted as the spec's ROOT `audioUrl`, and
`node_soundtrack` **clears every scene's `audio_url`**.

Why it cannot be per-scene:
- a music bed that restarts on every cut is audibly wrong
- `duck_envelope()` needs the WHOLE voice track to decide where to dip

Why the scene keys must be cleared: Remotion mounts `<Audio>` for the root AND for each
scene, so leaving both plays the voice against a copy of itself — comb-filtered mush that
still measures as perfectly healthy audio. `validate_spec` already rejects the combination;
`node_soundtrack` satisfies it by clearing, and `node_repair` must pass `audio_url` too or a
QA retry ships a silent video.

## Three traps, all of which bit

**1. Sample rate — the loudest one.** Qwen3-TTS writes 16-bit mono at **24 kHz**; the mixer
runs at **48 kHz**. Dropping raw samples into the timeline plays the voice at HALF SPEED.
`read_wav_mono()` resamples with `np.interp`. Assert duration, not sample count:

```python
out = read_wav_mono(clip_24k)      # 1.5 s source
assert len(out) == pytest.approx(1.5 * 48000, rel=0.001)
```

**2. Cue timing — transitions OVERLAP.** A transition before scene N pulls N *earlier*; it
does not add time. Summing `durationInFrames` naively walks every cue progressively late (on
an 8-scene spec the last hit landed 2.5 s off). `scene_start_times()` mirrors
`getTransitionPlan()` in `remotion/src/lib/transitions.ts` — if that changes, this must too.

**3. Total duration is NOT the naive sum.** It is the last scene's start plus its own length.
Three 3.0 s scenes with two 0.4 s transitions start at 0.0 / 2.6 / 5.2 and total **8.2 s**,
not 7.8. I asserted 7.8 first and the measurement corrected the test, not the code.

## Degrade vs raise

- unknown music bed or SFX name → print a warning and fall back. A typo must not kill a
  render that already paid minutes of TTS.
- clipping (true peak ≥ 0 dBFS) → **raise**. Shipping distorted audio is worse than failing.

## Prove the mix, don't assert it

`Timeline.render()` returns stems precisely because a mix is unverifiable from its own
output: duck depth means comparing the bed inside vs outside voice windows, impossible once
summed. Measure duck depth from `music` against the `duck_envelope` mask.

Reference numbers from a real 4-scene 10.86 s render:

```
whole track     -19.9 dB mean, -3.1 dB peak, no clipping
under speech    -18.6 dB / -17.8 dB (two separate voice windows)
between clips   -44.0 dB  ← bed present, NOT digital silence (~-90)
duck depth       7.39 dB measured from stems (configured 6 dB)
```

Per-window check on the rendered mp4:

```bash
ffmpeg -hide_banner -i out.mp4 -af "atrim=start=2.32:end=2.54,volumedetect" \
  -f null /dev/null 2>&1 | grep mean_volume
```

**Measured duck depth is lower than configured on short clips** and that is not a bug: the
120 ms attack and 400 ms release ramps count as "active", so on a 1.2 s voice inside a 4 s
window they average the dip upward (2.65 dB vs 7.39 dB on the real mix). Assert the duck is
real and directional, not a specific number.
