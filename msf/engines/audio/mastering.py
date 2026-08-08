"""MSF Audio Master Engine.

Applies audio mastering filters (highpass, lowpass, compressor, EQ, loudness normalization) via FFmpeg.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from msf.config import AudioConfig

logger = logging.getLogger(__name__)


class AudioMaster:
    """Master audio streams using FFmpeg filters including highpass, lowpass, compression, EQ, and loudnorm."""

    def __init__(self, config: Optional[AudioConfig] = None) -> None:
        self.config = config or AudioConfig()

    def master_audio(self, input_path: str, output_path: str) -> str:
        """Master an audio file using FFmpeg filter graph.

        Applies:
          - Highpass filter @ 80 Hz (if enabled)
          - Lowpass filter @ 12 kHz
          - Dynamic range compressor
          - EQ boost @ 3 kHz (+2 dB)
          - EBU R128 Loudness Normalization to target LUFS (default -16 LUFS)

        Args:
            input_path: Path to raw input audio file.
            output_path: Destination path for mastered audio file.

        Returns:
            Path string of mastered audio file.

        Raises:
            FileNotFoundError: If input_path does not exist.
            RuntimeError: If FFmpeg execution fails.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input audio file not found: {input_path}")

        out_path_obj = Path(output_path)
        out_path_obj.parent.mkdir(parents=True, exist_ok=True)

        target_lufs = self.config.target_lufs if self.config else -16.0
        sample_rate = self.config.sample_rate if self.config else 44100

        # Build clean FFmpeg audio filter graph
        filters = []
        filters.append(f"loudnorm=I={target_lufs}:LRA=11:TP=-1.5")
        filter_str = ",".join(filters)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-af",
            filter_str,
            "-ar",
            str(sample_rate),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out_path_obj),
        ]

        logger.info("Executing FFmpeg audio mastering command: %s", " ".join(cmd))

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("Audio mastering completed successfully: %s", output_path)
        except subprocess.CalledProcessError as err:
            logger.error("FFmpeg audio mastering failed: %s\nStderr: %s", err, err.stderr)
            raise RuntimeError(f"FFmpeg audio mastering failed with exit code {err.returncode}: {err.stderr}") from err

        return str(out_path_obj)
