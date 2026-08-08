"""Unit and integration tests for MSF Phase 5 (Engines)."""

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msf.config import AudioConfig, RenderConfig
from msf.contracts.models import (
    CameraPreset,
    LayoutChoice,
    MotionPreset,
    SceneComposition,
    VoiceResult,
    WordTimestamp,
)
from msf.engines.audio.mastering import AudioMaster
from msf.engines.render.assembler import VideoAssembler
from msf.engines.render.renderer import PlaywrightRenderer
from msf.engines.render.template import HTMLTemplateEngine


class TestHTMLTemplateEngine(unittest.TestCase):
    def setUp(self):
        self.engine = HTMLTemplateEngine()
        self.scene = SceneComposition(
            scene_id="scene_001",
            layout=LayoutChoice(layout_id="centered_single", name="Centered Single"),
            camera=CameraPreset(preset_id="slow_push_in", duration=3.0),
            motions=[MotionPreset(preset_id="fade_in", duration=0.6)],
            background_color="#121212",
            duration=3.0,
        )
        self.words = ["Hello", "world", "this", "is", "MSF"]

    def test_generate_scene_html(self):
        html_out = self.engine.generate_scene_html(self.scene, self.words)
        self.assertIn("<!DOCTYPE html>", html_out)
        self.assertIn("1080px", html_out)
        self.assertIn("1920px", html_out)
        self.assertIn("#121212", html_out)
        self.assertIn("setData(title, words)", html_out)
        self.assertIn("updateFrame(t, duration, wordIdx)", html_out)
        self.assertIn("progress-bar", html_out)
        self.assertIn("subtitle-text", html_out)
        self.assertIn("Hello", html_out)


class TestPlaywrightRenderer(unittest.IsolatedAsyncioTestCase):
    async def test_render_scene(self):
        temp_dir = tempfile.mkdtemp()
        try:
            engine = HTMLTemplateEngine()
            scene = SceneComposition(
                scene_id="test_render_scene",
                layout=LayoutChoice(layout_id="centered_single"),
                duration=1.0,
            )
            words = ["Test", "render"]
            html_content = engine.generate_scene_html(scene, words)

            voice = VoiceResult(
                audio_path="dummy.wav",
                duration_seconds=1.0,
                word_timestamps=[
                    WordTimestamp(word="Test", start=0.0, end=0.5),
                    WordTimestamp(word="render", start=0.5, end=1.0),
                ],
            )

            config = RenderConfig(fps=10, headless=True)
            renderer = PlaywrightRenderer(config=config)

            output_dir = Path(temp_dir) / "frames"

            await renderer.render_scene(html_content, voice, output_dir)

            frames = list(output_dir.glob("frame_*.jpg"))
            self.assertGreater(len(frames), 0)
            self.assertEqual(len(frames), 10)  # 1.0s * 10 fps
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestAudioMasterAndAssembler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_audio_mastering_and_video_assembly(self):
        # 1. Generate dummy audio using FFmpeg
        raw_audio = os.path.join(self.temp_dir, "raw_audio.wav")
        cmd_gen_audio = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1.0",
            "-ar",
            "44100",
            raw_audio,
        ]

        try:
            res = subprocess.run(cmd_gen_audio, capture_output=True, text=True)
            if res.returncode != 0:
                self.skipTest(f"FFmpeg audio gen failed: {res.stderr}")
        except Exception as e:
            self.skipTest(f"FFmpeg not installed: {e}")

        # 2. Master Audio
        mastered_audio = os.path.join(self.temp_dir, "mastered.aac")
        audio_master = AudioMaster(AudioConfig(sample_rate=44100))
        out_audio = audio_master.master_audio(raw_audio, mastered_audio)
        self.assertTrue(os.path.exists(out_audio))

        # 3. Generate dummy frames using FFmpeg
        frames_dir = Path(self.temp_dir) / "test_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        cmd_gen_frames = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=1080x1920:d=1.0",
            "-r",
            "10",
            str(frames_dir / "frame_%05d.jpg"),
        ]
        subprocess.run(cmd_gen_frames, capture_output=True, check=True)

        # 4. Video Assembly
        output_mp4 = os.path.join(self.temp_dir, "output.mp4")
        assembler = VideoAssembler()
        out_video = assembler.assemble(
            frames_dir=frames_dir,
            audio_path=out_audio,
            output_path=output_mp4,
            fps=10,
            cleanup=True,
        )

        self.assertTrue(os.path.exists(out_video))
        self.assertGreater(os.path.getsize(out_video), 0)
        self.assertFalse(frames_dir.exists())  # Cleanup verified


if __name__ == "__main__":
    unittest.main()
