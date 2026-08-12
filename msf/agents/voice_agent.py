"""MSF Voice Agent.

Generates Russian narration for a SceneSpec.

SPEAKER IDENTITY IS PART OF THE CONTRACT
----------------------------------------
The project's voice is a cloned MALE reference from assets/voices/voices.json,
synthesised by Qwen3-TTS with ICL prosody transfer. Silero ("kseniya") and
edge-tts ("ru-RU-SvetlanaNeural") are both FEMALE and cannot clone, so a fallback
does not degrade quality — it changes who is speaking. Both fallbacks are
therefore gated behind `allow_voice_substitution`; without it, failure is an
error rather than a different narrator.

Word-level timestamps come from faster-whisper, with proportional estimation as a
fallback.
"""

from __future__ import annotations

import asyncio
import os
import wave
from pathlib import Path
from typing import Any, Optional

from msf.agents.base import BaseAgent
from msf.config import MSFConfig
from msf.contracts.models import (
    ReviewResult,
    ReviewVerdict,
    SceneSpec,
    VoiceResult,
    VoiceSpec,
    WordTimestamp,
)
from msf.utils.file_manager import ProjectFileManager
from msf.utils.logger import StageLogger, setup_logger


class VoiceAgent(BaseAgent[SceneSpec, VoiceResult]):
    """Agent responsible for TTS synthesis and word-level alignment."""

    def __init__(
        self,
        config: Optional[MSFConfig] = None,
        logger: Optional[StageLogger | logging.Logger] = None,
        file_manager: Optional[ProjectFileManager] = None,
    ) -> None:
        cfg = config or MSFConfig()
        log = logger or setup_logger(self.__class__.__name__)
        super().__init__(config=cfg, logger=log)
        output_dir = getattr(self.config.output, 'base_dir', './output') if hasattr(self.config, 'output') else './output'
        self.file_manager = file_manager or ProjectFileManager(output_dir)

    def execute(self, input_data: SceneSpec | dict[str, Any]) -> VoiceResult:
        """Execute speech synthesis and timestamp alignment for scene text."""
        if isinstance(input_data, SceneSpec):
            scene_spec = input_data
        elif isinstance(input_data, dict):
            scene_spec = SceneSpec.from_dict(input_data)
        else:
            scene_spec = SceneSpec(scene_id="scene_001")

        text = scene_spec.narration_text.strip()
        if not text:
            text = "Без текста"

        output_filename = f"voice_{scene_spec.scene_id}.wav"
        output_path = str(self.file_manager.get_project_dir("default") / "audio" / output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        sample_rate = 24000
        duration_seconds = 0.0

        # Step 1: Synthesize audio (Qwen3-TTS 1.7B -> Silero TTS v4 -> edge-tts)
        tts_success = self._synthesize_qwen3_tts(text, output_path, sample_rate)
        if not tts_success:
            self.logger.warning("Qwen3-TTS failed. Falling back to Silero TTS.")
            tts_success = self._synthesize_silero(text, output_path, sample_rate)
        if not tts_success:
            self.logger.warning("Silero TTS failed or unavailable. Falling back to edge-tts.")
            self._synthesize_edge_tts(text, output_path)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            duration_seconds = self._get_wav_duration(output_path)
        else:
            raise RuntimeError(f"Audio file was not created or is empty at: {output_path}")

        # Step 2: Extract word timestamps via faster-whisper (or fallback to word length proportioning)
        word_timestamps = self._extract_timestamps(output_path, text, duration_seconds)

        return VoiceResult(
            audio_path=output_path,
            duration_seconds=round(duration_seconds, 2),
            sample_rate=sample_rate,
            word_timestamps=word_timestamps,
        )

    def validate(self, output: VoiceResult) -> ReviewResult:
        """Validate generated audio output and timestamps."""
        issues: list[str] = []

        if not output.audio_path or not os.path.exists(output.audio_path):
            issues.append(f"Audio file missing or not found at: {output.audio_path}")
        elif os.path.getsize(output.audio_path) == 0:
            issues.append(f"Audio file is 0 bytes: {output.audio_path}")

        if output.duration_seconds <= 0:
            issues.append(f"Invalid duration ({output.duration_seconds}s). Must be > 0.")

        if not output.word_timestamps or len(output.word_timestamps) == 0:
            issues.append("word_timestamps list is empty.")

        if issues:
            return ReviewResult(
                stage="voice",
                verdict=ReviewVerdict.FAIL,
                score=0.0,
                issues=issues,
                suggestions=["Ensure audio file exists, duration > 0, and timestamps non-empty."],
            )

        return ReviewResult(
            stage="voice",
            verdict=ReviewVerdict.PASS,
            score=1.0,
            issues=[],
            suggestions=[],
        )
    def _synthesize_qwen3_tts(self, text: str, output_path: str, sample_rate: int) -> bool:
        """Synthesize Russian text with Qwen3-TTS zero-shot cloning.

        WHY THIS WAS PRODUCING A FEMALE VOICE
        -------------------------------------
        It never ran at all. The reference was a hardcoded absolute path into the
        Hermes audio cache:

            'C:/Users/ANEN/AppData/Local/hermes/cache/audio/audio_3463d054d38f.mp3'

        That file does not exist (verified: No such file or directory). Cache files
        are transient, so this broke the moment the cache was cleared. The
        FileNotFoundError was swallowed by the `except` below, logged as a warning
        nobody reads, and the chain fell through to _synthesize_silero — speaker
        "kseniya", a FEMALE voice — and then to edge-tts "ru-RU-SvetlanaNeural",
        also female. Both male references in assets/voices/voices.json sat unused.

        So the voice was not chosen; it was the second fallback of a silent
        failure. Routing through the registry fixes the cause: resolve_voice()
        returns the reference AND its transcript, which also keeps ICL prosody
        transfer on instead of the flat x_vector_only_mode=True used here.
        """
        try:
            from msf.skills_bridge.qwen3_tts import describe_reference, synthesize_voice_clone

            voice = self._requested_voice()
            info = describe_reference(voice)
            if not info.get("exists"):
                # Loud, not swallowed: a missing reference means the fallback is
                # about to change the speaker's gender, which is never what the
                # caller wanted.
                self.logger.error(
                    "Voice reference missing: %s. Fix assets/voices/voices.json — "
                    "falling back would silently change the speaker.",
                    info.get("ref_audio"),
                )
                return False

            self.logger.info(
                "Qwen3-TTS voice=%s mode=%s ref=%s",
                voice or "(registry default)",
                info.get("mode"),
                Path(str(info.get("ref_audio"))).name,
            )

            wav_path, _duration = synthesize_voice_clone(
                text=text,
                voice=voice,
                output_path=output_path,
            )
            return bool(wav_path) and os.path.exists(output_path)
        except Exception as e:
            self.logger.warning(f"Qwen3-TTS error: {e}")
            return False

    def _requested_voice(self) -> Optional[str]:
        """Voice key for this run: explicit attribute, then config, then registry default.

        Returning None is meaningful — resolve_voice(None) picks the registry
        DEFAULT_VOICE and carries its transcript, so ICL stays on.

        Reads `config.tts.speaker`, which is the actual field name (TTSConfig);
        there is no `config.voice.reference`.
        """
        explicit = getattr(self, "voice", None)
        if explicit:
            return str(explicit)
        speaker = getattr(getattr(self.config, "tts", None), "speaker", None)
        if speaker:
            return str(speaker)
        return None

    def _synthesize_silero(self, text: str, output_path: str, sample_rate: int) -> bool:
        """Silero TTS v4 — a LAST-RESORT fallback, and it changes the speaker.

        Silero cannot clone: `speaker="kseniya"` is a fixed FEMALE synthetic voice,
        so reaching this path silently replaces the male cloned voice the project
        is built around. That is the bug the user reported, and the fix is upstream
        (see _synthesize_qwen3_tts) — this method stays only so a machine without
        CUDA can still produce sound.

        It is therefore opt-in. `allow_voice_substitution` must be set, otherwise
        producing audio in the wrong voice is worse than producing none: a silent
        run gets noticed, a wrong-gender narration ships.
        """
        if not getattr(self, "allow_voice_substitution", False):
            self.logger.error(
                "Refusing Silero fallback: speaker 'kseniya' is a different (female) "
                "voice than the configured clone reference. Set "
                "allow_voice_substitution=True to accept a substituted speaker."
            )
            return False
        try:
            import torch

            device = torch.device("cpu")
            torch.set_num_threads(4)

            local_model_path = os.path.join(
                os.path.expanduser("~"), ".cache", "torch", "hub", "snakers4_silero-models_master", "models"
            )
            # Try loading silero model via torch.hub
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language="ru",
                speaker="v4_ru",
                trust_repo=True,
            )
            model.to(device)

            audio_tensor = model.apply_tts(
                text=text,
                speaker="kseniya",
                sample_rate=sample_rate,
            )

            # Save wav tensor
            audio_numpy = (audio_tensor * 32767).numpy().astype("int16")
            with wave.open(output_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_numpy.tobytes())

            return True
        except Exception as e:
            self.logger.warning(f"Silero TTS error: {e}")
            return False

    def _synthesize_edge_tts(self, text: str, output_path: str) -> None:
        """edge-tts fallback — also a different speaker, and it needs network.

        "ru-RU-SvetlanaNeural" is female, so this is the second way a broken clone
        reference turned into a female narration. Same rule as Silero: opt in
        explicitly or get an error.
        """
        if not getattr(self, "allow_voice_substitution", False):
            raise RuntimeError(
                "All voice synthesis failed and edge-tts would substitute a different "
                "speaker (ru-RU-SvetlanaNeural, female). Fix the Qwen3-TTS reference in "
                "assets/voices/voices.json, or set allow_voice_substitution=True to "
                "accept a substituted speaker."
            )

        import edge_tts

        voice = "ru-RU-SvetlanaNeural"
        self.logger.warning("Substituting speaker: edge-tts %s (not the clone voice)", voice)

        async def _run() -> None:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

        try:
            asyncio.run(_run())
        except Exception as e:
            self.logger.error(f"edge-tts error: {e}")
            raise RuntimeError(f"Failed to generate TTS audio with edge-tts: {e}") from e

    def _get_wav_duration(self, wav_path: str) -> float:
        """Measure WAV duration in seconds using wave module or fallback audio check."""
        try:
            with wave.open(wav_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return frames / float(rate)
        except Exception as e:
            self.logger.warning(f"Could not read WAV header directly: {e}")

        # Fallback file size estimation if header read fails
        file_size = os.path.getsize(wav_path)
        # Assuming 24000Hz 16-bit mono = 48000 bytes/sec
        return max(1.0, file_size / 48000.0)

    def _extract_timestamps(
        self, audio_path: str, text: str, total_duration: float
    ) -> list[WordTimestamp]:
        """Extract word-level timestamps using faster-whisper, with proportional fallback."""
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_path, word_timestamps=True, language="ru")

            timestamps: list[WordTimestamp] = []
            for segment in segments:
                if segment.words:
                    for w in segment.words:
                        clean_word = w.word.strip()
                        if clean_word:
                            timestamps.append(
                                WordTimestamp(
                                    word=clean_word,
                                    start=round(w.start, 2),
                                    end=round(w.end, 2),
                                )
                            )

            if timestamps:
                return timestamps
        except Exception as e:
            self.logger.warning(f"faster-whisper alignment failed: {e}. Using proportional fallback.")

        # Proportional fallback timestamp calculation
        words = text.split()
        if not words:
            return [WordTimestamp(word="...", start=0.0, end=total_duration)]

        total_chars = sum(len(w) for w in words)
        current_time = 0.0
        timestamps: list[WordTimestamp] = []

        for w in words:
            word_dur = (len(w) / max(1, total_chars)) * total_duration
            word_dur = max(0.2, word_dur)
            start = round(current_time, 2)
            end = round(current_time + word_dur, 2)
            timestamps.append(WordTimestamp(word=w, start=start, end=end))
            current_time += word_dur

        return timestamps
