"""Sound effects — crypto/tech, transitions, mechanical, ambience, stingers.

Extends msf/audio/sfx.py (UI + money). Same contract: mono float32, registered
by name via @sfx, each with a max_ms the audit enforces.

Sections mirror EXPANSION_PLAN Part 3:
  3.3 Crypto / tech (16)
  3.4 Transitions / whooshes (18)
  3.5 Mechanical / physical (16)
  3.6 Ambience / texture (14, loops)
  3.7 Musical stingers (10)
"""
from __future__ import annotations

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
    place,
    reverb,
    silence,
    sine,
    square,
    saw,
    triangle,
)
from .sfx import PEAK_TRANSITION, PEAK_UI, click_hard, sfx

# ==========================================================================
# 3.3  Crypto / tech (16)
# ==========================================================================

@sfx("tx_pending", "crypto", 400, "Transaction submitted: neutral blip")
def tx_pending(sr: int = SR) -> np.ndarray:
    blip = sine(920, 0.09, sr) * adsr(0.09, 0.004, 0.02, 0.6, 0.04, sr)
    tick = click_hard(sr) * 0.35
    out = mix(np.pad(blip, (0, 0)), np.pad(tick, (int(0.1 * sr), 0)))
    return normalize(fade(out, 0.002, 0.03, sr), PEAK_UI)


@sfx("tx_confirm", "crypto", 600, "Transaction confirmed: solid double chord")
def tx_confirm(sr: int = SR) -> np.ndarray:
    a = mix(sine(659, 0.22, sr) * perc_env(0.22, sr, 3.2), sine(987, 0.22, sr) * perc_env(0.22, sr, 4.2) * 0.4)
    b = mix(sine(880, 0.35, sr) * perc_env(0.35, sr, 2.6), sine(1318, 0.35, sr) * perc_env(0.35, sr, 3.8) * 0.35)
    out = mix(a, np.pad(b, (int(0.14 * sr), 0)))
    return normalize(fade(reverb(out, 0.25, 0.4, sr), 0.003, 0.06, sr), PEAK_UI)


@sfx("block_mined", "crypto", 700, "New block: deep thud with rising shimmer")
def block_mined(sr: int = SR) -> np.ndarray:
    thud = sine(pitch_sweep(120, 70, 0.3, sr), 0.3, sr) * perc_env(0.3, sr, 3.0)
    shimmer = mix(
        sine(1567, 0.4, sr) * perc_env(0.4, sr, 2.8),
        sine(2349, 0.4, sr) * perc_env(0.4, sr, 3.8) * 0.4,
        sine(3136, 0.4, sr) * perc_env(0.4, sr, 4.8) * 0.2,
    )
    out = mix(thud, np.pad(shimmer, (int(0.22 * sr), 0)))
    return normalize(fade(reverb(out, 0.3, 0.45, sr), 0.003, 0.09, sr), PEAK_UI)


@sfx("hash_pulse", "crypto", 150, "Hash being computed: low pulse", peak_db=-20)
def hash_pulse(sr: int = SR) -> np.ndarray:
    p = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 11 * np.arange(int(0.13 * sr)) / sr))
    b = square(130, 0.13, sr, 0.4) * adsr(0.13, 0.005, 0.02, 0.6, 0.05, sr) * p * 0.5
    return normalize(fade(lowpass(b, 1800, sr), 0.002, 0.02, sr), PEAK_UI - 2)


@sfx("wallet_open", "crypto", 350, "Wallet unlocks: soft chime and latch")
def wallet_open(sr: int = SR) -> np.ndarray:
    latch = click_hard(sr) * 0.5
    chime = mix(sine(1046, 0.2, sr) * perc_env(0.2, sr, 3.4), sine(1568, 0.2, sr) * perc_env(0.2, sr, 4.4) * 0.4)
    out = mix(np.pad(latch, (0, 0)), np.pad(chime, (int(0.12 * sr), 0)))
    return normalize(fade(reverb(out, 0.18, 0.32, sr), 0.001, 0.04, sr), PEAK_UI)


@sfx("swap_whoosh", "crypto", 400, "Token swap: rapid double whoosh")
def swap_whoosh(sr: int = SR) -> np.ndarray:
    n1 = noise(0.3, sr, seed=51, kind="pink") * adsr(0.3, 0.02, 0.08, 0.5, 0.14, sr)
    n2 = noise(0.25, sr, seed=52, kind="pink") * adsr(0.25, 0.02, 0.06, 0.5, 0.12, sr)
    f1 = bandpass(n1, 2000, sr, q=0.6)
    f2 = bandpass(n2, 1400, sr, q=0.6)
    tone = sine(pitch_sweep(300, 1600, 0.35, sr), 0.35, sr) * adsr(0.35, 0.02, 0.08, 0.35, 0.15, sr) * 0.3
    return normalize(fade(mix(f1, f2, tone), 0.006, 0.05, sr), PEAK_UI)


@sfx("bridge_warp", "crypto", 700, "Cross-chain bridge: sci-fi warp")
def bridge_warp(sr: int = SR) -> np.ndarray:
    sweep = sine(pitch_sweep(400, 2600, 0.5, sr), 0.5, sr) * adsr(0.5, 0.03, 0.1, 0.5, 0.2, sr)
    n = noise(0.5, sr, seed=53, kind="pink") * adsr(0.5, 0.03, 0.1, 0.4, 0.2, sr)
    nf = bandpass(n, 2200, sr, q=0.7) * 0.5
    sub = sine(pitch_sweep(90, 40, 0.5, sr), 0.5, sr) * adsr(0.5, 0.04, 0.1, 0.5, 0.2, sr) * 0.5
    return normalize(fade(mix(sweep, nf, sub), 0.008, 0.08, sr), PEAK_UI)


