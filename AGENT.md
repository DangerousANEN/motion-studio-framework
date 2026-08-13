# AGENT.md — MSF Guide for AI Agents

> **Read this first.** MSF has hard-won invariants. Violating them silently breaks renders, voices, or readability — the defects that took days to find and fix. This file is the map.

---

## 1. What MSF Is

Motion Studio Framework generates vertical video (1080×1920, 60fps) from text. A **LangGraph** pipeline (Python) orchestrates LLM scripting, Qwen3-TTS voice cloning, Remotion rendering, and audio mastering. A **Control Panel** (FastAPI + vanilla JS) lets operators preview and run jobs.

## 2. Source-of-Truth Rules (NON-NEGOTIABLE)

| Thing | Truth Source | Python Reader | NEVER do |
|---|---|---|---|
| Presets (38) | `remotion/src/registry/presets.ts` | `msf/registry.py` | Hardcode preset names in Python |
| Effects (96) | `remotion/src/registry/effects_*.ts` | same | Duplicate the list |
| Transitions (18) | `remotion/src/lib/transitions.ts` (Zod) | `registry.scene_transition_types()` | Use legacy names (`fade_black`, `wipe_left`) |
| Style kits (14) | `remotion/src/theme/styleKits.ts` | `registry.load_style_kits()` | Define colors in Python |
| Pacing constants | `remotion/src/lib/pacing.ts` | `msf/spec.py` (parity test) | Change FPS — constants are frame-calibrated for 60 |
| Voices | `assets/voices/voices.json` | `msf/skills_bridge/qwen3_tts.py` | Hardcode paths in Python |
| Config | `config/default.yml` | `msf/config.py` | Set values in Python that should be in YAML |

**If you add a preset:** add it to `presets.ts`, create the `.tsx`, add demo props to `demo_props.py`, and the parser picks it up. Do not touch `registry.py`.

**If you add a transition:** add it to the Zod schema in `transitions.ts`. The Python parser, panel, and tests all read from there.

## 3. Key Directories

```
msf/
  graph/video_graph.py      LangGraph pipeline (nodes, edges, state)
  panel/server.py           FastAPI control panel (REST API)
  panel/render_client.py    HTTP client → resident render server
  panel/demo_props.py       Demo data for each preset
  audio/voice_prep.py       Whisper + ffmpeg voice preparation
  audio/soundtrack.py       Music bed + SFX generator
  skills_bridge/
    qwen3_tts.py            Qwen3-TTS ICL cloning
    deep_research.py        LDR integration (fail-closed)
  registry.py               TS → Python parser
  spec.py                   VideoSpec validator + constants
  config.py                 YAML config loader

remotion/
  src/presets/*.tsx         Scene compositions (React)
  src/registry/*.ts         Registration (presets, effects, types)
  src/theme/styleKits.ts    14 style kits
  src/lib/transitions.ts    18 Zod transitions (source of truth)
  src/lib/pacing.ts         Dwell pacing calculator
  src/lib/safeArea.ts       Safe area constants
  scripts/render_server.mjs Resident render server (:8766)
  scripts/stress.mjs        Batch render test (standalone)

tests/                      14 test files (pytest)
config/default.yml          Runtime config
assets/voices/             Voice references + voices.json
```

## 4. Design Invariants

### 4.1 Fail-Closed
- LDR raises rather than inventing facts.
- `resolve_voice()` raises if the configured voice doesn't exist (no silent fallback to a different voice).
- `validate_spec()` raises on bad row shapes, missing fields, or unreadable text.
- The render server returns errors, not fake success.

