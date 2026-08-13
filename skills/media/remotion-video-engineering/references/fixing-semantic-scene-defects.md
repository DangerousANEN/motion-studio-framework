# Fixing semantic scene defects (and proving the fix without vision)

Companion to `verifying-rendered-video.md` §10, which catalogues *how these
defects are found*. This file covers *how they are fixed* and — the harder
problem — **how you prove a text-level fix landed when vision tooling is down
and no OCR is installed.**

All numbers below are measured before/after on a re-rendered mp4.

---

## 1. The A/B differential render — proving a text fix with no OCR and no vision

The situation: a user reports "it says 108%, should be 108". You change a default
and re-render. How do you *prove* the glyph is gone? On that occasion
`vision_analyze` was returning 400 across the model pool and `tesseract` was not
installed.

You do not need either.

> **Retry vision before settling for this.** The same session's vision outage was
> transient — the user said "try vision" a few turns later, it worked, and it
> immediately found three layout defects (§2f–2h) that no numeric probe had caught.
> A failing vision call is a temporary condition, never a standing fact about the
> environment: retry it at the start of each verification pass. The A/B render
> below is the fallback for when it is genuinely down, and it remains the stronger
> instrument for *one specific disputed glyph* — but it cannot survey a frame. Render the same composition **twice, mutating only the
disputed field**, and diff the pixels.

```python
def variant(mutate, tag, frame):
    s = json.loads(spec_p.read_text(encoding="utf-8"))
    mutate(s)
    # --props needs a path relative to the remotion dir -> stage it in public/
    dest = rem / "public" / f"_t_{tag}.json"
    dest.write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
    out = tmp / f"{tag}.png"
    subprocess.run(["npx", "remotion", "still", "src/index.ts", "Main", str(out),
                    f"--frame={frame}", f"--props=public/_t_{tag}.json", "--log=error"],
                   cwd=rem, capture_output=True, text=True, shell=True, timeout=900)
    dest.unlink(missing_ok=True)          # never leave staged props in the repo
    return out if out.exists() and out.stat().st_size > 2000 else None

d = np.abs(a.astype(int) - b.astype(int)).sum(axis=2)
ys, xs = np.nonzero(d > 30)
print(len(ys), f"bbox x{xs.min()}..{xs.max()} y{ys.min()}..{ys.max()}")
```

Read the result as a three-way verdict:

| outcome | meaning |
|---|---|
| **identical** | the field has no effect — either the fix did not take, or the render used a stale bundle. Do not report success. |
| **differs in a bounded region** | that region *is* the glyph/word. Report the pixel count and bbox as the evidence. |
| **differs across the whole frame** | the change moved layout, not just text. Surgical fix failed; something reflowed. |

Measured on the two text fixes in this session:

| change | differing px | bbox | verdict |
|---|---|---|---|
| `statSuffix: '%'` → `''` | 16 139 | `x400..683 y814..917` | the `%` glyph occupied that box; now absent |
| `contactName` added vs old `title`-as-name | 2 259 | `x152..307 y295..328` | confined to the header band |

The second row carries the more valuable assertion. **Also test that the change
is confined**: `ys.max() < H * 0.28` proved the chat bubbles did not move, i.e.
the header edit did not reflow the thread. A fix that "works" while shifting
everything else is a new defect.

Note `remotion still` re-renders from source, so this proves the *code* is fixed.
Confirm on the delivered mp4 too (`verifying-rendered-video.md` §1).

---

## 2. Fix patterns for the five defect classes

### 2a. Default invents units → delete the default

```diff
-  statSuffix = '%',
+  // NO default suffix. This turned any plain count into a percentage: the spec
+  // "Эффектов в реестре / statValue 108" rendered as "108%". A counter cannot
+  // know its number is a proportion; inventing a unit is worse than none.
+  statSuffix = '',
```

Rule: a default may supply *styling* freely. A default may never supply
**units, currency, names, labels or identity** — those are content, and content
absent from the spec must be absent from the screen.

### 2b. Field doing double duty → give the second meaning its own field

`{title || 'Аня'}` in a chat header meant the scene's caption also renamed the
contact, and a spec setting neither got a hardcoded Russian name on screen.

```diff
-  {title || 'Аня'}
+  {contactName || title || 'Аня'}
```

plus dedicated optional schema fields (`contactName`, `contactStatus`). Keep the
old chain as fallback so existing specs do not change behaviour. `contactStatus`
uses `??` not `||` so `''` can suppress the status line entirely — a distinction
`||` silently destroys.

### 2c. Palette alias collision → deduplicate at build time

`PALETTE = [accentColor, BRAND.accentCyan, BRAND.accentGreen, ...]` painted
segments 1 and 3 identically, because `accentColor` defaults to `BRAND.neon`
`#00FF88` and `BRAND.accentGreen` is *also* `#00FF88`.

