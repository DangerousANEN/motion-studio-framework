# MSF Studio — Style & Scene Expansion Blueprint

## Цель

Расширение добавляет **10 новых style families** и **20 новых typed scenes** поверх существующего каталога. Style family определяет палитру, типографический характер, motion, backdrop, surface и post-FX, но не привязывает scene к одному цвету: оператор может безопасно переопределить `palette.neon`, `palette.bg`, `palette.surface`, `palette.cyan`, `palette.text`, `palette.muted`, backdrop/surface, `effects.bloom|grain|vignette|scanlines|chromatic` и stable motion tokens через `styleConfig`.

> Новый preset обязан решать отдельную визуальную задачу. Запрещено добавлять два одинаковых text-card presets с разными названиями.

## Десять новых style families

| ID | Визуальная работа | Характер | Рекомендуемые scenes |
|---|---|---|---|
| `aurora_flux` | Премиальный запуск или абстрактная технология | teal/violet aurora, mesh, glass | `FeatureSpotlight`, `DeviceShowcase`, `VideoFrame` |
| `cobalt_command` | B2B, инфраструктура и управленческие данные | cobalt blue, precise grid, soft panels | `SourceStack`, `StatsBand`, `BrowserTour` |
| `infrared_alert` | Breaking update и deadline | near-black/red, ticker urgency | `HookStack`, `CountdownRing`, `NotificationStack` |
| `violet_luxe` | Creator/premium narrative | violet/ice, cinematic glass | `CaseStudyBoard`, `QuoteEvidence`, `VoiceWave` |
| `porcelain` | Чистый educational explainers | light porcelain, ink typography, flat surfaces | `MythFact`, `ProblemSolution`, `QuoteEvidence` |
| `liquid_chrome` | Product reveal и 3D-like material framing | graphite/chrome/cyan, reflective mesh | `DeviceShowcase`, `FeatureSpotlight`, `ScreenMagnifier` |
| `kinetic_poster` | Сильный social hook | black/white/acid accent, poster scale | `KineticPhrase`, `HookStack`, `CountdownRing` |
| `midnight_orbit` | Космос, model ecosystem, roadmap | deep navy/orbit cyan, calm depth | `SourceStack`, `CaseStudyBoard`, `StatsBand` |
| `pixel_arcade` | Игровая механика, challenge, onboarding | pixel grid, lime/purple, stepwise motion | `PollResult`, `MythFact`, `PromptComposer` |
| `coral_creator` | Человечный creator/social контент | coral/peach on dark berry, soft cards | `CommentThread`, `VideoFrame`, `NotificationStack` |

## Двадцать новых scenes

| Pack | Preset | Visual job | Основные typed props |
|---|---|---|---|
| Narrative | `HookStack` | Резкий 2–3-level opening claim с proof pill | `headline`, `subhead`, `proof`, `urgency` |
| Narrative | `KineticPhrase` | Слово/фраза как ритмический anchor между beats | `phrase`, `highlight`, `caption` |
| Narrative | `ProblemSolution` | Проблема → решение через направленный split | `problem`, `solution`, `title` |
| Narrative | `FeatureSpotlight` | Один feature с benefit и indicator | `feature`, `benefit`, `index`, `title` |
| Narrative | `CaseStudyBoard` | Контекст → действие → результат без выдуманных цифр | `context`, `action`, `result`, `label` |
| Narrative | `MythFact` | Контраст myth/fact для education | `myth`, `fact`, `title` |
| Narrative | `QuoteEvidence` | Структурированная цитата с source attribution | `quote`, `source`, `role`, `title` |
| Narrative | `StatsBand` | Горизонтальная полоса 2–4 stat blocks | `stats`, `title`, `footnote` |
| Narrative | `SourceStack` | Карточки первоисточников и evidence hierarchy | `sources`, `title`, `status` |
| Narrative | `CountdownRing` | Условия, дата, release window или CTA deadline | `value`, `label`, `caption`, `progress` |
| Social | `PromptComposer` | Ввод prompt с controlled type/read dwell | `prompt`, `provider`, `sendLabel` |
| Social | `ProviderChat` | Красивый branded provider response с avatar | `provider`, `avatarText`, `prompt`, `answer`, `chips` |
| Social | `NotificationStack` | 1–3 platform-independent notification overlays | `notifications`, `title` |
| Social | `CommentThread` | Social proof / discussion thread | `comments`, `title`, `platformLabel` |
| Social | `PollResult` | Poll card с votes/progress and safe labels | `question`, `options`, `title` |
| Tutorial | `BrowserTour` | Browser chrome, URL bar и пронумерованные шаги | `url`, `title`, `steps`, `screenshotUrl` |
| Tutorial | `ScreenMagnifier` | Focused crop/zoom around screenshot region | `mediaUrl`, `focus`, `caption`, `zoom` |
| Tutorial | `DeviceShowcase` | Phone/desktop media inside adaptive device frame | `mediaUrl`, `device`, `title`, `caption` |
| Media | `VoiceWave` | Voice message/player with deterministic waveform and duration | `speaker`, `duration`, `caption`, `waveformSeed` |
| Media | `VideoFrame` | YouTube/reel-like video frame with chapter marker | `mediaUrl`, `title`, `channel`, `duration`, `chapter` |

## Compatibility rules

| Rule | Requirement |
|---|---|
| Theme adaptation | Every new preset reads `useStyle()`/`useSceneStyle()` and never hardcodes the active palette. Provider identity may supply a local accent only. |
| Typography | Use inner-card measured width, `fitOneLine`/`fitWrapped` where text is dynamic, `wordBreak: 'keep-all'` for primary Cyrillic headline and no constant scale animation during reading dwell. |
| Media safety | Media URLs flow through existing asset policy; a missing media URL renders a designed placeholder, never a broken native image icon. |
| Preset-tier agents | Choose the schema-registered props only; no custom CSS or arbitrary external component code. |
| Sandbox-tier agents | May compose the new typed scenes, create a new family from approved tokens, or propose a new scene pack with matching registry/schema/demo wiring. |
| Discovery | Every scene needs TypeScript registry entry, Zod schema, Python wire mapping, demo props, catalog intent/audio metadata and MCP/dashboard discoverability. |

## Quality gates

The extension is accepted only when TypeScript passes, the live catalog exposes every new preset and style, demo props validate through the same wire contract, and selected previews render without fallback composition or clipping. The catalog is dynamic: dashboard uses `/api/studio/catalog` and `/api/studio/styles`; MCP uses `search_scene_catalog`, `describe_scene`, `list_style_families` and `msf://styles`.
