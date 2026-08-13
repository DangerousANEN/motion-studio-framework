# Workflow: Auto-Registering User Audio Attachments as Qwen3-TTS Clone Voices

When a user attaches an audio file (`.mp3` / `.wav`) to add as a clone voice:

1. **Convert & Standardize Audio:**
   Convert the input audio to 24kHz mono PCM WAV via FFmpeg (`-ar 24000 -ac 1 -c:a pcm_s16le`).
   Save under `assets/voices/refs/<voice_name>_24k.wav`.

2. **Extract Exact Transcribing via Whisper:**
   Use `faster_whisper` (Base model on CUDA, `float16`) to transcribe the full reference audio in Russian/target language.
   A verbatim `ref_text` is mandatory for In-Context Learning (ICL) prosody transfer. Without it, Qwen3 falls back to `x_vector_only_mode=True` (timbre only, flat speech).

3. **Register in `assets/voices/voices.json`:**
   Add entry mapping voice ID to the standardized path and transcript:
   ```json
   "voice_id": {
     "ref_audio": "assets/voices/refs/voice_id_24k.wav",
     "ref_text": "Exact transcribed text from Whisper...",
     "lang": "ru",
     "notes": "Registered from user attachment."
   }
   ```

4. **Trigger Re-render / Test:**
   Synthesize scenes using `_synthesize_cloned_audio(text, ref_audio, ref_text)` and assemble video via Remotion.
