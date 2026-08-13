# Vertical Scene Design — safe zones, scene taxonomy, variety architecture

Knowledge bank for the *content* side of 9:16 shorts: where pixels are allowed to
live, which scene types exist, and how to stop every video looking identical.
Companion to `remotion-ecosystem-catalogue.md` (which covers packages/APIs).

---

## 1. Safe zones — the defect that survives every technical check

A frame can pass `tsc`, Zod, ffprobe, volume and luminance checks and still be
broken, because **the platform draws its own UI over your video**. On 1080×1920
the handle, caption, sound row, like/comment/share rail and progress bar all sit
*inside* the frame.

Working budget for 1080×1920:

| Edge | Reserve | What lives there |
|---|---|---|
| Top | **280 px** | status bar, "For You / Following" tabs, back arrow |
| Bottom | **380 px** | @handle, description, sound title, progress bar |
| Right | **140 px** | like / comment / share / avatar rail |
| Left & right base | **80 px** | general breathing room |

Consequences worth internalising:

- The *readable* band is roughly `y ∈ [280, 1540]` — about **66 %** of frame
  height. Compose for that box, not for 1920.
- Anything narrative-critical (a stat, a punchline, a CTA) belongs in the middle
  third. The bottom third is decoration only.
- Burned-in captions must sit **above** 380 px from the bottom, otherwise the
  description overlaps them on TikTok/Reels.

### Pitfall: parallel, disagreeing margin definitions

Real case in an MSF-style pipeline — **three** independent sets, none correct:

| Location | Value | Reaches the renderer? |
|---|---|---|
| `remotion/src/VideoSpec.schema.ts` → `safeMargin` | `120` all sides | yes |
| `msf/libraries/typography_library.py` | `top 140, bottom 240, l/r 60` | **no — never imported by the graph** |
| what platforms actually need | `top 280, bottom 380` | — |

Every one of them under-reserved the bottom, so subtitles collided with the
platform UI on every single render while all automated checks stayed green.

**Rule:** exactly one `SafeArea` definition, exported from the schema module and
consumed by every scene. When auditing, `grep` for *all* margin/padding constants
before trusting the first one you find — a dead second definition is a strong hint
that someone already tried to fix this and wired it up wrong.

---

## 2. Chart readability on a phone

Vertical + small + ~2 s of screen time kills most desktop chart types. Judge by
"can this be read in one glance at phone size":

| Visualisation | Verdict on 9:16 | Note |
|---|---|---|
| Big number / counter | **excellent** | highest information-per-pixel |
| 2–4 comparison bars | **excellent** | more than 4 becomes noise |
| Progress ring / donut | **excellent** | one percentage, unmistakable |
| Gauge / speedometer | good | needs a large arc |
| Bar chart race | good | inherently animated, but ≤ 6 rows |
| Line chart | good | ≤ 2 series, thick strokes, label endpoints |
| Waterfall | fair | only if steps ≤ 5 |
| Timeline | fair | vertical scroll suits the format |
| Heatmap grid | poor | cell labels unreadable; use for texture only |
| Treemap | **avoid** | nested labels illegible |
| Scatter plot | **avoid** | reads as random dots |
| Multi-series table | **avoid** | never legible at phone size |

Sparse 3D point clouds fall into the same trap as scatter plots — they read as
noise unless density and lighting carry the shape.

---

## 3. Scene taxonomy — organise by narrative function

Rotating presets on a list gives sameness; picking a scene by **the job it does
in the narrative** gives variety for free. Eight functional categories:

| Category | Function | Examples |
|---|---|---|
| Opening / hook | interrupt the scroll in < 1.5 s | pattern-break glitch, red-alert terminal, bold claim |
| Text / typography | carry a statement | kinetic type, word-by-word captions, quote card, term+definition, myth/truth |
| Data / proof | make a claim credible | counter, bar compare, bar race, line, progress ring, gauge, waterfall |
| Comparison | before/after, us/them | split screen, swipe panels, overlay diff |
| Process / mechanics | explain how it works | flow diagram, numbered steps, layer walk-through |
| Code / terminal | show it is real | code reveal, terminal session, diff |
| 3D | depth for abstract concepts | embedding cloud, layer stack, node graph, data flow, camera flight |
| Close / CTA | convert attention | subscribe card, channel end-plate |

Two composition rules that matter more than any individual scene:

