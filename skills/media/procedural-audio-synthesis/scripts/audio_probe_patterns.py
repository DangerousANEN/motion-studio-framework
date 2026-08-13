#!/usr/bin/env python3
"""Measurement probes for procedurally synthesized audio.

Every check here exists because its absence let a real defect through. The
recurring theme: a waveform screenshot, a "wet != dry" assertion, and a rounded
RMS comparison all report success on audio that is objectively broken. Numbers in
dB catch it; nothing cheaper does.

Adapt the REGISTRY import and the SPEC field names to the project, then run.
Exits non-zero on any issue so it can gate CI.
"""
from __future__ import annotations

import math
import sys

import numpy as np
from scipy import signal

SR = 48_000


# ---------------------------------------------------------------- utilities
def db(x: float) -> float:
    """Amplitude -> dBFS, floored so log(0) can't poison a comparison."""
    return 20.0 * math.log10(max(float(abs(x)), 1e-12))


def peak_db(sig: np.ndarray) -> float:
    return db(np.max(np.abs(sig))) if sig.size else -np.inf


def rms_db(sig: np.ndarray) -> float:
    return db(np.sqrt(np.mean(sig.astype(np.float64) ** 2))) if sig.size else -np.inf


def lufs(sig: np.ndarray, sr: int = SR) -> float:
    """ITU-R BS.1770 integrated loudness (K-weighting + 400 ms gated blocks).

    Do NOT estimate LUFS from peak amplitude -- peak and loudness diverge wildly
    between a click and a pad, which is exactly when the number matters.
    """
    # Stage 1: high-shelf. Stage 2: high-pass (RLB).
    sh_b, sh_a = signal.bilinear([1.0, 1.9952, 0.9952], [1.0, 0.9946, 0.0], fs=sr)
    hp_b, hp_a = signal.butter(2, 38.0 / (sr / 2), btype="high")
    k = signal.lfilter(hp_b, hp_a, signal.lfilter(sh_b, sh_a, sig.astype(np.float64)))

    block, hop = int(0.4 * sr), int(0.1 * sr)
    if k.size < block:
        return -70.0
    powers = [np.mean(k[i:i + block] ** 2) for i in range(0, k.size - block, hop)]
    loud = np.array([-0.691 + 10 * math.log10(max(p, 1e-12)) for p in powers])

    gated = loud[loud > -70.0]                       # absolute gate
    if gated.size == 0:
        return -70.0
    rel = gated.mean() - 10.0                        # relative gate
    final = gated[gated > rel]
    return float(final.mean() if final.size else gated.mean())


# ------------------------------------------------------- 1. registry sweep
def probe_registry(registry) -> list[str]:
    """Length / peak / clipping / edge-click / determinism, per declared budget.

    The critical design choice: compare each sound to ITS OWN declared peak_db,
    not to one global floor. A global -40 dB "audible" floor flagged all 14
    ambience beds (correctly quiet by design) and would have passed a foreground
    hit rendered 20 dB too soft.
    """
    issues: list[str] = []
    for name, spec in registry.items():
        sig = spec.render(sr=SR, seed=42)
        pk = peak_db(sig)
        bad: list[str] = []

        if sig.size == 0:
            bad.append("EMPTY")
        if (ms := 1000 * sig.size / SR) > spec.max_ms * 1.05:
            bad.append(f"TOO LONG {ms:.0f}>{spec.max_ms}ms")
        if np.max(np.abs(sig)) >= 0.999:
            bad.append("CLIPS")

        if pk < -80:
            bad.append("SILENT")
        elif abs(pk - spec.peak_db) > 1.5:
            bad.append(f"LEVEL {pk:.0f} want {spec.peak_db:.0f}")

        # Edge clicks: RELATIVE to this signal's own peak. An absolute 0.02
        # threshold passed a quiet sound ending at 0.0188 -- 15.6% of its own
        # peak, an obvious click.
        if sig.size and not spec.loop:
            pk_lin = max(np.max(np.abs(sig)), 1e-9)
            for label, v in (("start", sig[0]), ("end", sig[-1])):
                if abs(v) / pk_lin > 0.02:
                    bad.append(f"EDGE CLICK {label} {abs(v) / pk_lin:.1%} of peak")

        # Determinism is a testability requirement: without it, no regression
        # in this file is ever provable.
        if not np.array_equal(sig, spec.render(sr=SR, seed=42)):
            bad.append("NONDETERMINISTIC")

        if bad:
            issues.append(f"{name}: {', '.join(bad)}")
    return issues


