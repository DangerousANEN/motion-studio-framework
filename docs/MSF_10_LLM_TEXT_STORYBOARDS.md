# MSF: 10 текстовых storyboard-сценариев для проверки pipeline

**Статус:** сценарный тест, без рендера.  
**Цель:** проверить актуальность тем, структуру hooks и routing 117-сценного каталога до production pass. Каждый ролик получает **ровно один style family**, уникальный opening preset и другую визуальную логику. Все factual claims перед production должны быть повторно проверены в день публикации.

## Матрица batch-разнообразия

| № | Тема | Style family | Opening | Центральный visual job | Финальный beat |
|---:|---|---|---|---|---|
| 01 | DeepSeek-V4-Pro вышел из preview | `infrared_alert` | `ColdOpenContradiction` | Release + settings | `ProofBackedCTA` |
| 02 | Как работают новые peak/off-peak тарифы DeepSeek | `cobalt_command` | `TrueCostCalculator` | Cost/workload | `DecisionTree` |
| 03 | Reasoning: low, high или max | `porcelain` | `KineticPhrase` | Выбор режима | `TradeoffSliders` |
| 04 | Три новых Gemini для agent workflows | `kinetic_poster` | `HookStack` | Позиционирование моделей | `BenchmarkArena` |
| 05 | Gemini Robotics ER 2: не чат-бот, а embodied reasoning | `liquid_chrome` | `AssetOrbit3D` | 3D product explain | `WorkflowFlyThrough3D` |
| 06 | AlphaEvolve в облаке: как проверять обещания code optimization | `midnight_orbit` | `ClaimEvidenceChain` | Метод/доказательство | `ExperimentProtocol` |
| 07 | Gemini Spark и web errands: где заканчивается удобство | `violet_luxe` | `CounterfactualSplit` | Permission trade-off | `BrowserDecisionTable` |
| 08 | NotebookLM превращается в Gemini Notebook | `aurora_flux` | `ThreePhoto360Drift` | Research workflow | `AppScreenGallery` |
| 09 | Почему sandbox для AI-агента нельзя считать безопасным по умолчанию | `noir` | `EvidenceConflictBoard` | Incident → controls | `LayeredWindowStack` |
| 10 | OWASP LLM Top 10 2026: security — не финальный слайд | `coral_creator` | `TelegramChannelPost` | Community checklist | `BrandOutroMosaic` |

> Ни один opening preset в batch не повторяется. Ролики чередуют narrative, data, media, UI и 3D, а каждый style family используется один раз.

---

## 01. DeepSeek-V4-Pro: это не «ещё один релиз»

**Факт-рамка:** DeepSeek объявил доступность V4-Pro в app/web и API; в анонсе также заявлены регулируемое reasoning effort и поддержка OpenAI Responses API.[1]  
**Style:** `infrared_alert`. **Тон:** срочно, но без кликбейта «убийца всех моделей».

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `ColdOpenContradiction` | «Не спеши менять модель только потому, что вышел V4-Pro. Но и игнорировать релиз — дорого.» |
| 2 | `ReleaseDelta` | «Главное изменение не в слове “Pro”. DeepSeek заявляет: модель вышла из preview и доступна в приложении, вебе и API.» |
| 3 | `ProviderChat` | «В интерфейсе появляется полезный выбор: low — для простого, high — для ежедневных agent-задач, max — для сложных.» |
| 4 | `ChangelogTerminal` | «Ещё один практический пункт: заявлена нативная совместимость с OpenAI Responses API. Это надо проверить на своём SDK, а не верить по заголовку.» |
| 5 | `ClaimEvidenceChain` | «Вывод: сначала сверяем release note, цену и ваш workload. Потом переносим production.» |
| 6 | `ProofBackedCTA` | «В @llm_hubs — шаблон теста: качество, latency, retries и итоговая цена на одной задаче.» |

**Запрещённая формулировка:** «V4-Pro лучше любой модели». Вместо этого: «Проверьте на своей задаче».

---

## 02. DeepSeek меняет тарифы: почему list price всё ещё обманывает

