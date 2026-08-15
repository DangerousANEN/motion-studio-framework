# MSF Pipeline V2 — 10 text-only storyboard для review

Это второй batch: каждый ролик строится по схеме **один зрительский вопрос → 1–2 выбранных evidence claims → практический вывод → конкретный Telegram asset**.

| Gate | Результат |
|---|---:|
| Черновиков | 10 |
| Уникальных styles/openings | 10 / 10 |
| Selected claims на ролик | 1–2 |
| Конкретных CTA assets | 10 |
| Связанных evidence links | 32 |

## 01. Gemini 3.7 Flash: один тест, который ломает хайп

**Style:** `cobalt_command`  
**Visual sequence:** `BenchmarkArena → CapabilityRadar → ExperimentProtocol → ProofBackedCTA`  
**Зрительский вопрос / takeaway:** Проверьте именно свою coding-задачу: две метрики — это повод для теста, а не для вердикта о «лучшем ИИ».  
**Telegram asset:** таблица двух тестов и шаблон своей проверки


### Текст

1. **HOOK.** Коротко: Gemini не «убил» Sonnet, но в двух тестах он впереди.

2. **FACT.** По карточке модели от Google Gemini 3.7 Flash опережает Claude Sonnet 5: FrontierCode 1.1 Main (43.6% vs 42.7%), Code Arena Web Development (1588 vs 1541); это не претензия на универсальное превосходство.

3. **INSTRUCTION.** Проверьте вашу конкретную задачу по программированию: две метрики — повод для теста, не для вердикта о «лучшем ИИ».

4. **CTA.** Заберите таблица двух тестов и шаблон своей проверки в @llm_hubs.


### Источники
- https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/
- https://deepmind.google/models/model-cards/gemini-3-7-flash/
- https://www.anthropic.com/news/claude-sonnet-5


## 02. Gemini дешевле Sonnet? Сначала посчитайте свой сценарий

**Style:** `porcelain`  
**Visual sequence:** `TrueCostCalculator → CostQualityScatter → PromptABLab → BrandOutroMosaic`  
**Зрительский вопрос / takeaway:** Сначала сравните стоимость одной законченной задачи, а не цену миллиона токенов в прайсе.  
**Telegram asset:** калькулятор стоимости одной задачи


### Текст

1. **HOOK.** Цена API ниже на 62,5%. Но ваш продукт может не стать дешевле.

2. **FACT.** Google выпустил Gemini 3.7 Flash 13 August 2026 с вводной ценой $0.75 за миллион входных токенов и $3.75 за миллион выходных токенов до 31 December 2026.

3. **FACT.** По опубликованным ценам API Gemini 3.7 Flash на 62,5% дешевле за входной токен и за выходной токен, чем Claude Sonnet 5 ($0.75/$3.75 versus $2/$10 per million).

4. **INSTRUCTION.** Сначала сравните стоимость одной законченной задачи, а не цену миллиона токенов в прайсе.

5. **CTA.** Заберите калькулятор стоимости одной задачи в @llm_hubs.


### Источники
- https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/
- https://deepmind.google/models/model-cards/gemini-3-7-flash/
- https://www.anthropic.com/news/claude-sonnet-5


## 03. DeepSeek V4 Pro: что реально стало доступно

**Style:** `infrared_alert`  
**Visual sequence:** `ReleaseDelta → ProviderChat → ScreenMagnifier → ProofBackedCTA`  
**Зрительский вопрос / takeaway:** Возьмите одну знакомую задачу с JSON или инструментами и сравните результат, а не рекламный список возможностей.  
**Telegram asset:** мини-чеклист первого теста V4 Pro


### Текст

1. **HOOK.** Не слово «GA» — главное, что можно проверить уже сегодня.

2. **FACT.** DeepSeek объявил V4 Pro GA 13 August 2026; доступно в приложении/веб через Expert Mode и через API.

3. **FACT.** В документации по ценам DeepSeek указан V4-Pro-0813 с 1M контекста, максимум вывода 384K, JSON-выводом, вызовами инструментов и поддержкой Responses API и Anthropic API.

4. **INSTRUCTION.** Возьмите знакомую задачу с JSON или вызовами инструментов и сравните результаты, а не рекламный список возможностей.

5. **CTA.** Заберите мини-чеклист первого теста V4 Pro в @llm_hubs.


### Источники
- https://api-docs.deepseek.com/news/news260813/
- https://api-docs.deepseek.com/quick_start/pricing
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813


