# MSF Studio v2 — автономный release

**Дата:** 14 августа 2026, GMT+7  
**Статус:** готов к локальному использованию и дальнейшему UI/desktop-слою.  
**Артефакты серии:** `projects/llm_hubs/rendered/`.

> **Главное изменение:** Motion Studio Framework теперь имеет отдельный application-layer `msf.studio`: агенту не нужно знать имена React-компонентов, пути файлов или правила рендера. Он работает через contracts, каталог, evidence gates, storyboard validation, runs, события и безопасные traces.

## Что реализовано

| Контур | Реализация | Практический эффект |
|---|---|---|
| Единое ядро | Versioned contracts для assets, storyboard, evidence, scripts, runs, artifacts, events и traces. | Dashboard, MCP и workers используют одну модель данных вместо параллельных ad-hoc payloads. |
| Preset-first безопасность | Capability tiers (`preset`, `curated`, `sandbox`, `release`), asset lifecycle и manifest-driven catalog. | Ограниченный агент видит только stable presets и не подставляет data-driven scenes без обязательных props. |
| Research и сценарий | Evidence source/claim contracts, fail-closed policy, ScriptPlan validator и evidence → storyboard bridge. | Factual line не проходит без связанного claim; storyboard не принимает неизвестные claims. |
| Наблюдаемость | JSONL events и redacted TraceStore с allowlist атрибутов. | Оператор видит узлы, инструменты, статусы, ошибки и artifacts, но не хранит prompts, secrets или скрытые рассуждения. |
| Агентский интерфейс | Локальный stdio MCP server `python -m msf.studio.mcp_server`. | Агент может искать scenes, получать manifests и sound recipes, валидировать research/storyboard, сохранять draft и inspect run. |
| Библиотека scenes | Добавлены `StepList`, `BeforeAfter`, `MetricTrend`, `DecisionGrid` и брендированная `LlmHubsCTA`. | Есть bounded визуальные структуры для инструкций, сравнений, динамики, routing-выбора и финального CTA. |
| Эффекты и аудио | Добавлен `FocusPulse`, 19 procedural music beds, 112 local SFX и 11 sound-design recipes. | Music/SFX выбираются по семантике сцен без загрузки непроверенных сторонних файлов и вопросов лицензирования. |
| Reproducible rendering | System Chromium, checked Remotion bundling, batch render script, QA control frames. | Серия собирается из проверяемых JSON specs, локальных WAV и React scenes повторяемо. |

## Единый skill и модель полномочий

Skill `skills/msf-studio` объединяет workflows `preset-video`, `curated-storyboard`, `create-scene`, `modify-scene`, `add-voice`, `add-audio-pack`, `research-video` и `debug-run`.

| Режим | Доступ агента | Обязательные gates |
|---|---|---|
| `preset` | Только stable manifest assets, выбор из каталога и storyboard. | Catalog discovery, schema validation, readability, evidence links. |
| `curated` | Режиссёрская композиция из stable scenes/effects/audio. | Те же gates плюс проверка data-driven props. |
| `sandbox` | Draft scenes, effects, voices и audio packs. | Fixtures, TypeScript/Python checks, preview и отдельный release approval. |
| `release` | Публикация draft → stable. | Quality gates, asset lifecycle и человеческое решение. |

## MCP: локальный adapter для агентских клиентов

MCP server не является render shell. Он намеренно ограничен application-level операциями:

| Surface | Назначение | Ограничение безопасности |
|---|---|---|
| `msf://catalog/{tier}` | Live scene manifests по capability tier. | Нет жёстко закодированных списков и draft leakage в preset tier. |
| `msf://sound-design` | Declarative music/SFX recipes. | Только local registered assets. |
| `search_scene_catalog`, `describe_scene` | Discovery перед storyboard. | Агент не угадывает preset names/fields. |
| `validate_research_evidence`, `validate_storyboard` | Fail-closed research и композиционные gates. | Неподтверждённые facts и неизвестные claims отклоняются. |
| `save_storyboard_draft`, `prepare_render_run` | Локальные draft/run intent. | Render worker требует отдельного explicit approval в run service. |
| `inspect_run` | Events + redacted traces. | Нет raw prompts, credentials или chain-of-thought. |

## Серия `@llm_hubs`

Пять вертикальных роликов собраны в 720×1280, H.264, 30 fps, с процедурной фоновой музыкой, SFX на переходах, brand CTA и предоставленной круглой аватаркой. Каждая серия содержит machine-readable `ResearchPack`, `ScriptPlan` и `VideoSpec`; все фактические claims связаны с official/primary sources.

| Файл | Тема | Проверяемая идея | Ключевое ограничение |
|---|---|---|---|
| `01_ollama_local.mp4` | Локальная LLM через Ollama | Ollama документирует локальный запуск и API; квантование уменьшает память с компромиссом по точности. [1] [2] [3] | Не обещает работу любой модели на любом ноутбуке. |
| `02_gemini_free.mp4` | Gemini Free / AI Studio | Free tier ограничен моделью и project-level limits; AI Studio отображает актуальные условия. [4] [5] [6] | Не называет чужие лимиты универсальными и напоминает об условиях Free tier. |
| `03_openrouter_free.mp4` | OpenRouter Free Models Router | `openrouter/free` выбирает доступную free-модель; result указывает фактически выбранную модель. [7] | Не подаёт random free routing как стабильный production SLA; учитывает limits. [8] |
| `04_hf_cheapest.mp4` | Hugging Face Inference Providers | Unified routing даёт policy `:cheapest`; monthly Free credits — микро-бюджет на эксперименты. [9] [10] | Не выдаёт $0.10 monthly credits за production capacity. |
| `05_gemini_batch_flex.mp4` | Gemini Batch vs Flex | Batch и Flex дают 50% cost reduction для разных latency/cost trade-offs. [11] [12] | Это paid-tier режимы; Batch асинхронен и не подходит для live ответа. |