# --------------------------------------------------------- 2. reverb decay
def probe_reverb(reverb_fn) -> list[str]:
    """A reverb tail must be AUDIBLE and must actually decay.

    'wet != dry' passes on a tail at -132 dBFS. That was a real bug: each pass of
    a serial loop rescaled the whole signal by (1-amount), shrinking the previous
    pass's tail. Parallel combs summed once fixed it: -132 dBFS/RT40 12ms became
    -46.8 dBFS/RT40 445ms.
    """
    imp = np.zeros(int(2.0 * SR), dtype=np.float32)
    imp[0] = 1.0
    wet = reverb_fn(imp, room=0.8, damp=0.3, mix=0.6, sr=SR)

    tail = wet[int(0.25 * SR):]
    tail_db = rms_db(tail)

    env = np.abs(signal.hilbert(wet.astype(np.float64)))
    pk = env.max()
    below = np.where(env < pk * 10 ** (-40 / 20))[0]
    rt40_ms = 1000 * below[0] / SR if below.size else 1000 * wet.size / SR

    issues = []
    if tail_db < -60:
        issues.append(f"reverb tail inaudible: {tail_db:.1f} dBFS")
    if rt40_ms < 80:
        issues.append(f"reverb does not decay: RT40 {rt40_ms:.0f} ms")
    print(f"  reverb tail {tail_db:.1f} dBFS, RT40 {rt40_ms:.0f} ms")
    return issues