@sfx("mint_sparkle", "crypto", 800, "NFT minted: sparkle cascade")
def mint_sparkle(sr: int = SR) -> np.ndarray:
    out = silence(0.75, sr)
    rng = np.random.default_rng(54)
    for i in range(10):
        pos = int((0.05 + i * 0.065) * sr)
        f = 1800 + rng.uniform(-600, 900)
        t = sine(f, 0.18, sr) * perc_env(0.18, sr, 3.6) * rng.uniform(0.5, 1.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    chord = mix(
        sine(1318, 0.6, sr) * perc_env(0.6, sr, 2.2),
        sine(1760, 0.6, sr) * perc_env(0.6, sr, 3.0) * 0.4,
        sine(2637, 0.6, sr) * perc_env(0.6, sr, 4.0) * 0.2,
    )
    place(out, chord, 0.08, sr, gain=0.6)
    return normalize(fade(reverb(out, 0.3, 0.5, sr), 0.003, 0.1, sr), PEAK_UI)


@sfx("liquidation_alarm", "crypto", 900, "Position liquidating: urgent alternating tones")
def liquidation_alarm(sr: int = SR) -> np.ndarray:
    out = silence(0.85, sr)
    for i in range(7):
        f = 620 if i % 2 == 0 else 780
        pos = int(i * 0.11 * sr)
        t = square(f, 0.09, sr, 0.4) * adsr(0.09, 0.004, 0.02, 0.8, 0.03, sr)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(lowpass(out, 3000, sr), 0.003, 0.05, sr), PEAK_UI)


@sfx("gas_hiss", "crypto", 500, "Gas price: rising hiss", peak_db=-22)
def gas_hiss(sr: int = SR) -> np.ndarray:
    n = noise(0.45, sr, seed=55, kind="pink") * adsr(0.45, 0.05, 0.08, 0.6, 0.15, sr)
    nf = bandpass(n, 3200, sr, q=0.5)
    return normalize(fade(nf, 0.01, 0.06, sr), PEAK_UI - 4)


@sfx("chain_link", "crypto", 250, "Blockchain link: two metallic clicks", peak_db=-20)
def chain_link(sr: int = SR, seed: int = 56) -> np.ndarray:
    c1 = bandpass(noise(0.05, sr, seed=seed), 2400, sr, q=1.4) * perc_env(0.05, sr, 8.0)
    c2 = bandpass(noise(0.05, sr, seed=seed + 1), 2100, sr, q=1.4) * perc_env(0.05, sr, 8.0)
    return normalize(fade(concat(c1, silence(0.04, sr), c2), 0.001, 0.02, sr), PEAK_UI - 2)


@sfx("node_ping", "crypto", 120, "Network node responding: short blip", peak_db=-21)
def node_ping(sr: int = SR) -> np.ndarray:
    s = sine(pitch_sweep(800, 1200, 0.09, sr), 0.09, sr) * perc_env(0.09, sr, 5.0)
    return normalize(fade(s, 0.002, 0.015, sr), PEAK_UI - 3)


@sfx("data_burst", "crypto", 300, "Data packet burst: rapid stutter")
def data_burst(sr: int = SR, seed: int = 57) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.26, sr)
    for i in range(6):
        pos = int((0.01 + i * 0.042) * sr)
        t = sine(1400 + rng.uniform(-300, 500), 0.03, sr) * perc_env(0.03, sr, 9.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(highpass(out, 900, sr), 0.002, 0.02, sr), PEAK_UI)


@sfx("encrypt_scramble", "crypto", 500, "Encryption: rising digital scramble")
def encrypt_scramble(sr: int = SR, seed: int = 58) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.45, sr)
    for i in range(14):
        pos = int((0.02 + i * 0.028) * sr)
        f = rng.uniform(600, 3200)
        t = square(f, 0.022, sr, 0.4) * adsr(0.022, 0.002, 0.005, 0.8, 0.008, sr) * 0.5
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    sweep = sine(pitch_sweep(300, 2600, 0.45, sr), 0.45, sr) * adsr(0.45, 0.03, 0.1, 0.3, 0.2, sr) * 0.3
    return normalize(fade(mix(out, sweep), 0.004, 0.05, sr), PEAK_UI)


@sfx("sync_sweep", "crypto", 600, "Sync: smooth rise and settle")
def sync_sweep(sr: int = SR) -> np.ndarray:
    f = pitch_sweep(250, 1400, 0.5, sr)
    s = sine(f, 0.5, sr) * adsr(0.5, 0.04, 0.08, 0.55, 0.2, sr)
    settle = sine(330, 0.15, sr) * perc_env(0.15, sr, 4.5) * 0.35
    return normalize(fade(mix(s, np.pad(settle, (int(0.36 * sr), 0))), 0.006, 0.06, sr), PEAK_UI)


@sfx("server_hum", "crypto", 1000, "Server room: layered hum", peak_db=-26)
def server_hum(sr: int = SR) -> np.ndarray:
    h = 0.0
    for f, g in ((120, 1.0), (240, 0.6), (360, 0.35), (60, 0.5)):
        h += saw(f, 0.9, sr) * g
    fan = noise(0.9, sr, seed=59, kind="pink") * 0.25
    return normalize(fade(lowpass(h, 700, sr) * 0.6 + fan, 0.05, 0.1, sr), PEAK_UI - 8)


# ==========================================================================
# 3.4  Transitions / whooshes (18)
# ==========================================================================

@sfx("whoosh_short", "transition", 250, "Quick whoosh for small transitions", peak_db=-20)
def whoosh_short(sr: int = SR, seed: int = 61) -> np.ndarray:
    n = noise(0.22, sr, seed=seed, kind="pink")
    env = adsr(0.22, 0.02, 0.05, 0.5, 0.12, sr)
    return normalize(fade(bandpass(n * env, 1800, sr, q=0.6), 0.005, 0.05, sr), PEAK_TRANSITION)


