"""16 procedurally-generated music beds.

WHY THESE ARE SYNTHESISED
-------------------------
Same reasoning as the SFX library: a bed that is a function of (bpm, key, seed)
renders identically forever, needs no licence audit, and can be retuned or
re-lengthened without sourcing a new file. A sampled loop can do none of that.

WHAT MAKES A BED USABLE UNDER SPEECH
------------------------------------
The plan states it as a measurement, not a preference: no strong content above
4 kHz competing with consonants, and no busy melodic movement in the 200 Hz -
2 kHz vocal band. Both are enforced by audit/music_probe.py rather than left to
taste. In practice that means:

  - bass and sub carry the identity (below 200 Hz, out of the way)
  - harmony sits as sustained pads, not moving lines, in the low mids
  - anything bright is transient and quiet (soft ticks, not hats with sizzle)
  - a final lowpass keeps the top end from fighting speech

LOOPING
-------
`loop_bed(name, duration)` tiles a bed and crossfades the seam. A bed whose last
sample does not join its first clicks once per repetition, which is the single
most audible failure in a background track, so the probe measures the seam
discontinuity against the largest step found inside the bed itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .synth import (
    SR,
    adsr,
    fade,
    lowpass,
    highpass,
    mix,
    noise,
    normalize,
    perc_env,
    place,
    reverb,
    saw,
    silence,
    sine,
    square,
    triangle,
)

MUSIC_PEAK = -26.0  # the plan's music level, ducking to -32 under voice


@dataclass(frozen=True)
class BedSpec:
    name: str
    fn: Callable[..., np.ndarray]
    bpm: int
    key: str
    character: str
    use: str
    peak_db: float = MUSIC_PEAK


MUSIC_REGISTRY: dict[str, BedSpec] = {}


def bed(name: str, bpm: int, key: str, character: str, use: str, peak_db: float = MUSIC_PEAK):
    def deco(fn: Callable[..., np.ndarray]) -> Callable[..., np.ndarray]:
        if name in MUSIC_REGISTRY:
            raise ValueError(f"duplicate bed name: {name}")
        MUSIC_REGISTRY[name] = BedSpec(name, fn, bpm, key, character, use, peak_db)
        return fn

    return deco


def render_bed(name: str, sr: int = SR, **params) -> np.ndarray:
    if name not in MUSIC_REGISTRY:
        raise KeyError(f"unknown bed {name!r}; {len(MUSIC_REGISTRY)} registered")
    return MUSIC_REGISTRY[name].fn(sr=sr, **params)


# --------------------------------------------------------------------------
# note helpers
# --------------------------------------------------------------------------

_NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
         "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def note_hz(name: str, octave: int = 4) -> float:
    """Midi-style note to frequency. A4 = 440."""
    semitone = _NOTE[name] + (octave - 4) * 12 - 9
    return 440.0 * (2 ** (semitone / 12))


def chord(root: str, quality: str, octave: int = 3) -> list[float]:
    """Triad frequencies. Only the qualities the beds actually use."""
    intervals = {"maj": (0, 4, 7), "min": (0, 3, 7), "sus": (0, 5, 7),
                 "maj7": (0, 4, 7, 11), "min7": (0, 3, 7, 10)}[quality]
    base = note_hz(root, octave)
    return [base * (2 ** (i / 12)) for i in intervals]


def bar_seconds(bpm: int) -> float:
    """One 4/4 bar."""
    return 4 * 60.0 / bpm


def _pad(freqs: list[float], dur: float, sr: int, gain: float = 1.0,
         detune: float = 0.004, bright: float = 0.35) -> np.ndarray:
    """Sustained chord. Two slightly detuned saws per note give it width.

    Kept deliberately dull (`bright` lowpass) — a pad with a bright top end is
    exactly what makes speech hard to follow.
    """
    out = silence(dur, sr)
    for f in freqs:
        for d in (1 - detune, 1 + detune):
            out += saw(f * d, dur, sr) * 0.5
    out = lowpass(out, 200 + bright * 1800, sr)
    env = adsr(dur, dur * 0.25, dur * 0.15, 0.8, dur * 0.3, sr)
    return out * env * (gain / max(1, len(freqs)))


def _sub(freq: float, dur: float, sr: int, gain: float = 1.0) -> np.ndarray:
    """Sine sub with a soft attack; carries weight without muddying the mids."""
    s = sine(freq, dur, sr) * adsr(dur, 0.02, 0.1, 0.75, dur * 0.25, sr)
    return s * gain


def _pluck(freq: float, dur: float, sr: int, gain: float = 1.0) -> np.ndarray:
    """Short plucked tone — triangle keeps the harmonics tame."""
    return triangle(freq, dur, sr) * perc_env(dur, sr, curve=3.2) * gain


def _kick(sr: int, gain: float = 1.0) -> np.ndarray:
    d = 0.16
    f = np.linspace(110, 45, int(d * sr))
    return sine(f, d, sr) * perc_env(d, sr, curve=4.5) * gain


def _tick(sr: int, seed: int, gain: float = 1.0) -> np.ndarray:
    """Quiet high transient. Short and low-level so it never fights consonants."""
    n = noise(0.02, sr, seed=seed) * perc_env(0.02, sr, curve=12.0)
    return highpass(n, 4000, sr) * gain


def _progression(prog: list[tuple[str, str]], bars: int, bpm: int, sr: int,
                 octave: int = 3, gain: float = 1.0, bright: float = 0.35) -> np.ndarray:
    """Lay a chord progression across `bars`, one chord per bar."""
    bs = bar_seconds(bpm)
    out = silence(bars * bs, sr)
    for i in range(bars):
        root, qual = prog[i % len(prog)]
        place(out, _pad(chord(root, qual, octave), bs, sr, gain, bright=bright), i * bs, sr)
    return out


def _bassline(prog: list[tuple[str, str]], bars: int, bpm: int, sr: int,
              octave: int = 1, gain: float = 1.0, per_bar: int = 1) -> np.ndarray:
    bs = bar_seconds(bpm)
    out = silence(bars * bs, sr)
    step = bs / per_bar
    for i in range(bars):
        root, _ = prog[i % len(prog)]
        for j in range(per_bar):
            place(out, _sub(note_hz(root, octave), step * 0.9, sr, gain), i * bs + j * step, sr)
    return out


_EDGE_FADE = True  # see raw_render(): off while tiling a loop


def _finish(sig: np.ndarray, sr: int, peak_db: float = MUSIC_PEAK,
            top: float = 4000.0) -> np.ndarray:
    """Common tail: tame the top end, fade the edges, hit the target level.

    The lowpass is the speech-fitness requirement made mechanical — every bed
    goes through it, so no bed can accidentally ship with a bright top.

    The edge fade is right for a bed played once and wrong for one that will be
    tiled: fading both ends and then crossfading the seam attenuates the same
    material twice, which digs a hole at every repetition. `raw_render()` turns
    it off for that case.
    """
    out = lowpass(sig, top, sr)
    if _EDGE_FADE:
        out = fade(out, 0.03, 0.05, sr)
    return normalize(out, peak_db)


class raw_render:
    """Render beds without their edge fades, for seamless tiling.

    A context manager rather than a parameter because every bed calls _finish()
    positionally; threading a flag through 16 signatures buys nothing.
    """

    def __enter__(self) -> None:
        global _EDGE_FADE
        self._prev = _EDGE_FADE
        _EDGE_FADE = False

    def __exit__(self, *exc: object) -> None:
        global _EDGE_FADE
        _EDGE_FADE = self._prev


# ==========================================================================
# the 16 beds
# ==========================================================================

@bed("minimal_pulse", 90, "Am", "Muted pulse, soft sub", "Default explainer bed")
def minimal_pulse(sr: int = SR, bars: int = 8, seed: int = 1) -> np.ndarray:
    bpm, prog = 90, [("A", "min"), ("F", "maj"), ("C", "maj"), ("G", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.5, bright=0.3)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.7)
    pulse = silence(bars * bs, sr)
    for i in range(bars * 4):  # quarter notes
        place(pulse, _kick(sr, 0.35), i * bs / 4, sr)
    return _finish(mix(pad, bass, pulse), sr)


@bed("warm_keys", 84, "F", "Felt piano, tape hiss", "Narrative, testimonial")
def warm_keys(sr: int = SR, bars: int = 8, seed: int = 2) -> np.ndarray:
    bpm, prog = 84, [("F", "maj7"), ("D", "min7"), ("Bb", "maj7"), ("C", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.45, bright=0.25)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.6)
    keys = silence(bars * bs, sr)
    rng = np.random.default_rng(seed)
    for i in range(bars):
        root, qual = prog[i % len(prog)]
        for j, f in enumerate(chord(root, qual, 4)):
            place(keys, _pluck(f, bs * 0.5, sr, 0.25 * rng.uniform(0.8, 1.0)),
                  i * bs + j * bs * 0.18, sr)
    hiss = noise(bars * bs, sr, seed=seed, kind="pink") * 0.02
    return _finish(mix(pad, bass, keys, hiss), sr, top=3600)


@bed("tech_drift", 100, "Cm", "Filtered saw pad, ticks", "Product / tech")
def tech_drift(sr: int = SR, bars: int = 8, seed: int = 3) -> np.ndarray:
    bpm, prog = 100, [("C", "min"), ("Ab", "maj"), ("Eb", "maj"), ("G", "min")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.5, bright=0.4)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.65, per_bar=2)
    ticks = silence(bars * bs, sr)
    for i in range(bars * 8):
        place(ticks, _tick(sr, seed + i, 0.12), i * bs / 8, sr)
    return _finish(mix(pad, bass, ticks), sr)


@bed("crypto_dark", 96, "Dm", "Deep sub, sparse blips", "Finance, risk")
def crypto_dark(sr: int = SR, bars: int = 8, seed: int = 4) -> np.ndarray:
    bpm, prog = 96, [("D", "min"), ("D", "min"), ("Bb", "maj"), ("A", "min")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=2, gain=0.45, bright=0.2)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.8)
    blips = silence(bars * bs, sr)
    rng = np.random.default_rng(seed)
    for i in range(bars * 2):
        if rng.random() < 0.45:
            f = note_hz(prog[(i // 2) % len(prog)][0], 5)
            place(blips, _pluck(f, 0.18, sr, 0.15), i * bs / 2 + rng.uniform(0, 0.2), sr)
    return _finish(mix(pad, bass, blips), sr, top=3200)


@bed("upbeat_clean", 112, "G", "Plucks, light kick", "Growth, positive stats")
def upbeat_clean(sr: int = SR, bars: int = 8, seed: int = 5) -> np.ndarray:
    bpm, prog = 112, [("G", "maj"), ("E", "min"), ("C", "maj"), ("D", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.4, bright=0.35)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.6, per_bar=2)
    plucks = silence(bars * bs, sr)
    for i in range(bars):
        root, qual = prog[i % len(prog)]
        cs = chord(root, qual, 4)
        for j in range(4):
            place(plucks, _pluck(cs[j % len(cs)], bs / 6, sr, 0.2), i * bs + j * bs / 4, sr)
    kicks = silence(bars * bs, sr)
    for i in range(bars * 2):
        place(kicks, _kick(sr, 0.4), i * bs / 2, sr)
    return _finish(mix(pad, bass, plucks, kicks), sr)


@bed("lofi_soft", 76, "Ebm", "Dusty keys, vinyl noise", "Casual, personal")
def lofi_soft(sr: int = SR, bars: int = 8, seed: int = 6) -> np.ndarray:
    bpm, prog = 76, [("Eb", "min7"), ("Ab", "min7"), ("B", "maj7"), ("Bb", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.45, bright=0.2)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.65)
    keys = silence(bars * bs, sr)
    rng = np.random.default_rng(seed)
    for i in range(bars):
        root, qual = prog[i % len(prog)]
        for j, f in enumerate(chord(root, qual, 4)):
            # swung, slightly late — a grid-perfect lofi bed sounds mechanical
            off = i * bs + j * bs * 0.14 + rng.uniform(0, 0.03)
            place(keys, _pluck(f, bs * 0.4, sr, 0.22), off, sr)
    vinyl = noise(bars * bs, sr, seed=seed, kind="pink") * 0.035
    crackle = silence(bars * bs, sr)
    for _ in range(int(bars * 6)):
        place(crackle, _tick(sr, int(rng.integers(0, 9999)), 0.05), rng.uniform(0, bars * bs), sr)
    return _finish(mix(pad, bass, keys, vinyl, crackle), sr, top=3000)


@bed("corporate_calm", 92, "Bb", "Marimba, strings pad", "Business, B2B")
def corporate_calm(sr: int = SR, bars: int = 8, seed: int = 7) -> np.ndarray:
    bpm, prog = 92, [("Bb", "maj"), ("F", "maj"), ("G", "min"), ("Eb", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.45, bright=0.3)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.6)
    marimba = silence(bars * bs, sr)
    for i in range(bars):
        root, qual = prog[i % len(prog)]
        cs = chord(root, qual, 4)
        for j in range(6):
            f = cs[j % len(cs)]
            place(marimba, sine(f, 0.22, sr) * perc_env(0.22, sr, 5.0) * 0.18,
                  i * bs + j * bs / 6, sr)
    return _finish(mix(pad, bass, marimba), sr)


@bed("neon_synth", 108, "Fm", "Retro synth arp", "Gaming, hype")
def neon_synth(sr: int = SR, bars: int = 8, seed: int = 8) -> np.ndarray:
    bpm, prog = 108, [("F", "min"), ("Db", "maj"), ("Ab", "maj"), ("Eb", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.4, bright=0.45)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.7, per_bar=4)
    arp = silence(bars * bs, sr)
    for i in range(bars):
        root, qual = prog[i % len(prog)]
        cs = chord(root, qual, 4)
        for j in range(8):
            f = cs[j % len(cs)] * (2 if j >= 4 else 1)
            place(arp, square(f, bs / 10, sr, 0.35) * perc_env(bs / 10, sr, 4.0) * 0.12,
                  i * bs + j * bs / 8, sr)
    return _finish(mix(pad, bass, arp), sr)


@bed("ambient_wide", 70, "A", "Long pads, no drums", "Intro, contemplative")
def ambient_wide(sr: int = SR, bars: int = 8, seed: int = 9) -> np.ndarray:
    bpm, prog = 70, [("A", "maj7"), ("E", "min7")]
    bs = bar_seconds(bpm)
    # two-bar chords: slower harmonic rhythm suits a contemplative bed
    out = silence(bars * bs, sr)
    for i in range(0, bars, 2):
        root, qual = prog[(i // 2) % len(prog)]
        place(out, _pad(chord(root, qual, 3), bs * 2, sr, 0.55, bright=0.2), i * bs, sr)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.5)
    air = noise(bars * bs, sr, seed=seed, kind="pink") * 0.03
    return _finish(reverb(mix(out, bass, air), amount=0.35, decay=0.6, sr=sr), sr, top=3000)


@bed("percussive_tick", 104, "Em", "Woodblocks, shaker", "Process, tutorial")
def percussive_tick(sr: int = SR, bars: int = 8, seed: int = 10) -> np.ndarray:
    bpm, prog = 104, [("E", "min"), ("C", "maj"), ("G", "maj"), ("D", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.4, bright=0.3)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.6)
    blocks = silence(bars * bs, sr)
    for i in range(bars * 4):
        place(blocks, sine(820, 0.05, sr) * perc_env(0.05, sr, 8.0) * 0.16, i * bs / 4, sr)
    shaker = silence(bars * bs, sr)
    for i in range(bars * 8):
        place(shaker, _tick(sr, seed + i, 0.1), i * bs / 8, sr)
    return _finish(mix(pad, bass, blocks, shaker), sr)


@bed("cinematic_build", 88, "Gm", "Strings rising", "Reveal, climax")
def cinematic_build(sr: int = SR, bars: int = 8, seed: int = 11) -> np.ndarray:
    bpm, prog = 88, [("G", "min"), ("Eb", "maj"), ("Bb", "maj"), ("D", "min")]
    bs = bar_seconds(bpm)
    total = bars * bs
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.5, bright=0.3)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.7)
    # a build is a level shape, not a new part: ramp the whole bed
    ramp = np.linspace(0.45, 1.0, len(pad)).astype(np.float32)
    swell = noise(total, sr, seed=seed, kind="pink") * np.linspace(0.0, 0.06, int(total * sr)).astype(np.float32)
    return _finish(mix(pad * ramp, bass * ramp, swell), sr)


@bed("glass_bells", 80, "D", "Bell tones, reverb", "Elegant, premium")
def glass_bells(sr: int = SR, bars: int = 8, seed: int = 12) -> np.ndarray:
    bpm, prog = 80, [("D", "maj7"), ("B", "min7"), ("G", "maj7"), ("A", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.4, bright=0.25)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.55)
    bells = silence(bars * bs, sr)
    for i in range(bars):
        root, qual = prog[i % len(prog)]
        for j, f in enumerate(chord(root, qual, 5)):
            # bells are the one bright element; kept sparse and quiet
            place(bells, sine(f, 0.7, sr) * perc_env(0.7, sr, 2.4) * 0.09,
                  i * bs + j * bs * 0.22, sr)
    return _finish(reverb(mix(pad, bass, bells), amount=0.3, decay=0.55, sr=sr), sr)


@bed("sub_bass_focus", 98, "Am", "Sub + hats only", "Under heavy voiceover")
def sub_bass_focus(sr: int = SR, bars: int = 8, seed: int = 13) -> np.ndarray:
    bpm, prog = 98, [("A", "min"), ("F", "maj"), ("C", "maj"), ("E", "min")]
    bs = bar_seconds(bpm)
    # deliberately no pad: this bed exists to stay out of the way entirely
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.9, per_bar=2)
    hats = silence(bars * bs, sr)
    for i in range(bars * 8):
        place(hats, _tick(sr, seed + i, 0.08), i * bs / 8, sr)
    return _finish(mix(bass, hats), sr, top=2600)


@bed("hopeful_rise", 106, "C", "Piano arp ascending", "Conclusion, CTA")
def hopeful_rise(sr: int = SR, bars: int = 8, seed: int = 14) -> np.ndarray:
    bpm, prog = 106, [("C", "maj"), ("G", "maj"), ("A", "min"), ("F", "maj")]
    bs = bar_seconds(bpm)
    pad = _progression(prog, bars, bpm, sr, octave=3, gain=0.42, bright=0.35)
    bass = _bassline(prog, bars, bpm, sr, octave=1, gain=0.6)
    arp = silence(bars * bs, sr)
    for i in range(bars):
        root, qual = prog[i % len(prog)]
        cs = chord(root, qual, 4)
        for j in range(6):
            f = cs[j % len(cs)] * (2 if j >= 3 else 1)
            place(arp, _pluck(f, bs / 8, sr, 0.16), i * bs + j * bs / 6, sr)
    return _finish(mix(pad, bass, arp), sr)


@bed("tension_hold", 94, "Bbm", "Drone, tremolo", "Problem statement")
def tension_hold(sr: int = SR, bars: int = 8, seed: int = 15) -> np.ndarray:
    bpm = 94
    bs = bar_seconds(bpm)
    total = bars * bs
    n = int(total * sr)
    # a held minor drone with a tremolo — no progression, that is the point
    root = note_hz("Bb", 2)
    drone = (sine(root, total, sr) + sine(root * 1.5, total, sr) * 0.4
             + sine(root * (2 ** (3 / 12)), total, sr) * 0.35)
    trem = (0.8 + 0.2 * np.sin(2 * np.pi * 4.5 * np.arange(n) / sr)).astype(np.float32)
    sub = _sub(note_hz("Bb", 1), total, sr, 0.7)
    return _finish(mix(drone * trem * 0.4, sub), sr, top=2400)


@bed("silence_bed", 60, "-", "Room tone only", "When music would intrude", peak_db=-50.0)
def silence_bed(sr: int = SR, bars: int = 8, seed: int = 16) -> np.ndarray:
    """Not silence — room tone. Absolute digital silence under a cut reads as a
    dropout; a whisper of air does not."""
    total = bars * bar_seconds(60)
    return _finish(noise(total, sr, seed=seed, kind="brown") * 0.1, sr, peak_db=-50.0, top=1200)


# --------------------------------------------------------------------------
# looping
# --------------------------------------------------------------------------

def loop_bed(name: str, duration: float, sr: int = SR, crossfade: float = 0.9,
             **params) -> np.ndarray:
    """Tile a bed to `duration` seconds, overlapping each seam.

    The overlap is long (0.9 s by default) for a specific reason. Every pad note
    has an ADSR release of ~0.3 of a bar, so the final bar of a bed decays to
    near-silence — measured at -67 dBFS in the last 100 ms — simply because no
    bar follows it. A short crossfade splices two copies at exactly the point
    where one has faded out, digging an 11 dB hole once per repetition.

    Overlapping by at least the release length lets the decaying tail sum with
    the next copy's attack, which is what the tail would have overlapped had the
    bed continued. Equal-power (sqrt) curves keep the sum level: linear ones dip
    at the midpoint, which on a repeating bed is an audible pulse per loop.
    """
    with raw_render():
        one = render_bed(name, sr=sr, **params)

    n_total = int(duration * sr)
    if len(one) >= n_total:
        return _tail_fade(one[:n_total], sr)

    cf = max(1, min(int(crossfade * sr), len(one) // 3))
    stride = len(one) - cf  # each copy starts one overlap before the last ends
    fade_in = np.sqrt(np.linspace(0, 1, cf, dtype=np.float32))
    fade_out = np.sqrt(np.linspace(1, 0, cf, dtype=np.float32))

    out = np.zeros(n_total + len(one), dtype=np.float32)
    pos = 0
    while pos < n_total:
        seg = one.copy()
        if pos > 0:
            seg[:cf] *= fade_in
            out[pos : pos + cf] *= fade_out
        out[pos : pos + len(seg)] += seg
        pos += stride

    return _tail_fade(out[:n_total], sr)


def _tail_fade(sig: np.ndarray, sr: int) -> np.ndarray:
    return fade(sig, 0.02, 0.05, sr)


BED_NAMES = sorted(MUSIC_REGISTRY)
