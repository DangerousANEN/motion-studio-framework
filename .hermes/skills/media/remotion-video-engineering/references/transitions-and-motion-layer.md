# Transitions & the shared motion layer

Everything below was established by running commands against
`@remotion/transitions` **4.0.507** and reading rendered pixels — not from docs.

---

## 1. The count is 19 entry points, not 20

`ls node_modules/@remotion/transitions/dist/presentations/` shows 20 `.js` files,
but one (`upload-element-image`) is not a scene transition. `package.json`
`exports` is the honest list — **19** subpath exports, of which `none` is a
deliberate no-op:

```
fade  slide  wipe  flip  clock-wipe  book-flip  zoom-blur  dreamy-zoom
film-burn  linear-blur  zoom-in-out  none  iris  dissolve  ripple
crosswarp  cross-zoom  swap  push-cut
```

Verify rather than trust any prose (including this file):

```bash
node -e "console.log(Object.keys(require('@remotion/transitions/package.json').exports))"
```

Export name is camelCase of the file name: `clock-wipe` → `clockWipe`.

---

## 2. Constructor signatures differ per presentation — three shapes

`tsc` catches all of this, so compile after wiring each one. The traps:

| Shape | Members | Call |
|---|---|---|
| Optional props | `fade`, `slide`, `wipe`, `flip`, `pushCut`, `none` | `fade()` / `slide({direction})` |
| **Required** props object | every shader-backed one: `dissolve`, `ripple`, `crosswarp`, `crossZoom`, `swap`, `linearBlur`, `zoomInOut`, `dreamyZoom`, `filmBurn`, `zoomBlur`, `bookFlip` | `dissolve({})` — **omitting `{}` is a compile error** |
| Required geometry | `iris`, `clockWipe` | `iris({width, height})` |

- **`pushCut` has no `direction`.** It is a scale/flash cut. Passing `direction`
  fails type-check.
- Shader presentations export **two** symbols: `dissolveShader` (an
  `OffscreenCanvas` factory) and `dissolve` (the React presentation). You want
  the unsuffixed one.
- Each presentation is generic over its own props type and they are mutually
  incompatible (`IrisProps` needs width/height; `CrosswarpProps` is
  `Record<string, never>`). A `Record<string, unknown>` return type will not
  typecheck. Use `TransitionPresentation<any>` for the factory's return and let
  each `case` validate its own props.

**Shader transitions do render in headless Chrome without a GPU.** Measured over
a 456-frame render exercising 11 transitions: minimum frame YAVG was 15.81, zero
frames below 8. Do not pre-emptively avoid them on a black-frame assumption.

---

## 2b. The DOM/shader split — the single most useful diagnostic here

Every presentation takes one of two rendering paths, and **which path a bug
follows tells you where the bug is**. Classify them from the source, not memory:

```bash
cd node_modules/@remotion/transitions/dist/presentations
for f in *.js; do
  grep -q "html-in-canvas-presentation" "$f" \
    && echo "${f%.js}  HTML_IN_CANVAS" || echo "${f%.js}  dom"
done
```

At 4.0.507:

| path | presentations |
|---|---|
| **DOM** (plain CSS compositing) | `fade` `slide` `iris` `wipe` `clockWipe` `flip` `pushCut` `none` |
| **HTML-in-Canvas** (rasterised through `<canvas layoutSubtree>` + `captureElementImage`) | `ripple` `crosswarp` `filmBurn` `swap` `bookFlip` `zoomBlur` `linearBlur` `dreamyZoom` `zoomInOut` `crossZoom` `dissolve` |

Read the result like this:

- **Breaks on shader only, DOM fine** → a **container-sizing** bug in your scene
  wrapper (§11.5). The canvas subtree doesn't establish a containing block, so
  `inset: 0` / `flex: 1` collapse to zero. Not a preset bug — do not bisect
  presets, do not ablate CSS properties.
- **Breaks on both** → your preset, spec, or bundle.
- **Breaks on DOM only** → z-index / stacking context (§4).

A 2×2 matrix of {suspect preset, known-good preset} × {shader, DOM} localises
this in four stills. Real numbers from one session:

```
StatCounter + ripple    YMAX  29   HeroKinetic + ripple  YMAX 158
StatCounter + fade      YMAX 235   HeroKinetic + fade    YMAX 158
```

Reading that correctly ("shader+anything is blank → wrapper") ends it. Reading it
as "StatCounter is broken" leads to ablating `radial-gradient`, `boxShadow`,
`textShadow`, `fitOneLine`, `fitWrapped`, then replacing the whole component with
a solid red `div` — which was **still black**, because the wrapper was always the
problem. When a minimal replacement still fails, the fault is *above* the thing
you replaced; move up a level instead of further down.

`HtmlInCanvas.isSupported()` is worth one check before going deeper, but note it
returned `true` here (Chrome 149, `drawElementImage`/`requestPaint`/
`captureElementImage` all functions) — support was never the issue, and neither
was `--gl` (`angle`/`swangle`/`egl`/`swiftshader` all measured YMAX 29).

---

## 3. `TransitionSeries` shortens the timeline — the audio-desync trap

A `<TransitionSeries>` is **shorter** than the sum of its scene durations: every
`<TransitionSeries.Transition>` overlaps the outgoing and incoming scene and
consumes `timing` frames from the timeline.

A pipeline that lays one continuous voice-over over the whole video will desync
on every scene after the first transition, and lose the tail of the narration,
if the composition duration is still a plain sum.

**One planner, three consumers.** Compute the plan once and let everyone read it:

```ts
export const getTransitionPlan = (scenes: PlanScene[]): TransitionPlan => {
  const transitions: PlannedTransition[] = [];
  let overlapFrames = 0;
  const sumScenes = scenes.reduce((a, s) => a + s.durationInFrames, 0);

  for (let i = 1; i < scenes.length; i += 1) {      // i starts at 1 — see below
    const config = scenes[i].transition;
    if (!config || config.type === 'none') continue;

    const requested = config.durationInFrames ?? DEFAULT_TRANSITION_FRAMES;
    // Keep >=1 frame of each neighbour outside the overlap, or Remotion throws.
    const maxAllowed = Math.max(0,
      Math.min(scenes[i - 1].durationInFrames, scenes[i].durationInFrames) - 1);
    const durationInFrames = Math.min(requested, maxAllowed);
    if (durationInFrames <= 0) continue;

    transitions.push({ beforeSceneIndex: i, config, durationInFrames });
    overlapFrames += durationInFrames;
  }
  return { totalDurationInFrames: Math.max(1, sumScenes - overlapFrames),
           overlapFrames, transitions };
};
```

- `Root.tsx` uses `totalDurationInFrames` for `<Composition durationInFrames>`.
- `Main.tsx` uses `transitions` to lay out the series.
- The **Python** spec builder must mirror it so `durationInFrames` in the emitted
  spec, and any post-render duration QA check, agree. A QA check that sums scene
  durations will fail every video that has crossfades.

Semantics worth fixing early: a transition belongs to the scene it runs
**before**, so index 0 can never carry one. Reject it in the validator with a
message that says where to move it, rather than silently ignoring it.

**Clamp, don't throw.** A slightly shorter wipe beats a failed render.

### Parity test — run the real TS, don't re-read it

Two implementations of the same arithmetic will drift. Test them against shared
fixtures by executing the actual TypeScript through the project's own esbuild:

```python
entry.write_text(
    "import { getTransitionPlan } from './src/lib/transitions';\n"
    f"const cases = {json.dumps(fixtures)};\n"
    "console.log(JSON.stringify(cases.map((s:any) => {\n"
    "  const p = getTransitionPlan(s);\n"
    "  return {total: p.totalDurationInFrames, overlap: p.overlapFrames};\n"
    "})));\n")
subprocess.run([esbuild, entry, "--bundle", "--platform=node",
                "--format=cjs", f"--outfile={bundle}"], check=True)
ts = json.loads(subprocess.run(["node", bundle], capture_output=True,
                               text=True, check=True).stdout)
```

Import only the **pure planner**. Pulling in the presentation factory drags React
and the whole transitions package into a plain node process.

