"""Demo props for previewing any preset, effect, transition or style.

WHY THIS FILE EXISTS
--------------------
A preview is only useful if it shows the preset doing its job. Handing every
preset the same `{title, text}` produced the exact confusion this project already
paid for once: presets that render their own placeholder content looked like they
"worked", and presets needing structured data looked broken.

So each preset gets sample data shaped like what the pipeline would really pass —
Russian, realistically long, and with the item counts a generated video actually
uses. Anything shorter hides overflow bugs; anything in English hides the Cyrillic
metric problems that caused most of the layout fixes in this repo.

WHERE THE FIELD NAMES COME FROM
-------------------------------
`remotion/src/VideoSpec.schema.ts`, not memory. A wrong key does not warn — Zod
rejects the scene and the renderer replaces the WHOLE video with a red error card.
`tests/test_preview_props.py` validates every entry here through validate_spec for
that reason.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Realistic Russian narration: long enough to wrap, short enough to read.
SAMPLE_TITLE = "НЕЙРОСЕТИ 2026"
SAMPLE_TEXT = "Открытые модели догнали закрытые по длине контекста и по цене."
SAMPLE_SUB = "Что изменилось за год"

# Real model names, because they are the longest strings the pipeline handles and
# they broke three presets before (Leaderboard, DefinitionCard, CryptoWallet).
MODELS = ["Kimi-K3-Thinking", "DeepSeek-V4-Terminus", "Qwen3.6-235B-A22B", "GLM-5.2-Air"]

# Generated demo media, relative to remotion/public/ because presets pass any
# non-http path through staticFile(). Built by msf/panel/make_preview_assets.py.
from msf.panel.make_preview_assets import CLIP as PREVIEW_CLIP  # noqa: E402
from msf.panel.make_preview_assets import STILL_1 as PREVIEW_STILL_1  # noqa: E402
from msf.panel.make_preview_assets import STILL_2 as PREVIEW_STILL_2  # noqa: E402


def _rows(n: int = 3) -> List[Dict[str, Any]]:
    """Leaderboard rows. `name` + numeric `value` are the schema's own fields;
    sending `score` as well relies on .passthrough() and is read by nothing."""
    scores = [94, 88, 85, 79]
    return [{"name": MODELS[i], "value": scores[i]} for i in range(n)]


# Per-preset sample props. Presets absent from this map get TEXT_ONLY.
TEXT_ONLY: Dict[str, Any] = {"title": SAMPLE_TITLE, "text": SAMPLE_TEXT}

DEMO_PROPS: Dict[str, Dict[str, Any]] = {
    # ---------------------------------------------------------------- typography
    "HeroKinetic": {"title": SAMPLE_TITLE, "subtitle": SAMPLE_SUB},
    "TypewriterSub": {"title": SAMPLE_TITLE, "text": SAMPLE_TEXT},
    "QuoteCard": {
        "text": "Локальная модель на ноутбуке — это уже не демо, а рабочий инструмент.",
        "author": "Андрей Карпатый",
    },
    "CodeReveal": {
        "title": "Запуск локально",
        "code": "from llama_cpp import Llama\n\nllm = Llama(\n    model_path='qwen3.gguf',\n    n_ctx=32768,\n)\nprint(llm('Привет')['choices'][0]['text'])",
        "language": "python",
    },
    "DefinitionCard": {
        "term": "Квантование",
        "definition": "Сжатие весов модели с 16 до 4 бит: память падает вчетверо, "
                      "качество почти не меняется.",
    },
    # --------------------------------------------------------------------- data
    # statValue/statLabel, NOT value/label — verified against VideoSpec.schema.ts.
    # _DATA_REQUIREMENTS asks for exactly these, and `value` would render the
    # preset's zero default while passing every check.
    "StatCounter": {
        "title": "Контекст",
        "statValue": 262144,
        "statLabel": "токенов у открытых моделей",
        "suffix": " токенов",
    },
    "Leaderboard": {"title": "ТОП МОДЕЛЕЙ", "rows": _rows(3)},
    # `segments`, not `bars`. SegmentSchema requires BOTH label and value (neither
    # is .optional()), so a missing one red-cards the whole render.
    "Bars3D": {"title": "Цена за миллион токенов", "segments": [
        {"label": "GPT-5", "value": 12.5},
        {"label": "Kimi K3", "value": 2.4},
        {"label": "Qwen3.6", "value": 0.9},
    ]},
    "DonutFill": {"title": "Доля открытых моделей", "segments": [
        {"label": "Открытые", "value": 63},
        {"label": "Закрытые", "value": 37},
    ]},
    "RingStats": {"title": "Бенчмарки", "segments": [
        {"label": "MMLU", "value": 88},
        {"label": "GPQA", "value": 71},
        {"label": "SWE", "value": 64},
    ]},
    # `cards`, not left/right — those belong to VersusSplit. CardSchema requires
    # `title`; description/value/tag are optional.
    "CompareSplit": {"title": "Открытые против закрытых", "cards": [
        {"title": "Открытые", "value": "0.9 ₽", "description": "за миллион токенов"},
        {"title": "Закрытые", "value": "12.5 ₽", "description": "за миллион токенов"},
    ]},
    # left/right use `name` + numeric `value`; a string value fails the schema.
    "VersusSplit": {
        "title": "Kimi против DeepSeek",
        "left": {"name": "Kimi-K3", "value": 94},
        "right": {"name": "DeepSeek-V4", "value": 88},
        "vsLabel": "против",
    },
    # events use date/label/description. `time`/`text` pass Zod (.passthrough())
    # and render BLANK rows — validate_spec warns about exactly this.
    "TimelineReveal": {"title": "Год открытых моделей", "events": [
        {"date": "Март", "label": "Контекст 256K", "description": "Вырос в восемь раз"},
        {"date": "Июль", "label": "Цена ×10 ниже", "description": "Инференс подешевел"},
        {"date": "Ноябрь", "label": "Локальный запуск", "description": "4 бита на ноутбуке"},
    ]},
    "ProgressPath": {"title": "Как это работает", "steps": [
        {"label": "Скачать GGUF"},
        {"label": "Запустить llama.cpp"},
        {"label": "Подключить к редактору"},
    ]},
    # Studio v2 universal data-driven scenes. The prop shapes are deliberately
    # identical to VideoSpec.schema.ts and the studio registry fields.
    "LlmHubsCTA": {"title": "Больше практики с LLM", "text": "Подписывайтесь на @llm_hubs: разборы инструментов, промптов и экономии."},
    "DecisionGrid": {"title": "Выберите подходящий режим", "cards": [
        {"tag": "ЛОКАЛЬНО", "title": "Ollama", "description": "Для приватных экспериментов на своём устройстве"},
        {"tag": "БЫСТРО", "title": "Free tier", "description": "Для малого теста с проверкой лимитов"},
        {"tag": "ФОНОМ", "title": "Batch", "description": "Для не срочных массовых задач"},
    ]},
    "StepList": {"title": "Три шага к готовому ролику", "steps": [
        {"label": "Собрать факты", "description": "Зафиксировать источники и ключевые тезисы"},
        {"label": "Собрать storyboard", "description": "Выбрать подходящие проверенные сцены"},
        {"label": "Проверить превью", "description": "Исправить текст, звук и тайминг до рендера"},
    ]},
    "BeforeAfter": {
        "title": "От ручного процесса к студии",
        "before": {"label": "До", "title": "Ручная сборка", "text": "Сценарий, звук и рендер в разных инструментах"},
        "after": {"label": "После", "title": "Единый pipeline", "text": "Проверяемый storyboard, пресеты и диагностический trace"},
    },
    "MetricTrend": {
        "title": "Скорость подготовки ролика", "metricLabel": "Минуты на один черновик", "valueSuffix": " мин",
        "points": [
            {"label": "Базовый процесс", "value": 90},
            {"label": "С пресетами", "value": 45},
            {"label": "С Studio", "value": 18},
        ],
    },
    "FlowDiagram": {"title": "Пайплайн", "nodes": [
        {"label": "Сценарий"}, {"label": "Озвучка"}, {"label": "Рендер"},
    ]},
    # -------------------------------------------------------------- v2.3 expansion
    "HookStack": {"headline": "НЕ ВЫБИРАЙТЕ МОДЕЛЬ ПО ОДНОЙ ЦЕНЕ", "subhead": "Сначала проверьте задачу, кэш и effective output cost.", "proof": "ПЕРВОИСТОЧНИКИ СВЕРЕНЫ", "urgency": "НОВЫЙ РАЗБОР"},
    "KineticPhrase": {"phrase": "ДЕШЕВЛЕ ≠ ЛУЧШЕ", "highlight": "СМОТРИТЕ НА WORKLOAD", "caption": "Две цифры не заменяют реальный тест на вашей задаче."},
    "ProblemSolution": {"title": "КАК НЕ ОШИБИТЬСЯ", "problem": "Сравнивать list price", "solution": "Считать весь workload"},
    "FeatureSpotlight": {"feature": "КОНТРОЛЬ REASONING", "benefit": "Выбирайте глубину размышления только там, где она окупается.", "index": "02"},
    "CaseStudyBoard": {"label": "CASE STUDY", "context": "Нужно разобрать 200 писем", "action": "Проверили три режима на одном наборе", "result": "Выбрали быстрый режим для рутины"},
    "MythFact": {"title": "ПРОВЕРЬТЕ ТЕЗИС", "myth": "Больше параметров всегда лучше", "fact": "Качество зависит от задачи, данных и режима"},
    "QuoteEvidence": {"quote": "Сначала зафиксируйте источник, дату и точную формулировку claim.", "source": "Research policy · primary-source evidence pack", "role": "EVIDENCE FIRST"},
    "StatsBand": {"title": "ЧТО ПРОВЕРЯЕМ", "stats": [{"value": "3", "label": "первоисточника"}, {"value": "1", "label": "workload"}, {"value": "0", "label": "выдуманных claim"}], "footnote": "Все цифры требуют даты и URL источника."},
    "SourceStack": {"title": "ПЕРВОИСТОЧНИКИ", "status": "VERIFIED SOURCES", "sources": [{"title": "Официальный релиз", "url": "release note"}, {"title": "API документация", "url": "model limits"}, {"title": "Pricing page", "url": "effective date"}]},
    "CountdownRing": {"label": "ДО ИЗМЕНЕНИЯ ТАРИФА", "value": "16 AUG", "caption": "Проверьте дату перехода до расчёта бюджета.", "progress": 0.72},
    "PromptComposer": {"provider": "LLM WORKSPACE", "prompt": "Собери только доказуемые тезисы по официальным источникам.", "sendLabel": "Запустить"},
    "ProviderChat": {"provider": "DeepSeek V4 Pro", "avatarText": "DS", "prompt": "Как выбрать reasoning effort?", "answer": "Начните с low для рутины. High и max включайте после реального теста задачи.", "chips": ["LOW", "HIGH", "MAX"]},
    "NotificationStack": {"title": "НОВЫЕ СИГНАЛЫ", "notifications": [{"app": "RELEASE", "text": "Доступна новая версия модели"}, {"app": "EVIDENCE", "text": "Pricing page обновлена"}, {"app": "WORKFLOW", "text": "Storyboard готов к preview"}]},
    "CommentThread": {"title": "ОБСУЖДЕНИЕ", "platformLabel": "COMMUNITY THREAD", "comments": [{"author": "Аня", "text": "Проверила на своём кейсе — вывод сходится."}, {"author": "Илья", "text": "А где смотреть актуальный тариф?"}, {"author": "LLM Hubs", "text": "В release note и pricing page."}]},
    "PollResult": {"title": "КАК ВЫ ВЫБИРАЕТЕ МОДЕЛЬ?", "question": "Главный критерий", "options": [{"label": "Тест на workload", "value": 68}, {"label": "Только list price", "value": 32}]},
    "BrowserTour": {"title": "ПРОВЕРЬТЕ УСЛОВИЯ", "url": "provider.example/pricing", "screenshotUrl": PREVIEW_STILL_1, "steps": [{"label": "Откройте pricing page"}, {"label": "Проверьте дату"}, {"label": "Сохраните evidence"}]},
    "ScreenMagnifier": {"title": "СМОТРИТЕ НА ЭТОТ БЛОК", "mediaUrl": PREVIEW_STILL_1, "focus": "PRICING", "caption": "Увеличьте только relevant area, а не весь экран.", "zoom": 1.25},
    "DeviceShowcase": {"title": "РЕАЛЬНЫЙ ИНТЕРФЕЙС", "device": "phone", "mediaUrl": PREVIEW_STILL_2, "caption": "Вставьте собственный screenshot или запись экрана."},
    "VoiceWave": {"speaker": "LLM HUBS", "caption": "Короткое голосовое: сначала источник, потом вывод.", "waveformSeed": 27},
    "VideoFrame": {"title": "КАК ПРОВЕРЯТЬ CLAIM", "channel": "LLM Hubs", "chapter": "ГЛАВНЫЙ МОМЕНТ", "mediaUrl": PREVIEW_CLIP},
    "QuizCard": {
        "question": "Сколько токенов контекста у открытых моделей в 2026?",
        "options": ["8 тысяч", "32 тысячи", "256 тысяч", "1 миллион"],
        "correctIndex": 2,
    },
    # ------------------------------------------------------------------ ui-mock
    "TgChat": {"title": "Переписка", "messages": [
        {"from": "them", "text": "Ты пробовал Kimi K3 локально?"},
        {"from": "me", "text": "Да, 4 бита влезают в 24 гига"},
        {"from": "them", "text": "И как по скорости?"},
    ]},
    "AiChatStream": {
        "title": "Диалог с моделью",
        "messages": [{"from": "me", "text": "Объясни квантование в двух словах"}],
        "response": "Веса модели хранятся с меньшей точностью: памяти нужно вчетверо меньше, "
                    "а ответы почти не портятся.",
    },
    "CommentWall": {"title": "Комментарии", "comments": [
        {"author": "Никита", "text": "Наконец-то без подписки"},
        {"author": "Марина", "text": "На ноутбуке правда работает?"},
        {"author": "Олег", "text": "Проверил — работает"},
    ]},
    "PostCard": {
        "author": "llm_hubs",
        "text": "Открытые модели догнали закрытые по контексту. Разбор в канале.",
        "likes": 12400, "comments": 342, "reposts": 89,
    },
    "SubscribeCTA": {"channel": "llm_hubs", "subscribers": 12400},
    "CryptoWallet": {"title": "Кошелёк", "balance": 128450.32, "tokens": [
        {"symbol": "ETH", "amount": 12.4, "change": 3.2},
        {"symbol": "USDT", "amount": 45000, "change": 0.0},
        {"symbol": "SOL", "amount": 320.5, "change": -1.8},
    ]},
    # `last4`, not `number`: the schema deliberately has no full-PAN field, so a
    # mockup cannot carry a real card number. `balance` is z.number().
    "BankCard": {"holder": "NIKITA LIPSKY", "last4": "4242", "balance": 128450.0,
                 "brand": "VISA", "expiry": "09/29"},
    "ScoreHud": {
        "title": "РАУНД 3", "score": 9750, "combo": 3,
        "timeLeft": 45, "health": 80, "playerName": "ИГРОК 1",
    },
    # `from` is the count-down start and `finalWord` what replaces it at zero.
    "CountdownHero": {"from": 5, "finalWord": "СТАРТ"},
    # ------------------------------------------------------------------- device
    # PhoneMockup renders ANOTHER preset inside the phone screen; `innerPreset` is
    # what makes it show anything at all.
    "PhoneMockup": {
        "title": "Приложение",
        "innerPreset": "TgChat",
        "appName": "MosaicVPN",
        "messages": [
            {"from": "them", "text": "VPN поднялся?"},
            {"text": "Да, узел в Хельсинки", "out": True, "read": True},
        ],
    },
    # ScreenRecord takes a video `src` OR a still via images[0]; the address bar
    # field is `urlBar`, not `url`.
    "ScreenRecord": {
        "title": "Демонстрация",
        "images": [PREVIEW_STILL_1],
        "urlBar": "llm-hubs.ru/models",
        "chrome": "browser",
        "showRec": True,
    },
    "ScreenGuide": {
        "title": "Где включить экономный режим",
        "guideText": "Наведите курсор на нужный пункт: camera делает controlled zoom вместо хаотичной тряски.",
        "images": [PREVIEW_STILL_1],
        "urlBar": "console.example.ai/settings",
        "chrome": "browser",
        "focusX": 0.68, "focusY": 0.56, "focusScale": 1.28,
        "cursorSteps": [
            {"x": 0.51, "y": 0.42, "at": 0.18, "label": "Откройте Settings"},
            {"x": 0.68, "y": 0.56, "at": 0.55, "label": "Выберите Batch"},
        ],
    },
    "SwipePanels": {"title": "Три шага", "cards": [
        {"title": "Скачать", "description": "Один файл GGUF"},
        {"title": "Запустить", "description": "Одна команда"},
        {"title": "Работать", "description": "Без интернета"},
    ]},
    # -------------------------------------------------------------------- media
    # These reference generated demo assets (msf/panel/make_preview_assets.py).
    # Without a real file the preset renders MISSING ASSET and validate_spec
    # refuses the spec, so the panel could not preview them at all.
    # `images` is z.array(z.string()) — objects with captions fail the schema.
    "ImageShowcase": {
        "title": "Кадры",
        "images": [PREVIEW_STILL_1, PREVIEW_STILL_2],
        "fit": "cover",
        "kenBurns": True,
    },
    "VideoEmbed": {"title": "Разбор", "src": PREVIEW_CLIP, "muted": True},
    "YouTubeCard": {"title": "Как экономить на API без магии", "subtitle": "Вставьте свой клип или poster-кадр", "src": PREVIEW_CLIP, "channelName": "LLM Hubs", "handle": "@llm_hubs", "muted": True},
    "TelegramVoiceRound": {"title": "Короткое голосовое", "contactName": "LLM Hubs", "avatar": PREVIEW_STILL_2, "duration": 19, "waveformSeed": 27, "transcript": "Проверь цены и кэш на своём workload, а потом выбирай модель."},
    "ImageSpotlight": {"title": "Реальный продукт — главный герой", "subtitle": "Вставьте screenshot, фото или обложку: frame, crop и caption адаптируются под выбранный style.", "images": [PREVIEW_STILL_2], "fit": "cover", "kenBurns": True},
    "MusicPlayer": {"title": "Подкаст", "track": "Открытые модели", "artist": "llm_hubs"},
    "VinylRecord": {"title": "Выпуск 12", "track": "Год открытых моделей"},
    # `duration` is z.number() (seconds) — the string "0:42" fails the schema.
    "VoiceMemo": {"title": "Голосовое", "duration": 42, "text": SAMPLE_TEXT},
    "LyricLines": {"title": "Строки", "lines": [
        {"text": "Модель уместилась в ноутбук"},
        {"text": "И больше не спрашивает ключ"},
    ]},
    # --------------------------------------------------------------------- 3D
    "TokenCloud3D": {"title": "Векторы", "tokens": ["контекст", "токен", "внимание", "вес"]},
    "LayerStack3D": {"title": "Слои трансформера", "layers": [
        {"label": "Внимание"}, {"label": "MLP"}, {"label": "Норма"},
    ]},
    "ModelOrbit3D": {"title": "Архитектура"},
    "GridGridFloor": {"title": SAMPLE_TITLE, "subtitle": SAMPLE_SUB},
    # -------------------------------------------------------------- v2.4 scene 50
    "BenchmarkArena": {"title": "КТО ВЫИГРЫВАЕТ НА КОДЕ", "benchmark": "SWE-bench", "models": [{"name": "DeepSeek-V4-Terminus", "score": 91}, {"name": "Kimi-K3-Thinking", "score": 88}, {"name": "Qwen3.6-235B-A22B", "score": 85}], "source": "Один тест · одна дата"},
    "BenchmarkHeatmap": {"title": "КАРТА ВОЗМОЖНОСТЕЙ", "columns": ["Код", "Reasoning", "Vision"], "rows": [{"label": "Kimi-K3", "values": [91, 87, 79]}, {"label": "DeepSeek-V4", "values": [88, 92, 82]}, {"label": "Qwen3.6", "values": [84, 80, 90]}]},
    "LeaderboardRace": {"title": "РЕЙТИНГ ИЗМЕНИЛСЯ", "metric": "Качество на коде", "rankBefore": [{"name": "Kimi-K3", "score": 88}, {"name": "DeepSeek-V4", "score": 87}], "rankAfter": [{"name": "DeepSeek-V4", "score": 91}, {"name": "Kimi-K3", "score": 89}]},
    "CostQualityScatter": {"title": "ЦЕНА ПРОТИВ КАЧЕСТВА", "xLabel": "Цена", "yLabel": "Качество", "scatterPoints": [{"label": "Эконом", "x": 2, "y": 74}, {"label": "Баланс", "x": 5, "y": 87}, {"label": "Топ", "x": 12, "y": 93}]},
    "CapabilityRadar": {"title": "ПРОФИЛЬ МОДЕЛЕЙ", "axes": ["Reasoning", "Код", "Vision", "Скорость", "Контекст"], "series": [{"label": "DeepSeek", "values": [92, 91, 80, 78, 89]}, {"label": "Kimi", "values": [88, 87, 82, 89, 92]}]},
    "ContextWindowLadder": {"title": "КОНТЕКСТ — ЭТО ПРАКТИКА", "items": [{"model": "Базовый", "value": 32, "caption": "короткий документ"}, {"model": "Рабочий", "value": 128, "caption": "папка файлов"}, {"model": "Длинный", "value": 256, "caption": "большой анализ"}]},
    "TrueCostCalculator": {"title": "СКОЛЬКО СТОИТ WORKLOAD", "lineItems": [{"label": "Входные токены", "value": 2.1}, {"label": "Выходные токены", "value": 3.4}, {"label": "Кэш", "value": 0.8}, {"label": "Повторы", "value": 0.5}], "total": 6.8, "currency": "USD"},
    "TokenFlowSankey": {"title": "КУДА УХОДЯТ ТОКЕНЫ", "flowNodes": [{"label": "Вход", "value": 100}, {"label": "Кэш", "value": 45}, {"label": "Выход", "value": 28}], "links": [{"from": "Вход", "to": "Кэш", "value": 45}]},
    "ClaimEvidenceChain": {"claim": "Модель стала выгоднее для этого workload", "evidence": [{"label": "Релиз", "text": "Официальная дата"}, {"label": "Тариф", "text": "Цена входа и выхода"}, {"label": "Тест", "text": "Одинаковый набор задач"}], "caveat": "Проверьте регион и режим кэша."},
    "EvidenceConflictBoard": {"claim": "Два источника дают разные цифры", "sourceA": {"title": "Релиз", "detail": "Новая цена с 1 августа"}, "sourceB": {"title": "Тариф", "detail": "Старая дата на странице"}, "difference": "Сверьте effective date."},
    "ExperimentProtocol": {"title": "КАК ПОВТОРИТЬ ТЕСТ", "steps": [{"label": "Dataset", "detail": "Одинаковые задачи"}, {"label": "Prompt", "detail": "Одинаковые условия"}, {"label": "Метрика", "detail": "Качество, цена, latency"}], "threshold": "Порог: 90% качества"},
    "ReleaseDelta": {"title": "ЧТО ИЗМЕНИЛОСЬ", "previous": "v4.0", "current": "v4.1", "deltas": [{"kind": "ДОБАВЛЕНО", "text": "Новый режим reasoning"}, {"kind": "ИЗМЕНЕНО", "text": "Обновлён тариф"}, {"kind": "ПРОВЕРИТЬ", "text": "Дата вступления"}]},
    "TelegramChannelPost": {"channel": "LLM Hubs", "handle": "@llm_hubs", "avatar": PREVIEW_STILL_2, "postText": "Новый разбор: как честно сравнить модели по цене, кэшу и качеству на своей задаче.", "mediaUrl": PREVIEW_STILL_1, "reactions": [{"emoji": "🔥", "count": 124}, {"emoji": "🧠", "count": 68}], "views": 12400, "time": "сегодня", "cta": "Полный разбор в канале"},
    "TelegramFeedScroll": {"channel": "LLM Hubs", "posts": [{"id": "1", "tag": "RELEASE", "text": "Новый релиз и что он меняет"}, {"id": "2", "tag": "GUIDE", "text": "Как проверить pricing page"}, {"id": "3", "tag": "TEST", "text": "Сравнение на одном workload"}], "focusPostId": "2"},
    "TelegramForwardChain": {"title": "КАК ИДЁТ ИНФОРМАЦИЯ", "origin": {"channel": "LLM Hubs", "text": "Исходный разбор с источниками."}, "forwards": [{"channel": "AI Новости", "note": "переслал факт"}, {"channel": "Команда", "note": "обсуждает вывод"}]},
    "ReactionPulse": {"title": "РЕАКЦИЯ АУДИТОРИИ", "reactions": [{"emoji": "🔥", "count": 124}, {"emoji": "👍", "count": 88}, {"emoji": "🧠", "count": 52}], "views": 12400, "comments": 37},
    "QuoteRepost": {"title": "РЕПОСТ С РАЗБОРОМ", "original": {"author": "Источник", "text": "Модель стала дешевле."}, "commentary": "Проверьте дату, scope и условия тарифа до вывода.", "author": "LLM Hubs"},
    "CommunityFAQ": {"title": "ВОПРОСЫ ПОДПИСЧИКОВ", "questions": ["Где смотреть цену?", "Нужен ли reasoning?", "Как проверить claim?"], "answers": ["На официальной pricing page.", "Только после теста на задаче.", "Сверить источник, дату и метод."]},
    "ChangelogTerminal": {"product": "MSF Studio", "version": "v2.4", "date": "2026-08-14", "changes": [{"kind": "added", "text": "50 универсальных сцен"}, {"kind": "changed", "text": "Safe layout guards"}]},
    "PromptABLab": {"title": "A/B ПРОМПТ", "promptA": "Объясни модель.", "promptB": "Объясни модель, укажи источник и ограничение.", "resultA": "Общий ответ", "resultB": "Проверяемый ответ"},
    "AgentRunConsole": {"title": "PIPELINE АГЕНТА", "steps": [{"label": "Research", "status": "done"}, {"label": "Проверка", "status": "done"}, {"label": "Storyboard", "status": "running"}, {"label": "Render", "status": "queued"}]},
    "BrowserDecisionTable": {"title": "ТАБЛИЦА ВЫБОРА", "url": "provider.example/compare", "columns": ["Модель", "Цена", "Качество"], "rows": [{"Модель": "A", "Цена": "низкая", "Качество": "88"}, {"Модель": "B", "Цена": "средняя", "Качество": "92"}], "selectedCell": {"row": 2, "column": 3}, "caption": "Выделяем решение, а не весь экран."},
    "ThreePhoto360Drift": {"title": "ТРИ КАДРА — ОДНА ИСТОРИЯ", "images": [PREVIEW_STILL_1, PREVIEW_STILL_2, PREVIEW_STILL_1], "positions": [{"x": -0.28, "y": -0.12, "z": -120, "rotate": -12}, {"x": 0.22, "y": 0.03, "z": 0, "rotate": 8}, {"x": -0.06, "y": 0.18, "z": -80, "rotate": -6}], "captions": ["Факт", "Тест", "Вывод"]},
    "PhotoConstellation": {"title": "СОЗВЕЗДИЕ КАДРОВ", "images": [PREVIEW_STILL_1, PREVIEW_STILL_2, PREVIEW_STILL_1, PREVIEW_STILL_2], "focusOrder": [0, 2, 1]},
    "DeepZoomStory": {"title": "СМОТРИМ НА ДЕТАЛЬ", "image": PREVIEW_STILL_1, "stops": [{"x": 0.5, "y": 0.5, "scale": 1, "label": "ОБЩИЙ ВИД"}, {"x": 0.7, "y": 0.42, "scale": 1.6, "label": "ВАЖНАЯ ДЕТАЛЬ"}]},
    "BeforeAfterLens": {"title": "ДО И ПОСЛЕ", "beforeUrl": PREVIEW_STILL_1, "afterUrl": PREVIEW_STILL_2, "labelBefore": "ДО", "labelAfter": "ПОСЛЕ", "claim": "Интерфейс стал понятнее"},
    "VideoChapterRail": {"title": "КАК ПРОВЕРЯТЬ CLAIM", "videoUrl": PREVIEW_CLIP, "channel": "LLM Hubs", "chapters": [{"label": "Факт", "at": "0:00"}, {"label": "Тест", "at": "0:18"}, {"label": "Вывод", "at": "0:42"}]},
    "VoiceNotePullQuote": {"speaker": "LLM HUBS", "quote": "Сначала источник, потом вывод.", "waveformSeed": 27},
    "DocumentMarginNotes": {"title": "ЗАМЕТКИ НА ПОЛЯХ", "documentUrl": PREVIEW_STILL_1, "source": "Официальный документ", "notes": [{"x": 0.70, "y": 0.30, "text": "Дата"}, {"x": 0.62, "y": 0.58, "text": "Метод"}]},
    "AppScreenGallery": {"title": "ГАЛЕРЕЯ ЭКРАНОВ", "screens": [PREVIEW_STILL_1, PREVIEW_STILL_2, PREVIEW_STILL_1], "device": "phone"},
    "LayeredWindowStack": {"title": "СТЕК ОКОН", "windows": [{"label": "BROWSER", "url": PREVIEW_STILL_1}, {"label": "CHAT", "url": PREVIEW_STILL_2}, {"label": "TABLE", "url": PREVIEW_STILL_1}]},
    "ImageEvidenceCompare": {"title": "СРАВНЕНИЕ СКРИНШОТОВ", "leftImage": PREVIEW_STILL_1, "rightImage": PREVIEW_STILL_2, "leftMeta": "Источник A · вчера", "rightMeta": "Источник B · сегодня", "difference": "Проверьте дату и scope."},
    "AssetOrbit3D": {"title": "ОБЛЁТ 3D-МОДЕЛИ", "assetLicense": "procedural fallback", "cameraPreset": "orbit", "fallbackShape": "orb"},
    "ExplodedProductView": {"title": "СЛОИ ОБЪЕКТА", "parts": [{"label": "Интерфейс"}, {"label": "Логика"}, {"label": "Данные"}], "fallbackShape": "chip"},
    "WorkflowFlyThrough3D": {"title": "3D PIPELINE", "workflowNodes": [{"label": "Research"}, {"label": "Benchmark"}, {"label": "Review"}, {"label": "Render"}], "fallbackShape": "nodes"},
    "DataCube": {"title": "КУБ ДАННЫХ", "x": 24, "y": 91, "z": 68, "labels": ["Цена", "Качество", "Скорость"], "highlight": 1},
    "LogoSculpture3D": {"title": "ОБЪЁМНЫЙ ЗНАК", "tagline": "LLM HUBS", "fallbackShape": "ring"},
    "DeviceConveyor3D": {"title": "УСТРОЙСТВА", "devices": ["PHONE", "DESKTOP", "TABLET"], "screens": [PREVIEW_STILL_1, PREVIEW_STILL_2]},
    "ParticleDataField": {"title": "ПОЛЕ ЧАСТИЦ", "groups": [{"label": "Сигналы", "value": 72}, {"label": "Шум", "value": 18}, {"label": "Фокус", "value": 10}]},
    "IsometricWorkflowCity": {"title": "ГОРОД WORKFLOW", "zones": [{"label": "Inbox"}, {"label": "Model"}, {"label": "Review"}, {"label": "Output"}]},
    "GlobeSignalMap": {"title": "КАРТА СИГНАЛОВ", "locations": [{"label": "EU"}, {"label": "US"}, {"label": "APAC"}], "source": "Переданные точки"},
    "MilestoneCorridor3D": {"title": "КОРИДОР ВЕХ", "milestones": [{"date": "Март", "label": "Контекст"}, {"date": "Июль", "label": "Тариф"}, {"date": "Сейчас", "label": "Тест"}]},
    "ColdOpenContradiction": {"claimA": "МОДЕЛЬ ДЕШЕВЛЕ", "claimB": "МОДЕЛЬ ЛУЧШЕ", "realQuestion": "КАКАЯ МЕТРИКА НУЖНА ВАШЕЙ ЗАДАЧЕ?"},
    "CounterfactualSplit": {"title": "ДВЕ РАЗВИЛКИ", "choiceA": "Только list price", "choiceB": "Тест на workload", "outcomesA": ["Риск промаха", "Скрытые траты"], "outcomesB": ["Реальная стоимость", "Проверяемое решение"]},
    "MemoryTimeline": {"title": "КАК МЫ ДОШЛИ ДО ВЫВОДА", "past": "Сравнивали по одной цифре", "present": "Сверяем источники", "next": "Тестируем на workload"},
    "DecisionTree": {"title": "ДЕРЕВО РЕШЕНИЯ", "decisionNodes": [{"id": "privacy", "label": "Нужна приватность?", "branch": "Да → локально"}, {"id": "speed", "label": "Нужна скорость?", "branch": "Да → API"}], "chosenPath": ["privacy"]},
    "TradeoffSliders": {"title": "КОМПРОМИССЫ", "dimensions": [{"label": "Цена", "value": 28, "left": "дешевле", "right": "качественнее"}, {"label": "Latency", "value": 64, "left": "быстрее", "right": "точнее"}]},
    "CalendarLaunchWindow": {"title": "ОКНО ЗАПУСКА", "date": "16 AUG", "window": "ОБНОВЛЕНИЕ", "whatChanges": "Проверьте условия до расчёта бюджета."},
    "ProofBackedCTA": {"action": "ОТКРОЙТЕ ПОЛНЫЙ РАЗБОР", "proof": "Ссылки, дата и метод проверки.", "benefit": "Проверьте вывод на своей задаче.", "channel": "@llm_hubs"},
    "BrandOutroMosaic": {"brandName": "LLM HUBS", "handle": "@llm_hubs", "cta": "Разборы, тесты и практические workflow.", "media": [{"label": "ПРОДУКТ"}, {"label": "ДОКАЗАТЕЛЬСТВА"}, {"label": "КОМЬЮНИТИ"}]},
}


def props_for(preset: str) -> Dict[str, Any]:
    """Sample props for one preset. Falls back to title+text."""
    return dict(DEMO_PROPS.get(preset, TEXT_ONLY))


# Reading speed, mirrored from msf.spec.READ_CHARS_PER_SEC / pacing.ts. Imported
# rather than redeclared so the panel cannot disagree with the validator.
def _read_speed() -> float:
    from msf.spec import READ_CHARS_PER_SEC

    return READ_CHARS_PER_SEC


def suggested_duration(scene: Dict[str, Any], fps: int = 60) -> int:
    """Frames this scene needs for its text to be readable.

    WHY THE PREVIEW DOES NOT JUST USE 180 FRAMES
    --------------------------------------------
    It did, and validate_spec warned on seven presets that 3 seconds is not enough
    to read their demo text — correctly. In a real video the duration comes from
    the narration audio, so a fixed preview length was inventing a defect that the
    pipeline does not have, and burying real warnings under it.

    Counts the same visible fields validate_spec counts, so the two agree.
    """
    # Expansion scenes carry their copy in semantic fields rather than the older
    # generic title/text pair. Count them here; otherwise a rich proof or tutorial
    # card receives the three-second floor and previewing it manufactures a pacing
    # defect the production pipeline would avoid.
    text_fields = (
        "text", "definition", "code", "question", "response", "subtitle",
        "headline", "subhead", "proof", "urgency", "phrase", "highlight",
        "caption", "problem", "solution", "feature", "benefit", "context",
        "action", "result", "myth", "fact", "quote", "source", "role",
        "footnote", "value", "label", "provider", "prompt", "answer",
        "speaker", "channel", "chapter", "url", "status", "title", "focus",
        "duration", "sendLabel", "platformLabel", "avatarText",
    )
    chars = sum(len(str(scene[f])) for f in text_fields if isinstance(scene.get(f), str))
    for key in ("rows", "segments", "cards", "events", "comments", "steps",
                "messages", "tokens", "lines", "options", "nodes", "stats",
                "sources", "notifications", "chips"):
        val = scene.get(key)
        if isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    chars += len(item)
                elif isinstance(item, dict):
                    chars += sum(
                        len(str(v)) for v in item.values() if isinstance(v, str)
                    )
    need_sec = chars / _read_speed()
    # Floor of 3s so a bare title card still gets a normal-looking preview; cap at
    # 12s because past that the preview costs more than it teaches.
    return int(max(3.0, min(12.0, need_sec + 1.0)) * fps)


def scene_for(
    preset: str,
    duration_in_frames: Optional[int] = None,
    overrides: Dict[str, Any] | None = None,
    fps: int = 60,
) -> Dict[str, Any]:
    """One scene dict ready to drop into a VideoSpec's `scenes[]`.

    `duration_in_frames=None` sizes the scene to its own content — see
    suggested_duration().
    """
    scene: Dict[str, Any] = {"id": f"preview_{preset}", "preset": preset}
    scene.update(props_for(preset))
    if overrides:
        # Drop None values so a UI control left empty means "use the demo value"
        # rather than "send null" — null fails Zod on required string fields.
        scene.update({k: v for k, v in overrides.items() if v is not None})
    scene["durationInFrames"] = (
        duration_in_frames
        if duration_in_frames is not None
        else suggested_duration(scene, fps)
    )
    return scene


__all__ = ["DEMO_PROPS", "TEXT_ONLY", "MODELS", "props_for", "scene_for",
           "suggested_duration", "SAMPLE_TITLE", "SAMPLE_TEXT", "SAMPLE_SUB",
           "PREVIEW_STILL_1", "PREVIEW_STILL_2", "PREVIEW_CLIP"]
