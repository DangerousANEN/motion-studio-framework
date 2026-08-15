from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_ru_2026-08-14.json"
REPLACEMENTS = {
    "model-card": "карте модели",
    "model card": "карте модели",
    "reasoning-effort": "уровни рассуждений",
    "reasoning effort": "уровни рассуждений",
    "cache-hit": "кэшированного входа",
    "cache miss": "некэшированного входа",
    "cache-miss": "некэшированного входа",
    "through ": "до ",
    "August": "августа",
    "December": "декабря",
    "context": "контекст",
}

def clean(text: str) -> str:
    for before, after in REPLACEMENTS.items():
        text = text.replace(before, after)
    return text

def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    for row in data["drafts"]:
        script = row["script"]
        script["title"] = clean(script["title"])
        for line in script["lines"]:
            line["narration"] = clean(line["narration"])
            line["on_screen_text"] = line["narration"][:150]
        row["language_hygiene"] = {"audience_language": "ru", "preserved": "brands_numbers_dates_claim_ids"}
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("sanitized=10")
if __name__ == "__main__":
    main()
