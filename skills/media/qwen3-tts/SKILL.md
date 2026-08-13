---
name: qwen3-tts
description: "Use when generating speech or voice cloning with Qwen3-TTS."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [tts, qwen3-tts, voiceover, voice-clone, voice-design, audio-synthesis, russian, zero-shot]
---

# Qwen3-TTS (Zero-Shot Speech, Voice Clone & Voice Design)

Qwen3-TTS (0.6B & 1.7B) is Alibaba's state-of-the-art multi-lingual speech generation model supporting 10 languages (including Russian), voice cloning, emotion steering, and 9 built-in premium timbres (`Vivian`, `Serena`, `Uncle_Fu`, `Dylan`, `Eric`, `Ryan`, `Aiden`, `Ono_Anna`, `Sohee`).

## Quickstart Code

```python
import torch
import soundfile as sf
import warnings
import os

warnings.filterwarnings('ignore')
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'

from qwen_tts import Qwen3TTSModel

# Load 1.7B CustomVoice on GPU
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    device_map="cuda:0",
    dtype=torch.bfloat16,
    attn_implementation="eager"
)

# Generate Russian speech with speaker Serena & volume normalization
text = "Добро пожаловать в автономную систему Motion Studio Framework!"
wavs, sr = model.generate_custom_voice(
    text=text,
    language="Russian",
    speaker="Serena"
)

# Peak Volume Normalization
audio = wavs[0]
max_val = abs(audio).max()
if max_val > 0:
    audio = audio / max_val * 0.95

sf.write("output_qwen3_serena.wav", audio, sr)
```

## Zero-Shot Voice Cloning (1.7B-Base)

To clone any reference voice (e.g., user audio file `.mp3`/`.wav`) zero-shot using `Qwen/Qwen3-TTS-12Hz-1.7B-Base`:

```python
from qwen_tts import Qwen3TTSModel
import torch, soundfile as sf

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="cuda:0",
    dtype=torch.bfloat16,
    attn_implementation="eager"
)

# Use ICL mode (x_vector_only_mode=False + ref_text) for full prosody transfer.
# Omit ref_text or set x_vector_only_mode=True ONLY if no transcript is available (clones timbre only, sounds flatter).
wavs, sr = model.generate_voice_clone(
    text="Привет! Это синтез моим клонированным голосом.",
    language="Russian",
    ref_audio="assets/voices/refs/syenduk_8s_24k.wav",
    ref_text="Кому бы не хотелось поговорить с животными, Рик? Большинство людей.",
    x_vector_only_mode=False,
    max_new_tokens=512,  # Cap generation to prevent infinite loops on runaway inputs
)

audio = wavs[0]
max_val = abs(audio).max()
if max_val > 0:
    audio = audio / max_val * 0.95

sf.write("cloned_output.wav", audio, sr)
```

## Critical Voice Synthesis & Audio Quality Lessons

0. **CustomVoice vs Zero-Shot Voice Clone (Crucial Distinction):**
   - **Do NOT use `CustomVoice` (1.7B-CustomVoice) for cloning reference audio!** `CustomVoice` only supports preset built-in timbres (`Vivian`, `Serena`, etc.). If a user asks to synthesize "this voice", "like in the reference audio", or provides a reference clip/voice message, you MUST use `Qwen/Qwen3-TTS-12Hz-1.7B-Base` with `generate_voice_clone(ref_audio=..., ref_text=..., x_vector_only_mode=False)`.
   - **Locating Telegram voice messages in Hermes:** Audio/voice messages sent by the user in Telegram are cached at `AppData/Local/hermes/cache/audio/audio_*.ogg`. Convert them to 24kHz mono WAV before passing as `ref_audio`.

1. **Phonetic Transliteration for English Acronyms:**
   English terms like `LLM`, `GitHub`, `DevTools`, `Open Source` inside Russian TTS prompts cause unnatural accents or mispronunciations. Always transliterate English terms into Russian phonetic equivalents:
   - `LLM` -> `ЛЛМ`
   - `GitHub` -> `Гитхаб`
   - `DevTools` -> `ДевТулз`
   - `Open Source` -> `Оупен сорс`

