"""Synthesis primitives — the building blocks every SFX and music bed uses.

WHY SYNTHESISE
--------------
The alternative is a sample library, which costs a per-file licence audit across
112 files, makes renders depend on assets that may move or change, and pins each
sound to one pitch and length. A synthesised sound is a function: the same call
gives the same samples forever, and a caller can ask for the same click 20%
brighter or 50 ms shorter without sourcing a new file.

DESIGN
------
Everything returns mono float32 in [-1, 1] at a given sample rate. Stereo,
mixing, and loudness are handled downstream by the mixer, so these stay small
and composable. Functions are pure and take an explicit `seed` wherever noise is
involved, because a render that cannot be reproduced cannot be regression-tested.

The vocabulary is deliberately small: oscillators, noise, envelopes, filters,
and a few shaping helpers. Every one of the 112 effects is a recipe over these.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import signal

SR = 48_000  # matches the mastering chain's aresample target


# --------------------------------------------------------------------------
# oscillators
# --------------------------------------------------------------------------

def _t(n: int, sr: int) -> np.ndarray:
    return np.arange(n, dtype=np.float64) / sr


def sine(freq: float | np.ndarray, dur: float, sr: int = SR, phase: float = 0.0) -> np.ndarray:
    """Sine. `freq` may be an array of the same length for a glide."""
    n = int(dur * sr)
    t = _t(n, sr)
    if isinstance(freq, np.ndarray):
        # Integrate instantaneous frequency so a sweep stays phase-continuous;
        # naively multiplying t by a changing freq produces audible steps.
        ph = 2 * np.pi * np.cumsum(freq) / sr + phase
    else:
        ph = 2 * np.pi * freq * t + phase
    return np.sin(ph).astype(np.float32)


def saw(freq: float, dur: float, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    t = _t(n, sr)
    return (2.0 * (t * freq - np.floor(0.5 + t * freq))).astype(np.float32)


def square(freq: float, dur: float, sr: int = SR, duty: float = 0.5) -> np.ndarray:
    n = int(dur * sr)
    t = _t(n, sr)
    frac = (t * freq) % 1.0
    return np.where(frac < duty, 1.0, -1.0).astype(np.float32)


def triangle(freq: float, dur: float, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    t = _t(n, sr)
    frac = (t * freq) % 1.0
    return (4.0 * np.abs(frac - 0.5) - 1.0).astype(np.float32)


def noise(dur: float, sr: int = SR, seed: int = 0, kind: str = "white") -> np.ndarray:
    """White, pink (-3 dB/oct) or brown (-6 dB/oct) noise.

    Pink and brown matter for realism: white noise reads as hiss, while most
    physical sounds (wind, rain, room tone) have energy falling with frequency.
    """
    rng = np.random.default_rng(seed)
    n = int(dur * sr)
    w = rng.standard_normal(n).astype(np.float32)
    if kind == "white":
        out = w
    elif kind == "pink":
        # Voss-McCartney style via FFT shaping: cheap and exact enough here.
        spec = np.fft.rfft(w)
        freqs = np.fft.rfftfreq(n, 1 / sr)
        freqs[0] = freqs[1] if len(freqs) > 1 else 1.0
        spec /= np.sqrt(freqs)
        out = np.fft.irfft(spec, n).astype(np.float32)
    elif kind == "brown":
        out = np.cumsum(w).astype(np.float32)
    else:
        raise ValueError(f"unknown noise kind {kind!r}")
    peak = np.max(np.abs(out)) or 1.0
    return (out / peak).astype(np.float32)


# --------------------------------------------------------------------------
# envelopes
# --------------------------------------------------------------------------

def adsr(
    dur: float,
    attack: float = 0.005,
    decay: float = 0.05,
    sustain: float = 0.6,
    release: float = 0.1,
    sr: int = SR,
) -> np.ndarray:
    """Classic ADSR. Times in seconds; sustain is a level, not a time."""
    n = int(dur * sr)
    a, d, r = int(attack * sr), int(decay * sr), int(release * sr)
    s = max(0, n - a - d - r)
    env = np.concatenate([
        np.linspace(0.0, 1.0, a, endpoint=False) if a else np.empty(0),
        np.linspace(1.0, sustain, d, endpoint=False) if d else np.empty(0),
        np.full(s, sustain),
        np.linspace(sustain, 0.0, r) if r else np.empty(0),
    ])
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return env[:n].astype(np.float32)


def perc_env(dur: float, sr: int = SR, curve: float = 4.0) -> np.ndarray:
    """Percussive envelope: instant attack, exponential decay.

    `curve` controls how fast it dies; 4 is a click, 1.5 is a soft mallet.
    """
    n = int(dur * sr)
    x = np.linspace(0.0, 1.0, n)
    return np.exp(-curve * x * 5.0).astype(np.float32)


def fade(sig: np.ndarray, fade_in: float = 0.005, fade_out: float = 0.01, sr: int = SR) -> np.ndarray:
    """Apply short fades. Prevents the click a hard start/stop always produces."""
    out = sig.copy()
    fi, fo = int(fade_in * sr), int(fade_out * sr)
    if fi > 0:
        out[:fi] *= np.linspace(0.0, 1.0, fi)
    if fo > 0:
        out[-fo:] *= np.linspace(1.0, 0.0, fo)
    return out


# --------------------------------------------------------------------------
# filters
# --------------------------------------------------------------------------

def _biquad(sig: np.ndarray, b: tuple, a: tuple) -> np.ndarray:
    """Apply a biquad via scipy's lfilter.

    This was a hand-written per-sample Python loop, which is ~1000x slower and
    made filtering 112 sounds impractical. lfilter is the same difference
    equation, vectorised in C.
    """
    b0, b1, b2 = b
    a1, a2 = a
    return signal.lfilter([b0, b1, b2], [1.0, a1, a2], sig).astype(np.float32)


def lowpass(sig: np.ndarray, cutoff: float, sr: int = SR, q: float = 0.707) -> np.ndarray:
    w0 = 2 * math.pi * cutoff / sr
    alpha = math.sin(w0) / (2 * q)
    cos_w0 = math.cos(w0)
    a0 = 1 + alpha
    b = ((1 - cos_w0) / 2 / a0, (1 - cos_w0) / a0, (1 - cos_w0) / 2 / a0)
    a = (-2 * cos_w0 / a0, (1 - alpha) / a0)
    return _biquad(sig, b, a)


def highpass(sig: np.ndarray, cutoff: float, sr: int = SR, q: float = 0.707) -> np.ndarray:
    w0 = 2 * math.pi * cutoff / sr
    alpha = math.sin(w0) / (2 * q)
    cos_w0 = math.cos(w0)
    a0 = 1 + alpha
    b = ((1 + cos_w0) / 2 / a0, -(1 + cos_w0) / a0, (1 + cos_w0) / 2 / a0)
    a = (-2 * cos_w0 / a0, (1 - alpha) / a0)
    return _biquad(sig, b, a)


def bandpass(sig: np.ndarray, centre: float, sr: int = SR, q: float = 2.0) -> np.ndarray:
    w0 = 2 * math.pi * centre / sr
    alpha = math.sin(w0) / (2 * q)
    cos_w0 = math.cos(w0)
    a0 = 1 + alpha
    b = (alpha / a0, 0.0, -alpha / a0)
    a = (-2 * cos_w0 / a0, (1 - alpha) / a0)
    return _biquad(sig, b, a)


# --------------------------------------------------------------------------
# shaping / space
# --------------------------------------------------------------------------

def reverb(sig: np.ndarray, amount: float = 0.3, decay: float = 0.4, sr: int = SR) -> np.ndarray:
    """Schroeder reverb: parallel comb filters into series allpasses.

    The earlier version rescaled the whole signal by `(1 - amount)` inside the
    loop for each of four delays, so each pass shrank the previous pass's tail.
    Measured result: a tail at -132 dBFS with an RT40 of 12 ms — arithmetically
    present, inaudible in practice. Combs now run in parallel and are summed
    once, which is what actually sustains a tail.

    Still not a convolution reverb, and does not need to be: the job is to stop
    a dry synthesised blip from sounding pasted on top of the picture.
    """
    if amount <= 0:
        return sig.astype(np.float32)

    x = sig.astype(np.float32)
    decay = float(np.clip(decay, 0.0, 0.95))

    # Mutually prime delays avoid the metallic ring that comes from common
    # factors reinforcing the same frequencies.
    comb_ms = (29.7, 37.1, 41.1, 43.7)
    wet = np.zeros(len(x), dtype=np.float32)

    for ms in comb_ms:
        d = max(1, int(sr * ms / 1000))
        if d >= len(x):
            continue
        # y[n] = x[n] + g*y[n-d], as an IIR with a length-d feedback.
        a = np.zeros(d + 1, dtype=np.float64)
        a[0] = 1.0
        a[d] = -(0.75 + 0.2 * decay)
        wet += signal.lfilter([1.0], a, x).astype(np.float32)

    wet /= len(comb_ms)

    # Allpasses smear the comb output so it reads as diffuse rather than echoed.
    for ms, g in ((5.0, 0.7), (1.7, 0.7)):
        d = max(1, int(sr * ms / 1000))
        if d >= len(wet):
            continue
        b = np.zeros(d + 1, dtype=np.float64)
        b[0] = -g
        b[d] = 1.0
        a = np.zeros(d + 1, dtype=np.float64)
        a[0] = 1.0
        a[d] = -g
        wet = signal.lfilter(b, a, wet).astype(np.float32)

    out = x * (1.0 - amount) + wet * amount
    peak = float(np.max(np.abs(out)))
    if peak > 1.0:
        out = out / peak
    return out.astype(np.float32)


def pitch_sweep(f0: float, f1: float, dur: float, sr: int = SR, curve: str = "exp") -> np.ndarray:
    """Frequency array for a glide, for feeding into `sine`."""
    n = int(dur * sr)
    x = np.linspace(0.0, 1.0, n)
    if curve == "exp":
        return (f0 * (f1 / f0) ** x).astype(np.float64)
    return (f0 + (f1 - f0) * x).astype(np.float64)


def normalize(sig: np.ndarray, peak_db: float = -1.0) -> np.ndarray:
    """Scale so the loudest sample sits at `peak_db` dBFS."""
    peak = float(np.max(np.abs(sig)))
    if peak < 1e-9:
        return sig
    target = 10 ** (peak_db / 20)
    return (sig * (target / peak)).astype(np.float32)


def mix(*signals: np.ndarray, gains: list[float] | None = None) -> np.ndarray:
    """Sum signals of differing lengths, zero-padding to the longest."""
    if not signals:
        return np.zeros(0, dtype=np.float32)
    n = max(len(s) for s in signals)
    out = np.zeros(n, dtype=np.float32)
    for i, s in enumerate(signals):
        g = gains[i] if gains else 1.0
        out[: len(s)] += s * g
    return out


def concat(*signals: np.ndarray) -> np.ndarray:
    return np.concatenate(signals).astype(np.float32)


def silence(dur: float, sr: int = SR) -> np.ndarray:
    return np.zeros(int(dur * sr), dtype=np.float32)


@dataclass(frozen=True)
class Sound:
    """A rendered sound with the metadata the mixer needs."""
    name: str
    samples: np.ndarray
    sr: int = SR

    @property
    def duration(self) -> float:
        return len(self.samples) / self.sr

    def peak_db(self) -> float:
        peak = float(np.max(np.abs(self.samples)))
        return -120.0 if peak < 1e-9 else 20 * math.log10(peak)

    def rms_db(self) -> float:
        rms = float(np.sqrt(np.mean(self.samples.astype(np.float64) ** 2)))
        return -120.0 if rms < 1e-9 else 20 * math.log10(rms)
