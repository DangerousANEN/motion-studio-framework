"""Generate text-only LLM Hubs storyboards from MSF-owned evidence packs.

This is deliberately a pipeline stage, not a hand-written content list:
ResearchPack -> validate_research_pack -> plan_from_claims -> validate_script_plan
-> diversity/style gate -> JSON artifacts. It emits no render spec and makes no
web request. Fresh retrieval remains a separate upstream research job.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from msf.studio.contracts import ResearchPack
from msf.studio.research import validate_research_pack
from msf.studio.script_planner import plan_from_claims, validate_script_plan

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "projects" / "llm_hubs" / "evidence_packs_2026-08-14.json"
OUT = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_2026-08-14.json"

# Two production angles per evidence topic. The actual factual lines are emitted
# solely from ResearchPack.claims by plan_from_claims().
VARIANTS: dict[str, list[dict[str, Any]]] = {
    "research_gemini37_vs_sonnet5": [
        {"title": "GEMINI 3.7 FLASH: ГДЕ ОН СИЛЬНЕЕ — А ГДЕ НЕТ", "hook": "НЕ ВЕРЬТЕ ФРАЗЕ «УБИЛ SONNET». СМОТРИТЕ НА КОНКРЕТНЫЙ ТЕСТ.", "style": "cobalt_command", "presets": ["BenchmarkArena", "CapabilityRadar", "ClaimEvidenceChain", "ProofBackedCTA"]},
        {"title": "GEMINI 3.7 FLASH: ЦЕНА — ЭТО ЕЩЁ НЕ ВЫГОДА", "hook": "ДЕШЕВЛЕ API — НЕ ЗНАЧИТ ДЕШЕВЛЕ ВАШ WORKLOAD.", "style": "porcelain", "presets": ["TrueCostCalculator", "CostQualityScatter", "ExperimentProtocol", "BrandOutroMosaic"]},
    ],
    "research_deepseek_v4pro_release": [
        {"title": "DEEPSEEK V4 PRO ВЫШЕЛ ИЗ PREVIEW: ЧТО МЕНЯЕТСЯ", "hook": "НЕ «GA» ВАЖЕН. ВАЖНО, ЧТО ТЕПЕРЬ МОЖНО ПРОВЕРИТЬ НА СВОЁМ PIPELINE.", "style": "infrared_alert", "presets": ["ReleaseDelta", "ProviderChat", "ChangelogTerminal", "ProofBackedCTA"]},
        {"title": "REASONING В V4 PRO: КОГДА LOW ЛУЧШЕ MAX", "hook": "MAX НЕ ДЕЛАЕТ КАЖДЫЙ ОТВЕТ УМНЕЕ. ОН ДЕЛАЕТ ЕГО ДОРОЖЕ.", "style": "violet_luxe", "presets": ["KineticPhrase", "TradeoffSliders", "PromptABLab", "DecisionTree"]},
    ],
    "research_deepseek_v4pro_cost": [
        {"title": "DEEPSEEK PEAK/OFF-PEAK: КОГДА 50% ЭКОНОМИИ РЕАЛЬНЫ", "hook": "ЕСЛИ ВЫ НЕ ЗНАЕТЕ ЧАС ЗАПУСКА JOB — ВЫ НЕ ЗНАЕТЕ ЕЁ ЦЕНУ.", "style": "midnight_orbit", "presets": ["CalendarLaunchWindow", "TokenFlowSankey", "TrueCostCalculator", "DecisionTree"]},
        {"title": "КАК НЕ ПРОПУСТИТЬ СМЕНУ ТАРИФА", "hook": "ТАРИФ ПОМЕНЯЛСЯ НЕ КОГДА ВЫ УВИДЕЛИ ПОСТ, А В КОНКРЕТНОЕ ВРЕМЯ UTC.", "style": "kinetic_poster", "presets": ["CountdownRing", "DocumentMarginNotes", "BrowserTour", "TelegramChannelPost"]},
    ],
    "research_grok46_release": [
        {"title": "GROK 4.6: АГЕНТ ДОЛЬШЕ РАБОТАЕТ — НО КТО ПЛАТИТ ЗА RETRIES?", "hook": "ДЛИННЫЙ AGENT RUN — НЕ ПОБЕДА, ЕСЛИ ВЫ НЕ ВИДИТЕ ЕГО СЧЁТ.", "style": "liquid_chrome", "presets": ["AgentRunConsole", "TokenFlowSankey", "ClaimEvidenceChain", "ProofBackedCTA"]},
        {"title": "CACHE-AWARE ЦЕНА: КАК ЧИТАТЬ ЕЁ БЕЗ МАГИИ", "hook": "КЭШ МОЖЕТ СДЕЛАТЬ РЕЖИМ ДЕШЕВЛЕ. А МОЖЕТ НЕ СРАБОТАТЬ ВООБЩЕ.", "style": "aurora_flux", "presets": ["ThreePhoto360Drift", "TrueCostCalculator", "EvidenceConflictBoard", "BrandOutroMosaic"]},
    ],
    "research_august_model_costmap": [
        {"title": "ЧЕТЫРЕ МОДЕЛИ, ОДИН WORKLOAD: КАК СРАВНИВАТЬ ЧЕСТНО", "hook": "ЛУЧШАЯ МОДЕЛЬ В ТАБЛИЦЕ МОЖЕТ БЫТЬ ХУДШЕЙ ДЛЯ ВАШЕГО ПРОДУКТА.", "style": "coral_creator", "presets": ["TelegramChannelPost", "BenchmarkHeatmap", "TradeoffSliders", "CommunityFAQ"]},
        {"title": "АВГУСТОВСКАЯ COST MAP: С ЧЕГО НАЧАТЬ ТЕСТ", "hook": "НЕ НУЖНО ТЕСТИРОВАТЬ ДЕСЯТЬ МОДЕЛЕЙ. НУЖНО ОТСЕЯТЬ ЛИШНИЕ.", "style": "pixel_arcade", "presets": ["ColdOpenContradiction", "ContextWindowLadder", "DecisionTree", "BrandOutroMosaic"]},
    ],
}


def main() -> None:
    raw = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    packs = {item["research_id"]: ResearchPack.model_validate(item) for item in raw["packs"]}
    outputs: list[dict[str, Any]] = []
    styles: list[str] = []
    openings: list[str] = []

    for research_id, variants in VARIANTS.items():
        pack = packs[research_id]
        validate_research_pack(pack)
        for index, variant in enumerate(variants, start=1):
            plan = plan_from_claims(
                title=variant["title"], research=pack, hook=variant["hook"],
                cta_handle="@llm_hubs", intents=("hook", "evidence", "metric", "cta"),
            )
            validate_script_plan(plan, pack)
            opening = variant["presets"][0]
            outputs.append({
                "batch_id": f"{research_id}_{index}",
                "research_id": research_id,
                "research_topic": pack.topic,
                "style": variant["style"],
                "planned_presets": variant["presets"],
                "script": plan.model_dump(mode="json"),
                "source_urls": [source.url for source in pack.sources],
                "claim_ids": [claim.claim_id for claim in pack.claims],
            })
            styles.append(variant["style"])
            openings.append(opening)

    if len(outputs) != 10:
        raise RuntimeError(f"expected 10 drafts, got {len(outputs)}")
    if len(set(styles)) != len(styles):
        raise RuntimeError("one-style-per-video batch requires unique styles in this test")
    if len(set(openings)) != len(openings):
        raise RuntimeError("duplicate opening preset in batch")
    if any(len(set(item["planned_presets"])) != len(item["planned_presets"]) for item in outputs):
        raise RuntimeError("preset repeats inside a video")

    OUT.write_text(json.dumps({
        "pipeline": ["ResearchPack", "validate_research_pack", "plan_from_claims", "validate_script_plan", "diversity_gate"],
        "input_evidence": str(EVIDENCE.relative_to(ROOT)),
        "created_at": "2026-08-14",
        "drafts": outputs,
        "diversity_trace": {"styles": Counter(styles), "openings": Counter(openings)},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"drafts={len(outputs)} styles={len(set(styles))} openings={len(set(openings))} output={OUT}")


if __name__ == "__main__":
    main()
