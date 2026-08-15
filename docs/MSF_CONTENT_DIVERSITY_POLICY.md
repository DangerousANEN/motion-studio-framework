# MSF Content Diversity Policy

## Цель

Эта policy применяется до storyboard и render. Она не даёт pipeline собирать десять роликов из одинаковых hook, chat и CTA сцен, даже если все они технически валидны.

## Жёсткие правила

| Правило | Требование |
|---|---|
| Style consistency | Ровно один `style` на один ролик. Разрешены только safe `styleConfig` token overrides внутри этой family. |
| Scene diversity | В одном ролике нельзя повторять preset. В соседних роликах нельзя повторять один и тот же opening preset. |
| Visual rhythm | Ролик должен содержать минимум три разных visual categories: hook/narrative, proof/data, interface/media/3D/community. |
| Data discipline | Benchmark, price, release и claim scenes получают источник, дату и caveat; при отсутствии проверки тема не идёт в production. |
| CTA discipline | `ProofBackedCTA`, `TelegramChannelPost` или `BrandOutroMosaic` используются только после proof/explain beat, а не вместо содержания. |
| Media discipline | Реальный screenshot/video получает отдельную media/tutorial scene; нельзя заменять его выдуманным UI. |

## Тематическое routing

| Тема | Предпочтительные сцены | Style family |
|---|---|---|
| Новая модель / релиз | `ColdOpenContradiction`, `ReleaseDelta`, `ClaimEvidenceChain`, `TelegramChannelPost`, `ProofBackedCTA` | `infrared_alert` или `kinetic_poster` |
| Бенчмарк / сравнение | `BenchmarkArena`, `CostQualityScatter`, `CapabilityRadar`, `EvidenceConflictBoard`, `TradeoffSliders` | `cobalt_command` |
| Экономия / стоимость | `TrueCostCalculator`, `TokenFlowSankey`, `ContextWindowLadder`, `DecisionTree` | `porcelain` или `cobalt_command` |
| Tutorial / workflow | `BrowserTour`, `ScreenGuide`, `AgentRunConsole`, `WorkflowFlyThrough3D`, `AppScreenGallery` | `liquid_chrome` |
| Telegram / creator | `TelegramChannelPost`, `TelegramFeedScroll`, `ReactionPulse`, `QuoteRepost`, `BrandOutroMosaic` | `coral_creator` |
| Research / фактчек | `ClaimEvidenceChain`, `SourceStack`, `DocumentMarginNotes`, `ExperimentProtocol`, `ImageEvidenceCompare` | `midnight_orbit` |
| Пояснение / thought leadership | `KineticPhrase`, `MythFact`, `CounterfactualSplit`, `MemoryTimeline`, `ProofBackedCTA` | `violet_luxe` |
| Visual editorial | `ThreePhoto360Drift`, `PhotoConstellation`, `DeepZoomStory`, `VoiceNotePullQuote`, `VideoChapterRail` | `aurora_flux` |

## Pre-render checklist

Планировщик обязан выдать для каждого ролика: topic, evidence pack, один style family, unique opening, scene-category sequence, narration beats, CTA и explicit source/caveat. Если хотя бы два ролика имеют совпадающую первые три preset IDs или один и тот же style family без тематического обоснования, batch отклоняется до render.
