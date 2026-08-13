# Sizing text from measurement, not from a proxy

A class of defect that recurs across every preset pack: geometry computed from a
**proxy for the text** (character count, a fixed fraction of the canvas, a
percentage share of a row) instead of from the text's measured width. The proxy
is always tuned on the demo data, and the demo data is always the easy case.

Companion to `text-fitting-and-beat-sampling.md` (which covers the hero-word case
and the sampling blind spot) and `chart-and-widget-visual-design.md` (row/column
width budgets). This file is the general rule plus the four distinct failure
shapes seen so far, because each one fails *differently* and needs a different
assertion.

---

## 0. The rule

> If a dimension has to contain spec-supplied text, derive it from
> `measureText`/`fitText` on that text. Never from `text.length`, never from a
> fixed `height * k`, never from a share of the container.

Author-controlled geometry (avatar diameter, row height, padding, bar thickness)
is fine as a fraction. The line is whether the *content* is under the author's
control.

Audit command for a codebase that grew the other way:

```bash
grep -rn "\.length" src/presets/ | grep -i "font\|width\|size"
grep -rn "Math.round(height \* 0\.0[0-9][0-9])" src/presets/
```

Each hit needs the question: does spec text have to fit inside this? If yes, it
is a bug waiting for a longer string.

---

## 1. Character-count ladder — Cyrillic breaks it first

```ts
// WRONG — the exact ladder theme/layout.ts exists to replace
const termFontSize = Math.round(
  Math.min(height * 0.065, (safe.width * 0.88 / Math.max(t.length, 1)) * 1.5 + 8)
);
```

`DefinitionCard` with `term: "Квантизация"`. The ladder picked **118px**; eleven
Cyrillic glyphs at weight 900 need **~1090px** in a 1080px frame. The term ran to
x=1079 and rendered **"Квантизаци"** — the final я simply outside the canvas.

Why Cyrillic surfaces it: it is wider per character than the Latin the ladder was
tuned on. "Квантизация" and "Quantizatio" are both 11 characters and occupy
visibly different space. Same trap in the other direction with `iiiiiiiiiii`.

Fix — measure, and allow two lines so a compound term does not shrink to nothing:

```ts
const textW = safe.width - barWidth - barGap;   // the REAL column, not safe.width
const termFit = fitWrapped({
  text: t, maxWidth: textW, maxHeight: Math.round(safe.height * 0.22),
  fontFamily: fonts.display, fontWeight: 900, maxLines: 2, lineHeight: 1.1,
  maxFontSize: Math.round(height * 0.065), minFontSize: Math.round(height * 0.03),
});
```

Note `textW`: sizing against `safe.width` when an accent bar and its gap sit in
the row overflows by exactly the bar + gap. Subtract siblings first.

**Decorations derived from the same proxy inherit the bug.** The underline was
`Math.min(safe.width * 0.55, t.length * termFontSize * 0.55)` and stopped halfway
under the word. Span the *measured* width of the widest wrapped line instead.

Verification: bright-ink bbox right edge went `x=1079` (0px margin) → `x=976`.

---

## 2. `fitOneLine` CLAMPS — it does not promise a fit

The nastiest of the four, because the helper looks like a guarantee.

```ts
export const fitOneLine = ({ text, maxWidth, minFontSize = 32, ... }) => {
  const { fontSize } = fitText({ text, withinWidth: maxWidth, ... });
  return Math.max(minFontSize, Math.min(maxFontSize, fontSize));  // <-- clamp
};
```

When nothing fits, it returns `minFontSize` — a size that **overflows**. Paired
with the usual `whiteSpace: 'nowrap'; overflow: hidden`, the text is then sheared
mid-glyph with no ellipsis: `Leaderboard` showed **"Claude-Opus-4."** with the 6
gone. That is worse than an ellipsis, which at least admits it truncated.

Signature in a pixel probe: **several rows' text ending at the exact same x**.
Different strings cannot naturally share a right edge; four names all ending at
x=541 is the column boundary, i.e. a shear.

```python
# per-row ink extents; identical maxima == shear at a column edge
for ym in row_centres:
    m = (lum[ym-25:ym+25] > 110) & (sat[ym-25:ym+25] < 60)
    xs = np.where(m.any(0))[0]
    print(ym, xs.min(), xs.max())
```

Two ways out, both valid:
- Scale a measured width — `floor(probeSize * colW * 0.98 / probeW)` — which
  guarantees the fit because it *is* the fit.
- Give the column what the longest string needs at the smallest acceptable size,
  bounded so the neighbour keeps a readable minimum.

---

## 3. Estimated line counts — `ceil(width / colW)` is wrong in both directions

Reserving vertical space needs a line count. The obvious estimate is wrong
because **CSS breaks on word boundaries**:

- a string 1.05 columns wide takes 2 lines, and the estimate only says 2 above 1.0;
- a string 1.9 columns wide can take **3** lines, once the last word will not fit.

Use the library's real breakdown, pinned to a fixed size:

```ts
const wrapLines = (text, fontSize, colW, family, weight) =>
  fitWrapped({
    text, maxWidth: colW, fontFamily: family, fontWeight: weight,
    maxLines: 6,
    maxFontSize: fontSize, minFontSize: fontSize,   // pin: report, don't resize
  }).lines.length;
```

**`fontWeight` is not optional.** `measureText` defaults to normal weight; labels
rendered at 600–800 are wider, so omitting it under-measures and reports one line
where the browser wraps to two. A `ProgressPath` fix that got everything else
right still overflowed 63px for exactly this reason.

