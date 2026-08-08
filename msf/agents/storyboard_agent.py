"""MSF Storyboard Agent.

Decomposes video scripts into detailed scene specifications (Storyboard).
"""

from __future__ import annotations
import json
import logging
from typing import Any, Optional

from msf.agents.base import BaseAgent
from msf.agents.llm_client import LLMClient
from msf.config import MSFConfig
from msf.contracts.models import (
    Emotion,
    ProjectBrief,
    ReviewResult,
    ReviewVerdict,
    SceneSpec,
    Script,
    Storyboard,
)
from msf.utils.logger import StageLogger, setup_logger


class StoryboardAgent(BaseAgent[dict[str, Any], Storyboard]):
    """Agent responsible for converting scripts into visual scene storyboards."""

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
    def execute(self, input_data: dict[str, Any]) -> Storyboard:
        """Execute storyboard generation from input containing 'script' and optionally 'brief'."""
        raw_script = input_data.get("script")
        raw_brief = input_data.get("brief")

        if isinstance(raw_script, Script):
            script = raw_script
        elif isinstance(raw_script, dict):
            script = Script.from_dict(raw_script)
        else:
            script = Script()

        project_id = "project_001"
        if isinstance(raw_brief, ProjectBrief):
            project_id = getattr(raw_brief, "project_id", "project_001")
        elif isinstance(raw_brief, dict):
            project_id = raw_brief.get("project_id", "project_001")

        prompt = (
            f"Разбей следующий сценарий видео на визуальные сцены (Storyboard).\n"
            f"Заголовок сценария: {script.title}\n"
            f"Хук (первые секунды): {script.hook}\n"
            f"Тексты сцен: {json.dumps(script.scenes_text, ensure_ascii=False)}\n"
            f"Призыв к действию (CTA): {script.cta}\n"
            f"Общая целевая длительность: {script.total_duration} сек.\n\n"
            f"Преобразуй этот сценарий в список сцен (scenes).\n"
            f"Каждая сцена должна включать:\n"
            f"- scene_id: строка вида 'scene_1', 'scene_2', ...\n"
            f"- title: название/суть сцены (строка)\n"
            f"- narration_text: дикторский текст озвучки для этой сцены (строка на русском языке)\n"
            f"- duration: длительность сцены в секундах (число float)\n"
            f"- emotion: эмоция ('neutral', 'excited', 'serious', 'energetic', 'calm', 'dramatic', 'curiosity', 'urgent', 'inspirational')\n"
            f"- information_load: информационная нагрузка ('low', 'medium', 'high')\n"
            f"- visual_goal: визуальная цель / что должно происходить на экране на русском языке (строка)\n\n"
            f"Структура ответа JSON:\n"
            f"{{\n"
            f'  "project_id": "{project_id}",\n'
            f'  "scenes": [ ... ],\n'
            f'  "total_duration": {script.total_duration},\n'
            f'  "narrative_arc": "описание нарративной дуги (строка)"\n'
            f"}}\n"
            f"Важно: сумма длительностей всех сцен должна равняться total_duration.\n"
        )
        system_prompt = (
            "Ты режиссёр-постановщик коротких видео. Создай детализированный раскадрованный storyboard. "
            "Отвечай строго в формате JSON."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        response_dict = self.llm.chat_json(messages=messages)
        response_dict["project_id"] = response_dict.get("project_id") or project_id

        storyboard = Storyboard.from_dict(response_dict)

        # Recalculate total_duration if sum of scenes differs
        if storyboard.scenes:
            sum_dur = sum(s.duration for s in storyboard.scenes)
            if abs(storyboard.total_duration - sum_dur) > 0.1 and sum_dur > 0:
                storyboard.total_duration = round(sum_dur, 2)

        return storyboard

    def validate(self, output: Storyboard) -> ReviewResult:
        """Validate storyboard specification."""
        issues: list[str] = []

        if not output.scenes or len(output.scenes) == 0:
            issues.append("Scenes list is empty.")
        else:
            scene_sum = sum(s.duration for s in output.scenes)
            if abs(scene_sum - output.total_duration) > 1.0:
                issues.append(
                    f"Durations sum ({scene_sum:.2f}s) does not match total_duration ({output.total_duration:.2f}s)."
                )

            for i, scene in enumerate(output.scenes):
                if not scene.visual_goal or not scene.visual_goal.strip():
                    issues.append(f"Scene {i} ({scene.scene_id}) missing visual_goal.")

        if issues:
            return ReviewResult(
                stage="storyboard",
                verdict=ReviewVerdict.FAIL,
                score=0.0,
                issues=issues,
                suggestions=["Ensure scenes are not empty, visual goals exist, and durations sum to total."],
            )

        return ReviewResult(
            stage="storyboard",
            verdict=ReviewVerdict.PASS,
            score=1.0,
            issues=[],
            suggestions=[],
        )