## Запуск и повторяемость

```bash
cd /path/to/motion-studio-framework

# Подготовить source-backed specs и local WAV.
PYTHONPATH=. python tools/check_llm_hubs_evidence.py
PYTHONPATH=. python projects/llm_hubs/build_series.py

# Финальный batch render через уже установленный системный Chromium.
projects/llm_hubs/render_series.sh

# Локальный operator dashboard (без внешнего доступа).
PYTHONPATH=. python -m msf.panel.server
# Затем открыть http://127.0.0.1:8765/studio

# Agent interface через stdio.
PYTHONPATH=. python -m msf.studio.mcp_server
```

## Результаты проверок

| Проверка | Результат |
|---|---|
| `tools/check_studio_v2.py` | Прошёл: 43 scenes в live catalog; `StoryboardValidator` доступен. |
| `tools/check_studio_research.py` | Прошёл: evidence → script → storyboard → validation. |
| `tools/check_studio_observability.py` | Прошёл: 2 events и 2 redacted spans. |
| `tools/check_studio_audio.py` | Прошёл: 19 music beds, 112 SFX, 11 recipes. |
| `tools/check_studio_mcp.py` | Прошёл: MCP server создаётся, tier-filtered catalog доступен. |
| `tools/check_studio_mcp_protocol.py` | Прошёл: реальная stdio session инициализируется; зарегистрировано 8 tools, а live search возвращает `DecisionGrid`. |
| `tools/check_studio_api.py` | Прошёл: FastAPI catalog, evidence, storyboard и безопасное создание run draft. |
| `tools/check_llm_hubs_evidence.py` | Прошёл: все 5 evidence packs, по 3 sources и 3 claims. |
| TypeScript Studio pack | Прошёл: `tsc --noEmit -p remotion/tsconfig.studio.json`. |
| Preview/QA | Прошли: CTA control frame и Batch/Flex comparison control frame, без clipping. |
| Final media | Прошли: 5 H.264 MP4, примерно 2.9–3.2 MB каждый. |

Полный legacy `pytest` запущен и дал **131 passed, 1 skipped**, но не является release gate v2: оставшиеся сбои зависят от отсутствующих optional legacy components (`langgraph`, Torch voice stack, Playwright managed browser), а также отдельного LLM integration test. Документация больше не сообщает устаревший ложный результат полного suite. Studio v2 targeted checks и actual Remotion renders прошли.

## Следующий логичный релиз

В v2 уже включён локальный operator dashboard на `/studio`: brief composer, evidence gate, live scene catalog, безопасное создание run draft и timeline. Следующий релиз может развить этот единый UI-маршрут без дублирования orchestration: добавить визуальный storyboard editor, player артефактов, очередь явных approvals, evidence review с source preview и manager для подключения MCP-клиентов. Базовые contracts, visibility policy, events/traces и local MCP boundary уже готовы для такого расширения.

## References

[1]: https://docs.ollama.com/quickstart "Ollama Quickstart"
[2]: https://docs.ollama.com/import "Ollama — Importing and quantizing a model"
[3]: https://docs.ollama.com/api/introduction "Ollama API Introduction"
[4]: https://ai.google.dev/gemini-api/docs/pricing "Gemini Developer API pricing"
[5]: https://ai.google.dev/gemini-api/docs/rate-limits "Gemini API rate limits"
[6]: https://ai.google.dev/gemini-api/docs/billing "Gemini API billing"
[7]: https://openrouter.ai/docs/guides/routing/routers/free-router "OpenRouter Free Models Router"
[8]: https://openrouter.ai/docs/api_reference/limits "OpenRouter rate limits"
[9]: https://huggingface.co/docs/inference-providers/en/index "Hugging Face Inference Providers"
[10]: https://huggingface.co/docs/inference-providers/en/pricing "Hugging Face Inference Providers pricing"
[11]: https://ai.google.dev/gemini-api/docs/batch-api "Gemini Batch API"
[12]: https://blog.google/innovation-and-ai/technology/developers-tools/introducing-flex-and-priority-inference/ "Google: Flex and Priority inference"

## Визуальный smoke-check dashboard

Локальный dashboard `http://127.0.0.1:8765/studio` был открыт в Chromium. Operator view отрисовал live-каталог из 43 preset-scenes, включая `DecisionGrid` и `LlmHubsCTA`; selector сцен заполнился тем же API endpoint. Действие **«Загрузить пример»** вставило структурированный `ResearchPack` в Evidence panel, не создавая render job.

Проверен и отрицательный маршрут. Исходный sample с одним источником был отклонён Evidence Gate c диагностикой `research needs at least 2 sources`; затем sample был исправлен двумя официальными страницами Ollama и claim, связанным с обоими источниками. Это подтверждает server-side fail-closed policy, а не клиентскую имитацию успеха.

Исправленный пример прошёл validation в браузере: UI отобразил `Evidence OK · research_studio_demo_ollama` и `Evidence pack прошёл fail-closed policy.` Далее из Brief panel был создан opaque draft `run_a1f9a23f330f4c29a9004b1bc93f083a`: timeline содержит `run.created`, статус — `draft`, а UI явно сообщает, что renderer не запущен и требует отдельного approval. Так проверен полный browser → FastAPI → policy validator → run service → observable timeline маршрут без неявного запуска рендера.
