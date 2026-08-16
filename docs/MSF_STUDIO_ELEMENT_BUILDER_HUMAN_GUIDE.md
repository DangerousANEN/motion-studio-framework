# Element Builder: руководство оператора

## Зачем нужен Builder

**Element Builder** — безопасное рабочее пространство MSF Studio для расширения каталога без ручного редактирования production registry на первом шаге. Для каждого элемента действует одинаковая последовательность: описание задачи, preview, проверка, явное создание scaffold или draft, затем отдельное production-подключение.

> Preview показывает, что элемент выглядит и ведёт себя ожидаемо. Preview не означает, что новый код уже разрешён в production.

## Где находится

Откройте `Studio → Element Builder`. Внутри доступны вкладки **Сцена**, **Переход**, **Оверлей**, **Стиль**, **Музыка и SFX** и **Голоса**. Каталог готовых элементов находится в `Studio → Элементы`; там отдельно доступны сцены, переходы, музыка, SFX, оверлеи и стили.

## Общая схема работы

| Шаг | Действие оператора | Результат |
|---|---|---|
| 1 | Выберите категорию и заполните brief | Builder понимает назначение элемента |
| 2 | Нажмите preview | Видите design shell или runtime preview до регистрации |
| 3 | Проверьте safe area, текст, размер, motion и media slots | Отбрасываете неудобный или сломанный вариант |
| 4 | Нажмите scaffold/register только после проверки | Создаётся draft, recipe или файл scaffold |
| 5 | Выполните verification | Элемент можно передавать на code review или production wiring |

## Сцены

Во вкладке **Сцена** укажите PascalCase имя, категорию, краткое назначение, поля VideoSpec и совместимые style families. Поля должны быть короткими идентификаторами, например `title, subtitle, mediaUrl`. Если сцене нужен файл, используйте typed replaceable slot: `hero_image`, `screen_recording`, `video_insert`, `telegram_round`, `provider_avatar` или другую роль из Resources.

Сначала нажмите **Показать design preview**. Проверьте, что главный смысл читается без пользовательской картинки и что весь portrait frame помещается без crop. Затем нажмите **Рендер движения** и проверьте, что текст не дёргается, слова не обрезаются, а controls не наезжают друг на друга. Только после этого можно нажимать **Создать TypeScript scaffold**.

Scaffold нужно открыть в IDE, заполнить body, добавить registry manifest, выполнить TypeScript verification и сделать production render. Сам scaffold ещё не является готовой production-сценой.

## Переходы

Во вкладке **Переход** выберите базовый transition и стиль, задайте имя и краткое описание. Builder покажет две базовые сцены и центрированное transition window. Проверьте, что начало и конец обеих сцен видимы, dimensions integer-compatible, а MP4 воспроизводится с timeline.

После preview можно создать TypeScript recipe scaffold. Recipe хранится отдельно от production enum. Для подключения в production разработчик должен реализовать или проверить код, добавить registry wiring, прогнать `npx tsc --noEmit`, parity tests и render verification.

## Оверлеи

**Оверлеи — отдельная категория элементов.** Они не являются самостоятельной сценой: overlay накладывается поверх scene content через `scene.overlays[]` и должен соответствовать `OverlaySpec`.

В текущем Builder разрешены шесть безопасных типов.

| Тип | Назначение | Что настроить |
|---|---|---|
| `notification` | Telegram/app toast или системное уведомление | app, title, text, placement |
| `cursor` | Показать, куда нажать | normalized target или cursor path |
| `focus` | Подсветить область интерфейса | normalized target, radius, timing |
| `badge` | Proof pill, label или короткий CTA | badge text, placement, duration |
| `timer` | Countdown/count-up | value, unit, duration |
| `money` | Числовой value toast | value, currency/label, placement |

Создание выполняется так: выберите тип, задайте короткий label, стиль и target parameters, нажмите **Показать still preview**, затем **Рендер движения**. Проверьте z-order, contrast, safe-area bounds и отсутствие пересечения с субтитрами или CTA. После этого можно зарегистрировать recipe.

Не вставляйте произвольный HTML, CSS или JavaScript. Если нужен новый overlay type, сначала требуется расширить schema, renderer, catalog, preview endpoint и tests. Только после этого новый тип можно показывать в Builder.

## Стили

Стиль создаётся как **draft от существующей base family**, а не как произвольная CSS-тема. Выберите base style, задайте label, summary и безопасные token overrides: palette, surface, text contrast и motion preference. Нажмите preview и убедитесь, что style действительно виден на canonical scene, а не только в списке цветов.

Draft помечается в каталоге как `DRAFT` и не выбирается для production run. Для production нужно вручную проверить readability, contrast, motion duration и compatibility со сценами, затем перенести validated tokens в production style registry.

## Музыка и SFX

Во вкладке **Музыка и SFX** перетащите файл или выберите его через file picker. Сначала выберите роль: **Музыка на фон** или **Звуковой эффект**. Добавьте контекст, чтобы агент и оператор понимали назначение.

После обработки Studio приводит материал к WAV 48 kHz mono, target `-18 LUFS`, peak `-2 dBFS` и compression `3:1`. Для music bed дополнительно применяется ducking под voice; SFX получают controlled placement. Прослушайте audition и проверьте mastering report. Не подменяйте реальный пользовательский файл demo-заглушкой без явной маркировки.

## Голоса

Во вкладке **Голоса** перетащите reference-файл, проверьте качество, при необходимости подготовьте копию с denoise, trim и normalization, затем запустите speech recognition. Текст нужно вычитать вручную: автоматическая транскрипция не регистрируется без подтверждения.

После вычитки укажите voice key, язык и заметку, затем нажмите **Добавить в каталог голосов**. Перед использованием выполните test phrase и убедитесь, что voice подходит по языку, темпу и эмоциональной подаче.

## Что означает статус элемента

| Статус | Значение |
|---|---|
| `previewed` | Design или motion preview сделан, регистрации нет |
| `draft` | Сохранён preview-only draft, например style draft |
| `scaffolded` | Создан исходный файл для дальнейшей реализации |
| `registered` | Recipe или asset добавлен в Studio catalog |
| `production-verified` | Registry, TypeScript, runtime render и tests пройдены |

## Частые ошибки

Если сцена обрезается справа, уменьшите copy, включите safe-area layout и проверьте integer dimensions. Если слово разбивается, измените copy или примените bounded typography; не маскируйте проблему уменьшением всего текста до нечитаемого размера. Если overlay закрывает CTA, измените placement или timing. Если style виден только в palette tokens, preview считается недостаточным: нужен canonical scene preview. Если voice звучит рассинхронно, сначала проверьте duration/phrasing и только потом меняйте сцену.

## Передача в production

Перед production wiring сохраните preview, краткое описание и verification result. Для TypeScript-scaffold элементов отдельно укажите, что code review ещё не пройден. Production-готовым считается только элемент, который имеет валидный contract, renderer/registry integration, проверенный preview, тесты и воспроизводимый render.
