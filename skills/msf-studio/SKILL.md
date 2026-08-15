---
name: msf-studio
description: Создавать, проверять, отлаживать и расширять ролики в Motion Studio Framework. Использовать для storyboard, выбора stable сцен/эффектов/музыки/SFX, создания draft-роликов, research evidence, добавления голосов, создания или модификации TSX-сцен и расследования сбоев MSF.
---

# MSF Studio

## Обязательный старт

1. Определить результат: `video`, `storyboard`, `research`, `voice`, `audio-pack`, `media-guide`, `new-scene`, `modify-scene` или `debug`.
2. Определить tier: `preset`, `curated`, `sandbox` или `release`.
3. Запросить текущий catalog/manifest через MSF API или MCP. Не вспоминать имена presets, props, effects или voices из памяти.
4. Использовать только props из `SceneManifest.fields` и stable assets, если tier не разрешает draft.
5. Создать versioned draft и валидировать его до preview/render.

Не передавать свободный JSON напрямую renderer-у. Всегда собирать `StoryboardDraft` и выполнять `validate_storyboard`.

## Execution tiers

| Tier | Когда применять | Разрешено | Запрещено |
|---|---|---|---|
| `preset` | Нужен надёжный ролик из готовых assets. | Stable scenes, draft storyboard, preview, approved render. | TSX, manifests, draft assets, регистрация голоса. |
| `curated` | Нужна авторская композиция в библиотеке. | Комбинировать stable scenes, props/effects/audio policies. | Менять renderer-код или публиковать asset. |
| `sandbox` | Нужны новая/изменённая сцена, effect, voice или audio pack. | Draft workspace, manifests, fixtures, preview и tests. | Менять stable asset in place или пропускать quality gate. |
| `release` | Нужна публикация в stable catalog. | Review, versioning, publish/rollback. | Публиковать без tests, preview, consent/license metadata и approval. |

## Preset video: низкая свобода

Прочитать `workflows/preset-video.md`.

1. Превратить brief в intent tags, required data и brand constraints.
2. Вызвать `search_library`; выбрать не более трёх кандидатов на блок и объяснить выбор manifest-ом.
3. Вызвать `get_scene_manifest` для каждого выбранного preset.
4. Создать draft только со schema-compatible props. Для data-driven scenes передать все `required_data_hints`.
5. Выполнить `validate_storyboard`. Исправлять только диагностированные поля; не заменять поля догадками.
6. Сначала создать preview. Render запускать только после policy/пользовательского approval.
7. Вернуть run, artifacts, QA и короткий production summary.

При `scene.data_missing` собрать настоящие данные или использовать предложенные presets. Не выдумывать metric/rows/messages.

## Curated storyboard: средняя свобода

Прочитать `workflows/curated-storyboard.md`. Использовать только stable catalog. Выбирать эффекты по visual intent и audio роли по `recommended_audio_roles`. Не добавлять более одного сильного effect на сцену без явной причины. Делить длинные мысли на сцены и соблюдать safe area/readability diagnostics.

## New or modified scene: sandbox

Прочитать `workflows/create-scene.md` либо `workflows/modify-scene.md`.

1. Сначала описать `SceneManifest`: visual intent, inputs, safe-area policy, effects, audio roles и demo fixture.
2. Создать draft component/version. Никогда не менять stable scene in place.
3. Добавить Zod schema, registry entry, demo props и Python wire contract, если нужны новые props.
4. Выполнить typecheck, schema validation, preview/still render и visual/readability review.
5. Сформировать `AssetChangeSet`: files, fixture, preview, tests, migration/compatibility notes.
6. Передать change set на release review. Не объявлять asset stable самостоятельно.

Не вставлять `Math.random()` в Remotion components/effects. Использовать seeded randomness либо deterministic functions. Сохранять `intensity=0` как visual no-op для effect wrappers.

## Media insert / screen guide

Прочитать `workflows/media-guide.md`. Использовать `ScreenGuide`, `ScreenRecord`, `YouTubeCard`, `ImageSpotlight` и `TelegramVoiceRound` для настоящих assets; не рисовать имитацию продукта, когда доступен разрешённый screenshot/recording. Проверять asset consent/license, удалять credentials/PII, задавать 1–3 cursor steps с coordinates `0..1` и делать preview на каждом focus/click моменте. Выбирать `product_tutorial`, `social_native`, `creator_glass` или `terminal` через catalog; изменять только safe `styleConfig` tokens, не CSS/JS.

## Expansion styles and scenes

