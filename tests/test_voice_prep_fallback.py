from __future__ import annotations

from types import SimpleNamespace

from msf.audio import voice_prep


def test_transcribe_uses_local_cli_fallback_when_faster_whisper_is_absent(tmp_path, monkeypatch) -> None:
    source = tmp_path / "reference.wav"
    source.write_bytes(b"placeholder")
    transcript = tmp_path / "reference_transcription_20260815_120000.json"
    transcript.write_text(
        '{"language":"rus","segments":[{"start":0.1,"end":1.2,"text":"Проверяемый текст."}],"full_text":"Проверяемый текст."}',
        encoding="utf-8",
    )

    def missing_whisper():
        raise ImportError("faster-whisper unavailable")

    monkeypatch.setattr(voice_prep, "_get_whisper", missing_whisper)
    monkeypatch.setattr(voice_prep.shutil, "which", lambda name: "/usr/local/bin/manus-speech-to-text" if name == "manus-speech-to-text" else None)
    monkeypatch.setattr(
        voice_prep.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=f"Completed transcription, JSON saved to {transcript}\n", stderr=""),
    )

    result = voice_prep.transcribe(source)

    assert result["model"] == "local speech-to-text fallback"
    assert result["device"] == "managed runtime"
    assert result["needs_proofreading"] is True
    assert result["text"] == "Проверяемый текст."
    assert result["segments"] == [{"start": 0.1, "end": 1.2, "text": "Проверяемый текст.", "logprob": None}]
