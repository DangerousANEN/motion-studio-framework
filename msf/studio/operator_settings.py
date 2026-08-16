"""Persistent, non-secret operator defaults for the local Studio dashboard.

Settings influence newly created drafts only and never rewrite an approved run.
Secrets, full prompts and filesystem paths remain outside this store.
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
    "default_voice", "default_style", "default_agent_level", "default_research",
    "default_music", "default_sfx", "default_content_archetype", "default_audience",
    "default_cta_handle", "default_cta_asset", "default_research_provider",
    "default_max_queries", "default_max_sources", "default_community_proof_mode",
    "default_comparison_mode", "default_comparison_models", "default_visual_evidence_mode",
    "default_require_observed_comparison", "default_duration_seconds", "default_fps",
    "default_music_volume", "default_sfx_volume", "default_auto_subtitles",
}
_DEFAULTS: dict[str, Any] = {
    "default_voice": None,
    "default_style": "llm_hubs_neon",
    "default_agent_level": 3,
    "default_research": True,
    "default_music": True,
    "default_sfx": True,
    "default_content_archetype": "auto",
    "default_audience": "широкая русскоязычная аудитория",
    "default_cta_handle": "@llm_hubs",
    "default_cta_asset": "готовый чек-лист и ссылки на источники",
    "default_research_provider": "duckduckgo",
    "default_max_queries": 3,
    "default_max_sources": 6,
    "default_community_proof_mode": "off",
    "default_comparison_mode": "none",
    "default_comparison_models": [],
    "default_visual_evidence_mode": None,
    "default_require_observed_comparison": False,
    "default_duration_seconds": 35,
    "default_fps": 60,
    "default_music_volume": 0.22,
    "default_sfx_volume": 0.55,
    "default_auto_subtitles": True,
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
