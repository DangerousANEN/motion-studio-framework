"""Build the full soundtrack for a spec: voice + music bed + SFX, ducked.

WHY THIS EXISTS SEPARATELY FROM node_voice_synthesis
----------------------------------------------------
`node_voice_synthesis` writes one wav per scene and points each scene's
`audioUrl` at it. That gives speech and nothing else: `msf/audio/` ships a
mixer, ten music beds and ~70 SFX, but NOTHING in the graph ever imported it, so
every video shipped as dry narration over silence.

Mixing cannot be done per scene. A music bed that restarts on every cut is
audibly wrong, and a duck envelope needs the whole voice track to decide where to
dip. So the soundtrack is ONE continuous wav for the entire video, mounted as the
spec's ROOT `audioUrl`, and the per-scene `audioUrl`s are dropped.

That is also why `validate_spec` rejects a spec carrying both: Remotion mounts
`<Audio>` for the root AND for each scene, so leaving both in place plays the
voice twice — once dry, once inside the mix — a comb-filtered mess that still
measures as perfectly healthy audio.

CUE TIMING
----------
Scene start times must account for transitions OVERLAPPING their neighbours: a
20-frame transition before scene N means N starts 20 frames earlier than the
running sum of durations suggests. This mirrors getTransitionPlan() in
remotion/src/lib/transitions.ts. Getting it wrong walks every cue progressively
out of sync — on an 8-scene spec the last hit landed 2.5s late.
"""
from __future__ import annotations

import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from msf.audio.mixer import SR, Timeline, measure_lufs, write_wav
from msf.audio.music import MUSIC_REGISTRY
from msf.audio.sfx import SFX_REGISTRY

# Registers the extra ~60 sounds. Without this import only the core set exists
# and every accent name below falls back, which is not an error but is a much
# duller mix.
import msf.audio.sfx_extra  # noqa: F401

SOUNDTRACK_NAME = "soundtrack.wav"

# Default accents, in the order scenes tend to want them: something to open on,
# then neutral motion sounds. Every name is checked against the registry before
# use — a missing name must degrade, not crash a render at the audio stage.
DEFAULT_ACCENTS = (
    "riser_short",
    "send_swoosh",
    "sync_sweep",
    "glass_tap",
    "success_chime",
    "impact_hard",
    "coin_stack",
    "card_swipe",
)


def read_wav_mono(path: str | Path, target_sr: int = SR) -> np.ndarray:
    """Read a PCM wav as float32 mono at `target_sr`.

    The TTS writes 16-bit mono at 24 kHz while the mixer runs at 48 kHz, so a
    resample is mandatory: dropping the raw samples into a 48 kHz timeline plays
    the voice at half speed. Linear interpolation is enough for a 2x integer-ish
    ratio on speech and keeps this dependency-free.
    """
    with wave.open(str(path), "rb") as w:
        n_ch = w.getnchannels()
        width = w.getsampwidth()
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())

    if width != 2:
        raise ValueError(f"{path}: expected 16-bit PCM, got {width * 8}-bit")

    sig = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if n_ch > 1:
        sig = sig.reshape(-1, n_ch).mean(axis=1)

    if sr != target_sr:
        n_out = int(round(len(sig) * target_sr / sr))
        if n_out <= 0:
            return np.zeros(0, dtype=np.float32)
        src_idx = np.linspace(0.0, len(sig) - 1, n_out)
        sig = np.interp(src_idx, np.arange(len(sig)), sig).astype(np.float32)

    return sig


def scene_start_times(scenes: Sequence[Dict[str, Any]], fps: int) -> tuple[list[float], float]:
    """Scene start times in seconds, and the total duration.

    Transitions overlap, so a transition before scene N pulls N earlier. Mirrors
    getTransitionPlan() in remotion/src/lib/transitions.ts.
    """
    starts: list[float] = []
    t = 0.0
    for sc in scenes:
        tr = sc.get("transition") or sc.get("transition_in")
        if isinstance(tr, dict):
            overlap = tr.get("durationInFrames", tr.get("duration_in_frames", 30))
            t -= float(overlap) / fps
        starts.append(max(0.0, t))
        frames = sc.get("durationInFrames", sc.get("duration_in_frames", 0))
        t += float(frames) / fps
    return starts, t


def pick_bed(requested: Optional[str]) -> Optional[str]:
    """Resolve a music bed name, falling back rather than raising.

    A typo'd bed name must not kill a render that already cost minutes of TTS.
    """
    if requested and requested in MUSIC_REGISTRY:
        return requested
    if requested:
        print(f"[audio] unknown music bed {requested!r}; "
              f"available: {sorted(MUSIC_REGISTRY)}")
    if "minimal_pulse" in MUSIC_REGISTRY:
        return "minimal_pulse"
    return sorted(MUSIC_REGISTRY)[0] if MUSIC_REGISTRY else None


