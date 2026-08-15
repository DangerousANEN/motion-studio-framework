# MSF Pipeline — 10 текстовых storyboard для review

Эти черновики получены встроенным pipeline `ResearchPack → validate_research_pack → plan_from_claims → validate_script_plan → diversity_gate`. Фактические строки связаны с claim ID и source URLs из pipeline-owned evidence packs; рендера в этом pass нет.

| Показатель | Результат |
|---|---:|
| Черновиков | 10 |
| Уникальных style families | 10 |
| Уникальных opening presets | 10 |
| Factual lines с evidence claim | 30 |
| Live scene catalog при QA | 117 |

## 01. GEMINI 3.7 FLASH: ГДЕ ОН СИЛЬНЕЕ — А ГДЕ НЕТ

**Research topic:** Gemini 3.7 Flash: где он опережает Claude Sonnet 5 и сколько стоит  
**Style:** `cobalt_command`  
**Visual sequence:** `BenchmarkArena → CapabilityRadar → ClaimEvidenceChain → ProofBackedCTA`


### Текст

1. **HOOK.** НЕ ВЕРЬТЕ ФРАЗЕ «УБИЛ SONNET». СМОТРИТЕ НА КОНКРЕТНЫЙ ТЕСТ.

2. **FACT.** Google released Gemini 3.7 Flash on 13 August 2026 with introductory pricing of $0.75 per million input tokens and $3.75 per million output tokens through 31 December 2026. — evidence: `claim_g37_release_price`

3. **FACT.** In Google's published model-card table, Gemini 3.7 Flash scores above Claude Sonnet 5 on FrontierCode 1.1 Main (43.6% versus 42.7%) and Code Arena Web Development (1588 versus 1541); this is not a claim of universal superiority. — evidence: `claim_g37_specific_benchmark_edge`

4. **FACT.** At the published API list prices, Gemini 3.7 Flash costs 62.5% less per input token and 62.5% less per output token than Claude Sonnet 5 ($0.75/$3.75 versus $2/$10 per million). — evidence: `claim_g37_price_gap_sonnet`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/

- https://deepmind.google/models/model-cards/gemini-3-7-flash/

- https://www.anthropic.com/news/claude-sonnet-5



## 02. GEMINI 3.7 FLASH: ЦЕНА — ЭТО ЕЩЁ НЕ ВЫГОДА

**Research topic:** Gemini 3.7 Flash: где он опережает Claude Sonnet 5 и сколько стоит  
**Style:** `porcelain`  
**Visual sequence:** `TrueCostCalculator → CostQualityScatter → ExperimentProtocol → BrandOutroMosaic`


### Текст

1. **HOOK.** ДЕШЕВЛЕ API — НЕ ЗНАЧИТ ДЕШЕВЛЕ ВАШ WORKLOAD.

2. **FACT.** Google released Gemini 3.7 Flash on 13 August 2026 with introductory pricing of $0.75 per million input tokens and $3.75 per million output tokens through 31 December 2026. — evidence: `claim_g37_release_price`

3. **FACT.** In Google's published model-card table, Gemini 3.7 Flash scores above Claude Sonnet 5 on FrontierCode 1.1 Main (43.6% versus 42.7%) and Code Arena Web Development (1588 versus 1541); this is not a claim of universal superiority. — evidence: `claim_g37_specific_benchmark_edge`

4. **FACT.** At the published API list prices, Gemini 3.7 Flash costs 62.5% less per input token and 62.5% less per output token than Claude Sonnet 5 ($0.75/$3.75 versus $2/$10 per million). — evidence: `claim_g37_price_gap_sonnet`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/

- https://deepmind.google/models/model-cards/gemini-3-7-flash/

- https://www.anthropic.com/news/claude-sonnet-5



## 03. DEEPSEEK V4 PRO ВЫШЕЛ ИЗ PREVIEW: ЧТО МЕНЯЕТСЯ

