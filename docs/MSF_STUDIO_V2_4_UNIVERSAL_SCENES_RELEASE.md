# MSF Studio v2.4 — Universal Scene Expansion

## Release summary

This release raises the live MSF scene catalog from **67 to 117 scenes** by adding **50 typed, theme-adaptive presets**. They are designed around the LLM/news workflow—benchmark, evidence, Telegram post, research, screen tutorial, media montage and CTA—while retaining reusable contracts for product, education, creator, B2B and non-technical topics.

| Group | Scene IDs | Count | Intended use |
|---|---|---:|---|
| Research and benchmarks | `BenchmarkArena` through `ReleaseDelta` | 12 | Benchmarks, pricing, test protocol, source and release evidence |
| Telegram and community | `TelegramChannelPost` through `BrowserDecisionTable` | 10 | Configurable Telegram channel, social proof, prompt and agent workflow |
| Media choreography | `ThreePhoto360Drift` through `ImageEvidenceCompare` | 10 | Three-photo 360° motion, screen/video, document and visual proof |
| Universal 3D | `AssetOrbit3D` through `MilestoneCorridor3D` | 10 | Licensed-model orbit, procedure fallback, workflow and data visualization |
| Narrative and conversion | `ColdOpenContradiction` through `BrandOutroMosaic` | 8 | High-retention opener, decision, trade-off, dated launch and proof-backed CTA |

## Recommended LLM/news sequence

> `ColdOpenContradiction` → `BenchmarkArena` or `CostQualityScatter` → `ClaimEvidenceChain` → `TelegramChannelPost` or `QuoteRepost` → `ProofBackedCTA` → `BrandOutroMosaic`.

Use `ThreePhoto360Drift` for cinematic editorial evidence, `AppScreenGallery` for a product walkthrough and `AssetOrbit3D`/`DataCube` as a short visual relief beat. Do not repeat the same category twice consecutively unless the narrative requires it.

## 3D asset safety

External 3D scenes accept `assetUrl`, `assetLicense` and `assetAttribution`. They render a deterministic procedural fallback when no approved GLB/glTF is supplied. This release does **not** scrape or redistribute Sketchfab viewer assets. See [MSF 3D asset policy](MSF_3D_ASSET_POLICY.md).

## Discovery and validation

Every new scene has a TypeScript component and registry definition, Zod props, Python `Scene` wire fields, Russian dashboard demo fixture, catalog intent/audio metadata and a unified-skill routing rule. The dashboard and MCP derive their live catalog from the central registry.

| Check | Result |
|---|---|
| TypeScript renderer check | Passed |
| Python fixture validation | Passed: `117` scenes / `117` demo fixtures |
| Dashboard/API live catalog | Passed: catalog total `117`, styles `+10` |
| MCP discovery | Passed: `117` `describe_scene` manifests |
| Prior right-edge overflow regression | Fixed and visually verified for `ProblemSolution` and `MythFact` |

## Key assets

| File | Purpose |
|---|---|
| `remotion/src/presets/expansion_research.tsx` | Twelve benchmark/evidence presets |
| `remotion/src/presets/expansion_community.tsx` | Ten Telegram/community/agent presets |
| `remotion/src/presets/expansion_media_choreography.tsx` | Ten media/editorial presets |
| `remotion/src/presets/three/Universal3D.tsx` | Licensed asset loader, camera and fallback foundation |
| `remotion/src/presets/expansion_three.tsx` | Ten universal 3D presets |
| `remotion/src/presets/expansion_narrative_utility.tsx` | Eight narrative/conversion presets |
| `docs/MSF_NEXT_50_SCENE_CONCEPTS.md` | Russian concept and selection catalog |
| `docs/MSF_3D_ASSET_POLICY.md` | 3D license and attribution policy |