---

## 4. A percentage share that also has to hold a stub — stack instead

Sometimes the honest answer is that the space does not exist and the layout is
wrong. `Leaderboard`, measured at 5 rows in a 920px table: chrome (padding, gaps,
rank, logo) 318 + value 102 leaves **500px** for a bar needing ~250 to read as a
measurement *and* an 18-char model name needing ~310 at its smallest legible
size. 560 into 500 does not go.

Four side-by-side splits each shipped a different visible defect (ellipsis eating
the parameter count; two-line wrap breaking baselines across rows; the §2 shear;
bar collapsing to 190px and undoing the widening that was requested). Stacking
the name over the bar ended it — the row was 206px tall and using ~40 — and both
got the full column: bar fill 203→488px, thickness 29→75px, zero shear.

The general move: when two elements each need most of one axis, check the *other*
axis before arbitrating between them.

---

## 5. Vertical budgets: absolutely-positioned rows grow DOWN

Not a text-measurement bug but the same "assumed instead of measured" shape, and
it cost three iterations.

`ProgressPath` spacing was `safe.height * (title ? 0.82 : 0.92) / (count - 1)`,
where `0.82` was standing in for both the title block and the last row's height
and did neither — the title renders *above* the path area, so its height came out
of nothing. With 5 steps and a title, content reached **y=1656**, i.e. 116px
inside the 380px band `platform` safe-area reserves for the caption and action
rail. **Nothing was clipped, so no probe complained**; the step would simply have
rendered under TikTok's chrome.

Two wrong assumptions on the way to the fix:

1. `alignItems: 'center'` does **not** centre the row on the dot. The row is
   `position: absolute; top: spacing * i` and grows downward; `center` only
   centres the dot against the label *inside* the row. Reserving `lastRowH / 2`
   on that belief put content 36px deeper than reserving nothing would have.
2. `center` also makes each row's height depend on its own wrapped text, so a
   two-line description pushes **its own dot** down and the dot-to-dot gaps come
   out uneven (measured 237/261/285px) even though `stepSpacing` is constant.
   `alignItems: 'flex-start'` pins every dot to `spacing * i + dotR`; nudge the
   label block down by `(dotDiameter - labelFontSize * 1.2) / 2` to keep it
   optically centred.

Final: `y_max 1655 → 1534` (limit 1540), gaps `261/261/261`.

**Safe-area overflow needs its own assertion.** It is invisible to clipping
checks, red-card checks and byte comparison:

```python
BOTTOM_LIMIT = 1920 - 380     # 'platform' profile reserve
m = np.asarray(Image.open(png).convert("RGB")).mean(2) > 110
ys = np.where(m.any(1))[0]
assert ys.max() <= BOTTOM_LIMIT, f"content at y={ys.max()} is under platform UI"
print("gutters", m[:, :80].sum(), m[:, 1000:].sum())   # side bleed
```

Run it over every stress PNG; it is three lines and catches the whole class.

---

## 6. Probe-reading pitfalls that produced wrong diagnoses here

- **Green-channel probes lie on the leader row.** A highlighted first row has an
  accent-tinted card background, so "find saturated pixels" finds the card, not
  the bar. Measure a non-leader row, or diff against that row's own median
  background.
- **Restrict the probe window and you measure the window.** A name-zone probe
  capped at x<560 reported every long name ending at 541 *and* the cap at 559;
  the shear was real, but the cap could equally have manufactured it. Widen the
  window past any plausible edge before concluding.
- **`measure()` slack ≠ visual margin.** After the value column stopped
  overflowing, `padR = rowH * 0.30` produced 79px of visible air — two digits of
  dead space — because measured advance width exceeds the ink box. Tune padding
  against the *pixel* margin, not the CSS value: 0.30 → 0.15 landed at 48px.
- **Vision and a pixel probe can both be right about different things.** Vision
  called `progress_desc` "uneven spacing"; the probe said `stepSpacing` was
  constant. Both true — the dots had moved, not the spacing.

---

## 7. Track coverage explicitly, and never imply completeness

Fixing the presets a user *pointed at* is not the same as the pack being done. In
a 38-preset registry, 12 had been stress-verified and 26 had only ever been
rendered with demo data. Asked "are all the scenes finished?", the only correct
answer was the ratio plus the named remainder — and the very next preset opened
turned up two real defects, so the honest answer was also the accurate one.

Enumerate from the registry rather than from memory, since that is the list that
actually exists:

```bash
# .dump.entry.ts imports PRESETS and prints {category, fields, dataDriven, three}
./node_modules/.bin/esbuild .dump.entry.ts --bundle --platform=node \
  --format=cjs --outfile=.dump.js --log-level=error && node .dump.js
```

Diff that against the set you have actually stressed; report the ratio and list
the untested ones by category so the user can prioritise. "Visual is perfect"
about one preset does not generalise to the pack, and saying so costs nothing
while implying otherwise burns the next review.

## 8. Clean up probe scaffolding before committing

Stress runs leave `.cases_*.json`, `out/stress*/` and `.dump*` files, and — more
dangerous — a render that writes back into tracked assets. `git status` after one
session showed modified `public/props.json`, `public/video-spec.json` and an
unrelated `video_graph.py` edit that had nothing to do with the preset work.
Check `git status --short` and `git diff --stat` before staging, and
`git checkout --` the incidental ones rather than sweeping them into a layout
commit.
