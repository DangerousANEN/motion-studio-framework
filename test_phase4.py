"""Smoke test for MSF Phase 4 Agents."""

import logging
from unittest.mock import MagicMock
from msf.agents.research_agent import ResearchAgent
from msf.agents.script_agent import ScriptAgent
from msf.agents.storyboard_agent import StoryboardAgent
from msf.agents.scene_composer import SceneComposer
from msf.agents.voice_agent import VoiceAgent
from msf.agents.subtitle_agent import SubtitleAgent
from msf.contracts.models import ProjectBrief, SceneSpec, VoiceResult, WordTimestamp, ReviewVerdict
from msf.config import MSFConfig, LLMConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smoke_test")

def main():
    logger.info("Starting Phase 4 Agents Smoke Test...")

    config = MSFConfig(llm=LLMConfig(base_url="http://localhost:20128/v1", model="antigravity/gemini-3.6-flash-high"))

    brief = ProjectBrief(
        topic="Искусственный интеллект в 2026 году",
        style="modern_tech",
        duration_range=(15, 30),
        language="ru",
    )

    # 1. ResearchAgent
    logger.info("--- Testing ResearchAgent ---")
    mock_llm = MagicMock()
    mock_llm.chat_json.return_value = {
        "facts": ["ИИ развивается быстрыми темпами", "Нейросети помогают в дизайне", "Автоматизация возрастает"],
        "key_points": ["Высокая скорость работы", "Новые возможности креатива", "Доступность для каждого"],
        "statistics": ["80% компаний внедряют ИИ"],
        "sources": ["MSF Tech Report 2026"]
    }
    research_agent = ResearchAgent(config=config, llm=mock_llm)
    research_res = research_agent.run(brief)
    logger.info(f"ResearchResult facts count: {len(research_res.facts)}, key_points: {len(research_res.key_points)}")
    rev = research_agent.validate(research_res)
    assert rev.verdict == ReviewVerdict.PASS, f"Research validation failed: {rev.issues}"

    # 2. ScriptAgent
    logger.info("--- Testing ScriptAgent ---")
    mock_llm_script = MagicMock()
    mock_llm_script.chat_json.return_value = {
        "title": "ИИ в 2026 году",
        "hook": "Вы не поверите, на что способен ИИ в 2026 году!",
        "scenes_text": [
            "Нейросети теперь создают видео за считанные секунды.",
            "Каждый бизнес использует автоматизированный контент.",
            "Будущее уже наступило в каждом смартфоне."
        ],
        "cta": "Подписывайся на канал, чтобы знание было с тобой!",
        "total_duration": 20.0,
        "language": "ru"
    }
    script_agent = ScriptAgent(config=config, llm=mock_llm_script)
    script_res = script_agent.run({"brief": brief, "research": research_res})
    logger.info(f"Script hook: '{script_res.hook}', scenes_text count: {len(script_res.scenes_text)}")
    rev = script_agent.validate(script_res)
    assert rev.verdict == ReviewVerdict.PASS, f"Script validation failed: {rev.issues}"

    # 3. StoryboardAgent
    logger.info("--- Testing StoryboardAgent ---")
    mock_llm_storyboard = MagicMock()
    mock_llm_storyboard.chat_json.return_value = {
        "project_id": "proj_test",
        "scenes": [
            {
                "scene_id": "scene_1",
                "title": "Интро",
                "narration_text": "Вы не поверите, на что способен ИИ в 2026 году!",
                "duration": 5.0,
                "emotion": "excited",
                "information_load": "medium",
                "visual_goal": "Футуристический интерфейс с графиками"
            },
            {
                "scene_id": "scene_2",
                "title": "Основная часть",
                "narration_text": "Нейросети теперь создают видео за считанные секунды.",
                "duration": 7.0,
                "emotion": "energetic",
                "information_load": "high",
                "visual_goal": "Быстрая смена моушн-графики и элементов"
            },
            {
                "scene_id": "scene_3",
                "title": "Аутро",
                "narration_text": "Подписывайся на канал!",
                "duration": 8.0,
                "emotion": "inspirational",
                "information_load": "low",
                "visual_goal": "Крупный призыв подписки и логотип"
            }
        ],
        "total_duration": 20.0,
        "narrative_arc": "Захват внимания -> Факты -> Призыв"
    }
    storyboard_agent = StoryboardAgent(config=config, llm=mock_llm_storyboard)
    storyboard_res = storyboard_agent.run({"script": script_res, "brief": brief})
    logger.info(f"Storyboard scenes count: {len(storyboard_res.scenes)}, total_duration: {storyboard_res.total_duration}")
    rev = storyboard_agent.validate(storyboard_res)
    assert rev.verdict == ReviewVerdict.PASS, f"Storyboard validation failed: {rev.issues}"

    # 4. SceneComposer
    logger.info("--- Testing SceneComposer ---")
    mock_llm_composer = MagicMock()
    mock_llm_composer.chat_json.return_value = {
        "layout_id": "centered_single",
        "camera_id": "static_center",
        "motion_ids": ["fade_in", "pulse_attention"],
        "asset_requests": [
            {
                "asset_id": "scene_1_bg",
                "asset_type": "image",
                "description": "Futuristic AI visual"
            }
        ],
        "background_color": "#0f172a"
    }
    composer = SceneComposer(config=config, llm=mock_llm_composer)
    first_scene = storyboard_res.scenes[0]
    scene_comp = composer.run({"scene_spec": first_scene})
    logger.info(f"SceneComposition layout: {scene_comp.layout.layout_id}, camera: {scene_comp.camera.preset_id}, motions: {len(scene_comp.motions)}")
    rev = composer.validate(scene_comp)
    assert rev.verdict == ReviewVerdict.PASS, f"SceneComposer validation failed: {rev.issues}"

    # 5. VoiceAgent
    logger.info("--- Testing VoiceAgent ---")
    voice_agent = VoiceAgent(config=config)
    voice_res = voice_agent.run(first_scene)
    logger.info(f"VoiceResult audio_path: {voice_res.audio_path}, duration: {voice_res.duration_seconds}s, timestamps count: {len(voice_res.word_timestamps)}")
    rev = voice_agent.validate(voice_res)
    assert rev.verdict == ReviewVerdict.PASS, f"VoiceAgent validation failed: {rev.issues}"

    # 6. SubtitleAgent
    logger.info("--- Testing SubtitleAgent ---")
    subtitle_agent = SubtitleAgent(config=config)
    subtitles = subtitle_agent.run(voice_res)
    logger.info(f"Subtitle entries count: {len(subtitles)}")
    rev = subtitle_agent.validate(subtitles)
    assert rev.verdict == ReviewVerdict.PASS, f"SubtitleAgent validation failed: {rev.issues}"

    logger.info("ALL PHASE 4 AGENTS SMOKE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
