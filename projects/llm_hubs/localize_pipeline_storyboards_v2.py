from __future__ import annotations
import json
from pathlib import Path
from openai import OpenAI

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'projects'/'llm_hubs'/'pipeline_text_storyboards_v2_2026-08-14.json'
DST=ROOT/'projects'/'llm_hubs'/'pipeline_text_storyboards_v2_ru_2026-08-14.json'
SCHEMA={'name':'localized_angle_script','strict':True,'schema':{'type':'object','properties':{'title':{'type':'string'},'lines':{'type':'array','items':{'type':'string'}}},'required':['title','lines'],'additionalProperties':False}}

def main():
 data=json.loads(SRC.read_text(encoding='utf-8')); client=OpenAI(); output=[]
 for row in data['drafts']:
  script=row['script']; source=[x['narration'] for x in script['lines']]
  prompt=f'''Перепиши зрительский текст короткого русского TikTok об LLM. Верни title и ровно {len(source)} lines в исходном порядке.

Правила: только русский разговорный язык; hook — короткий и ясный; сохрани каждое число, дату, цену, версию, бренд и caveat; не добавляй фактов. Переводи общие слова (model card, reasoning effort, cache hit/miss, preview, workload), но не названия моделей, API и benchmark labels. Не пиши claim IDs. CTA должен оставить @llm_hubs и конкретный обещанный asset. Каждая line не длиннее 26 русских слов, если это возможно без потери факта.

Title: {script['title']}
Lines: {json.dumps(source, ensure_ascii=False)}'''
  r=client.chat.completions.create(model='gpt-5-mini',messages=[{'role':'system','content':'Return only strict JSON.'},{'role':'user','content':prompt}],response_format={'type':'json_schema','json_schema':SCHEMA})
  loc=json.loads(r.choices[0].message.content)
  if len(loc['lines'])!=len(script['lines']): raise RuntimeError('line count')
  new=json.loads(json.dumps(row)); new['script']['title']=loc['title']
  for item,text in zip(new['script']['lines'],loc['lines']): item['narration']=text; item['on_screen_text']=text[:150]
  new['localization']={'language':'ru','model':'gpt-5-mini','source_facts_preserved':True}; output.append(new)
 DST.write_text(json.dumps({**data,'drafts':output,'localization_stage':'evidence_preserving_ru_v2'},ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'localized={len(output)} output={DST}')
if __name__=='__main__': main()
