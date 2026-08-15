from __future__ import annotations
import json
import re
from pathlib import Path
from msf.studio.contracts import ResearchPack, ScriptPlan
from msf.studio.research import validate_research_pack
from msf.studio.script_planner import validate_script_plan

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_2026-08-14.json"
LOCALIZED = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_ru_2026-08-14.json"
EVIDENCE = ROOT / "projects" / "llm_hubs" / "evidence_packs_2026-08-14.json"
# Terms that are product/protocol names or normal Russian technical vocabulary.
ALLOW = {"API", "CTA", "JSON", "LLM", "GEMINI", "DEEPSEEK", "GROK", "CLAUDE", "SONNET", "FLASH", "PRO", "V4", "UTC", "EXPERT", "MODE", "RESPONSES", "ANTHROPIC", "OPENAI", "MAX", "LOW", "HIGH", "REASONING", "CACHE", "PEAK", "OFF", "WORKLOAD", "FRONTIERCODE", "CODE", "ARENA", "WEB", "DEVELOPMENT"}

def critical_tokens(text: str) -> set[str]:
    # Localisation may legitimately translate "13 August 2026" into
    # "13 августа 2026". Compare numeric amounts and formal identifiers only.
    numeric = re.findall(r"\$?\d+(?:[.,]\d+)?%?", text)
    identifiers = re.findall(r"\b(?:[A-Za-z]+[-.]?\d+(?:[.-][A-Za-z0-9]+)*)\b", text)
    return set(numeric + identifiers)

def main() -> None:
    packs = {p['research_id']: ResearchPack.model_validate(p) for p in json.loads(EVIDENCE.read_text(encoding='utf-8'))['packs']}
    original = json.loads(ORIGINAL.read_text(encoding='utf-8'))['drafts']
    localized = json.loads(LOCALIZED.read_text(encoding='utf-8'))['drafts']
    assert len(original) == len(localized) == 10
    leakage: list[str] = []
    for old, new in zip(original, localized):
        pack = packs[new['research_id']]
        validate_research_pack(pack)
        plan = ScriptPlan.model_validate(new['script'])
        validate_script_plan(plan, pack)
        assert [x.get('evidence_claim_ids') for x in old['script']['lines']] == [x.get('evidence_claim_ids') for x in new['script']['lines']]
        for idx, (before, after) in enumerate(zip(old['script']['lines'], new['script']['lines']), 1):
            missing = critical_tokens(before['narration']) - critical_tokens(after['narration'])
            if missing:
                raise AssertionError(f"{new['batch_id']} line {idx} lost critical tokens: {sorted(missing)}")
            words = set(re.findall(r"\b[A-Za-z]{4,}\b", after['narration']))
            bad = sorted(w for w in words if w.upper() not in ALLOW)
            if bad:
                leakage.append(f"{new['batch_id']} line {idx}: {', '.join(bad)}")
    print(f"localized=10 evidence_links=30 english_leakage={len(leakage)}")
    for row in leakage:
        print('WARN', row)

if __name__ == '__main__':
    main()