Fixtures that actually catch bugs: no transitions; default duration; explicit
duration; `type: 'none'`; a transition longer than its shortest neighbour (clamp);
a transition illegally on scene 0; many scenes mixed; a single scene.

Pin the arithmetic too (`120 + 90 - 18`), so a *coordinated* change to both sides
still fails the test.

---

## 4. The stacking-context bug — transitions that composite but look like cuts

**Symptom.** Transitions are wired correctly, the plan is right, the render has
exactly the predicted frame count — and the picture still hard-cuts.

**Cause.** Presets commonly put `zIndex: 5` on a foreground card so it sits above
their own background layer. `z-index` only competes *within a stacking context*,
and the transition wrappers do not create one, so those cards get promoted into
the **composition** stacking context. During the overlap the outgoing scene's
card therefore paints on top of the incoming scene, which is fully opaque behind
it. The blend is happening; it is being covered.

**Diagnosis that isolates it in one render pair.** Render the same cut with a
preset that leaks `zIndex` and one that does not:

```
HeroKinetic → StatCounter  (outgoing leaks z-index) : biggest single-frame
                                                      delta = 80% of range
StatCounter → StatCounter  (neither leaks)          : biggest delta = 16%
```

**Fix — one wrapper, not N preset edits.** In the scene dispatcher:

```tsx
export const SceneDispatcher: React.FC<Props> = (props) => (
  <div style={{ flex: 1, display: 'flex', isolation: 'isolate' }}>
    <ScenePreset {...props} />
  </div>
);
```

`isolation: 'isolate'` forces a stacking context per scene, keeping each preset's
z-indices local. Leave a comment saying why — it looks like a no-op wrapper and
is exactly the kind of thing a later cleanup pass deletes.

Find candidates with `grep -rn "zIndex" src/presets/`.

---

## 5. How to prove a transition actually composites

Do not judge blending by eye or by a single summary statistic.

**Frame-average is dominated by the shared background.** Both scenes sit on the
same dark canvas, so whole-frame `UAVG` moved by only 0.36 across a fade that
should have been obvious. Cropping to the card region can be worse — the incoming
card is still scaled small, so the crop is mostly background from both scenes.

**The reliable metric: largest single-frame delta as a share of total range.**

```bash
ffmpeg -v error -i out.mp4 \
  -vf "signalstats,metadata=print:key=lavfi.signalstats.VAVG:file=-" \
  -f null - 2>&1 | grep -o 'VAVG=[0-9.]*' | cut -d= -f2
```

Use the channel that separates the two scenes' accent colours (`VAVG` for
red-vs-green, `UAVG` for blue-vs-yellow). Then:

- **Hard cut** → one frame carries ~80–90 % of the full range.
- **Real blend** → change spreads across the overlap; largest delta ≲ 20 %.

**A/B against `none` is the decisive control.** Render the identical spec twice,
once with the transition and once with `{"type": "none"}`. If the frame where the
jump lands is unchanged (e.g. still exactly at the end of scene A's full
duration), the transition is not compositing regardless of what the plan says.

**Confirm the component is even executing** before deep-diving the visuals — a
`console.log` in the composition surfaces in `--log=verbose` render output as a
`chrome [...] CONSOLE` line:

```
chrome [...] "[MSF-DEBUG] scenes=2 plannedTransitions=1 overlap=24 total=96"
```

Remember to remove it afterwards.

---

## 6. Vision vs numeric probes — pick the right instrument

Vision analysis gave a **confidently wrong** verdict here: asked to judge 11
transitions from a tiled contact sheet, it reported 7 of them "NOT WORKING /
CLEAN FRAME". Two compounding reasons:

1. `select` renumbers frames **before** `tile`, so computed frame offsets no
   longer correspond to the labels reasoned about. Sampling *N* frames into a
   grid loses the frame-index mapping.
2. Semi-transparent compositing is genuinely hard to judge from a still.

Calibration that held up:

- **Layout, legibility, overflow, "is this an error card", text clipping →
  vision.** It correctly caught a code line running past its window.
- **Blending, opacity, precise timing, "did this composite" → numeric pixel
  probes.** `signalstats` per frame, no tiling.