**Факт-рамка:** DeepSeek объявил peak/off-peak rates и указал, что off-peak rates на 50% ниже peak; новая цена вступает в силу в 16:00 UTC 16 августа 2026 года.[1]  
**Style:** `cobalt_command`. **Тон:** аналитический, полезный владельцу продукта.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `TrueCostCalculator` | «Цена за миллион токенов — не ответ. Вопрос: когда именно ваш workload запускается?» |
| 2 | `CalendarLaunchWindow` | «Новая сетка цен начинает действовать в 16:00 UTC 16 августа. Сначала переведи это в свой часовой пояс.» |
| 3 | `CostQualityScatter` | «На графике не ищем “самую дешёвую точку”. Смотрим цену, качество и реальную нагрузку вместе.» |
| 4 | `TokenFlowSankey` | «Разложи стоимость: вход, выход, кэш и повторы. Именно повторы часто съедают экономию.» |
| 5 | `DecisionTree` | «Ночная batch-задача? Сравни off-peak. Пользовательский realtime? Считай peak.» |
| 6 | `BrandOutroMosaic` | «Нужен калькулятор workload, а не очередная таблица цен? Сохрани разбор в @llm_hubs.» |

**Production note:** перед рендером получить актуальную pricing page и приложить URL/дату к сценам 1–4.

---

## 03. Reasoning effort: почему max не делает каждый ответ умнее

**Факт-рамка:** DeepSeek описывает `low`, `high` и `max` как разные уровни reasoning effort для простых, ежедневных agent и сложных задач соответственно.[1]  
**Style:** `porcelain`. **Тон:** спокойный объяснительный.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `KineticPhrase` | «MAX — не настройка “сделай хорошо”. Это настройка “потрать больше”.» |
| 2 | `ProblemSolution` | «Ошибка: включать максимальное reasoning на каждую задачу. Решение: привязать effort к цене ошибки.» |
| 3 | `TradeoffSliders` | «Три шкалы: latency, стоимость, вероятность сложной ошибки. Нельзя максимизировать все одновременно.» |
| 4 | `PromptABLab` | «Один и тот же запрос: routine extraction против многошагового исследования. Нужны разные режимы.» |
| 5 | `ExperimentProtocol` | «Сделай A/B: одинаковые данные, одинаковый prompt, заранее выбранная метрика.» |
| 6 | `ProofBackedCTA` | «Скачай наш шаблон теста reasoning: не “какой режим круче”, а “какой окупается”.» |

---

## 04. Три Gemini-модели — это не три повода выбрать случайную

**Факт-рамка:** Google сообщил о Gemini 3.6 Flash, 3.5 Flash-Lite и 3.5 Flash Cyber, позиционируя их вокруг token efficiency, latency и production agent workflows.[2]  
**Style:** `kinetic_poster`. **Тон:** быстрый, сравнительный.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `HookStack` | «ТРИ НОВЫЕ GEMINI — И НИ ОДНА НЕ НАЗЫВАЕТСЯ “ЛУЧШАЯ ДЛЯ ВСЕГО”.» |
| 2 | `BenchmarkArena` | «Сравнивать нужно не названия. Сравниваем роль: скорость, бюджет, специализация.» |
| 3 | `CapabilityRadar` | «Ваши оси: latency, цена, код, security, качество на собственных тестах.» |
| 4 | `AgentRunConsole` | «Для agent workflow важна не только модель: retries, tool calls, timeout и наблюдаемость.» |
| 5 | `CounterfactualSplit` | «Выбор по хайпу → случайный счёт. Выбор по workload → понятный кандидат на тест.» |
| 6 | `TelegramChannelPost` | «В канале — таблица для своих тестов. Не копируйте чужой ranking без задачи.» |

---

## 05. Gemini Robotics ER 2: полезнее думать не о роботе, а о контуре задачи

