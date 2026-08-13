# Voice identity is part of the contract, and a fallback breaks it silently

Read before touching anything under `msf/agents/voice_agent.py`,
`msf/skills_bridge/qwen3_tts.py`, `assets/voices/voices.json`, or `tts.*` in config.

## The report and the actual cause

User: "женский голос используют почему-то хотя у нас есть пресеты лучше."

Nobody selected a female voice. `_synthesize_qwen3_tts` pointed at a hardcoded absolute
path into the Hermes audio cache:

```
C:/Users/ANEN/AppData/Local/hermes/cache/audio/audio_3463d054d38f.mp3
```

That file does not exist — cache entries are transient, so it broke the moment the cache
was cleared. The `FileNotFoundError` was swallowed by a bare `except`, logged as a
warning nobody reads, and the chain fell through:

```
Qwen3-TTS (clone, male)  →  Silero "kseniya" (FEMALE, cannot clone)
                         →  edge-tts "ru-RU-SvetlanaNeural" (FEMALE, cannot clone)
```

Both male references in `voices.json` sat unused. **The voice was not a choice; it was
the second fallback of a silent failure.**

## Rules

**1. A fallback that changes the speaker is not a degradation, it is a different product.**
Gate both engines behind an explicit `allow_voice_substitution` flag. Without it, Silero
returns False with an `.error()` log and edge-tts raises. A run that fails loudly gets
noticed; a wrong-gender narration ships.

**2. Never hardcode a reference path.** Resolve through `resolve_voice()`, which returns
the reference **and its transcript** from the registry. That also keeps ICL on — the old
code passed `x_vector_only_mode=True`, i.e. timbre copied, prosody flat, which is the
"robotic voice" complaint from earlier sessions.

**3. Registry paths must be repo-relative.** `voices.json` stores
`assets/voices/refs/<name>.wav`; an absolute path into a cache dir is exactly what broke.
When adding a voice, COPY the wav into `assets/voices/refs/`.

**4. A transcript is mandatory, not optional.** No `ref_text` → `resolve_voice` returns
`None` → `x_vector_only_mode`. Inaudible until the render is done. Refuse to create a
registry entry without one.

**5. Read the real config field name.** `getattr(self.config.voice, "reference")` returns
`None` forever because the field is `config.tts.speaker` (`TTSConfig`). A `getattr` chain
with a default silently means "use the default" instead of "this key is wrong".

## Config parity is load-bearing

`tts.speaker` was `"syenduk"` in BOTH `config/default.yml` and `TTSConfig`, while
`voices.json` only holds `voice_2` and `voice_3`. `resolve_voice("syenduk")` raises
`ValueError`, so any code honouring the config value failed synthesis outright and landed
in the female fallback. A stale string in a config file changed the narrator's gender.

`tests/test_config_parity.py` now asserts, for both the YAML and the dataclass default:

```python
cfg.tts.speaker in known_voices          # resolvable at all
resolve_voice(None) -> (existing file, non-empty ref_text)   # ICL, not x-vector
# and every registry entry resolves to a real file WITH a transcript
```

Plus two tests that the fallbacks refuse to run without opt-in. Instantiate the agent with
`VoiceAgent.__new__(VoiceAgent)` so no model loads.

## Assert the MODE, never the path

`describe_reference(voice)` reports which cloning mode a voice will ACTUALLY get. The
useful assertion is:

```python
describe_reference(None)["has_ref_text"] is True   # → "ICL (prosody transferred)"
```

A path check passes while prosody is silently disabled.

## Measured cost

`voice_3`, one short Russian phrase, through `synthesize_voice_clone`: 45.2 s wall, 2.23 s
of audio, peak 0.61, RMS −17.6 dB, 24 kHz. Most of that is cold start — the model is a
module-level singleton, so budget one load per run, not per scene.
