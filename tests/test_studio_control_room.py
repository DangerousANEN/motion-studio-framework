from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from msf.panel.server import SceneThumbnailRequest, _thumbnail_cache_entry, app
from msf.studio.contracts import RunRequest
from msf.studio.runs import RunStateError, StudioRunService
from msf.studio import operator_settings
from msf.studio.worker_job import _activity_for


def test_control_room_graph_is_canonical_and_safe() -> None:
    client = TestClient(app)
    response = client.get("/api/studio/control-room/graph")
    assert response.status_code == 200
    payload = response.json()
    ids = [item["id"] for item in payload["nodes"]]
    assert ids[:3] == ["gate_check", "deep_research", "script_split"]
    assert "render" in ids and "qa" in ids
    assert payload["transport"] == "cursor_polling"
    assert all("prompt" not in item for item in payload["nodes"])


def test_draft_patch_is_bounded_and_locked_after_validation(tmp_path) -> None:
    service = StudioRunService(root=tmp_path)
    snapshot = service.create_run(RunRequest(topic="Проверяемая тема", preset="HeroKinetic"))

    original, edited = service.patch_draft(
        snapshot.run_id,
        request_patch={"topic": "Новая проверяемая тема", "music": False},
        operator_overrides={"deep_research": "Сначала найди первичные источники."},
    )
    assert original.status.value == "draft"
    assert edited.topic == "Новая проверяемая тема"
    assert edited.music is False
    assert edited.operator_overrides["deep_research"] == "Сначала найди первичные источники."
    assert service.get_request(snapshot.run_id).operator_overrides == edited.operator_overrides

    with pytest.raises(ValueError, match="unsupported draft patch"):
        service.patch_draft(snapshot.run_id, request_patch={"approved": True})
    with pytest.raises(ValueError, match="not supported"):
        service.patch_draft(snapshot.run_id, operator_overrides={"render": "делай быстрее"})

    service.validate(snapshot.run_id, valid=True)
    with pytest.raises(RunStateError, match="only a draft"):
        service.patch_draft(snapshot.run_id, request_patch={"topic": "Поздняя правка"})


def test_run_history_uses_persistent_sqlite_index(tmp_path) -> None:
    service = StudioRunService(root=tmp_path)
    snapshot = service.create_run(RunRequest(topic="Тема для истории", preset="HeroKinetic", voice="voice_3"))
    first = service.list_runs()
    assert first[0]["run_id"] == snapshot.run_id
    assert first[0]["topic"] == "Тема для истории"
    assert first[0]["voice"] == "voice_3"
    assert (tmp_path / "run_index.sqlite3").is_file()

    service.patch_draft(snapshot.run_id, request_patch={"topic": "Исправленная тема"})
    updated = service.list_runs()
    assert updated[0]["topic"] == "Исправленная тема"


def test_operator_settings_persist_only_safe_defaults(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(operator_settings, "_SETTINGS_PATH", tmp_path / "operator_settings.json")
    saved = operator_settings.save({"default_voice": "voice_3", "default_agent_level": 2})
    assert saved["default_voice"] == "voice_3"
    assert saved["default_agent_level"] == 2
    assert operator_settings.load()["default_style"] == "llm_hubs_neon"
    with pytest.raises(ValueError, match="unsupported"):
        operator_settings.save({"api_key": "must-not-store"})


def test_thumbnail_cache_key_tracks_validated_scene_spec() -> None:
    request = SceneThumbnailRequest(preset="HeroKinetic", demo_props=True)
    _, _, path_a, filename_a = _thumbnail_cache_entry(request)
    _, _, path_b, filename_b = _thumbnail_cache_entry(request)
    _, _, _, filename_other = _thumbnail_cache_entry(SceneThumbnailRequest(preset="KineticPhrase", demo_props=True))
    assert path_a == path_b
    assert filename_a == filename_b
    assert filename_a.startswith("HeroKinetic-") and filename_a.endswith(".png")
    assert filename_other != filename_a
    assert path_a.parent.name == "thumbnails"


def test_activity_payload_never_claims_fake_scene_progress() -> None:
    render = _activity_for("render", {"spec_dict": {"scenes": [{}, {}, {}]}})
    assert render["activity"] == "Рендерим композицию"
    assert render["scene_count"] == 3
    assert "scene_index" not in render
    assert "per-scene" in str(render["detail"])