**Факт-рамка:** Google описывает Gemini Robotics ER 2 как модель для embodied reasoning: взаимодействия с людьми, понимания окружения и многошаговых задач.[2]  
**Style:** `liquid_chrome`. **Тон:** product reveal + объяснение.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `AssetOrbit3D` | «Это не просто “нейросеть для робота”. Главный вопрос: где модель принимает решение, а где нужен контроль?» |
| 2 | `FeatureSpotlight` | «Embodied reasoning: система получает контекст среды, общается и проходит многошаговую задачу.» |
| 3 | `WorkflowFlyThrough3D` | «Цепочка: восприятие → план → действие → проверка результата. Ошибка в любой точке ломает демо.» |
| 4 | `DecisionGrid` | «Для пилота выберите узкую повторяемую задачу, а не “пусть робот делает всё”.» |
| 5 | `MythFact` | «Миф: большая модель заменяет safety process. Факт: физическое действие повышает цену ошибки.» |
| 6 | `ProofBackedCTA` | «Хотите разбор без фантазий? В @llm_hubs — checklist для agent-пилота.» |

---

## 06. AlphaEvolve: как не перепутать оптимизацию кода с магией

**Факт-рамка:** Google сообщил о general availability AlphaEvolve на Gemini Enterprise Agent Platform и описал подход: базовый алгоритм + цели → поиск улучшений и human-readable optimized code.[2]  
**Style:** `midnight_orbit`. **Тон:** evidence-first, инженерный.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `ClaimEvidenceChain` | «“AI оптимизирует код” — это claim. Доказательство начинается с baseline и измеримой цели.» |
| 2 | `CodeReveal` | «Покажи маленький baseline: вход, ограничение, метрика. Без этого оптимизация — просто другой код.» |
| 3 | `ExperimentProtocol` | «Тест: одинаковые inputs, контроль корректности, time/memory/cost, зафиксированная среда.» |
| 4 | `BenchmarkHeatmap` | «Таблица не должна быть красивой. Она должна показать, где решение быстрее, где хуже и где нет разницы.» |
| 5 | `EvidenceConflictBoard` | «Если synthetic benchmark победил, а production нет — публикуем оба результата.» |
| 6 | `BrandOutroMosaic` | «В @llm_hubs — карточка “как проверить AI-оптимизацию до merge”.» |

---

## 07. Gemini Spark: агент с доступом — это сначала permission design

**Факт-рамка:** Google сообщил, что Gemini Spark расширил доступ и может с разрешения пользователя работать с logged-in accounts и saved passwords для некоторых web errands, например research/начала бронирования.[2]  
**Style:** `violet_luxe`. **Тон:** полезный и осторожный.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `CounterfactualSplit` | «Агент может сэкономить час. Или получить доступ шире, чем вы думали.» |
| 2 | `BrowserDecisionTable` | «Перед запуском задача проходит через три колонки: что агент читает, что меняет, что нельзя делать.» |
| 3 | `ScreenGuide` | «Показываем безопасный tutorial: проверка account scope, permissions и ручного confirmation.» |
| 4 | `TradeoffSliders` | «Удобство растёт — поверхность риска тоже. Не делайте это бинарным “да/нет”.» |
| 5 | `CommunityFAQ` | «Три вопроса: нужен ли доступ сейчас? Можно ли ограничить аккаунт? Где человек подтверждает действие?» |
| 6 | `ProofBackedCTA` | «Сохраните permission checklist. Агента проще ограничить до первого запуска, чем после инцидента.» |

---

## 08. NotebookLM → Gemini Notebook: как из источников сделать рабочее исследование

**Факт-рамка:** Google сообщил, что Gemini Notebook является тем же standalone-продуктом, что и NotebookLM, теперь связанным с Gemini app и Search и обновлённым secure cloud computer.[2]  
**Style:** `aurora_flux`. **Тон:** visual editorial + workflow.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `ThreePhoto360Drift` | «Исследование ломается не потому, что мало вкладок. Оно ломается, когда никто не помнит источник вывода.» |
| 2 | `SourceStack` | «Стек: primary release, docs, pricing, независимый тест — и дата у каждого.» |
| 3 | `DocumentMarginNotes` | «На документе оставляем не красивый highlight, а note: “что доказывает эта строка”.» |
| 4 | `MemoryTimeline` | «Тогда: ссылки в хаосе. Сейчас: evidence ID. Дальше: сценарий, который можно проверить.» |
| 5 | `AppScreenGallery` | «Покажи связку research workspace → note → storyboard, без подмены реального UI.» |
| 6 | `TelegramChannelPost` | «В @llm_hubs — шаблон evidence pack для новостей и сравнений.» |

