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


class TestVoiceRegistryParity(unittest.TestCase):
    """The configured speaker must be resolvable, or synthesis silently changes voice.

    `tts.speaker` was "syenduk" in both the YAML and TTSConfig, while
    assets/voices/voices.json only holds voice_2 and voice_3. resolve_voice()
    raises ValueError on an unknown key, the caller swallowed it, and the fallback
    chain reached Silero ("kseniya") and edge-tts ("ru-RU-SvetlanaNeural") — both
    FEMALE. So a stale config value silently changed the narrator's gender.
    """

    def _known_voices(self):
        from msf.skills_bridge.qwen3_tts import load_voices
        return {k for k in load_voices() if not k.startswith("_")}

    def test_yaml_speaker_exists_in_the_voice_registry(self):
        cfg = load_default_yml()
        known = self._known_voices()
        self.assertIn(
            cfg.tts.speaker, known,
            f"config/default.yml tts.speaker={cfg.tts.speaker!r} is not in "
            f"assets/voices/voices.json ({sorted(known)}). Voice synthesis would "
            "fail and fall back to a different (female) speaker."
        )

    def test_dataclass_default_speaker_exists(self):
        known = self._known_voices()
        self.assertIn(
            TTSConfig().speaker, known,
            f"TTSConfig().speaker={TTSConfig().speaker!r} is not a registry key."
        )

    def test_dataclass_speaker_matches_yaml(self):
        cfg = load_default_yml()
        self.assertEqual(TTSConfig().speaker, cfg.tts.speaker)

    def test_module_default_voice_exists_and_supports_icl(self):
        """DEFAULT_VOICE must resolve WITH a transcript.

        Without ref_text the model drops to x_vector_only_mode — timbre copied,
        prosody flat. That is the "robotic voice" failure, and it is silent.
        """
        from msf.skills_bridge.qwen3_tts import DEFAULT_VOICE, resolve_voice
        self.assertIn(DEFAULT_VOICE, self._known_voices())
        ref_audio, ref_text = resolve_voice(None)
        self.assertTrue(Path(ref_audio).is_file(), f"missing reference wav: {ref_audio}")
        self.assertTrue(ref_text, "registry default has no transcript — ICL disabled")

    def test_every_registry_voice_resolves_to_a_real_file(self):
        from msf.skills_bridge.qwen3_tts import resolve_voice
        for key in sorted(self._known_voices()):
            ref_audio, ref_text = resolve_voice(key)
            self.assertTrue(Path(ref_audio).is_file(), f"{key}: missing {ref_audio}")
            self.assertTrue(ref_text, f"{key}: no transcript, ICL would be disabled")


class TestVoiceSubstitutionIsGated(unittest.TestCase):
    """Fallback TTS engines use a different speaker and must not fire silently."""

    def _agent(self):
        from msf.agents.voice_agent import VoiceAgent
        return VoiceAgent.__new__(VoiceAgent)  # no __init__: no model loading

    def test_silero_refuses_without_explicit_opt_in(self):
        import logging
        agent = self._agent()
        agent.logger = logging.getLogger("test-silero")
        self.assertFalse(
            agent._synthesize_silero("текст", "/tmp/none.wav", 24000),
            "Silero ('kseniya', female) must not run unless substitution is allowed."
        )

    def test_edge_tts_raises_without_explicit_opt_in(self):
        import logging
        agent = self._agent()
        agent.logger = logging.getLogger("test-edge")
        with self.assertRaises(RuntimeError) as ctx:
            agent._synthesize_edge_tts("текст", "/tmp/none.wav")
        self.assertIn("different", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
