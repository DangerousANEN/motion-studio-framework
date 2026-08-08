# Product Requirements Document (PRD) — Motion Studio Framework (MSF) v2.0

## 1. Executive Summary & Vision
Motion Studio Framework (MSF v2.0) — это автономный Python-инструментарий нового поколения для генерации профессиональных 60 FPS 9:16 (1080x1920) видеороликов (Shorts/Reels/TikTok/Telegram) с использованием:
- **Frontend / Rendering Engine:** Remotion (React, TypeScript, CSS-in-JS, Spring animations).
- **Voiceover Engine:** Qwen3-TTS 1.7B-Base (Zero-Shot Voice Cloning в 1 клик по audio prompt) и CustomVoice.
- **Agent Governance & Safety:** Иерархическая система доступа для агентов (Dumb Agents vs Smart Agents) с авто-роутингом через `msf-gate`.
- **Orchestration Layer (LangGraph / LangChain Integration):** Государственная макро-автоматизация мультиагентного цепочечного пайплайна (Scriptwriter -> Storyboarder -> Remotion Spec Generator -> Voice Clone -> Render -> QA/Auditor).

---

## 2. Архитектура и Структура Системы

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Hermes Agent / User                           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                 msf-gate
                                     │
               ┌─────────────────────┴─────────────────────┐
               ▼                                           ▼
      [Level 1-2: Dumb Agent]                     [Level 3-5: Smart Agent]
    (Only presets allowed, no JS)               (Can author React Remotion specs)
               │                                           │
               └─────────────────────┬─────────────────────┘
                                     ▼
                      LangGraph Workflow Orchestrator
       ┌───────────────────────────────────────────────────────────┐
       │ Node 1: Text Script Normalizer (Phonetic RU translit)     │
       │ Node 2: Qwen3-TTS 1.7B Zero-Shot Engine (CUDA Singleton)  │
       │ Node 3: Remotion Scene Dispatcher & Public Spec Builder   │
       │ Node 4: Remotion CLI Headless Renderer (Chromium 60 FPS) │
       │ Node 5: Audio Mastering & Loudnorm (-16 LUFS)              │
       │ Node 6: Vision Auditor (Check frames for glitch/clip)    │
       └─────────────────────────────┬─────────────────────────────┘
                                     ▼
                            Final 1080x1920 MP4
```

---

## 3. Ответ на вопрос по LangGraph / LangChain

### Нужен ли LangGraph / LangChain для MSF?
**ДА, абcолютно!** LangGraph идеально подходит для MSF по следующим причинам:

1. **State Management (Управление состоянием пайплайна):**
   Генерация видео — это не монолитная функция, а графовый процесс с возможными циклами обратной связи:
   `Script` -> `Voice Synthesis` -> `Audio Duration Calculation` -> `Frame Allocation` -> `Remotion Render` -> `Frame Inspection (Vision QA)` -> `Retry/Adjust if visual bug`.
   LangGraph предоставляет цикличный граф состояний (StateGraph) с точным сохранением контрольных точек (checkpoints).

2. **Self-Correction & Human-in-the-Loop (Авто-коррекция и контрольные точки):**
   Если Vision-агент (через `vision_analyze`) видит, что текст вылез за пределы экрана или субтитры перекрывают логотип, LangGraph возвращает управление в узел `Scene Dispatcher` для изменения `font_size` или `preset` без повторного прогона долговременного синтеза речи Qwen3-TTS (благодаря кэшированию состояния в узлах графа).

3. **Разделение квалификации агентов:**
   LangGraph позволяет объявить отдельный сабграф для "Dumb" агентов (простая линейная цепочка с фиксированным набором узлов-пресетов) и расширяемый граф для "Smart" агентов (динамическая генерация JSX/TSX кода с верификатором кода AST-линтером перед рендерингом).

---

## 4. Набор Пресетов MSF Remotion (Built-in for Dumb Agents)

1. `HeroKinetic`: Агрессивная кинетическая типографика, вылетающие заголовки с пружинной физикой (`spring({ config: physics.wobbly })`), свечение неоновым градиентом `#0E0F11` / `#E6C475` / `#00FF88`.
2. `StatCounter`: Анимированный счетчик метрик (звезды GitHub, прирост подписчиков, скорости в миллисекундах) с плавным таймером и индикаторами прогресса.
3. `GridGridFloor`: Нео-бруталистический 3D сетчатый пол с плавающими Pop-Laboratory UI карточками.
4. `SwipePanels`: Горизонтальные свайпы карточек с эффектом параллакса.
5. `TypewriterSub`: Высокоскоростной постраничный вывод субтитров с подсвечиванием активного слова.

---

## 5. Дорожная Карта и TODO (План Реализации)

### Фаза 1: Оптимизация Remotion & Remotion CLI (ГОТОВО / ТЕСТИРУЕТСЯ)
- [x] Инициализация Remotion TypeScript проекта (`remotion/`).
- [x] Реализация 5 базовых React-компонентов пресетов.
- [x] Создание `msf/orchestrators/remotion_runner.py` для вызова `npx remotion render`.

### Фаза 2: Оптимизация Qwen3-TTS & Кэширование (ГОТОВО)
- [x] Исправление `msf/skills_bridge/qwen3_tts.py` (Zero-shot voice clone на 1.7B Base).
- [x] Автоматическая фонетическая транслитерация англицизмов на русский (ЛЛМ Хабс, Гитхаб).
- [x] Синглтон-кэширование модели Qwen3 в память GPU (CUDA 0).

### Фаза 3: Интеграция LangGraph Workflow Engine (В РАЗРАБОТКЕ)
- [ ] Установка `langgraph` и `langchain-core` в виртуальное окружение Hermes.
- [ ] Создание модуля `msf/graph/video_graph.py` с `StateGraph`:
  - `NodeScriptGen`
  - `NodeVoiceSynth`
  - `NodeRemotionSpec`
  - `NodeRender`
  - `NodeVisionQA`
- [ ] Добавление условных ребер (`conditional_edges`) для отката при ошибках рендеринга.

### Фаза 4: Полное обновление Hermes Skills & Руководства
- [x] Создание `msf-dumb-animate` в Hermes skills.
- [x] Создание `msf-smart-animate` в Hermes skills.
- [x] Создание `msf-gate` в Hermes skills.
- [ ] Публикация пакета скиллов в глобальный каталог `~/.hermes/skills/msf/`.
