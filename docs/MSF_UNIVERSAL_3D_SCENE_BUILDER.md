# Universal 3D Scene Builder

## Назначение

`Universal3DGraph` — это декларативный 3D scene graph для MSF. Он позволяет агенту собирать новую сцену из объектов в общем 3D-пространстве: primitive geometry, nested groups, локальные GLB/glTF assets, камеры, lights, grid и timeline motion. Агент описывает **что находится в сцене и как оно движется**, но не отправляет в браузер исполняемый TypeScript или JavaScript.

## Capability tiers

| Tier | Возможности | Ограничения |
|---|---|---|
| Preset agent | Выбирает готовый JSON template и меняет safe values | Не меняет node topology без проверки |
| Curated agent | Создаёт graph из разрешённых primitives, groups, camera и lights | Максимум 128 nodes, глубина groups до 8, только валидированные types |
| Strong agent | Проектирует произвольную declarative композицию, включая несколько spatial layers, asset nodes и motion channels | Не исполняет код через Builder; результат обязан пройти validation, preview и render QA |
| Production-approved | Использует зарегистрированный recipe в VideoSpec | Нужны review, asset license/attribution, safe-area и representative render checks |

## Разрешённые node types

`box`, `sphere`, `torus`, `cylinder`, `cone`, `plane`, `octahedron`, `icosahedron`, `line`, `asset` и `group`. Каждый node имеет уникальный `id`. `group` содержит `children`; `asset` требует `assetUrl`.

## Минимальный graph

```json
{
  "version": 1,
  "background": "#0b1020",
  "camera": {"preset": "orbit", "fov": 42},
  "lights": [
    {"type": "ambient", "intensity": 0.5},
    {"type": "directional", "position": [4, 6, 5], "intensity": 1.4, "color": "#ffffff"}
  ],
  "nodes": [
    {"id": "core", "type": "icosahedron", "position": [0, 0, 0], "color": "#52ff9a"},
    {"id": "ring", "type": "torus", "rotation": [1.1, 0, 0], "color": "#ffffff", "wireframe": true}
  ]
}
```

## Motion

Motion задаётся декларативно через `from`, `to`, `start`, `end`, `ease` и optional `loop`. Positions, rotations and scales используют единый Vec3 contract. Для спокойных сцен выбирайте `easeInOut`; `repeat` и `pingpong` применяйте только к объектам, которые действительно должны жить весь кадр.

## Workflow в Studio

Откройте **Element Builder → Сцена**, выберите категорию `3D`, задайте имя и назначение сцены, вставьте graph JSON и нажмите **3D still preview**. После проверки композиции нажмите **3D motion preview**. Только после проверки обоих preview используйте **Зарегистрировать graph recipe**. Recipe сохраняется отдельно от production preset; его можно подключать к VideoSpec после code review и render verification.

## Production checklist

Проверьте уникальность node IDs, отсутствие объектов за safe area, достаточное освещение, читаемость 3D текста/подписей в overlay, размер GLB/glTF, наличие лицензии и attribution, отсутствие внешнего live fetch, стабильность motion на начале/середине/конце ролика и отсутствие чрезмерного WebGL render cost. Для пользовательского агента следует предпочитать существующий preset, если новая сцена не требует уникальной spatial composition.

## Отдельные изображения и текстуры

Изображение добавляется сначала в **Resources** с одной из image-compatible ролей, например `supporting_image`, `hero_image`, `channel_avatar`, `provider_avatar` или `screen_recording`. В Element Builder выберите этот файл в поле **Изображение/текстура из Resources** и нажмите **Применить к 3D node**. Builder добавит в graph typed `resourceId`; прямые filesystem paths запрещены.

Resource можно назначить primitive node типа `plane`, `box`, `sphere`, `cylinder`, `cone`, `torus`, `octahedron` или `icosahedron`. Для still и motion preview Studio разрешает только зарегистрированный ProjectMedia image resource и сам резолвит его в локальный same-origin URL, доступный Remotion renderer. Неразрешённые paths, audio resources и отсутствующие assets блокируются до рендера.

Встроенные материалы GLB/glTF продолжают работать через `asset` node. Для видеофайлов как animated texture пока используется обычный `video_insert`/screen scene; video texture в Universal3DGraph намеренно не включён до отдельной deterministic frame-sampling реализации.
