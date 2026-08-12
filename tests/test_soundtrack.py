"""Soundtrack mixing: resampling, cue timing, and the double-audio guard.

These are the failures that shipped silently before this module existed:
  * the graph never imported msf.audio at all, so every video was dry narration
  * TTS writes 24 kHz, the mixer runs at 48 kHz — dropping raw samples into the
    timeline plays the voice at half speed
  * transitions overlap, so naively summing durations walks every cue late
  * a root audioUrl plus per-scene audioUrls makes Remotion play the voice twice
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from msf.audio.mixer import SR
from msf.audio.soundtrack import (
    build_soundtrack,
    pick_bed,
    read_wav_mono,
    scene_start_times,
)
from msf.spec import Scene, build_spec, validate_spec


def _write_wav(path: Path, seconds: float, sr: int, freq: float = 220.0) -> Path:
    t = np.arange(int(seconds * sr)) / sr
    sig = (0.4 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    pcm = (np.clip(sig, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm)
    return path


def test_read_wav_mono_resamples_preserving_duration(tmp_path: Path) -> None:
    """A 24 kHz clip must come back at 48 kHz with the SAME duration.

    Without the resample the mixer plays TTS output at half speed.
    """
    src = _write_wav(tmp_path / "v.wav", 1.5, 24_000)
    out = read_wav_mono(src)
    assert len(out) == pytest.approx(1.5 * SR, rel=0.001)


def test_scene_starts_account_for_transition_overlap() -> None:
    """A transition before scene N pulls N earlier — it does not add time."""
    scenes = [
        {"durationInFrames": 180},
        {"durationInFrames": 180, "transition": {"durationInFrames": 24}},
        {"durationInFrames": 180, "transition": {"durationInFrames": 24}},
    ]
    starts, total = scene_start_times(scenes, 60)
    # 180/60 = 3.0s per scene, each transition steals 24/60 = 0.4s
    assert starts == pytest.approx([0.0, 2.6, 5.2])
    # Total is the last start plus its own length, NOT the naive sum: 5.2 + 3.0.
    assert total == pytest.approx(8.2)


def test_scene_starts_accepts_snake_case_keys() -> None:
    """Python-side specs use snake_case; both spellings must work."""
    scenes = [
        {"duration_in_frames": 120},
        {"duration_in_frames": 120, "transition": {"duration_in_frames": 30}},
    ]
    starts, total = scene_start_times(scenes, 60)
    assert starts == pytest.approx([0.0, 1.5])
    assert total == pytest.approx(3.5)


def test_pick_bed_falls_back_instead_of_raising() -> None:
    """A typo must not kill a render that already paid for minutes of TTS."""
    assert pick_bed("definitely_not_a_bed") is not None
    assert pick_bed(None) is not None


def test_soundtrack_is_audible_in_voice_windows_and_between_them(tmp_path: Path) -> None:
    """The mix must carry voice under speech AND a bed in the gaps."""
    voices = [
        _write_wav(tmp_path / f"v{i}.wav", 1.0, 24_000, freq=200 + 60 * i)
        for i in range(3)
    ]
    scenes = [{"durationInFrames": 120} for _ in range(3)]  # 2s each at 60fps
    report = build_soundtrack(
        scenes, [str(v) for v in voices], 60, tmp_path / "mix.wav"
    )

    assert report["duration_sec"] == pytest.approx(6.0, abs=0.01)
    assert not report["clipping"]
    assert report["music_bed"] is not None
    assert len(report["sfx"]) == 3
    assert [v["scene"] for v in report["voice"]] == [0, 1, 2]

    sig = read_wav_mono(tmp_path / "mix.wav")
    # Under speech (0.2-0.9s) and in the gap between clips (1.4-1.8s) the track
    # must be non-silent. Digital silence would be ~1e-5 or lower.
    speech = sig[int(0.2 * SR) : int(0.9 * SR)]
    gap = sig[int(1.4 * SR) : int(1.8 * SR)]
    assert float(np.max(np.abs(speech))) > 0.01
    assert float(np.max(np.abs(gap))) > 1e-3


def test_soundtrack_ducks_the_bed_under_voice(tmp_path: Path) -> None:
    """The bed must measurably dip while speech plays.

    The configured depth is DUCK_DEPTH_DB (6 dB), but the MEASURED depth is
    lower on a short clip: the 120ms attack and 400ms release ramps are counted
    as "active" by the envelope, and on a 1.2s voice inside a 4s window those
    ramps are a large fraction of the active region, averaging the dip upward.
    Measured 2.65 dB here versus 7.39 dB on a real 4-scene 10.8s mix. So this
    asserts the duck is real and directional, not a specific number.
    """
    voices = [_write_wav(tmp_path / "v0.wav", 1.2, 24_000)]
    scenes = [{"durationInFrames": 240}]  # 4s, so there is a long voice-free tail
    report = build_soundtrack(
        scenes, [str(voices[0])], 60, tmp_path / "mix.wav"
    )
    assert report["duck_depth_db"] is not None
    assert report["duck_depth_db"] > 2.0


def test_soundtrack_can_be_voice_only(tmp_path: Path) -> None:
    """music=False, sfx=False leaves speech alone (used by opt-out specs)."""
    voices = [_write_wav(tmp_path / "v0.wav", 1.0, 24_000)]
    report = build_soundtrack(
        [{"durationInFrames": 120}],
        [str(voices[0])],
        60,
        tmp_path / "mix.wav",
        music=False,
        sfx=False,
    )
    assert report["music_bed"] is None
    assert report["sfx"] == []
    assert report["voice"][0]["seconds"] == pytest.approx(1.0, abs=0.01)


def test_root_and_per_scene_audio_together_is_rejected() -> None:
    """Remotion mounts both, so the voice would play against a copy of itself."""
    ok = build_spec(
        [Scene(id="a", preset="HeroKinetic", duration_in_frames=120, text="раз")],
        audio_url="soundtrack.wav",
    )
    validate_spec(ok)  # root-only is fine

    clash = build_spec(
        [
            Scene(
                id="a",
                preset="HeroKinetic",
                duration_in_frames=120,
                text="раз",
                audio_url="scene_00.wav",
            )
        ],
        audio_url="soundtrack.wav",
    )
    with pytest.raises(ValueError, match="root 'audioUrl'"):
        validate_spec(clash)


def test_zero_length_spec_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="zero-length"):
        build_soundtrack([], [], 60, tmp_path / "mix.wav")
