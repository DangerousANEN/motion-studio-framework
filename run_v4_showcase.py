"""MSF v4 showcase: every preset, ICL voice cloning, 60 FPS, Vision QA.

Hand-authored storyboard so structured presets (StatCounter, CompareSplit,
FlowDiagram, CodeReveal, QuoteCard, 3D) get real data instead of narration
scraps. Run:  python run_v4_showcase.py
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from msf.graph.video_graph import build_msf_graph

OUT = ROOT / "output" / "v4_showcase.mp4"

STORYBOARD = [
    {
        "preset": "HeroKinetic",
        "text": "Моушн Студио Фреймворк версия четыре. Локальный рендер вертикальных роликов.",
        "title": "MOTION STUDIO",
        "subtitle": "локальный рендер · 60 FPS",
    },
    {
        "preset": "TokenCloud3D",
        "text": "Три D сцены рендерятся честной геометрией через Three JS, а не картинками.",
        "title": "3D СЦЕНЫ",
        "subtitle": "Three.js × Remotion",
        "point_count": 900,
        "orbit_speed": 0.6,
    },
    {
        "preset": "StatCounter",
        "text": "Шестьдесят кадров в секунду на каждом пресете, без исключений.",
        "stat_value": 60,
        "stat_suffix": " FPS",
        "stat_label": "ЧАСТОТА КАДРОВ",
    },
    {
        "preset": "LayerStack3D",
        "text": "Слои модели показываются объёмным стеком с подписями.",
        "title": "АРХИТЕКТУРА",
        "layers": ["Embedding", "Attention", "Feed Forward", "Norm", "Output"],
    },
    {
        "preset": "CompareSplit",
        "text": "Сравнение двух подходов идёт разделённым экраном.",
        "title": "БЫЛО / СТАЛО",
        "cards": [
            {"title": "БЫЛО", "text": "x-vector: только тембр, чтение плоское"},
            {"title": "СТАЛО", "text": "ICL: переносится интонация носителя"},
        ],
    },
    {
        "preset": "FlowDiagram",
        "text": "Пайплайн собран как граф: текст, синтез, спека, рендер, контроль качества.",
        "title": "ПАЙПЛАЙН",
        "steps": [
            {"label": "Текст"},
            {"label": "Синтез речи"},
            {"label": "Спека"},
            {"label": "Рендер"},
            {"label": "Контроль"},
        ],
    },
    {
        "preset": "CodeReveal",
        "text": "Запуск занимает пять строк на Питоне.",
        "title": "ЗАПУСК",
        "language": "python",
        "code": 'app = build_msf_graph()\nresult = app.invoke({\n    "text": "...",\n    "voice": "syenduk",\n})',
    },
    {
        "preset": "SwipePanels",
        "text": "Ключевые возможности листаются карточками.",
        "title": "ВОЗМОЖНОСТИ",
        "cards": [
            {"title": "11 пресетов", "text": "2D кинетика и 3D сцены"},
            {"title": "Клон голоса", "text": "Qwen3 TTS, перенос интонации"},
            {"title": "Контроль", "text": "покадровая проверка результата"},
        ],
    },
    {
        "preset": "QuoteCard",
        "text": "Проверка результата встроена в граф, а не остаётся на человеке.",
        "author": "MSF",
        "role": "принцип пайплайна",
    },
    {
        "preset": "GridGridFloor",
        "text": "Фирменный стиль Поп Лаборатория держится на всех сценах.",
        "title": "POP LABORATORY",
        "subtitle": "единая палитра",
    },
    {
        "preset": "TypewriterSub",
        "text": "Полный цикл проходит на одной машине, без облака и без ручной сборки.",
    },
]


def main() -> int:
    t0 = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    presets = [s["preset"] for s in STORYBOARD]
    print(f"[showcase] scenes={len(STORYBOARD)} presets={len(set(presets))}")
    print(f"[showcase] {', '.join(presets)}")

    app = build_msf_graph()
    result = app.invoke(
        {
            "text": "",
            "storyboard": STORYBOARD,
            "preset": "HeroKinetic",
            "accent": "gold",
            "voice": "syenduk",
            "agent_level": 5,
            "output_path": str(OUT),
        },
        {"recursion_limit": 60},
    )

    elapsed = time.time() - t0
    print(f"\n[showcase] elapsed={elapsed:.1f}s")
    print(f"[showcase] final_mp4={result.get('final_mp4')}")
    print(f"[showcase] retry_count={result.get('retry_count')}")
    qa = result.get("qa_report") or {}
    print("[showcase] qa=" + json.dumps(qa, ensure_ascii=False)[:600])

    final = result.get("final_mp4")
    if not final or not Path(final).exists():
        print("[showcase] FAIL: no output file")
        return 1
    if not qa.get("all_passed", False):
        print("[showcase] FAIL: QA did not pass")
        return 1
    print("[showcase] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