## 04. DeepSeek: когда low разумнее max

**Style:** `violet_luxe`  
**Visual sequence:** `KineticPhrase → TradeoffSliders → PromptABLab → DecisionTree`  
**Зрительский вопрос / takeaway:** Для простого извлечения начинайте с low, а более тяжёлые рассуждения проверяйте отдельно — не платите максимум по умолчанию.  
**Telegram asset:** карточка выбора low/high/max


### Текст

1. **HOOK.** Max не делает каждый ответ умнее — он просто делает их дороже.

2. **FACT.** DeepSeek описывает уровни усилия рассуждения low, high и max для V4 Pro, чтобы выбирать усилие по сложности задачи, а не всегда максимальное.

3. **INSTRUCTION.** Для простого извлечения начинайте с low, а более тяжёлые рассуждения проверяйте отдельно — не платите максимум по умолчанию.

4. **CTA.** Заберите карточка выбора low/high/max в @llm_hubs.


### Источники
- https://api-docs.deepseek.com/news/news260813/
- https://api-docs.deepseek.com/quick_start/pricing
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813


## 05. Цена DeepSeek меняется в 16:00 UTC: почему это важно

**Style:** `midnight_orbit`  
**Visual sequence:** `CalendarLaunchWindow → TokenFlowSankey → TrueCostCalculator → DecisionTree`  
**Зрительский вопрос / takeaway:** В смете отдельно подпишите цену до даты изменения и цену после неё — иначе сравнение будет ложным.  
**Telegram asset:** шаблон сметы до/после смены тарифа


### Текст

1. **HOOK.** Тариф — это не пост в ленте. Это конкретная минута в счёте.

2. **FACT.** DeepSeek: пик/внепик V4 с 16:00 UTC 16 августа 2026; V4 Pro внепик — $0.022 при попадании в кэш, $0.66 при промахе кэша, $1.98 за млн токенов.

3. **FACT.** Объявленные внепиковые цены — это будущие ставки на 14 августа 2026, поэтому в смете отметьте, что они действуют с 16 августа, а не как текущий счёт.

4. **INSTRUCTION.** В смете отдельно подпишите цену до даты изменения и цену после неё — иначе сравнение будет ложным.

5. **CTA.** Заберите шаблон сметы до/после смены тарифа в @llm_hubs.


### Источники
- https://api-docs.deepseek.com/news/news260813/
- https://api-docs.deepseek.com/quick_start/pricing


## 06. Как не перепутать старую цену с новой

**Style:** `kinetic_poster`  
**Visual sequence:** `DocumentMarginNotes → BrowserTour → TelegramChannelPost → BrandOutroMosaic`  
**Зрительский вопрос / takeaway:** Ведите две строки: текущий счёт и объявленный счёт после даты вступления изменений.  
**Telegram asset:** готовая таблица текущих и будущих тарифов


### Текст

1. **HOOK.** Самая дорогая ошибка — считать будущий тариф сегодняшней ценой.

2. **FACT.** Перед 16 августа DeepSeek для V4 Pro: $0.003625 за млн входных токенов (попадание в кэш), $0.435 за млн (промах кэша), $0.87 за млн выходных токенов.

3. **FACT.** Объявленные внепиковые цены — будущие ставки на 14 августа 2026, так что расчёт должен помечать их как вступающие с 16 августа, а не за сегодняшние.

4. **INSTRUCTION.** Ведите две строки: текущий счёт и объявленный счёт после даты вступления изменений.

5. **CTA.** Заберите готовая таблица текущих и будущих тарифов в @llm_hubs.


### Источники
- https://api-docs.deepseek.com/news/news260813/
- https://api-docs.deepseek.com/quick_start/pricing


## 07. Grok 4.6: длинный агент может стать дорогим

**Style:** `liquid_chrome`  
**Visual sequence:** `AgentRunConsole → TokenFlowSankey → TrueCostCalculator → ProofBackedCTA`  
**Зрительский вопрос / takeaway:** Для долгих запусков измеряйте retries и выходные токены: именно они превращают «интересный агент» в счёт.  
**Telegram asset:** калькулятор agent-run с повторами


### Текст

1. **HOOK.** Агент работает дольше — видите цену его повторов?

2. **FACT.** xAI выпустила Grok 4.6 12 August 2026 с упором на долгие агенты, интерактивную работу и визуальные проекты.

3. **FACT.** xAI указывает цену Grok 4.6 API: $2 за миллион входных токенов, $0.50 за миллион кэшированных входных токенов и $6 за миллион выходных токенов.

