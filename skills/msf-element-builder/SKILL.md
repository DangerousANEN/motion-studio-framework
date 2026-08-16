---
name: msf-element-builder
description: "Создание и расширение элементов MSF Studio через Element Builder. Использовать для добавления сцен, переходов, оверлеев, style drafts, music/SFX и голосов с preview, validation, scaffold/register и regression verification."
---

# MSF Element Builder

Используй этот skill, когда нужно создать новый reusable element для Motion Studio Framework или расширить существующий catalog. Работай через локальный Element Builder и его API, а не через произвольное выполнение пользовательского кода.

## Главный workflow

1. Определи категорию элемента: `scene`, `transition`, `overlay`, `style`, `music_bed`, `sound_effect` или `voice`.
2. Найди существующий близкий preset, contract и renderer. Повторно используй production pattern, если он покрывает задачу.
3. Сформируй brief: назначение, audience, duration, style family, required fields, media roles и acceptance risks.
4. Сначала сделай preview. Для визуального элемента проверь design preview и motion preview, если он доступен. Preview должен использовать валидный runtime contract.
5. Не регистрируй элемент, пока не проверены композиция, safe area, readability, motion, aspect ratio и отсутствие crop/overflow.
6. Для scaffold или registration выполняй только явное действие оператора. Browser никогда не исполняет присланный TypeScript.
7. Выполни verification: `npx tsc --noEmit`, targeted pytest, registry/catalog probe и render preview.
8. Добавь human guide к созданному элементу: назначение, обязательные поля, подключение, ограничения и проверка.
9. Сохрани demo preview/screenshot и сообщи статус: `previewed`, `scaffolded`, `registered` или `production-verified`.

## Разрешённые workflows

| Категория | Действия | Правило |
|---|---|---|
| Scene | design preview, motion preview, TypeScript scaffold | PascalCase name; identifier-only fields; typed media slots; scaffold не равен production registration. |
| Transition | preview, scaffold, recipe register | Preview — two-scene production window; generated TS требует review и registry wiring. |
| Overlay | still preview, motion preview, recipe register | Только `notification`, `cursor`, `focus`, `badge`, `timer`, `money`; coordinates/timing bounded. |
| Style | canonical scene preview, draft register | Только token-safe overrides от существующей family; draft не разрешён в production run. |
| Music/SFX | upload, normalize, audition | Music bed и SFX имеют разные roles; сохраняй mastering report. |
| Voice | quality check, prepare, transcribe, edit, register | Нужны quality check и ручная вычитка transcript. |

## Overlay guardrails

Overlay — самостоятельная категория элементов, а не скрытое поле сцены. Overlay располагается поверх scene content в `scene.overlays[]` и использует `OverlaySpec`. Не добавляй новые runtime types без изменения schema, renderer, registry, preview и tests.

Разрешённые типы:

- `notification`: toast/banner; указывай app, title, text и placement.
- `cursor`: cursor path или target coordinates; нормализуй координаты в `0..1`.
- `focus`: ring/spotlight вокруг target; не выходи за safe area.
- `badge`: короткий label или proof pill; ограничивай текст одной-двумя строками.
- `timer`: bounded countdown/count-up; задавай unit и duration.
- `money`: monetary/value toast; не выдумывай данные и не форматируй значение неоднозначно.

Для нового overlay сначала добавь contract/schema и renderer support, затем static preview, motion preview, API validation, catalog entry и regression test. Никогда не регистрируй произвольный HTML/CSS/JS как overlay.

## Category-specific quality gates

### Scene

Используй responsive safe area и полный кадр без необоснованного crop. Не разбивай слова; сокращай copy или используй bounded typography. Для media input создавай typed replaceable slot и placeholder. Укажи совместимые styles. Preview должен показывать смысл сцены без пользовательских media assets.

### Transition

Показывай две базовые сцены до и после transition. Проверяй centred transition window, integer dimensions и playable MP4. Scaffold помещай в generated directory, но production enum/registry меняй только после code review.

### Overlay

Проверяй readable contrast, z-order, safe-area bounds, deterministic timing и отсутствие collision с subtitles/CTA. Для cursor/focus используй normalized coordinates. Для notification/badge ограничивай copy.

### Style

