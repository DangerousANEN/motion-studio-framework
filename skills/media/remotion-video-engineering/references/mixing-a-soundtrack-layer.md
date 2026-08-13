# Mixing a soundtrack layer into a render pipeline (voice + music bed + SFX)

Companion to `audio-track-silence-diagnosis.md` (detecting silence) and
`wiring-voiceover-and-proving-a-crossfade.md` (getting narration to play at all). This
file covers the next layer: an audio package that exists in the tree but was never wired
in, and the numeric failures that show up the moment you wire it.

Measured on MSF (Remotion + Python LangGraph), where `msf/audio/` had shipped a ducking
mixer, 10 music beds and ~70 SFX for a whole phase while `grep -rn "msf.audio" msf/graph/`
returned **nothing**. Every video was dry narration over silence.

---

## 1. Find the unwired module before designing anything new

The tell is not a missing file, it is a missing **import**:

```bash
grep -rn "msf\.audio" msf/graph/     # -> no hits, while msf/audio/ has 4 modules
grep -rn "from msf.audio" tools/     # -> one demo script, never called by the pipeline
```

A demo/tooling script that exercises the package (here `tools/render_demo_audio.py`, which
built a bed + SFX mix correctly) is worth reading before writing a node: it already encodes
the level choices (`gain_db=-3.0` on accents, cue placed `0.04 s` *before* the cut so it
reads as causing it) that the author validated once and nobody promoted into the pipeline.

## 2. Mixing cannot be per scene — it has to be one track

Two hard reasons, both architectural rather than stylistic:

- A music bed that **restarts on every cut** is audibly wrong.
- A duck envelope needs the **whole** voice track to decide where to dip. Per-scene, the
  key signal for the scene boundary does not exist yet.

So the mix is one wav for the entire video, mounted as the spec's **root** `audioUrl`, and
the per-scene urls are **cleared** by the same node that produced the mix:

```python
for sc in scenes:
    sc.pop("audio_url", None)
    sc.pop("audioUrl", None)
state["soundtrack_path"] = "soundtrack.wav"
```

This is what satisfies the mutual-exclusion validator from
`audio-track-silence-diagnosis.md` §5 — otherwise the composition mounts `<Audio>` twice
for the same speech (root + scene) and plays it against a copy of itself. That artifact
measures as perfectly healthy audio and is invisible in every still frame.

Also thread the root track through **every** builder, including the QA-repair path. A
repair pass that rebuilds the spec without `audio_url=state.get("soundtrack_path")` ships
a retry with no audio at all — and the retry is exactly the run nobody re-listens to.

## 3. Sample-rate mismatch plays the voice at half speed

The TTS wrote **24 kHz mono**; the mixer runs at **48 kHz**. Dropping the raw samples into
the timeline halves the playback rate — the voice is intelligible-ish, sounds "slow and
deep", and every level check passes.

Resample on read, and assert the invariant that catches it:

```python
if sr != target_sr:
    n_out = int(round(len(sig) * target_sr / sr))
    sig = np.interp(np.linspace(0, len(sig)-1, n_out), np.arange(len(sig)), sig)
```

```
source     24000 Hz  53520 frames = 2.230s
resampled  48000 Hz 107040 frames = 2.230s   <- durations must match, not frame counts
```

Linear interpolation is enough for speech at a near-integer ratio and keeps the module
dependency-free. Assert **duration equality**, never frame-count equality: the frame count
is supposed to change.

## 4. Cue timing must subtract transition overlap

Transitions **overlap** their neighbours, so summing `durationInFrames` walks every cue
progressively late — 2.5 s of drift by the eighth scene on a real spec.

```python
starts, t = [], 0.0
for sc in scenes:
    tr = sc.get("transition") or sc.get("transition_in")
    if isinstance(tr, dict):
        t -= float(tr.get("durationInFrames", tr.get("duration_in_frames", 30))) / fps
    starts.append(max(0.0, t))
    t += float(sc.get("durationInFrames", sc.get("duration_in_frames", 0))) / fps
```

