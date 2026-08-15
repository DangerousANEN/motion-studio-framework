# MSF Pipeline — 10 текстовых storyboard для review

Эти черновики получены встроенным pipeline `ResearchPack → validate_research_pack → plan_from_claims → validate_script_plan → evidence-preserving_ru → language_hygiene → diversity_gate`. Зрительская narration полностью локализована на русский; factual lines сохраняют исходные claim ID и source URLs. Рендера в этом pass нет.

| Показатель | Результат |
|---|---:|
| Черновиков | 10 |
| Уникальных style families | 10 |
| Уникальных opening presets | 10 |
| Factual lines с evidence claim | 30 |
| Live scene catalog при QA | 117 |

## 01. GEMINI 3.7 FLASH: где он сильнее, а где слабее

**Research topic:** Gemini 3.7 Flash: где он опережает Claude Sonnet 5 и сколько стоит  
**Style:** `cobalt_command`  
**Visual sequence:** `BenchmarkArena → CapabilityRadar → ClaimEvidenceChain → ProofBackedCTA`


### Текст

1. **HOOK.** Не верьте «убил Sonnet» — смотрите конкретный тест.

2. **FACT.** Google выпустил Gemini 3.7 Flash 13 августа 2026 с вводной ценой $0.75 за миллион входных токенов и $3.75 за миллион выходных токенов до 31 декабря 2026. — evidence: `claim_g37_release_price`

3. **FACT.** В опубликованной Google таблице карте модели Gemini 3.7 Flash опережает Claude Sonnet 5 по FrontierCode 1.1 Main (43.6% против 42.7%) и по Code Arena Web Development (1588 против 1541); это не заявление о всеобщем превосходстве. — evidence: `claim_g37_specific_benchmark_edge`

4. **FACT.** По опубликованным ценам API Gemini 3.7 Flash дешевле на 62.5% за входной токен и на 62.5% за выходной токен, чем Claude Sonnet 5 ($0.75/$3.75 против $2/$10 за миллион). — evidence: `claim_g37_price_gap_sonnet`

5. **CTA.** Подписывайтесь на @llm_hubs — там больше практичных разборов LLM.


### Источники

- https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/

- https://deepmind.google/models/model-cards/gemini-3-7-flash/

- https://www.anthropic.com/news/claude-sonnet-5



## 02. GEMINI 3.7 FLASH: ЦЕНА — ЭТО ЕЩЁ НЕ ВЫГОДА

**Research topic:** Gemini 3.7 Flash: где он опережает Claude Sonnet 5 и сколько стоит  
**Style:** `porcelain`  
**Visual sequence:** `TrueCostCalculator → CostQualityScatter → ExperimentProtocol → BrandOutroMosaic`


### Текст

1. **HOOK.** Дешевле API не делает ваши расходы дешевле.

2. **FACT.** Google выпустил Gemini 3.7 Flash 13 августа 2026; вводные цены $0.75 за млн входных токенов и $3.75 за млн выходных токенов до 31 декабря 2026. — evidence: `claim_g37_release_price`

3. **FACT.** В таблице карте модели Google Gemini 3.7 Flash опережает Claude Sonnet 5 по FrontierCode 1.1 Main (43.6% против 42.7%) и по Code Arena Web Development (1588 против 1541); это не претензия на абсолютное превосходство. — evidence: `claim_g37_specific_benchmark_edge`

4. **FACT.** По опубликованным ценам API Gemini 3.7 Flash на 62.5% дешевле за входной токен и на 62.5% дешевле за выходной токен, чем Claude Sonnet 5 ($0.75/$3.75 против $2/$10 за млн). — evidence: `claim_g37_price_gap_sonnet`

5. **CTA.** Подпишитесь на @llm_hubs — там больше практичных разборов LLM.


### Источники

- https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/

- https://deepmind.google/models/model-cards/gemini-3-7-flash/

- https://www.anthropic.com/news/claude-sonnet-5



## 03. DeepSeek V4 Pro вышел из Preview — что меняется

