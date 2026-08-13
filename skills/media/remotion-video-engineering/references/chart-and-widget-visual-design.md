# Chart & widget visual design — when correct is still ugly

The defect class where **every probe passes and the user rejects the frame anyway**.
A donut chart measured 221.4 / 84.3 / 47.3° against 219.5 / 85.0 / 49.6 expected for
`62/24/14` after three 2° gaps — arithmetically exact — and the verdict was three
words: *"бублик неооооч"* (the donut's rubbish). No probe in this skill can produce
that verdict, and no amount of re-measuring answers it.

When a user rejects a widget on looks, **redesign it and report the reasons as
measured ratios**. Do not defend the frame with the numbers that already passed:
they were never the thing being questioned. A terse aesthetic verdict is a complete
bug report — it just needs translating into ratios before it becomes actionable.

---

## 1. The five defects behind one "ugly"

Each was found by measuring a *ratio*, not by taste. Ratios are what make an
aesthetic complaint reproducible and fixable.

### 1a. The widget claimed the whole safe width

`available = min(safe.width, safe.height - legend - title)` gives the chart every
pixel the safe area allows. On 1080×1920 with the platform's 80 px l/r margin that
is **920 px = 85 % of frame width**, so the ring jams against both edges while the
tall vertical format sits empty above and below.

A vertical frame has height to spare and no width to spare. Cap the *width* term:

```ts
const available = Math.min(safe.width * 0.78, safe.height - legendH - titleH);
```

**738 px = 68 % of frame, 181 px margins.** Working band for a centred round widget
in 9:16: **60–70 % of frame width**. Above ~78 % it reads as cropped.

### 1b. Stroke was 30 % of the radius, so arcs read as capsules

`thickness ?? size * 0.13` → 120 px stroke on a 400 px radius. At that ratio the
segments stop reading as a chart and become fat lozenges, and the round line caps
dominate the geometry.

**Cap overhang in degrees is `(stroke / 2) / radius × 180 / π`** — it scales with
ring thickness, so a thick ring makes its own gaps impossible:

| stroke | radius | stroke/radius | cap overhang | vs a 2° gap |
|---|---|---|---|---|
| 120 px | 400 px | 30 % | 8.6° per end | swallows it (measured 359.9° of 360 coloured) |
| 57 px | 330 px | **17 %** | 4.9° per end | still larger — compensation mandatory |

Use `size * 0.08` for a donut. Keep the cap compensation (subtract the overhang
from dash length, only when a gap is requested) regardless — at no realistic
thickness is a round cap smaller than a 2° gap.

### 1c. `flex: 1` on a legend label separates it from its own value

A legend row of `[swatch] [label flex:1] [value]` inside a 920 px container throws
the value to the far right edge. The eye has to cross the entire frame to pair
`Сцены` with `62%` — on a phone that is a genuine reading failure, not a nitpick.

Shrink-wrap the row to its content and centre the group:

```tsx
<div style={{ display:'flex', flexDirection:'column', gap:14, alignSelf:'center' }}>
```

Rule: **a label and its value are one visual unit.** `space-between` and `flex: 1`
belong in wide layouts, not in a 9:16 legend.

#### 1c-bis. …and in a full row budget, `flex: 1` DELETES the text entirely

The same property has a worse failure mode when the row is over-subscribed. In
`Leaderboard` every element was sized as its own fraction of the table, and at 5
rows they summed to **977 px inside a 920 px table**: rank 92 + avatar 114 + bar
350 + value 166 + gaps 158 + padding 97. The name column was `flex: 1`, so it
absorbed the whole 57 px overflow and **collapsed to zero width**. With
`whiteSpace: nowrap` there is no ellipsis and no reflow — the rows simply have no
text, and the frame reads as *"this preset doesn't render names"* rather than
*"this row overflows"*. A defect that impersonates a missing feature will not be
filed as a layout bug by anyone reviewing screenshots.

Solve the budget instead of hoping:

1. reserve the TEXT column FIRST at a fixed width (`nameW = tableW * 0.34`);
2. give the elastic *decoration* whatever is genuinely left —
   `barMaxW = Math.max(floor, tableW - fixed)`;
3. `width: nameW; flexShrink: 0` for anything carrying meaning; never `flex: 1`.

Rationale worth keeping: **a stub bar still reads as a bar; a missing name is zero
information.** When a row cannot fit, the elastic element must be the decorative
one.

Then size the longest string to its reserved column rather than trusting a
fraction of height — a fixed `height * 0.021` was tuned for `Aria Chen` and 2026
model names like `Qwen3.6-235B-A22B` are far wider.

> **PARTIALLY SUPERSEDED — read this before applying the recipe above.** Steps
> 1–3 stop the text vanishing, but they only move the starvation to the other
> element: giving the bar the leftover left it **28 px**, clamped to a 74 px stub,
> and the user's next report was *«полоска слишком маленькая»*. Two follow-ups:
>
> * **`fitOneLine` CLAMPS at `minFontSize` — it does not promise a fit.** With
>   `overflow: hidden` the text overruns and is **sheared mid-glyph**: measured
>   signature is several long strings ending at *exactly* the same x (the column
>   edge), rendering `Claude-Opus-4.` with the 6 gone. Worse than an ellipsis,
>   which at least admits it truncated. Derive the size from `measure()` instead.
> * **When two elements both have hard minimums that a horizontal budget cannot
>   satisfy, stop reallocating width — stack them.** Four splits of one
>   `Leaderboard` row each shipped their own defect before the arithmetic was
>   written out: 500 px available, bar needs ~250, an 18-char name needs ~310.
>   The row was 206 px tall and using ~40 of it. Name over bar gave both the full
>   column: bar fill 203 → 488 px, thickness 29 → 75 px, no shear.
>
> Full history, the vendor-icon asset traps, and the measuring habits are in
> `brand-icon-assets-and-row-stacking.md`.

#### 1f. Two correctness traps that look cosmetic

**A silently-ignored key alias.** Every data preset here keys items on
`segments[].label` (RingStats, Bars3D, DonutFill), so a caller — human or pipeline
— naturally writes `label` for `Leaderboard.rows[]` too, where the field was
`name`. It fell through to `undefined`, which *also* fed `AvatarCircle`, so all
five avatars showed the letter **"U"**: the chart read as an unfinished template
instead of as bad input. Accept both keys and normalise. Any new item-list preset
should accept `label` as an alias on day one.

**Ordering is a claim, not a preference.** `Leaderboard` painted 🥇 on row 0 while
trusting caller order, so a row scoring 81 sat fifth with no medal while a 77 took
gold — a false statement on screen, not a layout nit. If a widget renders rank
badges, medals or podium positions, it must sort; expose `sortRows: false` for when
the supplied order *is* the ranking (alphabetical, chronological).

#### 1g. Reserve a fixed label slot, or the graphic drifts off its axis

Flex containers align on the item BOX, not on the graphic inside it, so a
one-line label makes its column a different height from a two-line one and the
graphic moves:

- `Bars3D` (row aligned `flex-end`): the gold bar sat visibly **below** the
  others' baseline — reported as *"the gold bar is lower"*.
- `RingStats` (centred wrap): a wrapping name **lifted** its ring above its
  neighbours. Measured centres `974/977/974` → `959/963/959` after the fix.

Reserve `labelFont * lineHeight * maxLines` for every label and size the text with
`fitWrapped({ maxLines: 2 })`. Mixed-length names are the normal case, not the edge
case: `GLM-5.2-Air` fits one line while `Qwen3.6-235B-A22B` never will.

When you add reserved label height, **shrink the graphic's height budget too**
(RingStats' cell term went to `* 0.8`) or a 6-item two-row layout overflows the
safe box.

### 1d. A default that can only ever print a tautology

`centerContent` defaulted to `'total'`. On a percentage breakdown the total is
always 100, so the largest type in the frame permanently read **"100%"** — zero
information, maximum prominence.

Check every default for *whether it can be interesting*. If a default's value is
determined by the data's shape rather than its content, it is decoration. Default
to `'label'` (the leading segment's name). This is Rule 1b2's "defaults must not
invent meaning" one step further: a default must not state the obvious either.

### 1e. A palette colour borrowed across semantic roles

`BRAND.gold` `#E6C475` is a muted metallic sand — correct for a card mark or a
surface, wrong as a data segment beside neon green `#00F780` and cyan `#00CDF2`,
where it reads as dirty. As legend text it was the dimmest thing on screen.

**Brand palettes carry role, not just hue.** A surface/metallic token and a data
token are not interchangeable. For chart series pick from a data ramp at matching
saturation — `#FF4D9D` here — and keep the metallic for marks and edges.

---

## 2. Measuring a ring without inventing defects

The first angular scan of the fixed ring reported **22 fragments in a 3-segment
donut**, with segments of 2.9°, 5.2°, 8.1°. All phantom. Three hygiene rules, in
the order they bite.

### 2a. Confirm the frame is not inside a transition

Frame 912 of a 752..922 scene returned **2 698 saturated pixels** against 126 145
on a settled frame — it was inside the exit crossfade. Compute spans first (see
`verifying-rendered-video.md`), then pick a frame that is past the value animation
(60 f easeOut here) *and* before the outgoing transition: `[start + anim, end - t]`.

Cheap pre-check before any geometry: count mask pixels and compare against a
neighbour. An order-of-magnitude drop means you are in an overlap.

### 2b. Sample the ring's mid-line, derived from a radial profile

Sampling at a guessed radius (344, then 345) catches the outer edge where
anti-aliasing and cap curvature break runs apart. Derive the ring from the image:

```python
prof = [(rr, sum(1 for a in range(0, 360, 3)
        if mask[int(cy + rr*math.sin(math.radians(a-90))),
                int(cx + rr*math.cos(math.radians(a-90)))]))
        for rr in range(80, 430)]
hits  = [rr for rr, c in prof if c > 60]      # 60 of 120 probes = a real ring
r_in, r_out = min(hits), max(hits)
r_mid = (r_in + r_out) // 2                   # sample here
```

This also yields stroke thickness (`r_out - r_in`) and diameter as a share of
frame width for free — the two numbers §1a and §1b are judged on.

### 2c. Classify by hue, never by a brightness threshold

A colour grade in the effect stack (`ColorGradeWarm`) darkens parts of the arc
below any fixed `sum(rgb)` / saturation cut-off, so a *continuous* segment splits
into fragments wherever the grade dips. That produced all 22 phantom runs.

```python
def classify(c):
    r, g, b = c
    if max(c) - min(c) < 28 and sum(c) < 260: return "bg"
    mx, mn = max(c), min(c)
    if mx == mn: return "bg"
    if mx == g:  return "green" if g > b else "cyan"
    if mx == b:  return "cyan"
    if mx == r:  return "magenta"
```

Hue survives a luminance grade; brightness does not. Result: 3 runs,
221.4 / 84.3 / 47.3°, gap 1.8°.

### 2d. Cross-check with a raw transition count

Before believing any run-length result, count bare bg↔ink transitions at one
radius and print the raw RGB either side. **`n` segments with gaps ⇒ `2n − 1`
transitions** (5 for three segments). If the classified run count exceeds that,
the classifier is wrong, not the render — go back to §2c rather than writing a fix.

Corollary: a self-reported defect can be a probe artifact. The "gap in the green
segment at 6 o'clock" here did not exist; green ran continuously for 221.4°. Say
so plainly when it happens — reporting a phantom as fixed is worse than the phantom.

---

## 3. Pre-flight checklist for any data widget

Run these against the settled frame before delivering. All are ratios, all take one
measurement each.

- Widget width ÷ frame width ∈ **[0.60, 0.72]** for a centred round widget in 9:16.
- Stroke ÷ radius ≤ **0.20** for a donut; above that it stops reading as a chart.
- Cap overhang `(stroke/2)/radius` in degrees — compensated out of every requested gap.
- Legend label and value within one shrink-wrapped row, group centred.
- No default field whose rendered value is fixed by the data's *shape* (a total on a
  percentage breakdown, a count of a list of length 1).
- Every series colour drawn from the data ramp, none borrowed from a surface/metallic
  token; assert `len(set(colours)) == n_segments` case-insensitively.
- **Re-render with the longest string the pipeline can emit**, not the built-in
  defaults. Every defect in §1c-bis, §1f and §1g was invisible with `Aria Chen`,
  `Скорость` and `Янв` — those are short by accident of authorship, and the
  pipeline feeds `Qwen3.6-235B-A22B`.
- Row/column budget adds up: `Σ(fixed widths) + Σ(gaps) + padding ≤ container`,
  with the text column reserved and the decoration elastic. If BOTH have hard
  minimums that do not fit, stack them vertically instead of splitting again.
- No `fitOneLine` result trusted as a fit — it clamps at `minFontSize`, so pair it
  with `measure()` or size the column from the text.
- Re-measure every margin AFTER each fix: corrections oscillate. A `%`-to-edge gap
  went 21 px (cramped) → 79 px (two digits of dead space) → 48 px, and the 79
  appeared only because removing an upstream overflow let the padding finally
  apply in full.
- Item labels accept the `label` alias as well as `name`.
- Any widget drawing rank badges sorts its own data.
- Brand logos, if any, resolve by brand substring and fall back to a letter
  avatar — never to a generic glyph. See `brand-icon-assets-and-row-stacking.md`.

### 3a. Sample the RIGHT frame before diagnosing

Scene spans matter more than they look. With 150-frame scenes, frames 120/130/140
are **all scene 0** — I diagnosed *"RingStats renders bar rows instead of rings"*
off exactly that mistake and wrote a paragraph of analysis about the wrong preset
before checking the arithmetic. Compute `sum(previous durations) + offset` per
scene (see `verifying-rendered-video.md` for the overlap-aware version) and confirm
the still shows the preset you think you are debugging.

Then, in order: pixel-measure the geometric claim (group extents, baselines, centre
lines, edge coverage) → vision A/B before-vs-after side by side, asked harshly and
item by item → NEAREST-upscale zoom for small features (bubble tails, bar caps),
which a full-frame view cannot resolve.

Vision earns its keep on exactly this class: it caught that a "fixed" Bars3D had
merged its labels onto one line and pushed values into the title, and that pale
green outgoing bubbles read as *WhatsApp* rather than Telegram. No probe here
reports either.
