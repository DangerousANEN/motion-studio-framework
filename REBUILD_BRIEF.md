# MSF v3 REBUILD BRIEF — fix a pipeline that renders demo placeholders instead of real content

Repo root: `C:\Users\ANEN\motion-studio-framework`
Remotion dir: `C:\Users\ANEN\motion-studio-framework\remotion` (Remotion 4.0.506, React 18, Node v24)

## CONFIRMED BUGS (verified by inspection + ffprobe + vision analysis of rendered output)

**BUG-1 (CRITICAL) — `--props` is never passed to Remotion.**
`msf/orchestrators/remotion_runner.py:107` and `msf/graph/video_graph.py:109` run:
`["npx.cmd","remotion","render","src/index.ts","Main",out_mp4]`
No `--props`. So `getInputProps()` in `remotion/src/Root.tsx` returns `{}`, and
`VideoSpecSchema.parse({})` fills in the built-in 5-scene DEMO REEL default.
=> Every video ever produced was the demo reel ("MOTION STUDIO", "NEO-BRUTALISM",
"FEATURES", "98% AUTOMATED MOTION"), NOT the user's text. Verified visually.

**BUG-2 (CRITICAL) — snake_case vs camelCase contract mismatch.**
Python writes `duration_in_frames`, `audio_file`, `text`, `accent`, `sub_text`.
Zod (`remotion/src/VideoSpec.schema.ts`) expects `durationInFrames`, `audioUrl`,
`title`, `subtitle`, `accentColor`. Even with `--props`, every field would be
dropped and silently replaced by defaults.

**BUG-3 (CRITICAL) — audio never reaches the video.**
Rendered mp4 measures `mean_volume: -91.0 dB` (digital silence) while the TTS wav
`remotion/public/scene_00.wav` is real speech at `-19.8 dB`. Cause: Python emits
`audio_file`, schema reads `audioUrl` => `<Audio>` never mounts.

**BUG-4 — `BRAND.muted` is undefined.**
`BRAND` in `remotion/src/presets/HeroKinetic.tsx` has no `muted` key, but
`StatCounter.tsx`, `GridGridFloor.tsx`, `SwipePanels.tsx`, `TypewriterSub.tsx` all
use `BRAND.muted` => `color: undefined`, silent styling breakage.

**BUG-5 — demo defaults mask failure.** `VideoSpecSchema.scenes` has a full
5-scene demo `.default()`. A totally broken pipeline still emits a pretty video.
This is why the bug survived. Defaults must not be able to stand in for real input.

**BUG-6 — Vision QA is fake and fail-open.**
`node_vision_qa` extracts frames hardcoded at n=15,45,75 (all inside scene 1),
judges quality by `file size > 3000 bytes`, and on ffmpeg exception sets
`qa_passed = True`. It cannot detect silence, wrong text, or blank frames.

**BUG-7 — self-correction loop is a no-op.** On failure it re-runs
`build_remotion_spec` with unchanged state => byte-identical render => same failure.

**BUG-8 — audio truncation.** `max(30, int(dur * 30))` floors the frame count, so
the tail of each scene's speech is cut. Needs ceil + tail padding.

**BUG-9 — FPS inconsistency.** Plan/PRD demand 60 FPS; code hardcodes 30 in
`remotion_runner.FPS`, `video_graph` (`int(dur*30)`), and schema default.

**BUG-10 — unsafe subprocess.** `subprocess.run([...], shell=True)` on Windows with
a list arg is fragile and mangles Cyrillic; stderr is discarded so Remotion's real
error never surfaces.

---

## REQUIRED IMPLEMENTATION (MSF v3)

### A. `remotion/src/VideoSpec.schema.ts` — strict contract, no demo fallback
- Keep camelCase as the ONLY wire format.
- `scenes`: `z.array(SceneSchema).min(1)` — **remove the 5-scene demo default entirely**.
- Remove `.default()` from `durationInFrames` (must be supplied).
- Add `fps` default 60, `width` 1080, `height` 1920.
- Add per-scene `audioUrl`, `title`, `subtitle`, `text`, `accentColor`, `bodyText`.
- Export `SAFE_PRESETS` list.
- Use `.passthrough()` NOT `.strict()` on scene objects (preset-specific extras),
  but the top-level VideoSpec must reject an empty `scenes`.

### B. `remotion/src/presets/brand.ts` — NEW shared brand module
Move `BRAND` out of HeroKinetic into its own file and **add the missing `muted`**:
```ts
export const BRAND = {
  bg: '#0E0F11', surface: '#16181C', gold: '#E6C475', neon: '#00FF88',
  cyan: '#00D4FF', text: '#FFFFFF', muted: '#8B92A0',
  darkBorder: '#000000', shadowColor: '#000000',
};
```
Update all 5 presets to `import { BRAND } from './brand'`. Keep
`export { BRAND } from './brand';` in HeroKinetic.tsx for backwards compat.

### C. All 5 presets — render REAL text, never placeholders
Each preset must render the scene's actual content. Critical rules:
- `HeroKinetic`: render `title`; if `title` is absent fall back to `text`. It must
  handle long Russian sentences — use `fontSize` that shrinks with text length
  (e.g. `clamp` logic: >60 chars => 56px, >30 => 72px, else 92px) and
  `overflowWrap:'break-word'` so text NEVER overflows the 1080px frame.
