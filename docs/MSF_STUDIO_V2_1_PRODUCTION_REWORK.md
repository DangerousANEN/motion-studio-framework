# MSF Studio v2.1 — Production Rework

**Дата:** 14 августа 2026, GMT+7  
**Статус:** пересобранный локальный release и серия из пяти роликов готовы к передаче.

## Что было исправлено

Переиздание заменяет прежнюю evergreen-серию на релизные темы, проверенные по первичным источникам. При этом оно не утверждает, что одна модель «лучшая вообще»: сравнения ограничены опубликованными ценами и конкретно указанными метриками. Каждый factual block связан с claim ID из `projects/llm_hubs/evidence_packs_2026-08-14.json` и проходит release-freshness gate.

| Направление | Реализация v2.1 |
|---|---|
| Editorial research | Gemini 3.7 Flash vs Sonnet 5, DeepSeek V4 Pro 0813 (GA и тарифная дата), Grok 4.6 и актуальная cost map. Все пять packs отмечены `release_topic=true`, имеют дату релиза и official/primary source. |
| Стиль | Введён `styleConfig` как типизированный contract: palette, backdrop, surfaces, typography, motion и PostFX. `llm_hubs_neon` — один из шести selectable visual families, а не глобально зафиксированная тема. |
| Visual families | `llm_hubs_neon`, `product_tutorial`, `terminal`, `creator_glass`, `social_native`, `editorial`; dashboard и MCP отдают один catalog разрешённых override tokens. |
| Media / guides | Добавлены `ScreenGuide`, `TelegramVoiceRound`, `YouTubeCard`, `ImageSpotlight`, cursor/focus/CTA HUD overlays и agent workflow для разрешённых screen recordings, изображений и video inserts. |
| Motion | `HeroKinetic` и `QuoteCard` переведены на style context. Release-safe LLM Hubs motion использует мягкий вход и reading dwell без pop tilt, flicker и chromatic jitter на тексте. |
| Audio | Для каждого ролика создана русская voice-over дорожка, общий оригинальный instrumental neon-tech bed, speech-aware ducking и 6–7 scene-timed procedural SFX. Master WAV синхронизирован с длительностью каждого VideoSpec и подключён как `audioUrl` в финальный Remotion render. |

> **Арт-дирекшен серии:** near-black technical background, neon-green primary action color, restrained aqua secondary accent, white body type и dark glass surfaces. Золотые и янтарные карточки запрещены для LLM Hubs release style.

## Актуальная серия

| Ролик | Фокус | Scene sequence | Runtime | Audio |
|---|---|---|---:|---|
| `01_gemini37_flash_vs_sonnet5.mp4` | Узкое price/benchmark comparison Gemini 3.7 Flash и Sonnet 5 | HeroKinetic → MetricTrend → DecisionGrid → QuoteCard → CTA | 33.51 s | Voice + music ducking + 6 cues |
| `02_deepseek_v4pro_0813.mp4` | DeepSeek V4 Pro GA, Expert Mode и reasoning effort | AiChatStream → TgChat → StepList → CodeReveal → CTA | 34.94 s | Voice + music ducking + 6 cues |
| `03_deepseek_v4pro_cost_clock.mp4` | Дата действия V4 Pro peak/off-peak pricing | CountdownHero → FlowDiagram → BeforeAfter → StatCounter → CTA | 31.96 s | Voice + music ducking + 6 cues |
| `04_grok46_long_agent.mp4` | Grok 4.6 для long-running agents и cache-aware API framing | HeroKinetic → TimelineReveal → MetricTrend → CodeReveal → CTA | 32.45 s | Voice + music ducking + 6 cues |
| `05_august_model_costmap.mp4` | Сравнение актуальных input/output API list prices | Leaderboard → DonutFill → CompareSplit → DecisionGrid → CTA | 35.52 s | Voice + music ducking + 7 cues |

## Research scope and factual grounding

Google объявил Gemini 3.7 Flash 13 августа 2026 года с указанной introductory ценой $0.75/$3.75 за миллион input/output tokens; опубликованная Google model card содержит конкретные сравнения с Claude Sonnet 5, которые в ролике обозначены как узкие, а не универсальный рейтинг.[1] [2] Anthropic указывает для Sonnet 5 $2/$10 за миллион input/output tokens.[3]

DeepSeek объявил V4 Pro GA 13 августа 2026 года, описал Expert Mode/API access и управляемые levels reasoning effort. Его pricing documentation отделяет текущую pricing table от peak/off-peak schedule, действующей с 16 августа; третий ролик специально не выдаёт будущую off-peak цену за текущую.[4] [5]

xAI анонсировал Grok 4.6 12 августа 2026 года. Developer docs перечисляют 500K context, tool/function calling, structured outputs, reasoning и API list prices, на которых основан четвёртый ролик.[6] [7]

## QA и release gates

| Проверка | Итог |
|---|---|
| Evidence gates | `check_studio_research.py` и параметризованный `check_llm_hubs_evidence.py` прошли для release packs. |
| Renderer / contracts | `tsc --noEmit -p tsconfig.studio.json`, `check_studio_v2.py` и `check_style_media_contract.py` прошли. |
| API / operator | `check_studio_api.py` проверил `/api/studio/styles` и draft run с сохранёнными `style`/`style_config`. Dashboard визуально отобразил family picker, token controls и 47 scene catalog items. |
| MCP | Real stdio protocol check подтвердил 9 tools, включая `list_style_families`, а также live scene/style discovery. |
| Output integrity | Все финальные MP4: H.264, AAC stereo 48 kHz, 720×1280. Первоначальная enum ошибка `DonutFill.centerContent` в ролике 05 устранена и ролик перерендерен до штатной длительности 35.52 s. |
| Audio | Master tracks: mean −21.6…−19.2 dBFS, max −1.3…−0.7 dBFS; прежний фактически тихий фон заменён слышимым music bed под русской narration. |
| Visual | Mid-roll contact sheet подтверждает отсутствие gold/amber cards и различие scene layouts. CTA contact sheet подтверждает единый @llm_hubs final с круглой avatar и неоновой зелёной кнопкой. |

## Как использовать новые возможности

Operator может открыть `http://127.0.0.1:8765/studio`, выбрать scene, tier и visual family, затем безопасно настроить neon/background/surface/bloom. Кнопка подготовки создаёт только draft run; renderer по-прежнему требует отдельного approval.

Агент получает style families через `GET /api/studio/styles`, `msf://styles` или MCP tool `list_style_families`. Для guides и реальных assets следует использовать `skills/msf-studio/workflows/media-guide.md`; он ограничивает preset-tier agent stable scenes и allowlisted props для screen capture, crop/zoom/pan, focus frame и deterministic cursor path.

## References

[1]: https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/ "Google — Introducing Gemini 3.7 Flash"
[2]: https://deepmind.google/models/model-cards/gemini-3-7-flash/ "Google DeepMind — Gemini 3.7 Flash Model Card"
[3]: https://www.anthropic.com/news/claude-sonnet-5 "Anthropic — Introducing Claude Sonnet 5"
[4]: https://api-docs.deepseek.com/news/news260813/ "DeepSeek — V4 Pro GA Release"
[5]: https://api-docs.deepseek.com/quick_start/pricing "DeepSeek — Models and Pricing"
[6]: https://x.ai/news/grok-4-6 "xAI — Introducing Grok 4.6"
[7]: https://docs.x.ai/developers/models/grok-4.6 "xAI — Grok 4.6 Developer Documentation"
