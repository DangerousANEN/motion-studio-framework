# LLM Hubs Series — Production Rework Audit

**Date:** 14 August 2026 (GMT+7)  
**Status:** Rebuild required before publication.

## Findings

| Area | Observed state | Root cause | Required correction |
|---|---|---|---|
| Research selection | The existing five topics focus on evergreen usage patterns and older pricing/routing material rather than the user-prioritised releases. | The series research brief optimised for cheap/free usage before a breaking-release selection gate existed. | Replace the editorial slate with current release-led topics: Gemini 3.7 Flash vs Sonnet 5 cost/quality, DeepSeek V4 Pro 0813, Grok 4.6, plus two current adjacent economical-use stories verified from primary sources. |
| Visual direction | Frames mix yellow/gold neo-brutal cards with the desired neon-green CTA language. | `build_series.py` passes `theme="noir"`, while `MainComposition` reads `style`; no global `style` is emitted. Several legacy presets also import hardcoded `BRAND` colors. | Build every spec with a single green-on-near-black style system. Replace the gold hero card with dark glass surfaces, a controlled green highlight and white type. Remove gold from all new scene props. |
| Scene variety | Each video repeats a nearly identical sequence: hero → quote → step list → CTA, with one variation. | Series builder uses a common five-scene pattern and never calls the broader catalog. | Use different bounded narrative structures per episode: product card/chat, metric trend, comparison grid, decision matrix, timeline, code/API, screen workflow, quote evidence and CTA. Do not repeat an entire scene sequence. |
| Voice-over | No narration path exists in the builder. | ScriptPlan text is saved but never synthesised, timed or mixed into a root track. | Generate Russian narration for each script, fit visual timings to the actual spoken duration and use deterministic loudness ducking for music during speech. |
| Music and SFX | A root WAV is present, but its exported level averages around -42 dBFS; cue count is limited. | Bed gain is deliberately low and there is no mastering/mix stage; only four generic cues are rendered. | Produce a mastered speech-aware mix: music under narration at approximately -28 LUFS short-term, foreground SFX accents at safe peaks, and export-normalised AAC. Give every scene at least one purposeful audio event, avoiding clutter. |
| Text motion | `HeroKinetic` hardcodes scale/rotation spring movement and a gold accent. The default `pop` kit is aggressive. | The current builder does not set a stable style; individual legacy presets remain pop-brutalist. | Add a release-safe motion profile: one entrance, no looping transform, overshoot clamping, 8–12 frame settle before text is read. Do not use high-frequency wobble, grain flicker or RGB split on text. |
| Audio stream | Current MP4 files do include AAC but no speech; source music/SFX is too quiet for social playback. | Root `<Audio>` is correctly mounted, but only receives an under-levelled procedural bed. | Preserve the root audio approach; replace its input with a speech + music + SFX master and verify stream/peak/loudness after export. |

## Non-negotiable art direction

> **LLM Hubs signature:** near-black technical background, neon-green primary accent, restrained aqua secondary accent, white body type, glass/dark surfaces, crisp readable Russian typography. Gold/yellow cards, amber lines and warm accents are prohibited in this series.

## Release gates for the revised set

1. Each release-related factual claim must cite an official model/provider source captured in the new evidence pack.
2. Each visual sequence must have a distinct scene order and no episode may reuse the previous episode’s exact preset progression.
3. Each MP4 must contain a Russian voice track, audible background music and scene-timed SFX.
4. The final audio master must be intelligible on a phone speaker; no background bed may be exported at the prior approximately -42 dBFS average level.
5. All entrance text must settle before the reading dwell begins. The release visual QA must reject flicker/jitter and gold/yellow dominant elements.
6. Every video ends with the existing green `@llm_hubs` CTA and supplied avatar.

## Final render QA — 2026-08-14

Техническая проверка подтвердила, что все пять обновлённых MP4 имеют H.264 video, стерео AAC audio и портретный формат 720×1280. У пятого ролика первоначально обнаружен 2-секундный красный fallback: Zod отклонил недопустимый `DonutFill.centerContent="LIST PRICE"`. Значение исправлено на enum `label`, spec пересобран, и повторный render выдал штатный ролик 35.52 s / 720×1280 с audio track.

