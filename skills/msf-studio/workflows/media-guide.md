# Media inserts and screen guides

Использовать для реальных screenshot, screen recording, изображения, видео-вставки, Telegram voice/round и long-form video card. Работать в `preset` tier, если используются stable сцены и разрешённые assets; переходить в `sandbox` только для нового renderer-кода.

## 1. Проверить asset

1. Получить локальный path или URL и подтвердить право на использование. Не использовать private screen captures, лицевые/голосовые данные или сообщения без разрешения.
2. Удалить credentials, API keys, личные данные и всплывающие private notifications до рендера.
3. Для записи экрана предпочесть 16:9 или 4:3 исходник; не растягивать его до вертикального кадра.
4. Передать path относительно `remotion/public/` либо URL. Не передавать `file://`, shell command или CSS/JS в props.

## 2. Выбрать stable preset

| Цель | Preset | Обязательные props | Допустимый motion |
|---|---|---|---|
| Гайд по интерфейсу | `ScreenGuide` | `src` или `images[0]`, `title` | `focusX`, `focusY`, `focusScale`, до 5 `cursorSteps` |
| Сырая запись экрана | `ScreenRecord` | `src` или `images[0]` | `chrome`, `urlBar`, `showRec` |
| Видео/YouTube-вставка | `YouTubeCard` | `src` или `images[0]`, `title` | `startFrom`, `showControls` |
| Иллюстрация/скриншот | `ImageSpotlight` | `src` или `images[0]`, `title` | `fit`, `kenBurns` |
| Telegram voice / circle | `TelegramVoiceRound` | `contactName`, `duration` | `avatar`, `transcript`, `waveformSeed` |
| Общий контент | `ImageShowcase` / `VideoEmbed` | asset + caption | только один мягкий reveal |

## 3. Построить guide path

Для `ScreenGuide` задавать координаты в нормализованном диапазоне `0..1`. Использовать 1–3 шага; каждый шаг имеет `x`, `y`, `at` и короткий `label`. Добавлять `focus` overlay вокруг важного control и `cursor` overlay только в момент клика. Не использовать camera shake, chromatic effect или typewriter на плотном UI-тексте.

```json
{
  "preset": "ScreenGuide",
  "src": "media/my-demo.mp4",
  "title": "Включите Batch",
  "focusX": 0.68,
  "focusY": 0.56,
  "focusScale": 1.28,
  "cursorSteps": [
    {"x": 0.51, "y": 0.42, "at": 0.18, "label": "Откройте Settings"},
    {"x": 0.68, "y": 0.56, "at": 0.56, "label": "Выберите Batch"}
  ],
  "overlays": [
    {"type": "focus", "x": 0.68, "y": 0.56, "w": 0.28, "h": 0.10, "at": 0.50, "hold": 2.2, "targetLabel": "Batch"}
  ]
}
```

## 4. Применить visual family

Получить style family через Studio API/MCP. Использовать `product_tutorial` для guides, `social_native` для Telegram, `creator_glass` для media insert, `terminal` для CLI/API demo. Передавать только `styleConfig` tokens: `palette.neon`, `palette.bg`, `palette.surface`, `backdrop`, `surface`, `effects` и `motion`. Для текстовых/фактологических сцен держать `effects.chromatic=0` и `motion.damping>=18`.

## 5. Проверить и выпустить

1. Выполнить schema/storyboard validation.
2. Рендерить preview в начале, середине и на cursor/focus step.
3. Проверить, что source не обрезает action, text читабелен, cursor не закрывает control и source audio не конфликтует с root mix.
4. Добавить music/SFX по semantic role, а не поверх речи. Для silent screen recording установить `muted=true`.
5. Сохранять asset reference, license/consent и preview в draft artifact. Stable release требует обычного review.
