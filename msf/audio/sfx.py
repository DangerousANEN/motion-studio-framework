"""112 synthesised sound effects, addressable by name.

CONTRACT
--------
Every effect is `(sr: int, **params) -> np.ndarray` returning mono float32.
Effects are registered by name in `SFX_REGISTRY` via the `@sfx` decorator, so a
scene refers to a sound as `"coin_stack"` and never imports the function. That
indirection is what lets a spec file, a JSON scene, or a CLI flag name a sound.

Each registration declares `max_ms`. The audit asserts the rendered length stays
within it, because a sound that overruns its budget bleeds into the next scene's
audio — the most common way a mix turns to mud.

Levels follow the plan: UI and general effects peak at -18 dBFS, transition
whooshes at -20 dBFS. Normalising per effect at author time means the mixer
receives predictable material and does not have to guess.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .synth import (
    SR,
    adsr,
    bandpass,
    concat,
    fade,
    highpass,
    lowpass,
    mix,
    noise,
    normalize,
    perc_env,
    pitch_sweep,
    reverb,
    silence,
    sine,
    square,
    saw,
    triangle,
)

PEAK_UI = -18.0
PEAK_TRANSITION = -20.0


@dataclass(frozen=True)
class SfxSpec:
    name: str
    fn: Callable[..., np.ndarray]
    family: str
    max_ms: float
    summary: str
    loop: bool = False
    # Target peak in dBFS. Declared per effect because ambience beds sit far
    # below foreground hits on purpose; a single global "is it audible" floor
    # cannot tell a deliberately quiet bed from a broken silent one.
    peak_db: float = PEAK_UI


SFX_REGISTRY: dict[str, SfxSpec] = {}


def sfx(name: str, family: str, max_ms: float, summary: str, loop: bool = False,
        peak_db: float = PEAK_UI):
    """Register a sound effect under `name`."""

    def deco(fn: Callable[..., np.ndarray]) -> Callable[..., np.ndarray]:
        if name in SFX_REGISTRY:
            raise ValueError(f"duplicate sfx name: {name}")
        SFX_REGISTRY[name] = SfxSpec(name, fn, family, max_ms, summary, loop, peak_db)
        return fn

    return deco


def render(name: str, sr: int = SR, **params) -> np.ndarray:
    """Render a registered effect by name."""
    if name not in SFX_REGISTRY:
        raise KeyError(f"unknown sfx {name!r}; {len(SFX_REGISTRY)} registered")
    return SFX_REGISTRY[name].fn(sr, **params)


# ==========================================================================
# 3.1  UI / interaction (20)
# ==========================================================================

@sfx("click_soft", "ui", 40, "Muted UI click, low-passed transient")
def click_soft(sr: int = SR) -> np.ndarray:
    n = noise(0.035, sr, seed=11) * perc_env(0.035, sr, curve=8.0)
    body = sine(1800, 0.035, sr) * perc_env(0.035, sr, curve=9.0) * 0.4
    return normalize(fade(lowpass(mix(n, body), 3500, sr), 0.001, 0.004, sr), PEAK_UI)


@sfx("click_hard", "ui", 60, "Sharp mechanical click with high transient")
def click_hard(sr: int = SR) -> np.ndarray:
    n = noise(0.05, sr, seed=12) * perc_env(0.05, sr, curve=7.0)
    tick = sine(3200, 0.05, sr) * perc_env(0.05, sr, curve=10.0) * 0.6
    return normalize(fade(highpass(mix(n, tick), 900, sr), 0.0005, 0.006, sr), PEAK_UI)


@sfx("tap_bubble", "ui", 80, "Soft bubble tap, pitch rising")
def tap_bubble(sr: int = SR) -> np.ndarray:
    f = pitch_sweep(420, 900, 0.07, sr)
    s = sine(f, 0.07, sr) * perc_env(0.07, sr, curve=4.0)
    return normalize(fade(s, 0.002, 0.02, sr), PEAK_UI)


@sfx("toggle_on", "ui", 90, "Switch on: two-tone rising")
def toggle_on(sr: int = SR) -> np.ndarray:
    a = sine(660, 0.03, sr) * perc_env(0.03, sr, curve=6.0)
    b = sine(990, 0.055, sr) * perc_env(0.055, sr, curve=5.0)
    return normalize(fade(concat(a, b), 0.001, 0.012, sr), PEAK_UI)


@sfx("toggle_off", "ui", 90, "Switch off: two-tone falling")
def toggle_off(sr: int = SR) -> np.ndarray:
    a = sine(880, 0.03, sr) * perc_env(0.03, sr, curve=6.0)
    b = sine(520, 0.055, sr) * perc_env(0.055, sr, curve=5.0)
    return normalize(fade(concat(a, b), 0.001, 0.012, sr), PEAK_UI)


@sfx("hover_tick", "ui", 30, "Tiny hover tick, barely there", peak_db=-24)
def hover_tick(sr: int = SR) -> np.ndarray:
    s = sine(2600, 0.022, sr) * perc_env(0.022, sr, curve=12.0)
    return normalize(fade(s, 0.0005, 0.004, sr), PEAK_UI - 6)


@sfx("keypress", "ui", 25, "Single keyboard keypress")
def keypress(sr: int = SR, seed: int = 21) -> np.ndarray:
    n = noise(0.02, sr, seed=seed) * perc_env(0.02, sr, curve=11.0)
    return normalize(fade(bandpass(n, 2200, sr, q=1.2), 0.0004, 0.003, sr), PEAK_UI)


@sfx("keyboard_run", "ui", 600, "Burst of typing, irregular rhythm")
def keyboard_run(sr: int = SR, keys: int = 9, seed: int = 22) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.6, sr)
    for i in range(keys):
        # Irregular spacing: evenly spaced keys read as a machine, not a person.
        pos = int((0.02 + i * 0.062 + rng.uniform(-0.012, 0.012)) * sr)
        k = keypress(sr, seed=seed + i)
        if pos + len(k) < len(out):
            out[pos : pos + len(k)] += k * rng.uniform(0.7, 1.0)
    return normalize(out, PEAK_UI)


@sfx("send_swoosh", "ui", 220, "Message sent: airy upward swoosh")
def send_swoosh(sr: int = SR) -> np.ndarray:
    n = noise(0.2, sr, seed=23, kind="pink")
    env = adsr(0.2, 0.02, 0.05, 0.5, 0.12, sr)
    swept = bandpass(n * env, 1400, sr, q=0.8)
    tone = sine(pitch_sweep(500, 1500, 0.2, sr), 0.2, sr) * env * 0.25
    return normalize(fade(mix(swept, tone), 0.005, 0.04, sr), PEAK_UI)


@sfx("receive_pop", "ui", 140, "Message received: soft pop")
def receive_pop(sr: int = SR) -> np.ndarray:
    f = pitch_sweep(300, 720, 0.12, sr)
    s = sine(f, 0.12, sr) * perc_env(0.12, sr, curve=3.5)
    return normalize(fade(reverb(s, amount=0.15, decay=0.3, sr=sr), 0.002, 0.03, sr), PEAK_UI)


@sfx("notify_ding", "ui", 400, "Single notification bell")
def notify_ding(sr: int = SR) -> np.ndarray:
    partials = mix(
        sine(1318, 0.35, sr) * perc_env(0.35, sr, curve=3.0),
        sine(1975, 0.35, sr) * perc_env(0.35, sr, curve=4.5) * 0.4,
        sine(2637, 0.35, sr) * perc_env(0.35, sr, curve=6.0) * 0.2,
    )
    return normalize(fade(reverb(partials, amount=0.25, decay=0.4, sr=sr), 0.002, 0.06, sr), PEAK_UI)


@sfx("notify_double", "ui", 500, "Two-tone notification")
def notify_double(sr: int = SR) -> np.ndarray:
    d1 = notify_ding(sr)[: int(0.18 * sr)]
    gap = silence(0.02, sr)
    d2 = mix(
        sine(1567, 0.28, sr) * perc_env(0.28, sr, curve=3.0),
        sine(2350, 0.28, sr) * perc_env(0.28, sr, curve=4.5) * 0.4,
    )
    return normalize(fade(concat(d1, gap, reverb(d2, 0.25, 0.4, sr)), 0.002, 0.06, sr), PEAK_UI)


@sfx("error_buzz", "ui", 260, "Error: low square buzz")
def error_buzz(sr: int = SR) -> np.ndarray:
    b = square(150, 0.22, sr, duty=0.35) * adsr(0.22, 0.004, 0.03, 0.7, 0.08, sr)
    sub = sine(75, 0.22, sr) * adsr(0.22, 0.004, 0.03, 0.7, 0.08, sr) * 0.5
    return normalize(fade(lowpass(mix(b, sub), 2200, sr), 0.002, 0.03, sr), PEAK_UI)


@sfx("success_chime", "ui", 600, "Success: rising major triad")
def success_chime(sr: int = SR) -> np.ndarray:
    notes = [(523, 0.0), (659, 0.07), (784, 0.14)]
    out = silence(0.55, sr)
    for freq, off in notes:
        tone = mix(
            sine(freq, 0.4, sr) * perc_env(0.4, sr, curve=2.8),
            sine(freq * 2, 0.4, sr) * perc_env(0.4, sr, curve=4.0) * 0.3,
        )
        pos = int(off * sr)
        seg = tone[: len(out) - pos]
        out[pos : pos + len(seg)] += seg
    return normalize(fade(reverb(out, 0.3, 0.45, sr), 0.003, 0.08, sr), PEAK_UI)


@sfx("unlock_click", "ui", 180, "Lock disengaging: click plus small thunk")
def unlock_click(sr: int = SR) -> np.ndarray:
    c = click_hard(sr)
    thunk = sine(180, 0.12, sr) * perc_env(0.12, sr, curve=5.0) * 0.7
    return normalize(fade(concat(c, thunk), 0.001, 0.02, sr), PEAK_UI)


@sfx("scroll_tick", "ui", 20, "Scroll detent tick", peak_db=-26)
def scroll_tick(sr: int = SR, seed: int = 24) -> np.ndarray:
    n = noise(0.015, sr, seed=seed) * perc_env(0.015, sr, curve=14.0)
    return normalize(fade(highpass(n, 2000, sr), 0.0003, 0.002, sr), PEAK_UI - 8)


@sfx("swipe_soft", "ui", 200, "Finger swipe across glass", peak_db=-21)
def swipe_soft(sr: int = SR) -> np.ndarray:
    n = noise(0.18, sr, seed=25, kind="pink")
    env = adsr(0.18, 0.03, 0.04, 0.55, 0.09, sr)
    return normalize(fade(bandpass(n * env, 2400, sr, q=0.7), 0.006, 0.05, sr), PEAK_UI - 3)


@sfx("focus_ring", "ui", 120, "Focus outline appears: soft blip", peak_db=-23)
def focus_ring(sr: int = SR) -> np.ndarray:
    s = sine(1200, 0.1, sr) * adsr(0.1, 0.008, 0.02, 0.5, 0.06, sr)
    return normalize(fade(s, 0.002, 0.02, sr), PEAK_UI - 5)


@sfx("dropdown_open", "ui", 160, "Menu opening: short upward glide", peak_db=-20)
def dropdown_open(sr: int = SR) -> np.ndarray:
    f = pitch_sweep(600, 1050, 0.14, sr)
    s = sine(f, 0.14, sr) * adsr(0.14, 0.006, 0.03, 0.45, 0.08, sr)
    n = noise(0.14, sr, seed=26, kind="pink") * adsr(0.14, 0.01, 0.03, 0.3, 0.08, sr) * 0.3
    return normalize(fade(mix(s, n), 0.002, 0.03, sr), PEAK_UI - 2)


@sfx("modal_in", "ui", 240, "Modal sliding in: whoosh with soft landing")
def modal_in(sr: int = SR) -> np.ndarray:
    n = noise(0.2, sr, seed=27, kind="pink") * adsr(0.2, 0.03, 0.06, 0.4, 0.1, sr)
    land = sine(320, 0.08, sr) * perc_env(0.08, sr, curve=6.0) * 0.5
    body = lowpass(n, 2600, sr)
    out = mix(body, np.pad(land, (int(0.14 * sr), 0)))
    return normalize(fade(out, 0.006, 0.05, sr), PEAK_UI)


# ==========================================================================
# 3.2  Money / finance (18)
# ==========================================================================

@sfx("coin_single", "money", 300, "One coin: bright metallic ring")
def coin_single(sr: int = SR, seed: int = 31) -> np.ndarray:
    # Inharmonic partials are what make metal read as metal rather than as a bell.
    partials = [(2400, 1.0), (3170, 0.6), (4310, 0.35), (5600, 0.2)]
    out = silence(0.26, sr)
    for f, g in partials:
        out += sine(f, 0.26, sr) * perc_env(0.26, sr, curve=5.5) * g
    strike = noise(0.02, sr, seed=seed) * perc_env(0.02, sr, curve=12.0) * 0.5
    return normalize(fade(reverb(mix(out, strike), 0.2, 0.35, sr), 0.001, 0.05, sr), PEAK_UI)


@sfx("coin_stack", "money", 700, "Several coins falling together")
def coin_stack(sr: int = SR, count: int = 6, seed: int = 32) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.68, sr)
    for i in range(count):
        pos = int(rng.uniform(0.0, 0.34) * sr)
        c = coin_single(sr, seed=seed + i * 7)
        # Detune each coin; identical copies sum into one loud coin, not a pile.
        stretch = rng.uniform(0.88, 1.14)
        idx = np.clip((np.arange(len(c)) / stretch).astype(int), 0, len(c) - 1)
        c = c[idx] * rng.uniform(0.55, 1.0)
        if pos + len(c) < len(out):
            out[pos : pos + len(c)] += c
    return normalize(out, PEAK_UI)


@sfx("cash_register", "money", 800, "Till: mechanical clack then bell then drawer")
def cash_register(sr: int = SR) -> np.ndarray:
    clack = noise(0.05, sr, seed=33) * perc_env(0.05, sr, curve=9.0)
    clack = bandpass(clack, 1200, sr, q=0.9)
    bell = mix(
        sine(1050, 0.4, sr) * perc_env(0.4, sr, curve=3.2),
        sine(1580, 0.4, sr) * perc_env(0.4, sr, curve=4.5) * 0.45,
    )
    drawer = lowpass(noise(0.25, sr, seed=34, kind="pink"), 1600, sr) * adsr(0.25, 0.02, 0.08, 0.4, 0.12, sr)
    out = mix(clack, np.pad(bell, (int(0.06 * sr), 0)), np.pad(drawer, (int(0.35 * sr), 0)))
    return normalize(fade(reverb(out, 0.18, 0.35, sr), 0.001, 0.06, sr), PEAK_UI)


@sfx("card_tap", "money", 200, "Contactless tap: plastic click plus confirm beep")
def card_tap(sr: int = SR) -> np.ndarray:
    tap = noise(0.03, sr, seed=35) * perc_env(0.03, sr, curve=10.0)
    tap = lowpass(tap, 4000, sr)
    beep = sine(2100, 0.09, sr) * adsr(0.09, 0.004, 0.02, 0.7, 0.04, sr) * 0.6
    return normalize(fade(mix(tap, np.pad(beep, (int(0.06 * sr), 0))), 0.001, 0.02, sr), PEAK_UI)


@sfx("card_swipe", "money", 350, "Magstripe swipe: friction then click")
def card_swipe(sr: int = SR) -> np.ndarray:
    fric = noise(0.24, sr, seed=36, kind="pink") * adsr(0.24, 0.04, 0.06, 0.6, 0.1, sr)
    fric = bandpass(fric, 1800, sr, q=0.6)
    clk = click_hard(sr) * 0.8
    return normalize(fade(mix(fric, np.pad(clk, (int(0.24 * sr), 0))), 0.008, 0.03, sr), PEAK_UI)


@sfx("atm_dispense", "money", 900, "Note counter whirring then notes pushed out")
def atm_dispense(sr: int = SR) -> np.ndarray:
    # Motor: a buzzy low tone amplitude-modulated by the roller rate.
    motor = saw(88, 0.6, sr) * adsr(0.6, 0.05, 0.1, 0.75, 0.15, sr)
    am = 0.7 + 0.3 * np.sin(2 * np.pi * 26 * np.arange(len(motor)) / sr)
    motor = lowpass(motor * am, 900, sr) * 0.5
    riffle = silence(0.85, sr)
    rng = np.random.default_rng(37)
    for i in range(7):
        pos = int((0.08 + i * 0.075) * sr)
        p = noise(0.04, sr, seed=40 + i, kind="pink") * perc_env(0.04, sr, curve=8.0)
        p = bandpass(p, 2600, sr, q=0.8) * rng.uniform(0.6, 1.0)
        riffle[pos : pos + len(p)] += p
    return normalize(fade(mix(motor, riffle), 0.02, 0.08, sr), PEAK_UI)


@sfx("transfer_send", "money", 500, "Funds leaving: upward whoosh with data chirp")
def transfer_send(sr: int = SR) -> np.ndarray:
    n = noise(0.4, sr, seed=38, kind="pink") * adsr(0.4, 0.05, 0.1, 0.5, 0.2, sr)
    swept = bandpass(n, 1600, sr, q=0.7)
    chirp = sine(pitch_sweep(400, 2200, 0.4, sr), 0.4, sr) * adsr(0.4, 0.03, 0.1, 0.35, 0.2, sr) * 0.3
    return normalize(fade(mix(swept, chirp), 0.01, 0.09, sr), PEAK_UI)


@sfx("transfer_receive", "money", 500, "Funds arriving: downward whoosh settling")
def transfer_receive(sr: int = SR) -> np.ndarray:
    n = noise(0.4, sr, seed=39, kind="pink") * adsr(0.4, 0.04, 0.1, 0.5, 0.2, sr)
    swept = bandpass(n, 1400, sr, q=0.7)
    chirp = sine(pitch_sweep(1800, 500, 0.4, sr), 0.4, sr) * adsr(0.4, 0.03, 0.1, 0.4, 0.2, sr) * 0.35
    settle = sine(260, 0.15, sr) * perc_env(0.15, sr, curve=4.0) * 0.4
    return normalize(fade(mix(swept, chirp, np.pad(settle, (int(0.3 * sr), 0))), 0.01, 0.09, sr), PEAK_UI)


@sfx("payment_ok", "money", 700, "Payment approved: warm two-note confirm")
def payment_ok(sr: int = SR) -> np.ndarray:
    a = mix(sine(784, 0.25, sr) * perc_env(0.25, sr, 3.0), sine(1568, 0.25, sr) * perc_env(0.25, sr, 4.5) * 0.3)
    b = mix(sine(1046, 0.45, sr) * perc_env(0.45, sr, 2.6), sine(2093, 0.45, sr) * perc_env(0.45, sr, 4.0) * 0.3)
    out = mix(a, np.pad(b, (int(0.16 * sr), 0)))
    return normalize(fade(reverb(out, 0.28, 0.4, sr), 0.003, 0.08, sr), PEAK_UI)


@sfx("payment_fail", "money", 600, "Payment declined: two falling minor tones")
def payment_fail(sr: int = SR) -> np.ndarray:
    a = square(440, 0.18, sr, 0.4) * adsr(0.18, 0.006, 0.04, 0.6, 0.07, sr)
    b = square(311, 0.32, sr, 0.4) * adsr(0.32, 0.006, 0.06, 0.55, 0.12, sr)
    out = concat(a, b)
    return normalize(fade(lowpass(out, 2400, sr), 0.003, 0.05, sr), PEAK_UI)


@sfx("balance_up", "money", 400, "Balance increasing: bright rising arp")
def balance_up(sr: int = SR) -> np.ndarray:
    out = silence(0.36, sr)
    for i, f in enumerate((659, 880, 1174)):
        pos = int(i * 0.055 * sr)
        t = sine(f, 0.22, sr) * perc_env(0.22, sr, curve=4.0)
        seg = t[: len(out) - pos]
        out[pos : pos + len(seg)] += seg
    return normalize(fade(reverb(out, 0.2, 0.35, sr), 0.002, 0.05, sr), PEAK_UI)


@sfx("balance_down", "money", 400, "Balance decreasing: falling arp")
def balance_down(sr: int = SR) -> np.ndarray:
    out = silence(0.36, sr)
    for i, f in enumerate((880, 659, 494)):
        pos = int(i * 0.055 * sr)
        t = sine(f, 0.22, sr) * perc_env(0.22, sr, curve=4.0)
        seg = t[: len(out) - pos]
        out[pos : pos + len(seg)] += seg
    return normalize(fade(reverb(out, 0.2, 0.35, sr), 0.002, 0.05, sr), PEAK_UI)


@sfx("counter_tick", "money", 30, "Single digit-roll tick", peak_db=-24)
def counter_tick(sr: int = SR, seed: int = 41) -> np.ndarray:
    n = noise(0.02, sr, seed=seed) * perc_env(0.02, sr, curve=13.0)
    t = sine(2900, 0.02, sr) * perc_env(0.02, sr, curve=14.0) * 0.4
    return normalize(fade(highpass(mix(n, t), 1500, sr), 0.0003, 0.003, sr), PEAK_UI - 6)


@sfx("counter_run", "money", 1200, "Number counting up: accelerating ticks")
def counter_run(sr: int = SR, ticks: int = 22, seed: int = 42) -> np.ndarray:
    out = silence(1.15, sr)
    # Ticks slow toward the end (ease-out), matching how a counter animation
    # decelerates as it lands on its final value.
    for i in range(ticks):
        x = i / max(1, ticks - 1)
        pos = int((1.0 - (1.0 - x) ** 2.2) * 1.02 * sr)
        t = counter_tick(sr, seed=seed + i)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(out, PEAK_UI)


@sfx("stamp_hit", "money", 200, "Rubber stamp landing on paper")
def stamp_hit(sr: int = SR) -> np.ndarray:
    thud = sine(140, 0.1, sr) * perc_env(0.1, sr, curve=7.0)
    slap = noise(0.06, sr, seed=43) * perc_env(0.06, sr, curve=9.0)
    slap = bandpass(slap, 1500, sr, q=0.7)
    return normalize(fade(mix(thud, slap), 0.0008, 0.03, sr), PEAK_UI)


@sfx("receipt_print", "money", 900, "Thermal printer feeding paper", peak_db=-21)
def receipt_print(sr: int = SR) -> np.ndarray:
    n = noise(0.8, sr, seed=44, kind="pink") * adsr(0.8, 0.03, 0.1, 0.8, 0.15, sr)
    body = bandpass(n, 2800, sr, q=0.5)
    # Buzz at the print-head step rate; without it this is just hiss.
    step = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 62 * np.arange(len(body)) / sr))
    return normalize(fade(body * step * 0.8, 0.02, 0.1, sr), PEAK_UI - 3)


@sfx("vault_close", "money", 800, "Heavy vault door shutting")
def vault_close(sr: int = SR) -> np.ndarray:
    slide = lowpass(noise(0.4, sr, seed=45, kind="brown"), 400, sr) * adsr(0.4, 0.06, 0.1, 0.7, 0.15, sr)
    boom = sine(pitch_sweep(90, 55, 0.45, sr), 0.45, sr) * perc_env(0.45, sr, curve=3.0)
    clank = bandpass(noise(0.12, sr, seed=46), 900, sr, q=1.2) * perc_env(0.12, sr, curve=7.0) * 0.7
    out = mix(slide, np.pad(boom, (int(0.32 * sr), 0)), np.pad(clank, (int(0.3 * sr), 0)))
    return normalize(fade(reverb(out, 0.3, 0.5, sr), 0.02, 0.1, sr), PEAK_UI)


@sfx("bell_profit", "money", 600, "Trading-floor bell, bright and short")
def bell_profit(sr: int = SR) -> np.ndarray:
    partials = [(880, 1.0), (1760, 0.5), (2640, 0.28), (3520, 0.14)]
    out = silence(0.5, sr)
    for f, g in partials:
        out += sine(f, 0.5, sr) * perc_env(0.5, sr, curve=2.6) * g
    return normalize(fade(reverb(out, 0.32, 0.45, sr), 0.001, 0.08, sr), PEAK_UI)
