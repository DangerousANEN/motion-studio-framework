#!/usr/bin/env python3
"""Vet candidate voice-clone reference audio before registering it.

Answers the question that actually matters: *is this a live recording, or is it a
previous TTS output?* Cloning from synthetic audio recycles vocoder artifacts and
is the usual root cause of a clone that sounds "slightly robotic".

Usage:
    python check_reference_audio.py ref1.wav ref2.wav ...
    python check_reference_audio.py --registry assets/voices/voices.json

Requires: numpy, soundfile.
Exit code 1 if any candidate is flagged SYNTHETIC.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf

# Live mics sit around -35..-45 dB in pauses; vocoder output pauses are digital
# silence, typically below -70 dB. 60 dB is a wide, safe separator.
SYNTHETIC_FLOOR_DB = -70.0
GOOD_MIN_SEC, GOOD_MAX_SEC = 8.0, 15.0


def to_db(x: float) -> float:
    return 20.0 * np.log10(max(float(x), 1e-12))


def analyze(path: str) -> dict:
    wav, sr = sf.read(path)
    channels = 1 if wav.ndim == 1 else wav.shape[1]
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    amp = np.abs(wav.astype(np.float32))
    dur = len(amp) / sr

    # Noise floor: 5th-percentile of 20 ms frame peaks == the quiet parts.
    fl = max(int(sr * 0.02), 1)
    usable = len(amp) // fl * fl
    frames = amp[:usable].reshape(-1, fl).max(axis=1) if usable else amp
    floor_db = to_db(np.percentile(frames, 5))
    peak_db = to_db(amp.max())

    # Non-zero final sample -> audible clipped cut-off once clips concatenate.
    tail = to_db(np.abs(amp[-int(sr * 0.005):]).max()) if len(amp) > sr * 0.005 else peak_db

    verdict, notes = "LIVE", []
    if floor_db <= SYNTHETIC_FLOOR_DB:
        verdict = "SYNTHETIC"
        notes.append(f"noise floor {floor_db:.1f} dB = digital silence in pauses")
    if sr == 24000 and channels == 1:
        notes.append("24 kHz mono is Qwen3-TTS native output format")
        if verdict == "LIVE":
            verdict = "SUSPECT"
    if not (GOOD_MIN_SEC <= dur <= GOOD_MAX_SEC):
        notes.append(f"duration {dur:.1f}s outside {GOOD_MIN_SEC:g}-{GOOD_MAX_SEC:g}s target")
    if tail > -40.0:
        notes.append(f"tail ends at {tail:.1f} dB - needs afade out")

    return dict(path=path, dur=dur, sr=sr, ch=channels, peak_db=peak_db,
                floor_db=floor_db, snr_db=peak_db - floor_db,
                verdict=verdict, notes=notes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--registry", help="voices.json to audit (reads each ref_audio)")
    args = ap.parse_args()

    paths = list(args.paths)
    if args.registry:
        with open(args.registry, encoding="utf-8") as fh:
            reg = json.load(fh)
        for key, entry in reg.items():
            if key.startswith("_") or not isinstance(entry, dict):
                continue
            ref = entry.get("ref_audio")
            if ref:
                paths.append(ref)
    if not paths:
        ap.error("pass audio paths or --registry")

    print(f"{'file':<34}{'dur':>7}{'sr':>7}{'ch':>4}{'peak':>8}{'floor':>8}{'SNR':>7}  verdict")
    print("-" * 90)
    bad = False
    for p in paths:
        if not os.path.exists(p):
            print(f"{os.path.basename(p):<34}{'MISSING':>41}")
            bad = True
            continue
        r = analyze(p)
        print(f"{os.path.basename(p):<34}{r['dur']:7.2f}{r['sr']:7d}{r['ch']:4d}"
              f"{r['peak_db']:8.1f}{r['floor_db']:8.1f}{r['snr_db']:7.1f}  {r['verdict']}")
        for n in r["notes"]:
            print(f"{'':<34}  - {n}")
        if r["verdict"] == "SYNTHETIC":
            bad = True

    if bad:
        print("\nFlagged entries: do NOT clone from SYNTHETIC audio - artifacts compound.")
        print("Record a fresh 8-15s live sample (clean speech, no music/reverb) instead.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
