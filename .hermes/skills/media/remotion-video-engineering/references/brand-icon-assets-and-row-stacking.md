# Brand logo assets in presets, and the row that had to be stacked

Two intertwined lessons from replacing letter avatars with real model logos in
`Leaderboard`, plus the measuring habits that stopped four "fixes" from shipping
their own defects.

Companion to `chart-and-widget-visual-design.md` (§1c-bis/§1f/§1g), which covers
the *first* half of this row's history: the `flex: 1` name column that collapsed
to zero width, `label` silently ignored as an alias for `name`, and rank badges
making sort order a correctness claim. This file picks up where that ends.

---

## 1. Vendor brand icons: `@lobehub/icons-static-svg`

`npm i -D @lobehub/icons-static-svg` ships ~900 SVGs in `node_modules/@lobehub/
icons-static-svg/icons/`. Naming: `<brand>.svg` (monochrome) and
`<brand>-color.svg` (full colour). Verify presence before writing a mapping —
several obvious names do **not** exist:

| want | reality |
|---|---|
| `glm`, `glm-color` | absent. `glmv` is a *different product*. Use `zhipu-color` — GLM is Zhipu's family. |
| `openai-color`, `grok-color` | absent. Only monochrome `openai`, `grok`, `xai`, `anthropic`, `microsoft`. |
| `llama` | absent as a brand mark. Use `meta-color`. |

### 1a. Copy into `public/`, never import from `node_modules`

Remotion resolves `staticFile()` against `public/` only. Referencing
`node_modules/...` from a component **works in the dev bundler and 404s in a
rendered still** — green locally, blank logos in the delivered MP4. That is the
worst failure shape available, so make the asset correct by construction with a
sync script (see `scripts/sync_model_icons.mjs` in this skill).

Curate the list. Copying all 900 puts 4.3 MB of unused SVG — including text
lockups that read as noise at avatar size — into every render bundle.

### 1b. `currentColor` inside `<img>` resolves to BLACK

Roughly a fifth of the vendor icons paint `fill="currentColor"` (measured: 8 of
42 in the curated set — `openai`, `grok`, `xai`, `anthropic`, `ollama`, `yi`,
`aws`, `cerebras`). Inside an `<img>` there is no inherited colour to resolve
against, so the browser falls back to black: an **invisible logo on a dark
backdrop, with no error anywhere**. A component cannot fix this, because it
cannot pass a colour into an `<img>`. Rewrite it at copy time:

```js
svg = svg.replaceAll('currentColor', '#FFFFFF');
svg = svg.replace('height="1em"', 'height="24"').replace('width="1em"', 'width="24"');
```

`1em` is equally meaningless in an `<img>` — the asset needs its own viewport.

### 1c. Match the brand SUBSTRING, not the exact name

Nothing upstream emits canonical vendor slugs. Labels arrive as whatever the
script or the research node produced: `Qwen3.6-235B-A22B`, `GLM-5.2-Air`,
`Llama-4-Scout-109B`, `claude opus 4.6`. A dictionary keyed on exact names misses
the next release and **silently degrades to a letter avatar**, which reads as a
deliberate design choice rather than a miss. Regex on the lower-cased label
survives version bumps: `Qwen4-Max` resolves the day it ships.

Rule order is load-bearing — first hit wins, so specific before generic:

* `claude` before `anthropic` (the model name is what's on screen).
* `llama` before a bare `\bmeta\b`.
* `\bglm\b|glm\d|zhipu` before anything that could swallow short tokens.

**Return `null` for unrecognised names.** The caller already has a good fallback
(gradient letter avatar); inventing a generic "AI chip" glyph would make an
unknown model look identified. Human names (`Aria Chen`) must hit this path.

### 1d. Put every logo on a common neutral disc

Brand marks differ wildly in shape and weight — Qwen is a dense purple glyph,
OpenAI a thin white monoline, Mistral a wide flat block. Dropped straight onto
the backdrop they read as different sizes and the column looks ragged. A shared
`borderRadius: '50%'` disc with `rgba(255,255,255,0.10)` fill, a hairline border
and `padding: size * 0.18` normalises silhouette and optical weight.

### 1e. Three things break silently, so assert all three

`tests/test_model_icons.py` (stdlib `unittest` + esbuild + node, matching
`test_transition_parity.py` — the project has no vitest) checks:

1. the label → slug mapping over **real pipeline strings**, version-bump
   resilience (`Qwen7-Ultra-2030`), rule ordering, and the null contract;
2. every slug referenced by the rules having a file in `public/model-icons/`;
3. no icon left containing `currentColor` or `="1em"`.

Bundling the resolver needs a stub, because `staticFile()` wants a
bundler/browser context: `--alias:remotion=./tests/fixtures/remotion_stub.ts`
exporting `staticFile = (p) => '/' + p`.

---

## 2. `fitOneLine` CLAMPS — it does not promise a fit

This is the sharpest trap in the layout helpers. `fitOneLine` returns
`minFontSize` when nothing fits, so combined with `overflow: hidden` the text
**overruns its column and gets sheared mid-glyph**. Measured signature: all four
long names ending at *exactly* the same x (541 = the column edge), rendering
`Claude-Opus-4.` with the 6 gone. That is worse than an ellipsis, which at least
admits it truncated.

Two safe patterns:

```ts
// Derive the size from a measurement instead of clamping to one.
const probeSize = Math.round(height * 0.02);
const probeW = measure({ text: longest, fontFamily, fontSize: probeSize, fontWeight: 800 }).width;
const fSize = Math.max(floor, Math.min(ceiling, Math.floor(probeSize * colW * 0.98 / probeW)));
```

```ts
// Or size the COLUMN from what the text needs at the smallest acceptable size.
const needed = Math.ceil(measure({ text: longest, fontSize: floor, ... }).width) + 4;
```

Same idea for a value column: measure the widest real string
(`9 840 очков`, not `77 %`). A percentage-share guess that is "wide enough" for
the sample data overflows on longer input, and because every row child is
`flexShrink: 0` the overflow **pushes the row right and eats its padding**.

---

## 3. When four splits all fail, the space is not there to divide

`Leaderboard` history, in order — each fix creating the next defect:

| attempt | outcome |
|---|---|
| flat font + ellipsis | `Llama-4-Scout-1...` — drops the parameter count that is the reason the name is on screen |
| two-line wrap | nothing lost, but `GLM-5.2-Air` wrapped while row 5 did not → inconsistent baselines |
| `fitOneLine`, bar takes the rest | silent mid-glyph shear (§2) |
| name takes what it needs, bar the rest | no shear, but the bar fell 301 → 190 px, undoing the widening that was requested |

Do the arithmetic before the fifth attempt. Measured, 5 rows in a 920 px table:
chrome (padding + gaps + rank + logo) = 318, value = 102, leaving **500** for a
bar needing ~250 to read as a measurement *plus* an 18-char name needing ~310 at
its smallest legible size. 560 into 500 does not go.

**Stack them.** The row was 206 px tall and using ~40 of it. Name over bar, each
getting the full column:

```
bar fill width   203 px -> 488 px
bar thickness     29 px ->  75 px
% right margin    21 px ->  48 px
name shear     4 rows at x=541 -> none
```

The general rule: when a horizontal budget cannot satisfy two elements that both
have hard minimums, stop reallocating width and **spend the unused vertical
space**. Data rows in vertical video are almost always height-rich.

---

## 4. Two measuring habits

**Re-measure after every fix; corrections oscillate.** The `%`-to-edge gap went
21 px (cramped) → 79 px (two digits of dead space) → 48 px. The 79 was not a
mistake in the padding value — it appeared because the *previous* defect (a value
column overflowing and eating padding) had been fixed, so the padding finally
applied in full. A fix that removes an overflow changes every downstream margin.

**Derive probe frames from the spec's own arithmetic.** Scenes at 150 frames each
mean frames 120/130/140 are all **scene 0**. Sampling those and then reasoning
about "scene 1" produced a confident wrong diagnosis (*"RingStats renders bar
rows"*) before the frame maths got checked. Compute `sum(durationInFrames)` up to
the target scene and sample inside it; for beat-divided presets also see
`text-fitting-and-beat-sampling.md` §2.