@sfx("whoosh_long", "transition", 600, "Long cinematic whoosh", peak_db=-20)
def whoosh_long(sr: int = SR, seed: int = 62) -> np.ndarray:
    n = noise(0.55, sr, seed=seed, kind="pink")
    env = adsr(0.55, 0.05, 0.1, 0.55, 0.22, sr)
    return normalize(fade(bandpass(n * env, 1600, sr, q=0.5), 0.01, 0.09, sr), PEAK_TRANSITION)


@sfx("whoosh_reverse", "transition", 500, "Reverse whoosh (sucked inward)", peak_db=-20)
def whoosh_reverse(sr: int = SR, seed: int = 63) -> np.ndarray:
    fwd = whoosh_long(sr, seed=seed)[: int(0.5 * sr)]
    return normalize(fade(fwd[::-1], 0.008, 0.08, sr), PEAK_TRANSITION)


@sfx("whip_pan", "transition", 300, "Camera whip: fast swipe", peak_db=-20)
def whip_pan(sr: int = SR, seed: int = 64) -> np.ndarray:
    n = noise(0.26, sr, seed=seed, kind="pink")
    env = adsr(0.26, 0.008, 0.04, 0.5, 0.16, sr)
    return normalize(fade(highpass(n * env, 1200, sr), 0.003, 0.07, sr), PEAK_TRANSITION)


@sfx("riser_short", "transition", 700, "Short tension riser", peak_db=-20)
def riser_short(sr: int = SR, seed: int = 65) -> np.ndarray:
    n = noise(0.65, sr, seed=seed, kind="pink")
    env = adsr(0.65, 0.06, 0.08, 0.7, 0.25, sr)
    f = pitch_sweep(400, 3400, 0.65, sr)
    tone = sine(f, 0.65, sr) * env * 0.35
    return normalize(fade(bandpass(n * env, 2200, sr, q=0.5) + tone, 0.01, 0.12, sr), PEAK_TRANSITION)


@sfx("riser_long", "transition", 1500, "Long cinematic riser", peak_db=-20)
def riser_long(sr: int = SR, seed: int = 66) -> np.ndarray:
    n = noise(1.4, sr, seed=seed, kind="pink")
    env = adsr(1.4, 0.1, 0.15, 0.65, 0.5, sr)
    f = pitch_sweep(200, 3000, 1.4, sr)
    tone = sine(f, 1.4, sr) * env * 0.3
    # tremolo intensifies toward the end
    t = np.arange(int(1.4 * sr)) / sr
    trem = 1 + 0.5 * np.sin(2 * np.pi * (4 + 18 * t) * t)
    return normalize(fade(bandpass(n * env, 2000, sr, q=0.4) * trem + tone, 0.02, 0.2, sr), PEAK_TRANSITION)


@sfx("impact_soft", "transition", 300, "Soft impact: sub thud with air", peak_db=-20)
def impact_soft(sr: int = SR, seed: int = 67) -> np.ndarray:
    sub = sine(pitch_sweep(110, 50, 0.25, sr), 0.25, sr) * perc_env(0.25, sr, 3.5)
    air = noise(0.08, sr, seed=seed) * perc_env(0.08, sr, 10.0)
    air = lowpass(air, 3000, sr) * 0.4
    return normalize(fade(mix(sub, air), 0.001, 0.06, sr), PEAK_TRANSITION)


@sfx("impact_hard", "transition", 500, "Hard impact: punchy boom", peak_db=-20)
def impact_hard(sr: int = SR, seed: int = 68) -> np.ndarray:
    sub = sine(pitch_sweep(90, 38, 0.4, sr), 0.4, sr) * perc_env(0.4, sr, 3.0)
    crack = noise(0.06, sr, seed=seed) * perc_env(0.06, sr, 11.0)
    crack = bandpass(crack, 1500, sr, q=0.8) * 0.5
    body = noise(0.12, sr, seed=seed + 1) * perc_env(0.12, sr, 7.0)
    body = lowpass(body, 2500, sr) * 0.6
    return normalize(fade(reverb(mix(sub, crack, body), 0.2, 0.35, sr), 0.001, 0.08, sr), PEAK_TRANSITION)


@sfx("boom_sub", "transition", 800, "Big sub boom", peak_db=-20)
def boom_sub(sr: int = SR) -> np.ndarray:
    s = sine(pitch_sweep(70, 30, 0.7, sr), 0.7, sr) * perc_env(0.7, sr, 2.2)
    return normalize(fade(reverb(s, 0.4, 0.6, sr), 0.002, 0.15, sr), PEAK_TRANSITION)


@sfx("glitch_tear", "transition", 300, "Digital glitch tear", peak_db=-20)
def glitch_tear(sr: int = SR, seed: int = 69) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.26, sr)
    for i in range(8):
        pos = int(rng.uniform(0.0, 0.2) * sr)
        dur = 0.02 + rng.uniform(0, 0.02)
        t = square(rng.uniform(900, 4200), dur, sr, 0.5) * adsr(dur, 0.001, 0.004, 0.7, 0.008, sr) * 0.35
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(out, 0.001, 0.01, sr), PEAK_TRANSITION)


@sfx("digital_scramble", "transition", 400, "Digital scramble", peak_db=-20)
def digital_scramble(sr: int = SR, seed: int = 70) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.36, sr)
    for i in range(20):
        pos = int((0.01 + i * 0.016) * sr)
        f = rng.uniform(400, 5000)
        t = square(f, 0.014, sr, 0.45) * adsr(0.014, 0.001, 0.003, 0.8, 0.005, sr) * 0.4
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(out, 0.001, 0.012, sr), PEAK_TRANSITION)


@sfx("tape_stop", "transition", 500, "Tape machine grinding to a halt", peak_db=-20)
def tape_stop(sr: int = SR) -> np.ndarray:
    n = noise(0.45, sr, seed=71, kind="pink") * adsr(0.45, 0.01, 0.05, 0.7, 0.2, sr)
    nf = bandpass(n, 1200, sr, q=0.5)
    # pitch drops as the motor slows
    t = np.arange(int(0.45 * sr)) / sr
    warble = np.sin(2 * np.pi * np.cumsum(60 * (1 - t * 0.7)) / sr)
    return normalize(fade(nf * (0.7 + 0.3 * warble), 0.004, 0.06, sr), PEAK_TRANSITION)


