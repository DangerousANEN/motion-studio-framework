"""Unit tests for MSF Phase 3 (Agents, LLM Client, Review Engine, Pipeline Orchestrator)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from msf.agents.base import BaseAgent
from msf.agents.llm_client import LLMClient
from msf.config import LLMConfig, MSFConfig
from msf.contracts.models import (
    AssetResult,
    CameraPreset,
    Emotion,
    LayoutChoice,
    MovementType,
    ProjectBrief,
    ProjectState,
    ProjectStatus,
    ResearchResult,
    ReviewResult,
    ReviewVerdict,
    SceneComposition,
    Script,
    VoiceResult,
)
from msf.pipeline.orchestrator import PipelineOrchestrator
from msf.review.reviewer import ReviewEngine
from msf.utils.logger import setup_logger


class TestLLMClient(unittest.TestCase):
    def setUp(self):
        self.config = LLMConfig(
            provider="openai",
            base_url="http://localhost:20128/v1",
            api_key="test-key",
            model="gpt-4o",
        )
        self.client = LLMClient(self.config)

    @patch("httpx.Client.post")
    def test_chat_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello world"}}]
        }
        mock_post.return_value = mock_response

        res = self.client.chat([{"role": "user", "content": "Hi"}])
        self.assertEqual(res, "Hello world")
        mock_post.assert_called_once()

    @patch("httpx.Client.post")
    def test_chat_json_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '```json\n{"status": "ok"}\n```'}}]
        }
        mock_post.return_value = mock_response

        res = self.client.chat_json([{"role": "user", "content": "Hi"}])
        self.assertEqual(res, {"status": "ok"})


class DummyAgent(BaseAgent[str, str]):
    def execute(self, input_data: str) -> str:
        if input_data == "fail_exec":
            raise ValueError("Execution error")
        return f"processed_{input_data}"

    def validate(self, output_data: str) -> ReviewResult:
        if "invalid" in output_data:
            return ReviewResult(
                stage="dummy_review",
                verdict=ReviewVerdict.FAIL,
                issues=["Invalid output"],
            )
        return ReviewResult(stage="dummy_review", verdict=ReviewVerdict.PASS)


class TestBaseAgent(unittest.TestCase):
    def setUp(self):
        self.config = MSFConfig()
        self.logger = setup_logger("test_agent")
        self.agent = DummyAgent(self.config, self.logger)

    def test_run_success(self):
        res = self.agent.run("test_input")
        self.assertEqual(res, "processed_test_input")

    def test_run_retry_failure(self):
        with self.assertRaises(RuntimeError):
            self.agent.run("invalid_input", max_attempts=2)


class TestReviewEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ReviewEngine()

    def test_review_script_pass(self):
        script = Script(
            title="Title",
            hook="Quick hook",
            scenes_text=["Scene 1 text here", "Scene 2 text here"],
            cta="CTA text",
            total_duration=45.0,
        )
        res = self.engine.review_script(script)
        self.assertEqual(res.verdict, ReviewVerdict.PASS)

    def test_review_script_fail_hook(self):
        script = Script(
            title="Title",
            hook="This hook sentence is far too long to be spoken in under three seconds because it contains an overwhelming amount of text words",
            scenes_text=["Scene 1 text here", "Scene 2 text here"],
            cta="CTA text",
            total_duration=45.0,
        )
        res = self.engine.review_script(script)
        self.assertEqual(res.verdict, ReviewVerdict.FAIL)
        self.assertTrue(any("Hook is too long" in issue for issue in res.issues))

    def test_review_scene_pass(self):
        scene = SceneComposition(
            scene_id="scene_01",
            layout=LayoutChoice(layout_id="centered_single"),
            camera=CameraPreset(
                preset_id="static",
                compatible_layouts=["centered_single"],
            ),
            assets=[AssetResult(asset_id="ast_1", file_path="assets/img.png")],
            voice=VoiceResult(audio_path="audio/voice.wav", duration_seconds=5.0),
        )
        res = self.engine.review_scene(scene)
        self.assertEqual(res.verdict, ReviewVerdict.PASS)

    def test_review_scene_fail_missing_voice(self):
        scene = SceneComposition(
            scene_id="scene_01",
            layout=LayoutChoice(layout_id="centered_single"),
            camera=CameraPreset(
                preset_id="static",
                compatible_layouts=["centered_single"],
            ),
            assets=[AssetResult(asset_id="ast_1", file_path="assets/img.png")],
            voice=None,
        )
        res = self.engine.review_scene(scene)
        self.assertEqual(res.verdict, ReviewVerdict.FAIL)
        self.assertTrue(any("Voice synthesis result is missing" in issue for issue in res.issues))

    def test_review_project_pass(self):
        scene = SceneComposition(
            scene_id="scene_01",
            layout=LayoutChoice(layout_id="centered_single"),
            camera=CameraPreset(
                preset_id="static",
                compatible_layouts=["centered_single"],
            ),
            assets=[AssetResult(asset_id="ast_1", file_path="assets/img.png")],
            voice=VoiceResult(audio_path="audio/voice.wav", duration_seconds=45.0),
            duration=45.0,
        )
        state = ProjectState(
            project_id="proj_1",
            brief=ProjectBrief(topic="Tech", duration_range=(30, 90)),
            scenes={"scene_01": scene},
        )
        res = self.engine.review_project(state)
        self.assertEqual(res.verdict, ReviewVerdict.PASS)


class TestPipelineOrchestrator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = MSFConfig()
        self.config.output.base_dir = self.temp_dir.name
        self.orchestrator = PipelineOrchestrator(self.config)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_run_success(self):
        state = self.orchestrator.run("Artificial Intelligence")
        self.assertEqual(state.status, ProjectStatus.COMPLETED)
        self.assertIsNotNone(state.brief)
        self.assertIsNotNone(state.research)
        self.assertIsNotNone(state.script)
        self.assertIsNotNone(state.storyboard)
        self.assertGreater(len(state.scenes), 0)
        self.assertIsNotNone(state.output_path)
        self.assertTrue(Path(state.output_path).parent.exists())
