"""MSF Script Agent.

Generates structured video scripts for viral YouTube Shorts / TikTok videos in Russian.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Optional

from msf.agents.base import BaseAgent
from msf.agents.llm_client import LLMClient
from msf.config import MSFConfig
from msf.contracts.models import ProjectBrief, ResearchResult, ReviewResult, ReviewVerdict, Script
from msf.utils.logger import StageLogger, setup_logger

class ScriptAgent(BaseAgent[dict[str, Any], Script]):
    """Agent responsible for writing viral video scripts in Russian."""
    def __init__(
        self,
        config: Optional[MSFConfig] = None,
        logger: Optional[StageLogger | logging.Logger] = None,
        llm: Optional[LLMClient] = None,
    ) -> None:
        cfg = config or MSFConfig()
        log = logger or setup_logger(self.__class__.__name__)
        super().__init__(config=cfg, logger=log)
        if llm is not None:
            self.llm = llm

    def execute(self, input_data: dict[str, Any]) -> Script:
        """Execute script generation from input containing 'brief' and 'research'."""
        raw_brief = input_data.get("brief")
        raw_research = input_data.get("research")

        if isinstance(raw_brief, ProjectBrief):
            brief = raw_brief
        elif isinstance(raw_brief, dict):
            brief = ProjectBrief.from_dict(raw_brief)
        else:
            brief = ProjectBrief(topic=str(raw_brief) if raw_brief else "General")

        if isinstance(raw_research, ResearchResult):
            research = raw_research
        elif isinstance(raw_research, dict):
            research = ResearchResult.from_dict(raw_research)
        else:
            research = ResearchResult()

        target_duration_min, target_duration_max = brief.duration_range
        target_duration = (target_duration_min + target_duration_max) / 2.0

        prompt = (
            f"Напиши виральный сценарий для короткого вертикального видео (Shorts/Reels/TikTok) на русском языке.\n"
            f"Тема: {brief.topic}\n"
            f"Стиль: {brief.style}\n"
            f"Целевая длительность: {target_duration} секунд (диапазон {target_duration_min}-{target_duration_max} сек).\n\n"
            f"Результаты исследования для использования:\n"
            f"Факты: {json.dumps(research.facts, ensure_ascii=False)}\n"
            f"Ключевые точки: {json.dumps(research.key_points, ensure_ascii=False)}\n"
            f"Статистика: {json.dumps(research.statistics, ensure_ascii=False)}\n\n"
            f"Сценарий ДОЛЖЕН содержать:\n"
            f"1. hook: мощная цепляющая фраза для первых 3 секунд.\n"
            f"2. title: заголовок сценария.\n"
            f"3. scenes_text: список из 3-7 сцен с текстом закадровой озвучки (narration text) на русском языке.\n"
            f"4. cta: призыв к действию в конце видео (подпишись, лайк, коммент).\n"
            f"5. total_duration: предполагаемая длительность видео в секундах (число).\n"
            f"6. language: 'ru'.\n\n"
            f"Верни ответ строго в формате JSON с ключами: title, hook, scenes_text, cta, total_duration, language."
        )
        system_prompt = (
            "Ты супер-сценарист виральных коротких видео. Напиши увлекательный сценарий на русском языке. "
            "Отвечай строго в формате JSON."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        response_dict = self.llm.chat_json(messages=messages)
        
        # Ensure fallback for required fields if needed
        if "total_duration" not in response_dict or not isinstance(response_dict["total_duration"], (int, float)):
            response_dict["total_duration"] = target_duration

        return Script.from_dict(response_dict)

    def validate(self, output: Script) -> ReviewResult:
        """Validate generated script structure and constraints."""
        issues: list[str] = []

        if not output.hook or not output.hook.strip():
            issues.append("Hook is missing or empty.")

        if not output.scenes_text or len(output.scenes_text) < 1:
            issues.append("scenes_text is empty.")

        total_words = len((output.hook + " " + " ".join(output.scenes_text) + " " + output.cta).split())
        # Average speaking speed: ~2.5 words per second (150 words / min)
        estimated_duration = total_words / 2.5

        # Check total duration vs estimated text length or declared duration
        if estimated_duration > (output.total_duration * 1.8) or estimated_duration < (output.total_duration * 0.3):
            issues.append(
                f"Total text word count ({total_words} words, ~{estimated_duration:.1f}s) "
                f"does not fit total duration estimate ({output.total_duration}s)."
            )
        if issues:
            return ReviewResult(
                stage="script",
                verdict=ReviewVerdict.FAIL,
                score=0.0,
                issues=issues,
                suggestions=["Ensure hook exists, scenes_text non-empty, and duration fits text."],
            )

        return ReviewResult(
            stage="script",
            verdict=ReviewVerdict.PASS,
            score=1.0,
            issues=[],
            suggestions=[],
        )