```ts
const PALETTE = ((): string[] => {
  const candidates = [accentColor, BRAND.accentCyan, BRAND.accentGreen,
                      BRAND.gold, '#FF6B9D', '#A78BFA', '#FFB86B'];
  const seen = new Set<string>();
  const unique: string[] = [];
  for (const colour of candidates) {
    const key = colour.trim().toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(colour);
  }
  return unique;
})();
```

Two details that matter: normalise case before comparing, and **add a spare
colour** — deduplication shortens the list, so a palette that exactly fitted the
maximum segment count now wraps and reintroduces the collision.

Any palette whose first entry is a caller-supplied prop is exposed to this.
Audit every `[someProp, ...brandConstants]` array in the codebase.

### 2d. RNG misused as motion → noise continuous in *time*

```diff
-  const rand = mulberry32(seed + frame * 7);   // reseeds EVERY frame
-  const nx = (rand() - 0.5) * 2;
+  const nx = driftNoise(seed, frame, 0);
```

```ts
const DRIFT_LATTICE = 24;   // frames between nodes; ~2.5 Hz at 60fps

const driftNoise = (seed: number, frame: number, channel: number): number => {
  const x = frame / DRIFT_LATTICE;
  const i = Math.floor(x);
  const f = x - i;
  // distinct stream per (channel, node) so x and y do not correlate into a
  // diagonal-only wobble
  const node = (n: number) =>
    mulberry32(seed * 7919 + channel * 104729 + n * 31)() * 2 - 1;
  const a = node(i);
  const b = node(i + 1);
  const s = f * f * (3 - 2 * f);      // smoothstep: zero slope at both nodes
  return a + (b - a) * s;
};
```

The general fault: **reseeding a PRNG with the frame number makes consecutive
frames statistically independent.** That is white noise. Any effect that should
look continuous — handheld drift, float, sway, flicker with body — needs noise
sampled as a function of time: sparse lattice nodes plus interpolation.
Determinism is preserved; the seed still fully specifies the motion.

Verified on the settled window of the affected scene (frames 200–240), measured
by centroid tracking:

| | mean step | max step | horizontal direction reversals |
|---|---|---|---|
| before | 1.029 px | 3.391 px | 23 / 39 frame pairs |
| after | 0.234 px | 1.951 px | 11 / 39 |

Reversal count is the diagnostic, not magnitude (see `verifying-rendered-video.md`
Recipe B).

### 2e. A reported defect can be a *symptom* of another defect

The user reported two separate donut problems: duplicate colours **and** holes
between segments. Only one bug existed. The two same-coloured segments sat either
side of the ring's closing boundary, so the 2° separator between them read as a
hole punched inside a single segment rather than as a divider between two.

Fixing the palette fixed both. Measured after, by angular run-length sampling:
`#00F780 219.1°`, `#00CDF2 79.9°`, `#E6BF6E 45.6°`, gaps `2.0 / 1.7 / 1.8°`
against 2° requested.

Before writing a second fix, check whether the first one already explains the
second report. Two symptoms, one cause is common when colour, adjacency or
z-order is involved.

### 2f. Rows positioned by independent magic percentages → band table

The defect class: **two elements inside the same container overlap.** No probe in
this skill catches it. Safe-area checks frame edges; the red-frame probe checks
hue; the `intensity=0` proof checks byte equality; span arithmetic checks time.
Element-vs-element geometry *inside* a card is measured by none of them, and
vision found all three defects below on the first look at a rendered frame.

`BankCard` positioned every row against its own hand-picked fraction — number at
`top: cardH*0.52`, holder at `bottom: cardH*0.14`, VISA at `bottom: cardH*0.1`
with face `cardH*0.2`. Independent constants cannot know about each other, so:

| collision | measured |
|---|---|
| number row over `CARD HOLDER` | number ran to y=168 on a 236px card; holder began y=153 |
| VISA through `EXPIRES` | scheme mark occupied the same band as the expiry caption |

Fix: make the vertical layout a **single declared table** and position everything
from it. Overlap then becomes arithmetically checkable — and mostly impossible.

```ts
const numberFace = cardH * 0.10;
const band = {
  number:  { top: cardH * 0.44, h: numberFace  * 1.2 },
  labels:  { top: cardH * 0.68, h: labelFont   * 1.2 },
  holder:  { top: cardH * 0.76, h: holderFont  * 1.2 },
  expires: { top: cardH * 0.76, h: holderFont  * 1.2 },
};
```

Two rows may share a `top` **only** when they occupy disjoint horizontal columns
(`holder` left, `expires` right). Assert that explicitly; do not leave it implied.

Where a crowded band forces a move, prefer the placement the real artefact uses:
VISA went to the top-right, because on a physical card the scheme mark lives
there and the top band held only the chip. Fixing a collision by shrinking type
is the worse trade — it fixes geometry and damages legibility.

### 2g. Fixed letter-spacing → derive the face from the width budget

Immediately after 2f, vision reported the number row running into the card edge.
Confirmed by measurement: **ink reached the card's right edge with 0px margin**,
and the container's `overflow: hidden` had silently amputated the last four
digits — the user-visible `4821` was simply gone.

