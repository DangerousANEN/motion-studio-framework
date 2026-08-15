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

## Studio v2: Safe Agent, MCP and Evidence-First Workflow

Studio v2 is the application boundary for both human operators and agent clients. It provides typed, versioned contracts for research packs, script plans, storyboards, assets, runs, events and redacted traces. A restricted agent should discover presets through the catalog, compose only stable manifests, validate the storyboard, and only then prepare a run. It must not guess scene names, construct arbitrary renderer code, or present an unsupported factual claim as verified.

```bash
# Check the Studio contracts, catalog, research gates, audio recipes and MCP import.
PYTHONPATH=. python tools/check_studio_v2.py
PYTHONPATH=. python tools/check_studio_research.py
PYTHONPATH=. python tools/check_studio_observability.py
PYTHONPATH=. python tools/check_studio_audio.py
PYTHONPATH=. python tools/check_studio_mcp.py

# Run the local agent adapter through stdio after installation.
PYTHONPATH=. python -m msf.studio.mcp_server
```

The MCP server exposes catalog discovery, scene manifests, sound-design recommendations, evidence/storyboard validation, draft persistence, safe render preparation, and event/trace inspection. It never exposes host filesystem paths, arbitrary commands, raw prompts, credentials, or hidden model reasoning. The versioned `skills/msf-studio` package routes agents into `preset`, `curated`, `sandbox`, `voice`, `research`, and `debug` workflows with explicit approval boundaries.

For the included LLM Hubs evidence-backed sample series, validate the source packs and build the specs/audio first. The final batch-render uses the system Chromium explicitly to avoid an unnecessary browser download.

```bash
PYTHONPATH=. python tools/check_llm_hubs_evidence.py
PYTHONPATH=. python projects/llm_hubs/build_series.py
projects/llm_hubs/render_series.sh
```

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
        ▼           Live preset catalog
   Qwen3-TTS         Visual effect catalog
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
| `msf/studio/` | v2 contracts, catalog, evidence/script gates, run/event/trace services and MCP adapter |
| `skills/msf-studio/` | Unified agent skill with preset, curated, sandbox, voice, research and debug workflows |
| `projects/llm_hubs/` | Evidence packs, reproducible scripts/specs and sample-series renderer |
| `remotion/src/presets/` | Live React scene composition catalog |
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
# Targeted Studio v2 release checks (works without optional GPU voice stack):
PYTHONPATH=. python tools/check_studio_v2.py
PYTHONPATH=. python tools/check_studio_research.py
PYTHONPATH=. python tools/check_studio_observability.py
PYTHONPATH=. python tools/check_studio_audio.py
PYTHONPATH=. python tools/check_studio_mcp.py
PYTHONPATH=. python tools/check_llm_hubs_evidence.py

# Full legacy suite; installs its optional LangGraph, Torch voice and Playwright browser dependencies separately.
PYTHONPATH=. python -m pytest tests/ -q
```

The repository contains legacy graph, panel and renderer tests in addition to the Studio v2 smoke checks. The full suite is environment-sensitive because the legacy path imports optional GPU voice, LLM orchestration and Playwright browser components.

## License

MIT