- **Contrast rule.** If scene *N* is flat text, scene *N+1* should have depth or
  motion. Two adjacent scenes from the same category read as a stall.
- **Pacing.** Change the visual (new scene, new angle, or a transform of the
  current object) every **1.5–2.2 s**. Longer than that on a static frame and
  retention drops.

---

## 4. Micro-primitives beat monolithic presets

Symptom of the monolith: a 164-line preset that hardcodes its layout, palette and
timing, so a new scene means a new 164-line file and nothing is reusable.

Split into a `primitives/` layer instead — `layout` (SafeArea, stack, grid),
`text` (fitted headline, kinetic word, caption), `shape` (badge, plate, arrow),
`chart` (bar, ring, line), `fx` (grain, light leak, vignette), `motion`
(entrance, parallax, camera). A scene becomes a 30–40 line composition.

Payoff: modifiers multiply instead of add — `theme × intensity × density ×
entrance × transition` yields many looks from one scene definition, and a fix to
text fitting lands everywhere at once.

Migration order that avoids breaking a working pipeline: build primitives →
port the *existing* scenes onto them and confirm frames are visually unchanged →
only then add new scene types.

---

## 5. Anti-sameness needs its own graph

Scene selection and script structure are different concerns from rendering. Keep
a separate script graph whose nodes are: research/facts → beat structure →
scene assignment → variety check → copy.

What actually removes sameness:

- **Variable beat count** (4–8), not a constant 5.
- **Several structural archetypes** (problem→solution, myth-bust, listicle,
  story, teardown, comparison, timeline, hot-take) chosen per topic.
- **Scene chosen by the beat's data type** — a beat carrying one number gets a
  counter, a beat carrying two options gets a split — instead of round-robin.
- **A fail-closed variety node**: reject the script if any scene repeats 3+ times
  or two adjacent beats share a category. Cheap to run, and it is the only check
  that catches "technically fine, visually monotonous".

Acceptance test: generate three videos on the *same* topic. If the scene sets and
beat structures are not visibly different, the variety layer is not working.

Facts feeding the copy node must arrive with sources attached, or the node will
confidently invent numbers that no research result contains.

---

## 6. Scene design doctrine — carriers, not illustrations

Learned by having a 48-scene catalogue *and* a follow-up 20-scene list rejected.
Both drafts failed the same two tests, so apply these before proposing any scene
list.

**Test 1 — is the scene a carrier?** A scene must accept arbitrary content and be
reusable across unrelated topics. Rejected as too narrow: `GaugeMeter` (one metric
on a dial), `TerminalType` (a shell session). Accepted: `CardScatter3D` (any cards,
any text, arranged in 3D), `ModelOrbit3D` (any `.glb`). Ask: *could this same
component carry two videos on incompatible subjects?* If no, it is a variant of a
broader scene, not its own entry.

**Test 2 — does each parameter change the frame visibly?** Rejected micro-flags:
`typoChance`, `punctuationPause`, `compressGaps`, `suffixWeight`. Granularity that
nobody will ever set is noise in the contract and extra surface for weak models to
get wrong.

**Style is five axes, not a palette.** Five existing themes that varied only colour
still felt identical. A style must set palette + typography + surface treatment +
motion character + grain together. Style stays orthogonal to scene, so `N` scenes ×
`M` styles multiply without new components.

Use `seed` to determinise anything "random" (particle layout, idle drift) so a
re-render reproduces the frame exactly.

---

## 7. One `motion` contract for every scene

Direct user requirement: *"во всех сценах должны быть плавные анимации, мягкие
интерполяции, умный агент должен иметь возможность гибко управлять интерполяцией."*
Roughly 30 scattered `*Ease` / `*Speed` / `*Curve` flags collapse into one object:

```ts
type Motion = {
  curve?: 'linear'|'ease'|'easeIn'|'easeOut'|'easeInOut'
        | 'spring'|'bounce'|'anticipate'|'overdamped'
        | [number, number, number, number];   // cubic bezier
  spring?: { damping?: number; stiffness?: number; mass?: number };
  duration?: number;   // frames
  delay?: number;      // frames
  stagger?: number;    // frames between sibling elements
  staggerFrom?: 'first'|'last'|'center'|'edges'|'random';
  loop?: 'none'|'pingpong'|'repeat';
};
```