Two details worth copying:

- Accept **both spellings** (`durationInFrames` / `duration_in_frames`). Python-side specs
  and wire specs disagree, and a `.get` on the wrong one silently yields 0 — a zero-length
  scene that swallows its own cue.
- The returned total is the **last start plus its own length**, not the naive sum. I
  asserted 7.8 s from the running total and the function measured 8.2 s; the *code* was
  right and the *test* was wrong. Derive the expected value from the definition, not from
  the arithmetic you did in your head.

This mirrors the renderer's own overlap plan (`getTransitionPlan()` in
`lib/transitions.ts`). If that changes, this must too — say so in the docstring.

## 5. Degrade for authoring mistakes, raise for output defects

The policy line matters because TTS already cost minutes before this node runs:

| condition | behaviour | why |
|---|---|---|
| unknown music bed name | print available names, fall back | a typo must not discard minutes of synthesis |
| unknown SFX names | drop them, print the list | same |
| no scenes / no voice clips | skip the mix, keep per-scene voice | opt-out and degenerate inputs share a path |
| zero-length spec | `ValueError` | nothing sensible to render |
| **clipping** (true peak ≥ 0 dBFS) | `RuntimeError` | shipping distorted audio is worse than failing |

## 6. Verify the mix in three windows, not one

A whole-file mean proves nothing: one voiced scene out of five passes it. Measure a voice
window, a **gap between clips**, and the whole track — the gap is what proves the bed is
actually there:

```
whole track      -19.9 dB mean, -3.1 dB peak, no clipping
under speech     -18.6 dB / -17.8 dB   (two separate voice windows)
between clips    -44.0 dB              <- bed present; digital silence would be ~-91
duck depth        7.39 dB              measured from the stems
```

Use `atrim` inside the filter chain, not `-ss/-to` (see
`wiring-voiceover-and-proving-a-crossfade.md` §6 for why seeks can measure the wrong span).

Have the mixer return **stems**, not just the mix. Duck depth is unprovable from a summed
file: you need the bed measured inside voice-active regions versus outside them.

```python
env = result["duck_envelope"]; active = env < 0.99
duck_db = measure_lufs(music_post[~active]) - measure_lufs(music_post[active])
```

## 7. Measured duck depth is lower than configured — assert direction, not the constant

Configured depth was `DUCK_DEPTH_DB = 6.0`. Measurements:

- real 4-scene / 10.8 s mix → **7.39 dB**
- unit test, 1.2 s voice inside a 4 s window → **2.65 dB**

Neither is a bug. The envelope's 120 ms attack and 400 ms release ramps count as "active",
and on a short clip those ramps dominate the active region, averaging the dip upward.
Master-bus normalisation also shifts the absolute numbers.

So a test asserting `> 3.0` fails on legitimate output. Assert that the duck is **real and
directional** (`> 2.0`, bed quieter under voice than outside it) and record the two measured
values in the test docstring so the next reader does not "fix" the code to hit 6.0.

Class-level rule: for any DSP parameter, the configured constant is a target for the
envelope generator, not a prediction about the measured output. Assert sign and rough
magnitude; pin exact numbers only against a stored golden file.

## 8. When the whole test suite hangs, bisect by file

`pytest tests/ -q` printed 29 dots and then hung past a 500 s timeout, so no summary line
ever arrived and the pass/fail count was unknowable. Running each file separately took 75 s
total and localised it immediately:

```
test_config_parity       8 passed
test_libraries          12 passed
test_phase3              1 failed, 9 passed   <- test_pipeline_run_success
test_phase5              3 passed
test_pipeline            2 passed
test_soundtrack          9 passed
test_transition_parity   8 passed + 26 subtests
```

The offender ran the **real** pipeline (TTS + render) inside a unit test. Confirmed
pre-existing by the stash check from `wiring-voiceover-and-proving-a-crossfade.md` §8: it
hangs identically with the working tree stashed. Report the per-file tally plus which
failures are pre-existing — never "the suite passes" when you never saw a summary line.
