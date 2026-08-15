"""Audio preparation for voice references: transcription, denoise, measurement.

WHY THIS EXISTS
---------------
Adding a voice by hand went wrong in three ways that all produce a *worse voice*
rather than an error:

1. NO TRANSCRIPT -> the registry falls back to `x_vector_only_mode`: Qwen3-TTS
   copies the timbre but not the prosody, and the result is flat. Nothing warns
   you; you find out after rendering a video. So transcription is automated here
   and the transcript is treated as required.

2. NOISY REFERENCE -> ICL clones the *recording*, not just the speaker. Room hum
   and hiss in the reference come back in every synthesised line. Denoise is
   offered, but as an explicit choice with a before/after listen, because
   over-aggressive denoising eats sibilants and makes the clone lisp.

3. WRONG LENGTH OR LEVEL -> a 3-second reference gives the model too little to
   work with, and a clipped one bakes distortion into every output. Measured and
   reported before the voice is accepted.

WHAT IS DELIBERATELY NOT AUTOMATIC
----------------------------------
Nothing here silently "fixes" audio and reports success. Every transform returns
the measurements of what it did, and the caller (the panel) shows them, because
the failure mode being designed against is exactly a pipeline that quietly
produced something worse.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf

# Qwen3-TTS reference audio is resampled to 24k internally; keeping references at
# 24k mono means what the panel plays is what the model receives.
TARGET_SR = 24000

# Reference-length limits, measured against the two working voices in the repo
# (17.6s and 26.2s). Below ~6s ICL has too little prosody to copy; above ~40s the
# extra material stops helping and slows every synthesis call.
MIN_REF_SEC = 6.0
MAX_REF_SEC = 40.0
IDEAL_REF_SEC = (12.0, 30.0)


@dataclass
class AudioStats:
    """Objective measurements of a reference clip."""

    duration_sec: float
    sample_rate: int
    channels: int
    peak: float
    rms_db: float
    # Noise floor estimated from the quietest 10% of 50ms frames. A clean studio
    # recording sits below -55 dB; a laptop mic in a room is around -45.
    noise_floor_db: float
    # Peak minus noise floor. Under ~35 dB the reference carries audible hiss into
    # every cloned line.
    snr_db: float
    clipped_samples: int
    silence_lead_sec: float
    silence_tail_sec: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _db(x: float) -> float:
    return 20.0 * math.log10(max(1e-12, x))


def load_mono(path: Path) -> Tuple[np.ndarray, int]:
    """Read any audio file as float32 mono.

    ffmpeg rather than soundfile for the decode: references arrive as mp3/m4a/ogg
    from phones and Telegram, and libsndfile does not read mp3 on every build.
    """
    try:
        data, sr = sf.read(str(path), dtype="float32", always_2d=True)
        mono = data.mean(axis=1)
        return mono, int(sr)
    except Exception:
        pass

    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "decoded.wav"
        proc = subprocess.run(
            ["ffmpeg", "-nostdin", "-y", "-i", str(path), "-ac", "1",
             "-c:a", "pcm_f32le", str(wav)],
            capture_output=True, text=True, timeout=300,
        )
        if proc.returncode != 0 or not wav.is_file():
            tail = (proc.stderr or "").strip().splitlines()[-3:]
            raise ValueError(f"cannot decode {path.name}: {' | '.join(tail)}")
        data, sr = sf.read(str(wav), dtype="float32", always_2d=True)
        return data.mean(axis=1), int(sr)


def measure(path: Path) -> AudioStats:
    """Measure a clip. No modification, no opinions — just numbers."""
    y, sr = load_mono(path)
    if y.size == 0:
        raise ValueError(f"{path.name} decodes to zero samples")

    frame = max(1, int(sr * 0.05))
    n_frames = max(1, y.size // frame)
    trimmed = y[: n_frames * frame].reshape(n_frames, frame)
    frame_rms = np.sqrt((trimmed.astype(np.float64) ** 2).mean(axis=1))

    peak = float(np.abs(y).max())
    rms = float(np.sqrt((y.astype(np.float64) ** 2).mean()))
    # Quietest 10% of frames as the noise floor: speech has natural pauses, and
    # the floor in those pauses is what gets cloned into every output.
    quiet = np.sort(frame_rms)[: max(1, n_frames // 10)]
    floor = float(quiet.mean())

    # Leading/trailing silence, at a threshold relative to the clip's own peak so
    # it works for both a hot and a quiet recording.
    thresh = max(floor * 3.0, peak * 0.02)
    loud = np.nonzero(frame_rms > thresh)[0]
    lead = float(loud[0] * frame / sr) if loud.size else 0.0
    tail = float((n_frames - 1 - loud[-1]) * frame / sr) if loud.size else 0.0

    return AudioStats(
        duration_sec=round(y.size / sr, 2),
        sample_rate=sr,
        channels=1,
        peak=round(peak, 4),
        rms_db=round(_db(rms), 1),
        noise_floor_db=round(_db(floor), 1),
        snr_db=round(_db(peak) - _db(floor), 1),
        clipped_samples=int(np.count_nonzero(np.abs(y) >= 0.999)),
        silence_lead_sec=round(lead, 2),
        silence_tail_sec=round(tail, 2),
    )


def review(stats: AudioStats) -> List[Dict[str, str]]:
    """Turn measurements into findings the panel can show.

    Levels: "error" blocks the voice, "warn" is shown but allowed. A reference can
    be legitimately imperfect — the point is that the operator KNOWS before it
    becomes the project's voice, not that the tool refuses anything short of a
    studio booth.
    """
    out: List[Dict[str, str]] = []

    if stats.duration_sec < MIN_REF_SEC:
        out.append({
            "level": "error",
            "text": f"Всего {stats.duration_sec} с. ICL нужно минимум {MIN_REF_SEC:.0f} с, "
                    "иначе интонация не переносится и клон звучит плоско.",
        })
    elif stats.duration_sec > MAX_REF_SEC:
        out.append({
            "level": "warn",
            "text": f"{stats.duration_sec} с — длиннее {MAX_REF_SEC:.0f} с не улучшает клон, "
                    "но замедляет каждый синтез. Можно обрезать.",
        })
    elif not (IDEAL_REF_SEC[0] <= stats.duration_sec <= IDEAL_REF_SEC[1]):
        out.append({
            "level": "warn",
            "text": f"{stats.duration_sec} с — рабочая длина, но лучший диапазон "
                    f"{IDEAL_REF_SEC[0]:.0f}–{IDEAL_REF_SEC[1]:.0f} с.",
        })

    if stats.clipped_samples > 32:
        out.append({
            "level": "error",
            "text": f"{stats.clipped_samples} клиппованных сэмплов. Искажение попадёт "
                    "в каждую озвученную строку — шумодав его не убирает.",
        })
    elif stats.clipped_samples:
        out.append({
            "level": "warn",
            "text": f"{stats.clipped_samples} сэмплов на пределе — на грани клиппинга.",
        })

    if stats.snr_db < 30:
        out.append({
            "level": "warn",
            "text": f"SNR {stats.snr_db} dB — шумно. ICL клонирует запись, а не только "
                    "голос, поэтому шум вернётся в каждой строке. Включи шумоподавление.",
        })
    elif stats.snr_db < 40:
        out.append({
            "level": "warn",
            "text": f"SNR {stats.snr_db} dB — терпимо, но шумоподавление скорее поможет.",
        })

    if stats.peak < 0.1:
        out.append({
            "level": "warn",
            "text": f"Пик {stats.peak} — очень тихо. Нормализация включена по умолчанию.",
        })

    if stats.silence_lead_sec > 0.5 or stats.silence_tail_sec > 0.5:
        out.append({
            "level": "warn",
            "text": f"Тишина по краям: {stats.silence_lead_sec} с в начале, "
                    f"{stats.silence_tail_sec} с в конце. Обрезка включена по умолчанию.",
        })

    if stats.sample_rate < TARGET_SR:
        out.append({
            "level": "warn",
            "text": f"{stats.sample_rate} Гц ниже целевых {TARGET_SR} Гц — апсэмплинг "
                    "не добавит верхних частот, тембр будет глуше исходного.",
        })

    return out


# ------------------------------------------------------------------ transforms

@dataclass
class PrepResult:
    """What preparation actually did, with numbers on both sides."""

    out_path: str
    applied: List[str]
    before: Dict[str, Any]
    after: Dict[str, Any]
    findings: List[Dict[str, str]]


def prepare(
    src: Path,
    dst: Path,
    denoise: bool = False,
    trim_silence: bool = True,
    normalize: bool = True,
    denoise_strength: int = 14,
) -> PrepResult:
    """Produce a 24k mono reference, reporting every step.

    Chain order matters and is not arbitrary:
      highpass -> denoise -> trim -> normalize

    * highpass first: rumble below 80 Hz is not speech, and leaving it in makes
      the denoiser spend its noise budget on it instead of on hiss.
    * denoise before trim: silence detection reads levels, and denoising changes
      them. Trimming first would cut against the old floor and clip word onsets.
    * normalize last: anything after it would undo the level it set.

    `afftdn` rather than `arnndn`: arnndn needs an external .rnnn model file which
    is not shipped with the WinGet ffmpeg build here (verified: the filter exists,
    the models do not), so it would fail at runtime. `anlmdn` measured as doing
    almost nothing on this material (SNR 23.2 -> 23.2) for much more CPU.

    WHY `nf` IS MEASURED AND NOT A CONSTANT
    --------------------------------------
    afftdn's `nf` tells it where the noise floor is; it only removes what it
    believes is noise. The first version of this function hardcoded `nf=-45`,
    which on a clip whose real floor is -38.6 dB is a claim that the noise is 6 dB
    quieter than it is — so afftdn removed almost nothing:

        input (floor -38.6)              SNR 23.0
        nr=12 nf=-45  (hardcoded guess)  SNR 24.2   <- +1.2 dB, i.e. nothing
        nr=20 nf=-38  (measured)         SNR 37.0   <- +14 dB

    Worse, `nr` looked like it did nothing: 12, 25 and 40 dB all produced SNR 24.2
    because `nf` was the binding constraint, not `nr`. A "strength" control that
    changes nothing is exactly the kind of silent no-op this project keeps finding.

    HOW THE DEFAULT STRENGTH WAS CHOSEN
    -----------------------------------
    Not by ear — by measuring damage against the clean source. Test clip built by
    adding known noise to the real voice_3 reference, then comparing 5-11 kHz
    energy (sibilants) and 300-4000 Hz energy (speech body) to the clean original:

        nr    SNR   sibilants  speech body
        none  23.2    5.038      1.068      (5x = the noise itself)
        14    32.8    0.968      0.980      <- default
        20    37.0    0.645      0.967
        25    45.3    0.299      0.935
        30    50.6    0.067      0.859      s/sh audibly destroyed
        40    60.0    0.005      0.738

    So the SNR number keeps improving long after the voice has been ruined. At
    nr=14 sibilants land within 3% of the clean original while SNR gains ~10 dB;
    past nr=20 the loss is measurable, and past 25 it is gross. Hence the default
    of 14 and a hard cap at 24.
    """
    if not src.is_file():
        raise FileNotFoundError(f"no such audio file: {src}")

    before = measure(src)
    applied: List[str] = []

    chain: List[str] = ["highpass=f=80"]
    applied.append("highpass 80 Гц (убирает рокот, не речь)")

    if denoise:
        nr = max(1, min(24, int(denoise_strength)))
        # nf from the MEASURED floor of this clip. Rounding down by ~0 dB was the
        # best of the tested offsets; -1 dB begins to leave HF noise behind
        # (sibilant ratio 1.17, i.e. brighter than the clean source = residual
        # hiss), and +1 dB starts cutting real sibilants.
        nf = int(round(before.noise_floor_db))
        # tn=0: noise tracking follows a changing floor, which on a short static
        # recording chases the speech itself and re-learns the voice as noise.
        chain.append(f"afftdn=nr={nr}:nf={nf}:tn=0")
        applied.append(f"afftdn nr={nr} dB, nf={nf} dB (порог измерен по записи)")

    if trim_silence:
        # Trim both ends by reversing between passes: silenceremove only trims the
        # start, so start -> reverse -> start -> reverse handles the tail.
        peak_db = max(-60.0, min(-20.0, before.noise_floor_db + 8.0))
        one = (f"silenceremove=start_periods=1:start_duration=0.05:"
               f"start_threshold={peak_db:.0f}dB:detection=rms")
        chain += [one, "areverse", one, "areverse"]
        applied.append(f"обрезка тишины по краям (порог {peak_db:.0f} dB)")

    if normalize:
        # Peak-normalise to -1.5 dBFS rather than EBU loudnorm: the reference is a
        # short clip and loudnorm's two-pass gating misbehaves on those, while the
        # model cares about level consistency, not broadcast loudness.
        chain.append("dynaudnorm=f=200:g=5:p=0.9")
        # `level=0` is essential: FFmpeg's default post-limiter auto-level can
        # scale the protected signal back up to full scale, defeating the -1.5
        # dBFS ceiling and creating clipped samples in the prepared reference.
        chain.append("alimiter=limit=0.84:level=0")
        applied.append("выравнивание уровня + лимитер -1.5 dBFS")

    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-nostdin", "-y", "-i", str(src),
        "-af", ",".join(chain),
        "-ac", "1", "-ar", str(TARGET_SR),
        "-c:a", "pcm_s16le", str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not dst.is_file():
        tail = (proc.stderr or "").strip().splitlines()[-4:]
        raise RuntimeError(f"ffmpeg failed: {' | '.join(tail)}")

    after = measure(dst)

    # Verify the transform did not destroy the clip. Silence trimming with a bad
    # threshold can eat almost everything, and that must not pass as success.
    if after.duration_sec < min(MIN_REF_SEC, before.duration_sec * 0.5):
        raise RuntimeError(
            f"обработка сократила запись с {before.duration_sec}s до "
            f"{after.duration_sec}s — порог тишины съел речь; отключи обрезку"
        )

    findings = review(after)
    if denoise:
        gained = after.snr_db - before.snr_db
        # Report SNR, NOT the absolute noise floor. Normalization raises the whole
        # signal — the floor moved -38.6 -> -31.3 dB on the test clip while the
        # noise got objectively quieter, so quoting the raw floor across the chain
        # reads as if denoising made things worse.
        findings.insert(0, {
            "level": "info",
            "text": f"Шумодав nr={nr}: SNR {before.snr_db} → {after.snr_db} dB "
                    f"({gained:+.1f}). Уровень выровнен, поэтому абсолютный "
                    f"шумовой пол сравнивать нельзя — сравнивай SNR.",
        })
        # A "turn on denoise" hint after denoising is already on is noise itself.
        findings = [
            f for f in findings
            if "Включи шумоподавление" not in f["text"]
            and "шумоподавление скорее поможет" not in f["text"]
        ]
        if after.snr_db < 30:
            findings.append({
                "level": "warn",
                "text": f"SNR {after.snr_db} dB даже после обработки. Сильнее давить "
                        "нельзя — начнут пропадать шипящие. Нужна более чистая запись.",
            })

    return PrepResult(
        out_path=str(dst),
        applied=applied,
        before=before.to_dict(),
        after=after.to_dict(),
        findings=findings,
    )


# ---------------------------------------------------------------- transcription

_WHISPER_MODEL = None

# large-v3-turbo, chosen by measurement rather than by "bigger is better".
#
# Benchmarked on the real voice_3 reference (26.2s of Russian speech) on this
# machine's RTX 4060, float16, beam_size=5, accuracy = word-level similarity
# against the human-written transcript already in voices.json:
#
#     model             load    transcribe        accuracy
#     large-v3-turbo    5.1s    1.9s  (13.5x RT)   97.7%   <- default
#     large-v3          7.3s    6.6s  ( 4.0x RT)   97.7%
#     medium            3.5s    5.7s  ( 4.6x RT)   92.5%
#
# turbo matches large-v3 word for word here while being 3.5x faster, so large-v3
# buys nothing on this material. `medium` is visibly worse and not worth the 5%.
#
# The single disagreement in both large models was "дефонизирующие" ->
# "дифонизирующие" — a nonsense word in a deliberately absurd test sentence. That
# is why the panel always shows the transcript for editing instead of saving it
# blind: 97.7% is excellent and still not exact, and ICL aligns audio to the text
# it is given.
_WHISPER_SIZE = "large-v3-turbo"


def _get_whisper():
    """Load faster-whisper once and keep it.

    faster-whisper (CTranslate2) rather than openai-whisper: same weights, much
    faster, already installed (1.2.1 verified).

    CUDA is used when available and CPU is a real fallback, not a silent one — on
    CPU the same clip took 68.4s against 38.2s on GPU for the large model, so the
    device is reported to the caller and shown in the panel.
    """
    global _WHISPER_MODEL
    if _WHISPER_MODEL is not None:
        return _WHISPER_MODEL
    from faster_whisper import WhisperModel

    device, compute = "cpu", "int8"
    try:
        import torch

        if torch.cuda.is_available():
            device, compute = "cuda", "float16"
    except Exception:
        pass
    _WHISPER_MODEL = WhisperModel(_WHISPER_SIZE, device=device, compute_type=compute)
    # WhisperModel exposes no .device attribute (checked: returns '?'), so record
    # what was asked for — otherwise the panel cannot report GPU vs CPU at all.
    _WHISPER_MODEL._msf_device = device  # type: ignore[attr-defined]
    _WHISPER_MODEL._msf_compute = compute  # type: ignore[attr-defined]
    return _WHISPER_MODEL


def _transcribe_with_local_cli(path: Path) -> Dict[str, Any]:
    """Use the bundled local speech-to-text utility when faster-whisper is absent.

    The utility may use a managed runtime rather than the project's Python env. Its
    output still remains review-only: no result from this fallback is auto-saved to
    a voice registry, and no artificial confidence score is invented.
    """
    command = shutil.which("manus-speech-to-text")
    if not command:
        raise ImportError("faster-whisper and local speech-to-text fallback are unavailable")
    started = __import__("time").time()
    proc = subprocess.run([command, str(path)], capture_output=True, text=True, timeout=900)
    output = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    if proc.returncode != 0:
        tail = output.strip().splitlines()[-4:]
        raise RuntimeError(f"local speech-to-text failed: {' | '.join(tail)}")
    found = re.findall(r"JSON saved to\s+(.+?\.json)(?:\n|$)", output)
    candidate = Path(found[-1].strip()) if found else None
    if not candidate or not candidate.is_file():
        # The command writes beside the source. Time-gate candidates so an old
        # transcription cannot be incorrectly returned for a new reference.
        recent = [item for item in path.parent.glob(f"{path.stem}_transcription_*.json") if item.stat().st_mtime >= started - 2]
        candidate = max(recent, key=lambda item: item.stat().st_mtime) if recent else None
    if not candidate or not candidate.is_file():
        raise RuntimeError("local speech-to-text completed but produced no JSON transcript")
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    raw_segments = payload.get("segments") if isinstance(payload, dict) else None
    parts = []
    for segment in raw_segments if isinstance(raw_segments, list) else []:
        if not isinstance(segment, dict):
            continue
        parts.append({
            "start": round(float(segment.get("start", 0)), 2),
            "end": round(float(segment.get("end", 0)), 2),
            "text": str(segment.get("text", "")).strip(),
            "logprob": None,
        })
    text = " ".join(part["text"] for part in parts).strip()
    return {
        "text": text or str(payload.get("full_text", "")).strip(),
        "language": str(payload.get("language", "unknown")),
        "language_probability": None,
        "segments": parts,
        "mean_logprob": None,
        "low_confidence": None,
        "model": "local speech-to-text fallback",
        "device": "managed runtime",
        "compute_type": "managed",
        "needs_proofreading": True,
    }


def transcribe(path: Path, language: str = "ru") -> Dict[str, Any]:
    """Transcribe a reference clip verbatim.

    WHY `condition_on_previous_text=False`
    --------------------------------------
    Whisper's default carries previous output forward as context, which on a short
    clip makes it *invent* continuations that were never said. For a voice
    reference the transcript must match the audio exactly — a hallucinated tail
    silently degrades the ICL alignment.

    WHY NO VAD FILTER
    -----------------
    vad_filter drops segments it judges non-speech. On a quiet-but-real utterance
    that removes words, and a transcript missing words is worse than one including
    a breath.
    """
    try:
        model = _get_whisper()
    except ImportError:
        return _transcribe_with_local_cli(path)
    segments, info = model.transcribe(
        str(path),
        language=language,
        beam_size=5,
        condition_on_previous_text=False,
        vad_filter=False,
        word_timestamps=False,
    )
    parts: List[Dict[str, Any]] = []
    for s in segments:
        parts.append({
            "start": round(s.start, 2),
            "end": round(s.end, 2),
            "text": s.text.strip(),
            # avg_logprob is the model's own confidence. Below about -1.0 the
            # transcript is usually wrong, and a wrong transcript is worse for ICL
            # than no transcript, so it is surfaced rather than hidden.
            "logprob": round(getattr(s, "avg_logprob", 0.0), 2),
        })

    text = " ".join(p["text"] for p in parts).strip()
    text = " ".join(text.split())
    mean_lp = (
        round(sum(p["logprob"] for p in parts) / len(parts), 2) if parts else -99.0
    )
    return {
        "text": text,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "segments": parts,
        "mean_logprob": mean_lp,
        "low_confidence": mean_lp < -1.0,
        "model": _WHISPER_SIZE,
        "device": getattr(model, "_msf_device", "unknown"),
        "compute_type": getattr(model, "_msf_compute", "unknown"),
        # Measured 97.7% word agreement with a human transcript on the project's own
        # reference. Surfaced so the operator knows to proofread rather than trust.
        "needs_proofreading": True,
    }


__all__ = [
    "AudioStats",
    "PrepResult",
    "TARGET_SR",
    "MIN_REF_SEC",
    "MAX_REF_SEC",
    "load_mono",
    "measure",
    "review",
    "prepare",
    "transcribe",
]