Channels — `motion.camera`, `motion.value`, `motion.reveal`, `motion.transform`,
`motion.opacity`. Fallback chain: channel → scene-level `motion` → project default
(`easeInOut`, 24 frames, `spring{damping:14, stiffness:90}`).

Preset Refactor Pattern:
- **`reveal` channel**: Drives header / title entry and container reveals (`resolveMotion(motion, fps, 'reveal')`).
- **`transform` channel + `calculateStagger`**: Drives list items, panels, and card entrances with staggered delays (`10 + cardDelays[idx]`).
- **Absolute container layout (`position: 'absolute'; inset: 0`)**: Avoids zero-height collapse in flex children inside transition `OffscreenCanvas` wrappers while still using `getSafeArea` content positioning or `safeAreaPadding`.
- **Text auto-fitting (`fitOneLine` / `fitWrapped`)**: Sizes typography accurately by safe box bounds (`Math.min(safe.width, maxCardWidth)`) instead of hardcoding character length ladders (e.g. `len > 50 ? ...`).
- **Font Stack Consistency**: Module-scoped font constant (e.g., `HERO_FONT`, `GRID_FONT`) must be used for both `fitOneLine`/`fitWrapped` measurement and element CSS styles so glyph width calculations match rendered DOM.
- **Refactored Presets Reference**: all ten 2D presets are now on safeArea+motion and serve as canonical examples — `HeroKinetic`, `StatCounter`, `GridFloor`, `CompareSplit`, `FlowDiagram`, `CodeReveal`, `QuoteCard`, `DonutFill`, `BarCompare`, `TerminalType`. Read the nearest one before writing a new scene instead of inventing a layout.
  - *Migration is parallelisable*: one subagent per preset works well, but the final one always needs a manual pass — a batch of six left `QuoteCard` untouched while reporting success. Verify with `grep -L "getSafeArea\|resolveMotion" presets/*.tsx` rather than trusting the batch summary.
  - *Card width vs safe width*: a `900px` card inside a `920px` safe band puts its border and box-shadow outside the safe area. Derive card width from `safe.width` and subtract the visual extras (border, shadow spread), don't hardcode a number that "looks close".
  - *Side-by-side card split (`CompareSplit`)*: Derive column widths directly from `safe.width` minus fixed badge/gap reserves (`(safe.width - totalGapAndVS) / 2`).
  - *Staggered node flow (`FlowDiagram`)*: Combine `calculateStagger` with `resolveMotion(motion, fps, 'transform')` so node pop-in and connector line growth sequence naturally across safe box bounds.

**Linear is never a default.** `bounce` / `anticipate` only when set explicitly.

### Tie the guardrail to the contract

Level ≤ 2 agents get **only** an `intensity` enum that expands to a preset
(`calm` / `normal` / `punchy` / `extreme`); the raw `motion` object stays closed by
the validator. Same reasoning as the measured type-error findings in
`spec-validation-and-agent-guardrails.md` — weaker models emit bezier coordinates
outside `0..1`. Give them a safe enum rather than a free-form numeric contract.

### Two couplings that read as bugs when broken

- **Camera position and look-at need separate curves.** Sharing one curve makes the
  camera yaw while travelling between targets. The gaze must arrive *before* the
  position — give look-at a shorter `duration`.
- **A counter must share the curve of the shape it annotates.** Percent labels on a
  donut animated on a different curve than the arc fill visibly desynchronise from
  the geometry. Verify at **mid-animation**, not just the final frame: a shared
  curve and two different curves both land on the same endpoint, so only the
  middle exposes the desync. Measured on a working `DonutFill` at frame 30 —
  legend `42/16/10`, arcs `42.5/16.6/10.5` (≤0.6 pp, the residue of rounding
  counters to integers).

