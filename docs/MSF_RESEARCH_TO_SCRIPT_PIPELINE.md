# MSF Research-to-Script Pipeline

## Назначение

`Research-to-Script` — встроенный в MSF локальный workflow, который принимает тему ролика и возвращает готовый к проверке набор артефактов: проверяемый `ResearchPack`, короткий русскоязычный `ScriptPlan` и связанный с ним `StoryboardDraft`. Он заменяет зависимость от отдельной установки Local Deep Research для базового сценарного пути, но не запрещает сохранить прежний bridge как compatibility fallback для уже настроенных машин.

В основе лежат идеи из [LearningCircuit/local-deep-research](https://github.com/LearningCircuit/local-deep-research): ограниченная декомпозиция темы, индексированный сбор источников, дедупликация ссылок, ограниченные бюджеты поиска и отказ от сценария, если доказательная база не собрана. Новый MSF-модуль реализует эти идеи нативно и с минимальными зависимостями; исходный код LDR не включается целиком. Внешний reference распространяется по MIT License.

> **Главное правило:** модель не получает права выдавать текст из памяти за исследование. Фактическая реплика сценария возможна только после связи с `EvidenceClaim`, а каждый `EvidenceClaim` — только после валидации ссылок в `ResearchPack`.

## Вход и выход

| Артефакт | Роль |
|---|---|
| `ResearchToScriptRequest` | Тема, аудитория, Telegram handle и конкретный CTA asset, лимиты исследования, опциональные style family и release marker. |
| `ResearchPack` | Нормализованные источники, публикационные даты, excerpt и claim graph; проходит существующий `validate_research_pack`. |
| `ScriptPlan` | Структура `hook → explanation → proof → takeaway → CTA`; factual lines привязаны к claim IDs. |
| `StoryboardDraft` | Уникальные preset scenes, единый `default_style_kit`, recipe audio и evidence links для proof beats. |
| `ResearchToScriptResult` | Объединяет все артефакты, observable milestones и безопасные diagnostics без скрытых рассуждений модели. |

## Оркестрация

Workflow собирается через существующий MSF LangGraph runtime. Он намеренно ограничен шестью deterministic nodes, поэтому слабый агент не может обходить policy, а сильный агент получает редактируемые contracts, а не свободный shell-доступ.

| Этап | Что делает | Fail-closed условие |
|---|---|---|
| `plan_queries` | Разбивает тему на 2–4 нейтральных поисковых вопроса: официальный релиз, возможности/ограничения, цена/доступность, независимая проверка. | Пустая или дублирующаяся query plan. |
| `collect_sources` | Ищет через встроенный provider; удаляет дубли, локальные адреса и небезопасные URL. | Меньше двух пригодных источников. |
| `fetch_evidence` | Забирает и очищает текст страниц только с публичных HTTP(S) URL; ограничивает размер, время и число страниц. | Нет пригодных excerpt для подтверждения facts. |
| `build_claims` | Использует structured LLM output для формирования кратких утверждений и допускает только source IDs из набора. | Claim с неизвестным source ID, без source или с невалидной схемой. |
| `validate_evidence` | Запускает существующие MSF freshness, primary-source и cost/availability gates. | Любая `ResearchQualityError`. |
| `compose_script` | Выбирает 1–2 claims вокруг одной viewer question и вызывает `plan_from_angle`; затем строит storyboard из live catalog. | Неподдержанный факт, повтор preset, больше одного style family или невалидный storyboard. |

## Local research provider contract

Нативный путь использует интерфейс `SearchProvider`, а не жёстко привязан к конкретной поисковой системе. Первая реализация поддерживает публичный DuckDuckGo search без API key и опциональный совместимый SearXNG endpoint через environment configuration. Сторонний LDR subprocess не требуется.

`SearchProvider` не возвращает готовые выводы модели: только title, URL, publisher hint, excerpt и publication metadata, если они доступны. URL дополнительно проходят SSRF guard: запрещаются `file:`, `data:`, `localhost`, loopback, private и link-local IP ranges. Page fetching разрешён только для прошедших guard источников и строго ограничен по времени и объёму.

## Russian audience policy

Сценарий создаётся только на русском. Неразъяснённый технический жаргон блокируется до сохранения: `GA`, `Preview`, `General Availability`, `model card`, `reasoning`, `workload`, `agent run`, `cache-aware`, `cache hit/miss`, `pipeline`, `retry`. Название продукта или официальный тариф могут сохраняться, но вывод должен объясняться обычными словами.

Сценарная структура всегда одинакова по функции, но не по тексту:

1. **Hook.** Короткий вопрос или контраст, без неподтверждённых цифр и обещаний.
2. **Explanation.** Первая выбранная доказанная мысль отвечает, почему тема вообще важна зрителю.
3. **Proof.** Вторая доказанная мысль или источник показывает, на чём основан вывод.
4. **Takeaway.** Практическое действие, поддержанное теми же claim IDs.
5. **CTA.** Telegram handle плюс конкретный asset: таблица цен, готовый промпт, ссылки на источники, чек-лист или сравнение.

## Storyboard policy

Генератор выбирает preset только из live MSF catalog, не повторяет preset внутри одного ролика и назначает ровно одну style family на весь `StoryboardDraft`. Opening preset выбирается из отдельной rotation pool; оставшиеся сцены подбираются по ролям `explanation`, `evidence`, `proof`, `takeaway` и `cta`. На каждой factual storyboard scene остаются исходные `evidence_claim_ids`.

Результат возвращается как draft и не запускает render. Для видео требуется уже существующее отдельное explicit approval действие.

## Наблюдаемость

В API и MCP доступны только безопасные milestones: `query_plan_created`, `sources_collected`, `pages_extracted`, `claims_validated`, `script_composed`, `storyboard_validated`. Скрытые рассуждения LLM, API keys, raw prompts и полный контент непрошедших источников не сохраняются в timeline.

## Configuration

| Переменная | Значение по умолчанию | Назначение |
|---|---:|---|
| `MSF_RESEARCH_MODEL` | `gpt-5-mini` | Модель для структуры queries, claims и angle. |
| `MSF_RESEARCH_SEARCH_PROVIDER` | `duckduckgo` | `duckduckgo` или `searxng`. |
| `MSF_RESEARCH_SEARXNG_URL` | — | Public SearXNG-compatible endpoint, нужен только при provider `searxng`. |
| `MSF_RESEARCH_MAX_QUERIES` | `4` | Верхняя граница search decomposition. |
| `MSF_RESEARCH_MAX_SOURCES` | `8` | Верхняя граница fetched source pages. |
| `MSF_RESEARCH_TIMEOUT_SECONDS` | `15` | Request timeout для поиска и page fetch. |

При отсутствии реальных источников workflow возвращает error. Он не переключается на генерацию «по памяти».

## Compatibility

Существующий `msf.skills_bridge.deep_research` сохраняется как legacy integration для пользователей, уже настроивших внешнюю LDR среду. Новый Studio workflow не импортирует его и не требует отдельного virtualenv, Docker или LDR runtime.

## Проверки

Минимальный release gate включает deterministic unit tests на URL safety, deduplication, source-to-claim linking, jargon rejection, no-repeat preset selection и API/MCP contract. Один fixture-based demo run подтверждает полный путь без обращения к сети или модели; отдельный opt-in live run используется только при наличии network и LLM configuration.

## References

[1] [LearningCircuit/local-deep-research — source repository and MIT license](https://github.com/LearningCircuit/local-deep-research)
[2] [MSF evidence policy — `msf/studio/research.py`](../msf/studio/research.py)
[3] [MSF script planner — `msf/studio/script_planner.py`](../msf/studio/script_planner.py)
[4] [MSF storyboard validator — `msf/studio/storyboard.py`](../msf/studio/storyboard.py)


## Проверенные primary-source маршруты

Для provider-specific тем workflow не принимает зеркала документации за официальный источник. В частности, проверенная страница OpenAI о rate limits доступна по адресу `https://developers.openai.com/api/docs/guides/rate-limits`; прежний `platform.openai.com/docs/guides/rate-limits` перенаправляет на этот домен. Native source routing использует `developers.openai.com` как допустимый официальный host для OpenAI API documentation.


## Evidence-first side-by-side comparison

Для model-versus-model ролика native request принимает `comparison_mode`, `comparison_models`, `visual_evidence_mode` и `require_observed_comparison`. Результат содержит typed `ComparisonProof` наряду с research, script и storyboard; timeline фиксирует milestone `comparison_proof_validated`.

`observed` разрешён только при одной задаче, сопоставимых условиях, связанных evidence claims и URL результата/источника, уже извлечённого в research pack. Если публичная пара результатов не найдена, workflow возвращает `proposed` с `inconclusive` outcome и не называет победителя. Такой draft показывает зрителю план честного A/B теста: `ColdOpenContradiction → PromptABLab → EvidenceConflictBoard → ClaimEvidenceChain → CTA`.

Полный contract, visual mapping и source policy находятся в [MSF comparison-proof policy](MSF_COMPARISON_PROOF_POLICY.md).