# ------------------------------------------------------ 3. loop seam (tiled)
def probe_loop_seam(bed_fn, bars: int = 4) -> list[str]:
    """Measure the seam on a TILED loop, never on a single bed.

    sig[0] vs sig[-1] on an edge-faded bed is 0 by construction: it prints a
    perfect score whether or not looping works.

    Two real bugs this catches:
      1. Double-fading -- tiling already-faded material attenuates twice.
      2. Overlap shorter than the ADSR release. The final bar decays to -67 dBFS
         simply because no bar follows it; a 250ms crossfade splices copies right
         where one has faded to nothing, digging an 11 dB hole per repetition.
         Overlap 0.9s (> release) took the worst dip from -11.0 dB to -0.4 dB.
    """
    bed = bed_fn(bars=bars, sr=SR, seed=7, fade_edges=False)   # trap 1
    overlap = int(0.9 * SR)                                    # trap 2
    step = bed.size - overlap

    out = np.zeros(step * 3 + bed.size, dtype=np.float64)
    # Equal-power (sqrt) curves: linear crossfades dip at the midpoint, which on
    # a repeating bed is an audible pulse every single loop.
    t = np.linspace(0, 1, overlap, dtype=np.float64)
    fin, fout = np.sqrt(t), np.sqrt(1 - t)

    for i in range(4):
        seg, pos = bed.astype(np.float64).copy(), i * step
        if i > 0:
            seg[:overlap] *= fin
        if i < 3:
            seg[-overlap:] *= fout
        out[pos:pos + seg.size] += seg

    win, issues, worst = int(0.1 * SR), [], 0.0
    for i in range(1, 4):
        c = i * step
        at = rms_db(out[c - win // 2:c + win // 2])
        ref = rms_db(out[c - int(0.6 * SR):c - int(0.6 * SR) + win])
        dip = at - ref
        worst = min(worst, dip)
        if dip < -3.0:
            issues.append(f"seam {i}: {dip:+.1f} dB dip")
    print(f"  worst seam dip {worst:+.1f} dB")
    return issues


# ---------------------------------------------------- 4. ducking + loudness
def probe_duck(mix_fn, voice: np.ndarray, music: np.ndarray,
               windows: list[tuple[float, float]]) -> list[str]:
    """Verify duck DEPTH and duck TIMING, and that the voice actually leads.

    Requires stems: proving a duck works needs the music measured inside AND
    outside voice windows, which is impossible once everything is summed.

    Real failure this catches: a synthetic test voice at -26.5 LUFS -- same as
    the bed -- sat 2.7 dB BELOW the music it was meant to lead. The duck fired
    correctly for a voice nobody could hear. Normalise voice on the way in.
    """
    res = mix_fn(voice=voice, music=music, sr=SR, return_stems=True)
    m = res["stems"]["music"]
    issues = []

    inside = np.zeros(m.size, dtype=bool)
    for s, e in windows:
        inside[int(s * SR):int(e * SR)] = True
    if inside.all() or not inside.any():
        return ["duck probe needs both voiced and unvoiced regions"]

    depth = rms_db(m[inside]) - rms_db(m[~inside])
    if not -20 < depth < -4:
        issues.append(f"duck depth {depth:+.1f} dB outside -4..-20")

    v_lufs, m_lufs = lufs(res["stems"]["voice"]), lufs(m[inside])
    if v_lufs - m_lufs < 6.0:
        issues.append(f"voice only {v_lufs - m_lufs:+.1f} dB over ducked music")

    # Look-ahead: without it the first ~120 ms of every sentence competes with
    # music at full level -- exactly when the first consonant lands. Target is
    # most of the gain travel already spent AT onset.
    onset = int(windows[0][0] * SR)
    pre = rms_db(m[max(0, onset - int(0.3 * SR)):onset - int(0.05 * SR)])
    at = rms_db(m[onset:onset + int(0.03 * SR)])
    travel = (pre - at) / max(pre - rms_db(m[inside]), 1e-6)
    if travel < 0.4:
        issues.append(f"no look-ahead: only {travel:.0%} of duck travel at onset")

    print(f"  duck {depth:+.1f} dB | voice {v_lufs:.1f} LUFS vs music "
          f"{m_lufs:.1f} | {travel:.0%} travel at onset")
    return issues


# ------------------------------------------------- 5. mutation-test the probe
MUTATIONS = [
    ("silent",          "return np.zeros(int(0.3*sr), dtype=np.float32)"),
    ("overlong",        "return 0.5*np.ones(int(2.0*sr), dtype=np.float32)"),
    ("clipping",        "return 3.0*np.ones(int(0.2*sr), dtype=np.float32)"),
    ("edge click",      "<same body, fade removed>"),
    ("nondeterministic", "<default_rng() with no seed>"),
    ("level 12dB soft", "<render then *= 0.25>"),
]


def mutation_test(src_path, run_probe) -> None:
    """Confirm the probe FAILS on known-bad input, then restore and re-verify.

    'ALL PASS' over 112 sounds is a claim about the probe, not the sounds. A real
    run of exactly this caught 4 of 5 and exposed one blind spot (the edge-click
    check did not fire on an un-faded tone) -- 'PROBE HAS BLIND SPOTS' is far
    more useful than a green tick.

    Always restore in a finally: a harness that dies mid-run leaves the codebase
    broken, which is a worse outcome than the bug it was hunting.
    """
    original = src_path.read_text(encoding="utf-8")
    blind: list[str] = []
    try:
        for label, mutated in MUTATIONS:
            src_path.write_text(apply_mutation(original, mutated), encoding="utf-8")
            caught = "ISSUES" in run_probe()
            print(f"  {label:<18}{'caught' if caught else 'NOT CAUGHT -- BLIND SPOT'}")
            if not caught:
                blind.append(label)
    finally:
        src_path.write_text(original, encoding="utf-8")

    assert "ALL PASS" in run_probe(), "restore failed -- source left mutated!"
    print("PROBE HAS BLIND SPOTS: " + ", ".join(blind) if blind
          else "probe catches every injected defect")


def apply_mutation(original: str, mutated_body: str) -> str:  # project-specific
    raise NotImplementedError("swap one generator's body for `mutated_body`")


if __name__ == "__main__":
    from msf.audio.sfx import SFX_REGISTRY      # names are easy to guess wrong;
    from msf.audio.music import MUSIC_REGISTRY  # grep the module for its exports

    found = probe_registry({**SFX_REGISTRY, **MUSIC_REGISTRY})
    if found:
        print(f"ISSUES ({len(found)}):")
        for i in found:
            print("  -", i)
    else:
        print(f"ALL PASS ({len(SFX_REGISTRY) + len(MUSIC_REGISTRY)} sounds)")
    sys.exit(1 if found else 0)
