"""MSF Remotion Runner — text → Qwen3 cloned voice → Remotion render → mastered MP4.

Public API:
    from msf.orchestrators.remotion_runner import create_video
    mp4_path = create_video(text="...", preset="HeroKinetic",
                            reference_audio="path/to/ref.mp3")
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
REMOTION_DIR = REPO_ROOT / "remotion"
PUBLIC_DIR = REMOTION_DIR / "public"
DEFAULT_OUTPUT = REPO_ROOT / "output" / "remotion"

WORD_LIMIT_PER_SCENE = 28
FPS = 30
SIZE = (1080, 1920)

_MODULE_MODEL_CACHE = {}


def _get_qwen3_model():
    """Module-level singleton for Qwen3-TTS 1.7B-Base (zero-shot clone)."""
    from msf.skills_bridge.qwen3_tts import get_qwen3_clone_model
    return get_qwen3_clone_model()


def _split_into_scenes(text: str, max_words: int = WORD_LIMIT_PER_SCENE) -> list[dict]:
    """Auto-split long narration into bite-size scenes (one per sentence-ish chunk)."""
    sentences = re.split(r'(?<=[.!?…])\s+', text.strip())
    scenes, bucket, counter = [], [], 0
    for s in sentences:
        words = s.split()
        if counter + len(words) > max_words and bucket:
            scenes.append({"text": " ".join(bucket)})
            bucket, counter = [], 0
        bucket.append(s)
        counter += len(words)
    if bucket:
        scenes.append({"text": " ".join(bucket)})
    return scenes


def _synthesize_cloned_audio(text: str, ref_audio: str) -> tuple[str, float]:
    """Return (wav_path, duration_seconds) using Qwen3 1.7B-Base zero-shot."""
    from msf.skills_bridge.qwen3_tts import synthesize_voice_clone
    return synthesize_voice_clone(text=text, ref_audio=ref_audio, language="Russian")


def create_video(
    text: str,
    preset: str = "HeroKinetic",
    reference_audio: str = r"C:/Users/ANEN/qwen3_1.7B_clone_test.wav",
    output_path: Optional[str] = None,
    accent: str = "gold",
) -> str:
    """One-call API: narration text → mastered MP4 (1080x1920 vertical short)."""
    output_dir = Path(output_path).parent if output_path else DEFAULT_OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    scenes = _split_into_scenes(text)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    scene_specs = []
    audio_paths = []
    for i, sc in enumerate(scenes):
        wav, dur = _synthesize_cloned_audio(sc["text"], reference_audio)
        scene_wav = audio_dir / f"scene_{i:02d}.wav"
        os.replace(wav, scene_wav)
        audio_paths.append(str(scene_wav))
        scene_specs.append({
            "preset": preset,
            "text": sc["text"],
            "sub_text": "",
            "accent": accent,
            "audio_file": f"scene_{i:02d}.wav",
            "duration_in_frames": max(30, int(dur * FPS)),
        })

    spec = {
        "fps": FPS,
        "width": SIZE[0],
        "height": SIZE[1],
        "scenes": scene_specs,
    }
    (PUBLIC_DIR / "video-spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    # Copy audio files into remotion public dir so staticFile() works
    for wav in audio_paths:
        tgt = PUBLIC_DIR / Path(wav).name
        if not tgt.exists():
            import shutil
            shutil.copy(wav, tgt)

    out_mp4 = str(output_dir / (Path(output_path).name if output_path else f"msf_{preset.lower()}.mp4"))

    subprocess.run(
        ["npx.cmd", "remotion", "render", "src/index.ts", "Main", out_mp4],
        cwd=str(REMOTION_DIR), check=True, shell=True,
    )

    return out_mp4


if __name__ == "__main__":
    demo = ("Ищете лучшие оупен сорс решения в области искусственного интеллекта? "
            "Канал точка ЛЛМ Хабс — ваш главный источник передовых нейросетей. "
            "Глубокие разборы архитектур, свежие бенчмарки моделей и научные статьи.")
    print(create_video(demo, preset="HeroKinetic"))