When a vision verdict contradicts a measurement, re-derive the measurement — but
do not discard it in favour of the narrative. Here the numbers were right and
also revealed the *real* bug (§4) that vision had attributed to the wrong cause.

---

## 7. Motion layer — verified Remotion API behaviour

- **`measureSpring()` returns a `number`**, not an object. `const {durationInFrames} = measureSpring(...)`
  fails with `Property 'durationInFrames' does not exist on type 'Number'`. Its
  `config` param is `Partial<SpringConfig>`, so a full `SpringConfig` literal is
  not required.
- **`Object.keys(Easing)` returns `[]`.** `Easing` is a *function* with static
  members; the keys are non-enumerable. Probe members directly
  (`typeof Easing.bounce`) instead of concluding they don't exist. Confirmed
  present: `linear ease in out inOut bounce bezier elastic poly step0 step1 back
  circle cubic exp quad sin`.
- **`extrapolateRight: 'clamp'` destroys spring overshoot.** An under-damped
  spring returns progress > 1 mid-flight; clamping the `interpolate` output
  flattens it back to the target and silently removes the bounce. Extrapolate
  freely unless the caller asked for `overshootClamping`. With the fix a spring
  peaked at 129 on a 0→100 range.
- **`Easing.bounce` does NOT overshoot** — measured range over `[0,1]` is
  `0.0 → 0.9999`, dipping mid-flight (`0.91 → 0.77 → 1.0`) like a ball settling
  on a floor. It is *non-monotonic*, not overshooting. Assert it for backward
  steps, and keep it clamped. `anticipate` is the one that genuinely leaves the
  band on both ends.
- **Custom bezier: x controls are time, y controls are not.** Bound `x1,x2` to
  `[0,1]`; allow `y1,y2` outside it — that is exactly how an author requests
  overshoot (`[.34, 1.56, .64, 1]`). Enable right-extrapolation when a y control
  leaves `[0,1]`.
- Clamp the **displayed** value of an animated counter even when the card's scale
  is free to overshoot, or a spring shows a number above its target.
- `stagger` from `center` and from `edges` produce identical arrays at odd item
  counts and differ only at even ones. Verify across 4/5/6/7 before calling it a
  bug.

Numeric probe worth keeping: for each curve assert start = `from`, end = `to`,
finite everywhere, monotonic curves stay in range, and max per-frame delta stays
small (a smooth curve over 60 frames covering 100 units peaks ~2.8 units/frame;
linear is 1.67).

---

## 8. zod version conflict with `@remotion/studio`

`@remotion/studio` and `@remotion/studio-server` **pin zod 4.x**. A project on
zod 3 prints a version-mismatch block on *every* render. It is only a warning,
but it buries real errors in render output.

**Removing `@remotion/zod-types` does not fix it** — that was the wrong
hypothesis. Find the actual source:

```bash
npm ls zod
# └─┬ @remotion/cli
#   ├─┬ @remotion/studio-server → zod@4.4.3
#   └─┬ @remotion/studio        → zod@4.4.3
# └── zod@3.25.76
```

Before upgrading, prove the schema survives zod 4 **at runtime**, not just in
`tsc` — v4 changed `.record()` (now requires two args) and deprecated
`.passthrough()`. Install zod 4 into a scratch dir, copy the schema in, and
assert: `.strict()` still rejects unknown keys, `.passthrough()` still *preserves*
them, and the real production spec files still parse. Then:

```bash
npm i zod@4.4.3 --save-exact     # exact, so the dedupe holds
npm ls zod                        # all three lines should say "deduped"
```

---

## 9. Two more silent-failure guards

**Closed enums must be validated on the Python side.** An unknown `theme`
(`"midnight"` for a set of `pop|noir|glass|blueprint|sunset`) passes every Python
check, fails Zod inside `Root.tsx`, and degrades the whole render to a 2-second
red ERROR card — with exit code 0 and a plausible MP4. Validate against a
constant, raise with the offending value *and* the valid set, and add a parity
test that parses the TS source so the two lists cannot drift:

