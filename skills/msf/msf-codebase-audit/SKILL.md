---
name: msf-codebase-audit
description: Use when MSF audio is silent or graph nodes need wiring.
---
# MSF Codebase Audit — Verified Findings & Engineering Patterns

Use this skill when:
- Diagnosing "-91 dB silence" or missing audio in MSF renders
- Adding new nodes to `build_msf_graph()`
- Updating `scripts_tg/*.json` scenario files for new model data
- Tracing `audio_url` / `audioUrl` field through the Python → TypeScript wire
- Fixing preset LAYOUT or GEOMETRY (clipping, invisible labels, drifting baselines,
  UI mockups that don't look like the real app) → `references/preset_layout_budget.md`
- Adding music / SFX / mixing to a render → `references/soundtrack_mixing.md`
- **"Агенты используют только первые N сцен"**, writing any Python list of presets /
  effects / graph nodes, parsing the TS registry, or building a catalogue or panel over
  it → `references/registry_parity_and_derived_lists.md`
- **Wrong or unexpected NARRATOR** (female voice, flat/robotic prosody), touching
  `voice_agent.py` / `qwen3_tts.py` / `voices.json` / `tts.*` config, or adding a voice
  → `references/voice_identity_and_fallbacks.md`
- Reveals that finish too late to read, scenes that feel rushed → the pacing reference in
  the `remotion-video-engineering` skill

All findings verified via actual code reads + ffmpeg/ffprobe measurements.

> **STATUS 2026-08-12 — the audio wiring below is FIXED, in commit `197dfac`.** The dead
> key, the unconditional hardcode and the voice default are all resolved; the sections are
> kept because they document *how* the failure was found. Two corrections to what this file
> used to claim:
> - Path A's "-18 dB confirmed" was measured on `output/remotion/msf_herokinetic.mp4`, an
>   artifact **four days old**. A stale mp4 is not evidence the graph works today. Re-measure
>   before trusting it.
> - The `node_deep_research` contract below was **fail-open** and that is wrong. See the
>   correction under "Adding node_deep_research".

> **STATUS 2026-08-12 (later) — `node_soundtrack` and `node_deep_research` are both SHIPPED**
> (`b489c2b`, `9a592ae`). The graph order section at the bottom is updated. Audio is no longer
> just voice: it is one mixed wav at the root. Read `references/soundtrack_mixing.md` before
> touching audio and `references/preset_layout_budget.md` before touching any preset layout.

Support files:
- `references/node_deep_research_impl.md` — full `node_deep_research` implementation
  (constants, VideoState fields, helpers, build_msf_graph() wiring, example invocation).
- `references/soundtrack_mixing.md` — the shipped voice+music+SFX mixer: why ONE root wav,
  the 24k→48k resample trap, transition-overlap cue timing, and the measurements that prove
  a mix rather than assert it.
- `references/preset_layout_budget.md` — the class of preset bug where text goes INVISIBLE
  rather than clipped, plus the label-alias and ranking-correctness traps. Read before
  declaring any preset "fits".
- `references/registry_parity_and_derived_lists.md` — why NO Python list may mirror the TS
  registry, how to verify a parser against node, why `rotation_safe` ≠ "renders my text",
  row-shape validation, and the "plausible wrong answer" bug class (code succeeds, result is
  false). Read before writing any preset/effect/voice list or catalogue.
- `references/voice_identity_and_fallbacks.md` — the female-voice report: a dead hardcoded
  reference path swallowed by a bare `except`, falling through to Silero/edge-tts, which
  cannot clone. Fallbacks that change the speaker must be opt-in; config parity is
  load-bearing.

---

## The Three Render Paths (audio behaves differently in each)

### Path A — `build_msf_graph().invoke()` ✅ WORKS (-18 dB confirmed)
```
node_voice_synthesis:
  sc["audio_file"] = scene_wav_name   ← dead key — never read
  shutil.copy(wav → remotion/public/scene_NN.wav)

_scene_kwargs() line 301:
  kwargs["audio_url"] = f"scene_{index:02d}.wav"   ← hardcode fallback, correct

spec.py Scene._CAMEL["audio_url"] = "audioUrl"
→ to_dict() → {"audioUrl": "scene_00.wav"}
→ Main.tsx: {scene.audioUrl && <Audio src={staticFile(scene.audioUrl)}/>}
```
**This path is the only correct path. Use it exclusively.**

### Path B — `render_promo_shorts.py` ⚠️ BYPASS
Does NOT set `sc["audio_url"]` before `node_build_remotion_spec`. Hardcode at line 301
still produces the right filename. Then `ffmpeg -map 1:a:0 merged_wav` adds audio
externally — if Remotion also renders `<Audio>`, both fire (double-track risk).

### Path C — `scripts_tg/*.json` → `npx remotion render --props=…` 🔴 SILENCE
**None of the three `scripts_tg/*.json` files contain `audioUrl` on any scene.**
Direct Remotion render → `scene.audioUrl = undefined` → no `<Audio>` tag → **-91 dB silence**.
This is the confirmed source of the silent-render problem.

Fix options (prefer order):
1. Always route through `build_msf_graph().invoke()` — graph sets `audioUrl` automatically
2. Add `"audioUrl": "scene_NN.wav"` (0-based index) to each scene in the JSON file

---

## Known Dead Key: `sc["audio_file"]` (video_graph.py:369)

`node_voice_synthesis` writes `sc["audio_file"] = scene_wav_name`. This key is **never
read** — `_scene_kwargs`, `Scene`, and `to_dict()` all ignore it. The hardcode at line 301
masks the bug by producing the same filename independently.

**Planned fix:**
```python
# video_graph.py line 369 — BEFORE:
sc["audio_file"] = scene_wav_name
# AFTER:
sc["audio_url"] = scene_wav_name

# video_graph.py line 301 — BEFORE (always overwrites):
audio_url=f"scene_{index:02d}.wav",
# AFTER (prefer explicit value from scene):
audio_url=normalised.get("audio_url") or f"scene_{index:02d}.wav",
```

---

## Audio Triage Checklist (when mean_volume = -91 dB)

```bash
# 1. WAV files exist in remotion/public/?
ls C:/Users/ANEN/motion-studio-framework/remotion/public/scene_*.wav

# 2. audioUrl in every scene of the spec JSON?
python -c "
import json
spec = json.load(open('C:/Users/ANEN/motion-studio-framework/remotion/public/video-spec.json', encoding='utf-8'))
for sc in spec['scenes']:
    print(sc['id'], '|', sc.get('audioUrl', 'MISSING'))"

# 3. Final MP4 has audio?
ffmpeg -hide_banner -nostats -i output\msf_herokinetic.mp4 -af volumedetect -f null NUL 2>&1 | grep mean_volume
# Expect: mean_volume: -18.x dB   NOT -91 dB
```

If (1)✓ but (2) shows MISSING → `_scene_kwargs` not carrying `audio_url`; check line 301.
If (1)✓ and (2)✓ but (3) silent → MP4 rendered directly from JSON, bypassing the graph.

---

## Adding `node_deep_research` to the Graph

### Graph wiring (build_msf_graph)
```python
# BEFORE:  gate_check → script_split
# AFTER:   gate_check → deep_research → script_split

workflow.add_node("deep_research", node_deep_research)
workflow.add_edge("gate_check", "deep_research")
workflow.add_edge("deep_research", "script_split")
```

### New VideoState fields
```python
ldr_enabled: Optional[bool]      # True → run LDR; None/False → pass-through
ldr_query: Optional[str]         # explicit query; None → auto from text/topic
ldr_topic: Optional[str]
ldr_detailed: Optional[bool]
ldr_iters: Optional[int]         # default 2
ldr_qpi: Optional[int]           # questions_per_iteration, default 3
ldr_model: Optional[str]         # default "antigravity/claude-sonnet-4-6"
ldr_summary: Optional[str]
ldr_sources: Optional[List[str]]
ldr_context: Optional[str]
ldr_cache_path: Optional[str]    # path to ldr_last_raw.json; skip rerun if present
```

### Critical: LDR subprocess must use LDR_WORKDIR as cwd
```python
LDR_VENV_PYTHON = r"C:\Users\ANEN\ldr_venv\Scripts\python.exe"
LDR_SCRIPT      = r"C:\Users\ANEN\ldr_work\ldr_run.py"
LDR_WORKDIR     = r"C:\Users\ANEN\ldr_work"
```
`C:\Users\ANEN\local_deep_research.py` shadows the installed package. Running from the
home directory raises `ImportError`. `cwd=LDR_WORKDIR` is mandatory.

### node_deep_research design contract
- `ldr_enabled=False` or not set → immediate `return state`, zero side effects
- Writes `ldr_last_raw.json`; pass `ldr_cache_path` to reuse without re-running

> **CORRECTION — must be FAIL-CLOSED, not fail-open.** The original bullet here said
> "LDR subprocess failure → log WARNING, set `ldr_context=""`, continue (non-fatal)".
> That defeats the entire point of the node: if SearXNG is down or the search returns zero
> sources, the pipeline silently builds a video from model memory, which is exactly the
> stale-facts failure the research gate exists to prevent. The runner's exit code does not
> help — it is `return 0 if summary else 1`, so a zero-source run that answered from memory
> exits **0**.
>
> Correct behaviour: parse the source count (`sources=(\d+)` from stdout, or read
> `ldr_last_raw.json` in the cwd) and when `require_research` is set and `sources == 0`,
> **raise**. Two independent code-writing subagents produced fail-open nodes with zero
> `raise` statements across a 553-line plan, so do not accept a generated implementation
> without grepping it for `raise`.

### Voice default (fixed 2026-08-12)
`DEFAULT_VOICE` in `msf/skills_bridge/qwen3_tts.py` pointed at `"syenduk"`, a key that does
not exist in `assets/voices/voices.json` (only `voice_2` and `voice_3` do). `resolve_voice(None)`
fell through the registry onto a bare wav path **with no transcript**, so cloning degraded to
x-vector — timbre only, flat prosody. Default is now `voice_3`. Assert the mode, not the path:

```python
describe_reference(None)["has_ref_text"] is True   # -> "ICL (prosody transferred)"
```

> **Same stale key bit again later, in a worse way.** `tts.speaker` was ALSO `"syenduk"` in
> `config/default.yml` and `TTSConfig`, so anything honouring the config raised, got swallowed,
> and fell through to Silero `kseniya` / edge-tts `SvetlanaNeural` — both FEMALE and unable to
> clone. Full account and the rules that prevent it:
> `references/voice_identity_and_fallbacks.md`.

Also: Qwen3-TTS's ~60 s per phrase is **cold-start cost, not per-phrase cost**. Measured on a
two-scene spec: 96 s then 22 s. The model is cached in a module-level singleton, so a 15-scene
video costs ≈ 96 + 14×22 ≈ 6 min, not 15. Load once per run; never re-init per scene.

---

## scripts_tg Scenario Update — 2026 Model Data

Verified figures (multi-source corroborated in ldr_work/msf_models_2026.md):

| Model | Date | Type | VRAM@4bit | SWE-bench | AIME 2026 | GPQA | License |
|-------|------|------|-----------|-----------|-----------|------|---------|
| Gemma 4 31B | Jun 2026 | Dense 31B | ~18-20 GB | — | 89.2% | 84.3% | — |
| Qwen3.6-27B | Apr 2026 | MoE 3B active | 16 GB | 77.2% | — | — | Apache 2.0 |
| Qwen3.6-35B-A3B | Apr 2026 | MoE 3B active | <24 GB | 77.2% | — | — | Apache 2.0 |
| DeepSeek V4 | 2026 | — | server | leader | — | — | — |
| Llama 4 Scout | 2026 | — | ≤16 GB | — | — | — | Meta |

**Do NOT include benchmark numbers for GLM-5.2 or Llama 4 Scout** — single-source only.

Scripts needing update (audioUrl + 2026 models):
- `script1_local_vs_cloud.json` — replace Qwen3 32B / GPT-4o / Llama4 / DeepSeek V3
- `script2_prompt_unlock.json` — name the model explicitly (Gemma 4 31B, not "Модель")
- `script3_phone_model.json` — "8B phone model" → Qwen3.6-27B MoE (16 GB)

Full rewritten versions (with audioUrl per scene) in `ENGINEERING_PLAN_2026.md`.

---

## MSF Graph Node Order

SHIPPED (2026-08-12, commits `b489c2b` + `9a592ae`):
```
gate_check → deep_research → script_split → voice_synthesis → soundtrack
           → build_spec → render → master_audio → qa → [repair → render]
```

Placement reasons — both are load-bearing:
- `deep_research` sits BEFORE `script_split` because it can REPLACE `state["text"]`; running
  it after the split would leave the scenes built from the unresearched text.
- `soundtrack` sits AFTER `voice_synthesis` (it consumes the per-scene wavs) and BEFORE
  `build_spec` (it sets `soundtrack_path`, which `build_spec` mounts as the root `audioUrl`).
  `node_repair` must forward `audio_url=state.get("soundtrack_path")` too, or a QA retry
  re-renders with no audio at all.

Both nodes are OPT-IN and no-op by default: `research`/`research_query` for the first,
`music`/`sfx` (default True) for the second. An unrelated render never touches SearXNG.

> **The builder is `build_msf_graph`, not `build_video_graph`.** Anything that introspects
> the pipeline (a panel, a docs generator, a progress UI) must derive node names from the
> `add_node("<name>", node_fn)` calls in that function — the registered name differs from
> the function name in two places (`build_spec` → `node_build_remotion_spec`,
> `render` → `node_remotion_render`), so `hasattr(mod, f"node_{name}")` reports false
> misses. Name the builder candidates explicitly and raise on an empty result; a
> `try/except AttributeError` returning `[]` reads as "the pipeline has no nodes".

### Fail-closed research, as actually implemented
`msf/skills_bridge/deep_research.py` raises `ResearchUnavailable` on: SearXNG not answering
JSON, runner exit ≠ 0, missing result file, `sources < min_sources`, empty summary. Two extra
guards that are NOT theoretical:
- **stale file** — `ldr_run.py` overwrites `ldr_last_raw.json` only on success, so after a
  crash a file with `sources=60` is still sitting there and a naive reader sails through the
  gate holding someone else's research. Stamp mtime BEFORE launching, compare after.
- **wrong query** — concurrent runs share that one file, so compare the echoed `query`.

`check_searxng()` probes `?format=json` specifically: `/` returns 200 while the JSON endpoint
returns 403 when the format is disabled, and that 403 IS the silent-degradation path.

Live-verified: 103 s / 8 sources / real URLs on the happy path; with SearXNG pointed at a dead
port the pipeline STOPPED instead of narrating from model memory.
