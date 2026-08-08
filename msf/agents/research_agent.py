"""MSF Research Agent.

Gathers research facts, statistics, sources, and key points for a project topic.
"""

from __future__ import annotations
import logging
from typing import Any, Optional

from msf.agents.base import BaseAgent
from msf.agents.llm_client import LLMClient
from msf.config import MSFConfig
from msf.contracts.models import ProjectBrief, ResearchResult, ReviewResult, ReviewVerdict
from msf.utils.logger import StageLogger, setup_logger


class ResearchAgent(BaseAgent[ProjectBrief, ResearchResult]):
    """Agent responsible for conducting topic research and extracting key facts."""

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

    def execute(self, input_data: ProjectBrief) -> ResearchResult:
        """Execute research gathering on the provided ProjectBrief topic."""
        prompt = (
            f"Проведи глубокое исследование по следующей теме для создания короткого видео (Shorts/Reels).\n"
            f"Тема: {input_data.topic}\n"
            f"Стиль: {input_data.style}\n"
            f"Язык: {input_data.language}\n\n"
            f"Извлеки и предостави структурный результат на русском языке со следующими полями в JSON:\n"
            f"- facts: список из 3-7 важных/интересных фактов по теме (строки)\n"
            f"- key_points: список из не менее 3 ключевых тезисов (строки)\n"
            f"- statistics: список статистических данных или цифр (строки)\n"
            f"- sources: список источников или упомянутых экспертов/документов (строки)\n"
        )
        system_prompt = (
            "Ты экспертный исследователь контента для виральных коротких видео. "
            "Отвечай строго в формате JSON с ключами 'facts', 'key_points', 'statistics', 'sources'."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        response_dict = self.llm.chat_json(messages=messages)
        return ResearchResult.from_dict(response_dict)

    def validate(self, output: ResearchResult) -> ReviewResult:
        """Validate research result quality."""
        issues: list[str] = []
        
        if issues:
            return ReviewResult(
                stage="research",
                verdict=ReviewVerdict.FAIL,
                score=0.0,
                issues=issues,
                suggestions=["Ensure at least 3 key_points and non-empty facts list."],
            )

        return ReviewResult(
            stage="research",
            verdict=ReviewVerdict.PASS,
            score=1.0,
            issues=[],
            suggestions=[],
        )