Две визуальные проверки (fallback diagnostic и mid-roll contact sheet) зафиксировали следующее: красный fallback отсутствует после исправления; золотые/янтарные карточки отсутствуют; сцены внутри серии различаются (DecisionGrid, StepList, BeforeAfter, MetricTrend, CompareSplit); общая база — near-black, cyan и configurable neon green. Следующий QA-проход проверяет CTA contact sheet и фактическую включённость музыкально-речевых master tracks.

CTA contact sheet проверен на финальных секундах всех пяти MP4. Во всех эпизодах присутствуют supplied circular LLM Hubs avatar, readable `@llm_hubs`, white CTA copy, near-black backdrop и neon-green button/glow. Золотые/янтарные элементы в CTA не обнаружены.

Audio master QA: все пять WAV имеют mean level от -21.6 до -19.2 dBFS и max peak от -1.3 до -0.7 dBFS; это заменяет ранее зафиксированный подуровневый примерно -42 dBFS фон. Каждый master содержит русский voice-over, один sliced original instrumental music bed с ducking примерно -7 dB под речью и 6–7 scene-timed procedural SFX.

## v2.2 scene audit

Полный contact sheet всех 25 кодированных сцен проверен вместе с full-resolution кадром `TgChat`. Исправления Telegram прошли визуальную проверку: появился нижний composer с placeholder/typed copy и send action, thread имеет корректные bubbles, а brain sticker появляется отдельной реакцией без фальшивого text bubble. Цена V4 Pro теперь выводится как крупное число и отдельная unit-строка, без прежнего наложения `$0.87 / 1M output`.

Аудит также подтвердил, что TimelineReveal больше не получает критически длинные English labels в narrow column: события сокращены до читаемых Russian-first labels. Hooks стали глубокими dark-glass signal cards с ясным controversial-but-grounded тезисом и более сильной first-frame hierarchy. Перед передачей требуется ещё одна точечная правка: `CompareSplit` по-прежнему использует legacy red accent для левой колонки, который не относится к выбранной LLM Hubs style family и нарушает единый visual language.

После точечного rerender `05_august_model_costmap` финальный contact sheet обновлён. `CompareSplit` больше не использует legacy red: левая колонка наследует restrained cyan, правая — выбранный neon accent, а VS badge использует active accent. В contact sheet сохранены имена preset и timestamp каждой из 26 сцен. Материал пригоден для следующей user-review итерации: можно называть карточку в формате `V.S Preset` (например, `2.2 TgChat` или `5.4 CompareSplit`).

## Focused scene fix pass — first QA pair

`2.1 AiChatStream` прошёл визуальную проверку: отдельная DeepSeek `DS` avatar, provider-blue header, ответ без character-stream reflow, reasoning chips и нижний composer читаемы и выдержаны в едином chat-card языке.

`1.3 DecisionGrid` больше не использует scale transform, поэтому вход не дёргает текст. Однако контрольный кадр показал, что даже сокращённый title нижней карточки занимает три строки. В следующем микропассе copy будет уменьшен до короткого title и одной короткой description, чтобы нижняя карточка читалась мгновенно.

Вторая focused QA pair прошла. `3.1 HeroKinetic` переносит `ТАРИФ` и `МЕНЯЕТСЯ` только между словами; ни title, ни subtitle не разрывают слово посередине. `4.2 TimelineReveal` подтверждает corrected geometry: все три dot center находятся на одной axis line, а connector стартует от правого края точки. Финальная ожидаемая операция в этом pass — rerender `01_gemini37_flash_vs_sonnet5` с укороченной copy `СВОЙ ТЕСТ / Проверьте workload` и обновление соответствующего control frame.

### Focused pass completion

`1.3 DecisionGrid` получил final microcopy `СВОЙ ТЕСТ / Проверьте workload`; control frame подтверждает одну строку title и одну строку description. `2.1 AiChatStream` заменён на provider-branded DeepSeek V4 Pro workspace с `DS` avatar, reasoning chips и composer. `3.1 HeroKinetic` использует non-breaking word wrap. `4.2 TimelineReveal` исправлен через axis-centered dot geometry. Четыре затронутых MP4 прошли технический QA: H.264 720×1280, AAC stereo 48 kHz, корректные 27.46–30.44 s runtimes.

### Hero clipping hotfix

`03_01_HeroKinetic_noclip_final.png` подтверждает root-cause fix: размер `ТАРИФ МЕНЯЕТСЯ` теперь лимитирован реальной внутренней шириной glass-card и самым длинным неразрывным словом. Полное слово `МЕНЯЕТСЯ` видно целиком; title не переносится внутри слова и не обрезается по правой границе.
