from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "projects" / "llm_hubs" / "generated"
OUT = GEN / "batch_2026-08-16"
OUT.mkdir(parents=True, exist_ok=True)


def load(name: str) -> dict:
    return json.loads((GEN / name).read_text(encoding="utf-8"))


def base_from(name: str, slug: str, title: str, style: str = "llm_hubs_neon") -> dict:
    d = load(name)
    d["style"] = style
    d["title"] = title
    d["slug"] = slug
    d.pop("audioUrl", None)
    return d


def scene(**kwargs: object) -> dict:
    return dict(kwargs)

videos: list[dict] = []

# 1 — retain the already researched model comparison but add explicit narration texts.
d = load("01_gemini37_flash_vs_sonnet5.spec.json")
d["slug"] = "01_gemini37_flash_vs_sonnet5"
d["scenes"][0]["text"] = "Gemini 3.7 Flash против Sonnet 5. В этом ролике не объявляем абсолютного победителя: смотрим, где Flash оказался сильнее и сколько стоит такая разница."
d["scenes"][1]["text"] = "На FrontierCode 1.1 Gemini 3.7 набрал 43,6 процента, а Sonnet 5 — 42,7. Это преимущество всего в одной конкретной задаче, не универсальный рейтинг."
d["scenes"][2]["text"] = "Ещё одна цифра — 1588 Elo в Code Arena Web Development. Но benchmark не знает ваш проект, поэтому главный тест — одинаковый prompt на вашей реальной задаче."
d["scenes"][3]["text"] = "По опубликованному сравнению, Flash дешевле Sonnet 5 по API-тарифу. Выигрыш особенно заметен, если у вас много коротких запросов и не нужен самый длинный reasoning."
d["scenes"][4]["text"] = "Нужны не громкие рейтинги, а проверяемые сравнения моделей. Подписывайтесь на @llm_hubs — здесь разбираем цифры и показываем, где они действительно полезны."
videos.append(d)

# 2 — DeepSeek release explainer.
d = load("02_deepseek_v4pro_0813.spec.json")
d["slug"] = "02_deepseek_v4pro_0813"
d["scenes"][0]["text"] = "DeepSeek V4 Pro 0813 — новый релиз, о котором говорят как о переходе от preview к более стабильному режиму. Но что это меняет обычному пользователю?"
d["scenes"][1]["text"] = "Главное отличие не в красивой вывеске, а в контракте использования: стабильнее endpoint, понятнее ограничения и меньше риска строить продукт на временной демонстрации."
d["scenes"][2]["text"] = "Слово GA часто переводят неправильно. Простыми словами: модель считается доступной для нормального использования, а не только экспериментом для ранних тестеров."
d["scenes"][3]["text"] = "Но доступность не означает автоматическое качество. Проверяйте latency, лимиты, цену, structured output и поведение на своих промптах до миграции."
d["scenes"][4]["text"] = "DeepSeek V4 Pro стоит тестировать не по hype, а по рабочему сценарию. @llm_hubs — короткие разборы релизов без сложных терминов и маркетингового тумана."
videos.append(d)

