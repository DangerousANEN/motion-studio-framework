"""MSF Voice Agent.

Generates Russian speech synthesis for SceneSpec narration using Silero TTS v4 (Torch) locally,
or falls back to edge-tts. Extracts word-level timestamps via faster-whisper.
"""

from __future__ import annotations

import asyncio
import os
import wave
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
        """Synthesize Russian text using Qwen3-TTS 1.7B Base Zero-Shot Voice Clone."""
        try:
            import torch
            import soundfile as sf
            import warnings
            warnings.filterwarnings('ignore')
            os.environ['TRANSFORMERS_VERBOSITY'] = 'error'

            from qwen_tts import Qwen3TTSModel

            ref_audio = 'C:/Users/ANEN/AppData/Local/hermes/cache/audio/audio_3463d054d38f.mp3'

            model = Qwen3TTSModel.from_pretrained(
                'Qwen/Qwen3-TTS-12Hz-1.7B-Base',
                device_map='cuda:0',
                dtype=torch.bfloat16,
                attn_implementation='eager'
            )

            wavs, sr = model.generate_voice_clone(
                text=text,
                language='Russian',
                ref_audio=ref_audio,
                x_vector_only_mode=True
            )

            audio = wavs[0]
            max_val = abs(audio).max()
            if max_val > 0:
                audio = audio / max_val * 0.95

            sf.write(output_path, audio, sr)
            return True
        except Exception as e:
            self.logger.warning(f"Qwen3-TTS error: {e}")
            return False

    def _synthesize_silero(self, text: str, output_path: str, sample_rate: int) -> bool:
        """Synthesize Russian text using Silero TTS v4 locally via PyTorch."""
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
        """Fallback synthesis using edge-tts (Russian voice ru-RU-SvetlanaNeural or ru-RU-DmitryNeural)."""
        import edge_tts

        voice = "ru-RU-SvetlanaNeural"

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