**Research topic:** DeepSeek V4 Pro 0813: GA-релиз, agent upgrades и гибкое reasoning  
**Style:** `infrared_alert`  
**Visual sequence:** `ReleaseDelta → ProviderChat → ChangelogTerminal → ProofBackedCTA`


### Текст

1. **HOOK.** Важно не «GA», а возможность проверить на своём пайплайне.

2. **FACT.** DeepSeek объявил V4 Pro GA 13 августа 2026; доступен в приложении и на вебе в режиме Expert Mode и по API. — evidence: `claim_ds_v4pro_ga_access`

3. **FACT.** DeepSeek описывает уровни уровни рассуждений: low, high и max для V4 Pro — можно выбирать усилие по сложности задачи, а не всегда ставить максимум. — evidence: `claim_ds_v4pro_reasoning`

4. **FACT.** В документации по ценообразованию DeepSeek указан V4-Pro-0813: 1M контекст, максимум вывода 384K, JSON-вывод, вызовы инструментов, поддержка Responses API и Anthropic API. — evidence: `claim_ds_v4pro_capabilities`

5. **CTA.** Подписывайтесь на @llm_hubs — практичные разборы LLM.


### Источники

- https://api-docs.deepseek.com/news/news260813/

- https://api-docs.deepseek.com/quick_start/pricing

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813



## 04. Рассуждение в V4 Pro — когда low лучше max

**Research topic:** DeepSeek V4 Pro 0813: GA-релиз, agent upgrades и гибкое reasoning  
**Style:** `violet_luxe`  
**Visual sequence:** `KineticPhrase → TradeoffSliders → PromptABLab → DecisionTree`


### Текст

1. **HOOK.** MAX не делает каждый ответ умнее — он делает его дороже.

2. **FACT.** DeepSeek объявила V4 Pro GA 13 августа 2026; доступна в приложении и на вебе в режиме Expert Mode и через API. — evidence: `claim_ds_v4pro_ga_access`

3. **FACT.** DeepSeek описывает уровни уровни рассуждений — low, high и max для V4 Pro, чтобы выбирать усилие по сложности задачи вместо постоянного использования max. — evidence: `claim_ds_v4pro_reasoning`

4. **FACT.** Документация по ценам DeepSeek перечисляет V4-Pro-0813: контекст 1M, максимум вывода 384K, JSON-вывод, вызовы инструментов, поддержка Responses API и Anthropic API. — evidence: `claim_ds_v4pro_capabilities`

5. **CTA.** Подписывайтесь на @llm_hubs — там больше практичных разборов LLM.


### Источники

- https://api-docs.deepseek.com/news/news260813/

- https://api-docs.deepseek.com/quick_start/pricing

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813



## 05. DeepSeek — пиковые и внепиковые тарифы: когда 50% экономии реальны

**Research topic:** DeepSeek V4 Pro 0813: как читать текущие и новые peak/off-peak цены  
**Style:** `midnight_orbit`  
**Visual sequence:** `CalendarLaunchWindow → TokenFlowSankey → TrueCostCalculator → DecisionTree`


### Текст

1. **HOOK.** Если вы не знаете время запуска задачи — вы не знаете её цену.

2. **FACT.** До объявленного изменения 16 августа DeepSeek указывал V4 Pro: $0.003625 за миллион входных токенов с попаданием в кэш, $0.435 за миллион входных токенов без попадания в кэш и $0.87 за миллион выходных токенов. — evidence: `claim_ds_current_prices`

3. **FACT.** DeepSeek сообщает, что новые пиковые/внепиковые ставки V4 вступают в силу в 16:00 UTC 16 августа 2026; для V4 Pro указаны внепиковые ставки: $0.022 за миллион входных токенов с попаданием в кэш, $0.66 за миллион входных токенов без попадания в кэш и $1.98 за миллион выходных токенов. — evidence: `claim_ds_future_offpeak`

4. **FACT.** Объявленные внепиковые цены — будущие ставки по состоянию на 14 августа 2026, поэтому смету нужно помечать как действующую с 16 августа, а не как сегодняшнюю. — evidence: `claim_ds_future_not_current`