**Research topic:** DeepSeek V4 Pro 0813: GA-релиз, agent upgrades и гибкое reasoning  
**Style:** `infrared_alert`  
**Visual sequence:** `ReleaseDelta → ProviderChat → ChangelogTerminal → ProofBackedCTA`


### Текст

1. **HOOK.** НЕ «GA» ВАЖЕН. ВАЖНО, ЧТО ТЕПЕРЬ МОЖНО ПРОВЕРИТЬ НА СВОЁМ PIPELINE.

2. **FACT.** DeepSeek announced V4 Pro GA on 13 August 2026; it is available on app/web through Expert Mode and via the API. — evidence: `claim_ds_v4pro_ga_access`

3. **FACT.** DeepSeek documents low, high and max reasoning-effort levels for V4 Pro, allowing effort to be selected by task complexity rather than always using the maximum setting. — evidence: `claim_ds_v4pro_reasoning`

4. **FACT.** The DeepSeek pricing documentation lists V4-Pro-0813 with 1M context, a 384K maximum output, JSON output, tool calls, Responses API and Anthropic API support. — evidence: `claim_ds_v4pro_capabilities`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://api-docs.deepseek.com/news/news260813/

- https://api-docs.deepseek.com/quick_start/pricing

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813



## 04. REASONING В V4 PRO: КОГДА LOW ЛУЧШЕ MAX

**Research topic:** DeepSeek V4 Pro 0813: GA-релиз, agent upgrades и гибкое reasoning  
**Style:** `violet_luxe`  
**Visual sequence:** `KineticPhrase → TradeoffSliders → PromptABLab → DecisionTree`


### Текст

1. **HOOK.** MAX НЕ ДЕЛАЕТ КАЖДЫЙ ОТВЕТ УМНЕЕ. ОН ДЕЛАЕТ ЕГО ДОРОЖЕ.

2. **FACT.** DeepSeek announced V4 Pro GA on 13 August 2026; it is available on app/web through Expert Mode and via the API. — evidence: `claim_ds_v4pro_ga_access`

3. **FACT.** DeepSeek documents low, high and max reasoning-effort levels for V4 Pro, allowing effort to be selected by task complexity rather than always using the maximum setting. — evidence: `claim_ds_v4pro_reasoning`

4. **FACT.** The DeepSeek pricing documentation lists V4-Pro-0813 with 1M context, a 384K maximum output, JSON output, tool calls, Responses API and Anthropic API support. — evidence: `claim_ds_v4pro_capabilities`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://api-docs.deepseek.com/news/news260813/

- https://api-docs.deepseek.com/quick_start/pricing

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813



## 05. DEEPSEEK PEAK/OFF-PEAK: КОГДА 50% ЭКОНОМИИ РЕАЛЬНЫ

**Research topic:** DeepSeek V4 Pro 0813: как читать текущие и новые peak/off-peak цены  
**Style:** `midnight_orbit`  
**Visual sequence:** `CalendarLaunchWindow → TokenFlowSankey → TrueCostCalculator → DecisionTree`


### Текст

1. **HOOK.** ЕСЛИ ВЫ НЕ ЗНАЕТЕ ЧАС ЗАПУСКА JOB — ВЫ НЕ ЗНАЕТЕ ЕЁ ЦЕНУ.

2. **FACT.** Before the announced 16 August change, DeepSeek lists V4 Pro at $0.003625 per million cache-hit input tokens, $0.435 per million cache-miss input tokens and $0.87 per million output tokens. — evidence: `claim_ds_current_prices`

3. **FACT.** DeepSeek says the new V4 peak/off-peak rates take effect at 16:00 UTC on 16 August 2026; for V4 Pro, the listed off-peak rates are $0.022 cache-hit input, $0.66 cache-miss input and $1.98 output per million tokens. — evidence: `claim_ds_future_offpeak`

4. **FACT.** The announced off-peak prices are future rates on 14 August 2026, so a cost estimate must label them as effective from 16 August rather than present them as today's invoice. — evidence: `claim_ds_future_not_current`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://api-docs.deepseek.com/news/news260813/

