#!/usr/bin/env python3
"""Generates a high-converting promotional Short (1080x1920) for the Telegram channel @llm_hubs (.llm hubs)
using Motion Studio Framework and Qwen3-TTS 1.7B Zero-Shot Voice Clone of user voice.
"""

import sys
import os
import asyncio
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from msf.config import MSFConfig
from msf.utils.logger import setup_logger, StageLogger
from msf.agents.voice_agent import VoiceAgent
from msf.libraries import MotionLibrary, LayoutLibrary, CameraLibrary, TypographyLibrary
from msf.engines import HTMLTemplateEngine, PlaywrightRenderer, VideoAssembler, AudioMaster
from msf.contracts.models import (
    SceneSpec, SceneComposition, SubtitleEntry,
    Emotion, AssetType, AssetRequest
)

logger = setup_logger("tg_promo")
log = StageLogger(logger, "PROMO")

def main():
    log.info("Starting Telegram Channel Promo Video Generation for @llm_hubs")

    cfg = MSFConfig.from_yaml("config/default.yml")

    # Promo script scenes detailing @llm_hubs value proposition (Translitted EN words)
    promo_scenes = [
        SceneSpec(
            scene_id="promo_scene_1",
            title="Заголовок и Хук",
            narration_text="Ищете лучшие оупен сорс решения в области искусственного интеллекта? Канал точка ЛЛМ Хабс — ваш главный источник передовых нейросетей!",
            duration=6.5,
            emotion=Emotion.EXCITED,
            visual_goal="Разборы LLM, ДевТулз и Мультиагентных систем",
        ),
        SceneSpec(
            scene_id="promo_scene_2",
            title="Факты и Разборы",
            narration_text="Глубокие разборы архитектур, свежие бенчмарки моделей от трехсот звезд на Гитхаб и научные статьи с высокой цитируемостью.",
            duration=7.5,
            emotion=Emotion.SERIOUS,
            visual_goal="Архитектура Моделей, Код и Бенчмарки >300★ GitHub",
        ),
        SceneSpec(
            scene_id="promo_scene_3",
            title="Призыв к действию",
            narration_text="Будьте в авангарде ИИ разработки. Подписывайтесь на канал точка ЛЛМ Хабс прямо сейчас!",
            duration=5.5,
            emotion=Emotion.EXCITED,
            visual_goal="Присоединяйтесь к сообществу @llm_hubs",
        )
    ]

    output_dir = Path("output/tg_promo_project_cloned")
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes_dir = output_dir / "scenes"
    scenes_dir.mkdir(exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    ml = MotionLibrary()
    ll = LayoutLibrary()
    cl = CameraLibrary()
    tl = TypographyLibrary()

    voice_agent = VoiceAgent(cfg)
    composed_scenes = []

    for i, scene_spec in enumerate(promo_scenes):
        log.info(f"--- Processing Scene {i+1}/{len(promo_scenes)} ---")

        # Voice generation with Qwen3-TTS 1.7B Zero-Shot Clone
        log.info("Generating Qwen3-TTS 1.7B Zero-Shot Voice Clone...")
        voice_result = voice_agent.run(scene_spec)
        log.info(f"Voice ready: {voice_result.duration_seconds}s")

        # Create exact subtitles from original narration text words (No Whisper hallucination)
        words = scene_spec.narration_text.split()
        dur = voice_result.duration_seconds
        total_chars = sum(len(w) for w in words) or 1
        t = 0.0
        subtitles = []
        for w in words:
            wd = max(0.2, (len(w) / total_chars) * dur)
            subtitles.append(SubtitleEntry(
                word=w,
                start=round(t, 2),
                end=round(t + wd, 2),
                style={"font": "Montserrat", "size": "48px", "color": "#FFFFFF", "highlight": "#E6C475"}
            ))
            t += wd

        # Layout and visual selection
        layouts = ll.list_all()
        cameras = cl.list_all()
        motions = ml.list_all()

        pick_layout = layouts[i % len(layouts)]
        pick_camera = cameras[i % len(cameras)]
        pick_motions = [motions[i % len(motions)], motions[(i+1) % len(motions)]]

        accent_color = "#E6C475" if i != 1 else "#00FF88"

        scene_comp = SceneComposition(
            scene_id=scene_spec.scene_id,
            layout=pick_layout,
            camera=pick_camera,
            motions=pick_motions,
            assets=[AssetRequest(
                asset_id=f"promo_asset_{i}",
                asset_type=AssetType.TEXT_BLOCK,
                description=scene_spec.visual_goal,
                style_constraints={"color": accent_color, "bg": "#0E0F11"},
                dimensions=(1080, 1920)
            )],
            voice=voice_result,
            subtitles=subtitles,
            background_color="#0E0F11",
            duration=voice_result.duration_seconds
        )
        composed_scenes.append(scene_comp)

    # HTML rendering & Frame compilation via Playwright
    log.info("Rendering HTML & Compiling Frames via Playwright...")
    html_engine = HTMLTemplateEngine()
    renderer = PlaywrightRenderer(cfg.render)

    all_frame_dirs = []
    scene_audio_paths = []

    for i, scene_comp in enumerate(composed_scenes):
        words = [sub.word for sub in scene_comp.subtitles]
        scene_html = html_engine.generate_scene_html(scene_comp, words)
        
        scene_output = scenes_dir / f"scene_{i+1}"
        scene_output.mkdir(exist_ok=True)

        frames_dir = asyncio.run(renderer.render_scene(
            scene_html, scene_comp.voice, scene_output
        ))
        log.info(f"Scene {i+1} frames rendered to: {frames_dir}")
        all_frame_dirs.append(frames_dir)
        if scene_comp.voice:
            scene_audio_paths.append(scene_comp.voice.audio_path)

    # Combine audio tracks
    log.info("Combining audio tracks...")
    combined_audio = str(audio_dir / "combined_audio.wav")
    if len(scene_audio_paths) > 1:
        concat_file = str(audio_dir / "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for ap in scene_audio_paths:
                f.write(f"file '{ap}'\n")
        os.system(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" -c copy "{combined_audio}" 2>&1')
    elif scene_audio_paths:
        combined_audio = scene_audio_paths[0]

    # Combine frames into sequential dir
    all_frames_dir = output_dir / "all_frames"
    all_frames_dir.mkdir(exist_ok=True)
    frame_idx = 0
    for fd in all_frame_dirs:
        if Path(fd).exists():
            for f in sorted(Path(fd).glob("frame_*.jpg")):
                dst = all_frames_dir / f"frame_{frame_idx:05d}.jpg"
                shutil.copy(str(f), str(dst))
                frame_idx += 1

    log.info(f"Total frame count across scenes: {frame_idx}")

    # Assemble raw MP4 video
    assembler = VideoAssembler()
    output_mp4 = str(output_dir / "tg_llm_hubs_cloned_master.mp4")
    result_path = assembler.assemble(
        frames_dir=all_frames_dir,
        audio_path=combined_audio if os.path.exists(combined_audio) else None,
        output_path=output_mp4,
        fps=cfg.render.fps
    )
    log.info(f"Video assembled: {result_path}")

    # Clean Audio Mastering
    if os.path.exists(result_path):
        master = AudioMaster()
        mastered_output = str(output_dir / "tg_llm_hubs_cloned_master_clean.mp4")
        try:
            master.master_audio(result_path, mastered_output)
            log.info(f"Audio mastered: {mastered_output}")
            result_path = mastered_output
        except Exception as e:
            log.warning(f"Audio mastering failed: {e}")

    final_abs = Path(result_path).resolve()
    size_mb = os.path.getsize(final_abs) / (1024 * 1024)
    log.info(f"🎉 MASTER PROMO VIDEO WITH USER VOICE CLONE CREATED: {final_abs} ({size_mb:.2f} MB)")
    print(f"\nSUCCESS: Video generated at {final_abs}")

if __name__ == "__main__":
    main()