5. **CTA.** Подписывайтесь на @llm_hubs — там больше практичных разборов LLM.


### Источники

- https://api-docs.deepseek.com/news/news260813/

- https://api-docs.deepseek.com/quick_start/pricing



## 06. Как не пропустить смену тарифа

**Research topic:** DeepSeek V4 Pro 0813: как читать текущие и новые peak/off-peak цены  
**Style:** `kinetic_poster`  
**Visual sequence:** `CountdownRing → DocumentMarginNotes → BrowserTour → TelegramChannelPost`


### Текст

1. **HOOK.** Тариф меняется не в момент просмотра поста, а в указанное время по UTC.

2. **FACT.** До объявленного изменения 16 августа DeepSeek указывает цену V4 Pro: $0.003625 за миллион входных токенов с кэшированного входа, $0.435 за миллион входных токенов с некэшированного входа и $0.87 за миллион выходных токенов. — evidence: `claim_ds_current_prices`

3. **FACT.** DeepSeek сообщает, что новые пиковые/внепиковые тарифы V4 вступают в силу в 16:00 UTC 16 августа 2026; для V4 Pro указаны внепиковые цены: $0.022 за миллион входных токенов с кэшированного входа, $0.66 за миллион входных токенов с некэшированного входа и $1.98 за миллион выходных токенов. — evidence: `claim_ds_future_offpeak`

4. **FACT.** Объявленные внепиковые цены на 14 августа 2026 — будущие ставки, поэтому оценка затрат должна пометить их как вступающие в силу с 16 августа, а не выдавать за текущий счёт. — evidence: `claim_ds_future_not_current`

5. **CTA.** Подписывайтесь на @llm_hubs — там больше практичных разборов LLM.


### Источники

- https://api-docs.deepseek.com/news/news260813/

- https://api-docs.deepseek.com/quick_start/pricing



## 07. GROK 4.6: агент работает дольше — кто платит за повторы?

**Research topic:** Grok 4.6: новый long-running agent, API и cache-aware цена  
**Style:** `liquid_chrome`  
**Visual sequence:** `AgentRunConsole → TokenFlowSankey → ClaimEvidenceChain → ProofBackedCTA`


### Текст

1. **HOOK.** Длительная работа агента — не победа, если вы не видите его счёт.

2. **FACT.** xAI выпустила Grok 4.6 12 августа 2026 с заявленным фокусом на долго работающих агентах, интерактивной работе и визуальных проектах. — evidence: `claim_grok46_release_focus`

3. **FACT.** Документация xAI указывает для Grok 4.6 500K контекстное окно, вызов функций, структурированные ответы и возможности рассуждения. — evidence: `claim_grok46_api_capabilities`

4. **FACT.** xAI указывает цену API Grok 4.6: $2 за миллион входных токенов, $0.50 за миллион кэшированных входных токенов и $6 за миллион выходных токенов. — evidence: `claim_grok46_price_cache`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://x.ai/news/grok-4-6

- https://docs.x.ai/developers/models/grok-4.6

- https://x.ai/pricing



## 08. Цена с учётом кэша: как читать без магии

**Research topic:** Grok 4.6: новый long-running agent, API и cache-aware цена  
**Style:** `aurora_flux`  
**Visual sequence:** `ThreePhoto360Drift → TrueCostCalculator → EvidenceConflictBoard → BrandOutroMosaic`


### Текст

1. **HOOK.** Кэш может удешевить режим — а может и не сработать вовсе.

2. **FACT.** xAI выпустила Grok 4.6 12 августа 2026 с заявленным фокусом на длительные агенты, интерактивные задачи и визуальные проекты. — evidence: `claim_grok46_release_focus`

3. **FACT.** В документации xAI для Grok 4.6 указано окно контекста 500K, вызов функций, структурированные ответы и способности к рассуждению. — evidence: `claim_grok46_api_capabilities`

