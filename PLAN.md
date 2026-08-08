# MSF v2 — Migration to Remotion + Skill Presets (PLAN)

## Цель
Перевести Motion Studio Framework с Playwright-HTML → **Remotion (React)**, сделав систему так, чтобы:
- **«Тупой» агент** кидал ТОЛЬКО текст озвучки + 1 пресет → получал красивый вертикальный ролик (1080×1920, озвучка Qwen3 clone, субтитры, spring-анимации).
- **«Умный» агент** мог писать свои React-компоненты сцены (Three.js, GSAP, WebGL), но его валидация блокируется gate-логикой (skill `msf-gate`), пока не докажет квалификацию.
- Все генерации голоса — Qwen3 1.7B-Base zero-shot (файл ref_audio хранится как настройка проекта).

## Архитектура
```
MSF/
  remotion/                        # Remotion-проект (npm, TypeScript)
    package.json
    remotion.config.ts
    src/
      Root.tsx                     # registerRoot(RemotionRoot)
      VideoSpec.schema.ts          # zodSchema: scenes[], preset, voice, texts
      compositions/Main.tsx       # <Series> по scenes[] из JSON
      presets/                    # ТОЛЬКО готовые золотые пресеты (для dumb-агентов)
        HeroKinetic.tsx           # кинетическая типографика (spring, overshoot)
        StatCounter.tsx           # счётчик metriqов (useSpring на число)
        GridGridFloor.tsx         # 3D-сетка пола с неоном
        SwipePanels.tsx          # горизонтальные слайды карточек
        TypewriterSub.tsx        # субтитры кинетически выводятся
      parts/                     # фигуры, шумы, градиенты (переиспользуемо)
        Prism.tsx, NeonGrid.tsx, GridFloor.tsx, GlassCard.tsx
      audio/                     # TTS files injection via staticFile()
  msf/
    orchestrators/
      remotion_runner.py          # обёртка: текст → TTS → JSON → npx remotion render
      scene_builder.py            # текст авто-режется на сцены по паузам/словам
    skills_bridge/
      qwen3_tts.py                # zero-shot clone, нормализация, кэш модели
      preset_guard.py             # маппинг agent_level → allowed_presets
  skills/                          # Hermes skills (skills/ папка профиля)
    msf-dumb-animate/SKILL.md     # пресеты-only пайплайн (no-coding)
    msf-smart-animate/SKILL.md    # кастом React-пресеты + review-gate
    msf-gate/SKILL.md             # gate-логика: classifier agent_level
```

## Gate-механика (тупые vs умные)
1. При вызове `msf-dumb-animate` или `msf-smart-animate` сначала идёт классификатор через OmniRoute:
   * Промпт: «Оцени уровень агента: 1—5. Если ≤2 — DUMB (только пресеты)».
2. DUMB-агенты видят константу `ALLOWED_PRESETS=[HeroKinetic, StatCounter, GridGridFloor, SwipePanels, TypewriterSub]`. 
3. Попытка dumb-агента создать новый React-компонент блокируется (fail в Review). 
4. Smart-агенты получают доступ к `remotion/src/` и могут добавлять свой код — но изменения требуют двойного рендер-стейджа.

## База пресетов (со ссылками на мировые приёмы)
- **HeroKinetic** — spring overshoot, 3D-поворот текста (Remotion examples: github.com/remotion-dev/example-title-cards).
- **StatCounter** — цифра нарастает useSpring(0→value), градиентный glow (приём из Vercel Analytics).
- **GridGridFloor** — 3D-нцена Neo-Brutalism: пол 50%-прозрачный wireframe, кубы в Spring (inspiration: Neo-Brutalism Pop UI skill).
- **SwipePanels** — карточки входят слева/справа, blur+scale (деньги/файнтек short-стили).
- **TypewriterSub** — пословная кинетическая прокрутка субтитров (приём из MrBeast-стиля).

## Auto-Text-to-Video (одна строка вход)
```python
from msf.orchestrators.remotion_runner import create_video

video = create_video(
    text="Ищете лучшие оупен сорс решения в области ИИ? Канал .LLM Hubs — ваш источник...",
    preset="HeroKinetic",       # dumb-agent может выбрать пресет
    reference_audio="cache/audio/audio_3463d054d38f.mp3",  # ваш голос
    camera_slow_zoom=True,
)
# → scenes auto-split, TTS Qwen3 clone, merge аудио, Remotion рендер
```

## MCP-сервер (опционально)
* `msf-mcp` — stdio MCP server: tool `msf.create_video(text, preset)` возвращает path к MP4. Hermes Agent может вызывать как native tool.
* Fallback: простой Python CLI (без SDK усложнений).

## QA & Verification
1. `npm install` + `npx remotion render` scale-test (3-сек placeholder → 5 fps).
2. Vision-check: Hermes browser-vision берёт скриншот из Remotion Studio первого кадра.
3. Видеофайл собирается через ffmpeg из Remotions-рендера → AudioMaster → final mp4.

## Приоритеты для субагентов OMP
- **OMP-1:** scaffold `remotion/` проекта + 5 пресет-компонентов + schema.
- **OMP-2:** Python-оркестратор: auto-split сцене → TTS → JSON → npx remotion render.
- **OMP-3:** 3 Hermes скилла: msf-dumb-animate, msf-smart-animate, msf-gate.
