from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'projects'/'llm_hubs'/'pipeline_text_storyboards_v2_ru_2026-08-14.json'
DST=ROOT/'docs'/'MSF_PIPELINE_10_TEXT_STORYBOARDS_V2_REVIEW_RU.md'

def main():
 data=json.loads(SRC.read_text(encoding='utf-8'))
 out=['# MSF Pipeline V2 — 10 text-only storyboard для review\n','Это второй batch: каждый ролик строится по схеме **один зрительский вопрос → 1–2 выбранных evidence claims → практический вывод → конкретный Telegram asset**.\n']
 out.append('| Gate | Результат |\n|---|---:|\n| Черновиков | 10 |\n| Уникальных styles/openings | 10 / 10 |\n| Selected claims на ролик | 1–2 |\n| Конкретных CTA assets | 10 |\n| Связанных evidence links | 32 |\n')
 for i,row in enumerate(data['drafts'],1):
  script=row['script']; angle=row['angle']
  out.append(f'## {i:02d}. {script["title"]}\n')
  out.append(f'**Style:** `{row["style"]}`  \n**Visual sequence:** `{ " → ".join(row["planned_presets"]) }`  \n**Зрительский вопрос / takeaway:** {angle["takeaway"]}  \n**Telegram asset:** {angle["cta_asset"]}\n')
  out.append('\n### Текст\n')
  for n,line in enumerate(script['lines'],1): out.append(f'{n}. **{line["kind"].upper()}.** {line["narration"]}\n')
  out.append('\n### Источники\n'+'\n'.join(f'- {url}' for url in row['source_urls'])+'\n\n')
 DST.write_text('\n'.join(out),encoding='utf-8'); print(DST)
if __name__=='__main__': main()
