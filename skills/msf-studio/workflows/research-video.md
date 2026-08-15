# Research video workflow

Используй этот workflow, когда агент получает только тему ролика и должен подготовить доказательный русскоязычный storyboard. Не собирай факты «по памяти» и не обходи Studio evidence gates.

1. Вызови `research_topic_to_storyboard` с `topic`, аудиторией, `cta_handle`, конкретным `cta_asset` и одной существующей `style_family`. Для релизов включай `release_topic=true`.
2. Native workflow сам строит до четырёх поисковых вопросов, извлекает публичные страницы, исключает небезопасные URL и останавливается, если нет минимум двух пригодных источников.
3. Для тем известных LLM-провайдеров workflow требует официальный источник. Для цен, доступности и лимитов не заменяй первичную документацию обзорной статьёй или зеркалом.
4. Получи `ResearchPack`, `ScriptPlan` и `StoryboardDraft` одним результатом. Каждая factual и practical сцена должна сохранить `evidence_claim_ids` из возвращённого `ScriptPlan`.
5. Проверь, что сценарий остаётся на русском, без неразъяснённого provider jargon. Структура должна быть: hook → смысл → доказательство → практический вывод → конкретный Telegram asset.
6. Не меняй `default_style_kit` и не смешивай families внутри этого storyboard. Native workflow уже выбирает уникальные preset scenes из live catalog; не подменяй их догадками.
7. Для описания модели с visual proof запроси `comparison_mode=observed` и передай две/три модели через `comparison_models`. Observed proof обязан содержать одну задачу, одинаковые условия, критерий, linked claims и source/result asset URL. Если этого нет, workflow должен вернуть `proposed`/`inconclusive`; не называй победителя.
8. Подбирай scene по виду сравнения: `PromptABLab`/`BenchmarkArena` для одной задачи, `BeforeAfterLens`/`AppScreenGallery` для интерфейса или игры, `EvidenceConflictBoard` для спорного результата. Не показывай одну карточку текста вместо результатов двух моделей.
9. Перед сохранением вызови `validate_storyboard` с исходным `ResearchPack`. Затем сохрани draft. Render запускай только отдельным явным approval действием.

Если native workflow сообщает об отсутствии первичного источника, недостатке доказательств или недопустимом сценарии, не продолжай к render. Уточни тему, подожди официальную публикацию или запроси у оператора ссылку на источник. Если comparison proof имеет `proposed` mode, показывай только метод теста, а не победу модели.
