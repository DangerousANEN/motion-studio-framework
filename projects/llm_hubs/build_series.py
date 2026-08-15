"""Build the current LLM Hubs release series from evidence-backed video specs.

The five short videos deliberately use distinct scene progressions. Every factual
line maps to a claim in ``evidence_packs_2026-08-14.json``; narration and the
final master mix are added by the audio production step.
"""
from __future__ import annotations

import json
import shutil
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from msf.audio.music import loop_bed
from msf.audio.sfx import SFX_REGISTRY, render as render_sfx
import msf.audio.sfx_extra  # noqa: F401 - registers local SFX assets
from msf.audio.synth import SR
from msf.spec import Scene, build_spec, compute_total_frames, validate_spec
from msf.studio.contracts import ResearchPack, ScriptLine, ScriptPlan
from msf.studio.script_planner import validate_script_plan

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "projects" / "llm_hubs"
OUTPUT = PROJECT / "generated"
PUBLIC_AUDIO = ROOT / "remotion" / "public" / "audio"
EVIDENCE_PATH = PROJECT / "evidence_packs_2026-08-14.json"
NEON_GREEN = "#00F0A8"


@dataclass(frozen=True)
class VideoDraft:
    slug: str
    title: str
    research_id: str
    hook: str
    factual_lines: list[tuple[str, str, str]]
    visual_scenes: list[Scene]
    music_bed: str
    cta: str


def transition(kind: str = "fade", duration: int = 12) -> dict[str, Any]:
    return {"type": kind, "durationInFrames": duration}


def scene(scene_id: str, preset: str, duration: int, **props: Any) -> Scene:
    return Scene(id=scene_id, preset=preset, duration_in_frames=duration, accent_color=NEON_GREEN, **props)


