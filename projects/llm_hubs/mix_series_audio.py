"""Build narration-first masters for the LLM Hubs August release series.

The source music is generated once and sliced deterministically.  Procedural SFX
come from MSF's registered semantic catalog; their gain is intentionally lower
than speech.  Every master is duration-locked to its VideoSpec.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from msf.audio.sfx import SFX_REGISTRY, render as render_sfx
import msf.audio.sfx_extra  # noqa: F401 - registers extended local effects

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "projects" / "llm_hubs"
AUDIO = PROJECT / "audio"
OUTPUT = PROJECT / "generated"
SR = 44_100
VOICE_OFFSET = 0.32

# Cues create edit rhythm without fighting the voice.  Names not present in an
# older MSF catalog are skipped deterministically rather than breaking release.
CUE_PLAN: dict[str, list[tuple[float, str, float]]] = {
    "01_gemini37_flash_vs_sonnet5": [(0.15, "whoosh_short", 0.30), (5.2, "counter_tick", 0.20), (10.6, "counter_tick", 0.20), (16.0, "focus_ring", 0.18), (22.0, "success_chime", 0.20), (24.2, "send_swoosh", 0.22)],
    "02_deepseek_v4pro_0813": [(0.12, "modal_in", 0.26), (4.9, "receive_pop", 0.18), (9.1, "send_swoosh", 0.18), (15.0, "keyboard_run", 0.16), (20.4, "focus_ring", 0.18), (27.5, "success_chime", 0.20)],
    "03_deepseek_v4pro_cost_clock": [(0.10, "whoosh_short", 0.28), (3.5, "counter_tick", 0.20), (7.2, "counter_tick", 0.20), (12.3, "focus_ring", 0.18), (17.5, "notify_ding", 0.18), (25.2, "success_chime", 0.20)],
    "04_grok46_long_agent": [(0.12, "modal_in", 0.26), (5.0, "focus_ring", 0.18), (10.4, "whoosh_short", 0.22), (15.8, "counter_tick", 0.18), (22.0, "keyboard_run", 0.15), (24.8, "success_chime", 0.20)],
    "05_august_model_costmap": [(0.12, "whoosh_short", 0.28), (3.6, "counter_tick", 0.19), (7.4, "counter_tick", 0.19), (11.3, "counter_tick", 0.19), (15.2, "counter_tick", 0.19), (21.0, "focus_ring", 0.17), (30.2, "success_chime", 0.20)],
}
MUSIC_OFFSETS = {
    "01_gemini37_flash_vs_sonnet5": 0.0,
    "02_deepseek_v4pro_0813": 31.0,
    "03_deepseek_v4pro_cost_clock": 62.0,
    "04_grok46_long_agent": 93.0,
    "05_august_model_costmap": 121.0,
}


def _read_stereo(path: Path) -> np.ndarray:
    data, rate = sf.read(path, always_2d=True, dtype="float32")
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    if rate == SR:
        return data
    from math import gcd
    factor = gcd(int(rate), SR)
    return resample_poly(data, SR // factor, int(rate) // factor, axis=0).astype(np.float32)


def _fit(source: np.ndarray, length: int, offset: int = 0) -> np.ndarray:
    if len(source) == 0:
        return np.zeros((length, 2), dtype=np.float32)
    if offset:
        offset %= len(source)
        source = np.concatenate((source[offset:], source[:offset]), axis=0)
    repeats = int(np.ceil(length / len(source)))
    return np.tile(source, (repeats, 1))[:length].copy()


def _fade(samples: np.ndarray, seconds: float = 0.5) -> None:
    n = min(int(seconds * SR), len(samples) // 2)
    if n:
        ramp = np.linspace(0.0, 1.0, n, dtype=np.float32)[:, None]
        samples[:n] *= ramp
        samples[-n:] *= ramp[::-1]


def _place(master: np.ndarray, mono: np.ndarray, start_sec: float, gain: float) -> None:
    start = max(0, int(start_sec * SR))
    if start >= len(master):
        return
    signal = np.column_stack((mono, mono)).astype(np.float32) * gain
    count = min(len(signal), len(master) - start)
    master[start:start + count] += signal[:count]


def _voice_duck(background: np.ndarray, voice: np.ndarray) -> np.ndarray:
    # Smooth envelope; music remains present, but loses ~7 dB while someone speaks.
    env = np.max(np.abs(voice), axis=1)
    window = max(1, int(SR * 0.07))
    env = np.convolve(env, np.ones(window, dtype=np.float32) / window, mode="same")
    norm = np.clip(env / 0.035, 0.0, 1.0)[:, None]
    return background * (1.0 - 0.58 * norm)


def _duration_map() -> dict[str, float]:
    manifest = json.loads((OUTPUT / "series_manifest.json").read_text(encoding="utf-8"))
    return {item["slug"]: float(item["duration_seconds"]) for item in manifest["videos"]}


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    music = _read_stereo(AUDIO / "music_neon_tech_master.wav")
    durations = _duration_map()
    produced: list[dict[str, Any]] = []
    for index, (slug, duration) in enumerate(durations.items(), start=1):
        length = int(round(duration * SR))
        # v2.2 narration is authored as scene-level beats. Fall back only for
        # historical specs so the source project remains reproducible.
        voice_path = AUDIO / f"voice_v22_{index:02d}_{slug.split('_', 1)[1]}.wav"
        if not voice_path.is_file():
            voice_path = AUDIO / f"voice_{index:02d}_{slug.split('_', 1)[1]}.wav"
        voice_source = _read_stereo(voice_path)
        voice = np.zeros((length, 2), dtype=np.float32)
        voice_samples = min(len(voice_source), length - int(VOICE_OFFSET * SR))
        if voice_samples > 0:
            start = int(VOICE_OFFSET * SR)
            voice[start:start + voice_samples] = voice_source[:voice_samples] * 0.90
        bed = _fit(music, length, int(MUSIC_OFFSETS[slug] * SR)) * 0.095
        _fade(bed, 0.6)
        master = _voice_duck(bed, voice) + voice
        rendered_cues: list[str] = []
        for at, cue_id, gain in CUE_PLAN[slug]:
            if cue_id not in SFX_REGISTRY:
                continue
            _place(master, render_sfx(cue_id, sr=SR), at, gain)
            rendered_cues.append(cue_id)
        # Preserve transient SFX while hard-limiting safely below full scale.
        peak = float(np.max(np.abs(master))) or 1.0
        if peak > 0.92:
            master *= 0.92 / peak
        output = AUDIO / f"master_{slug}.wav"
        sf.write(output, master, SR, subtype="PCM_16")
        produced.append({"slug": slug, "audio": str(output.relative_to(ROOT)), "duration_seconds": round(len(master) / SR, 3), "voice": str(voice_path.relative_to(ROOT)), "music_source": "music_neon_tech_master.wav", "cues": rendered_cues, "ducking": "-7 dB music under narration", "narration_version": "v2.2-beat-aligned"})
    (AUDIO / "master_mix_manifest.json").write_text(json.dumps({"sample_rate": SR, "masters": produced}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"masters": produced}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
