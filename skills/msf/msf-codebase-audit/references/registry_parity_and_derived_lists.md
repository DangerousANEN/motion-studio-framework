# Derived lists, registry parity, and the "plausible wrong answer" bug class

Read this before writing ANY Python list that names presets, effects, voices, graph
nodes, or audio assets — and before trusting a parser, lookup, or catalogue you just
wrote.

## The failure: a hardcoded mirror that drifts, silently

MSF declares scene presets once in `remotion/src/registry/*.ts`. Python needed the
same facts and got them by hand-written lists in `msf/graph/video_graph.py`. Measured
against the registry on 2026-08-12:

| Python list | held | registry says | consequence |
|---|---|---|---|
| `_TEXT_SAFE_PRESETS` | 5 | 13 rotation-safe | 8 finished presets could NEVER appear in a generated video |
| `_DATA_DRIVEN_PRESETS` | 11 | 25 data-driven | the 14 omitted were eligible for blind rotation → ⚠ placeholder |

Neither raised, logged, or looked wrong. The user's report was "агенты всё ещё
используют первые 5 сцен" — the symptom of a list, not of the agents.

`BankCard` was ALSO listed as data-driven in Python and not in the registry, so it was
excluded from rotation for a reason that no longer existed. Drift goes both ways.

**Rule:** never mirror the TS registry in Python. Parse it (`msf/registry.py`) and
derive every list from that. If a list must be narrower than the registry (see the
blocklist section below), express it as `registry_list − explicit_blocklist` so the
base still tracks the source.

## Verify the parser against node, or you have not verified it

`msf/registry.py` parses TypeScript with regexes — a deliberate trade so
`import msf.graph.video_graph` does not need node. The cost is that **a regex returns
FEWER results when formatting changes, and fewer is invisible.**

`tests/test_registry_parity.py` bundles the same TS with esbuild, runs it under node,
and diffs. Three bugs it caught, each of which "succeeded":

1. **Matched a doc comment.** `presets.ts` mentions `mergeRegistries()` in its header
   comment, with empty parens. `re.search(r"mergeRegistries\(([^)]*)\)")` found the
   COMMENT first → zero packs → **completely empty registry**, no exception.
   Fix: require a payload — `mergeRegistries\(\s*([^)]*?_PRESETS[^)]*?)\)`.
2. **Required `export`.** `effects.ts` declares `ENTRANCE_EFFECTS` / `EXIT_EFFECTS` /
   `EMPHASIS_EFFECTS` as module-private `const` and only exports the merged result.
   `^export const` matched none of them: 44 of 96 effects dropped.
   Fix: `^(?:export\s+)?const`.
3. **Required a key that one pack omits.** `effects_scene.ts` has no `family:` on any
   entry, so `if "family:" not in block: continue` dropped all 12 atmosphere
   overlays. Fix: per-section default family, and surface anything still unresolved
   as `"unknown"` plus a test that asserts the list is empty.

Also: `EffectStack.tsx` resolves `EFFECTS ∪ VISUAL_EFFECTS ∪ SCENE_EFFECTS`, so all
three packs are valid in a spec — reading only `effects.ts` under-reports by half.
`TRANSITIONS` lives in the same file but takes `SceneTransitionProps`; a transition
named in `scene.effects` is silently skipped with a console warning, so keep it in a
separate list.

**Never fall back to a short hardcoded list when the parse comes up empty.** A silent
fallback is how the library shrank to five presets. Prefer one obviously-degraded
entry plus a loud error, and assert non-emptiness in a test:

```python
assert len(registry.preset_names()) > 20, "the parse collapsed"
```

## `rotation_safe` does NOT mean "renders my text"

The registry's `dataDriven` flag answers "does this need structured data", which is
not the same question as "will this show the narration". Rendering all 13 rotation-safe
presets with ONLY `title` + `text` (exactly what rotation supplies) showed three
groups:

```
title AND text      QuoteCard, TypewriterSub
title only          HeroKinetic, GridGridFloor, TokenCloud3D,
                    MusicPlayer, VinylRecord, VoiceMemo, ModelOrbit3D
ignores both,       CountdownHero → "СТАРТ"
renders own demo    ScoreHud      → PLAYER 1 / СЧЁТ 9750 / КОМБО x3
data                SubscribeCTA  → TechChannel / 142.0K подписчиков
                    BankCard      → ALEXEY NIKITIN / ···· 4242
```

The third group is the dangerous one: convincing, fictional, unrelated to the script.
Auto-rotating them puts invented facts on screen — the exact failure `node_deep_research`
is fail-closed to prevent. They are in `_ROTATION_BLOCKLIST` with the measurement in
the comment, and remain available when a caller names them explicitly with data.
`ModelOrbit3D` is blocked for a different reason: no `modelUrl` means nothing to orbit.