- **`strokeLinecap: 'round'` silently widens every arc.** A round cap adds a
  half-disc of radius `strokeWidth/2` at *each* end, so an arc drawn on radius `r`
  covers an extra `degrees(strokeWidth/2 / r)` per side. Real numbers: `stroke 120`
  on `radius 400` → **+8.6° per side, +17.2° per segment**. With `gapAngle: 2`
  the caps swallowed the gaps entirely (measured total 359.9° of 360°) and inflated
  the smallest slice from a declared 14 % to a rendered 18.8 % — the legend and the
  geometry disagreed while every automated check passed.

  Subtract the cap from the arc length and re-centre it in its sector:

  ```ts
  const capDeg = (strokeWidth / 2) / radius * (180 / Math.PI);
  const drawnSweep = Math.max(0, sectorSweep - gapAngle - 2 * capDeg);
  const startAngle = sectorStart + gapAngle / 2 + capDeg;
  ```

  After the fix: declared `62/24/14` → measured `61.7/24.0/14.4`. **Measure arcs
  in pixels** (sample along the ring, bucket by angle) rather than trusting the
  `stroke-dasharray` you computed — the bug lives precisely in the gap between
  intended and painted geometry, so re-reading your own arithmetic cannot find it.
  Use `butt` caps whenever segments must sum exactly.

---

## 8. Sourcing 3D models programmatically

For scenes that orbit a real downloaded model. **Search working is not evidence
that download works** — verify the download endpoint separately before promising a
feature built on it.

Measured with `curl -o /dev/null -w "%{http_code}"`:

| Source | Result | Usable without credentials |
|---|---|---|
| Khronos `glTF-Sample-Models` | `200`, 104 models under `2.0/` | yes |
| Khronos `glTF-Sample-Assets` | `200` on direct `.glb` | yes |
| Quaternius, Kenney (CC0) | `200` | yes |
| Sketchfab `/v3/search` | `200` — search works | search only |
| Sketchfab `/v3/models/<uid>/download` | **`401`** | needs OAuth |
| Poly Pizza `/v1.1/search` | **`401`** | needs API key |

Design a `ModelProvider` interface with keyless providers as the default and
token-gated ones opt-in. Cache to `assets/models/<provider>/<id>.glb` so renders
don't refetch.

Confirmed again on a later session (Khronos `glTF-Sample-Assets`, direct `.glb`):
`DamagedHelmet` 3 773 916 B, `Avocado` 8 110 040 B, `BoomBox` 10 614 184 B, all
with a valid `glTF` magic. Keep `glTF-Sample-Models` (legacy, `2.0/<Name>/…`) as a
fallback URL — some names exist in only one of the two repos.

Three implementation details that matter more than the provider list:

- **Download to `<name>.glb.part`, validate, then `replace()`.** A partial file
  left at the cache path is indistinguishable from a good cache hit on the next
  run, so one interrupted download poisons every later render. Validate magic +
  a minimum plausible size *before* the rename, never after.
- **Remotion renders each frame in a separate worker.** An uncached URL is
  re-fetched many times for one video, and a moved upstream file makes an old
  render irreproducible. This — not politeness — is why the cache is mandatory.
- **Prove "offline" rather than asserting it.** Monkey-patch the fetch entry
  point to raise, then resolve again; a real cache hit still succeeds:

  ```python
  real = urllib.request.urlopen
  urllib.request.urlopen = lambda *a, **k: (_ for _ in ()).throw(
      AssertionError("network used despite a warm cache"))
  try:
      m = resolve_model("khronos:DamagedHelmet")   # must come from cache
  finally:
      urllib.request.urlopen = real
  ```

  Measured: cold 1.44 s, warm 0.001 s, offline resolve OK. Also assert the error
  paths (unknown provider, missing `provider:` prefix, 404 name, and an HTML page
  fetched via `url:` — the last must be *rejected*, not cached).

Note `require.resolve('three')` **fails** even when three is installed and
working: `three/package.json` is not in the package's `exports` map. Probe with
`require('three').REVISION` instead — a failed resolve here is not a missing
dependency.

### Validate a GLB before wiring it into a scene

A truncated download or an HTML error page still lands as a `.glb` and renders
blank. Parse the 12-byte header:

```python
import struct
d = open('m.glb', 'rb').read()
magic, ver, length = struct.unpack('<III', d[:12])
assert d[:4] == b'glTF' and length == len(d), 'corrupt or truncated GLB'
```

### Dependency compatibility

`three@0.169` already ships `GLTFLoader`
(`three/examples/jsm/loaders/GLTFLoader.js` resolves) and `THREE.Box3` for
auto-framing the camera to model bounds. `@react-three/drei` is a **separate
install**, required for `useGLTF`, environment maps and contact shadows. With
`@react-three/fiber@8` the last compatible release is **`@react-three/drei@9.x`** —
the 10.x line requires r3f v9. Check the r3f major before installing drei.