- https://api-docs.deepseek.com/quick_start/pricing



## 06. КАК НЕ ПРОПУСТИТЬ СМЕНУ ТАРИФА

**Research topic:** DeepSeek V4 Pro 0813: как читать текущие и новые peak/off-peak цены  
**Style:** `kinetic_poster`  
**Visual sequence:** `CountdownRing → DocumentMarginNotes → BrowserTour → TelegramChannelPost`


### Текст

1. **HOOK.** ТАРИФ ПОМЕНЯЛСЯ НЕ КОГДА ВЫ УВИДЕЛИ ПОСТ, А В КОНКРЕТНОЕ ВРЕМЯ UTC.

2. **FACT.** Before the announced 16 August change, DeepSeek lists V4 Pro at $0.003625 per million cache-hit input tokens, $0.435 per million cache-miss input tokens and $0.87 per million output tokens. — evidence: `claim_ds_current_prices`

3. **FACT.** DeepSeek says the new V4 peak/off-peak rates take effect at 16:00 UTC on 16 August 2026; for V4 Pro, the listed off-peak rates are $0.022 cache-hit input, $0.66 cache-miss input and $1.98 output per million tokens. — evidence: `claim_ds_future_offpeak`

4. **FACT.** The announced off-peak prices are future rates on 14 August 2026, so a cost estimate must label them as effective from 16 August rather than present them as today's invoice. — evidence: `claim_ds_future_not_current`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://api-docs.deepseek.com/news/news260813/

- https://api-docs.deepseek.com/quick_start/pricing



## 07. GROK 4.6: АГЕНТ ДОЛЬШЕ РАБОТАЕТ — НО КТО ПЛАТИТ ЗА RETRIES?

**Research topic:** Grok 4.6: новый long-running agent, API и cache-aware цена  
**Style:** `liquid_chrome`  
**Visual sequence:** `AgentRunConsole → TokenFlowSankey → ClaimEvidenceChain → ProofBackedCTA`


### Текст

1. **HOOK.** ДЛИННЫЙ AGENT RUN — НЕ ПОБЕДА, ЕСЛИ ВЫ НЕ ВИДИТЕ ЕГО СЧЁТ.

2. **FACT.** xAI released Grok 4.6 on 12 August 2026 with a stated focus on long-running agents, interactive work and visual projects. — evidence: `claim_grok46_release_focus`

3. **FACT.** The xAI model documentation lists Grok 4.6 with a 500K context window, function calling, structured outputs and reasoning capabilities. — evidence: `claim_grok46_api_capabilities`

4. **FACT.** xAI lists Grok 4.6 API pricing at $2 per million input tokens, $0.50 per million cached input tokens and $6 per million output tokens. — evidence: `claim_grok46_price_cache`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://x.ai/news/grok-4-6

- https://docs.x.ai/developers/models/grok-4.6

- https://x.ai/pricing



## 08. CACHE-AWARE ЦЕНА: КАК ЧИТАТЬ ЕЁ БЕЗ МАГИИ

**Research topic:** Grok 4.6: новый long-running agent, API и cache-aware цена  
**Style:** `aurora_flux`  
**Visual sequence:** `ThreePhoto360Drift → TrueCostCalculator → EvidenceConflictBoard → BrandOutroMosaic`


### Текст

1. **HOOK.** КЭШ МОЖЕТ СДЕЛАТЬ РЕЖИМ ДЕШЕВЛЕ. А МОЖЕТ НЕ СРАБОТАТЬ ВООБЩЕ.

2. **FACT.** xAI released Grok 4.6 on 12 August 2026 with a stated focus on long-running agents, interactive work and visual projects. — evidence: `claim_grok46_release_focus`

3. **FACT.** The xAI model documentation lists Grok 4.6 with a 500K context window, function calling, structured outputs and reasoning capabilities. — evidence: `claim_grok46_api_capabilities`

