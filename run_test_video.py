#!/usr/bin/env python3
"""MSF test video generation script.

Runs the full pipeline: brief → research → script → storyboard → scenes → render → assemble.
Outputs to ./output/test_video.mp4
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from msf.config import MSFConfig
from msf.utils.logger import setup_logger, StageLogger
from msf.agents.llm_client import LLMClient
from msf.agents.research_agent import ResearchAgent
from msf.agents.script_agent import ScriptAgent
from msf.agents.storyboard_agent import StoryboardAgent
from msf.agents.scene_composer import SceneComposer
from msf.agents.voice_agent import VoiceAgent
from msf.agents.subtitle_agent import SubtitleAgent
from msf.review.reviewer import ReviewEngine
from msf.libraries import MotionLibrary, LayoutLibrary, CameraLibrary, TypographyLibrary
from msf.engines import HTMLTemplateEngine, PlaywrightRenderer, VideoAssembler, AudioMaster
from msf.contracts.models import (
    ProjectBrief, ResearchResult, Script, Storyboard,
    SceneSpec, SceneComposition, VoiceResult, SubtitleEntry,
    ProjectState, ProjectStatus, ReviewResult, ReviewVerdict,
    Emotion, AssetType, AssetRequest
)
import httpx

logger = setup_logger("msf_test")
log = StageLogger(logger, "TEST")

def main():
    log.info("Starting MSF test video generation")

    # 1. Load config
    cfg = MSFConfig.from_yaml("config/default.yml")
    log.info(f"Config loaded: model={cfg.llm.model}, base_url={cfg.llm.base_url}")

    # 2. Create LLM client
    llm = LLMClient(cfg.llm)

    # 3. Create brief
    topic = "Почему нейросети меняют мир в 2026 году"
    brief = ProjectBrief(
        topic=topic,
        style="tech",
        duration_range=(15, 25),
        language="ru",
        output_format="mp4"
    )
    log.info(f"Project brief: {brief.topic}")

    # 4. Research agent
    log.info("Running Research Agent...")
    research_agent = ResearchAgent(cfg)
    try:
        research = research_agent.run(brief, max_attempts=2)
        log.info(f"Research done: {len(research.facts)} facts, {len(research.key_points)} key points")
    except Exception as e:
        log.warning(f"Research agent failed: {e}. Using minimal research.")
        research = ResearchResult(
            facts=["AI市场规模预计2026年达到5000亿美元", "大语言模型参数量突破万亿级别", "多模态AI成为主流技术方向"],
            sources=["openai.com", "anthropic.com", "google.com"],
            key_points=["LLM革命", "多模态融合", "AI代理自治化"],
            statistics=["5000亿市场规模", "1T+参数", "90%准确率"]
        )

    # 5. Script agent
    log.info("Running Script Agent...")
    script_agent = ScriptAgent(cfg)
    try:
        script = script_agent.run({"brief": brief, "research": research}, max_attempts=2)
        log.info(f"Script done: hook='{script.hook[:50]}...', {len(script.scenes_text)} scenes")
    except Exception as e:
        log.warning(f"Script agent failed: {e}. Using hardcoded script.")
        script = Script(
            title="Нейросети 2026",
            hook="Мир изменился навсегда. Нейросети уже среди нас.",
            scenes_text=[
                "В 2026 году нейросети пишут код, создают видео и ведут переговоры.",
                "Модели с триллионом параметров работают на каждом смартфоне.",
                "Мультиагентные системы автономно выполняют сложные задачи без человека.",
            ],
            cta="Подпишись, чтобы не пропустить будущее.",
            total_duration=20,
            language="ru"
        )

    # 6. Storyboard agent
    log.info("Running Storyboard Agent...")
    storyboard_agent = StoryboardAgent(cfg)
    try:
        storyboard = storyboard_agent.run({"script": script, "brief": brief}, max_attempts=2)
        log.info(f"Storyboard done: {len(storyboard.scenes)} scenes")
    except Exception as e:
        log.warning(f"Storyboard agent failed: {e}. Building manually.")
        scenes = []
        for i, text in enumerate(script.scenes_text):
            scenes.append(SceneSpec(
                scene_id=f"scene_{i+1}",
                title=f"Сцена {i+1}",
                narration_text=text,
                duration=5.0,
                emotion=Emotion.EXCITED if i == 0 else Emotion.SERIOUS,
                information_load="medium",
                visual_goal="Показать рост AI технологий"
            ))
        storyboard = Storyboard(
            project_id="test_001",
            scenes=scenes,
            total_duration=float(sum(s.duration for s in scenes)),
            narrative_arc="hook → development → climax → resolution"
        )

    # 7. For each scene: compose + voice + subtitle
    output_dir = Path("output/test_project")
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes_dir = output_dir / "scenes"
    scenes_dir.mkdir(exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    ml = MotionLibrary()
    ll = LayoutLibrary()
    cl = CameraLibrary()
    tl = TypographyLibrary()

    composed_scenes = []

    for i, scene_spec in enumerate(storyboard.scenes):
        log.info(f"--- Scene {i+1}/{len(storyboard.scenes)} ---")

        # 7a. Compose scene
        log.info(f"  Composing scene...")
        layouts = ll.list_all()
        cameras = cl.list_all()
        motions = ml.list_all()

        # LLM picks layout + camera
        pick_layout = layouts[i % len(layouts)]
        pick_camera = cl.get_compatible(pick_layout.layout_id)
        if pick_camera:
            pick_camera = pick_camera[0]
        else:
            pick_camera = cameras[0]

        pick_motions = [motions[i % len(motions)], motions[(i+1) % len(motions)]]

        scene_comp = SceneComposition(
            scene_id=scene_spec.scene_id,
            layout=pick_layout,
            camera=pick_camera,
            motions=pick_motions,
            assets=[AssetRequest(
                asset_id=f"asset_{i}",
                asset_type=AssetType.TEXT_BLOCK,
                description=scene_spec.visual_goal or scene_spec.title,
                style_constraints={"color": "#E6C475", "bg": "#0E0F11"},
                dimensions=(1080, 1920)
            )],
            voice=None,
            subtitles=[],
            background_color="#0E0F11",
            duration=scene_spec.duration
        )

        # 7b. Voice synthesis
        log.info(f"  Generating voice...")
        voice_agent = VoiceAgent(cfg)
        try:
            voice_result = voice_agent.run(scene_spec, max_attempts=2)
            scene_comp.voice = voice_result
            log.info(f"  Voice: {voice_result.duration_seconds}s, {len(voice_result.word_timestamps)} words")
        except Exception as e:
            log.warning(f"  Voice failed: {e}. Using synth fallback.")
            try:
                import edge_tts
                import tempfile
                voice_path = str(audio_dir / f"voice_{scene_spec.scene_id}.mp3")
                async def _tts():
                    communicate = edge_tts.Communicate(scene_spec.narration_text, "ru-RU-SvetlanaNeural")
                    await communicate.save(voice_path)
                asyncio.run(_tts())
                # Estimate duration from file size
                fsize = os.path.getsize(voice_path)
                duration = max(2.0, fsize / 16000.0)
                words = scene_spec.narration_text.split()
                timestamps = []
                t = 0.0
                total_chars = sum(len(w) for w in words) or 1
                for w in words:
                    wd = max(0.3, (len(w) / total_chars) * duration)
                    timestamps.append({"word": w, "start": round(t, 2), "end": round(t + wd, 2)})
                    t += wd

                voice_result = VoiceResult(
                    audio_path=voice_path,
                    duration_seconds=round(duration, 2),
                    sample_rate=24000,
                    word_timestamps=timestamps
                )
                scene_comp.voice = voice_result
                log.info(f"  Voice (edge-tts): {duration}s, {len(timestamps)} words")
            except Exception as e2:
                log.error(f"  edge-tts also failed: {e2}")
                continue

        # 7c. Subtitles
        log.info(f"  Generating subtitles...")
        word_ts = voice_result.word_timestamps if isinstance(voice_result.word_timestamps[0], dict) else [
            {"word": wt.word, "start": wt.start, "end": wt.end}
            for wt in voice_result.word_timestamps
        ]
        subtitles = []
        for j, wt in enumerate(word_ts):
            subtitles.append(SubtitleEntry(
                word=wt["word"],
                start=wt["start"],
                end=wt["end"],
                style={"font": "Inter", "size": 42, "weight": "bold", "color": "#FFFFFF"},
                position={"x": 540, "y": 1650}
            ))
        scene_comp.subtitles = subtitles
        log.info(f"  Subtitles: {len(subtitles)} entries")

        composed_scenes.append((scene_comp, scene_spec))

    # 8. Render each scene
    log.info("=== RENDERING SCENES ===")
    template_engine = HTMLTemplateEngine()
    renderer = PlaywrightRenderer(cfg.render)

    all_frames = []
    scene_audio_paths = []

    for i, (scene_comp, scene_spec) in enumerate(composed_scenes):
        log.info(f"Rendering scene {i+1}/{len(composed_scenes)}...")
        words = [wt["word"] if isinstance(wt, dict) else wt.word
                 for wt in (scene_comp.voice.word_timestamps if scene_comp.voice else [])]
        html = template_engine.generate_scene_html(scene_comp, words)
        log.info(f"  HTML: {len(html)} chars")

        scene_output = scenes_dir / f"scene_{i+1}"
        scene_output.mkdir(exist_ok=True)

        try:
            frames_dir = asyncio.run(renderer.render_scene(
                html, scene_comp.voice, scene_output
            ))
            log.info(f"  Frames rendered to {frames_dir}")
            all_frames.append(frames_dir)
            if scene_comp.voice:
                scene_audio_paths.append(scene_comp.voice.audio_path)
        except Exception as e:
            log.error(f"  Render failed: {e}")
            import traceback
            log.error(traceback.format_exc())

    # 9. Assemble video
    log.info("=== ASSEMBLING VIDEO ===")
    if all_frames:
        assembler = VideoAssembler()

        # Concatenate audio from all scenes
        combined_audio = str(audio_dir / "combined_audio.wav")
        if len(scene_audio_paths) > 1:
            # Build concat list for ffmpeg
            concat_file = str(audio_dir / "concat_list.txt")
            with open(concat_file, "w") as f:
                for ap in scene_audio_paths:
                    f.write(f"file '{ap}'\n")
            os.system(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" -c copy "{combined_audio}" 2>&1')
        elif scene_audio_paths:
            combined_audio = scene_audio_paths[0]

        # Assemble frames from first scene (for demo)
        first_frames = all_frames[0]
        output_mp4 = str(output_dir / "test_video.mp4")

        # Combine ALL frames into one sequence
        all_frames_dir = output_dir / "all_frames"
        all_frames_dir.mkdir(exist_ok=True)
        frame_idx = 0
        for fd in all_frames:
            if Path(fd).exists():
                for f in sorted(Path(fd).glob("frame_*.jpg")):
                    dst = all_frames_dir / f"frame_{frame_idx:05d}.jpg"
                    import shutil
                    shutil.copy(str(f), str(dst))
                    frame_idx += 1

        log.info(f"Total frames: {frame_idx}")

        # FFmpeg assembly
        result_path = assembler.assemble(
            frames_dir=all_frames_dir,
            audio_path=combined_audio if os.path.exists(combined_audio) else None,
            output_path=output_mp4,
            fps=cfg.render.fps
        )
        log.info(f"Video assembled: {result_path}")

        # 10. Audio mastering
        if os.path.exists(result_path):
            master = AudioMaster()
            mastered_output = str(output_dir / "test_video_mastered.mp4")
            try:
                master.master_audio(result_path, mastered_output)
                log.info(f"Audio mastered: {mastered_output}")
                result_path = mastered_output
            except Exception as e:
                log.warning(f"Audio mastering failed: {e}")

        if os.path.exists(result_path):
            size_mb = os.path.getsize(result_path) / (1024*1024)
            log.info(f"=== DONE: {result_path} ({size_mb:.1f} MB) ===")
            return result_path
        else:
            log.error("Output file not found after assembly!")
            return None
    else:
        log.error("No frames rendered!")
        return None


if __name__ == "__main__":
    result = main()
    if result:
        print(f"\n✅ SUCCESS: {result}")
        sys.exit(0)
    else:
        print("\n❌ FAILED")
        sys.exit(1)
