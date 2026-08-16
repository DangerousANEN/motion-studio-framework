# MSF Studio Element Builder

## Назначение

**Element Builder** — отдельный операторский workspace для расширения Studio. Он заменяет узкий `Scene Builder` и объединяет авторинг сцен, переходов, оверлеев, style families, аудио и голосов. В отличие от свободного выполнения кода, Builder работает по схеме **brief → безопасный preview → явный scaffold или регистрация → verification**.

> Браузер никогда не исполняет пользовательский TypeScript. Он может отрендерить только детерминированный design shell или контракт существующего renderer.

| Builder-тип | Что создаётся | Preview до регистрации | Статус после явного действия |
|---|---|---|---|
| Scene | TypeScript preset scaffold, VideoSpec fields и style affinities | Static design shell и motion clip на базовом preset | Регистрируется в generated scene pack, затем требует TypeScript/registry verification |
| Transition | Контракт transition recipe с безопасным базовым движением | Two-scene MP4 с timeline вокруг transition window | Создаётся как draft recipe; production shader/enum подключается только после code review и verify |
| Overlay | Декларативный overlay recipe поверх базовой сцены | Static frame и clip с `notification`, `cursor`, `focus`, `badge`, `timer` или `money` | Профиль регистрируется в Studio и должен соответствовать OverlaySpec |
| Style | Token-safe style draft, основанный на существующей family | Canonical scene preview на выбранном base style и safe tokens | Сохраняется как draft; runtime style application допускает только безопасные tokens |
| Music / SFX | Project audio asset с ролью `music_bed` или `sound_effect` | Audition-файл после preprocessing | Сохраняется в resource inventory и участвует в mastering/ducking |
| Voice | Voice reference workflow | Reference audition и TTS test phrase | Добавляется только после quality check, подготовки и вычитки текста |

## Навигация

Element Builder находится отдельной вкладкой в левом меню непосредственно перед **Настройками**. Прежняя верхнеуровневая вкладка «Голоса» становится обратной совместимой ссылкой на `#builder?tab=voices`; сам Voice Lab отображается как одна из вкладок Builder.

| Вкладка | Операторское действие | Ограничение безопасности |
|---|---|---|
| Сцены | Определить preset name, category, required fields, media slots и compatible styles | Только PascalCase names, фиксированный category whitelist и identifier-only fields |
| Переходы | Подобрать recipe и сразу увидеть motion window на общей паре сцен | Preview использует production transition contract; произвольный GLSL/TS не выполняется |
| Оверлеи | Собрать Telegram notification, CTA, cursor, focus, timer или money overlay | Допускаются только известные `OverlaySpec` types и bounded coordinates/timing |
| Стили | Создать токен-safe style draft от base family | Запрещены CSS/scripts; validation покрывает цвета, motion и читабельность текста |
| Audio | Перетащить music/SFX, получить audition и mastering report | PCM normalization, loudness/peak gate, compression и voice ducking обязательны |
| Голоса | Добавить reference, подготовить, транскрибировать и зарегистрировать | Нужны реальный файл, проверка качества и операторская вычитка текста |

## Две ступени preview

Каждый визуальный builder использует два разных, честно подписанных уровня preview.

1. **Design preview** показывает композицию, типографику, safe area, style tokens и media placeholders до создания исходника.
2. **Motion preview** рендерит короткий MP4 исключительно из известного валидного runtime contract. Для Scenes это safe motion shell, для Transitions — two-scene window, для Overlays — OverlayStack над базовой сценой.

Создание scaffold не является публикацией: оно формирует файл и verification plan. Новый код становится production-доступным только после обычных `tsc`, registry probe и render verification.

## Медиа и аудио

Media slot в Scene Inspector ведёт в Resources с уже выбранной типизированной ролью. Роли включают `hero_image`, `screen_recording`, `video_insert`, `telegram_round`, `channel_avatar`, `provider_avatar`, `speaker_avatar`, `supporting_image`, `music_bed` и `sound_effect`.

Пользовательские `music_bed` и `sound_effect` приводятся к WAV 48 kHz mono и проходят mastering policy: target `-18 LUFS`, true peak `-2 dBFS`, controlled compression `3:1`. Музыка ducked под голос, SFX остаются привязанными к scene actions.

## Acceptance criteria

- Style Inspector показывает полноразмерный canonical scene preview для каждой family, а не только palette tokens.
- Element Builder доступен отдельно в левом меню, Voice Lab перенесён в его вкладку.
- Оператор может получить static preview и playable video/timeline до регистрации Scene, Transition или Overlay recipe.
- Любой загружаемый audio file получает report о нормализации, compression и target loudness.
- Style и media affinities попадают в catalog filtering без leakage локальных filesystem paths.
- Builder не принимает и не исполняет произвольный код из браузера.