4. **FACT.** xAI lists Grok 4.6 API pricing at $2 per million input tokens, $0.50 per million cached input tokens and $6 per million output tokens. — evidence: `claim_grok46_price_cache`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://x.ai/news/grok-4-6

- https://docs.x.ai/developers/models/grok-4.6

- https://x.ai/pricing



## 09. ЧЕТЫРЕ МОДЕЛИ, ОДИН WORKLOAD: КАК СРАВНИВАТЬ ЧЕСТНО

**Research topic:** Свежая cost map: Gemini 3.7 Flash, DeepSeek V4 Pro 0813, Grok 4.6 и Claude Sonnet 5  
**Style:** `coral_creator`  
**Visual sequence:** `TelegramChannelPost → BenchmarkHeatmap → TradeoffSliders → CommunityFAQ`


### Текст

1. **HOOK.** ЛУЧШАЯ МОДЕЛЬ В ТАБЛИЦЕ МОЖЕТ БЫТЬ ХУДШЕЙ ДЛЯ ВАШЕГО ПРОДУКТА.

2. **FACT.** For the published standard/list input prices captured on 14 August 2026, Gemini 3.7 Flash is $0.75, DeepSeek V4 Pro is $0.435 cache-miss, Grok 4.6 is $2 and Claude Sonnet 5 is $2 per million input tokens. — evidence: `claim_costmap_input`

3. **FACT.** For the published standard/list output prices captured on 14 August 2026, Gemini 3.7 Flash is $3.75, DeepSeek V4 Pro is $0.87, Grok 4.6 is $6 and Claude Sonnet 5 is $10 per million output tokens. — evidence: `claim_costmap_output`

4. **FACT.** Token list price alone is not a quality ranking: providers publish different cache prices, context conditions, effort controls and benchmark methodologies, so a production choice needs a task-specific test. — evidence: `claim_costmap_not_benchmark`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing

- https://api-docs.deepseek.com/quick_start/pricing

- https://docs.x.ai/developers/models/grok-4.6

- https://www.anthropic.com/news/claude-sonnet-5



## 10. АВГУСТОВСКАЯ COST MAP: С ЧЕГО НАЧАТЬ ТЕСТ

**Research topic:** Свежая cost map: Gemini 3.7 Flash, DeepSeek V4 Pro 0813, Grok 4.6 и Claude Sonnet 5  
**Style:** `pixel_arcade`  
**Visual sequence:** `ColdOpenContradiction → ContextWindowLadder → DecisionTree → BrandOutroMosaic`


### Текст

1. **HOOK.** НЕ НУЖНО ТЕСТИРОВАТЬ ДЕСЯТЬ МОДЕЛЕЙ. НУЖНО ОТСЕЯТЬ ЛИШНИЕ.

2. **FACT.** For the published standard/list input prices captured on 14 August 2026, Gemini 3.7 Flash is $0.75, DeepSeek V4 Pro is $0.435 cache-miss, Grok 4.6 is $2 and Claude Sonnet 5 is $2 per million input tokens. — evidence: `claim_costmap_input`

3. **FACT.** For the published standard/list output prices captured on 14 August 2026, Gemini 3.7 Flash is $3.75, DeepSeek V4 Pro is $0.87, Grok 4.6 is $6 and Claude Sonnet 5 is $10 per million output tokens. — evidence: `claim_costmap_output`

4. **FACT.** Token list price alone is not a quality ranking: providers publish different cache prices, context conditions, effort controls and benchmark methodologies, so a production choice needs a task-specific test. — evidence: `claim_costmap_not_benchmark`

5. **CTA.** Подписывайтесь на @llm_hubs: там больше практичных разборов LLM.


### Источники

- https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing

- https://api-docs.deepseek.com/quick_start/pricing

- https://docs.x.ai/developers/models/grok-4.6

- https://www.anthropic.com/news/claude-sonnet-5


