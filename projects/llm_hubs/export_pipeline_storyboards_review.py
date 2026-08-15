from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_ru_2026-08-14.json"
DST = ROOT / "docs" / "MSF_PIPELINE_10_TEXT_STORYBOARDS_REVIEW_RU.md"

data = json.loads(SRC.read_text(encoding="utf-8"))
lines = [
    "# MSF Pipeline — 10 текстовых storyboard для review\n",
    "Эти черновики получены встроенным pipeline `ResearchPack → validate_research_pack → plan_from_claims → validate_script_plan → evidence-preserving_ru → language_hygiene → diversity_gate`. Зрительская narration полностью локализована на русский; factual lines сохраняют исходные claim ID и source URLs. Рендера в этом pass нет.\n",
    "| Показатель | Результат |\n|---|---:|\n| Черновиков | 10 |\n| Уникальных style families | 10 |\n| Уникальных opening presets | 10 |\n| Factual lines с evidence claim | 30 |\n| Live scene catalog при QA | 117 |\n",
]
for n, row in enumerate(data["drafts"], 1):
    script = row["script"]
    lines.append(f"## {n:02d}. {script['title']}\n")
    lines.append(f"**Research topic:** {row['research_topic']}  \n**Style:** `{row['style']}`  \n**Visual sequence:** `{' → '.join(row['planned_presets'])}`\n")
    lines.append("\n### Текст\n")
    for i, item in enumerate(script["lines"], 1):
        label = item["kind"].upper()
        refs = ", ".join(item.get("evidence_claim_ids") or [])
        suffix = f" — evidence: `{refs}`" if refs else ""
        lines.append(f"{i}. **{label}.** {item['narration']}{suffix}\n")
    lines.append("\n### Источники\n")
    for url in row["source_urls"]:
        lines.append(f"- {url}\n")
    lines.append("\n")
DST.write_text("\n".join(lines), encoding="utf-8")
print(DST)