@sfx("vinyl_scratch", "transition", 400, "Record scratch", peak_db=-20)
def vinyl_scratch(sr: int = SR, seed: int = 72) -> np.ndarray:
    n = noise(0.35, sr, seed=seed, kind="pink")
    env = adsr(0.35, 0.005, 0.04, 0.7, 0.1, sr)
    nf = bandpass(n * env, 5000, sr, q=1.0)
    t = np.arange(int(0.35 * sr)) / sr
    wob = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * (8 + 20 * t) * t))
    return normalize(fade(nf * wob, 0.003, 0.04, sr), PEAK_TRANSITION)


@sfx("film_burn", "transition", 700, "Film stock burning: crackle", peak_db=-20)
def film_burn(sr: int = SR, seed: int = 73) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.65, sr)
    for i in range(26):
        pos = int(rng.uniform(0.0, 0.6) * sr)
        d = 0.03 + rng.uniform(0, 0.04)
        t = bandpass(noise(d, sr, seed=seed + i), 3000, sr, q=1.2) * perc_env(d, sr, 6.0) * rng.uniform(0.4, 1.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    sub = sine(pitch_sweep(80, 40, 0.65, sr), 0.65, sr) * adsr(0.65, 0.1, 0.1, 0.6, 0.25, sr) * 0.4
    return normalize(fade(mix(out, sub), 0.01, 0.08, sr), PEAK_TRANSITION)


@sfx("light_flash", "transition", 250, "Flash of light: bright ping", peak_db=-23)
def light_flash(sr: int = SR) -> np.ndarray:
    s = sine(pitch_sweep(1200, 3200, 0.2, sr), 0.2, sr) * perc_env(0.2, sr, 4.0)
    return normalize(fade(s, 0.002, 0.05, sr), PEAK_TRANSITION - 3)


@sfx("wipe_swipe", "transition", 200, "Wipe transition: directional swipe", peak_db=-20)
def wipe_swipe(sr: int = SR, seed: int = 74) -> np.ndarray:
    n = noise(0.18, sr, seed=seed, kind="pink") * adsr(0.18, 0.015, 0.04, 0.5, 0.09, sr)
    return normalize(fade(bandpass(n, 2500, sr, q=0.7), 0.004, 0.04, sr), PEAK_TRANSITION)


@sfx("morph_bend", "transition", 600, "Shape morph: liquid bend", peak_db=-20)
def morph_bend(sr: int = SR) -> np.ndarray:
    f = pitch_sweep(300, 900, 0.3, sr)
    f2 = pitch_sweep(900, 400, 0.3, sr)
    s = sine(f, 0.3, sr) * adsr(0.3, 0.04, 0.06, 0.6, 0.12, sr)
    s2 = sine(f2, 0.3, sr) * adsr(0.3, 0.03, 0.06, 0.5, 0.12, sr)
    return normalize(fade(mix(s, np.pad(s2, (int(0.3 * sr), 0))), 0.01, 0.08, sr), PEAK_TRANSITION)


@sfx("zoom_rush", "transition", 450, "Camera zoom: rushing air", peak_db=-20)
def zoom_rush(sr: int = SR, seed: int = 75) -> np.ndarray:
    n = noise(0.4, sr, seed=seed, kind="pink") * adsr(0.4, 0.02, 0.08, 0.6, 0.18, sr)
    nf = bandpass(n, 1700, sr, q=0.5)
    sweep = sine(pitch_sweep(200, 2000, 0.4, sr), 0.4, sr) * adsr(0.4, 0.02, 0.08, 0.4, 0.18, sr) * 0.3
    return normalize(fade(mix(nf, sweep), 0.006, 0.07, sr), PEAK_TRANSITION)


# ==========================================================================
# 3.5  Mechanical / physical (16)
# ==========================================================================

@sfx("switch_flip", "mech", 100, "Toggle switch flipping")
def switch_flip(sr: int = SR, seed: int = 81) -> np.ndarray:
    a = bandpass(noise(0.03, sr, seed=seed), 2800, sr, q=1.5) * perc_env(0.03, sr, 10.0)
    b = bandpass(noise(0.03, sr, seed=seed + 1), 1900, sr, q=1.5) * perc_env(0.03, sr, 10.0) * 0.8
    return normalize(fade(concat(a, b), 0.0008, 0.012, sr), PEAK_UI)


@sfx("latch_close", "mech", 150, "Latch engaging")
def latch_close(sr: int = SR, seed: int = 82) -> np.ndarray:
    snap = bandpass(noise(0.05, sr, seed=seed), 1600, sr, q=1.0) * perc_env(0.05, sr, 9.0)
    low = sine(220, 0.09, sr) * perc_env(0.09, sr, 6.0) * 0.6
    return normalize(fade(mix(snap, low), 0.001, 0.02, sr), PEAK_UI)


@sfx("gear_turn", "mech", 400, "Gear ratcheting", peak_db=-20)
def gear_turn(sr: int = SR, seed: int = 83) -> np.ndarray:
    out = silence(0.36, sr)
    rng = np.random.default_rng(seed)
    for i in range(7):
        pos = int((0.02 + i * 0.05) * sr)
        t = bandpass(noise(0.04, sr, seed=seed + i), 1100 + rng.uniform(-300, 300), sr, q=1.2) * perc_env(0.04, sr, 8.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(out, 0.002, 0.03, sr), PEAK_UI - 2)


@sfx("spring_boing", "mech", 350, "Spring twang", peak_db=-20)
def spring_boing(sr: int = SR) -> np.ndarray:
    # A spring is a pitch that wobbles as it settles; FM gives the wobble.
    f0 = 300
    t = np.arange(int(0.32 * sr)) / sr
    fm = f0 * (1 + 0.35 * np.exp(-t * 18) * np.sin(2 * np.pi * 11 * t))
    s = sine(np.cumsum(fm) / sr, 0.32, sr)
    return normalize(fade(s * perc_env(0.32, sr, 2.0), 0.001, 0.04, sr), PEAK_UI - 2)


@sfx("paper_slide", "mech", 250, "Paper sliding across a surface", peak_db=-22)
def paper_slide(sr: int = SR, seed: int = 84) -> np.ndarray:
    n = noise(0.22, sr, seed=seed, kind="pink") * adsr(0.22, 0.04, 0.05, 0.6, 0.08, sr)
    nf = bandpass(n, 4500, sr, q=0.6)
    return normalize(fade(nf, 0.008, 0.04, sr), PEAK_UI - 4)


@sfx("paper_tear", "mech", 300, "Paper tearing")
def paper_tear(sr: int = SR, seed: int = 85) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.26, sr)
    for i in range(12):
        pos = int(rng.uniform(0.0, 0.2) * sr)
        d = 0.02 + rng.uniform(0, 0.02)
        t = bandpass(noise(d, sr, seed=seed + i), 3000 + rng.uniform(-500, 1000), sr, q=1.0) * perc_env(d, sr, 9.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t * rng.uniform(0.5, 1.0)
    return normalize(fade(out, 0.001, 0.02, sr), PEAK_UI)


@sfx("glass_tap", "mech", 180, "Tapping glass")
def glass_tap(sr: int = SR, seed: int = 86) -> np.ndarray:
    partials = [(2600, 1.0), (3800, 0.5), (5100, 0.25)]
    out = silence(0.16, sr)
    for f, g in partials:
        out += sine(f, 0.16, sr) * perc_env(0.16, sr, 6.0) * g
    strike = noise(0.02, sr, seed=seed) * perc_env(0.02, sr, 12.0) * 0.4
    return normalize(fade(mix(out, strike), 0.0008, 0.03, sr), PEAK_UI)


@sfx("glass_break", "mech", 700, "Glass shattering")
def glass_break(sr: int = SR, seed: int = 87) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.65, sr)
    for i in range(30):
        pos = int(rng.uniform(0.0, 0.12) * sr)
        f = 2600 + rng.uniform(-800, 3200)
        d = 0.1 + rng.uniform(0, 0.2)
        t = sine(f, d, sr) * perc_env(d, sr, 5.0) * rng.uniform(0.3, 0.8)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    shatter = bandpass(noise(0.1, sr, seed=seed + 1), 4000, sr, q=0.7) * perc_env(0.1, sr, 8.0) * 0.5
    return normalize(fade(mix(out, np.pad(shatter, (0, 0))), 0.001, 0.1, sr), PEAK_UI)


