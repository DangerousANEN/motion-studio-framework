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
    "FlowDiagram": {"title": "Пайплайн", "nodes": [
        {"label": "Сценарий"}, {"label": "Озвучка"}, {"label": "Рендер"},
    ]},
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
    text_fields = ("text", "definition", "code", "question", "response", "subtitle")
    chars = sum(len(str(scene[f])) for f in text_fields if isinstance(scene.get(f), str))
    for key in ("rows", "segments", "cards", "events", "comments", "steps",
                "messages", "tokens", "lines", "options", "nodes"):
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