SERIES: list[VideoDraft] = [
    VideoDraft(
        slug="01_gemini37_flash_vs_sonnet5",
        title="Gemini 3.7 Flash против Sonnet 5: где Flash впереди за меньшие деньги",
        research_id="research_gemini37_vs_sonnet5",
        hook="Google показывает Gemini 3.7 Flash выше Sonnet 5 в двух конкретных метриках. Разбираем, где это правда, а где нельзя делать общий вывод.",
        factual_lines=[
            ("fact", "Google выпустил Gemini 3.7 Flash 13 августа. До конца года заявлена цена: 75 центов за миллион входных и 3 доллара 75 центов за миллион выходных токенов.", "claim_g37_release_price"),
            ("fact", "В таблице Google Flash выше Sonnet 5 на FrontierCode: 43.6 против 42.7 процента, и на Code Arena Web Development: 1588 против 1541 Elo.", "claim_g37_specific_benchmark_edge"),
            ("fact", "По опубликованному API-прайсу это на 62.5 процента дешевле Sonnet 5 и на входе, и на выходе. Но один бенчмарк — не универсальный победитель.", "claim_g37_price_gap_sonnet"),
        ],
        visual_scenes=[
            scene("g37-hero", "HeroKinetic", 150, title="FLASH ВЫШЕ SONNET 5?", badge="2 МЕТРИКИ · НЕ ОБЩИЙ РЕЙТИНГ", subtitle="Google даёт преимущество в двух таблицах. Проверяем цену и контекст."),
            scene("g37-frontiercode", "MetricTrend", 210, metric_label="FrontierCode 1.1 · production code", title="ГДЕ FLASH ВПЕРЕДИ", value_suffix="%", points=[
                {"label": "Gemini 3.6", "value": 34.4},
                {"label": "Sonnet 5", "value": 42.7},
                {"label": "Gemini 3.7", "value": 43.6},
            ], transition=transition("wipe")),
            scene("g37-decision", "DecisionGrid", 180, title="КАК ЧИТАТЬ СРАВНЕНИЕ", cards=[
                {"tag": "ФАКТ", "title": "43.6%", "description": "FrontierCode 1.1 в таблице Google"},
                {"tag": "ФАКТ", "title": "1588 Elo", "description": "Code Arena Web Development"},
                {"tag": "ВЫВОД", "title": "СВОЙ ТЕСТ", "description": "Проверьте workload"},
            ], transition=transition("pushCut", 10)),
            scene("g37-price", "QuoteCard", 180, text="API list price: Flash — $0.75 / $3.75. Sonnet 5 — $2 / $10 за 1M input / output.", author="Google DeepMind + Anthropic", transition=transition("fade")),
            scene("g37-cta", "LlmHubsCTA", 150, title="Меньше цены. Больше проверки.", text="@llm_hubs — свежие модели без маркетинговых обобщений.", transition=transition("dreamyZoom")),
        ],
        music_bed="data_spark",
        cta="Подписывайтесь на @llm_hubs: новые модели, цены и реальные ограничения.",
    ),
    VideoDraft(
        slug="02_deepseek_v4pro_0813",
        title="DeepSeek V4 Pro 0813: что меняет выход из preview",
        research_id="research_deepseek_v4pro_release",
        hook="DeepSeek V4 Pro 0813 вышел из preview. Главная практическая настройка — не новая цифра в бенчмарке, а выбор effort под задачу.",
        factual_lines=[
            ("fact", "DeepSeek 13 августа объявил, что V4 Pro вышел из preview и стал доступен в Expert Mode на app и web, а также через API.", "claim_ds_v4pro_ga_access"),
            ("fact", "Для V4 Pro есть три уровня reasoning effort: low, high и max. Простую задачу не обязательно запускать в максимальном режиме.", "claim_ds_v4pro_reasoning"),
            ("fact", "Документация указывает 1 миллион токенов контекста, максимум 384 тысячи токенов на output, tool calls и совместимые API-режимы.", "claim_ds_v4pro_capabilities"),
        ],
        visual_scenes=[
            scene("ds-chat", "AiChatStream", 210, title="DEEPSEEK V4 PRO", chat_title="Expert Mode", response="Вышел из preview. Выбирай effort под задачу: low, high или max."),
            scene("ds-effort", "TgChat", 240, contact_name="AGENT ROUTING", contact_status="в сети", tg_theme="light", date_pill="СЕГОДНЯ", compose="high — когда нужен разбор и tools", typing=True, show_input_bar=True, show_cursor=False, send_at_progress=0.76, messages=[
                {"text": "А для простой задачи?", "out": False, "time": "12:08"},
                {"text": "low — быстро и без лишних токенов", "out": True, "read": True, "time": "12:08"},
                {"sticker": "brain", "out": True, "time": "12:08"},
                {"text": "А если нужно разобрать репозиторий?", "out": False, "time": "12:09"},
            ], transition=transition("slide")),
            scene("ds-api", "StepList", 195, title="ЧТО ЕСТЬ В API", steps=[
                {"label": "1M context", "description": "для длинного рабочего контекста"},
                {"label": "Tool calls", "description": "для агентских workflow"},
                {"label": "384K max output", "description": "не означает, что он нужен в каждом запросе"},
            ], transition=transition("wipe")),
            scene("ds-code", "CodeReveal", 165, language="python", code="task = classify(ticket)\neffort = \"low\" if task.simple else \"high\"\nanswer = client.responses.create(\n  model=\"deepseek-v4-pro\",\n  reasoning_effort=effort\n)", title="ВЫБИРАЙТЕ EFFORT", transition=transition("fade")),
            scene("ds-cta", "LlmHubsCTA", 150, title="Агенту — нужное усилие", text="@llm_hubs — как использовать модели без лишнего оверхеда.", transition=transition("dreamyZoom")),
        ],
        music_bed="focus_loop",
        cta="Подписывайтесь на @llm_hubs: практические настройки для новых LLM.",
    ),
    VideoDraft(
        slug="03_deepseek_v4pro_cost_clock",
        title="DeepSeek V4 Pro: не перепутайте текущую цену и тариф с 16 августа",
        research_id="research_deepseek_v4pro_cost",
        hook="У DeepSeek V4 меняется цена. Ключевой момент: новые peak и off-peak ставки вступают в силу 16 августа, а не работают задним числом.",
        factual_lines=[
            ("fact", "Сейчас в документации V4 Pro указаны 43.5 цента за миллион cache-miss input токенов и 87 центов за миллион output токенов.", "claim_ds_current_prices"),
            ("fact", "DeepSeek сообщает, что новая peak и off-peak сетка вступает в силу в 16:00 UTC 16 августа. Для V4 Pro off-peak output указан как 1 доллар 98 центов за миллион токенов.", "claim_ds_future_offpeak"),
            ("fact", "Поэтому будущую off-peak цену нельзя выдавать за сегодняшнюю. В estimate всегда указывайте дату действия тарифа.", "claim_ds_future_not_current"),
        ],
        visual_scenes=[
            scene("ds-cost-hook", "HeroKinetic", 165, title="ТАРИФ МЕНЯЕТСЯ", badge="ВАЖНО · 16 АВГУСТА, 16:00 UTC", subtitle="Одна дата меняет расчёт DeepSeek V4 Pro. Не перепутайте текущий и будущий прайс."),
            scene("ds-cost-flow", "FlowDiagram", 210, title="ЦЕНА ЗАВИСИТ ОТ ВРЕМЕНИ", nodes=[
                {"label": "Запрос V4 Pro", "sub": "input + output"},
                {"label": "Дата и UTC", "sub": "проверьте effective time"},
                {"label": "Peak / off-peak", "sub": "не смешивайте прайсы"},
            ], transition=transition("clockWipe")),
            scene("ds-cost-beforeafter", "BeforeAfter", 195, title="НЕ ПУТАЙТЕ ПЕРИОДЫ", before={"label": "14 августа", "title": "Текущий прайс", "text": "$0.435 input cache-miss · $0.87 output"}, after={"label": "с 16 августа", "title": "Новая сетка", "text": "Off-peak и peak rates с указанного UTC-времени"}, transition=transition("swap")),
            scene("ds-cost-counter", "StatCounter", 195, stat_value=0.87, stat_prefix="$", stat_suffix=" / 1M output", stat_label="V4 Pro · текущая опубликованная output-цена", transition=transition("fade")),
            scene("ds-cost-cta", "LlmHubsCTA", 150, title="Цена без даты — не цена", text="@llm_hubs — разбираем прайсы до того, как они бьют по счёту.", transition=transition("dreamyZoom")),
        ],
        music_bed="clarity_steps",
        cta="Подписывайтесь на @llm_hubs: новые тарифы и честный разбор условий.",
    ),
    VideoDraft(
        slug="04_grok46_long_agent",
        title="Grok 4.6: новый long-running agent без мифа о бесплатном безлимите",
        research_id="research_grok46_release",
        hook="Grok 4.6 вышел для длинных агентских траекторий. Но ценность — не в громком названии, а в том, как вы считаете контекст, кэш и инструменты.",
        factual_lines=[
            ("fact", "xAI выпустил Grok 4.6 12 августа с фокусом на long-running agents, интерактивные и визуальные задачи.", "claim_grok46_release_focus"),
            ("fact", "В API-документации указаны 500 тысяч токенов контекста, function calling, structured outputs и reasoning.", "claim_grok46_api_capabilities"),
            ("fact", "Опубликованная цена API: 2 доллара за миллион input, 50 центов за миллион cached input и 6 долларов за миллион output токенов.", "claim_grok46_price_cache"),
        ],
        visual_scenes=[
            scene("grok-hero", "HeroKinetic", 150, title="GROK 4.6", badge="АГЕНТ МОЖЕТ ДУМАТЬ ДОЛЬШЕ", subtitle="Но длинная траектория не отменяет счёт за контекст и output."),
            scene("grok-timeline", "TimelineReveal", 195, title="ЧТО ДОБАВИЛИ 12 АВГУСТА", events=[
                {"date": "12 АВГ", "label": "Grok 4.6", "description": "релиз от xAI"},
                {"date": "AGENT", "label": "Длинные задачи", "description": "многошаговый workflow"},
                {"date": "API", "label": "Tools + JSON", "description": "контролируемый output"},
            ], transition=transition("wipe")),
            scene("grok-eval", "MetricTrend", 195, metric_label="DeepSWE 1.1 · xAI release table", title="GROK 4.5 → 4.6", value_suffix="%", points=[
                {"label": "Grok 4.5", "value": 54.0},
                {"label": "Grok 4.6", "value": 65.9},
            ], transition=transition("crossZoom")),
            scene("grok-cache", "CodeReveal", 180, language="typescript", code="const request = await xai.responses.create({\n  model: \"grok-4.6\",\n  input: task,\n  tools: [searchTool]\n});\n// cached input: $0.50 / 1M", title="КЭШ И TOOLS — ОТДЕЛЬНО", transition=transition("fade")),
            scene("grok-cta", "LlmHubsCTA", 150, title="Агенту нужен контроль", text="@llm_hubs — модели, контекст и стоимость без иллюзий.", transition=transition("dreamyZoom")),
        ],
        music_bed="tech_drift",
        cta="Подписывайтесь на @llm_hubs: делаем агента сильнее, а счёт предсказуемее.",
    ),
    VideoDraft(
        slug="05_august_model_costmap",
        title="Свежая LLM cost map: Gemini 3.7, DeepSeek V4 Pro, Grok 4.6 и Sonnet 5",
        research_id="research_august_model_costmap",
        hook="Какая новая LLM сейчас дешевле? Правильный ответ начинается с одной таблицы, но не заканчивается на ней.",
        factual_lines=[
            ("fact", "На опубликованных input list prices: Gemini 3.7 Flash — 75 центов, DeepSeek V4 Pro — 43.5 цента cache-miss, Grok 4.6 и Sonnet 5 — по 2 доллара за миллион токенов.", "claim_costmap_input"),
            ("fact", "На output list prices картина другая: DeepSeek V4 Pro — 87 центов, Gemini 3.7 Flash — 3.75 доллара, Grok 4.6 — 6 долларов, Sonnet 5 — 10 долларов за миллион.", "claim_costmap_output"),
            ("fact", "Но token list price — не рейтинг качества: кэш, контекст, effort и ваша задача меняют итоговую стоимость и полезность.", "claim_costmap_not_benchmark"),
        ],
        visual_scenes=[
            scene("cost-hook", "HeroKinetic", 150, title="КТО СЖИГАЕТ БЮДЖЕТ?", badge="ЦЕНА ТОКЕНА ≠ ЦЕНА ЗАДАЧИ", subtitle="Свежая cost map: сначала цифры, потом ваш реальный workload."),
            scene("cost-rank", "Leaderboard", 210, title="INPUT · $ / 1M TOKENS", value_suffix="$", rows=[
                {"name": "Grok 4.6", "value": 2.0},
                {"name": "Sonnet 5", "value": 2.0},
                {"name": "Gemini 3.7 Flash", "value": 0.75},
                {"name": "DeepSeek V4 Pro", "value": 0.435},
            ]),
            scene("cost-output", "DonutFill", 210, title="OUTPUT · $ / 1M TOKENS", center_content="label", value_suffix="$", segments=[
                {"label": "DeepSeek", "value": 0.87, "color": "#00F0A8"},
                {"label": "Gemini", "value": 3.75, "color": "#58E6D2"},
                {"label": "Grok", "value": 6.0, "color": "#A3FFD9"},
                {"label": "Sonnet", "value": 10.0, "color": "#CFFFE7"},
            ], transition=transition("ripple")),
            scene("cost-compare", "CompareSplit", 180, title="ДЕШЕВЛЕ ≠ ЛУЧШЕ", cards=[
                {"title": "Список цен", "description": "Быстрая стартовая гипотеза", "tag": "ШАГ 1"},
                {"title": "Ваш workload", "description": "Кэш, output mix, effort и качество", "tag": "ШАГ 2"},
            ], transition=transition("pushCut", 10)),
            scene("cost-decision", "DecisionGrid", 180, title="ТЕСТИРУЙТЕ ПЕРЕД МИГРАЦИЕЙ", cards=[
                {"tag": "1", "title": "Один prompt set", "description": "Одинаковые входы для всех"},
                {"tag": "2", "title": "Ваша метрика", "description": "Качество, latency, ошибки"},
                {"tag": "3", "title": "Реальный счёт", "description": "Input, output, cache и retries"},
            ], transition=transition("fade")),
            scene("cost-cta", "LlmHubsCTA", 165, title="Не выбирайте по одной цифре", text="@llm_hubs — свежие модели, реальные workflow и экономия.", transition=transition("dreamyZoom")),
        ],
        music_bed="upbeat_clean",
        cta="Подписывайтесь на @llm_hubs: больше актуальных LLM-разборов.",
    ),
]


