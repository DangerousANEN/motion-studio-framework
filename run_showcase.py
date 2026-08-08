"""MSF v3 showcase: exercise every preset in one render via a hand-authored storyboard.

Unlike run_full_proof.py (which feeds plain narration and lets the graph auto-split
and auto-rotate text-safe presets), this drives the full spec surface: StatCounter's
animated numbers, SwipePanels' cards, and opt-in badges. All numbers quoted here are
real values measured from previous verified pipeline runs.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from msf.graph.video_graph import build_msf_graph  # noqa: E402

OUT = REPO / "output" / "showcase.mp4"

STORYBOARD = [
    {
        "id": "s1-hook",
        "preset": "HeroKinetic",
        "title": "МОУШН-ВИДЕО ЛОКАЛЬНО",
        "subtitle": "без облака и подписок",
        "text": "Моушн-видео целиком локально. Без облака и без подписок.",
    },
    {
        "id": "s2-fps",
        "preset": "StatCounter",
        "stat_value": 60,
        "stat_suffix": " FPS",
        "stat_label": "рендер 1080 на 1920",
        "badge": "REMOTION",
        "accent_color": "#00FF88",
        "text": "Рендер идёт в шестьдесят кадров в секунду, вертикальный формат.",
    },
    {
        "id": "s3-stack",
        "preset": "SwipePanels",
        "title": "ЧТО ВНУТРИ",
        "cards": [
            {"title": "LangGraph", "description": "граф с QA и самопочинкой", "tag": "ГРАФ", "color": "#00D4FF"},
            {"title": "Remotion", "description": "React-анимация и пружины", "tag": "РЕНДЕР", "color": "#E6C475"},
            {"title": "Qwen3-TTS", "description": "клон голоса за один проход", "tag": "ГОЛОС", "color": "#00FF88"},
        ],
        "text": "Внутри граф оркестрации, реакт-рендер и клонирование голоса.",
    },
    {
        "id": "s4-voice",
        "preset": "GridGridFloor",
        "title": "ГОЛОС КЛОНИРУЕТСЯ",
        "subtitle": "один референсный файл",
        "text": "Голос клонируется с одного референсного файла, без обучения.",
    },
    {
        "id": "s5-qa",
        "preset": "StatCounter",
        "stat_value": 6,
        "stat_prefix": "",
        "stat_suffix": "",
        "stat_label": "проверки качества до выдачи",
        "badge": "FAIL-CLOSED",
        "accent_color": "#00D4FF",
        "text": "Шесть автоматических проверок качества проходят до выдачи результата.",
    },
    {
        "id": "s6-cta",
        "preset": "TypewriterSub",
        "text": "Подписывайся на канал ЛЛМ Хабс.",
    },
]

NARRATION = " ".join(s["text"] for s in STORYBOARD)


def probe(path: Path) -> dict:
    fields = "stream=codec_name,width,height,r_frame_rate,sample_rate,channels"
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", fields,
         "-show_entries", "format=duration,size",
         "-of", "default=noprint_wrappers=1", str(path)],
        capture_output=True, text=True, errors="replace",
    )
    return {"rc": r.returncode, "out": r.stdout.strip()}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    app = build_msf_graph()

    result = app.invoke(
        {
            "text": NARRATION,
            "storyboard": STORYBOARD,
            "preset": "HeroKinetic",
            "accent": "gold",
            "agent_level": 4,
            "reference_audio": "C:/Users/ANEN/qwen3_1.7B_clone_test.wav",
            "output_path": str(OUT),
        },
        {"recursion_limit": 50},
    )

    print("=== SHOWCASE RESULT ===")
    print("final_mp4 :", result.get("final_mp4"))
    print("qa_passed :", result.get("qa_passed"))
    print("retry_cnt :", result.get("retry_count"))

    spec = result.get("spec_dict") or {}
    scenes = spec.get("scenes", [])
    print(f"scenes    : {len(scenes)}")
    presets = []
    for i, sc in enumerate(scenes):
        presets.append(sc.get("preset"))
        extras = []
        if sc.get("statValue") is not None:
            extras.append(f"stat={sc.get('statPrefix','')}{sc['statValue']}{sc.get('statSuffix','')}")
        if sc.get("cards"):
            extras.append(f"cards={len(sc['cards'])}")
        if sc.get("badge"):
            extras.append(f"badge={sc['badge']}")
        txt = (sc.get("text") or sc.get("title") or "")[:44]
        print(f"  [{i}] {sc.get('preset'):<14} {sc['durationInFrames']:>4}f "
              f"{' '.join(extras):<34} {txt!r}")
    print("distinct presets used :", len(set(presets)), sorted(set(presets)))

    print("--- QA REPORT ---")
    print(json.dumps(result.get("qa_report"), indent=1, ensure_ascii=False))

    final = Path(result["final_mp4"])
    print("--- FFPROBE ---")
    print(probe(final)["out"])

    print("=== DONE_MARKER ===")
    return 0 if result.get("qa_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