# 3 — OpenHarness.
d = base_from("03_deepseek_v4pro_cost_clock.spec.json", "03_openharness_agent_os", "OpenHarness: модель — это только половина агента")
d["style"] = "terminal"
d["scenes"] = [
    scene(id="oh-hook", durationInFrames=165, preset="HeroKinetic", title="МОДЕЛЬ — НЕ АГЕНТ", subtitle="Почему один и тот же LLM ведёт себя по-разному в разных harness", accentColor="#66E3FF", badge="TOOLS · MEMORY · PERMISSIONS"),
    scene(id="oh-loop", durationInFrames=210, preset="FlowDiagram", title="ЧТО ДЕЛАЕТ HARNESS", accentColor="#66E3FF", nodes=[{"label":"Prompt", "sub":"задача пользователя"}, {"label":"Tools + MCP", "sub":"действия в мире"}, {"label":"Memory + loop", "sub":"контекст и повтор"}], transition={"type":"clockWipe", "durationInFrames":12}),
    scene(id="oh-safety", durationInFrames=180, preset="DecisionGrid", title="ГДЕ СИЛА И ГДЕ РИСК", accentColor="#66E3FF", cards=[{"tag":"СИЛА", "title":"Skills", "description":"повторяемые инструкции"}, {"tag":"КОНТРОЛЬ", "title":"Permissions", "description":"границы файлов и действий"}, {"tag":"ПРОВЕРКА", "title":"Dry run", "description":"увидеть план без запуска"}], transition={"type":"pushCut", "durationInFrames":10}),
    scene(id="oh-fit", durationInFrames=180, preset="QuoteCard", text="OpenHarness: 43 tools · skills · memory · multi-agent coordination", accentColor="#66E3FF", author="OpenHarness README", transition={"type":"fade", "durationInFrames":12}),
    scene(id="oh-cta", durationInFrames=150, preset="LlmHubsCTA", title="НЕ МЕНЯЙТЕ МОДЕЛЬ СЛЕПУЮ", text="@llm_hubs — показываем, что реально делает harness вокруг LLM.", accentColor="#66E3FF", transition={"type":"dreamyZoom", "durationInFrames":12}),
]
texts = [
    "OpenHarness показывает неприятную правду: сама модель — только половина агента. Остальное решает harness — оболочка, которая управляет инструментами, памятью и безопасностью.",
    "Запрос проходит цикл: prompt, вызов инструмента, результат, память и следующий шаг. Поэтому одна и та же модель в разных agent harness может выглядеть как два разных продукта.",
    "Сильная сторона OpenHarness — skills, permissions, MCP и dry run. Но автономность без границ превращается в риск: агенту нужны правила доступа и проверяемый план.",
    "В README проект заявляет tool use, skills, memory и multi-agent coordination. Это не benchmark модели — это инфраструктура, которая делает поведение агента повторяемым.",
    "Когда модель кажется слабой, сначала проверьте harness. @llm_hubs — коротко объясняем, где заканчивается интеллект модели и начинается инженерия агента.",
]
for s, t in zip(d["scenes"], texts): s["text"] = t
videos.append(d)

# 4 — OpenCode.
d = base_from("01_gemini37_flash_vs_sonnet5.spec.json", "04_opencode_open_source_coder", "OpenCode: coding agent без привязки к одной модели")
d["style"] = "product_tutorial"
d["scenes"] = [
    scene(id="oc-hook", durationInFrames=150, preset="HeroKinetic", title="ОДИН CODING AGENT — МНОГО ПРОВАЙДЕРОВ", subtitle="OpenCode переносит фокус с чата на рабочий terminal loop", accentColor="#FFB86B", badge="OPEN SOURCE · TERMINAL · PROVIDERS"),
    scene(id="oc-loop", durationInFrames=210, preset="FlowDiagram", title="КАК ИДЁТ ЗАДАЧА", accentColor="#FFB86B", nodes=[{"label":"Repo", "sub":"читает контекст"}, {"label":"Agent", "sub":"планирует изменения"}, {"label":"Diff + tests", "sub":"проверяет результат"}], transition={"type":"wipe", "durationInFrames":12}),
    scene(id="oc-choice", durationInFrames=180, preset="DecisionGrid", title="ГДЕ ПОЛЬЗА", accentColor="#FFB86B", cards=[{"tag":"ЛОКАЛЬНО", "title":"Ollama", "description":"свой runtime"}, {"tag":"API", "title":"Провайдеры", "description":"меняйте backend"}, {"tag":"КОНТРОЛЬ", "title":"Diff", "description":"review до merge"}], transition={"type":"pushCut", "durationInFrames":10}),
    scene(id="oc-proof", durationInFrames=180, preset="QuoteCard", text="OpenCode · open-source AI coding agent · install: curl -fsSL https://opencode.ai/install | bash", accentColor="#FFB86B", author="opencode.ai", transition={"type":"fade", "durationInFrames":12}),
    scene(id="oc-cta", durationInFrames=150, preset="LlmHubsCTA", title="КОД ПИШЕТ НЕ ЧАТ", text="@llm_hubs — тестируем инструменты на реальных задачах.", accentColor="#FFB86B", transition={"type":"dreamyZoom", "durationInFrames":12}),
]
texts = [
    "OpenCode — open-source coding agent, который ставит в центр не чат, а рабочий loop в терминале. Агент читает репозиторий, меняет код и показывает diff.",
    "Задача начинается с контекста репозитория, продолжается планом и заканчивается изменениями с проверкой. Именно loop отличает coding agent от автодополнения строки.",
    "На официальном сайте OpenCode отдельно вынесены провайдеры, подписки, стоимость и приватность. Это удобно, если вы не хотите навсегда привязывать workflow к одной модели.",
    "На странице проекта указаны open-source статус и несколько способов установки. Но главный тест — не количество звёзд, а то, как агент проходит вашу задачу и сколько прав ему можно дать.",
    "OpenCode — это не кнопка «сделай всё». Это рабочий контур с review. @llm_hubs — показываем, где agent экономит время, а где просит контроля.",
]
for s, t in zip(d["scenes"], texts): s["text"] = t
videos.append(d)