**Method, not just the answer:** you cannot read this off a flag. Render the preset with
the props rotation actually supplies and LOOK at the frame.

## Row shape: the wrong-shaped item red-cards the ENTIRE video

`validate_spec` proved a list-valued field was PRESENT and stopped there. These are not
equivalent failures:

- missing list → one placeholder scene
- wrong item shape → Zod fails inside `Root.tsx` → the **whole video** becomes a red
  ERROR card, which renders to a real mp4 and can be uploaded

Found with `tokens: [{name, symbol, value, change}]` — plausible, accepted by every
Python check, and `value` is not `amount`, so all three rows failed `invalid_type`.

`msf/spec.py` now has `_ROW_SHAPES_HARD` (raise) and `_ROW_SHAPES_SOFT` (warn). The
split matters in both directions: treating a soft field as hard rejects valid specs;
treating a hard field as soft ships red cards. `tests/test_row_shapes.py` greps
`VideoSpec.schema.ts` for `.optional()` and fails if a field sits in the wrong table —
do not classify from memory.

Related trap in the same function: `_DATA_REQUIREMENTS` used `sc.get(k) is not None`,
which accepts `tokens: []` — an empty list renders exactly the empty chrome the guard
exists to prevent. Test truthiness, but exempt numeric zero so `statValue: 0` and
`health: 0` still validate.

## The "plausible wrong answer" bug class

Every bug in this file shares a shape: **the code succeeds and returns something
false.** No exception, no empty result, nothing that looks like failure. Collected
instances, all from reading real output rather than reasoning:

| Symptom | Cause |
|---|---|
| every music bed described as `""` | read `BedSpec.summary`; the fields are `character` / `use` / `bpm` / `key` |
| graph reports 0 nodes, all 10 node functions "unwired" | guessed the builder name `build_video_graph`; it is `build_msf_graph`. A `try/except AttributeError` turned a typo into a tidy wrong answer |
| every scene preview rendered at the same frame | passed `frame_pct` to `stress.mjs`, which reads `frame` (absolute). Unknown keys are ignored |
| literal `null` printed on the page | `Node.replaceChildren()` STRINGIFIES `null`; a conditional section passed as `null` renders as text |
| duplicate `media media` tag | pack name equals category name; also `ui_mock` vs `ui-mock` needs separator normalisation before comparing |

Defences that actually work:
- **Name candidates explicitly and error on empty.** `_GRAPH_BUILDERS = (...)` plus a
  500 when no candidate yields nodes, instead of a bare `except` returning `[]`.
- **Read the dataclass/interface before reading its fields.** `getattr(x, "summary", "")`
  is how an absent field becomes an empty string forever.
- **Assert on the parsed value, not on the call succeeding.** `status_code == 200` said
  nothing about whether `/api/graph` had found the pipeline.

## Panel as a view over the source

`msf/panel/` (FastAPI, `python -m msf.panel.server`, :8765) exists because the library
was invisible: 38 presets / 96 effects / 12 transitions / 38 SFX / 16 beds, all
discoverable only by reading TypeScript. That invisibility is what let five-preset
rotation and a wrong-gender voice run for weeks.

It is deliberately a **view**, never a second catalogue — scenes from `msf.registry`,
audio from `SFX_REGISTRY`/`MUSIC_REGISTRY`, voices via `describe_reference`, graph from
the `add_node()` calls, LDR from `deep_research`. Nothing to drift.
`tests/test_panel_api.py` asserts each endpoint against the registry modules rather
than against expected counts.

Previews go through the pipeline's own code paths (`stress.mjs`, `synthesize_voice_clone`,
`msf.audio`) — a panel with its own renderer makes "it looked fine in the panel"
meaningless. Scene previews run `validate_spec` FIRST, or a bad row shape displays a red
ERROR card as a working preview.

Operational notes worth keeping:
- Runs are **subprocesses** (`msf/panel/run_job.py`), not threads: the graph puts a 1.7B
  TTS model on CUDA and shells out to Remotion and ffmpeg. Progress is parsed from
  stdout (`[<node>] done`, `OUTPUT: <path>`, `ERROR: ...`).
- Drain that stdout on a **reader thread**. `readline()` on a blocking pipe waits, so
  polling from the request handler hangs the HTTP request for the whole quiet stretch of
  a render.
- No authentication; bound to 127.0.0.1. The preview endpoints run node/ffmpeg,
  `/api/graph/run` starts a render, `POST /api/voices` writes into the repo. Validate
  both path segments of any file-serving route against a whitelist AND check the resolved
  path stays inside the cache.
- On Windows, `subprocess.run(["npx", ...], shell=False)` raises WinError 2 — the
  executable is `npx.cmd`. Resolve with `shutil.which()` first and keep `shell=False`.