This is why safe-area probes miss it. Nothing crossed the *frame* edge; the clip
happened at a *container* edge, and `overflow: hidden` removed the evidence
instead of letting it spill somewhere a bounds check would notice. **Any element
inside `overflow: hidden` needs its own width assertion.**

Cause was a fixed `letterSpacing: cardW * 0.012` never rescaled when the face
changed. Cheap estimator, no browser needed — monospace advance ≈ 0.60em:

```python
advance   = face * 0.60
total     = len(text) * (advance + tracking)
available = cardW - 2 * sideMargin
```

19 chars at face 63.7px + 9.48px tracking → **906px against 664px available**;
tracking alone contributed 180px of the overflow. Sweeping the two knobs showed
tracking could not rescue it at any value (726px bare, still over), so the face
had to come down: `cardH*0.10` with tracking at **8% of the face** rather than a
fraction of the card. Result measured on the re-render: ink ends 102px inside the
edge, 12.9% of card width.

Rule: tracking belongs in units of the face it tracks. A spacing expressed
against the *container* silently breaks every time the type size moves.

### 2h. Vision and measurement each catch what the other cannot — cross-check both ways

Same session, both directions fired:

- **Measurement blind, vision right.** Every collision in 2f/2g passed the full
  numeric gate (Zod, `tsc`, red-frame, safe-area, byte-exact no-op, span
  arithmetic) and was obvious in one look at the frame.
- **Vision wrong, measurement right.** The same vision pass also asserted the
  card was "squeezed horizontally". Measured aspect was **1.612** against ISO
  7810 ID-1's **1.586** — a 1.6% deviation, not a squeeze. Reporting that as a
  defect would have started a hunt for a bug that did not exist.

So: treat a vision finding as a **lead, not a verdict** — reproduce it as a
number before fixing, and re-render plus re-look after fixing. Fixing 2f is what
exposed 2g, which means one look is never enough either; each fix changes the
frame and can reveal the next defect underneath.

Card-rect detection used for all measurements above (works on any centred panel
lighter than its page background):

```python
bg   = a[4, 4]                                   # page background sample
card = a.sum(axis=2) > bg.sum() + 18
rows = card.sum(axis=1)                          # longest run of wide rows = card
# ... take the longest run where rows[y] > w * 0.35 -> y0, y1
cols  = card[y0:y1 + 1].sum(axis=0)
xs    = np.flatnonzero(cols > (y1 - y0) * 0.5)   # x0, x1
```

Then per row: slice the band from the table, threshold ink (`luma > 140`), take
the ink bbox, and assert `cardRight - inkRight > cardW * 0.05`. Run that for
every text row, not only the one that was reported broken.

---

## 3. Open finding: transitions that consume timeline without blending

Not root-caused. Recorded because the measurement is reproducible and the probe
is reusable — **do not repeat the measurement believing it is already explained.**

A probe walking each transition window and measuring per-frame `|Δluma|` reported
that on an 8-scene demo, none of the seven transitions spread the handover across
its overlap:

```
slide      → TgChat         worst  14%   content trough   5%
crossZoom  → AiChatStream   worst  79%   content trough  10%
wipe       → CryptoWallet   worst  15%   content trough   0%
flip       → BankCard       worst   9%   content trough   0%
iris       → DonutFill      worst  12%   content trough  14%
dreamyZoom → QuoteCard      worst  86%   content trough   0%
zoomBlur   → StatCounter    worst  11%   content trough   0%
```

`worst` = largest single-frame share of the window's total change; a real
22-frame blend should sit near 5 % and certainly under 40 %. `crossZoom` and
`dreamyZoom` exceed that decisively — the same signature §6 of
`transitions-and-motion-layer.md` documents for `dissolve`.

**What is actually proven.** The `content trough` column used corner-pixel
background sampling, which Recipe A warns is unreliable mid-wipe. It was
re-measured reference-free (edge energy) for `wipe` and `crossZoom` only, and
both confirmed: on the `crossZoom` window the donor scene's solid content fell
from 19 563 px to 1 949 px **in a single frame** (287→288), with the incoming
scene not yet drawn — a hard cut through near-black, not a blend. The other five
rows have *not* been re-measured reference-free and may be metric artifacts.

Probe method, for whoever picks this up:

```python
lumas  = [luma(frame) for frame in window]
deltas = [abs(lumas[i] - lumas[i-1]).mean() for i in range(1, len(lumas))]
worst  = max(deltas) / sum(deltas)          # share carried by one frame
```

Candidate causes not yet eliminated: the HTML-in-Canvas rasterisation path
(§2b of `transitions-and-motion-layer.md`) interacting with the per-scene
`EffectStack` wrapper; scene wrappers sized such that the donor rasterises empty;
or genuine gl-transition threshold behaviour as with `dissolve`. Run the 2×2
{suspect, known-good} × {shader, DOM} matrix before theorising.
