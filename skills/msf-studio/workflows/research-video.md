# Research video workflow

1. Break the brief into individually verifiable claims.
2. Retrieve at least two current sources; use official/primary documentation for pricing, free tiers, availability and model limits.
3. Store each source as `EvidenceSource` with URL, publisher, retrieval date, type and a bounded excerpt.
4. Store every claim as `EvidenceClaim` with source IDs and confidence. Run `validate_research_pack`; stop on a hard error.
5. Build `ScriptPlan` where every `fact`, `interpretation` or `instruction` line has an evidence claim ID. Hooks and CTA are explicitly non-factual.
6. Run `validate_script_plan`, then `storyboard_from_script`; preserve evidence claim IDs on each factual scene.
7. Validate storyboard with the original `ResearchPack`. If evidence conflicts or is incomplete, state uncertainty, seek another source or remove the claim.

Never use a search-result snippet as final evidence and never fabricate citations to satisfy a storyboard format.
