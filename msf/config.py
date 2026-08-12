"""MSF Configuration System.

Defines configuration data structures for LLM, TTS, Render, Audio, Pipeline, and Output settings,
with YAML file loading and default value handling.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Optional, Self

import yaml


@dataclasses.dataclass
class LLMConfig:
    """LLM provider and model parameters."""
    provider: str = "openai"
    # Defaults mirror config/default.yml: this project talks to the local
    # OmniRoute gateway, not api.openai.com. A None base_url made LLMClient
    # fall back to the public endpoint, so any code path constructing a bare
    # MSFConfig() (e.g. tests) hit the internet and failed with 403.
    api_key: str = "omniroute-local-key"
    base_url: Optional[str] = "http://localhost:20128/v1"
    model: str = "antigravity/gemini-3.6-flash-high"
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclasses.dataclass
class TTSConfig:
    """Text-to-Speech synthesis parameters."""
    # The render path calls Qwen3-TTS with ICL voice cloning
    # (msf/skills_bridge/qwen3_tts.py). The former silero/kseniya defaults
    # described a provider no longer in the pipeline.
    provider: str = "qwen3"
    # MUST be a key that exists in assets/voices/voices.json. It was "syenduk",
    # which is NOT in the registry — resolve_voice("syenduk") raises ValueError,
    # so anything that honoured this config value failed voice synthesis outright
    # and fell through to a female fallback voice. Guarded by
    # tests/test_config_parity.py against qwen3_tts.DEFAULT_VOICE.
    speaker: str = "voice_3"
    sample_rate: int = 24000
    speed: float = 1.0


@dataclasses.dataclass
class RenderConfig:
    """Playwright and FFmpeg video rendering parameters."""
    # Must equal msf.spec.FPS. Frame-denominated constants elsewhere assume 60
    # (DEFAULT_TRANSITION_FRAMES=18 -> 300ms; motion preset durations), so a
    # mismatch silently doubles or halves every animation.
    # Guarded by tests/test_config_parity.py.
    fps: int = 60
    width: int = 1080
    height: int = 1920
    headless: bool = True
    viewport_width: int = 1080
    viewport_height: int = 1920


@dataclasses.dataclass
class AudioConfig:
    """Audio mastering filters and LUFS target settings."""
    target_lufs: float = -16.0
    # 48kHz to match master_video_audio()'s aresample=48000 in
    # msf/engines/audio/mastering.py. These are two paths onto the same
    # timeline; 44100 here meant AudioMasterEngine resampled differently
    # than the graph did.
    sample_rate: int = 48000
    enable_highpass: bool = True
    enable_compressor: bool = True
    enable_eq: bool = True


@dataclasses.dataclass
class PipelineConfig:
    """Production pipeline execution and retry policies."""
    max_qc_attempts: int = 3
    auto_retry: bool = True
    parallel_scenes: bool = True
    save_intermediate: bool = True


@dataclasses.dataclass
class OutputConfig:
    """Output directory and codec specifications."""
    base_dir: str = "./output"
    format: str = "mp4"
    video_codec: str = "libx264"
    audio_codec: str = "aac"


def _section_from_dict(cls: type[Any], data: dict[str, Any] | None) -> Any:
    """Instantiate a config section dataclass safely from a dictionary."""
    if data is None or not isinstance(data, dict):
        return cls()
    field_names = {f.name for f in dataclasses.fields(cls)}
    filtered = {k: v for k, v in data.items() if k in field_names}
    return cls(**filtered)


@dataclasses.dataclass
class MSFConfig:
    """Root configuration object for Motion Studio Framework."""
    llm: LLMConfig = dataclasses.field(default_factory=LLMConfig)
    tts: TTSConfig = dataclasses.field(default_factory=TTSConfig)
    render: RenderConfig = dataclasses.field(default_factory=RenderConfig)
    audio: AudioConfig = dataclasses.field(default_factory=AudioConfig)
    pipeline: PipelineConfig = dataclasses.field(default_factory=PipelineConfig)
    output: OutputConfig = dataclasses.field(default_factory=OutputConfig)

    def to_dict(self) -> dict[str, Any]:
        """Export full configuration as a dictionary."""
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Self:
        """Construct MSFConfig from dictionary data, populating defaults for missing sections."""
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            llm=_section_from_dict(LLMConfig, data.get("llm")),
            tts=_section_from_dict(TTSConfig, data.get("tts")),
            render=_section_from_dict(RenderConfig, data.get("render")),
            audio=_section_from_dict(AudioConfig, data.get("audio")),
            pipeline=_section_from_dict(PipelineConfig, data.get("pipeline")),
            output=_section_from_dict(OutputConfig, data.get("output")),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> Self:
        """Load configuration from a YAML file. Returns default config if file does not exist."""
        file_path = Path(path)
        if not file_path.is_file():
            return cls()
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data if isinstance(data, dict) else {})

    def to_yaml(self, path: str | Path) -> None:
        """Save configuration to a YAML file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
