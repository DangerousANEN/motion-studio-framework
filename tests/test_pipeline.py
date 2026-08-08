"""Integration tests for MSF Pipeline Orchestrator and CLI."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from msf.cli import cli
from msf.config import MSFConfig
from msf.contracts.models import (
    ProjectBrief,
    ProjectState,
    ProjectStatus,
    ResearchResult,
    SceneComposition,
    SceneSpec,
    Script,
    Storyboard,
    VoiceResult,
    WordTimestamp,
)
from msf.pipeline.orchestrator import PipelineOrchestrator
from msf.utils.file_manager import ProjectFileManager


class TestPipelineOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.config = MSFConfig()
        self.config.output.base_dir = self.temp_dir
        self.orchestrator = PipelineOrchestrator(self.config)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("msf.agents.llm_client.LLMClient.chat_json")
    @patch("msf.agents.voice_agent.VoiceAgent.execute")
    @patch("msf.engines.audio.mastering.AudioMaster.master_audio")
    @patch("msf.engines.render.assembler.VideoAssembler.assemble")
    @patch("msf.engines.render.assembler.VideoAssembler.concatenate")
    @patch("msf.engines.render.renderer.PlaywrightRenderer.render_scene")
    def test_full_pipeline_execution(
        self,
        mock_render,
        mock_concat,
        mock_assemble,
        mock_master_audio,
        mock_voice,
        mock_chat_json,
    ) -> None:
        """Verify that full pipeline runs end-to-end and produces a valid ProjectState."""

        # Mock LLM responses based on call prompt/context
        def mock_llm_side_effect(messages, **kwargs):
            sys_msg = ""
            usr_msg = ""
            for m in messages:
                if m.get("role") == "system":
                    sys_msg = m.get("content", "")
                elif m.get("role") == "user":
                    usr_msg = m.get("content", "")

            sys_lower = sys_msg.lower()
            usr_lower = usr_msg.lower()

            if "исследователь" in sys_lower or "исследование" in usr_lower:
                return {
                    "facts": ["Fact 1: AI is evolving.", "Fact 2: Python is popular."],
                    "key_points": ["Key point 1", "Key point 2"],
                    "statistics": ["80% adoption rate"],
                    "sources": ["Tech Report 2026"],
                }
            elif "режиссёр" in sys_lower or "storyboard" in sys_lower or "разбей следующий сценарий" in usr_lower:
                return {
                    "scenes": [
                        {
                            "scene_id": "scene_001",
                            "title": "Scene 1 Intro",
                            "narration_text": "AI video generation is advancing rapidly.",
                            "visual_description": "Futuristic digital grid with glowing nodes.",
                            "visual_goal": "Show futuristic digital grid with glowing nodes.",
                            "duration": 15.0,
                            "on_screen_text": "AI Video Evolution",
                            "emotion": "excited",
                            "information_load": "high",
                        },
                        {
                            "scene_id": "scene_002",
                            "title": "Scene 2 Outro",
                            "narration_text": "It empowers creators around the globe.",
                            "visual_description": "Global map highlighting active creative nodes.",
                            "visual_goal": "Show global map highlighting active creative nodes.",
                            "duration": 15.0,
                            "on_screen_text": "Empowering Creators",
                            "emotion": "inspirational",
                            "information_load": "medium",
                        },
                    ]
                }
            elif "сценарист" in sys_lower or "сценарий" in usr_lower:
                return {
                    "title": "AI Video Automation",
                    "hook": "Did you know AI creates videos now?",
                    "scenes_text": [
                        "AI video generation is advancing rapidly.",
                        "It empowers creators around the globe.",
                    ],
                    "cta": "Subscribe for more AI tools!",
                    "total_duration": 30.0,
                    "language": "ru",
                }
            elif "scene composer" in sys_lower or "арт-директор" in sys_lower or "layout" in usr_lower or "композици" in usr_lower:
                return {
                    "scene_id": "scene_001",
                    "layout": {"layout_id": "split_vertical"},
                    "camera": {"preset_id": "zoom_in"},
                    "motions": [{"preset_id": "fade_in"}],
                    "asset_requests": [],
                    "background_color": "#0a0a0a",
                    "duration": 15.0,
                }
            return {}

        mock_chat_json.side_effect = mock_llm_side_effect

        # Mock VoiceAgent execution
        def mock_voice_side_effect(input_data):
            scene_id = input_data.scene_id if isinstance(input_data, SceneSpec) else "scene_001"
            audio_path = os.path.join(self.temp_dir, f"mock_{scene_id}.wav")
            with open(audio_path, "wb") as f:
                f.write(b"MOCK_AUDIO_DATA")
            return VoiceResult(
                audio_path=audio_path,
                duration_seconds=15.0,
                sample_rate=24000,
                word_timestamps=[
                    WordTimestamp(word="AI", start=0.0, end=0.5),
                    WordTimestamp(word="video", start=0.5, end=1.0),
                ],
            )

        mock_voice.side_effect = mock_voice_side_effect

        # Mock AudioMaster
        def mock_master_audio_side_effect(in_path, out_path):
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(b"MOCK_MASTERED_AUDIO_DATA")
            return out_path

        mock_master_audio.side_effect = mock_master_audio_side_effect

        # Mock PlaywrightRenderer
        async def mock_render_side_effect(scene_html, voice_res, scene_frames_dir):
            from PIL import Image
            d = Path(scene_frames_dir)
            d.mkdir(parents=True, exist_ok=True)
            img = Image.new("RGB", (1080, 1920), color=(10, 10, 10))
            img.save(d / "frame_00000.jpg")
            return d

        mock_render.side_effect = mock_render_side_effect

        # Mock assembler methods to create output files
        def mock_assemble_side_effect(frames_dir, audio_path, output_path, fps=30, cleanup=True):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"MOCK_MP4_VIDEO")
            return str(output_path)

        def mock_concat_side_effect(video_paths, output_path):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"MOCK_FINAL_CONCAT_MP4_VIDEO")
            return str(output_path)

        mock_assemble.side_effect = mock_assemble_side_effect
        mock_concat.side_effect = mock_concat_side_effect

        # Execute pipeline
        topic = "Artificial Intelligence Video Automation"
        state = self.orchestrator.run(topic=topic, duration=30.0)

        # Assertions
        self.assertIsNotNone(state)
        self.assertTrue(state.project_id.startswith("proj_"))
        self.assertEqual(state.status, ProjectStatus.COMPLETED)
        self.assertEqual(state.brief.topic, topic)
        self.assertIsNotNone(state.research)
        self.assertTrue(len(state.research.facts) > 0)
        self.assertIsNotNone(state.script)
        self.assertEqual(state.script.hook, "Did you know AI creates videos now?")
        self.assertIsNotNone(state.storyboard)
        self.assertEqual(len(state.storyboard.scenes), 2)
        self.assertEqual(len(state.scenes), 2)

        # Verify output path
        self.assertIsNotNone(state.output_path)
        self.assertTrue(os.path.exists(state.output_path))

        # Verify persisted state file
        file_mgr = ProjectFileManager(self.temp_dir)
        loaded_state = file_mgr.load_project_state(state.project_id)
        self.assertEqual(loaded_state.project_id, state.project_id)
        self.assertEqual(loaded_state.status, ProjectStatus.COMPLETED)

    @patch("msf.pipeline.orchestrator.PipelineOrchestrator.run")
    def test_cli_execution(self, mock_orchestrator_run) -> None:
        """Verify Click CLI invocation."""
        mock_state = ProjectState(
            project_id="proj_test_cli",
            status=ProjectStatus.COMPLETED,
            output_path="/tmp/output.mp4",
        )
        mock_orchestrator_run.return_value = mock_state

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--topic", "Test CLI Topic", "--duration", "30", "--style", "viral_shorts"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Motion Studio Framework CLI", result.output)
        self.assertIn("Video Generation Complete!", result.output)
        self.assertIn("proj_test_cli", result.output)


if __name__ == "__main__":
    unittest.main()
