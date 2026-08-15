"""Persistent, non-secret operator defaults for the local Studio dashboard.

The settings are deliberately narrow: they influence newly created drafts only and
never rewrite an approved run. API keys, full LLM prompts and filesystem paths are
not settings and are therefore outside this store.
"""
from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_SETTINGS_PATH = _REPO / "output" / "studio" / "operator_settings.json"
_LOCK = RLock()
_ALLOWED = {
    "default_voice",
    "default_style",
    "default_agent_level",
    "default_research",
    "default_music",
    "default_sfx",
}
_DEFAULTS: dict[str, Any] = {
    "default_voice": None,
    "default_style": "llm_hubs_neon",
    "default_agent_level": 3,
    "default_research": True,
    "default_music": True,
    "default_sfx": True,
}


def load() -> dict[str, Any]:
    """Return safe defaults, merging a malformed/missing file back to defaults."""
    with _LOCK:
        payload = dict(_DEFAULTS)
        if not _SETTINGS_PATH.is_file():
            return payload
        try:
            saved = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return payload
        if isinstance(saved, dict):
            payload.update({key: saved[key] for key in _ALLOWED if key in saved})
        return payload


def save(patch: dict[str, Any]) -> dict[str, Any]:
    """Persist a validated partial settings patch atomically."""
    unknown = set(patch) - _ALLOWED
    if unknown:
        raise ValueError(f"unsupported settings fields: {', '.join(sorted(unknown))}")
    with _LOCK:
        payload = load()
        payload.update(patch)
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SETTINGS_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(_SETTINGS_PATH)
        return payload


__all__ = ["load", "save"]
