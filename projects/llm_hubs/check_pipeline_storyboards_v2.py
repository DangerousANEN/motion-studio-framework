from __future__ import annotations
import json
from pathlib import Path
from msf.studio.contracts import ResearchPack, ScriptPlan
from msf.studio.research import validate_research_pack
from msf.studio.script_planner import validate_script_plan, words
from msf.studio.catalog import all_scenes

ROOT=Path(__file__).resolve().parents[2]
PACKS=ROOT/'projects'/'llm_hubs'/'evidence_packs_2026-08-14.json'
BATCH=ROOT/'projects'/'llm_hubs'/'pipeline_text_storyboards_v2_ru_2026-08-14.json'
GENERIC='больше практичных разборов'

def main():
 packs={x['research_id']:ResearchPack.model_validate(x) for x in json.loads(PACKS.read_text(encoding='utf-8'))['packs']}
 data=json.loads(BATCH.read_text(encoding='utf-8')); rows=data['drafts']; assert len(rows)==10
 live={x.name for x in all_scenes()}; styles=[]; openings=[]; cited=0
 for row in rows:
  pack=packs[row['research_id']]; validate_research_pack(pack)
  plan=ScriptPlan.model_validate(row['script']); validate_script_plan(plan,pack)
  selected=set(row['angle']['selected_claim_ids']); assert 1<=len(selected)<=2
  factual=[x for x in plan.lines if x.kind in {'fact','interpretation','instruction'}]
  assert len(factual)<=3, row['batch_id']
  for line in factual:
   assert set(line.evidence_claim_ids)<=selected, (row['batch_id'],line.evidence_claim_ids,selected)
   assert words(line.narration)<=34, (row['batch_id'],words(line.narration))
   cited+=len(line.evidence_claim_ids)
  cta=next(x for x in plan.lines if x.kind=='cta')
  assert '@llm_hubs' in cta.narration and GENERIC not in cta.narration
  assert row['angle']['cta_asset'].lower() in cta.narration.lower(), (row['batch_id'], cta.narration)
  assert set(row['planned_presets'])<=live
  assert len(row['planned_presets'])==len(set(row['planned_presets']))
  styles.append(row['style']); openings.append(row['planned_presets'][0])
 assert len(set(styles))==10 and len(set(openings))==10
 print(f'drafts=10 styles=10 openings=10 selected_claims<=2 cited_links={cited} cta_assets=10')
if __name__=='__main__': main()