2. **Preventing High-Pitched Squeaks & Volume Decay ("Писк" & Attenuation):**
   - Do NOT apply aggressive FFmpeg `equalizer=f=3000` or `acompressor` post-processing filters on Qwen3-TTS output, as they create high-pitched whistle artifacts ("писк") or volume decay toward the end of audio files.
   - Use clean peak volume normalization (`audio / max_val * 0.95`) or standard `loudnorm=I=-16:LRA=11:TP=-1.5`.

3. **Always fade the tail of every scene clip.**
   Qwen3-TTS clips frequently end on a non-zero sample, heard as a clipped/abrupt cut-off at the end of a scene — most obvious once per-scene WAVs are concatenated. Apply a short fade to every clip *before* concatenation and *before* the loudnorm master pass, not only on the final mix:
   `afade=t=in:st=0:d=0.03,afade=t=out:st=<dur-0.12>:d=0.12`

4. **Vet the reference audio before blaming the model.**
   A "robotic" clone is far more often a bad reference or missing transcript than a model limitation. See "Reference Audio Vetting" below, and run `scripts/check_reference_audio.py` on any candidate before registering it as a voice.

5. **Supply `ref_text` for ICL Prosody Transfer:**
   `x_vector_only_mode=True` (or missing `ref_text`) clones speaker timbre only — delivery becomes monotone and robotic. Passing the exact transcript (`ref_text`) with `x_vector_only_mode=False` engages In-Context Learning (ICL), which transfers vocal inflections, rhythm, and prosody from the reference.

6. **Reference Length Limit in ICL Mode (8–15s for stability, up to 30s with full transcript):**
   - 30s clips work provided an **EXACT full-length transcript** is supplied in `ref_text` for ICL mode (e.g. `kireevoice` 30.6s with Whisper transcription).
   - If `ref_text` is missing or shorter than the audio, Qwen3's context window over-truncates output.
   - For short one-line synthesis, 8–15s remains the most stable sweet-spot.

7. **Always Cap Generation (`max_new_tokens`):**
   Without `max_new_tokens`, Qwen3-TTS can enter infinite token generation loops on certain prompt/ref pairs, causing hangs (>180s). Budget tokens based on text length: `max_new_tokens = int(min(4096, max(256, est_seconds * 12.5 * 3)))`.

8. **FFmpeg Filter Path Escaping (Windows):**
   When passing Windows paths inside FFmpeg filter strings (e.g. `-af loudnorm=...`), backslashes in `output\file.mp4` break the FFmpeg filter parser with `Undefined constant or missing '('`. Always convert backslashes to forward slashes (`/`) in path strings inside FFmpeg filters.

9. **Measure before claiming.**
   Never report a diagnosis, duration, line number, or quality verdict that a tool has not actually returned in this session. Audio work is full of plausible-sounding numbers, and asserting one before the probe finishes forces retractions that destroy user trust. If a background job (model load, A/B synthesis) has not finished, say so and show the real numbers when it does — a model load alone is ~70s and a full A/B can run many minutes, so start it in the background and do other work rather than guessing its outcome.

## Reference Audio Vetting (avoiding vocoder-artifact recycling)

The highest-leverage quality check in a voice-clone pipeline. **Cloning from a previous TTS output recycles and compounds vocoder artifacts** — the usual root cause of a clone that sounds "slightly robotic" no matter how the prompt is tuned.

**Noise floor is the discriminator.** Measure the 5th-percentile frame amplitude (the quiet parts between words):

| Signal | Noise floor | Verdict |
|---|---|---|
| Live microphone recording | roughly -35 to -45 dB | Real voice: room air, breath, mic self-noise |
| Qwen3-TTS / vocoder output | roughly -75 dB or lower | Synthetic: pauses are *digital silence* |

Corroborating tells that a "reference" is actually a model output:
- **24 kHz mono** is Qwen3-TTS's native output format, so a 24 kHz mono "voice sample" is suspect by default; real recordings are usually 44.1/48 kHz and often stereo.
- A peak sitting at exactly -0.4 dB (or similar round value) is the fingerprint of a prior `audio / max_val * 0.95` normalization pass.