def build_soundtrack(
    scenes: Sequence[Dict[str, Any]],
    voice_wavs: Sequence[str],
    fps: int,
    out_path: str | Path,
    music_bed: Optional[str] = None,
    sfx_names: Optional[Sequence[str]] = None,
    custom_music_wav: Optional[str | Path] = None,
    custom_sfx_wavs: Optional[Sequence[str | Path]] = None,
    sfx_gain_db: float = -3.0,
    music: bool = True,
    sfx: bool = True,
) -> Dict[str, Any]:
    """Mix voice + bed + accents into one wav and return the measurements.

    Returns a report rather than just a path: a soundtrack is not verifiable from
    its own existence, and the caller (node_soundtrack, or a test) needs the
    numbers to assert on — total loudness, per-scene voice presence, and the duck
    depth measured from the stems.
    """
    starts, total = scene_start_times(scenes, fps)
    if total <= 0:
        raise ValueError("cannot build a soundtrack for a zero-length spec")

    tl = Timeline()

    # ---- voice: one clip per scene, placed at that scene's start
    voice_report: list[dict[str, Any]] = []
    for i, (start, wav) in enumerate(zip(starts, voice_wavs)):
        if not wav or not Path(wav).exists():
            voice_report.append({"scene": i, "at": start, "wav": None, "seconds": 0.0})
            continue
        samples = read_wav_mono(wav)
        tl.add_voice(samples, start)
        voice_report.append(
            {"scene": i, "at": round(start, 3), "wav": Path(wav).name,
             "seconds": round(len(samples) / SR, 3)}
        )

    # ---- music: one continuous bed, looped to length. A standardised user WAV
    # is treated as a first-class bed and therefore receives identical loudness
    # normalisation and voice ducking inside Timeline.render().
    custom_music = Path(custom_music_wav) if custom_music_wav else None
    bed = pick_bed(music_bed) if music and not (custom_music and custom_music.is_file()) else None
    music_label: Optional[str] = bed
    if music and custom_music and custom_music.is_file():
        tl.add_music(read_wav_mono(custom_music), 0.0, total)
        music_label = f"user:{custom_music.name}"
    elif bed:
        tl.add_music(bed, 0.0, total)

    # ---- sfx: one accent per scene start, a hair EARLY so it reads as causing
    # the cut rather than reacting to it
    placed: list[dict[str, Any]] = []
    if sfx:
        custom_paths = [Path(path) for path in (custom_sfx_wavs or []) if Path(path).is_file()]
        if custom_paths:
            pool: list[str | np.ndarray] = [read_wav_mono(path) for path in custom_paths]
            labels = [f"user:{path.name}" for path in custom_paths]
        else:
            wanted = list(sfx_names) if sfx_names else list(DEFAULT_ACCENTS)
            pool = [n for n in wanted if n in SFX_REGISTRY]
            missing = [n for n in wanted if n not in SFX_REGISTRY]
            if missing:
                print(f"[audio] unknown sfx dropped: {missing}")
            if not pool:
                pool = sorted(SFX_REGISTRY)[:8]
            labels = [str(item) for item in pool]
        if pool:
            for i, start in enumerate(starts):
                cue = pool[i % len(pool)]
                at = max(0.0, start - 0.04)
                tl.add_sfx(cue, at, gain_db=sfx_gain_db)
                placed.append({"scene": i, "sfx": labels[i % len(labels)], "at": round(at, 3)})

    result = tl.render(total)
    mix = result["mix"]

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_wav(str(out_path), mix)

    # ---- measurements: prove the mix, do not assert it
    peak = float(np.max(np.abs(mix))) if mix.size else 0.0
    voice_stem = result["voice"]
    music_pre = result["music_predduck"]
    music_post = result["music"]

    # Duck depth: compare the bed's level where voice is active against where it
    # is not. Reading the envelope alone would only prove we computed one.
    env = result["duck_envelope"]
    active = env < 0.99
    duck_db = None
    if active.any() and (~active).any() and music_pre.any():
        loud_in = measure_lufs(music_post[active], SR)
        loud_out = measure_lufs(music_post[~active], SR)
        duck_db = round(loud_out - loud_in, 2)

    report = {
        "path": str(out_path),
        "duration_sec": round(len(mix) / SR, 3),
        "lufs": round(measure_lufs(mix), 2),
        "true_peak_dbfs": round(20 * float(np.log10(peak)), 2) if peak > 0 else None,
        "clipping": bool(peak >= 1.0),
        "music_bed": music_label,
        "sfx": placed,
        "voice": voice_report,
        "voice_lufs": round(measure_lufs(voice_stem), 2) if voice_stem.any() else None,
        "duck_depth_db": duck_db,
        "scene_starts": [round(s, 3) for s in starts],
    }
    return report