@sfx("metal_ping", "mech", 400, "Metallic ping")
def metal_ping(sr: int = SR) -> np.ndarray:
    partials = [(1880, 1.0), (2510, 0.55), (3390, 0.3), (4240, 0.18)]
    out = silence(0.35, sr)
    for f, g in partials:
        out += sine(f, 0.35, sr) * perc_env(0.35, sr, 4.2) * g
    return normalize(fade(reverb(out, 0.25, 0.4, sr), 0.001, 0.06, sr), PEAK_UI)


@sfx("wood_knock", "mech", 150, "Knocking wood")
def wood_knock(sr: int = SR, seed: int = 88) -> np.ndarray:
    thud = sine(180, 0.1, sr) * perc_env(0.1, sr, 7.0)
    tap = bandpass(noise(0.03, sr, seed=seed), 2400, sr, q=1.0) * perc_env(0.03, sr, 10.0) * 0.4
    return normalize(fade(mix(thud, tap), 0.001, 0.02, sr), PEAK_UI)


@sfx("rubber_squeak", "mech", 200, "Rubber squeak", peak_db=-22)
def rubber_squeak(sr: int = SR) -> np.ndarray:
    f = pitch_sweep(700, 1000, 0.09, sr)
    a = sine(f, 0.09, sr) * perc_env(0.09, sr, 4.0)
    f2 = pitch_sweep(950, 700, 0.09, sr)
    b = sine(f2, 0.09, sr) * perc_env(0.09, sr, 4.0)
    return normalize(fade(concat(a, b), 0.002, 0.02, sr), PEAK_UI - 4)


@sfx("chain_rattle", "mech", 500, "Chain rattling", peak_db=-21)
def chain_rattle(sr: int = SR, seed: int = 89) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = silence(0.45, sr)
    for i in range(10):
        pos = int(rng.uniform(0.0, 0.36) * sr)
        f = 1800 + rng.uniform(-400, 700)
        d = 0.04 + rng.uniform(0, 0.03)
        t = bandpass(noise(d, sr, seed=seed + i), f, sr, q=1.3) * perc_env(d, sr, 8.0) * rng.uniform(0.5, 1.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(out, 0.001, 0.04, sr), PEAK_UI - 3)


@sfx("door_slide", "mech", 600, "Door sliding open")
def door_slide(sr: int = SR, seed: int = 90) -> np.ndarray:
    n = noise(0.5, sr, seed=seed, kind="pink") * adsr(0.5, 0.03, 0.1, 0.6, 0.2, sr)
    nf = bandpass(n, 900, sr, q=0.5)
    rumble = lowpass(noise(0.5, sr, seed=seed + 1, kind="brown"), 250, sr) * adsr(0.5, 0.05, 0.1, 0.5, 0.2, sr) * 0.5
    return normalize(fade(mix(nf, rumble), 0.01, 0.08, sr), PEAK_UI)


