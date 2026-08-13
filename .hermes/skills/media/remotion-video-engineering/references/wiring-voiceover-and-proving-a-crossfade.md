# Wiring voice-over through a render pipeline, and proving a cross-fade actually blends

Companion to `references/audio-track-silence-diagnosis.md` (which covers *detecting*
silence) and `references/audit-4-preset-capabilities-and-transitions.md` (which names the
`fade` root cause). This file covers the **repair** phase of both: the field-drift class
that breaks per-scene audio, the tool that makes a hand-authored spec speak, and the probe
design that decides whether a transition blends — including the probe that lies at exactly
the frame you care about.

---

## 1. Field drift: two names for one concept, joined only by a coincidence

The synthesis node wrote the filename under one key and the spec builder read a different
key:

```python
# synthesis node
sc["audio_file"] = scene_wav_name          # written, read by NOTHING

# spec builder, same module
audio_url=f"scene_{index:02d}.wav",        # rebuilt from the loop index
```

Audio worked anyway, because both sides independently derived the same string from the same
index. `grep audio_file` returned exactly one hit — the write. That is the signature of dead
field drift: **a key written once and read nowhere, masked by a parallel derivation.**

Two separate defects, fix both:

- **Write the field the consumer reads.** Here: `sc["audio_url"]`, matching the dataclass
  field that the wire-key normaliser maps to `audioUrl`.
- **Stop the unconditional overwrite.** `audio_url=f"scene_{i:02d}.wav"` made a caller-supplied
  path *unreachable* — a spec naming its own asset silently rendered against a different track,
  or a nonexistent one (which Remotion turns into silence, not an error). Correct shape:

```python
audio_url=normalised.get("audio_url") or f"scene_{index:02d}.wav",
```

Assert all three paths, because the fallback hides the other two:

| input | expect |
|---|---|
| `{"audio_url": "custom.wav"}` | `custom.wav` |
| `{"audioUrl": "wire.wav"}` (camel wire spelling) | `wire.wav` |
| `{}` at index 7 | `scene_07.wav` |

## 2. A default that is not a registry key falls through to a degraded mode

```python
DEFAULT_VOICE = "syenduk"        # NOT a key in voices.json
```

`resolve_voice(None)` checked the registry, missed, and fell through to a bare
`DEFAULT_REF_AUDIO` path with `ref_text=None`. A missing transcript downgrades zero-shot
cloning from ICL (prosody transferred) to **x-vector (timbre only, flat)** — silently, with
a healthy-looking wav on disk at normal loudness. Nothing in the audio *level* reveals it.

Class-level rule: when a default names an entry in a registry, assert the entry **exists and
carries the fields the good path needs**, not merely that the file resolves. The cheap probe
prints the mode the library itself reports:

```
None     -> voice_3_24k.wav  ref_text=381 chars  mode=ICL (prosody transferred)
voice_2  -> voice_2_17s.wav  ref_text=275 chars  mode=ICL (prosody transferred)
```

A `describe_reference()`-style accessor that names the active mode is worth adding to any
cloning bridge for exactly this reason.

## 3. TTS wall-clock is cold-start, not per-phrase

An early single-call measurement read **62 s for one sentence** and made a 15-scene video
look like a 15-minute job. Measuring two consecutive scenes through the same process:

```
[00]  96.4s synth | 3.03s speech
[01]  22.2s synth | 2.39s speech
```

The first call pays model load; the rest are ~4x cheaper. A cross-check on a different local
engine showed the same shape even harder (31 s, then 0.13–3.3 s per phrase on GPU).

Consequences:
- **Never benchmark a TTS engine with one call.** Synthesize 3+ distinct phrases in one
  process and report first-call and steady-state separately.
- **Use distinct texts.** Repeating the same string can return in ~0.05 s from an internal
  cache and fabricate a spectacular throughput number.
- Keep the model a module-level singleton so an N-scene job pays load once. Budget
  `load + (N-1) * steady`, not `N * first_call`.

## 4. Voicing an already-authored spec (the fast CLI path)

The pipeline's fast path — `remotion render --props=spec.json` — skips the synthesis node
entirely, so a hand-authored spec has no `audioUrl` and ships silent. A small tool closes
that gap; the design choices that matter:

- **Validate before loading the model.** Check every scene has narration text *first*. A
  minute of model load followed by "scene 7 has no text" wastes the run, and skipping the
  scene instead produces a video that goes silent partway through — worse than an error.
