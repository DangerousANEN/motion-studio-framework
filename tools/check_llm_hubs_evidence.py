"""Validate all evidence packs used by the LLM Hubs video series."""
import json
import sys
from pathlib import Path

from msf.studio.contracts import ResearchPack
from msf.studio.research import validate_research_pack


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("projects/llm_hubs/evidence_packs.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    for raw in payload["packs"]:
        pack = ResearchPack.model_validate(raw)
        warnings = validate_research_pack(pack)
        if warnings:
            raise SystemExit(f"{pack.research_id}: unexpected source warnings: {warnings}")
        print(f"{pack.research_id}: sources={len(pack.sources)} claims={len(pack.claims)} OK")