@sfx("lock_turn", "mech", 350, "Key turning in a lock")
def lock_turn(sr: int = SR, seed: int = 91) -> np.ndarray:
    t1 = bandpass(noise(0.05, sr, seed=seed), 2400, sr, q=1.2) * perc_env(0.05, sr, 8.0)
    t2 = bandpass(noise(0.06, sr, seed=seed + 1), 1900, sr, q=1.2) * perc_env(0.06, sr, 7.0)
    clk = bandpass(noise(0.04, sr, seed=seed + 2), 3000, sr, q=1.4) * perc_env(0.04, sr, 10.0) * 0.8
    return normalize(fade(concat(t1, silence(0.05, sr), t2, silence(0.03, sr), clk), 0.001, 0.02, sr), PEAK_UI)


@sfx("stamp_press", "mech", 250, "Press: stamping down", peak_db=-21)
def stamp_press(sr: int = SR) -> np.ndarray:
    down = sine(pitch_sweep(150, 90, 0.12, sr), 0.12, sr) * perc_env(0.12, sr, 5.0)
    return normalize(fade(down, 0.001, 0.04, sr), PEAK_UI - 3)


@sfx("typewriter_return", "mech", 550, "Typewriter carriage return")
def typewriter_return(sr: int = SR, seed: int = 92) -> np.ndarray:
    slide = noise(0.28, sr, seed=seed, kind="pink") * adsr(0.28, 0.01, 0.05, 0.6, 0.12, sr)
    slide = bandpass(slide, 2200, sr, q=0.6)
    ding = mix(sine(1318, 0.25, sr) * perc_env(0.25, sr, 3.4), sine(1975, 0.25, sr) * perc_env(0.25, sr, 4.4) * 0.4)
    return normalize(fade(mix(slide, np.pad(ding, (int(0.22 * sr), 0))), 0.004, 0.05, sr), PEAK_UI)


# ==========================================================================
# 3.6  Ambience / texture (14, all loops)
# ==========================================================================

def _loop(dur: float, sr: int, fn, crossfade: float = 0.05):
    """Render a loopable buffer with a short crossfade at the seam.

    A loop is only usable if the end of the buffer matches the start; without
    the crossfade every repetition clicks at the wrap point.
    """
    n = int(dur * sr)
    cf = int(crossfade * sr)
    sig = fn(dur + crossfade * 2, sr)
    out = sig[:n].copy()
    fade_in = np.linspace(0, 1, cf)
    out[:cf] *= fade_in
    out[n - cf :] *= fade_in[::-1]
    tail = sig[n : n + cf]
    out[n - cf :] += tail * fade_in
    return out


@sfx("room_tone", "ambience", 5000, "Quiet room air", loop=True, peak_db=-48)
def room_tone(sr: int = SR, seed: int = 101) -> np.ndarray:
    return normalize(fade(noise(5.0, sr, seed=seed, kind="brown") * 0.12, 0.02, 0.02, sr), PEAK_UI - 30)


@sfx("city_hum", "ambience", 5000, "Distant city rumble", loop=True, peak_db=-42)
def city_hum(sr: int = SR, seed: int = 102) -> np.ndarray:
    base = noise(5.0, sr, seed=seed, kind="brown") * 0.5
    drone = saw(55, 5.0, sr) * 0.2
    return normalize(fade(lowpass(base + drone, 500, sr), 0.05, 0.05, sr), PEAK_UI - 24)


@sfx("office_murmur", "ambience", 5000, "Indistinct office chatter", loop=True, peak_db=-44)
def office_murmur(sr: int = SR, seed: int = 103) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = noise(5.0, sr, seed=seed, kind="pink") * 0.3
    for _ in range(40):
        pos = int(rng.uniform(0, 4.8) * sr)
        d = 0.3 + rng.uniform(0, 0.5)
        # formant-ish bands make it read as speech, not noise
        t = bandpass(noise(d, sr, seed=int(rng.integers(0, 9999))), 800 + rng.uniform(0, 500), sr, q=2.0)
        t = bandpass(t, 2400 + rng.uniform(0, 1200), sr, q=1.5) * adsr(d, 0.05, 0.08, 0.5, 0.15, sr)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t * 0.5
    return normalize(fade(out, 0.05, 0.05, sr), PEAK_UI - 26)


@sfx("rain_soft", "ambience", 5000, "Soft rain on leaves", loop=True, peak_db=-40)
def rain_soft(sr: int = SR, seed: int = 104) -> np.ndarray:
    n = noise(5.0, sr, seed=seed, kind="white")
    # many tiny drops: amplitude-modulate white noise with high-rate blips
    t = np.arange(int(5.0 * sr)) / sr
    drops = (np.sin(2 * np.pi * 71 * t) > 0.97).astype(float) * 0.5
    drops += (np.sin(2 * np.pi * 53 * t) > 0.97).astype(float) * 0.3
    out = n * (0.4 + drops)
    return normalize(fade(highpass(out, 600, sr), 0.05, 0.05, sr), PEAK_UI - 22)


@sfx("wind_low", "ambience", 5000, "Low wind", loop=True, peak_db=-44)
def wind_low(sr: int = SR, seed: int = 105) -> np.ndarray:
    n = noise(5.0, sr, seed=seed, kind="pink")
    t = np.arange(int(5.0 * sr)) / sr
    # slow LFO swells make it wind rather than static hiss
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t) * np.sin(2 * np.pi * 0.07 * t)
    return normalize(fade(lowpass(n, 800, sr) * lfo, 0.2, 0.2, sr), PEAK_UI - 26)


@sfx("electric_buzz", "ambience", 5000, "Electrical mains hum", loop=True, peak_db=-40)
def electric_buzz(sr: int = SR) -> np.ndarray:
    b = square(50, 5.0, sr, 0.35) * 0.5
    h = square(150, 5.0, sr, 0.35) * 0.2
    return normalize(fade(lowpass(b + h, 1200, sr), 0.05, 0.05, sr), PEAK_UI - 22)


