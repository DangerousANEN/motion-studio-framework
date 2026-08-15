"""Quality gate for pipeline-generated text-only storyboard batch."""
from __future__ import annotations

import json
from pathlib import Path

from msf.studio.catalog import all_scenes
from msf.studio.contracts import ResearchPack, ScriptPlan
from msf.studio.research import validate_research_pack
from msf.studio.script_planner import validate_script_plan

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "projects" / "llm_hubs" / "evidence_packs_2026-08-14.json"
BATCH = ROOT / "projects" / "llm_hubs" / "pipeline_text_storyboards_2026-08-14.json"


def main() -> None:
    packs_raw = json.loads(EVIDENCE.read_text(encoding="utf-8"))["packs"]
    packs = {row["research_id"]: ResearchPack.model_validate(row) for row in packs_raw}
    for pack in packs.values():
        validate_research_pack(pack)

    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    drafts = batch["drafts"]
    assert len(drafts) == 10, len(drafts)
    live = {scene.name for scene in all_scenes()}
    styles, openings = [], []
    cited_lines = 0
    for row in drafts:
        pack = packs[row["research_id"]]
        plan = ScriptPlan.model_validate(row["script"])
        validate_script_plan(plan, pack)
        assert row["source_urls"], row["batch_id"]
        assert set(row["claim_ids"]) <= {claim.claim_id for claim in pack.claims}
        presets = row["planned_presets"]
        assert set(presets) <= live, (row["batch_id"], sorted(set(presets) - live))
        assert len(presets) == len(set(presets)), row["batch_id"]
        styles.append(row["style"])
        openings.append(presets[0])
        cited_lines += sum(bool(line.evidence_claim_ids) for line in plan.lines)
    assert len(styles) == len(set(styles)), "style family repeats in this diversity test"
    assert len(openings) == len(set(openings)), "opening preset repeats in this diversity test"
    assert cited_lines >= 20, cited_lines
    print(f"drafts={len(drafts)} styles={len(set(styles))} openings={len(set(openings))} cited_lines={cited_lines} catalog={len(live)}")


if __name__ == "__main__":
    main()
