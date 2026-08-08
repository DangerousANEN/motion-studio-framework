# Motion Studio Framework — PRD

Version: 1.0 | Status: Draft

## Vision
MSF — open-source production framework для автономного создания профессиональных вертикальных видеороликов с моушн-инфографикой. Framework моделирует работу production-команды через специализированных AI-агентов: продюсер, режиссер, исследователь, сценарист, арт-директор, моушн-дизайнер, аниматор, звукорежиссер, монтажер и QC.

## Problem
Текущие AI-видео инструменты строятся вокруг одной модели, что приводит к случайности результатов и невоспроизводимости. LLM придумывает анимации "из головы" вместо использования библиотек паттернов.

## Product Goal
Production framework для Shorts/Reels/TikTok уровня motion design студии. Композиция специализированных агентов, строгие контракты, библиотеки дизайнерских решений.

## Design Philosophy
1. LLM не создает видео — она принимает решения. Генерация — специализированными движками.
2. Производство разбивается на профессиональные роли. Каждый агент — только своя область.
3. Полная детерминированность через структурированные контракты.
4. Обязательное ревью каждого этапа (PASS/FAIL).
5. Сцена — минимальная производственная единица.

## Scope
- Вертикальные видео 30-90 секунд
- Motion-инфографика, динамическая типографика, русская озвучка, субтитры
- Категории: технологии, AI, программирование, финансы, бизнес, наука, образование

## Core Domain Model
- Project → Scene[] → Asset[] → Artifact[] → Review (PASS/FAIL)

## Production Pipeline
1. Project Brief → Research → Story Structure → Script
2. Script → Storyboard → Scene[] decomposition
3. Per Scene: Composition → Layout → Camera → Assets → Animation → Voice → Subtitles → Scene QC
4. Final: Composition → Audio Mix → Project QC → Export MP4

## Libraries (NOT generated — selected from):
- Motion Library: animation presets with IDs, params, constraints
- Layout Library: composition templates (grid, split, centered, etc.)
- Camera Presets: predefined movements (pan, zoom, orbit, parallax)
- Typography System: font rules, hierarchy, safe zones

## Technical Stack
- Python 3.12 + asyncio orchestration
- LLM via OpenAI-compatible API (any provider)
- TTS: Silero v4 / CosyVoice 3 / Qwen3-TTS
- Render: Playwright frame-by-frame screenshots + FFmpeg assembly
- Audio mastering: FFmpeg filters (highpass, compressor, EQ, LUFS normalization)
- faster-whisper for word-level subtitle timestamps

## Voice Philosophy
- Russian priority: Silero kseniya / CosyVoice cross-lingual cloning
- Post-processing: noise reduction, compression, EQ, -16 LUFS normalization

## Review System
- Every stage → PASS or FAIL
- FAIL → structured feedback → retry (max N attempts)
- Measurable criteria, not subjective

## Non-Functional Requirements
- Scene generation < 5 min with local models
- Horizontal scaling, distributed execution
- Any LLM/TTS/graphics provider swappable
- Reproducible results with same inputs
