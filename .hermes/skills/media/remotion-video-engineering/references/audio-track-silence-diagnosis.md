# Silent Audio in a Rendered Video — Diagnosis and the Two-Path Divergence

A rendered mp4 that *has* an audio stream but plays nothing. This is a distinct defect
class from "no audio stream": every superficial check passes, the container looks
correct, and the file is only revealed as broken when someone plays it.

Measured on a Remotion + Python-graph pipeline (MSF), but the diagnostic chain and the
architectural trap generalise to any renderer where a spec file drives audio mounting.

---

## 1. `ffprobe` cannot detect silence — it reports the container, not the signal

The failing artifacts looked healthy on every structural check:

```
$ ffprobe -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels
codec_name=aac
sample_rate=48000
channels=2
duration=9.557333
```

An audio stream, correct codec, correct rate, correct channel count, full duration.
Nothing here is wrong. The track was **digital silence**:

```
$ ffmpeg -hide_banner -i out.mp4 -map a:0 -af volumedetect -f null /dev/null 2>&1 \
    | grep -E "mean_volume|max_volume"
mean_volume: -91.0 dB
max_volume:  -91.0 dB
```

`mean_volume == max_volume == -91.0 dB` is the signature of an all-zero PCM track
(−91 dBFS is the noise floor of 16-bit silence). Real speech on the same pipeline
measures **mean ≈ −17 dB, max ≈ −3 dB**.

**Rules:**
- Never certify audio from `ffprobe` stream metadata. It answers "is there a track",
  not "is there sound".
- `-map a:0` matters. Without it `volumedetect` may attach to the wrong stream and print
  nothing at all — an empty grep result reads as "no problem found" and is the same
  false negative one layer up.
- Two thresholds worth encoding: `mean_volume > -50 dB` catches total silence;
  `mean == max` within a hair catches it even when a DC offset lifts the floor.

## 2. Mastering preserves silence — it cannot manufacture signal

The pipeline ran `loudnorm=I=-16:LRA=11:TP=-1.5,aresample=48000` over the raw render.
A normaliser on an all-zero track outputs an all-zero track; it has no signal to lift.
So the mastering stage is exonerated *and* useless as a safety net: it will happily
re-encode silence into a professionally-formatted silent AAC track.

Corollary: put the volume assertion **after** mastering, and make it fail-closed. A QA
node that checks `mean_volume > -50 dB` does catch this — the bug survived because
nothing ran that check on the direct-render path (§3).

## 3. The real cause: two render paths, only one of which mounts audio

The pipeline had two ways to produce a video, and they diverged silently.

| Path | Command | Audio? |
|---|---|---|
| A — full graph | `build_msf_graph().invoke({...})` | yes: a voice-synthesis node writes wavs and injects the field |
| B — direct CLI | `npx remotion render src/index.ts Main out.mp4 --props=spec.json` | **no** |

Path B is the attractive one: it's fast, it takes a hand-written spec, and it's what you
reach for while iterating on visuals. It skips every Python node, including synthesis.

The renderer mounts audio conditionally:

```tsx
{audioUrl && <Audio src={resolveSrc(audioUrl)} />}            // root track
{scene.audioUrl && <Audio src={resolveSrc(scene.audioUrl)} />} // per-scene
```

A hand-written spec has no `audioUrl`, so both guards are falsy, no `<Audio>` element
ever mounts — and the encoder still emits a full-length silent AAC track because the
container profile demands one. **Nothing errors. Nothing warns.**

The wav files were not even missing: `remotion/public/scene_00.wav … scene_10.wav` were
all present and non-empty on disk, left over from earlier graph runs. Absence of assets
was never the problem, which is why "check the files exist" would have cleared the bug.

### Proving it instead of assuming it

One probe settles the whole diagnosis. Take a minimal two-scene spec, point
`audioUrl` at wavs that already exist in the static directory, render, measure:

```python
spec = {"width":1080,"height":1920,"fps":60,"scenes":[
  {"id":"a","preset":"HeroKinetic","durationInFrames":134,"title":"A","audioUrl":"scene_00.wav"},
  {"id":"b","preset":"QuoteCard","durationInFrames":134,"text":"B","audioUrl":"scene_01.wav"},
]}
# render, then volumedetect
```
Result: **mean −16.7 dB / max −3.1 dB**. The field is the whole story; do this before
writing a single line of fix.

## 4. Field-name drift that would have bitten next

Two adjacent bugs in the same chain, both invisible while the names happened to agree:

- The synthesis node wrote `sc["audio_file"] = "scene_00.wav"`, but the dataclass field
  and its camelCase wire mapping are `audio_url` → `audioUrl`. **Nothing reads
  `audio_file`.** `grep -n audio_file` across the package returning exactly one hit —
  the write — is the tell.
- The kwargs builder hard-coded `audio_url=f"scene_{index:02d}.wav"` unconditionally,
  regenerating the name from the index instead of reading what synthesis produced. It
  worked only because both sides derive the same string from the same index. A scene
  cannot bring its own audio, and any change to the naming scheme breaks one side
  silently.

Pattern to look for: **a value written under one key and re-derived under another.**
The system works until either derivation changes, and the failure is a missing asset,
not an exception.

## 5. Root vs per-scene tracks double-play

When a renderer supports both a root `audioUrl` (one bed for the whole video) and
per-scene `audioUrl`, a spec carrying both mounts both — narration plays twice, offset.
No validator objects because each field is individually legal. If the spec format allows
both, add a mutual-exclusion check to spec validation; there is no legitimate case for a
full narration bed plus per-scene narration.

## 6. TTS cost is a planning input, not a detail

Measure synthesis wall-clock on one sentence before designing around it. A zero-shot
voice-clone model (Qwen3-TTS 1.7B, no flash-attn) took **62 s for one short sentence**
and emitted **24 kHz mono** into a 48 kHz stereo container. Fifteen scenes ≈ 15 minutes
per video, plus a resample nobody asked for.

Also check the reference-voice registry actually resolves to an entry *with a
transcript*: the default resolved to a wav with no `ref_text`, which silently downgrades
in-context prosody transfer to x-vector timbre copy (the log said
`mode: x-vector (timbre only, flatter)` — a warning, not an error). A registry can be
correct and still have its default pointing at the degraded path.

---

## Checklist

- [ ] `ffmpeg -map a:0 -af volumedetect` on the delivered file, not `ffprobe`
- [ ] `mean_volume > -50 dB` **and** `mean != max`
- [ ] Assertion runs on *every* render path, including the fast hand-written-spec one
- [ ] `grep` the audio field name across the whole package: exactly one writer, ≥1 reader
- [ ] Spec validation rejects root + per-scene tracks together
- [ ] Per-scene volume, not just whole-file: one voiced scene out of five still passes a
      whole-file mean check
- [ ] Music/SFX modules that exist in the tree are actually imported by the pipeline —
      `grep` for the import, not for the file