# 5 — oh-my-openagent / multi-harness engineering.
d = base_from("05_august_model_costmap.spec.json", "05_ohmyopenagent_multiharness", "oh-my-openagent: когда один harness — уже мало")
d["style"] = "midnight_orbit"
d["scenes"] = [
    scene(id="omo-hook", durationInFrames=165, preset="HeroKinetic", title="АГЕНТА НУЖНО НЕ ТОЛЬКО ЗАПУСТИТЬ", subtitle="oh-my-openagent строит слой правил поверх нескольких harness", accentColor="#C9A7FF", badge="OPENCODE · CODEX · PI · CLAUDE CODE"),
    scene(id="omo-map", durationInFrames=210, preset="MetricTrend", title="МНОГО WORKER-ОВ", accentColor="#C9A7FF", points=[{"label":"OpenCode", "value": 25}, {"label":"Codex", "value": 50}, {"label":"Pi", "value": 75}], metricLabel="разные workers · один orchestration layer", valueSuffix="", transition={"type":"wipe", "durationInFrames":12}),
    scene(id="omo-rules", durationInFrames=180, preset="DecisionGrid", title="ЧТО ДАЁТ СЛОЙ ПРАВИЛ", accentColor="#C9A7FF", cards=[{"tag":"ПРОТОКОЛ", "title":"Skills", "description":"одинаковые правила"}, {"tag":"КОНТЕКСТ", "title":"Memory", "description":"не начинать с нуля"}, {"tag":"КОНТРОЛЬ", "title":"Review gates", "description":"остановка до merge"}], transition={"type":"pushCut", "durationInFrames":10}),
    scene(id="omo-proof", durationInFrames=180, preset="QuoteCard", text="Multi-Harness Agent OS Refactor in Progress · OpenCode · Codex · Pi", accentColor="#C9A7FF", author="oh-my-openagent README", transition={"type":"fade", "durationInFrames":12}),
    scene(id="omo-cta", durationInFrames=150, preset="LlmHubsCTA", title="HARNESS — ЭТО ПРОТОКОЛ РАБОТЫ", text="@llm_hubs — следим за тем, как агенты становятся системами.", accentColor="#C9A7FF", transition={"type":"dreamyZoom", "durationInFrames":12}),
]
texts = [
    "oh-my-openagent — проект для тех, кому одного coding harness уже мало. Его идея: вынести правила, skills и orchestration выше конкретного worker-а.",
    "В репозитории прямо описывается refactor под несколько harness: OpenCode, Codex, Pi и другие. То есть меняется не только модель — меняется исполнительный слой вокруг неё.",
    "Зачем это нужно? Чтобы skills, память и review gates не исчезали при смене worker-а. Но чем больше автоматизации, тем важнее тесты, лимиты и понятная остановка.",
    "Это направление лучше воспринимать как инженерный эксперимент, а не готовую гарантию качества. Сильный orchestration layer помогает только тогда, когда правила проверяемы.",
    "Будущее coding agents — не один магический CLI, а совместимые слои. @llm_hubs — разбираем новые harness до того, как они станут модным словом.",
]
for s, t in zip(d["scenes"], texts): s["text"] = t
videos.append(d)

