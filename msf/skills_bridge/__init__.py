"""Thin wrappers around optional external AI services used by MSF orchestrators.

Heavy TTS dependencies are imported only when the TTS engine is explicitly used.
This keeps research, catalog, MCP and dashboard paths runnable on a local-first
installation that has not yet installed the optional Torch voice stack.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from msf.skills_bridge.qwen3_tts import Qwen3TTSEngine

__all__ = ["Qwen3TTSEngine"]


def __getattr__(name: str) -> Any:
    if name == "Qwen3TTSEngine":
        from msf.skills_bridge.qwen3_tts import Qwen3TTSEngine
        return Qwen3TTSEngine
    raise AttributeError(name)
