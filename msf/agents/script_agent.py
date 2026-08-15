"""MSF Script Agent.

Generates structured video scripts for viral YouTube Shorts / TikTok videos
in Russian. Optimised for four quality axes:

  1. **Retention** — hook in first 1–3 s, open loop per scene, payoff at the end.
  2. **Conversion** — CTA drives the viewer into a TG channel or bot.
  3. **Clarity** — mass-audience language (no jargon, no complex clauses).
  4. **Narrative arc** — problem → escalation → reveal → CTA.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from msf.agents.base import BaseAgent
from msf.agents.llm_client import LLMClient
from msf.config import MSFConfig
from msf.contracts.models import (
    ProjectBrief,
    ResearchResult,
    ReviewResult,
    ReviewVerdict,
    Script,
)
from msf.utils.logger import StageLogger, setup_logger

# ── Retention constants ──────────────────────────────────────────────────────
# Russian speech averages ~2.2 words/s for punchy delivery; 2.5 is calm.
_WORDS_PER_SEC_FAST = 2.2
_WORDS_PER_SEC_CALM = 2.5
_HOOK_MAX_WORDS = 8        # ≤ 3 s at fast pace
_HOOK_MAX_CHARS = 50       # hard screen-width limit
_CTA_MAX_WORDS = 15        # CTA must not drag
_MIN_SCENES = 3
_MAX_SCENES = 8
_MAX_WORDS_PER_SCENE = 25  # keeps visual card readable
_FLESCH_THRESHOLD = 60     # rough readability floor (adapted for Russian)


SYSTEM_PROMPT = """\
Ты — лучший в мире сценарист виральных вертикальных видео (Shorts / Reels / TikTok).
Твоя задача — написать **русскоязычный** сценарий, который:
• Удерживает зрителя с первой секунды (hook открывает «петлю любопытства»).
• Ведёт его по чёткой нарративной арке: ПРОБЛЕМА → НАГНЕТАНИЕ → РАСКРЫТИЕ → ВЫВОД.
• Говорит простым живым языком — как будто объясняешь крутому другу в баре.
  Запрещены: канцелярит, причастные обороты длиннее 4 слов, англицизмы без пояснения,
  вводные конструкции, слова «данный», «является», «осуществлять».
• Заканчивается CTA, который прямо отправляет в Telegram-канал или бота
  (пример: «Ссылка в описании — там ещё круче»).

ФОРМАТ ОТВЕТА — строго JSON (без markdown-обёрток):
{
  "title": "краткий заголовок видео",
  "hook": "цепляющая фраза ≤ 8 слов, ≤ 50 символов — ПЕРВОЕ, что слышит зритель",
  "scenes_text": [
    "Сцена 1: …",
    "Сцена 2: …",
    …
  ],
  "cta": "призыв к действию с упоминанием ТГ-канала/бота",
  "total_duration": <число секунд>,
  "language": "ru",
  "retention_score": <0–100>,
  "clarity_notes": "почему текст понятен массовой аудитории"
}

ПРАВИЛА СЦЕН:
1. Каждая сцена — 1–2 предложения, ≤ 25 слов. Короче = лучше.
2. Минимум 3 сцены, максимум 8.
3. Каждая сцена ДОЛЖНА начинаться с мини-крючка или перехода
   («А вот тут начинается самое интересное…», «Но подожди…»,
    «И вот почему это важно…»).
4. Последняя сцена перед CTA — это РАСКРЫТИЕ / ПЭЙОФФ.
5. Не повторяй слова из hook в первой сцене.

ПРАВИЛА HOOK:
— Начинай с вопроса, шокирующего факта или провокации.
— Открой «петлю» — зритель ДОЛЖЕН захотеть узнать ответ.
— Никаких приветствий, представлений, «в этом видео мы…».

ПРАВИЛА CTA:
— Прямо скажи, что делать: перейти по ссылке, подписаться, написать боту.
— Упомяни конкретную площадку (Telegram).
— Не более 15 слов.
"""

USER_PROMPT_TEMPLATE = """\
Тема: {topic}
Стиль: {style}
Целевая длительность: {target_duration} секунд (диапазон {dur_min}–{dur_max} с).

Результаты исследования:
— Факты: {facts}
— Ключевые точки: {key_points}
— Статистика: {statistics}

