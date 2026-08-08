"""MSF Video Assembler.

Assembles image frames and audio into an H.264 MP4 video file via FFmpeg.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoAssembler:
    """Combines sequential JPEG frames and optional audio into H.264 MP4 videos using FFmpeg."""

    def assemble(
        self,
        frames_dir: Path | str,
        audio_path: str,
        output_path: str,
        fps: int = 30,
        cleanup: bool = True,
    ) -> str:
        """Assemble frames and audio into an MP4 file.

        Args:
            frames_dir: Directory containing frame_%05d.jpg images.
            audio_path: Path to input audio file (or empty string if no audio).
            output_path: Path for output MP4 file.
            fps: Video frames per second.
            cleanup: Whether to delete frames_dir after assembly.

        Returns:
            Path string of generated video.

        Raises:
            FileNotFoundError: If frames_dir or frames do not exist.
            RuntimeError: If FFmpeg execution fails.
        """
        frames_dir = Path(frames_dir)
        if not frames_dir.exists():
            raise FileNotFoundError(f"Frames directory not found: {frames_dir}")

        frames = list(frames_dir.glob("frame_*.jpg"))
        if not frames:
            raise FileNotFoundError(f"No frame_*.jpg images found in: {frames_dir}")

        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        frames_pattern = str(frames_dir / "frame_%05d.jpg")

        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-start_number",
            "0",
            "-i",
            frames_pattern,
        ]

        has_audio = bool(audio_path and os.path.exists(audio_path))
        if has_audio:
            cmd.extend([
                "-i",
                audio_path,
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
            ])
        else:
            logger.warning("No audio provided or audio file missing (%s); encoding video stream only", audio_path)

        cmd.extend([
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(output_path_obj),
        ])

        logger.info("Executing FFmpeg assembly command: %s", " ".join(cmd))

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("FFmpeg assembly completed successfully: %s", output_path)
        except subprocess.CalledProcessError as err:
            logger.error("FFmpeg assembly failed: %s\nStderr: %s", err, err.stderr)
            raise RuntimeError(f"FFmpeg assembly failed with exit code {err.returncode}: {err.stderr}") from err

        if cleanup:
            try:
                shutil.rmtree(frames_dir)
                logger.info("Cleaned up frames directory: %s", frames_dir)
            except Exception as clean_err:
                logger.warning("Failed to clean up frames directory %s: %s", frames_dir, clean_err)

        return str(output_path_obj)

    def concatenate(self, video_paths: list[str | Path], output_path: str | Path) -> str:
        """Concatenate multiple MP4 video files into a single video file via FFmpeg.

        Args:
            video_paths: List of file paths to input MP4 video files.
            output_path: Destination path for the merged MP4 video file.

        Returns:
            Path string of the output merged video file.
        """
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if not video_paths:
            raise ValueError("video_paths list cannot be empty")

        if len(video_paths) == 1:
            shutil.copy(video_paths[0], output_path_obj)
            return str(output_path_obj)

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as list_file:
            list_file_path = list_file.name
            for vp in video_paths:
                p_str = str(Path(vp).resolve()).replace("\\", "/")
                list_file.write(f"file '{p_str}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file_path,
            "-c", "copy",
            str(output_path_obj),
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as err:
            logger.error("FFmpeg concatenate failed: %s\nStderr: %s", err, err.stderr)
            raise RuntimeError(f"FFmpeg concatenate failed with exit code {err.returncode}: {err.stderr}") from err
        finally:
            if os.path.exists(list_file_path):
                os.remove(list_file_path)

        return str(output_path_obj)
