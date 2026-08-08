"""MSF Qwen3-TTS Bridge — Zero-Shot Voice Clone & CustomVoice interface.

Exposes a singleton-cached Qwen3TTSEngine and top-level helper functions for
seamless integration with MSF orchestrators.
"""
from __future__ import annotations

import os
import re
import tempfile
import warnings
from typing import Any, Optional, Tuple

import soundfile as sf
import torch

warnings.filterwarnings("ignore")

DEFAULT_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
DEFAULT_REF_AUDIO = r"C:/Users/ANEN/qwen3_1.7B_clone_test.wav"

_MODEL_SINGLETON: Optional[Any] = None


def get_qwen3_clone_model(model_id: str = DEFAULT_MODEL_ID) -> Any:
    global _MODEL_SINGLETON
    if _MODEL_SINGLETON is not None:
        return _MODEL_SINGLETON

    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    from qwen_tts import Qwen3TTSModel

    model = Qwen3TTSModel.from_pretrained(
        model_id,
        device_map="cuda:0",
        dtype=torch.bfloat16,
        attn_implementation="eager",
    )
    _MODEL_SINGLETON = model
    return _MODEL_SINGLETON


def phonetic_normalize(text: str) -> str:
    """Replace English tech terms with Russian transliterations for clear pronunciation."""
    replacements = {
        r"\bLLM\b": "ЛЛМ",
        r"\bHubs\b": "Хабс",
        r"\bGitHub\b": "Гитхаб",
        r"\bDevTools\b": "ДевТулз",
        r"\bOpenSource\b": "Оупенсорс",
        r"\bPython\b": "Пайтон",
        r"\bAI\b": "ИИ",
        r"\bOpenAI\b": "ОупенИИ",
    }
    for pat, rep in replacements.items():
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text


def synthesize_voice_clone(
    text: str,
    ref_audio: str = DEFAULT_REF_AUDIO,
    language: str = "Russian",
    output_path: Optional[str] = None,
) -> Tuple[str, float]:
    """Top-level helper for zero-shot voice cloning (1.7B-Base).
    
    Returns: (output_wav_path, duration_in_seconds)
    """
    normalized_text = phonetic_normalize(text)
    model = get_qwen3_clone_model()

    wavs, sr = model.generate_voice_clone(
        text=normalized_text,
        language=language,
        ref_audio=ref_audio,
        x_vector_only_mode=True,
    )

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="qwen3_clone_")
        os.close(fd)

    sf.write(output_path, wavs[0], sr)
    duration = len(wavs[0]) / float(sr)
    return output_path, duration


class Qwen3TTSEngine:
    def __init__(self, model_id: str = DEFAULT_MODEL_ID):
        self.model_id = model_id

    def voice_clone(self, text: str, ref_audio: str = DEFAULT_REF_AUDIO, output_path: Optional[str] = None) -> Tuple[str, float]:
        return synthesize_voice_clone(text=text, ref_audio=ref_audio, output_path=output_path)


__all__ = ["get_qwen3_clone_model", "synthesize_voice_clone", "phonetic_normalize", "Qwen3TTSEngine"]