```python
match = re.search(r"export\s+const\s+THEMES\s*:\s*Record<[^>]*>\s*=\s*\{([^}]*)\}", src)
ts_themes = {p.split(":")[0].strip() for p in match.group(1).split(",") if p.strip()}
assert ts_themes == set(THEMES)
```

Cover `""` and `"Pop"` — Zod is case-sensitive, and an empty string is a caller
bug, not a request for the default.

**A validator must resolve its own assets from its own directory.** The spec
validator bundled the schema from `process.cwd()`, so it worked from
`remotion/` and crashed from the project root — reporting **every** spec as
`INVALID`, including specs that had just rendered successfully. Use
`dirname(fileURLToPath(import.meta.url))`. A validator that emits false INVALID
is worse than no validator: it trains you to ignore it.

---

## 10. Windows / MSYS notes for this loop

- **ffmpeg here is a native Windows binary and cannot open MSYS paths.**
  `/c/Users/...` fails with "No such file or directory" even though the file
  exists. Pass relative paths (after `cd`) or native `C:\...`.
- `drawtext` needs fontconfig and segfaults without it. Build labelled contact
  strips with `hstack`/`tile` and keep the labels in the prompt instead.
- Remotion resolves a relative `--output` against the **Remotion project dir**,
  not the shell's cwd, so `../audit/x.mp4` from `remotion/` lands where you
  expect but a bare `audit/x.mp4` does not.

---

## 11. Probe hygiene — validate the probe before trusting the result

