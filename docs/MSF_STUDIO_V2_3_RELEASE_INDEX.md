# MSF Studio v2.3 — Theme-Adaptive Expansion Release Index

## Release scope

This release extends the stable MSF Studio catalog from **47 to 67 typed scenes** and adds **10 renderer-backed style families**. The release is designed for two operating modes: preset-tier agents select only discoverable manifests and allowlisted style tokens; sandbox-tier agents can extend scenes only through the matching renderer, schema, registry, fixture and wire-contract changes.

> **Discovery is live rather than duplicated.** The dashboard reads `/api/studio/catalog` and `/api/studio/styles`; MCP exposes `search_scene_catalog`, `describe_scene`, `list_style_families`, `msf://catalog/{tier}` and `msf://styles` from the same catalog sources.

## New style families

| Style ID | Visual job | Renderer defaults | Recommended scene types |
|---|---|---|---|
| `aurora_flux` | Premium technology launch | Teal-violet mesh, glass, luminous bloom, settled motion | Hooks, feature reveals, product media |
| `cobalt_command` | B2B systems and browser/data walkthrough | Cobalt grid, soft panels, controlled motion | Browser tours, proof, source stacks |
| `infrared_alert` | Deadline and breaking-update urgency | Red dot field, flat broadcast surface | Countdowns, notifications, corrective hooks |
| `violet_luxe` | Premium creator narrative | Violet-ice glass, cinematic mesh | Testimonials, creator stories, device media |
| `porcelain` | High-legibility education | Light flat surface, ink typography, near-zero FX | Myth/fact, evidence, explainers |
| `liquid_chrome` | Product reveal and reflective media frame | Graphite/cyan mesh, glass and controlled glow | Devices, features, screen focus |
| `kinetic_poster` | Strong social opening hook | Acid high-contrast poster panels | Hooks, phrases, polls and countdowns |
| `midnight_orbit` | Model ecosystems, roadmaps and research | Deep navy noise field, calm glass | Sources, case studies, stats |
| `pixel_arcade` | Playful onboarding and challenge | Lime-purple dot field, deliberate arcade motion | Polls, prompt input, notification moments |
| `coral_creator` | Community and social proof | Coral soft cards over berry noise | Provider chat, comments, voice/video cards |

Every family can be selected by ID. Operators can safely override only the documented `styleConfig` tokens: palette (`neon`, `bg`, `surface`, `cyan`, `text`, `muted`), `backdrop`, `surface`, PostFX (`bloom`, `grain`, `vignette`, `scanlines`, `chromatic`) and stable motion controls (`damping`, `stiffness`, `staggerScale`). Arbitrary CSS and scripts are intentionally excluded.

## New typed production scenes

| Pack | Scene | Primary visual job | Required production data |
|---|---|---|---|
| Narrative / proof | `HookStack` | Multi-level opening claim with proof pill | `headline`, `subhead` |
| Narrative / proof | `KineticPhrase` | Phrase anchor between story beats | `phrase` |
| Narrative / proof | `ProblemSolution` | Directed problem-to-solution split | `problem`, `solution` |
| Narrative / proof | `FeatureSpotlight` | Single feature plus benefit | `feature`, `benefit` |
| Narrative / proof | `CaseStudyBoard` | Context, action and result board | `context`, `action`, `result` |
| Narrative / proof | `MythFact` | Educational correction contrast | `myth`, `fact` |
| Narrative / proof | `QuoteEvidence` | Source-attributed evidence quotation | `quote`, `source` |
| Narrative / proof | `StatsBand` | Compact stat evidence band | `stats` |
| Narrative / proof | `SourceStack` | Primary-source hierarchy | `sources` |
| Narrative / proof | `CountdownRing` | Date, window or CTA condition | `value` |
| Social / tutorial / media | `PromptComposer` | Typed agent prompt and send action | `prompt` |
| Social / tutorial / media | `ProviderChat` | Branded provider dialogue | `provider`, `prompt`, `answer` |
| Social / tutorial / media | `NotificationStack` | Platform-neutral update overlays | `notifications` |
| Social / tutorial / media | `CommentThread` | Community conversation and social proof | `comments` |
| Social / tutorial / media | `PollResult` | Poll values and response choice | `options` |
| Social / tutorial / media | `BrowserTour` | Browser walkthrough and screenshot evidence | `screenshotUrl` or `src` |
| Social / tutorial / media | `ScreenMagnifier` | Controlled screenshot/video focus | `mediaUrl` or `src/images` |
| Social / tutorial / media | `DeviceShowcase` | Adaptive device-framed media | `mediaUrl` or `src/images` |
| Social / tutorial / media | `VoiceWave` | Deterministic voice-message presentation | `speaker` or `caption` |
| Social / tutorial / media | `VideoFrame` | Reel/video chapter framing | `mediaUrl` or `src/images` |

For every row above, this release contains a TypeScript registry entry, Zod fields, Python camelCase wire support, validated Russian-language demo props, intent tags, audio-role metadata and live dashboard/MCP discovery.

## Compatibility and safety changes

| Area | Release behavior |
|---|---|
| Typed options | `options` now accepts both legacy string arrays for `QuizCard` and typed `{label, value}` rows for `PollResult`. |
| Python pre-render validation | New structured presets fail before render if required meaningful input is absent; data rows use soft warnings only where the TypeScript schema genuinely permits missing display keys. |
| Registry parsing | Python discovery now correctly delimits compact inline TypeScript entries, preventing text-safe scenes from inheriting a later `dataDriven: true` flag. |
| Local media | Expansion social/tutorial media resolves relative paths through `staticFile()`, matching the existing media-pack contract. |
| Agent guidance | The unified `msf-studio` skill routes agents by visual job and encourages a varied hook → proof → explain → social/tutorial rhythm without inventing fields. |

## Verification record

| Check | Result |
|---|---|
| `tsc --noEmit -p tsconfig.studio.json` | Passed after final local-media fix. |
| `tools/check_studio_v2.py` | Passed: `scenes=67`, `demo_fixtures=67`. |
| Focused parity suite | Passed: `49 passed`, `139 subtests passed`; covers themes, registry names/categories/fields/data flags, row shapes and transitions. |
| `tools/check_studio_api.py` | Passed: full 67-scene API catalog, ten new style IDs, evidence/storyboard routing and styleConfig round-trip. |
| `tools/check_studio_mcp_protocol.py` | Passed: 20 expansion manifests via `describe_scene`, full search catalog and ten new style IDs. |
| Live dashboard HTTP | Passed: `/api/studio/styles` returned 16 style IDs and catalog returned 67 scenes. |
| Visual smoke | Four sampled 1080×1920 stills passed: `HookStack`/Aurora Flux, `SourceStack`/Midnight Orbit, `ProviderChat`/Coral Creator, `BrowserTour`/Cobalt Command. See `remotion/out/expansion-smoke/qa_findings.md`. |

## Included release assets

The source release includes the new scene packs, registry modules, style kits and palettes, dashboard/MCP catalog updates, demo fixture mapping, agent skill guidance, smoke scripts and this index. The generated smoke PNGs and generated preview media are intentionally excluded from the source archive to keep the distribution small and reproducible; `msf.panel.make_preview_assets` recreates local preview media on demand.