def _write_wav(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SR)
        output.writeframes(pcm.tobytes())


def _audio_track(duration: float, bed: str, transition_offsets: list[float]) -> np.ndarray:
    """Temporary preview bed; audio production replaces it with mastered voice mix."""
    track = loop_bed(bed, duration=duration, sr=SR) * 0.55
    cue_ids = ["whoosh_short", "counter_tick", "whoosh_short", "success_chime"]
    for offset, cue_id in zip(transition_offsets, cue_ids):
        if cue_id not in SFX_REGISTRY:
            continue
        cue = render_sfx(cue_id, sr=SR) * 0.38
        start = int(offset * SR)
        end = min(len(track), start + len(cue))
        if start < len(track):
            track[start:end] += cue[: end - start]
    return np.clip(track, -1.0, 1.0)


def _load_packs() -> dict[str, ResearchPack]:
    raw = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    return {item["research_id"]: ResearchPack.model_validate(item) for item in raw["packs"]}


def _script_for(video: VideoDraft, pack: ResearchPack) -> ScriptPlan:
    lines = [ScriptLine(kind="hook", narration=video.hook, scene_intent="hook")]
    for kind, narration, claim_id in video.factual_lines:
        lines.append(ScriptLine(kind=kind, narration=narration, evidence_claim_ids=[claim_id], scene_intent="evidence"))
    lines.append(ScriptLine(kind="cta", narration=video.cta, scene_intent="cta"))
    plan = ScriptPlan(research_id=pack.research_id, title=video.title, language="ru", lines=lines, cta_handle="@llm_hubs")
    validate_script_plan(plan, pack)
    return plan


