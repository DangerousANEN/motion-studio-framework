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


def master_video_audio(in_mp4: str, out_mp4: str, target_lufs: float = -16.0) -> str:
    """Master video audio using ffmpeg loudnorm filter without re-encoding video.

    FFmpeg filter: loudnorm=I=-16:LRA=11:TP=-1.5, re-encode audio to AAC 192k, -c:v copy.
    Raises RuntimeError on ffmpeg failure.
    """
    if not os.path.exists(in_mp4):
        raise FileNotFoundError(f"Input video file not found: {in_mp4}")

    out_path = Path(out_mp4)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # loudnorm resamples internally to 192kHz; without an explicit -ar the muxed
    # AAC stream inherits that rate. Pin 48kHz — the delivery standard for
    # YouTube Shorts / Reels / TikTok.
    filter_str = f"loudnorm=I={target_lufs}:LRA=11:TP=-1.5,aresample=48000"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        in_mp4,
        "-af",
        filter_str,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        str(out_path),
    ]

    logger.info("Mastering video audio with loudnorm: %s", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")

    if res.returncode != 0:
        raise RuntimeError(
            f"ffmpeg audio mastering failed with exit code {res.returncode}.\n"
            f"Stderr: {res.stderr}"
        )

    return str(out_path)


class AudioMasterEngine:
    """Master audio streams using FFmpeg filters including highpass, lowpass, compression, EQ, and loudnorm."""

    def __init__(self, config: Optional[AudioConfig] = None) -> None:
        self.config = config or AudioConfig()

    def master_audio(self, input_path: str, output_path: str) -> str:
        """Master an audio file using FFmpeg filter graph.

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

        filters = [f"loudnorm=I={target_lufs}:LRA=11:TP=-1.5"]
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

        res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if res.returncode != 0:
            logger.error("FFmpeg audio mastering failed: exit code %d\nStderr: %s", res.returncode, res.stderr)
            raise RuntimeError(f"FFmpeg audio mastering failed with exit code {res.returncode}: {res.stderr}")

        logger.info("Audio mastering completed successfully: %s", output_path)
        return str(out_path_obj)


# Backwards compatibility alias
AudioMaster = AudioMasterEngine
