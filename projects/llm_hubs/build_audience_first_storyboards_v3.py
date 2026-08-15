from __future__ import annotations
import json, re
from pathlib import Path
from openai import OpenAI
from msf.studio.contracts import ResearchPack, ScriptLine, ScriptPlan
from msf.studio.research import validate_research_pack
from msf.studio.script_planner import validate_script_plan

ROOT=Path(__file__).resolve().parents[2]
PACKS=ROOT/'projects'/'llm_hubs'/'evidence_packs_2026-08-14.json'
SRC=ROOT/'projects'/'llm_hubs'/'pipeline_text_storyboards_v2_ru_2026-08-14.json'
DST=ROOT/'projects'/'llm_hubs'/'pipeline_text_storyboards_v3_ru_2026-08-14.json'
SCHEMA={'name':'audience_first_storyboard','strict':True,'schema':{'type':'object','properties':{'title':{'type':'string'},'hook':{'type':'string'},'explainer':{'type':'string'},'facts':{'type':'array','items':{'type':'string'}},'takeaway':{'type':'string'}},'required':['title','hook','explainer','facts','takeaway'],'additionalProperties':False}}
# Names and formal labels may remain only if their user-facing consequence is explained.
BANNED_RE=re.compile(r'(?i)\b(GA|general availability|preview|model[ -]?card|reasoning|workload|agent[ -]?run|cache-aware|cache hit|cache miss|coding-задач|pipeline|retr(?:y|ies))\b')
CTA_FORMS={
 'таблица двух тестов и шаблон своей проверки':'таблицу двух тестов и шаблон своей проверки',
 'карточка выбора low/high/max':'карточку выбора low/high/max',
 'готовая таблица текущих и будущих тарифов':'готовую таблицу текущих и будущих тарифов',
 'матрицу «модель × тип задачи»':'матрицу «модель × тип задачи»',
}

def line(kind:str,narration:str,claim_ids:list[str],intent:str)->dict:
 return ScriptLine(kind=kind,narration=narration,on_screen_text=narration[:150],evidence_claim_ids=claim_ids,scene_intent=intent).model_dump(mode='json')
def cta_for(asset:str)->str: return f'Заберите {CTA_FORMS.get(asset,asset)} в @llm_hubs.'
def bad_terms(text:str)->list[str]: return sorted(set(m.group(0) for m in BANNED_RE.finditer(text)))

def create(client:OpenAI,row:dict,selected:list[str],facts:list[dict],attempt:int)->dict:
 retry_note='' if attempt==0 else '\nПредыдущая версия использовала запрещённые технические слова. Исправь их через простое объяснение смысла.'
 prompt=f'''Ты — главный редактор русскоязычного TikTok-канала об ИИ для умных, но не технических зрителей. Создай короткий и доступный evidence-backed сценарий ТОЛЬКО по данным ниже.

Зрительский вопрос: {row['script']['title']}
Доказательства: {json.dumps(facts,ensure_ascii=False)}
Практический вывод: {row['angle']['takeaway']}

Верни JSON. `facts` содержит ровно {len(facts)} элементов в исходном порядке.

Структура удержания: hook (конфликт/выгода) → explainer («что это меняет лично для зрителя») → evidence → takeaway («что сделать») → в отдельной системе добавится CTA.

Правила: hook до 13 слов; explainer и takeaway до 22 слов; каждая fact line до 28 слов. Не добавляй фактов, чисел, дат, цен или обещаний. Сохрани из источника все числа, цены, версии, даты, бренды и ограничения.

Никогда не пиши: GA, Preview, General Availability, model card, reasoning, workload, agent run, cache-aware, cache hit/miss, pipeline, retry. Не объясняй термин его переводом. Показывай смысл для человека: например, вместо GA — «провайдер открыл обычный доступ к модели»; вместо reasoning — «режим, где модель тратит больше шагов на обдумывание»; вместо model card — «таблица провайдера с результатами тестов». Названия моделей, API, JSON и benchmark labels допустимы только если фраза сразу говорит, зачем они зрителю.{retry_note}'''
 r=client.chat.completions.create(model='gpt-5-mini',messages=[{'role':'system','content':'Return only strict JSON.'},{'role':'user','content':prompt}],response_format={'type':'json_schema','json_schema':SCHEMA},max_completion_tokens=1800)
 return json.loads(r.choices[0].message.content)

def main():
 packs={x['research_id']:ResearchPack.model_validate(x) for x in json.loads(PACKS.read_text(encoding='utf-8'))['packs']}
 source=json.loads(SRC.read_text(encoding='utf-8')); client=OpenAI(); output=[]
 for row in source['drafts']:
  pack=packs[row['research_id']]; validate_research_pack(pack); selected=row['angle']['selected_claim_ids']; lookup={c.claim_id:c.statement for c in pack.claims}; facts=[{'claim_id':c,'statement':lookup[c]} for c in selected]
  val=None
  for attempt in range(3):
   candidate=create(client,row,selected,facts,attempt); spoken=' '.join([candidate['title'],candidate['hook'],candidate['explainer'],*candidate['facts'],candidate['takeaway']])
   if len(candidate['facts'])==len(selected) and not bad_terms(spoken): val=candidate; break
  if val is None: raise RuntimeError(f'jargon gate failed after retries: {row["batch_id"]}')
  lines=[line('hook',val['hook'],[],'hook'),line('interpretation',val['explainer'],selected,'explainer')]
  lines += [line('fact',text,[claim_id],'evidence') for text,claim_id in zip(val['facts'],selected)]
  lines += [line('instruction',val['takeaway'],selected,'takeaway'),line('cta',cta_for(row['angle']['cta_asset']),[],'cta')]
  plan=ScriptPlan.model_validate({'research_id':pack.research_id,'title':val['title'],'language':'ru','lines':lines,'cta_handle':'@llm_hubs'})
  validate_script_plan(plan,pack)
  new=json.loads(json.dumps(row)); new['script']=plan.model_dump(mode='json'); new['audience_first']={'structure':['hook','human_meaning','evidence','action','concrete_cta'],'selected_claims':len(selected),'jargon_gate':'passed'}; output.append(new)
 DST.write_text(json.dumps({**source,'pipeline':['ResearchPack','validate_research_pack','angle_planner','audience_first_explainer','evidence_preserving_ru','jargon_gate','narrative_gate','diversity_gate'],'drafts':output},ensure_ascii=False,indent=2),encoding='utf-8'); print(f'v3_drafts={len(output)} output={DST}')
if __name__=='__main__': main()