§5 gives the right metric. This section is about the probe *around* it. One
session produced four consecutive wrong root causes ("shader transitions are
broken", "`StatCounter` collapses", "HTML-in-Canvas is unsupported", "`Main.tsx`
was reverted") — every one traced back to a probe that was not measuring what it
claimed. Run these checks in order; each is seconds and kills a whole class of
phantom.

**1. Frame count is the cheapest oracle for "is the transition applied at all".**
`total == sum(durations)` means zero overlap, so no transition is in the series —
stop and fix the wiring before touching pixels. Measured: 144 frames for
`72 + 72` with a 24-frame transition; correct is 120. Bonus tell: `fade`,
`dissolve` and `none` produced **byte-identical** output.

**2. Hand-written probe specs bypass the Python validator.** They go straight to
`--props`, so a closed-enum typo (§9) renders the red ERROR card and every pixel
statistic then describes *that card*. Signature of this failure: the video is
static — per-frame mean identical to one decimal across all 120 frames
(`84.9` everywhere), max delta `0.00`, `d(f0,f44) = 0.01`. **A zero range or a
static video means you are measuring an error card, not a transition.** Cost of
skipping this: ~15 renders and six wrong conclusions. Either run the same Zod
pre-flight on probe specs, or read one frame with `vision_analyze` first — the
card names the bad field and the valid set verbatim.

**3. A/B distance is a precondition, not an output.** Normalised blend metrics
divide by the distance between the two scenes, so visually similar endpoints give
`range 0.0` and a `ZeroDivisionError`. `StatCounter → StatCounter` is degenerate;
`HeroKinetic → StatCounter` measured `AB_dist 11.8`. Assert a floor on `AB_dist`
and print it, so a degenerate pair reports itself instead of crashing or
returning a confident zero.

**4. Confirm the bundle is fresh.** `tsc --noEmit` must exit 0 **before** you
render. A render started while an import is broken silently reuses the previous
bundle, so you measure old code — this is what produced the phantom "blank scene"
readings that were then blamed on layout.

**5. Scene wrapper: `inset: 0` alone collapses inside a shader transition.**
*(Resolved — this supersedes an earlier note here that called the cause
inconclusive.)* A wrapper styled `{position:'absolute', inset:0}` renders fine
under DOM transitions and produces a **fully black frame** under every
shader-backed one. The canvas subtree that HTML-in-Canvas rasterises into does
not establish the containing block an absolutely-positioned child resolves
`inset` against, so the box resolves to zero size. Nothing throws; the render
reports success.

Add explicit dimensions alongside the inset:

```tsx
<div style={{ position:'absolute', inset:0, width:'100%', height:'100%',
              display:'flex', flexDirection:'column', isolation:'isolate' }}>
```

Measured on frame 20 of a two-scene spec differing only in transition name:

| wrapper style | YMAX |
|---|---|
| `inset: 0` alone | 29 (blank) |
| `inset: 0` + `width/height` | 220 (renders) |

`flex: 1` fails the same way and for a related reason — `TransitionSeries.Sequence`
is not a flex container. Either way the giveaway is **the split in §2b**: DOM
transitions fine, shader transitions black. That pattern is a *container-sizing*
bug, never a preset bug, so stop bisecting presets the moment you see it.

**6. `dissolve` is a cut, not a blend — do not ship it.** Two separate defects:

*Red flash.* It is a burn effect; `spreadColor` defaults to `#ff0000`, so a
saturated frame appears mid-transition (measured VAVG 181.9 on a dark theme),
close enough to the red-error-card heuristic to confuse both probes.

*It never blends.* The gl-transitions shader derives a per-pixel threshold from
the **outgoing** scene's luminance and hard-swaps each pixel — the two scenes are
never mixed:

```glsl
float burn = 0.5 + 0.5 * luma(from);
float show = burn - progress;
if (show < 0.001) return to;   // hard per-pixel swap, no mix()
```

Scenes made of large near-uniform luma areas cross the threshold on the same
frame, so it degenerates to a cut. **A longer overlap makes it worse, not
better** — the earlier advice here to "give it a longer window" was wrong:

| overlap | worst single-frame share |
|---|---|
| 24 frames, HeroKinetic | 99.0 % |
| 48 frames, HeroKinetic | 99.0 % (active window shrank to 2 frames) |
| 48 frames, textured GridFloor | 91.9 % |

Frame-by-frame: A fully opaque at f22, B fully opaque at f23. No parameter tunes
this away. Remove it from the registry rather than leaving a trap-shaped option
in the enum, and leave a comment at the old `case` explaining why so it does not
come back. Use `fade` for a real blend, or `filmBurn` when the fiery look is
actually wanted.

**6b. Re-probe `fade` before relying on that advice — in MSF it also cut.** A later
session in the same repo probed a two-scene spec with `{"type":"fade","durationInFrames":30}`
and found scene B's title **fully opaque at frame 80**, ten frames *before* scene A's
90-frame duration ended, with no frame anywhere showing both titles. Sampled f10/f30/f60
showed A, f80/f90/f96 showed only B. So the whole transition layer in that project was
still cutting, `fade` included, and §6's "use `fade` for a real blend" did not hold there.

Root cause not yet isolated (§4's stacking context and §11.5's container sizing are both
live candidates). Until it is, the practical rule for that project:

- **Carry the motion in per-scene `effects`**, not transitions — `ZoomPunch`, `GlitchRgb`,
  `ParticlesSparks`, `DollyIn`, `ElasticPop`, `SlideInUp` all composite correctly and give
  a cut its energy without depending on the transition layer.
- Combine with a **per-scene style kit** so the palette changes on every cut; that reads as
  deliberate editing rather than a missing blend.
- Do not design a script around a blend you have not just measured. One two-scene probe with
  distinct titles costs one render and settles it.

Naming trap found in the same pass: `transition.type` takes **lowercase transition
identifiers** (`fade`, `slide`, `wipe`, `iris`, `crossZoom`, `dreamyZoom`, `zoomBlur`,
`bookFlip`), *not* effect-registry names. Passing `CrossFade` — a real effect, wrong
namespace — invalidates the spec, and the render then exits 0 with an error card. `dissolve`
is also absent from that project's enum, having been removed per §6.


**7. `git checkout -- <file>` discards uncommitted work in that file.** Used to
repair one broken file, it silently reverted `Root.tsx` to the naive duration sum
(§3) and cost a re-debug. Commit each layer the moment its tests go green.

**Related silent failure — config loaders that ignore unknown keys.** A
`_section_from_dict`-style loader that filters YAML down to known dataclass
fields drops a misspelled key without a word (`voice:` silently vanished; the
field was `speaker`), so the file *looks* like it configures something it never
touched. Same family as the closed-enum trap: prefer strict parsing, or at
minimum warn on unconsumed keys.
