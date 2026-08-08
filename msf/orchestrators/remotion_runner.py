"""MSF Remotion Runner — text → Qwen3 cloned voice → Remotion render → mastered MP4.
Uses single source of truth msf.spec for spec generation and passes --props to Remotion.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from msf.spec import Scene, build_spec, frames_for, validate_spec, FPS, WIDTH, HEIGHT
from msf.engines.audio.mastering import master_video_audio

REPO_ROOT = Path(__file__).resolve().parents[2]
REMOTION_DIR = REPO_ROOT / "remotion"
PUBLIC_DIR = REMOTION_DIR / "public"
DEFAULT_OUTPUT = REPO_ROOT / "output" / "remotion"

# Vertical shorts live on scene changes. A scene that sits still for 10+ seconds
# kills retention, so we target one sentence (or clause) per scene and only merge
# very short fragments. MAX_WORDS_PER_SCENE is a hard ceiling, not a target.
MAX_WORDS_PER_SCENE = 10
MIN_WORDS_PER_SCENE = 4
WORD_LIMIT_PER_SCENE = MAX_WORDS_PER_SCENE  # backwards-compat alias

_MODULE_MODEL_CACHE = {}


def _get_qwen3_model():
    """Module-level singleton for Qwen3-TTS 1.7B-Base (zero-shot clone)."""
    from msf.skills_bridge.qwen3_tts import get_qwen3_clone_model
    return get_qwen3_clone_model()


def _split_into_scenes(text: str, max_words: int = MAX_WORDS_PER_SCENE) -> list[dict]:
    """Split narration into short, punchy scenes — one sentence/clause each.

    Strategy:
      1. Split on sentence terminators (. ! ? …).
      2. A sentence longer than `max_words` is split further on clause boundaries
         (commas, dashes, colons, semicolons) so no single card is a wall of text.
      3. Fragments shorter than MIN_WORDS_PER_SCENE are merged into the neighbour,
         because a 1-word scene reads as a glitch.

    Returns a list of {"text": ...} dicts, always at least one when text is non-empty.
    """
    text = (text or "").strip()
    if not text:
        return []

    def _hard_wrap(chunk: str) -> list[str]:
        """Last resort for a clause with no internal punctuation."""
        cw = chunk.split()
        if len(cw) <= max_words:
            return [chunk]
        return [" ".join(cw[i:i + max_words]) for i in range(0, len(cw), max_words)]

    sentences = [s for s in re.split(r'(?<=[.!?…])\s+', text) if s.strip()]

    chunks: list[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence.split()) <= max_words:
            chunks.append(sentence)
            continue

        # Too long for one card: break on clause boundaries, keeping the delimiter.
        parts = [p.strip() for p in re.split(r'(?<=[,;:—–])\s+', sentence) if p.strip()]

        buf: list[str] = []
        for part in parts:
            part_words = part.split()
            if buf and len(buf) + len(part_words) > max_words:
                chunks.extend(_hard_wrap(" ".join(buf)))
                buf = part_words
            else:
                buf.extend(part_words)
        if buf:
            chunks.extend(_hard_wrap(" ".join(buf)))

    # Merge runt fragments into the previous scene so we never show a 1-word card.
    merged: list[str] = []
    for chunk in chunks:
        if merged and len(chunk.split()) < MIN_WORDS_PER_SCENE:
            candidate = f"{merged[-1]} {chunk}"
            if len(candidate.split()) <= max_words + MIN_WORDS_PER_SCENE:
                merged[-1] = candidate
                continue
        merged.append(chunk)

    return [{"text": c} for c in merged]


def _synthesize_cloned_audio(
    text: str, ref_audio: str, ref_text: str | None = None
) -> tuple[str, float]:
    """Return (wav_path, duration_seconds) using Qwen3 1.7B-Base zero-shot.

    Passing `ref_text` keeps ICL mode on, which transfers the reference speaker's
    prosody. Without it the model only copies timbre and reads flat.
    """
    from msf.skills_bridge.qwen3_tts import synthesize_voice_clone
    return synthesize_voice_clone(
        text=text, ref_audio=ref_audio, ref_text=ref_text, language="Russian"
    )


def render_remotion_video(spec_dict: dict, out_mp4: str) -> str:
    """Render Remotion composition using spec_dict passed via --props.

    Raises RuntimeError with stderr output if render fails.
    """
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    # Fail fast: a broken spec must raise here, not silently render a placeholder.
    validate_spec(spec_dict)

    props_path = (PUBLIC_DIR / "props.json").resolve()
    spec_json_path = (PUBLIC_DIR / "video-spec.json").resolve()

    json_str = json.dumps(spec_dict, ensure_ascii=False, indent=2)
    props_path.write_text(json_str, encoding="utf-8")
    spec_json_path.write_text(json_str, encoding="utf-8")

    out_path = Path(out_mp4).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
    cmd = [
        npx_cmd,
        "remotion",
        "render",
        "src/index.ts",
        "Main",
        str(out_path),
        f"--props={str(props_path)}",
        "--log=verbose",
        "--concurrency=4",
    ]

    res = subprocess.run(
        cmd,
        cwd=str(REMOTION_DIR),
        shell=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if res.returncode != 0:
        stderr_tail = res.stderr[-4000:] if res.stderr else "No stderr output."
        stdout_tail = res.stdout[-1000:] if res.stdout else "No stdout output."
        raise RuntimeError(
            f"Remotion render failed with code {res.returncode}.\n"
            f"--- STDERR (last 4000 chars) ---\n{stderr_tail}\n"
            f"--- STDOUT (last 1000 chars) ---\n{stdout_tail}"
        )

    return str(out_path)


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

    raw_scenes = _split_into_scenes(text)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    scenes: list[Scene] = []
    accent_color_hex = "#E6C475" if accent == "gold" else accent

    for i, sc in enumerate(raw_scenes):
        wav, dur = _synthesize_cloned_audio(sc["text"], reference_audio)
        scene_wav_name = f"scene_{i:02d}.wav"
        scene_wav_dest = audio_dir / scene_wav_name
        shutil.copy(wav, scene_wav_dest)

        # Copy into remotion public dir so staticFile() resolves it
        pub_wav = PUBLIC_DIR / scene_wav_name
        shutil.copy(scene_wav_dest, pub_wav)

        dur_frames = frames_for(dur, FPS)
        scenes.append(
            Scene(
                id=f"scene-{i+1}",
                duration_in_frames=dur_frames,
                preset=preset,
                text=sc["text"],
                accent_color=accent_color_hex,
                audio_url=scene_wav_name,
            )
        )

    spec_dict = build_spec(scenes, fps=FPS, width=WIDTH, height=HEIGHT)
    raw_mp4 = str(output_dir / (Path(output_path).name if output_path else f"msf_{preset.lower()}_raw.mp4"))
    final_mp4 = str(output_dir / (Path(output_path).name if output_path else f"msf_{preset.lower()}.mp4"))

    render_remotion_video(spec_dict, raw_mp4)
    master_video_audio(raw_mp4, final_mp4)

    return final_mp4


if __name__ == "__main__":
    demo = (
        "Ищете лучшие оупен сорс решения в области искусственного интеллекта? "
        "Канал точка ЛЛM Хабс — ваш главный источник передовых нейросетей. "
        "Глубокие разборы архитектур, свежие бенчмарки моделей и научные статьи."
    )
    print(create_video(demo, preset="HeroKinetic"))
