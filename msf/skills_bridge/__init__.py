"""MSF Skills Bridge package.

Thin Python wrappers around external AI services used by MSF orchestrators,
so that higher-level orchestration code can stay model-agnostic.
"""

from msf.skills_bridge.qwen3_tts import Qwen3TTSEngine

__all__ = ["Qwen3TTSEngine"]
