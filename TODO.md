# MSF — TODO

**Last updated:** 2026-08-14  
**Status:** v1.0 shipped; roadmap below.

---

## ✅ Completed (v1.0)

- [x] 38 presets across 11 categories (social, hero, charts, device, compare, code, learn, media, stage, crypto, layout)
- [x] 96 visual effects in 6 families
- [x] 18 Zod scene transitions (`lib/transitions.ts`) — legacy names removed
- [x] 14 style kits with WCAG-AA-compliant contrast
- [x] Qwen3-TTS ICL voice cloning (default: `voice_3`)
- [x] Whisper `large-v3-turbo` transcription (97.7% accuracy, ~1.9s on RTX 4060)
- [x] Voice preparation pipeline: highpass → afftdn (measured nf) → trim → normalize
- [x] Dwell Pacing Contract: `MIN_DWELL_SEC=1.0`, `READ_CHARS_PER_SEC=12.0`
- [x] Safe Area enforcement: top 160px, bottom 380px
- [x] Soundtrack node: music bed + SFX, -7.39 dB duck under voice
- [x] Deep Research (LDR) node: fail-closed, no invented facts
- [x] Model icon resolver (42 AI model avatars)
- [x] Control Panel: FastAPI + vanilla JS (status, presets, voices, runs, previews)
- [x] Resident render server (`render_server.mjs` :8766): bundle once, still ~7s, clip ~4s
- [x] Render client (`render_client.py`): ping/still/clip/stop with error handling
- [x] Demo props generator (`demo_props.py`): 22+ preset-specific demo data sets
- [x] Registry parity: Python parser reads TS source-of-truth (38 presets, 96 effects, 18 transitions, 14 kits)
- [x] 14 test files, 165+ passing tests
- [x] Config parity test (FPS, voices, presets locked between YAML and Python)

---

## 🔲 Next: P1 (high value)

### Panel UI
- [ ] Wire clip preview button to `/api/preview/clip` (backend ready, UI not yet)
- [ ] Add voice preparation wizard: measure → prepare → transcribe → review → register
- [ ] Add render-server status indicator (poll `/api/render-server`)
- [ ] Add restart render-server button (calls `/api/render-server/restart`)
- [ ] Show `durationInFrames` from response in preview results (solves the "what frame %" question)

### Presets
- [ ] Add `ImageShowcase` Ken Burns motion (zoom + pan on static images)
- [ ] Add `VideoEmbed` background video loop with overlay text
- [ ] Add `ScreenRecord` scroll-and-highlight zoom effect
- [ ] Verify all 38 presets pass DV (design verification) with demo props

### Pipeline
- [ ] Wire `agent_level` to script quality (currently: level 1-5 but only affects prompt)
- [ ] Add per-scene preset override in `build_spec` (currently single preset for all scenes)
- [ ] Add multi-voice support (different voices per scene)
- [ ] Add music library selector (currently auto-generated beds)

---

## 🔲 Next: P2 (medium value)

### Rendering
- [ ] GPU-accelerated encoding (currently CPU x264; `--gpu` flag for NVENC)
- [ ] Parallel scene rendering (currently sequential)
- [ ] Render progress WebSocket (currently poll `/api/runs/{id}`)
- [ ] Output to S3/R2 (currently local `output/`)

### Voices
- [ ] Multi-language support (current pipeline assumes Russian)
- [ ] Voice comparison view (render same text with 2 voices, A/B)
- [ ] Automatic ref_text alignment from Whisper timestamps

### Presets
- [ ] `MapOverlay` — animated geo maps with route lines
- [ ] `BarChartRace` — animated ranking over time
- [ ] `SplitScreen` — two scenes side by side
- [ ] `TableGrid` — sortable data table with reveal animation

### Testing
- [ ] Visual regression: snapshot PNG diffing for every preset
- [ ] E2E test: full pipeline run → MP4 exists → has audio → duration sane
- [ ] Stress test: 10 consecutive renders, detect leaks

---

## 🔲 Next: P3 (nice to have)

- [ ] WebSocket live preview (instead of POST + wait for PNG)
- [ ] Preset editor GUI (drag-and-drop layout)
- [ ] Style kit editor (color picker + live preview)
- [ ] Social media auto-post (Telegram, YouTube Shorts)
- [ ] Template library (reusable spec templates for recurring video formats)
- [ ] Timeline editor (reorder scenes, adjust durations visually)
- [ ] Multi-language UI (English / Russian)
- [ ] Plugin system for custom presets

---

## 🔲 Technical Debt

- [ ] `stress.mjs` — keep or remove? Render server replaced it for previews; still used for batch tests
- [ ] `make_preview_assets.py` — wired? Check if called from panel or standalone
- [ ] `tools/timing_probe.py` — document usage (pulse filter, frame detection)
- [ ] Consolidate `subprocess` imports in `server.py` (imported in multiple functions)
- [ ] Type-check `.tsx` presets with `tsc --noEmit` in CI
- [ ] Add `engines` field to `remotion/package.json` (`node >= 18`)
- [ ] `.gitignore` — exclude `remotion/out/` (207 PNGs tracked, 12 MB)

---

## 🔲 Documentation

- [x] `PRD.md` — product requirements
- [x] `TODO.md` — this file
- [x] `AGENT.md` — AI agent onboarding
- [ ] `README.md` — project overview + quickstart
- [ ] API reference (auto-generated from FastAPI OpenAPI at `/docs`)
- [ ] Preset catalog (screenshots of all 38 presets)
- [ ] Deployment guide (VPS/bare metal)