Guidance:
- Keep a voice registry (e.g. `assets/voices/voices.json`) mapping voice id to `ref_audio`, and record provenance (live recording vs synthetic) per entry. Audit it — registries silently accumulate synthetic entries that were never meant to be clone sources.
- Target a short window of clean continuous speech (roughly 8-15 s). Longer is not automatically better; if you change reference length, *measure* output duration and truncation rather than assuming.
- Reference must be clean speech only: no music bed, no reverb/echo, no overlapping speakers.
- **Supply a verbatim `ref_text` transcript whenever possible.** `x_vector_only_mode=True` skips in-context learning and clones timbre only, which tends to sound flatter; the exact transcript engages ICL and carries prosody. Confirm the difference by A/B measurement, not assumption.

## FFmpeg / ffprobe path handling on Windows

Where `terminal` runs through git-bash/MSYS, `ffmpeg`/`ffprobe` are **native Windows builds** and do not resolve MSYS-style paths:

1. Pass native paths (`C:\Users\...` or `C:/Users/...`), never `/c/Users/...` — the latter fails with `Error opening input: No such file or directory`.
2. **Never split `path:label` pairs with `${pair%%:*}` in bash loops** — the drive-letter colon in `C:/...` truncates the path to `C`. Use a delimiter that cannot appear in a path (`|`), or drive batch ffmpeg work from Python with `subprocess.run([...])` and raw strings, which sidesteps shell quoting entirely.

## Mandatory Windows & PyTorch Configuration

1. **Required Dependency Versions:**
   - `transformers==4.57.3`
   - `accelerate==1.12.0`
   - `qwen-tts==0.1.1`
   - `huggingface-hub<1.0` (e.g. `0.36.2`)

2. **Attention Backend Requirement:**
   - Pass `attn_implementation="eager"` in `from_pretrained(...)`.
   - **Do NOT use `sdpa`** on Windows without `flash-attn` — PyTorch's native SDPA panics with a dimension mismatch error (`RuntimeError: The expanded size of the tensor (17) must match the existing size (32)`) because SDPA cannot handle Qwen3's 3D mRoPE position embeddings.

3. **Required Code Fixes in `qwen_tts` Package:**
   If `create_causal_mask()` raises `TypeError` during inference, fix the following in `qwen_tts/core/models/modeling_qwen3_tts.py`:
   - Change `inputs_embeds=inputs_embeds` to `input_embeds=inputs_embeds` in `mask_kwargs` / `causal_mask` calls.
   - Pass `cache_position=cache_position` into `create_causal_mask(...)` calls.

## Remotion Orchestrator Integration (Module-Level Singleton Pattern)

When integrating `Qwen3TTSModel` into long-running video orchestration pipelines (such as `msf.orchestrators.remotion_runner`):

1. **Process-Level Singleton Caching:**
   Always cache the loaded model instance in a module-level variable (`_MODEL`) to avoid re-loading the 1.7B parameters (~3.5 GB VRAM) on every scene/clip.
   - **Performance impact:** First clip load ~70-75s; subsequent clips in the same process ~35s.

2. **Per-Scene Timing & Padding:**
   - Split narration scripts into sentence chunks of <= 28 words.
   - Pad each scene's audio duration by +0.3s before converting to Remotion frames (`durationInFrames = ceil((dur_sec + 0.3) * fps)`).
   - Write per-scene WAV files directly into `remotion/public/audio/scene_X.wav` so Remotion can import them via `staticFile("audio/scene_X.wav")`.

3. **Audio Mastering & Muxing:**
   - Concatenate scene WAV clips and master full narration with EBU R128 loudnorm (-16 LUFS target) via `AudioMaster`.
   - Mux raw Remotion video output with mastered audio via FFmpeg: `ffmpeg -y -i raw.mp4 -i mastered.wav -c:v copy -c:a aac -shortest final.mp4`.

## Output is 24 kHz mono — resample before it reaches a 48 kHz mixer

The clone path writes **24 kHz mono** (`pcm_s16le`, verified with `ffprobe`), while video
containers and most mix buses run at 48 kHz stereo. Two distinct failure modes:

- **Muxing** (`ffmpeg -i raw.mp4 -i voice.wav`) resamples for you. Fine.
- **Numpy mixing** (dropping the samples into a 48 kHz timeline as an array) does **not**.
  The voice then plays at **half speed** — intelligible but slow and deep, and every level
  check still passes because the signal is perfectly healthy, just wrong-rate.