При выборе visual system сначала вызвать style catalog, затем выбрать family по **visual job**, а не только по цвету. Для premium launch использовать `aurora_flux`, для B2B/data — `cobalt_command`, для deadline — `infrared_alert`, для premium narrative — `violet_luxe`, для education — `porcelain`, для product reveal — `liquid_chrome`, для hook — `kinetic_poster`, для ecosystem/roadmap — `midnight_orbit`, для playful onboarding — `pixel_arcade`, для creator/social — `coral_creator`.

Для разнообразного storyboard не повторять одну композицию: чередовать hook (`HookStack`, `KineticPhrase`, `ColdOpenContradiction`), proof (`QuoteEvidence`, `SourceStack`, `ClaimEvidenceChain`, `EvidenceConflictBoard`), explain (`ProblemSolution`, `MythFact`, `FeatureSpotlight`, `DecisionTree`), social (`ProviderChat`, `TelegramChannelPost`, `CommunityFAQ`, `PromptABLab`), data (`BenchmarkArena`, `BenchmarkHeatmap`, `CostQualityScatter`, `TrueCostCalculator`) и tutorial/media (`BrowserTour`, `ThreePhoto360Drift`, `AppScreenGallery`, `DocumentMarginNotes`, `VideoChapterRail`). Передавать только manifest fields; media URL должен пройти existing asset policy.

Для 3D выбирать `AssetOrbit3D`, `ExplodedProductView`, `WorkflowFlyThrough3D`, `DataCube`, `LogoSculpture3D`, `DeviceConveyor3D`, `ParticleDataField`, `IsometricWorkflowCity`, `GlobeSignalMap` или `MilestoneCorridor3D` только при явном `assetUrl` с `assetLicense`/attribution либо при использовании procedural fallback. Не скачивать и не извлекать модели из viewer без разрешённой загрузки. Для LLM-ролика предпочитать последовательность: `ColdOpenContradiction` → benchmark/data → claim/evidence → Telegram/community proof → `ProofBackedCTA`/`BrandOutroMosaic`.

## Add voice: consent-first

Прочитать `workflows/add-voice.md`. Проверить явное согласие, владельца, назначение и retention policy. Сохранять original/prepared copy раздельно. Выполнить quality measurement, транскрипцию, пользовательскую правку и фиксированный audition text. Регистрировать голос как `draft`; stable publication требует human approval. Не использовать найденный в сети или неразрешённый голос.

## Add audio pack

Прочитать `workflows/add-audio-pack.md`. Добавлять audio через manifest с license/source, loudness, loop points, mood/semantic tags и gain boundaries. Для procedural audio добавлять registration, deterministic seed behavior и smoke test. Map SFX к semantic roles, а не к жёстким позициям одного ролика.

## Research video

Прочитать `workflows/research-video.md`. Хранить claims, source URL, retrieval date и confidence отдельно от сценарного текста. Factual scene должен ссылаться на evidence ID. При недостаточном evidence обозначать непроверенность или расширять исследование; не маскировать summary как источник.

## Debug run

Прочитать `workflows/debug-run.md`. Диагностировать по `RunEvent`, `TraceSpan`, diagnostics и artifacts. Показывать только наблюдаемые шаги: node, tool, status, duration, error и safe metadata. Не хранить/показывать hidden reasoning, prompts, credentials или raw private data. Начинать с первого `node.failed`/ERROR diagnostic. Не повторять expensive render, пока известная причина не исправлена.

## Инварианты

- `stable` и `draft` — разные lifecycle states.
- Catalog/manifest — источник доступности props/assets для агентов.
- Renderer changes проходят schema + TypeScript + fixture + preview проверки.
- GPU/external paid actions требуют policy/approval.
- Audio gain и duration берутся из manifest/defaults и validation, не из догадок.
- Style family задаёт базовый visual system; `styleConfig` меняет только allowlisted tokens (palette/backdrop/surface/motion/PostFX), не arbitrary CSS.
- Реальный screen/media asset проходит consent/PII review и держится отдельно от renderer source.
- Trace содержит operational telemetry, не chain-of-thought.

## Ресурсы

| Когда нужно | Прочитать |
|---|---|
| Выбрать scenes/effects/audio | `references/catalog-contract.md` |
| Проверить доступ и approval | `references/tiers-and-approvals.md` |
| Создать storyboard | `references/storyboard-policy.md` |
| Вставить media или screen guide | `workflows/media-guide.md` |
| Выбрать новые styles/scenes | `../../docs/MSF_STUDIO_STYLE_SCENE_EXPANSION.md` |
| Создать asset/release | `references/release-gates.md` |
| Разобрать trace/events | `references/observability.md` |
