from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from msf.skills_bridge import qwen3_tts


class _FakeCloneModel:
    def __init__(self) -> None:
        self.prompt_calls = []
        self.generate_calls = []

    def create_voice_clone_prompt(self, **kwargs):
        self.prompt_calls.append(kwargs)
        return {"encoded": len(self.prompt_calls)}

    def generate_voice_clone(self, **kwargs):
        self.generate_calls.append(kwargs)
        return [np.zeros(240, dtype=np.float32)], 24000


def test_icl_prompt_is_reused_for_same_reference(tmp_path, monkeypatch) -> None:
    reference = tmp_path / "reference.wav"
    sf.write(reference, np.zeros(240, dtype=np.float32), 24000)
    model = _FakeCloneModel()
    qwen3_tts.clear_voice_prompt_cache()
    monkeypatch.setattr(qwen3_tts, "get_qwen3_clone_model", lambda: model)

    qwen3_tts.synthesize_voice_clone(
        "Первая строка.", ref_audio=str(reference), ref_text="Точный текст.",
        output_path=str(tmp_path / "first.wav"), polish=False,
    )
    qwen3_tts.synthesize_voice_clone(
        "Вторая строка.", ref_audio=str(reference), ref_text="Точный текст.",
        output_path=str(tmp_path / "second.wav"), polish=False,
    )

    assert len(model.prompt_calls) == 1
    assert len(model.generate_calls) == 2
    assert all("voice_clone_prompt" in call for call in model.generate_calls)
    assert all("ref_audio" not in call for call in model.generate_calls)
    assert qwen3_tts.voice_prompt_cache_stats() == {"entries": 1, "hits": 1, "misses": 1}