---

## 09. AI cyber-evals: почему тестовый sandbox обязан иметь настоящую защиту

**Факт-рамка:** Anthropic описал три инцидента, где модели в сторонних evaluation environments получили доступ к реальным системам из-за доступного internet path; компания выделила containment, monitoring и scope control как уроки.[3]  
**Style:** `noir`. **Тон:** серьёзный, без инструкций по атаке.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `EvidenceConflictBoard` | «“Это же sandbox” — не гарантия. Вопрос: проверили ли вы все пути наружу?» |
| 2 | `LayeredWindowStack` | «Слои контроля: isolated environment, сеть, credentials, logging, human escalation.» |
| 3 | `IncidentTimeline` | «Хронология без sensationalism: misconfiguration → неожиданный доступ → review → remediation.» |
| 4 | `DecisionTree` | «Если агент видит живую систему или неясный scope — стоп, а не “попробуй ещё раз”.» |
| 5 | `ExperimentProtocol` | «Перед eval: network deny-by-default, проверка egress, журналы, kill switch, независимый review.» |
| 6 | `ProofBackedCTA` | «В канале — безопасный checklist для agent evaluation. Не публикуем attack steps.» |

---

## 10. OWASP LLM Top 10 2026: security — часть storyboard, а не последняя плашка

**Факт-рамка:** OWASP выпустил Top 10 for LLM Applications 2026, описывая обновлённые rankings, расширенное threat coverage и actionable mitigations, связанные с отраслевыми framework.[4]  
**Style:** `coral_creator`. **Тон:** community checklist, не страх.

| Beat | Сцена | Текст / задача narration |
|---:|---|---|
| 1 | `TelegramChannelPost` | «Если ваш AI-агент уже читает документы и вызывает tools — security нельзя добавлять “потом”.» |
| 2 | `PollResult` | «Быстрый вопрос комьюнити: где ваш самый слабый контур — prompt, tool, data или permissions?» |
| 3 | `ProblemSolution` | «Проблема: считать модель единственной точкой риска. Решение: смотреть на целое приложение.» |
| 4 | `AgentRunConsole` | «Trace должен показывать действие, источник, tool и статус. Но не скрытые рассуждения и не secrets.» |
| 5 | `CommunityFAQ` | «Минимум на старт: allowlist tools, least privilege, проверка данных, audit log, human approval.» |
| 6 | `BrandOutroMosaic` | «Сохрани security checklist и отправь тому, кто сегодня подключает AI к production.» |

## Рекомендованные pipeline-настройки после теста

| Сигнал | Изменение policy |
|---|---|
| Два ролика звучат как один и тот же news recap | Повысить штраф за повтор category order и hook family. |
| Ролики о моделях скатываются в рейтинг без контекста | Обязать `ClaimEvidenceChain`, `ExperimentProtocol` либо `TrueCostCalculator` после любой benchmark scene. |
| Telegram CTA выглядит рекламой без пользы | Разрешать Telegram/CTA только после data/evidence beat. |
| Новый факт не помещается в короткий ролик | Разделить на news fact, practical implication и test guide вместо ускорения текста. |
| Style начинает дрейфовать внутри ролика | Поставить `one_style_per_video` в storyboard validator как hard gate. |

## References

[1]: https://api-docs.deepseek.com/news/news260813/ "DeepSeek-V4-Pro GA Release"
[2]: https://blog.google/innovation-and-ai/technology/ai/google-ai-updates-july-2026/ "Google: The latest AI news we announced in July 2026"
[3]: https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals "Anthropic: Investigating three real-world incidents in our cybersecurity evaluations"
[4]: https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/ "OWASP GenAI LLM Top 10 2026"