### 4.2 No Silent No-Ops
- Denoise `nf` is MEASURED per clip — a hardcoded `nf` made `nr` a no-op (SNR didn't change).
- `durationInFrames` comes from `calculateMetadata`, not a guess — frame percentage resolves against the real composition length.
- Spec validation runs BEFORE rendering — a row-shape error returns a 422, not a red ERROR card rendered as if it were a working scene.

### 4.3 Readability Contract
Every scene must satisfy: `dwell_time ≥ max(1.0s, text_length / 12 chars_per_sec)`. Presets compute `settleBy()` via `pacing.ts` then derive their animations backward from the settle deadline. Do not hardcode frame offsets — use the pacing module.

### 4.4 Safe Area
Content must fit between Y=160 (top) and Y=1540 (bottom, = 1920 − 380). The validator checks `_ROW_SHAPES_HARD` rules. Presets that clip into the safe area fail validation, not silently render clipped text.

### 4.5 Single Renderer
The panel uses the SAME render path as the pipeline (`render_client.py` → `render_server.mjs`). There is no separate panel renderer. If they diverged, "it looked fine in the panel" would stop meaning "it works in production."

## 5. Common Tasks

### Add a preset
1. Create `remotion/src/presets/MyPreset.tsx` — React component receiving `{ scene, styleKit, fps, durationInFrames }`.
2. Register in `remotion/src/registry/presets.ts` with metadata (category, row shapes, etc.).
3. Add demo props in `msf/panel/demo_props.py` (`DEMO_PROPS["MyPreset"] = { ... }`).
4. Test: `python -m pytest tests/test_registry_parity.py`.

### Add a transition
1. Add Zod type + implementation in `remotion/src/lib/transitions.ts`.
2. The Python parser, panel `/api/effects`, and tests automatically pick it up.
3. Test: `python -m pytest tests/test_theme_parity.py`.

### Add a voice
1. Prepare the reference: `POST /api/voices/measure` → `POST /api/voices/prepare`.
2. Transcribe: `POST /api/voices/transcribe` (Whisper, 97.7% accuracy — **proofread**).
3. Register: `POST /api/voices` (requires `key`, `ref_audio` path, `ref_text`).
4. Or do it via CLI: edit `assets/voices/voices.json` and place the wav in `assets/voices/refs/`.

### Fix a rendering bug
1. Reproduce: `POST /api/preview/scene {"preset":"X","scale":0.5}` — get a PNG in ~7s.
2. If the bug is motion: `POST /api/preview/clip {"preset":"X","scale":0.5,"from_frame":0,"to_frame":60}` — get an MP4 in ~4s.
3. Fix the `.tsx` preset.
4. Restart the render server: `POST /api/render-server/restart` (the bundle is held in memory).
5. Re-render to verify.

### Run the full test suite
```bash
python -m pytest tests/ -q
# Expected: 165 passed, 1 skipped, 0 failed
```

### Run a full pipeline
```bash
python -m msf.panel.server                    # start panel
# POST /api/graph/run {"topic":"...", "preset":"HeroKinetic", "scenes":4}
```

## 6. What NOT to Do

- **Don't hardcode preset/transition/effect/style names in Python.** Read them from the registry parser.
- **Don't change FPS to 30.** Frame-count constants (transition=18f, motion presets) are calibrated for 60fps. A different FPS breaks pacing tests.
- **Don't add a fallback voice.** `resolve_voice()` raises if the configured voice is missing. That is the design — a silent fallback to a different voice was the original bug.
- **Don't skip `validate_spec()`.** It catches row-shape errors before render. A preset with the wrong row shape renders the red error card — and the panel would display it as a "working" preview.
- **Don't use `arnndn` for denoising.** No model file ships with the ffmpeg build here. `afftdn` is the chosen denoiser with a MEASURED noise floor.
- **Don't auto-save Whisper transcripts.** 97.7% accuracy means 2.3% is wrong. ICL aligns audio to whatever text it's handed — a wrong ref_text degrades cloning silently. Always return for editing.
- **Don't add a second renderer for the panel.** Divergence between panel and pipeline renderers is how bugs hide.
- **Don't guess durations.** Use `demo_props.suggested_duration()` or `pacing.ts`. A fixed 180 frames invented readability warnings on 7 presets whose demo copy can't be read in 3s.

## 7. Testing Strategy

- **Unit tests** (`tests/test_*.py`): 14 files, 165+ tests, run with pytest.
- **Registry parity**: Python parser output vs TypeScript source (test_registry_parity, test_theme_parity).
- **Config parity**: YAML values vs Python constants (test_config_parity) — FPS locked at 60.
- **API tests**: Panel endpoints (test_panel_api) — served effects match registry, transitions validate.
- **Visual tests**: `stress.mjs` generates PNGs; `timing.mjs` probes reveal timings.

When you change something, run the tests. When you add something, add a test. When you fix a bug, add a regression test.

## 8. Error Philosophy

MSF reports failures, it does not hide them:

- **`measure()` before `prepare()`**: reports SNR, clipping, silence — doesn't fix silently.
- **`validate_spec()` before render**: returns 422 with the specific error, not a red card rendered as a preview.
- **`deep_research` fail-closed**: raises rather than producing a video with invented facts.
- **Render server**: returns `{ ok: false, error: "..." }`, not a fake success.
- **Voice prep guard**: refuses to return a clip the silence threshold ate (`duration < 50% → RuntimeError`).

If you're adding a feature, ask: what happens when it fails? The answer should be "the operator sees the error" — not "it silently produces garbage."

## 9. Commit Conventions

```
feat(scope): short description
fix(scope): short description
```

Scopes: `scenes`, `audio`, `panel`, `render`, `graph`, `theme`, `pacing`, `voice`, `research`, `rotation`.

Examples from the log:
- `fix(Bars3D): rebuild the extrusion as isometric clip-paths`
- `feat(audio): wire music beds and SFX into the graph via a mixed soundtrack`
- `fix(rotation,voice): use the whole library, and the voice that was configured`

---

*This file is the product of ~60 commits of hard-won lessons. When you change something that contradicts an invariant here, update this file too.*