4. **INSTRUCTION.** Для долгих запусков следите за повторными попытками и выходными токенами: именно они превращают «интересный агент» в счёт.

5. **CTA.** Заберите калькулятор agent-run с повторами в @llm_hubs.


### Источники
- https://x.ai/news/grok-4-6
- https://docs.x.ai/developers/models/grok-4.6
- https://x.ai/pricing


## 08. Grok 4.6: 500K контекста — что проверить первым

**Style:** `aurora_flux`  
**Visual sequence:** `ThreePhoto360Drift → ContextWindowLadder → DeviceShowcase → BrandOutroMosaic`  
**Зрительский вопрос / takeaway:** Проверяйте не размер окна сам по себе, а ваш реальный сценарий: контекст, инструмент и структурированный ответ в одном тесте.  
**Telegram asset:** протокол теста длинного контекста


### Текст

1. **HOOK.** Большой контекст не решает задачу, если агент не вызывает нужные инструменты.

2. **FACT.** В документации xAI указано, что Grok 4.6 имеет окно контекста 500K, вызов функций, структурированные выводы и способности к рассуждению.

3. **INSTRUCTION.** Проверяйте не размер окна сам по себе, а ваш реальный сценарий: контекст, инструмент и структурированный ответ в одном тесте.

4. **CTA.** Заберите протокол теста длинного контекста в @llm_hubs.


### Источники
- https://x.ai/news/grok-4-6
- https://docs.x.ai/developers/models/grok-4.6
- https://x.ai/pricing


## 09. Четыре модели: не выбирайте по самой низкой цене

**Style:** `coral_creator`  
**Visual sequence:** `TelegramChannelPost → BenchmarkHeatmap → TradeoffSliders → CommunityFAQ`  
**Зрительский вопрос / takeaway:** Сначала исключите модели по требованиям задачи, а цену сравнивайте только между теми, что прошли ваш тест.  
**Telegram asset:** матрицу «модель × тип задачи»


### Текст

1. **HOOK.** Самая дешёвая строка в прайсе может проиграть на вашей задаче.

2. **FACT.** 14 августа 2026: Gemini 3.7 Flash — $0.75; DeepSeek V4 Pro — $0.435 при промахе кэша; Grok 4.6 и Claude Sonnet 5 — по $2 за миллион входных токенов.

3. **FACT.** Цена за токены не равна качеству: провайдеры дают разные цены при кэше, контекст, контролы усилия и методологии бенчмарков, поэтому выбор в продакшн требует теста по задаче.

4. **INSTRUCTION.** Сначала исключите модели по требованиям задачи, а цену сравнивайте только между теми, что прошли ваш тест.

5. **CTA.** Заберите матрицу «модель × тип задачи» в @llm_hubs.


### Источники
- https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing
- https://api-docs.deepseek.com/quick_start/pricing
- https://docs.x.ai/developers/models/grok-4.6
- https://www.anthropic.com/news/claude-sonnet-5


## 10. С чего начать тест четырёх LLM за 15 минут

**Style:** `pixel_arcade`  
**Visual sequence:** `ColdOpenContradiction → BenchmarkHeatmap → DecisionTree → BrandOutroMosaic`  
**Зрительский вопрос / takeaway:** Выберите одну задачу, один критерий качества и один лимит стоимости — этого достаточно для первого отсечения.  
**Telegram asset:** 15-минутный протокол первого LLM-теста


### Текст

1. **HOOK.** Не тестируйте десять моделей. Сначала отсейте лишние.

2. **FACT.** По ценам на выход (стандарт/список) от 14.08.2026: Gemini 3.7 Flash $3.75, DeepSeek V4 Pro $0.87, Grok 4.6 $6, Claude Sonnet 5 $10 за млн выходных токенов.

3. **FACT.** Цена токенов в прайс-листе сама по себе не рейтинг: провайдеры разные цены кеша, контекстные условия, контроль усилий и методики бенчмарков — для продакшна нужен тест по задаче.

4. **INSTRUCTION.** Выберите одну задачу, один критерий качества и один лимит стоимости — этого достаточно для первого отсечения.

5. **CTA.** Заберите 15-минутный протокол первого LLM-теста в @llm_hubs.


### Источники
- https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing
- https://api-docs.deepseek.com/quick_start/pricing
- https://docs.x.ai/developers/models/grok-4.6
- https://www.anthropic.com/news/claude-sonnet-5