# Hand-authored batches bypass research-to-script, so they must not quietly
# regress to the same five-scene template. The plan changes visual grammar while
# keeping semantics and narration order intact. It is deliberately transparent
# and limited to presets with safe text/renderer fallbacks.
_DIVERSE_VISUAL_PLANS = {
    "01_gemini37_flash_vs_sonnet5": ["HookStack", "MetricTrend", "ProblemSolution", "QuoteCard", "LlmHubsCTA"],
    "02_deepseek_v4pro_0813": ["KineticPhrase", "ProgressPath", "FeatureSpotlight", "CaseStudyBoard", "LlmHubsCTA"],
    "03_openharness_agent_os": ["HookStack", "FlowDiagram", "ProblemSolution", "CaseStudyBoard", "LlmHubsCTA"],
    "04_opencode_open_source_coder": ["KineticPhrase", "FeatureSpotlight", "DecisionGrid", "PostCard", "LlmHubsCTA"],
    "05_ohmyopenagent_multiharness": ["HeroKinetic", "MetricTrend", "CaseStudyBoard", "QuoteCard", "LlmHubsCTA"],
}


def apply_diverse_visual_plan(video: dict) -> None:
    plan = _DIVERSE_VISUAL_PLANS[video["slug"]]
    if len(plan) != len(video["scenes"]):
        raise ValueError(f"visual plan mismatch for {video['slug']}")
    for index, (item, preset) in enumerate(zip(video["scenes"], plan)):
        item["preset"] = preset
        item.setdefault("intensity", "calm")
        copy = item.get("text") or item.get("subtitle") or item.get("title") or "Проверяемый факт и следующий шаг"
        title = item.get("title") or "ПРОВЕРЯЕМ НА ПРАКТИКЕ"
        # Supply explicit text keys for the alternate grammar; individual presets
        # retain their safe defaults when a field is not used.
        if preset == "HookStack":
            item.update({"headline": title, "subhead": copy, "proof": "ПРОВЕРЯЕМЫЙ РАЗБОР", "urgency": "СЕЙЧАС"})
        elif preset == "KineticPhrase":
            item.update({"phrase": title, "highlight": "НЕ ВЕРЬТЕ НА СЛОВО", "caption": copy})
        elif preset == "ProgressPath":
            item.update({"steps": [
                {"label": "Релиз", "description": "Появилась новая версия"},
                {"label": "Проверка", "description": "Смотрим реальные условия"},
                {"label": "Тест", "description": "Пробуем свой prompt"},
                {"label": "Решение", "description": "Выбираем осознанно"},
            ], "currentStep": 2, "orientation": "vertical"})
        elif preset == "FeatureSpotlight":
            item.update({"feature": title, "benefit": copy, "index": f"0{index + 1}"})
        elif preset == "ProblemSolution":
            item.update({"problem": "Решать по громкому заявлению", "solution": "Проверить на своей задаче"})
        elif preset == "CaseStudyBoard":
            item.update({"context": "Есть конкретная задача", "action": "Сравниваем одинаковые условия", "result": "Фиксируем проверяемый вывод"})
        elif preset == "DecisionGrid":
            # Never delegate card typography to scale-capable scene motion.
            item["intensity"] = "calm"
        elif preset == "PostCard":
            item.setdefault("author", "ПРОВЕРЕННЫЙ ИСТОЧНИК")
            item.setdefault("handle", "@llm_hubs")


for d in videos:
    apply_diverse_visual_plan(d)
    slug = d["slug"]
    (OUT / f"{slug}.spec.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

manifest = {"date": "2026-08-16", "channel": "@llm_hubs", "videos": [{"slug": d["slug"], "title": d.get("title", d["slug"]), "spec": str((OUT / f"{d['slug']}.spec.json").relative_to(ROOT)), "scenes": len(d["scenes"]), "style": d.get("style")} for d in videos]}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
