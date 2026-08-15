"""Localize MSF evidence-backed script plans for a Russian short-video audience.

The stage operates after plan_from_claims(). It preserves the evidence linkage and
requires the model to retain every number, date, model name and caveat; only
viewer-facing narration is rewritten. No web search or new facts are allowed.
"""
from __future__ import annotations

import json
from pathlib import Path
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_2026-08-14.json"
DST = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_ru_2026-08-14.json"
MODEL = "gpt-5-mini"

SCHEMA = {
    "name": "localized_script", "strict": True,
    "schema": {"type": "object", "properties": {
        "title": {"type": "string"},
        "lines": {"type": "array", "items": {"type": "string"}},
    }, "required": ["title", "lines"], "additionalProperties": False},
}


def localize(client: OpenAI, row: dict) -> dict:
    script = row["script"]
    source_lines = [item["narration"] for item in script["lines"]]
    prompt = f"""Ты — редактор русскоязычных TikTok/Shorts роликов об LLM.
Перепиши title и каждую narration line полностью по-русски, естественно и коротко.

ЖЁСТКИЕ ПРАВИЛА:
- Верни ровно {len(source_lines)} lines в исходном порядке.
- Нельзя добавлять факты, числа, даты, сравнения, рекомендации или названия моделей, которых нет в исходной строке.
- Сохрани все числа, даты, валюты, версии моделей, API-названия и caveat. Технические названия допустимы только когда они нужны как имя продукта.
- Hook должен быть цепляющим, но не кликбейтным. CTA обязан сохранить @llm_hubs.
- Убери канцелярит и английские связки: не использовать words вроде 'through', 'versus', 'published model-card table', 'workload' если есть ясный русский эквивалент.
- Не показывай claim IDs или слова evidence зрителю.

Title: {script['title']}
Lines: {json.dumps(source_lines, ensure_ascii=False)}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Output only the requested strict JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_schema", "json_schema": SCHEMA},
    )
    localized = json.loads(response.choices[0].message.content)
    if len(localized["lines"]) != len(script["lines"]):
        raise RuntimeError("localization line-count mismatch")
    output = json.loads(json.dumps(row))
    output["script"]["title"] = localized["title"]
    for item, narration in zip(output["script"]["lines"], localized["lines"]):
        item["narration"] = narration
        item["on_screen_text"] = narration[:150]
    output["localization"] = {"language": "ru", "model": MODEL, "source_facts_preserved": True}
    return output


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    client = OpenAI()
    drafts = [localize(client, row) for row in data["drafts"]]
    DST.write_text(json.dumps({**data, "drafts": drafts, "localization_stage": "evidence_preserving_ru"}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"localized_drafts={len(drafts)} output={DST}")


if __name__ == "__main__":
    main()