Напиши сценарий строго по правилам из системного промпта.
"""


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

    # ── Core generation ──────────────────────────────────────────────────

    def execute(self, input_data: dict[str, Any]) -> Script:
        """Generate a structured script from a brief + research bundle."""
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

        dur_min, dur_max = brief.duration_range
        target_duration = (dur_min + dur_max) / 2.0

        user_prompt = USER_PROMPT_TEMPLATE.format(
            topic=brief.topic,
            style=brief.style,
            target_duration=target_duration,
            dur_min=dur_min,
            dur_max=dur_max,
            facts=json.dumps(research.facts, ensure_ascii=False),
            key_points=json.dumps(research.key_points, ensure_ascii=False),
            statistics=json.dumps(research.statistics, ensure_ascii=False),
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        response_dict = self.llm.chat_json(messages=messages)

        if "total_duration" not in response_dict or not isinstance(
            response_dict["total_duration"], (int, float)
        ):
            response_dict["total_duration"] = target_duration

        return Script.from_dict(response_dict)

    # ── Validation ───────────────────────────────────────────────────────

    def validate(self, output: Script) -> ReviewResult:
        """Validate generated script against retention / clarity / conversion rules."""
        issues: list[str] = []
        suggestions: list[str] = []

        # ── Hook checks ──────────────────────────────────────────────────
        hook = (output.hook or "").strip()
        if not hook:
            issues.append("Hook отсутствует.")
            suggestions.append("Добавь цепляющую фразу ≤ 8 слов.")
        else:
            hw = hook.split()
            if len(hw) > _HOOK_MAX_WORDS:
                issues.append(
                    f"Hook слишком длинный: {len(hw)} слов (макс {_HOOK_MAX_WORDS})."
                )
                suggestions.append("Сократи hook до 5–8 слов.")
            if len(hook) > _HOOK_MAX_CHARS:
                issues.append(
                    f"Hook слишком длинный: {len(hook)} символов (макс {_HOOK_MAX_CHARS})."
                )
            # Hook should not start with a greeting
            if re.match(r"^(привет|здравствуй|всем привет|в этом видео)", hook, re.I):
                issues.append("Hook начинается с приветствия — убей удержание.")
                suggestions.append("Начни с вопроса, факта или провокации.")

        # ── Scenes checks ───────────────────────────────────────────────
        scenes = output.scenes_text or []
        if len(scenes) < _MIN_SCENES:
            issues.append(f"Слишком мало сцен: {len(scenes)} (мин {_MIN_SCENES}).")
            suggestions.append("Разбей текст на большее количество коротких сцен.")
        if len(scenes) > _MAX_SCENES:
            issues.append(f"Слишком много сцен: {len(scenes)} (макс {_MAX_SCENES}).")
            suggestions.append("Объедини мелкие сцены.")

        for i, st in enumerate(scenes):
            wc = len(st.split())
            if wc > _MAX_WORDS_PER_SCENE:
                issues.append(
                    f"Сцена {i + 1} слишком длинная: {wc} слов (макс {_MAX_WORDS_PER_SCENE})."
                )
                suggestions.append(f"Раздели сцену {i + 1} на две.")

        # ── CTA checks ──────────────────────────────────────────────────
        cta = (output.cta or "").strip()
        if not cta:
            issues.append("CTA отсутствует.")
            suggestions.append("Добавь призыв к действию с упоминанием Telegram.")
        else:
            cta_words = cta.split()
            if len(cta_words) > _CTA_MAX_WORDS:
                issues.append(f"CTA слишком длинный: {len(cta_words)} слов (макс {_CTA_MAX_WORDS}).")
            # CTA should mention a platform
            if not re.search(r"(telegram|тг|канал|бот|ссыл|описани)", cta, re.I):
                issues.append("CTA не упоминает Telegram / канал / бота / ссылку.")
                suggestions.append("Добавь конкретное направление: Telegram-канал или бот.")

        # ── Duration sanity ──────────────────────────────────────────────
        all_text = " ".join(
            [hook] + scenes + [cta]
        )
        total_words = len(all_text.split())
        est_duration_fast = total_words / _WORDS_PER_SEC_FAST
        est_duration_calm = total_words / _WORDS_PER_SEC_CALM
        declared = output.total_duration

        if declared > 0:
            if est_duration_fast > declared * 1.5:
                issues.append(
                    f"Текста слишком много для {declared}с: ~{est_duration_fast:.0f}с при быстрой озвучке."
                )
            if est_duration_calm < declared * 0.4:
                issues.append(
                    f"Текста слишком мало для {declared}с: ~{est_duration_calm:.0f}с при спокойной озвучке."
                )

        # ── Clarity heuristics ───────────────────────────────────────────
        # Detect overly complex sentences (> 20 words) across all text
        for i, sentence in enumerate(re.split(r'[.!?…]+', all_text)):
            sw = sentence.split()
            if len(sw) > 22:
                issues.append(
                    f"Предложение #{i + 1} слишком длинное ({len(sw)} слов) — "
                    f"массовая аудитория потеряет нить."
                )
                suggestions.append("Разбей длинные предложения на короткие.")

        # Check for bureaucratic / AI-isms
        bad_words = ["является", "осуществлять", "данный", "вышеуказанный", "нижеследующий"]
        found_bad = [w for w in bad_words if w in all_text.lower()]
        if found_bad:
            issues.append(f"Канцелярит: {', '.join(found_bad)}.")
            suggestions.append("Замени канцелярские слова простыми синонимами.")

        # ── Narrative arc check ──────────────────────────────────────────
        if len(scenes) >= 3:
            # The last scene before CTA should feel like a payoff, not setup
            last_scene = scenes[-1].lower()
            setup_markers = ["а что если", "но подожди", "и вот почему", "самое интересное"]
            if any(m in last_scene for m in setup_markers):
                issues.append(
                    "Последняя сцена начинается как setup, а не как payoff/раскрытие."
                )
                suggestions.append("Последняя сцена должна давать ответ / раскрытие.")

        # ── Score ────────────────────────────────────────────────────────
        if issues:
            score = max(0.0, 1.0 - len(issues) * 0.15)
            verdict = ReviewVerdict.FAIL if score < 0.6 else ReviewVerdict.PASS
            return ReviewResult(
                stage="script",
                verdict=verdict,
                score=round(score, 2),
                issues=issues,
                suggestions=suggestions,
            )

        return ReviewResult(
            stage="script",
            verdict=ReviewVerdict.PASS,
            score=1.0,
            issues=[],
            suggestions=[],
        )