@sfx("fan_whirr", "ambience", 5000, "Cooling fan", loop=True, peak_db=-42)
def fan_whirr(sr: int = SR, seed: int = 106) -> np.ndarray:
    n = noise(5.0, sr, seed=seed, kind="pink") * 0.4
    t = np.arange(int(5.0 * sr)) / sr
    blade = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 23 * t))
    return normalize(fade(bandpass(n, 700, sr, q=0.6) * blade, 0.05, 0.05, sr), PEAK_UI - 24)


@sfx("crowd_distant", "ambience", 5000, "Distant crowd roar", loop=True, peak_db=-42)
def crowd_distant(sr: int = SR, seed: int = 107) -> np.ndarray:
    n = noise(5.0, sr, seed=seed, kind="pink")
    t = np.arange(int(5.0 * sr)) / sr
    swell = 0.7 + 0.3 * np.sin(2 * np.pi * 0.09 * t)
    return normalize(fade(lowpass(n, 1500, sr) * swell, 0.15, 0.15, sr), PEAK_UI - 24)


@sfx("water_flow", "ambience", 5000, "Running water", loop=True, peak_db=-38)
def water_flow(sr: int = SR, seed: int = 108) -> np.ndarray:
    n = noise(5.0, sr, seed=seed, kind="white")
    nf = bandpass(n, 2400, sr, q=0.4)
    t = np.arange(int(5.0 * sr)) / sr
    churn = 0.7 + 0.3 * np.sin(2 * np.pi * 1.7 * t) * np.sin(2 * np.pi * 2.3 * t)
    return normalize(fade(nf * churn, 0.1, 0.1, sr), PEAK_UI - 20)


@sfx("fire_crackle", "ambience", 5000, "Campfire crackle", loop=True, peak_db=-40)
def fire_crackle(sr: int = SR, seed: int = 109) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = noise(5.0, sr, seed=seed, kind="brown") * 0.25
    for _ in range(120):
        pos = int(rng.uniform(0, 4.8) * sr)
        d = 0.01 + rng.uniform(0, 0.03)
        t = bandpass(noise(d, sr, seed=int(rng.integers(0, 99999))), 3500, sr, q=1.4) * perc_env(d, sr, 7.0) * rng.uniform(0.3, 1.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(out, 0.05, 0.05, sr), PEAK_UI - 22)


@sfx("night_crickets", "ambience", 5000, "Crickets at night", loop=True, peak_db=-44)
def night_crickets(sr: int = SR, seed: int = 110) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = noise(5.0, sr, seed=seed, kind="brown") * 0.15
    for _ in range(60):
        pos = int(rng.uniform(0, 4.8) * sr)
        d = 0.05 + rng.uniform(0, 0.06)
        f = 3800 + rng.uniform(0, 800)
        pulse = (np.sin(2 * np.pi * 29 * np.arange(int(d * sr)) / sr) > 0.0).astype(float)
        t = sine(f, d, sr) * pulse * adsr(d, 0.005, 0.01, 0.8, 0.02, sr)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t * 0.4
    return normalize(fade(out, 0.05, 0.05, sr), PEAK_UI - 26)


@sfx("keyboard_office", "ambience", 5000, "Office typing in the background", loop=True, peak_db=-42)
def keyboard_office(sr: int = SR, seed: int = 111) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = noise(5.0, sr, seed=seed, kind="brown") * 0.15
    for _ in range(90):
        pos = int(rng.uniform(0, 4.8) * sr)
        t = bandpass(noise(0.02, sr, seed=int(rng.integers(0, 99999))), 2200, sr, q=1.2) * perc_env(0.02, sr, 10.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t * 0.6
    return normalize(fade(out, 0.05, 0.05, sr), PEAK_UI - 24)


@sfx("traffic_far", "ambience", 5000, "Distant traffic", loop=True, peak_db=-42)
def traffic_far(sr: int = SR, seed: int = 112) -> np.ndarray:
    n = noise(5.0, sr, seed=seed, kind="brown") * 0.5
    t = np.arange(int(5.0 * sr)) / sr
    # passing cars: band-limited swells at irregular intervals
    passes = np.zeros(int(5.0 * sr))
    rng = np.random.default_rng(seed)
    for _ in range(8):
        centre = rng.uniform(0.4, 4.6) * sr
        width = rng.uniform(0.3, 0.9) * sr
        idx = np.arange(len(passes))
        passes += np.exp(-((idx - centre) ** 2) / (2 * width**2)) * rng.uniform(0.3, 0.7)
    return normalize(fade(lowpass(n, 700, sr) * (0.5 + passes), 0.1, 0.1, sr), PEAK_UI - 24)


@sfx("datacenter_drone", "ambience", 5000, "Data centre: fans and hum", loop=True, peak_db=-44)
def datacenter_drone(sr: int = SR, seed: int = 113) -> np.ndarray:
    fan = noise(5.0, sr, seed=seed, kind="pink") * 0.4
    t = np.arange(int(5.0 * sr)) / sr
    blade = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 31 * t))
    hum = saw(60, 5.0, sr) * 0.3 + saw(120, 5.0, sr) * 0.2
    return normalize(fade(bandpass(fan, 800, sr, q=0.6) * blade + lowpass(hum, 500, sr), 0.05, 0.05, sr), PEAK_UI - 26)


# ==========================================================================
# 3.7  Musical stingers (10)
# ==========================================================================

@sfx("sting_up_major", "stinger", 800, "Bright major rise")
def sting_up_major(sr: int = SR) -> np.ndarray:
    out = silence(0.75, sr)
    for i, f in enumerate((523, 659, 784, 1046)):
        pos = int(i * 0.11 * sr)
        t = sine(f, 0.4, sr) * perc_env(0.4, sr, 3.2)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(reverb(out, 0.3, 0.5, sr), 0.003, 0.1, sr), PEAK_UI)


