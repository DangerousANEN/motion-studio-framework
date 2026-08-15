from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from msf.panel.server import app


client = TestClient(app)


def test_voice_upload_stages_supported_audio_without_registering_voice() -> None:
    response = client.post(
        "/api/voices/upload",
        files={"file": ("candidate.wav", b"small-wave-placeholder", "audio/wav")},
    )
    assert response.status_code == 200
    payload = response.json()
    staged = Path(payload["path"])
    try:
        assert payload["original_name"] == "candidate.wav"
        assert payload["bytes"] == len(b"small-wave-placeholder")
        assert staged.is_file()
        assert staged.parent.name == "voice_uploads"
    finally:
        staged.unlink(missing_ok=True)


def test_voice_upload_rejects_non_audio_extension_before_staging() -> None:
    response = client.post(
        "/api/voices/upload",
        files={"file": ("not-audio.txt", b"not audio", "text/plain")},
    )
    assert response.status_code == 422
    assert "unsupported audio format" in response.json()["detail"]