- **Retime scenes to narration length by default.** A 90-frame (1.5 s) scene holding 3 s of
  speech cuts the voice mid-word. Compute `round(dur * fps) + pad` and let authored frames
  be overridden; offer `--keep-timing` for the rare case the author means it. Observed:
  90 → 194 and 90 → 155 frames.
- **Name wavs after the spec**, not `scene_00.wav`, so several voiced specs coexist in the
  static directory without overwriting each other's tracks.
- **Drop any root-level track when writing per-scene tracks** (see §5).

## 5. Root track + per-scene tracks = the narration plays twice

Compositions commonly mount both:

```tsx
{audioUrl && <Audio src={resolveSrc(audioUrl)} />}                  // root
{scene.audioUrl && <Audio src={resolveSrc(scene.audioUrl)} />}      // per scene
```

Supplying both is never intentional: the voice-over plays twice, offset by each scene start,
which sounds like room echo rather than an obvious bug — and is **completely invisible in a
still frame**. Reject it in spec validation. Partial coverage (some scenes voiced, some not)
should *warn* rather than fail: a deliberately silent B-roll scene is legitimate, a
half-voiced video usually is not.

## 6. Per-scene audibility: `-ss/-to` can measure the wrong thing

Verifying that *every* scene is audible, not just the first, by seeking:

```bash
ffmpeg -ss 0.0  -to 3.2 -i out.mp4 -map a:0 -af volumedetect -f null -   # -21.3 dB
ffmpeg -ss 3.23 -to 5.8 -i out.mp4 -map a:0 -af volumedetect -f null -   # -21.3 dB
```

Two different windows returning **identical means to 0.1 dB** is the tell that the seek did
not shape what the filter saw. Trim inside the filter chain instead, so the measurement is
unambiguously scoped:

```bash
ffmpeg -i out.mp4 -map a:0 -af "atrim=start=3.3:end=5.8,volumedetect" -f null -
```

An out-of-range window then returns **no `mean_volume` line at all**, which is itself a
useful control: if a window past the end of the file still prints a number, the scoping is
wrong.

## 7. Proving a cross-fade blends — and the colour probe that fails mid-blend

The upstream default leaves the exiting scene at `opacity: 1` for the whole overlap, so a
"cross-fade" is a fade-**in** over an opaque scene that cuts on the last frame of the window.
Fix is one argument (`shouldFadeOutExitingScene: true`), but the fix must be *proven*, and
the obvious probe has a trap.

**Probe design.** Give the two scenes distinct accent colours, render the mp4, extract every
frame in and around the overlap window, and count pixels matching each accent mask. Then
count frames where **both** masks are populated:

```
before fix: frames scanned 68..124 (57)   frames showing BOTH scenes: 0
```

Zero out of fifty-seven is unambiguous evidence of a cut, and it needs no reference image.

**The trap.** After the fix, the same probe still reported `BOTH: 0` — and both counters
collapsed toward zero around the midpoint (`n=80: redA=26, cyanB=5`). Blending two saturated
hues at ~50 % produces a desaturated mixture that matches **neither** strict colour mask.
The metric is blind exactly where the answer lives. Mean RGB told the real story — a smooth
crimson-to-cyan ramp across `n=76..87` with no discontinuity — and vision on the frame strip
confirmed both captions superimposed at equal opacity on `n=80`.

Generalisable rules:
- A mask-based "is X present" metric measures **unblended** pixels. During a blend it
  under-reports both sides. Pair it with a continuous statistic (mean channel values across
  the window) that cannot go blind at the crossover.
- A monotone ramp with no jump *is* the blend signature; a cut shows as a one-frame step.
- `remotion still` renders each frame independently and can disagree with the encoded file.
  Pull transition frames from the **rendered mp4** (`ffmpeg -vf select=between(n,a,b)`),
  which is what ships.
- Frame-count oracle: `sum(durations) - sum(overlaps)`. Two 120-frame scenes with a 48-frame
  transition must yield 192. If the file has 240, the transition never engaged.

## 8. Is that failing test yours?

Before reporting a regression — or letting one block a commit — stash the working tree and
run the same test on the parent commit:

```bash
git stash && pytest tests/the_failing_one.py -q; git stash pop
```

A theme-parity test failed identically at HEAD~ (ten style kits present in the TS palette
and absent from the Python table — an unrelated prior debt). Reporting it as "my change
broke the suite" would have been wrong; silently ignoring it would also have been wrong.
State which failures are pre-existing and cite the stashed run.
