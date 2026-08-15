"""Generate angle-first, evidence-backed text-only MSF storyboards."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from typing import Any
from msf.studio.contracts import ResearchPack
from msf.studio.research import validate_research_pack
from msf.studio.script_planner import StoryAngle, plan_from_angle, validate_script_plan

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "projects" / "llm_hubs" / "evidence_packs_2026-08-14.json"
OUT = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_v2_2026-08-14.json"

# Each record is deliberately a single viewer question, not a second dump of an
# entire research pack. `takeaway_claim_ids` fail closed against selected claims.
VARIANTS: dict[str, list[dict[str, Any]]] = {
 "research_gemini37_vs_sonnet5": [
  {"title":"Gemini 3.7 Flash: один тест, который ломает хайп", "hook":"Gemini не «убил» Sonnet — но в двух тестах он реально впереди.", "style":"cobalt_command", "presets":["BenchmarkArena","CapabilityRadar","ExperimentProtocol","ProofBackedCTA"], "angle":(["claim_g37_specific_benchmark_edge"],"Проверьте именно свою coding-задачу: две метрики — это повод для теста, а не для вердикта о «лучшем ИИ».",["claim_g37_specific_benchmark_edge"],"таблица двух тестов и шаблон своей проверки","Заберите в канале")},
  {"title":"Gemini дешевле Sonnet? Сначала посчитайте свой сценарий", "hook":"Цена API ниже на 62,5%. Но ваш продукт может не стать дешевле.", "style":"porcelain", "presets":["TrueCostCalculator","CostQualityScatter","PromptABLab","BrandOutroMosaic"], "angle":(["claim_g37_release_price","claim_g37_price_gap_sonnet"],"Сначала сравните стоимость одной законченной задачи, а не цену миллиона токенов в прайсе.",["claim_g37_price_gap_sonnet"],"калькулятор стоимости одной задачи","Он уже лежит в")},
 ],
 "research_deepseek_v4pro_release": [
  {"title":"DeepSeek V4 Pro: что реально стало доступно", "hook":"Не слово «GA» важно. Важно, что вы можете проверить уже сегодня.", "style":"infrared_alert", "presets":["ReleaseDelta","ProviderChat","ScreenMagnifier","ProofBackedCTA"], "angle":(["claim_ds_v4pro_ga_access","claim_ds_v4pro_capabilities"],"Возьмите одну знакомую задачу с JSON или инструментами и сравните результат, а не рекламный список возможностей.",["claim_ds_v4pro_capabilities"],"мини-чеклист первого теста V4 Pro","Заберите в")},
  {"title":"DeepSeek: когда low разумнее max", "hook":"Max не делает каждый ответ умнее. Он делает его дороже.", "style":"violet_luxe", "presets":["KineticPhrase","TradeoffSliders","PromptABLab","DecisionTree"], "angle":(["claim_ds_v4pro_reasoning"],"Для простого извлечения начинайте с low, а более тяжёлые рассуждения проверяйте отдельно — не платите максимум по умолчанию.",["claim_ds_v4pro_reasoning"],"карточка выбора low/high/max","Заберите в")},
 ],
 "research_deepseek_v4pro_cost": [
  {"title":"Цена DeepSeek меняется в 16:00 UTC: почему это важно", "hook":"Тариф — это не пост в ленте. Это конкретная минута в счёте.", "style":"midnight_orbit", "presets":["CalendarLaunchWindow","TokenFlowSankey","TrueCostCalculator","DecisionTree"], "angle":(["claim_ds_future_offpeak","claim_ds_future_not_current"],"В смете отдельно подпишите цену до даты изменения и цену после неё — иначе сравнение будет ложным.",["claim_ds_future_offpeak","claim_ds_future_not_current"],"шаблон сметы до/после смены тарифа","Он уже в")},
  {"title":"Как не перепутать старую цену с новой", "hook":"Самая дорогая ошибка — считать будущий тариф сегодняшней ценой.", "style":"kinetic_poster", "presets":["DocumentMarginNotes","BrowserTour","TelegramChannelPost","BrandOutroMosaic"], "angle":(["claim_ds_current_prices","claim_ds_future_not_current"],"Ведите две строки: текущий счёт и объявленный счёт после даты вступления изменений.",["claim_ds_current_prices","claim_ds_future_not_current"],"готовая таблица текущих и будущих тарифов","Заберите в")},
 ],
 "research_grok46_release": [
  {"title":"Grok 4.6: длинный агент может стать дорогим", "hook":"Агент работает дольше — но вы видите цену его повторов?", "style":"liquid_chrome", "presets":["AgentRunConsole","TokenFlowSankey","TrueCostCalculator","ProofBackedCTA"], "angle":(["claim_grok46_release_focus","claim_grok46_price_cache"],"Для долгих запусков измеряйте retries и выходные токены: именно они превращают «интересный агент» в счёт.",["claim_grok46_release_focus","claim_grok46_price_cache"],"калькулятор agent-run с повторами","Он в")},
  {"title":"Grok 4.6: 500K контекста — что проверить первым", "hook":"Большой контекст не решает задачу, если агент не вызывает нужные инструменты.", "style":"aurora_flux", "presets":["ThreePhoto360Drift","ContextWindowLadder","DeviceShowcase","BrandOutroMosaic"], "angle":(["claim_grok46_api_capabilities"],"Проверяйте не размер окна сам по себе, а ваш реальный сценарий: контекст, инструмент и структурированный ответ в одном тесте.",["claim_grok46_api_capabilities"],"протокол теста длинного контекста","Заберите в")},
 ],
 "research_august_model_costmap": [
  {"title":"Четыре модели: не выбирайте по самой низкой цене", "hook":"Самая дешёвая строка в прайсе может проиграть на вашей задаче.", "style":"coral_creator", "presets":["TelegramChannelPost","BenchmarkHeatmap","TradeoffSliders","CommunityFAQ"], "angle":(["claim_costmap_input","claim_costmap_not_benchmark"],"Сначала исключите модели по требованиям задачи, а цену сравнивайте только между теми, что прошли ваш тест.",["claim_costmap_input","claim_costmap_not_benchmark"],"матрицу «модель × тип задачи»","Она в")},
  {"title":"С чего начать тест четырёх LLM за 15 минут", "hook":"Не тестируйте десять моделей. Сначала отсейте лишние.", "style":"pixel_arcade", "presets":["ColdOpenContradiction","BenchmarkHeatmap","DecisionTree","BrandOutroMosaic"], "angle":(["claim_costmap_output","claim_costmap_not_benchmark"],"Выберите одну задачу, один критерий качества и один лимит стоимости — этого достаточно для первого отсечения.",["claim_costmap_output","claim_costmap_not_benchmark"],"15-минутный протокол первого LLM-теста","Заберите в")},
 ],
}

def main() -> None:
 raw=json.loads(EVIDENCE.read_text(encoding='utf-8')); packs={x['research_id']:ResearchPack.model_validate(x) for x in raw['packs']}
 rows=[]; styles=[]; openings=[]
 for research_id, variants in VARIANTS.items():
  pack=packs[research_id]; validate_research_pack(pack)
  for n,v in enumerate(variants,1):
   selected,takeaway,takeaway_ids,asset,cta=v['angle']
   angle=StoryAngle(tuple(selected),takeaway,tuple(takeaway_ids),asset,cta)
   plan=plan_from_angle(title=v['title'],research=pack,hook=v['hook'],angle=angle,cta_handle='@llm_hubs')
   validate_script_plan(plan,pack)
   rows.append({'batch_id':f'{research_id}_{n}','research_id':research_id,'research_topic':pack.topic,'style':v['style'],'planned_presets':v['presets'],'angle':{'selected_claim_ids':selected,'takeaway':takeaway,'cta_asset':asset},'script':plan.model_dump(mode='json'),'source_urls':[s.url for s in pack.sources],'claim_ids':selected})
   styles.append(v['style']); openings.append(v['presets'][0])
 if len(rows)!=10 or len(set(styles))!=10 or len(set(openings))!=10: raise RuntimeError('diversity gate failed')
 OUT.write_text(json.dumps({'pipeline':['ResearchPack','validate_research_pack','angle_planner','plan_from_angle','validate_script_plan','diversity_gate'],'input_evidence':str(EVIDENCE.relative_to(ROOT)),'created_at':'2026-08-14','drafts':rows,'diversity_trace':{'styles':Counter(styles),'openings':Counter(openings)}},ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'drafts={len(rows)} styles={len(set(styles))} openings={len(set(openings))} output={OUT}')
if __name__=='__main__': main()
