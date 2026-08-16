from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from msf.panel.server import app
from msf.studio import project_resources


client = TestClient(app)


def test_project_media_store_is_project_scoped_and_publicly_pathless(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(project_resources, "_PROJECTS_ROOT", tmp_path / "projects")
    staged = tmp_path / "candidate.png"
    staged.write_bytes(b"png-placeholder")

    asset = project_resources.register_staged_media(
        "demo_project", staged, "launch.png", "hero_image", "Official launch still",
    )
    assert asset.kind == "image"
    assert asset.role == "hero_image"
    assert asset.relative_uri == f"/api/studio/projects/demo_project/media/{asset.asset_id}"
    assert not staged.exists()

    resolved, media_path = project_resources.find_media("demo_project", asset.asset_id)
    assert resolved.asset_id == asset.asset_id
    assert media_path.is_file()
    assert "/output/" not in resolved.relative_uri
    assert "/projects/" in resolved.relative_uri

    project_resources.remove_media("demo_project", asset.asset_id)
    assert not media_path.exists()
    assert project_resources.list_media("demo_project") == []


def test_pinned_source_api_persists_public_brief_and_removes_by_id() -> None:
    response = client.post(
        "/api/studio/projects/source_test/sources",
        json={
            "url": "https://example.com/docs#section",
            "mode": "required",
            "reason": "Официальная документация нужна для factual claim",
        },
    )
    assert response.status_code == 200
    source = response.json()["source"]
    try:
        assert source["url"] == "https://example.com/docs"
        assert source["mode"] == "required"
        listed = client.get("/api/studio/projects/source_test/sources").json()["items"]
        assert [item["source_id"] for item in listed] == [source["source_id"]]
    finally:
        deleted = client.delete(f"/api/studio/projects/source_test/sources/{source['source_id']}")
        assert deleted.status_code == 200


def test_project_media_upload_api_stages_and_registers_without_path_input() -> None:
    response = client.post(
        "/api/studio/projects/upload_test/media/upload",
        data={"role": "supporting_image", "caption": "Скрин для сценария"},
        files={"file": ("screen.png", b"png-placeholder", "image/png")},
    )
    assert response.status_code == 200
    asset = response.json()["asset"]
    try:
        assert asset["kind"] == "image"
        assert asset["role"] == "supporting_image"
        assert asset["relative_uri"].endswith(asset["asset_id"])
        assert "output" not in asset["relative_uri"]
        listed = client.get("/api/studio/projects/upload_test/media").json()["items"]
        assert any(item["asset_id"] == asset["asset_id"] for item in listed)
    finally:
        deleted = client.delete(f"/api/studio/projects/upload_test/media/{asset['asset_id']}")
        assert deleted.status_code == 200


def test_registered_media_materializes_into_run_isolated_remotion_public(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(project_resources, "_PROJECTS_ROOT", tmp_path / "projects")
    monkeypatch.setattr(project_resources, "_REPO", tmp_path / "repo")
    staged = tmp_path / "recording.webm"
    staged.write_bytes(b"webm-placeholder")
    asset = project_resources.register_staged_media(
        "demo_project", staged, "recording.webm", "screen_recording", "Экран с шагами настройки",
    )

    run_id = "run_" + "a" * 32
    materialized = project_resources.materialize_media_for_render("demo_project", [asset], run_id)

    assert materialized == [{
        "asset_id": asset.asset_id,
        "role": "screen_recording",
        "kind": "video",
        "caption": "Экран с шагами настройки",
        "src": f"studio-resources/{run_id}/{asset.asset_id}.webm",
    }]
    assert (tmp_path / "repo" / "remotion" / "public" / "studio-resources" / run_id / f"{asset.asset_id}.webm").is_file()
    assert "projects" not in materialized[0]["src"]
    assert "output" not in materialized[0]["src"]


def test_prepare_run_resolves_project_resource_ids_into_immutable_snapshot(tmp_path, monkeypatch) -> None:
    from msf.studio import runs
    from msf.studio.runs import StudioRunService as RealStudioRunService

    monkeypatch.setattr(project_resources, "_PROJECTS_ROOT", tmp_path / "projects")
    staged = tmp_path / "hero.png"
    staged.write_bytes(b"png-placeholder")
    asset = project_resources.register_staged_media(
        "project_run", staged, "hero.png", "hero_image", "Product proof still",
    )
    source = project_resources.add_pinned_source(
        "project_run", "https://example.com/official", "required", "Official release notes",
    )
    run_root = tmp_path / "runs"
    monkeypatch.setattr(runs, "StudioRunService", lambda: RealStudioRunService(run_root))

    response = client.post(
        "/api/studio/runs/prepare",
        json={
            "project_id": "project_run",
            "topic": "Проверяем новый продукт по официальным материалам",
            "preset": "HeroKinetic",
            "media_asset_ids": [asset.asset_id],
            "pinned_source_ids": [source.source_id],
            "research": True,
        },
    )
    assert response.status_code == 200
    request = response.json()["request"]
    assert request["media_assets"][0]["asset_id"] == asset.asset_id
    assert request["media_assets"][0]["relative_uri"].startswith("/api/studio/projects/")
    assert request["pinned_sources"][0]["source_id"] == source.source_id
    assert "output/" not in request["media_assets"][0]["relative_uri"]
    assert str(tmp_path) not in request["media_assets"][0]["relative_uri"]
