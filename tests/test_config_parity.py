"""Config parity: the YAML, the dataclass defaults, and msf.spec must agree.

WHY THIS EXISTS
---------------
The project has three places that claim to know the render settings:
  - config/default.yml          (what an operator reads)
  - msf/config.py dataclasses  (what code imports)
  - msf/spec.py constants      (what the render path actually uses)

They drifted twice:
  - render.fps: 30 in YAML vs FPS=60 in spec.py. Frame-denominated constants
    (DEFAULT_TRANSITION_FRAMES=18 -> 300ms at 60fps but 600ms at 30fps; motion
    preset durations) silently doubled every animation at 30fps.
  - audio.sample_rate: 44100 in AudioConfig vs aresample=48000 baked into
    master_video_audio(). The two mastering paths produced different sample
    rates for the same timeline.

These tests fail on the next drift instead of letting it ship as a video that
just "feels wrong".

stdlib unittest -- the project has no pytest and no virtualenv.
Run: python tests/test_config_parity.py
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from msf.config import AudioConfig, MSFConfig, RenderConfig, TTSConfig  # noqa: E402
from msf.spec import FPS  # noqa: E402


def load_default_yml() -> MSFConfig:
    """Parse config/default.yml with the real loader."""
    cfg = MSFConfig.from_yaml(ROOT / "config" / "default.yml")
    return cfg


class TestRenderParity(unittest.TestCase):
    def test_yaml_fps_equals_spec_fps(self):
        cfg = load_default_yml()
        self.assertEqual(
            cfg.render.fps,
            FPS,
            f"config/default.yml says {cfg.render.fps} fps but msf.spec.FPS is "
            f"{FPS}. Frame constants (DEFAULT_TRANSITION_FRAMES=18, motion preset "
            "durations) assume 60fps, so a mismatch doubles every animation.",
        )

    def test_dataclass_default_fps_equals_spec_fps(self):
        self.assertEqual(
            RenderConfig().fps,
            FPS,
            "RenderConfig default fps has drifted from msf.spec.FPS.",
        )

    def test_render_geometry_matches_spec(self):
        """YAML should describe the same canvas as the spec's vertical format."""
        from msf.spec import FORMATS, DEFAULT_FORMAT
        fmt = FORMATS[DEFAULT_FORMAT]
        cfg = load_default_yml()
        self.assertEqual((cfg.render.width, cfg.render.height),
                         (fmt.width, fmt.height))


class TestAudioParity(unittest.TestCase):
    def test_sample_rate_matches_mastering(self):
        # master_video_audio() in msf/engines/audio/mastering.py hardcodes
        # aresample=48000. AudioConfig must agree.
        self.assertEqual(
            AudioConfig().sample_rate,
            48000,
            "AudioConfig.sample_rate has drifted from the aresample=48000 in "
            "mastering.py.",
        )

    def test_yaml_lufs_matches_default(self):
        cfg = load_default_yml()
        self.assertEqual(cfg.audio.target_lufs, AudioConfig().target_lufs)


class TestTTSParity(unittest.TestCase):
    def test_yaml_provider_matches_dataclass(self):
        cfg = load_default_yml()
        self.assertEqual(
            cfg.tts.provider,
            TTSConfig().provider,
            "YAML tts.provider differs from the TTSConfig default.",
        )

    def test_qwen3_is_the_pipeline_provider(self):
        """The render path calls Qwen3-TTS, not silero. Guard against reverting."""
        cfg = load_default_yml()
        self.assertEqual(
            cfg.tts.provider,
            "qwen3",
            "config/default.yml tts.provider must be qwen3 -- the silero entry "
            "described a provider the pipeline no longer uses.",
        )


class TestLLMParity(unittest.TestCase):
    def test_dataclass_defaults_match_yaml(self):
        """Bare MSFConfig() must point at the local gateway, not the internet."""
        from msf.config import LLMConfig
        cfg = load_default_yml()
        dflt = LLMConfig()
        self.assertEqual(dflt.base_url, cfg.llm.base_url,
                         "LLMConfig default base_url differs from YAML -- a bare "
                         "MSFConfig() would hit the public OpenAI endpoint.")
        self.assertEqual(dflt.model, cfg.llm.model,
                         "LLMConfig default model differs from YAML.")
        self.assertEqual(dflt.api_key, cfg.llm.api_key,
                         "LLMConfig default api_key differs from YAML.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