@sfx("sting_down_minor", "stinger", 800, "Minor fall")
def sting_down_minor(sr: int = SR) -> np.ndarray:
    out = silence(0.75, sr)
    for i, f in enumerate((1046, 880, 698, 523)):
        pos = int(i * 0.11 * sr)
        t = sine(f, 0.4, sr) * perc_env(0.4, sr, 3.4)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(reverb(out, 0.3, 0.5, sr), 0.003, 0.1, sr), PEAK_UI)


@sfx("sting_reveal", "stinger", 1200, "Big reveal: chord swell")
def sting_reveal(sr: int = SR) -> np.ndarray:
    dur = 1.1
    out = silence(dur, sr)
    for f, g in ((392, 1.0), (523, 0.8), (659, 0.7), (784, 0.5), (1046, 0.35)):
        tone = sine(f, dur, sr) * adsr(dur, 0.15, 0.2, 0.75, 0.4, sr) * g
        out[: len(tone)] += tone
    sparkle = mix(
        sine(1567, dur, sr) * adsr(dur, 0.3, 0.2, 0.5, 0.5, sr) * 0.2,
        sine(2093, dur, sr) * adsr(dur, 0.35, 0.2, 0.4, 0.5, sr) * 0.12,
    )
    out[: len(sparkle)] += sparkle
    return normalize(fade(reverb(out, 0.35, 0.6, sr), 0.02, 0.2, sr), PEAK_UI)


@sfx("sting_tension", "stinger", 1000, "Suspenseful dissonant swell", peak_db=-20)
def sting_tension(sr: int = SR) -> np.ndarray:
    dur = 0.9
    # minor second cluster: dissonant by design
    out = sine(440, dur, sr) * adsr(dur, 0.2, 0.2, 0.7, 0.3, sr)
    out += sine(466, dur, sr) * adsr(dur, 0.2, 0.2, 0.55, 0.3, sr) * 0.7
    out += sine(587, dur, sr) * adsr(dur, 0.25, 0.2, 0.5, 0.3, sr) * 0.5
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * 5.5 * np.arange(len(out)) / sr)
    return normalize(fade(reverb(out * trem, 0.3, 0.55, sr), 0.03, 0.15, sr), PEAK_UI - 2)


@sfx("sting_resolve", "stinger", 1400, "Tension resolving into a major chord")
def sting_resolve(sr: int = SR) -> np.ndarray:
    dur = 1.3
    riser = sine(pitch_sweep(300, 800, 0.7, sr), 0.7, sr) * adsr(0.7, 0.05, 0.1, 0.6, 0.3, sr) * 0.4
    riser += noise(0.7, sr, seed=121, kind="pink") * adsr(0.7, 0.05, 0.1, 0.5, 0.3, sr) * 0.2
    chord = silence(dur, sr)
    for f, g in ((523, 1.0), (659, 0.8), (784, 0.7)):
        tone = sine(f, 0.9, sr) * adsr(0.9, 0.25, 0.2, 0.7, 0.4, sr) * g
        place(chord, tone, 0.7, sr)
    out = mix(riser, chord)
    return normalize(fade(reverb(out, 0.32, 0.55, sr), 0.01, 0.2, sr), PEAK_UI)


@sfx("arp_up", "stinger", 600, "Fast rising arpeggio")
def arp_up(sr: int = SR) -> np.ndarray:
    out = silence(0.55, sr)
    for i, f in enumerate((523, 659, 784, 1046, 1318, 1567)):
        pos = int((0.04 + i * 0.075) * sr)
        t = triangle(f, 0.14, sr) * perc_env(0.14, sr, 3.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(out, 0.003, 0.06, sr), PEAK_UI)


@sfx("arp_down", "stinger", 600, "Fast falling arpeggio")
def arp_down(sr: int = SR) -> np.ndarray:
    out = silence(0.55, sr)
    for i, f in enumerate((1567, 1318, 1046, 784, 659, 523)):
        pos = int((0.04 + i * 0.075) * sr)
        t = triangle(f, 0.14, sr) * perc_env(0.14, sr, 3.0)
        if pos + len(t) < len(out):
            out[pos : pos + len(t)] += t
    return normalize(fade(out, 0.003, 0.06, sr), PEAK_UI)


@sfx("chord_stab", "stinger", 400, "Sharp chord stab")
def chord_stab(sr: int = SR) -> np.ndarray:
    dur = 0.35
    out = silence(dur, sr)
    for f, g in ((523, 1.0), (659, 0.8), (784, 0.6)):
        tone = square(f, dur, sr, 0.4) * adsr(dur, 0.004, 0.05, 0.5, 0.15, sr) * g * 0.5
        out[: len(tone)] += tone
    return normalize(fade(lowpass(out, 3800, sr), 0.002, 0.06, sr), PEAK_UI)


@sfx("bell_reveal", "stinger", 1000, "Bell announcing a reveal")
def bell_reveal(sr: int = SR) -> np.ndarray:
    partials = [(880, 1.0), (1760, 0.45), (2640, 0.25), (3520, 0.12)]
    out = silence(0.9, sr)
    for f, g in partials:
        out += sine(f, 0.9, sr) * perc_env(0.9, sr, 1.8) * g
    return normalize(fade(reverb(out, 0.4, 0.65, sr), 0.002, 0.15, sr), PEAK_UI)


@sfx("pad_swell", "stinger", 2000, "Slow pad swell", peak_db=-20)
def pad_swell(sr: int = SR) -> np.ndarray:
    dur = 1.9
    out = silence(dur, sr)
    for f, g in ((220, 0.8), (277, 0.6), (330, 0.5), (440, 0.35)):
        tone = sine(f, dur, sr) * adsr(dur, 0.5, 0.2, 0.65, 0.7, sr) * g
        out[: len(tone)] += tone
    air = noise(dur, sr, seed=122, kind="pink") * adsr(dur, 0.6, 0.2, 0.3, 0.7, sr) * 0.12
    return normalize(fade(reverb(mix(out, air), 0.35, 0.6, sr), 0.05, 0.3, sr), PEAK_UI - 2)
