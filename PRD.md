# Motion Studio Framework — PRD

**Version:** 1.0  
**Date:** 2026-08-14  
**Status:** Production-ready (38 presets, 96 effects, 18 transitions, 14 style kits)

---

## 1. Vision

Motion Studio Framework (MSF) is a modular system for generating short-form vertical video (1080×1920, 60fps) from a text prompt. It combines a **Remotion** (React/TypeScript) scene renderer with a **LangGraph** (Python) pipeline graph, and ships a **Control Panel** web UI for operators to preview presets, manage voices, and run pipeline jobs without touching the CLI.

The framework produces videos like those on popular AI/tech Telegram channels — kinetic typography, 3D charts, phone mockups, Telegram chat reenactments — with per-scene voice cloning (Qwen3-TTS ICL), background music beds, SFX, and a readability contract that guarantees text is on screen long enough to read.

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Control Panel (:8765)                │
│  FastAPI + Vanilla JS   ←   operator previews & runs     │
└───────────┬──────────────────────────┬───────────────────┘
            │                          │
            ▼                          ▼
┌───────────────────────┐   ┌──────────────────────────────┐
│  LangGraph Pipeline  │   │  Resident Render Server      │
│  (msf/graph/)        │   │  (remotion/scripts/          │
│                      │   │   render_server.mjs :8766)   │
│  gate_check          │   │                              │
│  deep_research       │   │  Bundles once, answers       │
│  script_split       │   │  stills & clips in ~7s / ~4s  │
│  voice_synthesis     │   └──────────────────────────────┘
│  soundtrack          │
│  build_spec          │   ┌──────────────────────────────┐
│  render              │──→│  Remotion (React/TS)         │
│  master_audio        │   │  38 presets / 96 effects     │
│  qa                  │   │  18 transitions / 14 styles  │
│  repair              │   └──────────────────────────────┘
└───────────────────────┘
```

### 2.1 Pipeline Graph (LangGraph)

Nodes execute in order, passing a shared `state` dict:

| Node | File | Purpose |
|---|---|---|
| `gate_check` | `video_graph.py` | Validates topic, preset, voice exist before spending compute |
| `deep_research` | `skills_bridge/deep_research.py` | Optional LDR (local-deep-research) fact-gathering; fail-closed |
| `script_split` | `video_graph.py` | LLM splits topic into N scene scripts |
| `voice_synthesis` | `skills_bridge/qwen3_tts.py` | Qwen3-TTS ICL cloning per scene |
| `soundtrack` | `audio/soundtrack.py` | Generates music bed + SFX; ducks under voice (-7.39 dB) |
| `build_spec` | `video_graph.py` | Assembles VideoSpec JSON from scripts + audio |
| `render` | `panel/render_client.py` | Sends spec to resident render server → MP4 |
| `master_audio` | `audio/voice_prep.py` | Mix voice + music + SFX to -16 LUFS |
| `qa` | `video_graph.py` | Validates output exists, has audio, meets duration |
| `repair` | `video_graph.py` | Re-renders failed scenes if QC fails |

### 2.2 Remotion Renderer

Scene compositions live in `remotion/src/presets/*.tsx`. Each preset is a React component receiving `{ scene, styleKit, fps, durationInFrames }`. The registration system (`remotion/src/registry/presets.ts`) maps preset names to component + metadata (category, row shapes, safe-area constraints).

**Resident render server** (`remotion/scripts/render_server.mjs`): a persistent Node process that bundles once and answers `still` / `clip` / `range` requests over HTTP. Cold start: ~14s (bundle). Warm: still ~7s, clip ~4s.

### 2.3 Control Panel

FastAPI backend (`msf/panel/server.py`) + vanilla HTML/JS/CSS frontend (`msf/panel/static/`). No build step needed for the UI.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/status` | GET | Health: registry, voices, node, ffmpeg, LDR |
| `/api/scenes` | GET | All 38 presets with metadata |
| `/api/effects` | GET | 96 effects + 18 scene transitions |
| `/api/demo/props/{preset}` | GET | Demo props for a preset (prefill editor) |
| `/api/preview/scene` | POST | Render a still (PNG) via render server |
| `/api/preview/clip` | POST | Render a frame range (MP4) |
| `/api/preview/voice` | POST | Synthesize a voice sample |
| `/api/preview/sfx/{name}` | GET | SFX preview audio |
| `/api/preview/music/{name}` | GET | Music bed preview audio |
| `/api/render-server` | GET | Render server status |
| `/api/render-server/restart` | POST | Drop render bundle (re-bundle on next request) |
| `/api/voices` | GET / POST / DELETE | Voice registry CRUD |
| `/api/voices/measure` | POST | Measure a candidate reference (SNR, clipping, silence) |
| `/api/voices/prepare` | POST | Clean audio: highpass → afftdn → trim → normalize |
| `/api/voices/transcribe` | POST | Whisper large-v3-turbo transcription (97.7% accuracy) |
| `/api/graph` | GET | Pipeline graph structure |
| `/api/graph/run` | POST | Start a full pipeline run (subprocess) |
| `/api/runs` | GET | List active/finished runs |
| `/api/runs/{id}` | GET | Run status + log |
| `/api/runs/{id}/kill` | POST | Terminate a run |
| `/api/ldr` | GET | LDR wiring status |

## 3. Scene Registry

**Source of truth:** TypeScript files in `remotion/src/registry/*.ts`. Python parser (`msf/registry.py`) reads them for 100% parity.

### 3.1 Presets (38)

| Category | Presets |
|---|---|
| Social | `Leaderboard`, `SubscribeCTA`, `CommentWall`, `PostCard` |
| Hero | `HeroKinetic`, `CountdownHero`, `TypewriterSub`, `QuoteCard` |
| Charts | `Bars3D`, `RingStats`, `DonutFill`, `StatCounter` |
| Device | `PhoneMockup`, `TgChat`, `AiChatStream`, `MusicPlayer`, `VoiceMemo` |
| Compare | `CompareSplit`, `VersusSplit`, `SwipePanels` |
| Code | `CodeReveal`, `FlowDiagram` |
| Learn | `DefinitionCard`, `ProgressPath`, `QuizCard` |
| Media | `ImageShowcase`, `VideoEmbed`, `ScreenRecord`, `VinylRecord` |
| Stage | `ScoreHud`, `TimelineReveal`, `LayerStack3D` |
| Crypto | `CryptoWallet`, `TokenCloud3D`, `ModelOrbit3D` |
| Layout | `GridGridFloor`, `BankCard`, `LyricLines` |

### 3.2 Scene Transitions (18 Zod camelCase)

`wipe`, `slide`, `dreamyZoom`, `fade`, `flip`, `clockWipe`, `radialWipe`, `curtain`, `door`, `glitch`, `pixelate`, `zoomBlur`, `iris`, `wave`, `cube`, `ripple`, `pageCurl`, `shake`

**Source:** `remotion/src/lib/transitions.ts` (Zod schema). Legacy names (`fade_black`, `wipe_left`) are removed.

### 3.3 Style Kits (14)

`blueprint`, `candy`, `clean`, `cyber_lime`, `editorial`, `forest`, `glass`, `mono_warm`, `noir`, `pop`, `sunset`, `tech_dark`, `tech_neon`, `vapor`

Each kit defines: `bg`, `surface`, `primary`, `secondary`, `accent`, `text`, `muted`, `glass` colors + font sizes. Source: `remotion/src/theme/styleKits.ts`.

### 3.4 Effects (96)

Organized by family in `remotion/src/registry/effects_*.ts`. Python parser exposes `load_effects()` and `effects_by_family()`.

## 4. Voice Pipeline

### 4.1 Qwen3-TTS ICL (In-Context Learning)

Default voice: `voice_3`. The synthesizer clones from a reference audio + verbatim transcript. Without `ref_text`, the model falls to x-vector mode (timbre copied, prosody flat) — the panel refuses to create a voice entry without a transcript.

### 4.2 Voice Preparation (`msf/audio/voice_prep.py`)

1. **Measure** — SNR, clipping, silence, sample rate (no modification)
2. **Prepare** — highpass 80Hz → afftdn (measured noise floor) → trim silence → normalize to -1.5 dBFS
3. **Transcribe** — Whisper large-v3-turbo (97.7% word agreement, ~1.9s on RTX 4060)
4. **Register** — Copy to `assets/voices/refs/`, add to `voices.json` with transcript

### 4.3 Denoiser Choice

`afftdn` over `arnndn` (no model shipped) and `anlmdn` (measured no-op). Noise floor `nf` is measured from the clip, not hardcoded — a fixed `nf=-45` made the strength control a no-op (SNR 23→24 dB; measured `nf` gives SNR 23→37 dB).

## 5. Readability Contract (Dwell Pacing)

| Constant | Value | Source |
|---|---|---|
| `SAFE_AREA_TOP_PX` | 160 | `msf/spec.py`, `remotion/src/lib/safeArea.ts` |
| `SAFE_AREA_BOTTOM_PX` | 380 | same |
| `MIN_DWELL_SEC` | 1.0 | `msf/spec.py`, `remotion/src/lib/pacing.ts` |
| `READ_CHARS_PER_SEC` | 12.0 | same |
| `FPS` | 60 | `msf/spec.py`, `config/default.yml` |

Every scene's `durationInFrames` must satisfy: `dwell_time ≥ max(MIN_DWELL_SEC, text_len / READ_CHARS_PER_SEC)`. The pacing module (`remotion/src/lib/pacing.ts`) computes absolute `settleBy()` times — presets call it instead of guessing frame offsets.

## 6. Rotation & Safety

- **ROTATION_SAFE** (8 presets): `HeroKinetic`, `Bars3D`, `RingStats`, `TgChat`, `PhoneMockup`, `StatCounter`, `TypewriterSub`, `QuoteCard`
- The graph's `build_spec` node selects from this set when `preset` is not specified.
- `ALLOWED_PRESETS` (all 38) is the full library when the operator explicitly names a preset.
- `_TEXT_SAFE_PRESETS` is the subset with verified safe-area compliance.

## 7. Configuration

`config/default.yml`:

```yaml
llm:
  base_url: http://localhost:20128/v1
  model: antigravity/gemini-3.6-flash-high
tts:
  provider: qwen3
  speaker: voice_3          # must exist in assets/voices/voices.json
  sample_rate: 24000
render:
  fps: 60                   # load-bearing for frame-count constants
  width: 1080
  height: 1920
audio:
  target_lufs: -16.0
pipeline:
  max_qc_attempts: 3
  save_intermediate: true
```

## 8. Testing

14 test files, 165+ tests:

| File | Tests | Validates |
|---|---|---|
| `test_pacing.py` | 9 | Dwell pacing constants parity |
| `test_registry_parity.py` | 12 | Python parser vs TypeScript source |
| `test_row_shapes.py` | 10 | Row shape validation rules |
| `test_panel_api.py` | 6+ | REST API endpoints |
| `test_soundtrack.py` | 9 | Music bed + SFX mixing |
| `test_deep_research.py` | 18 | LDR fail-closed behavior |
| `test_theme_parity.py` | — | Style kit + transition parity |
| `test_model_icons.py` | — | Avatar resolver |
| `test_phase3.py` | — | End-to-end spec → render |
| ... | | |

Run: `python -m pytest tests/ -q`

## 9. Quick Start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Remotion deps
cd remotion && npm install && cd ..

# 3. Start the control panel
python -m msf.panel.server
# → http://127.0.0.1:8765

# 4. Or run a pipeline job directly
python -m msf.cli "Сравнение локальных и облачных LLM" --preset HeroKinetic
```

## 10. Constraints

- **No secrets in repo.** API keys go in `config/default.yml` (gitignored) or env vars.
- **TS is truth.** Registry changes happen in `.ts` files first; `msf/registry.py` parses them.
- **60fps only.** Frame-count constants (transitions, motion presets) are calibrated for 60fps.
- **Fail-closed.** LDR, voice resolution, and spec validation raise rather than invent.
- **No build step for UI.** Panel is vanilla HTML/JS/CSS served by FastAPI StaticFiles.
