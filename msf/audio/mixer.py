"""Offline mixer: timeline assembly, voice-keyed ducking, loudness targeting.

SIGNAL FLOW (from docs/EXPANSION_PLAN.md, implemented literally)

    scene SFX ──┐
    transition ─┼─► bus ──► sidechain duck (voice-keyed) ──► master ──► -14 LUFS
    music bed ──┘              ▲
    voice ─────────────────────┘  never ducked, always the loudest element

LEVELS
    music   -26 LUFS, ducking to -32 under voice (a 6 dB duck)
    SFX     -18 dBFS peak; transition whooshes -20 dBFS
    master  -14 LUFS integrated

THE LOOK-AHEAD, AND WHY IT IS NOT OPTIONAL
A duck computed causally from voice RMS with a 120 ms attack means the first
120 ms of every sentence competes with music at full level — exactly the moment
a listener needs to catch the first consonant. The standard fix is to run the
key signal early: the envelope is computed from voice shifted forward by the
attack time, so the gain has already travelled by the time speech actually
starts. That is what `lookahead` does here, and it defaults to the attack time.

LOUDNESS
Integrated loudness is measured with an ITU-R BS.1770 K-weighting filter and
gated mean square, not estimated from peaks. `measure_lufs()` is exposed so the
probe can assert against a real number rather than an assumption.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
from scipy import signal as sps

from .music import loop_bed
from .sfx import SFX_REGISTRY
from .synth import SR, place

# Import for the registration side effect: the extra families live in a separate
# module and must be present before a Timeline can resolve their names.
from . import sfx_extra  # noqa: F401

MUSIC_LUFS = -26.0
MUSIC_DUCKED_LUFS = -32.0
MASTER_LUFS = -14.0
DUCK_DEPTH_DB = MUSIC_LUFS - MUSIC_DUCKED_LUFS  # 6 dB

# Voice is levelled on the way in rather than trusted to arrive correct.
# TTS engines, recordings and test fixtures all land at different levels, and a
# quiet voice track silently inverts the whole design: it still keys the duck,
# so the music dips, but it never rises above the bed it was supposed to lead.
# -16 LUFS sits a clear 10 LU above the music bed's -26.
VOICE_LUFS = -16.0


# --------------------------------------------------------------------------
# loudness (ITU-R BS.1770)
# --------------------------------------------------------------------------

def _k_weight(sig: np.ndarray, sr: int) -> np.ndarray:
    """K-weighting: a shelving filter plus a high-pass, per BS.1770.

    Coefficients are the standard 48 kHz ones, re-derived for other rates via
    a bilinear-style frequency warp so the probe is not silently wrong at 44.1.
    """
    # stage 1: high-frequency shelf
    f0, g_db, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = math.tan(math.pi * f0 / sr)
    vh = 10 ** (g_db / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    b = [(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0]
    a = [1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    out = sps.lfilter(b, a, sig)

    # stage 2: high-pass
    f0, q = 38.13547087602444, 0.5003270373238773
    k = math.tan(math.pi * f0 / sr)
    a0 = 1 + k / q + k * k
    b = [1.0, -2.0, 1.0]
    a = [1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    return sps.lfilter(b, a, out)


def measure_lufs(sig: np.ndarray, sr: int = SR) -> float:
    """Gated integrated loudness in LUFS."""
    if len(sig) < sr // 10:
        return -70.0
    weighted = _k_weight(sig.astype(np.float64), sr)

    block = int(0.4 * sr)
    hop = int(0.1 * sr)  # 75% overlap, per spec
    if len(weighted) < block:
        block, hop = len(weighted), max(1, len(weighted) // 4)

    powers = np.array([
        float(np.mean(weighted[i : i + block] ** 2))
        for i in range(0, max(1, len(weighted) - block + 1), hop)
    ])
    powers = powers[powers > 0]
    if not len(powers):
        return -70.0

    loud = -0.691 + 10 * np.log10(powers)

    # absolute gate, then a relative gate 10 LU below the ungated mean
    keep = loud > -70.0
    if not keep.any():
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(powers[keep])) - 10.0
    keep &= loud > rel
    if not keep.any():
        return -70.0
    return float(-0.691 + 10 * np.log10(np.mean(powers[keep])))


def normalize_lufs(sig: np.ndarray, target: float, sr: int = SR) -> np.ndarray:
    """Scale to a target integrated loudness, with a peak guard.

    A pure loudness scale can push peaks past full scale; the guard trades a
    fraction of a LU for not clipping, which is the right way round.
    """
    cur = measure_lufs(sig, sr)
    if cur <= -70.0:
        return sig.astype(np.float32)
    out = sig.astype(np.float32) * (10 ** ((target - cur) / 20))
    peak = float(np.max(np.abs(out))) if len(out) else 0.0
    if peak > 0.99:
        out = out * (0.99 / peak)
    return out.astype(np.float32)


# --------------------------------------------------------------------------
# ducking
# --------------------------------------------------------------------------

def duck_envelope(
    key: np.ndarray,
    sr: int = SR,
    depth_db: float = DUCK_DEPTH_DB,
    attack: float = 0.120,
    release: float = 0.400,
    lookahead: float | None = None,
    threshold_db: float = -45.0,
) -> np.ndarray:
    """Gain envelope (linear, <= 1) that dips while `key` is active.

    `lookahead` defaults to the attack time so the envelope is already moving
    when speech starts; see the module docstring.
    """
    if lookahead is None:
        lookahead = attack

    # Short-window RMS of the key signal.
    win = max(1, int(0.02 * sr))
    power = np.convolve(key.astype(np.float64) ** 2, np.ones(win) / win, mode="same")
    rms = np.sqrt(np.maximum(power, 1e-20))
    active = (20 * np.log10(np.maximum(rms, 1e-10))) > threshold_db

    # Shift the key earlier so the ramp completes by the time voice arrives.
    shift = int(lookahead * sr)
    if shift > 0:
        active = np.concatenate([active[shift:], np.zeros(shift, dtype=bool)])

    target = np.where(active, 10 ** (-depth_db / 20), 1.0)

    # One-pole smoothing, asymmetric: fast down, slow back up.
    a_att = math.exp(-1.0 / max(1, attack * sr))
    a_rel = math.exp(-1.0 / max(1, release * sr))
    env = np.empty_like(target)
    g = 1.0
    for i, t in enumerate(target):
        coeff = a_att if t < g else a_rel
        g = t + (g - t) * coeff
        env[i] = g
    return env.astype(np.float32)


# --------------------------------------------------------------------------
# timeline
# --------------------------------------------------------------------------

@dataclass
class Cue:
    sound: str | np.ndarray
    at: float
    gain_db: float = 0.0


@dataclass
class Timeline:
    """Assembles SFX, music and voice into a finished, mastered track."""

    sr: int = SR
    sfx_cues: list[Cue] = field(default_factory=list)
    voice_cues: list[Cue] = field(default_factory=list)
    music: list[tuple[str | np.ndarray, float, float | None]] = field(default_factory=list)

    def add_sfx(self, name: str | np.ndarray, at: float, gain_db: float = 0.0) -> "Timeline":
        if isinstance(name, str) and name not in SFX_REGISTRY:
            raise KeyError(f"unknown sfx {name!r}; {len(SFX_REGISTRY)} registered")
        self.sfx_cues.append(Cue(name, at, gain_db))
        return self

    def add_music(self, bed: str | np.ndarray, start: float = 0.0, duration: float | None = None) -> "Timeline":
        self.music.append((bed, start, duration))
        return self

    def add_voice(self, samples: np.ndarray, at: float, gain_db: float = 0.0) -> "Timeline":
        self.voice_cues.append(Cue(samples, at, gain_db))
        return self

    # -- rendering ---------------------------------------------------------

    def _render_layer(self, cues: Sequence[Cue], n: int) -> np.ndarray:
        buf = np.zeros(n, dtype=np.float32)
        for cue in cues:
            sig = SFX_REGISTRY[cue.sound].fn(self.sr) if isinstance(cue.sound, str) else cue.sound
            place(buf, np.asarray(sig, dtype=np.float32), cue.at, self.sr,
                  gain=10 ** (cue.gain_db / 20))
        return buf

    def render(self, duration: float, master_lufs: float = MASTER_LUFS) -> dict:
        """Render the timeline. Returns the mix plus the stems, for auditing.

        Stems come back because a mix is not verifiable from its output alone:
        proving the duck works means comparing the music stem's level inside and
        outside voice windows, which is impossible once everything is summed.
        """
        n = int(duration * self.sr)

        voice = self._render_layer(self.voice_cues, n)
        if voice.any():
            # Levelled here so the mix does not depend on whatever level the
            # caller's TTS or recording happened to produce.
            voice = normalize_lufs(voice, VOICE_LUFS, self.sr)
        sfx = self._render_layer(self.sfx_cues, n)

        music = np.zeros(n, dtype=np.float32)
        for bed, start, dur in self.music:
            length = dur if dur is not None else duration - start
            if length > 0:
                if isinstance(bed, str):
                    samples = loop_bed(bed, length, sr=self.sr)
                else:
                    source = np.asarray(bed, dtype=np.float32).reshape(-1)
                    wanted = max(1, int(round(length * self.sr)))
                    samples = np.tile(source, int(np.ceil(wanted / max(len(source), 1))))[:wanted] if source.size else np.zeros(wanted, dtype=np.float32)
                place(music, samples, start, self.sr)
        music = normalize_lufs(music, MUSIC_LUFS, self.sr) if music.any() else music

        env = duck_envelope(voice, self.sr) if voice.any() else np.ones(n, dtype=np.float32)
        music_ducked = music * env

        # Voice bypasses the duck entirely — it is the key, not a victim of it.
        bus = music_ducked + sfx
        mix = bus + voice
        mastered = normalize_lufs(mix, master_lufs, self.sr)

        # Same scale on the stems, so stem measurements describe the mix.
        scale = 1.0
        pre = float(np.max(np.abs(mix))) or 1.0
        post = float(np.max(np.abs(mastered))) or 1.0
        scale = post / pre

        return {
            "mix": mastered,
            "music": (music_ducked * scale).astype(np.float32),
            "music_predduck": (music * scale).astype(np.float32),
            "sfx": (sfx * scale).astype(np.float32),
            "voice": (voice * scale).astype(np.float32),
            "duck_envelope": env,
            "sr": self.sr,
        }


def write_wav(path: str, sig: np.ndarray, sr: int = SR) -> str:
    """16-bit PCM, for handing to ffmpeg or a player."""
    import wave

    pcm = np.clip(sig, -1.0, 1.0)
    data = (pcm * 32767).astype("<i2").tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data)
    return path
