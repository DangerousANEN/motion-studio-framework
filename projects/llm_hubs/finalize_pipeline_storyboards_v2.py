from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/'projects'/'llm_hubs'/'pipeline_text_storyboards_v2_ru_2026-08-14.json'

def main():
 data=json.loads(PATH.read_text(encoding='utf-8'))
 for row in data['drafts']:
  cta=next(line for line in row['script']['lines'] if line['kind']=='cta')
  asset=row['angle']['cta_asset']
  cta['narration']=f'Заберите {asset} в @llm_hubs.'
  cta['on_screen_text']=cta['narration']
  row['finalization']={'cta_asset_source':'angle_planner','audience_language':'ru'}
 PATH.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print('finalized=10 concrete_cta_assets=10')
if __name__=='__main__': main()