4. **FACT.** xAI указывает цену API Grok 4.6: $2 за миллион входных токенов, $0.50 за миллион кэшированных входных токенов и $6 за миллион выходных токенов. — evidence: `claim_grok46_price_cache`

5. **CTA.** Подписывайтесь на @llm_hubs — там больше практичных разборов LLM.


### Источники

- https://x.ai/news/grok-4-6

- https://docs.x.ai/developers/models/grok-4.6

- https://x.ai/pricing



## 09. Четыре модели, одна нагрузка: как честно сравнить

**Research topic:** Свежая cost map: Gemini 3.7 Flash, DeepSeek V4 Pro 0813, Grok 4.6 и Claude Sonnet 5  
**Style:** `coral_creator`  
**Visual sequence:** `TelegramChannelPost → BenchmarkHeatmap → TradeoffSliders → CommunityFAQ`


### Текст

1. **HOOK.** Лучший в таблице может оказаться хуже для вашего продукта.

2. **FACT.** Опубликованные стандартные/списочные цены на вход, зафиксированные 14 августа 2026: Gemini 3.7 Flash — $0.75, DeepSeek V4 Pro — $0.435 при промахе кэша, Grok 4.6 — $2 и Claude Sonnet 5 — $2 за миллион входных токенов. — evidence: `claim_costmap_input`

3. **FACT.** Опубликованные стандартные/списочные цены на выход, зафиксированные 14 августа 2026: Gemini 3.7 Flash — $3.75, DeepSeek V4 Pro — $0.87, Grok 4.6 — $6 и Claude Sonnet 5 — $10 за миллион выходных токенов. — evidence: `claim_costmap_output`

4. **FACT.** Цена за токен в прайсе сама по себе не является рейтингом качества: провайдеры публикуют разные цены с учётом кэша, условия контекста, настройки усилий и методики бенчмарков, поэтому выбор для боевой эксплуатации требует теста, специфичного для задачи. — evidence: `claim_costmap_not_benchmark`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing

- https://api-docs.deepseek.com/quick_start/pricing

- https://docs.x.ai/developers/models/grok-4.6

- https://www.anthropic.com/news/claude-sonnet-5



## 10. Августовая карта затрат: с чего начать тест

**Research topic:** Свежая cost map: Gemini 3.7 Flash, DeepSeek V4 Pro 0813, Grok 4.6 и Claude Sonnet 5  
**Style:** `pixel_arcade`  
**Visual sequence:** `ColdOpenContradiction → ContextWindowLadder → DecisionTree → BrandOutroMosaic`


### Текст

1. **HOOK.** Не нужно тестировать десять моделей. Отсеиваем лишние.

2. **FACT.** По опубликованным стандартным входным ценам, зафиксированным 14 августа 2026: Gemini 3.7 Flash — $0.75 за миллион входных токенов; DeepSeek V4 Pro — $0.435 (некэшированного входа) за миллион входных токенов; Grok 4.6 — $2 за миллион входных токенов; Claude Sonnet 5 — $2 за миллион входных токенов. — evidence: `claim_costmap_input`

3. **FACT.** По опубликованным стандартным выходным ценам, зафиксированным 14 августа 2026: Gemini 3.7 Flash — $3.75 за миллион выходных токенов; DeepSeek V4 Pro — $0.87 за миллион выходных токенов; Grok 4.6 — $6 за миллион выходных токенов; Claude Sonnet 5 — $10 за миллион выходных токенов. — evidence: `claim_costmap_output`

4. **FACT.** Цена токенов из прайс‑листа не равна рангу качества: провайдеры дают разные кеш‑цены, условия контекста, параметры усилий и методики тестирования, поэтому для продакшна нужен тест по задаче. — evidence: `claim_costmap_not_benchmark`

5. **CTA.** Подписывайтесь на @llm_hubs — там больше практичных разборов LLM.


### Источники

- https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing

- https://api-docs.deepseek.com/quick_start/pricing

- https://docs.x.ai/developers/models/grok-4.6

- https://www.anthropic.com/news/claude-sonnet-5


