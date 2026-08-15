"""MSF Qwen3-TTS Bridge — zero-shot voice cloning with prosody transfer.

Model: Qwen3-TTS Base — CUDA 1.7B when available, official 0.6B CPU fallback otherwise.

Two cloning modes exist, and the difference is audible:

  x_vector_only_mode=True   speaker embedding only. Timbre is copied, prosody is
                            not — the model falls back to its own flat default
                            cadence. This is what made earlier renders sound
                            robotic.
  x_vector_only_mode=False  in-context learning. Requires ref_text (the verbatim
                            transcript of ref_audio). The model hears HOW the
                            reference was spoken and carries that rhythm and
                            intonation into the new line.

ICL is the default here. A reference without a transcript silently degrades to
x-vector mode, so `describe_reference()` makes that explicit rather than leaving
you guessing why the output sounds flat.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import soundfile as sf

warnings.filterwarnings("ignore")

CUDA_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
CPU_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
# Users with a local model cache may override either choice without changing code.
DEFAULT_MODEL_ID = os.getenv("MSF_TTS_MODEL", CUDA_MODEL_ID)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VOICES_JSON = _REPO_ROOT / "assets" / "voices" / "voices.json"

# Fallback when no voice registry entry is selected.
# Default voice key from the registry. Points at a trimmed human recording that
# is verified to work in ICL mode — see assets/voices/voices.json.
# The default MUST be a key that exists in voices.json WITH a transcript.
# It used to be "syenduk", which is absent from the registry: resolve_voice(None)
# fell through to the bare DEFAULT_REF_AUDIO path with ref_text=None, silently
# downgrading every unattended render to x-vector mode (timbre copy, flat
# prosody) instead of the ICL prosody transfer Qwen3-TTS is chosen for.
DEFAULT_VOICE = "msf_narrator_recovered"

# Absolute fallback if the registry is missing entirely.
DEFAULT_REF_AUDIO = str(_REPO_ROOT / "assets" / "voices" / "refs" / "syenduk_8s_24k.wav")

_MODEL_SINGLETON: Optional[Any] = None
_VOICES_CACHE: Optional[Dict[str, Dict[str, Any]]] = None
# Qwen can reuse the encoded reference prompt across many lines. Caching is keyed
# by the exact audio path, stat signature and verbatim text so modified references
# cannot silently borrow an obsolete speaker embedding.
_VOICE_PROMPT_CACHE: Dict[str, Any] = {}
_VOICE_PROMPT_CACHE_HITS = 0
_VOICE_PROMPT_CACHE_MISSES = 0
_VOICE_PROMPT_LOCK = threading.RLock()
_SYNTH_LOCK = threading.RLock()

# Tail fade. Qwen3 sometimes ends a clip while the waveform still carries real
# energy, which reads as a clipped word. A short fade removes the click without
# audibly shortening speech.
TAIL_FADE_MS = 60
LEAD_SILENCE_MS = 30
TAIL_SILENCE_MS = 120


def get_qwen3_clone_model(model_id: Optional[str] = None) -> Any:
    """Load an official Qwen3-TTS Base model as a process-wide singleton.

    GPU hosts keep the 1.7B checkpoint. CPU-only hosts must not attempt a false
    ``cuda:0`` load: they use the official 0.6B Base model in float32 eager mode.
    It is slower than GPU inference, but it is a real, bounded batch fallback for
    local Studio rendering rather than an immediate 500 error.
    """
    global _MODEL_SINGLETON
    if _MODEL_SINGLETON is not None:
        return _MODEL_SINGLETON

    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    import torch
    from qwen_tts import Qwen3TTSModel

    if torch.cuda.is_available():
        selected = model_id or DEFAULT_MODEL_ID
        model = Qwen3TTSModel.from_pretrained(
            selected,
            device_map="cuda:0",
            dtype=torch.bfloat16,
            attn_implementation="eager",
        )
    else:
        selected = model_id or os.getenv("MSF_TTS_CPU_MODEL", CPU_MODEL_ID)
        model = Qwen3TTSModel.from_pretrained(
            selected,
            device_map="cpu",
            dtype=torch.float32,
            attn_implementation="eager",
        )
    _MODEL_SINGLETON = model
    return _MODEL_SINGLETON


def _voice_prompt_key(ref_audio: str, ref_text: str) -> str:
    path = Path(ref_audio).resolve()
    stat = path.stat()
    material = f"{path}|{stat.st_mtime_ns}|{stat.st_size}|{ref_text}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _cached_voice_clone_prompt(model: Any, ref_audio: str, ref_text: str) -> Any:
    """Build one Qwen ICL reference prompt per exact audio/transcript pair."""
    global _VOICE_PROMPT_CACHE_HITS, _VOICE_PROMPT_CACHE_MISSES
    key = _voice_prompt_key(ref_audio, ref_text)
    with _VOICE_PROMPT_LOCK:
        if key in _VOICE_PROMPT_CACHE:
            _VOICE_PROMPT_CACHE_HITS += 1
            return _VOICE_PROMPT_CACHE[key]
        _VOICE_PROMPT_CACHE_MISSES += 1
        _VOICE_PROMPT_CACHE[key] = model.create_voice_clone_prompt(
            ref_audio=ref_audio,
            ref_text=ref_text,
            x_vector_only_mode=False,
        )
        return _VOICE_PROMPT_CACHE[key]


def voice_prompt_cache_stats() -> Dict[str, int]:
    """Small safe observability snapshot; no prompt content or source transcript."""
    with _VOICE_PROMPT_LOCK:
        return {
            "entries": len(_VOICE_PROMPT_CACHE),
            "hits": _VOICE_PROMPT_CACHE_HITS,
            "misses": _VOICE_PROMPT_CACHE_MISSES,
        }


def clear_voice_prompt_cache() -> None:
    """Clear encoded references after an operator replaces or removes voice assets."""
    global _VOICE_PROMPT_CACHE_HITS, _VOICE_PROMPT_CACHE_MISSES
    with _VOICE_PROMPT_LOCK:
        _VOICE_PROMPT_CACHE.clear()
        _VOICE_PROMPT_CACHE_HITS = 0
        _VOICE_PROMPT_CACHE_MISSES = 0


# ---------------------------------------------------------------- voice registry

def load_voices() -> Dict[str, Dict[str, Any]]:
    """Load the voice registry (assets/voices/voices.json)."""
    global _VOICES_CACHE
    if _VOICES_CACHE is not None:
        return _VOICES_CACHE
    if _VOICES_JSON.exists():
        _VOICES_CACHE = json.loads(_VOICES_JSON.read_text(encoding="utf-8"))
    else:
        _VOICES_CACHE = {}
    return _VOICES_CACHE


def resolve_voice(voice: Optional[str]) -> Tuple[str, Optional[str]]:
    """Resolve a voice name to (ref_audio_path, ref_text).

    `voice` may be a registry key ("syenduk") or a direct path to a wav file.
    Registry paths may be relative to the repo root so the project stays
    portable. Returns ref_text=None when no transcript is known, which
    downgrades the render to x-vector mode.
    """
    if not voice:
        # Fall through to the registry default so the transcript comes with it —
        # returning a bare path here would silently disable ICL.
        voices = load_voices()
        if DEFAULT_VOICE in voices:
            voice = DEFAULT_VOICE
        else:
            return DEFAULT_REF_AUDIO, None

    voices = load_voices()
    if voice in voices:
        entry = voices[voice]
        ref = entry["ref_audio"]
        if not os.path.isabs(ref):
            ref = str((_REPO_ROOT / ref).resolve())
        return ref, entry.get("ref_text")

    if os.path.exists(voice):
        return voice, None

    known = sorted(k for k in voices if not k.startswith("_"))
    raise ValueError(
        f"Unknown voice {voice!r}. Known voices: {known or '(registry empty)'}. "
        "Pass a registry key or an existing wav path."
    )


def describe_reference(voice: Optional[str]) -> Dict[str, Any]:
    """Report which cloning mode a voice will actually get, and why."""
    ref_audio, ref_text = resolve_voice(voice)
    exists = os.path.exists(ref_audio)
    info: Dict[str, Any] = {"ref_audio": ref_audio, "exists": exists}
    if exists:
        meta = sf.info(ref_audio)
        info["duration_sec"] = round(meta.duration, 2)
        info["sample_rate"] = meta.samplerate
    info["has_ref_text"] = bool(ref_text)
    info["mode"] = "ICL (prosody transferred)" if ref_text else "x-vector (timbre only, flatter)"
    if not ref_text:
        info["hint"] = (
            "No transcript for this reference — add one to assets/voices/voices.json "
            "to unlock prosody transfer."
        )
    return info


# ---------------------------------------------------------------- text handling

def _load_lexicon() -> Dict[str, str]:
    path = _REPO_ROOT / "assets" / "voices" / "lexicon.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def phonetic_normalize(text: str, extra: Optional[Dict[str, str]] = None) -> str:
    """Rewrite terms the TTS mispronounces into phonetic Russian spellings.

    Longest-first so 'Qwen3-TTS' wins over a bare 'TTS'. The project lexicon in
    assets/voices/lexicon.json is applied first, then any per-call overrides.
    """
    table: Dict[str, str] = dict(_load_lexicon())
    if extra:
        table.update(extra)

    for src in sorted(table, key=len, reverse=True):
        dst = table[src]
        # \b fails against Cyrillic on some builds; use explicit boundaries.
        pattern = r"(?<![0-9A-Za-zА-Яа-яЁё])" + re.escape(src) + r"(?![0-9A-Za-zА-Яа-яЁё])"
        text = re.sub(pattern, dst, text, flags=re.IGNORECASE)
    return text


# ---------------------------------------------------------------- audio polish

def _polish(wav: np.ndarray, sr: int) -> np.ndarray:
    """Fade the tail and pad both ends.

    Qwen3 can stop mid-decay, which sounds like a cut-off word and clicks when
    scenes are concatenated. Fading the last few ms and padding with a little
    digital silence fixes both without trimming speech.
    """
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    wav = wav.astype(np.float32, copy=True)

    fade_len = min(int(sr * TAIL_FADE_MS / 1000), len(wav))
    if fade_len > 0:
        wav[-fade_len:] *= np.linspace(1.0, 0.0, fade_len, dtype=np.float32)

    lead = np.zeros(int(sr * LEAD_SILENCE_MS / 1000), dtype=np.float32)
    tail = np.zeros(int(sr * TAIL_SILENCE_MS / 1000), dtype=np.float32)
    return np.concatenate([lead, wav, tail])


def tail_energy_ratio(wav: np.ndarray, sr: int, window_ms: int = 80) -> float:
    """Ratio of last-window peak to overall peak. High values mean an abrupt cut."""
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    a = np.abs(wav)
    peak = float(a.max()) if a.size else 0.0
    if peak <= 0:
        return 0.0
    n = min(int(sr * window_ms / 1000), len(a))
    return float(a[-n:].max() / peak)


# ---------------------------------------------------------------- synthesis

def synthesize_voice_clone(
    text: str,
    ref_audio: Optional[str] = None,
    ref_text: Optional[str] = None,
    voice: Optional[str] = None,
    language: str = "Russian",
    output_path: Optional[str] = None,
    lexicon: Optional[Dict[str, str]] = None,
    polish: bool = True,
    max_new_tokens: Optional[int] = None,
) -> Tuple[str, float]:
    """Synthesize `text` in a cloned voice.

    Prefers ICL (prosody transfer). Falls back to x-vector mode only when no
    transcript is available for the reference.

    `max_new_tokens` caps generation. Without a cap the model can loop and hang
    indefinitely on some reference/text combinations. The default budget scales
    with text length at ~12.5 audio tokens per second of speech.

    Returns: (wav_path, duration_seconds)
    """
    if voice is not None:
        resolved_audio, resolved_text = resolve_voice(voice)
        ref_audio = ref_audio or resolved_audio
        ref_text = ref_text or resolved_text
    ref_audio = ref_audio or DEFAULT_REF_AUDIO

    if not os.path.exists(ref_audio):
        raise FileNotFoundError(
            f"Reference audio not found: {ref_audio}. "
            "Check assets/voices/voices.json or pass an existing path."
        )

    normalized = phonetic_normalize(text, extra=lexicon)
    model = get_qwen3_clone_model()

    use_icl = bool(ref_text)
    kwargs: Dict[str, Any] = {
        "text": normalized,
        "language": language,
    }
    if use_icl:
        # Official Qwen API supports a reusable `voice_clone_prompt`; this avoids
        # re-encoding the same source WAV for every scene narration line.
        kwargs["voice_clone_prompt"] = _cached_voice_clone_prompt(model, ref_audio, str(ref_text))
    else:
        kwargs["ref_audio"] = ref_audio
        kwargs["x_vector_only_mode"] = True

    # Hard cap on generation. Qwen3 emits ~12.5 audio tokens per second; Russian
    # narration runs ~13 chars/sec. Budget generously (3x) so normal lines are
    # never clipped, but a runaway loop still terminates instead of hanging.
    if max_new_tokens is None:
        est_seconds = max(2.0, len(normalized) / 13.0)
        max_new_tokens = int(min(4096, max(256, est_seconds * 12.5 * 3)))
    kwargs["max_new_tokens"] = max_new_tokens

    # Model objects are process-wide and Torch generation is not safe to execute
    # concurrently through the same CPU model. Serialize calls instead of trading
    # a small queue for corrupt audio or an out-of-memory crash.
    with _SYNTH_LOCK:
        wavs, sr = model.generate_voice_clone(**kwargs)
    wav = np.asarray(wavs[0], dtype=np.float32)

    if polish:
        wav = _polish(wav, sr)

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="qwen3_clone_")
        os.close(fd)

    sf.write(output_path, wav, sr)
    return output_path, len(wav) / float(sr)


class Qwen3TTSEngine:
    def __init__(self, model_id: str = DEFAULT_MODEL_ID):
        self.model_id = model_id

    def voice_clone(
        self,
        text: str,
        ref_audio: Optional[str] = None,
        voice: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Tuple[str, float]:
        return synthesize_voice_clone(
            text=text, ref_audio=ref_audio, voice=voice, output_path=output_path
        )


__all__ = [
    "get_qwen3_clone_model",
    "synthesize_voice_clone",
    "phonetic_normalize",
    "Qwen3TTSEngine",
    "load_voices",
    "resolve_voice",
    "describe_reference",
    "tail_energy_ratio",
    "clear_voice_prompt_cache",
    "voice_prompt_cache_stats",
    "CUDA_MODEL_ID",
    "CPU_MODEL_ID",
    "DEFAULT_MODEL_ID",
]
