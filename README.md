# Motion Studio Framework

**Modular AI video generation** — text in, vertical video (1080×1920, 60fps) out.

38 presets · 96 effects · 18 transitions · 14 style kits · Qwen3-TTS voice cloning · Whisper transcription · Remotion rendering · LangGraph pipeline · FastAPI control panel

---

## What It Does

Give MSF a topic and it produces a short vertical video — the kind you see on AI/tech Telegram channels. The pipeline:

1. **LLM** splits the topic into N scene scripts
2. **Qwen3-TTS** clones a reference voice and synthesizes per-scene narration (ICL)
3. **Soundtrack** generates a music bed + SFX, ducked under the voice
4. **Remotion** renders each scene (React components) to MP4
5. **Audio mastering** mixes everything to -16 LUFS
6. **QA** validates the output exists, has audio, and meets duration

An optional **Deep Research** node (local-deep-research) gathers facts before scripting — fail-closed, so no video ships with invented facts.

## Quick Start

```bash
# Prerequisites: Python 3.10+, Node 18+, ffmpeg, CUDA (optional, for TTS/Whisper)

# 1. Install Python deps
pip install -r requirements.txt

# 2. Install Remotion deps
cd remotion && npm install && cd ..

# 3. Start the control panel (http://127.0.0.1:8765)
python -m msf.panel.server

# 4. Or run a pipeline job from CLI
python -m msf.cli "Сравнение локальных и облачных LLM" --preset HeroKinetic --scenes 4
```

## Control Panel

The panel at `http://127.0.0.1:8765` lets you:

- **Preview** any of 38 presets as a still (PNG, ~7s) or clip (MP4, ~4s)
- **Manage voices**: measure, prepare (denoise + normalize), transcribe (Whisper), register
- **Run pipeline jobs** and watch their log live
- **Check status**: registry, voices, node, ffmpeg, LDR — all probed, none assumed

No build step for the UI — it's vanilla HTML/JS/CSS served by FastAPI.

## Architecture

```
Operator ─→ Control Panel (:8765)
                │
        ┌───────┴───────┐
        ▼               ▼
   LangGraph          Render Server (:8766)
   Pipeline          (resident node process)
   (Python)               │
        │           Remotion (React/TS)
        ▼           38 presets
   Qwen3-TTS         96 effects
   Whisper           18 transitions
   ffmpeg            14 style kits
```

**Source of truth:** TypeScript files in `remotion/src/` (presets, effects, transitions, style kits). Python parser (`msf/registry.py`) reads them for 100% parity — no duplicate registries.

## Key Files

| File | Purpose |
|---|---|
| `PRD.md` | Product requirements, full architecture, API reference |
| `TODO.md` | Completed work + roadmap (P1/P2/P3) |
| `AGENT.md` | AI agent onboarding guide — invariants, rules, what NOT to do |
| `msf/graph/video_graph.py` | LangGraph pipeline (11 nodes) |
| `msf/panel/server.py` | FastAPI control panel |
| `msf/panel/render_client.py` | HTTP client → resident render server |
| `msf/audio/voice_prep.py` | Whisper + ffmpeg voice preparation |
| `msf/audio/soundtrack.py` | Music bed + SFX generator |
| `msf/registry.py` | TS → Python parser (presets, effects, transitions, kits) |
| `msf/spec.py` | VideoSpec validator + readability constants |
| `remotion/src/presets/` | 38 scene compositions (React) |
| `remotion/lib/transitions.ts` | 18 Zod scene transitions |
| `remotion/lib/pacing.ts` | Dwell pacing calculator |
| `config/default.yml` | Runtime config (LLM, TTS, render, audio) |

## Readability Contract

Every scene is guaranteed readable:

- **Safe area:** 160px top, 380px bottom — content outside fails validation
- **Dwell time:** `≥ max(1.0s, text_length / 12 chars-per-sec)`
- **Pacing module:** presets compute `settleBy()` then derive animations backward
- **60fps:** frame-count constants calibrated for 60fps — do not change

## Testing

```bash
python -m pytest tests/ -q
# 165 passed, 1 skipped, 0 failed
```

14 test files covering: registry parity (Python ↔ TypeScript), pacing constants, row shapes, panel API, soundtrack, deep research, model icons, theme parity, and end-to-end spec validation.

## License

MIT