Resample on read and assert **duration equality**, never frame-count equality (the frame
count is *supposed* to change):

```python
if sr != target_sr:
    n_out = int(round(len(sig) * target_sr / sr))
    sig = np.interp(np.linspace(0, len(sig) - 1, n_out), np.arange(len(sig)), sig)
# 24000 Hz  53520 frames = 2.230s  ->  48000 Hz 107040 frames = 2.230s
```

Do not "fix" this by making the synth emit 48 kHz — the model's native rate is 24 kHz and
upsampling at the source just moves the same interpolation earlier.

## Do not swap this engine out on speed grounds

Voice cloning is the reason this model was chosen: one registered reference per persona
gives a whole cast of voices. A faster non-cloning engine (Silero and friends) is **not** a
substitute, and proposing one because synthesis takes minutes has been explicitly rejected.
If speed is the concern, the fix is the singleton + cold-start budgeting above, not a
different model. Benchmark a faster engine only to establish what the cold start actually
costs — never as a candidate default.

## Registry defaults: a `DEFAULT_VOICE` that is not a registry key silently kills ICL

Lesson #5 says supply `ref_text` for ICL. The practical way that rule gets violated is not
forgetting the argument — it is a **default that points at nothing**.

Observed: `DEFAULT_VOICE = "syenduk"` while `voices.json` contained only `voice_2` and
`voice_3`. The resolver's fallback chain read:

```python
if not voice:
    voices = load_voices()
    if DEFAULT_VOICE in voices:
        voice = DEFAULT_VOICE
    else:
        return DEFAULT_REF_AUDIO, None      # <-- transcript-free path, ICL off
```

So every unattended call (`resolve_voice(None)`) fell through to a bare wav path with
`ref_text=None` and produced timbre-only x-vector output — at normal loudness, with no
error, no warning in the render log worth noticing. Nothing about the audio says "the
default is broken"; it just reads flatter than the reference.

**Assertion to run after any change to the registry or the default:**

```python
for v in (None, *registry_keys):
    ref, txt = resolve_voice(v)
    info = describe_reference(v)
    assert info["has_ref_text"], f"{v}: no transcript -> x-vector only"
    print(v, Path(ref).name, len(txt or ""), info["mode"])
# every line must report "ICL (prosody transferred)"
```

Include `None` in that loop — it is the case every automated caller actually takes, and the
one a keyed test never covers. Keep a `describe_reference()`-style helper that reports the
*mode it will actually get* rather than the arguments it was handed; without it, the
downgrade is invisible.

Corollary: `DEFAULT_REF_AUDIO` as an "absolute fallback" file path is a trap when it has no
registered transcript. Either register it in `voices.json` with a transcript, or make the
resolver raise instead of quietly degrading.

## Load cost is a cold-start cost, not a per-sentence cost

Budget the singleton correctly or you will over-plan. Measured on the 1.7B Base clone path,
same process, distinct sentences:

| Call | Wall clock |
|---|---|
| first sentence (includes model load) | **96 s** |
| every sentence after | **~22 s** |

A one-off timing test of a single sentence reports ~62 s and reads as the per-sentence price,
which makes a 15-scene video look like a 15-minute job. With the module-level singleton the
real figure is `load + n × 22 s` (≈6 min for 15 scenes). Time a **second** sentence before
quoting a per-item cost or choosing a different engine on speed grounds.

## Reference Files

- `references/windows_setup_and_pitfalls.md`: PyTorch SDPA mRoPE dimension errors and `create_causal_mask` patch details.
- `references/motion_studio_framework_integration.md`: Integration guide for MSF `VoiceAgent` with peak volume normalization and phonetic handle tuning.
- `references/russian_pronunciation_and_stress.md`: Transliteration table for English tech terms, combining-acute stress marks for homographs, punctuation pacing, and the display-text-vs-spoken-text split.
- `scripts/check_reference_audio.py`: Probe candidate clone references (or a whole `voices.json`) and flag synthetic/vocoder-recycled audio via noise-floor analysis. Run before registering any new voice.
