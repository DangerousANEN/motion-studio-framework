"""Voice-over an already-authored VideoSpec JSON in place.

WHY THIS EXISTS
---------------
There are two ways to get a video out of MSF and they disagree about audio:

  (A) the LangGraph pipeline -- node_voice_synthesis synthesizes one wav per
      scene, copies it into remotion/public/ and writes `audio_url` onto every
      scene, so <Audio> mounts and the render has sound;

  (B) `npx remotion render ... --props=my_spec.json` -- renders exactly what the
      JSON says. A hand-authored spec has no `audioUrl`, so Main.tsx never mounts
      an <Audio> element and the mp4 ships with a silent AAC track (-91 dB).

Path (B) is the convenient one for iterating on a script, and it produced three
finished-looking videos with no narration at all. This tool closes that gap: it
takes a spec authored by hand, speaks every scene, and returns a spec that
renders WITH sound through the plain Remotion CLI.

WHAT IT DOES
------------
1. Reads the spec, requires a `text` on every scene (that is the narration --
   a scene with no text cannot be voiced, and silently skipping it is how you
   end up with a video that is 70% silent).
2. Synthesizes each scene with Qwen3-TTS 1.7B in ICL mode, so the reference
   speaker's prosody carries over rather than just their timbre. The model is a
   module-level singleton: the first call pays ~60s of load, the rest are cheap,
   so voicing N scenes costs far less than N x 60s.
3. Copies each wav into remotion/public/ (staticFile() resolves there) and sets
   `audioUrl` on the scene.
4. Optionally retimes each scene to its narration length. This is on by default:
   a 90-frame scene carrying 4 seconds of speech cuts the voice off mid-word.
   Pass --keep-timing to preserve the authored durations exactly.

USAGE
-----
  python tools/voice_spec.py scripts_tg/script2_prompt_unlock.json
  python tools/voice_spec.py spec.json --voice voice_2 --out spec.voiced.json
  python tools/voice_spec.py spec.json --keep-timing        # trust authored frames

Then render normally:
  cd remotion && npx remotion render src/index.ts Main out.mp4 --props=../spec.voiced.json
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import wave
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PUBLIC_DIR = REPO_ROOT / "remotion" / "public"

# Voice-over needs air on both sides of a scene cut: speech that starts on the
# very first frame sounds clipped, and speech that ends exactly on the last frame
# gets swallowed by the next scene's audio. 12 frames = 200ms at 60fps.
PAD_FRAMES = 12
MIN_SCENE_FRAMES = 60


def _wav_duration(path: str) -> float:
    with wave.open(path) as w:
        return w.getnframes() / float(w.getframerate())


def voice_spec(
    spec_path: Path,
    out_path: Path,
    voice: str | None,
    retime: bool,
    fps: int | None = None,
) -> Dict[str, Any]:
    from msf.skills_bridge.qwen3_tts import describe_reference, resolve_voice
    from msf.orchestrators.remotion_runner import _synthesize_cloned_audio

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    scenes: List[Dict[str, Any]] = spec.get("scenes") or []
    if not scenes:
        raise ValueError(f"{spec_path.name}: spec has no scenes")

    fps = fps or int(spec.get("fps") or 60)

    # Fail before spending a minute loading the model: a scene with no narration
    # cannot be voiced, and a half-voiced video is worse than a clear error.
    missing = [i for i, sc in enumerate(scenes) if not (sc.get("text") or "").strip()]
    if missing:
        raise ValueError(
            f"{spec_path.name}: scenes {missing} have no `text` to speak. "
            "Every scene needs narration, or the render is partly silent."
        )

    ref_audio, ref_text = resolve_voice(voice)
    info = describe_reference(voice)
    print(f"[voice] {info['mode']} | ref={Path(ref_audio).name} "
          f"dur={info.get('duration_sec')}s sr={info.get('sample_rate')}")
    if not info.get("has_ref_text"):
        print("[voice] WARNING: reference has no transcript -> timbre only, flat prosody.")

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    audio_dir = out_path.parent / f"{out_path.stem}_audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    total_synth = 0.0
    total_speech = 0.0

    for i, sc in enumerate(scenes):
        text = sc["text"].strip()
        t0 = time.time()
        wav_path, dur = _synthesize_cloned_audio(text, ref_audio, ref_text)
        synth_s = time.time() - t0
        total_synth += synth_s
        total_speech += dur

        # Name the wav after the spec so several voiced specs can coexist in
        # public/ without overwriting each other's tracks.
        name = f"{out_path.stem}_{i:02d}.wav"
        dst = audio_dir / name
        shutil.copy(wav_path, str(dst))
        shutil.copy(str(dst), str(PUBLIC_DIR / name))

        sc["audioUrl"] = name

        if retime:
            needed = int(round(dur * fps)) + PAD_FRAMES
            authored = int(sc.get("durationInFrames") or 0)
            sc["durationInFrames"] = max(needed, MIN_SCENE_FRAMES)
            flag = "" if sc["durationInFrames"] == authored else f" (was {authored})"
            print(f"[{i:02d}] {synth_s:5.1f}s synth | {dur:4.2f}s speech "
                  f"-> {sc['durationInFrames']}f{flag} | {text[:44]}")
        else:
            print(f"[{i:02d}] {synth_s:5.1f}s synth | {dur:4.2f}s speech "
                  f"| {sc.get('durationInFrames')}f kept | {text[:44]}")

    # A root-level audioUrl would play ON TOP of the per-scene tracks -- Main.tsx
    # mounts both -- so strip it once scenes carry their own narration.
    if spec.pop("audioUrl", None) is not None:
        print("[voice] dropped root audioUrl: per-scene tracks would double up with it")

    out_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[voice] {len(scenes)} scenes | synth {total_synth:.1f}s "
          f"for {total_speech:.1f}s speech | wavs -> {audio_dir}")
    print(f"[voice] spec -> {out_path}")
    return spec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="path to the VideoSpec JSON to voice")
    ap.add_argument("--voice", default=None,
                    help="registry key from assets/voices/voices.json (default: voice_3)")
    ap.add_argument("--out", default=None,
                    help="output spec path (default: <spec>.voiced.json)")
    ap.add_argument("--keep-timing", action="store_true",
                    help="keep authored durationInFrames instead of fitting them to speech")
    ap.add_argument("--fps", type=int, default=None, help="override spec fps")
    args = ap.parse_args()

    spec_path = Path(args.spec).resolve()
    if not spec_path.is_file():
        print(f"error: {spec_path} not found", file=sys.stderr)
        return 2

    out_path = Path(args.out).resolve() if args.out else spec_path.with_suffix(".voiced.json")

    try:
        voice_spec(spec_path, out_path, args.voice, retime=not args.keep_timing,
                   fps=args.fps)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