def build() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PUBLIC_AUDIO.mkdir(parents=True, exist_ok=True)
    packs = _load_packs()
    manifest: list[dict[str, Any]] = []
    for video in SERIES:
        pack = packs[video.research_id]
        plan = _script_for(video, pack)
        # The series has one release-safe visual system. Individual scene props
        # may never override it with a gold/warm palette.
        spec = build_spec(
            video.visual_scenes,
            fps=30,
            width=720,
            height=1280,
            theme="noir",
            style="llm_hubs_neon",
        )
        validate_spec(spec)
        duration = compute_total_frames(spec["scenes"]) / spec["fps"]
        starts: list[float] = []
        frame_cursor = 0
        for index, item in enumerate(spec["scenes"]):
            if index:
                starts.append(frame_cursor / spec["fps"])
            frame_cursor += item["durationInFrames"] - (item.get("transition") or {}).get("durationInFrames", 0)
        audio_name = f"llm-hubs-{video.slug}.wav"
        master = PROJECT / "audio" / f"master_{video.slug}.wav"
        if master.is_file():
            # The production pass owns the finished voice/music/SFX master.  Copy
            # it only after duration has been computed from the same VideoSpec.
            shutil.copyfile(master, PUBLIC_AUDIO / audio_name)
        else:
            _write_wav(PUBLIC_AUDIO / audio_name, _audio_track(duration, video.music_bed, starts))
        spec["audioUrl"] = f"audio/{audio_name}"
        validate_spec(spec)
        spec_path = OUTPUT / f"{video.slug}.spec.json"
        script_path = OUTPUT / f"{video.slug}.script.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        script_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        manifest.append({
            "slug": video.slug,
            "title": video.title,
            "spec": str(spec_path.relative_to(ROOT)),
            "script": str(script_path.relative_to(ROOT)),
            "audio": f"remotion/public/audio/{audio_name}",
            "audio_mastered": master.is_file(),
            "duration_seconds": round(duration, 2),
            "research_id": video.research_id,
            "release_topic": True,
        })
    (OUTPUT / "series_manifest.json").write_text(json.dumps({"videos": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"videos": manifest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