Стиль — это system of tokens и motion preferences, а не только палитра. Создавай draft от существующей base family, делай canonical scene preview и не разрешай arbitrary CSS/scripts. Отмечай draft в catalog и блокируй его для production run.

### Music/SFX

Выбирай роль до загрузки. Применяй normalization contract проекта: WAV 48 kHz mono, target `-18 LUFS`, peak `-2 dBFS`, compression `3:1`. Для music bed учитывай ducking под voice; для SFX — controlled placement по scene action. Всегда сохраняй audition/report.

### Voice

Сначала качество файла и подготовка копии, затем denoise/trim/normalize, затем transcription. Transcript необходимо проверить вручную; только после этого регистрируй voice key, language и notes.

## Anti-patterns

Не регистрируй preview-only draft как production. Не добавляй необработанный пользовательский TS в registry. Не используй filesystem paths в catalog payload. Не создавай style family без scene preview. Не называй overlay «готовым», если у него есть только still preview и нет motion/contract verification. Не подменяй реальный audio/voice asset текстовой заглушкой без явной маркировки demo.

## Отчёт агенту

В конце возвращай таблицу с колонками `category`, `name`, `preview`, `artifact`, `status`, `verification`, `next step`. Для каждого production-неподключённого результата указывай конкретную причину: `draft`, `scaffold awaiting review`, `audio awaiting file`, `voice awaiting transcript` или другую блокировку.

## Universal 3D Graph

Используй `Universal3DGraph` для новой сцены, когда готовые 3D presets не покрывают spatial composition. Сильный агент может собирать произвольный graph из разрешённых node types: `box`, `sphere`, `torus`, `cylinder`, `cone`, `plane`, `octahedron`, `icosahedron`, `line`, `asset` и `group`. Каждый node обязан иметь уникальный identifier; `group` может содержать nested `children`, а `asset` обязан ссылаться на разрешённый GLB/glTF resource.

Рабочий порядок: сформируй graph с `version: 1`, camera, lights, optional grid и nodes; отправь его на `/api/studio/element-builder/3d/preview`; затем проверь motion через `/api/studio/element-builder/3d/motion`; только после этого используй `/api/studio/element-builder/3d/register`. Renderer исполняет только declarative graph; пользовательский TypeScript/JavaScript через Builder не запускается.

Соблюдай limits: максимум 128 nodes и глубина групп до 8. Используй Vec3 для position/rotation/scale. Для анимации применяй `from`, `to`, `start`, `end`, `ease` и bounded `loop`. Не создавай live network fetch внутри scene. Для GLB/glTF проверь размер, лицензию, attribution, отсутствующие текстуры, bounding box и fallback preview.

Capability policy: слабый агент выбирает существующий template и изменяет safe values; curated agent может менять node topology только внутри разрешённых primitives; сильный агент проектирует полный graph, но обязан пройти still preview, motion preview, safe-area/readability check и representative render. Registered recipe не считается production-approved до TypeScript check, catalog/registry verification и code review.

Для 3D QA проверяй кадры в начале, середине и конце motion, visibility каждой spatial layer, clipping, camera framing, lighting, contrast, render duration и MP4 playback. Если graph не требует уникальной композиции, предпочитай готовый production preset.

## Image textures in 3D graphs

Добавляй отдельное изображение сначала через Project Resources с image-compatible role. В graph используй `resourceId`, а не filesystem path и не произвольный URL. Допустимые target nodes: `plane`, `box`, `sphere`, `cylinder`, `cone`, `torus`, `octahedron` и `icosahedron`; назначай `doubleSided: true` для карточек/экранов, которым нужна видимость с обеих сторон.

Перед preview проверь, что resource существует в том же `project_id`, его kind равен `image`, а роли и caption понятны оператору. Studio API резолвит resourceId в локальный validated media URI и только затем передаёт textureUrl в Remotion. Не отправляй `textureUrl` наружу напрямую, не используй audio/document assets и не передавай filesystem paths.

Сделай still preview и motion preview. В QA проверь цветовое пространство изображения, framing/crop, aspect ratio plane, visibility в начале/середине/конце движения, safe area, readable overlays поверх texture и отсутствие renderer network/CORS errors. Video textures не считай поддержанными: для видео используй screen/video scene до появления отдельного deterministic frame-sampling contract.