- `TypewriterSub`: word-by-word reveal driven by `text`. Timing must scale to the
  scene's real duration: `framesPerWord = durationInFrames / words.length`, not a
  hardcoded 5. Cap displayed words so long text stays inside the frame.
- Remove the hardcoded `★ LLM HUBS • SOTA TECH ★` badge from HeroKinetic — make it
  an optional `badge` prop (the user's channel rules forbid "SOTA" jargon).
- All presets must accept and honour `accentColor`.
- Add safe text truncation/scaling everywhere so nothing overflows 1080x1920.

### D. `remotion/src/Root.tsx`
- Read props via `getInputProps()`, parse with the strict schema.
- If `scenes` is missing/empty, still register a composition (Remotion needs one at
  bundle time) but with a single explicit `ERROR: no scenes supplied` scene so the
  failure is LOUD and obvious, never a pretty demo reel.
- `durationInFrames` = sum of scene durations (must be >= 1).
- Keep the 5 standalone per-preset compositions for isolated testing.

### E. `msf/spec.py` — NEW single source of truth (Python side)
- `FPS = 60`, `WIDTH = 1080`, `HEIGHT = 1920`, `TAIL_PAD_FRAMES = 12`.
- `@dataclass Scene` with camelCase serialization via `to_dict()`.
- `frames_for(duration_sec, fps)` => `math.ceil(duration_sec * fps) + TAIL_PAD_FRAMES`.
- `build_spec(scenes, fps, width, height) -> dict` producing EXACTLY the camelCase
  JSON the Zod schema expects. This function is the only place that emits spec JSON.

### F. `msf/orchestrators/remotion_runner.py` — rewrite
- Import from `msf.spec`; never hand-roll spec dicts.
- Write spec to `remotion/public/video-spec.json` AND to a temp props file.
- Render with props ACTUALLY passed:
  `npx.cmd remotion render src/index.ts Main <out> --props=<abs path to props.json>
   --log=verbose --concurrency=4`
- `subprocess.run(cmd, shell=False, capture_output=True, text=True, encoding='utf-8')`.
  On non-zero exit, raise `RuntimeError` including the last 4000 chars of stderr.
- Copy every scene wav into `remotion/public/` and set `audioUrl` to the bare
  filename so `staticFile()` resolves it.

### G. `msf/engines/audio/mastering.py` — add final-mux mastering
Add `master_video_audio(in_mp4, out_mp4, target_lufs=-16.0)`:
ffmpeg `loudnorm=I=-16:LRA=11:TP=-1.5`, re-encode audio to AAC 192k, `-c:v copy`.
Raise on ffmpeg failure. Never swallow errors.

### H. `msf/graph/video_graph.py` — real QA + real self-correction
Rewrite completely.
- Nodes: `gate_check -> script_split -> voice_synthesis -> build_spec -> render -> master_audio -> qa -> (repair -> render | END)`.
- `node_qa` must perform REAL checks and be **fail-CLOSED** (any exception => fail):
  1. mp4 exists and size > 100 KB.
  2. `ffprobe` duration within 15% of expected (sum of scene frames / fps).
  3. `ffmpeg volumedetect` => `mean_volume > -50 dB`. **This is the check that
     catches the silence bug — it must exist.**
  4. Extract one frame at the MIDPOINT of every scene (compute offsets from the
     spec, do NOT hardcode n=15/45/75). Write to `<out>/qa_frames/`.
  5. For each frame compute stddev of pixel luminance via ffmpeg `signalstats`
     (or Pillow if available). Reject frames that are effectively blank
     (stddev < 3) — catches black/empty renders.
  6. If there is more than one scene, assert not all frames are byte-identical
     (catches "every scene renders the same thing").
  Populate `state['qa_report']` with a per-check dict of pass/fail + measured values.
- `node_repair` must CHANGE something before retry, based on the failure reason:
  - silent audio => re-copy wavs into public/ and re-assert audioUrl fields;
  - blank frames => swap that scene's preset to the safe fallback `HeroKinetic`;
  - duration mismatch => recompute durations from the actual wav files;
  and increment `retry_count`. Never retry with an unchanged spec.
- Max 2 repairs; if QA still fails, **raise RuntimeError with the qa_report** —
  never return a broken mp4 as success.
- `check_qa_decision` returns `end` only when `qa_passed` is truly True.

### I. Housekeeping
- Delete the stale `remotion/public/video-spec.json` demo content on each run.
- `remotion.config.ts`: keep jpeg + overwrite, add `Config.setChromiumOpenGlRenderer('angle')`
  for stable Windows GPU rendering.
- Do NOT break existing public APIs: `create_video(...)` and `build_msf_graph()`
  must keep working with the same call signature.

## ACCEPTANCE CRITERIA (all must hold)
1. Rendering with `text="Тест стилистики Pop Laboratory и Neo Brutalism."` produces a
   video whose frames show THAT Russian text — never "MOTION STUDIO"/"NEO-BRUTALISM".
2. Output mp4 `mean_volume` is between -30 dB and -8 dB (real speech, not -91 dB).
3. Output is 1080x1920 @ 60 fps.
4. Deliberately breaking the spec (e.g. empty scenes) makes the pipeline RAISE,
   not silently emit a demo reel.
5. `python -c "from msf.graph.video_graph import build_msf_graph; build_msf_graph()"`
   compiles clean.
6. No TypeScript errors: `npx tsc --noEmit -p remotion/tsconfig.json`.

Write real, complete, working code. No placeholders, no TODOs, no stubs.
