# CSS-3D faces that detach, and slack that a geometry fix only relocates

Two defect classes that survive every automated probe and only surface when a human
looks at the frame. Both were found on a Bars3D / PhoneMockup pass after the specs
had already passed schema validation, still rendering, and a vision review.

**Both were later fixed properly, and both first fixes were wrong.** The corrected
resolutions are in §1.1 and §2.1 — read those before reapplying the earlier advice.

---

## 1. A fix that removes slack at one edge creates a defect at the other

An earlier session fixed `PhoneMockup` cropping the nested scene: scaling by
`max(screenW/width, screenH/height)` overflowed the sides by ~80 px each and ate the
first and last character of every line. The fix was to scale by **width** and anchor
the child to the bottom:

```tsx
top: screenH - height * (screenW / width),
```

That is correct for the crop. But the leftover band does not disappear — it *moves*.
Measured on the next render: screen 522x1160, child 1080x1920 scaled by 0.483 → 928 px
tall, leaving **232 px** of unused screen plus the child's own `loose` top inset (~68 px).
Result: a black band filling roughly **26 % of the screen height above the chat header**,
where a real Telegram thread pins its header to the top edge.

The user reported this as "телефон обрезанный" — a crop. It was not a crop; it was the
dead band. Take a reported symptom as a pointer to the region, not as the diagnosis.

### 1.1 The real fix: remove the slack instead of relocating it

Every option in the "where do I put the slack" framing is a defect:

| scale rule | consequence |
|---|---|
| by height (`max`) | overflows the sides, silently truncates text (80 px/side measured) |
| by width, centred | letterbox above **and** below the content |
| by width, bottom-anchored | one dead band at the top (26 % of screen height) |

The framing itself was the bug. Slack exists only because the **container aspect differs
from the content aspect**, and the container was hardcoded to a real phone's 19.5:9 while
the nested child lays out against the full 9:16 canvas (`useVideoConfig()` returns the
*composition's* size, not the wrapper's — a child cannot be laid out at screen size
without making every internal `height * 0.03` font microscopic).

Derive the screen from the canvas aspect and the fit is exact on both axes, so no slack
exists to misplace:

```tsx
const BEZEL_RATIO = 0.022;
const A = height / width;                        // canvas aspect, e.g. 1920/1080
// bodyH = screenW*A + 2*bezel, with bezel = BEZEL_RATIO*bodyW  =>
const bodyToWidth = (1 - 2 * BEZEL_RATIO) * A + 2 * BEZEL_RATIO;
let bodyW = Math.min(safe.width, Math.floor(availH / bodyToWidth));
let bezel = Math.max(6, Math.round(bodyW * BEZEL_RATIO));
let screenW = bodyW - bezel * 2;
let screenH = Math.round(screenW * A);           // <- matches the child exactly
let bodyH   = screenH + bezel * 2;
if (bodyH > availH) { /* re-solve once: the max(6,…) bezel floor can overshoot */ }
```

Then the child placement is unconditional — `top: 0`, `scale(screenW / width)` — because
`screenW/width` and `screenH/height` are now the same ratio.

Cost: the device silhouette is no longer a real phone's proportions. For a 9:16 short that
is invisible (the mockup is a framing device, not a product shot) and strictly better than
either truncated text or a quarter-empty screen. If a session genuinely needs true 19.5:9
hardware proportions, the child must be authored for that aspect — not scaled into it.

**Generalisation.** When placing fixed-aspect content into a fixed-aspect container you
control, make the container match the content. Only reach for "which edge gets the slack"
when both aspects are externally imposed.

**Assertion that catches the band** (works without a reference image):

```python
# inside the lit screen bbox, look for a contiguous dark run
band = frame[:, xs:xe, :].mean(axis=(1, 2))     # row means across screen width
runs = contiguous(lambda i: band[i] < 22, min_len=60)
# a run longer than ~10% of screen height above the first UI element = dead zone
```

Before/after on the real renders: `[(328, 570, 242)]` → `[]`.

Note the trap: a naive "is the phone cut off?" probe on the **full canvas** returns
`bbox = x 0..1079, y 123..1919` and looks like edge-to-edge cropping, because the
mockup's drop shadow and backdrop are non-black. The phone body was in fact fully
inside the frame. Probe the *lit screen interior*, not canvas ink extent, or you will
chase a crop that does not exist while missing the band that does.

---

## 2. CSS 3D extrusion collapses when `perspective` sits on a flex ancestor

`Bars3D` built each bar from three divs — front face, top face rotated
`rotateX(-90deg)`, right face rotated `rotateY(90deg)` — inside a wrapper that itself
carried `transform: rotateX(6deg) rotateY(-16deg)` and `transformStyle: preserve-3d`,
while `perspective` / `perspectiveOrigin` lived on the **flex row** above:

```tsx
<div style={{ display:'flex', perspective: height*1.1, perspectiveOrigin:'50% 78%' }}>
  <div style={{ transformStyle:'preserve-3d', transform:'rotateX(6deg) rotateY(-16deg)' }}>
    <div/* front */ style={{ inset:0 }}/>
    <div/* top   */ style={{ transform:'rotateX(-90deg)', transformOrigin:'top' }}/>
    <div/* right */ style={{ transform:'rotateY(90deg)',  transformOrigin:'right' }}/>
```

Rendered result (vision, 3 bars): the top and side faces do **not** join the front
face. Each bar shows a small detached triangular shard at the top-right corner, and the
bars lose baseline alignment. The bars read as flat rectangles with glitch artifacts,
not solids.

Two compounding causes, both geometric rather than a missing-property bug:

- A face rotated `-90deg` inside a parent tilted only `6deg` ends up ~84° to the camera —
  nearly edge-on — so the cap rasterises as a 1–2 px sliver, not a cap.
- The bars stand **above** `perspectiveOrigin: 50% 78%`, so the camera looks at the
  underside of that cap. What survived was a **backface**. That is the "detached shard":
  not a stray polygon, but the wrong side of a nearly edge-on plane.

### 2.1 The real fix: isometric `clip-path` polygons, not CSS 3D

The earlier note here guessed that "the intermediate wrapper needs its own perspective."
Do not spend time on that. Drop perspective entirely and cut three polygons out of one
box with fixed pixel offsets — an isometric projection cannot produce an edge-on face or
a visible backface, because there is no camera:

```tsx
const dx = depth, dy = Math.round(depth * 0.52);
const blockW = barW + dx, blockH = h + dy;
const front = `polygon(0px ${dy}px, ${barW}px ${dy}px, ${barW}px ${blockH}px, 0px ${blockH}px)`;
const cap   = `polygon(0px ${dy}px, ${dx}px 0px, ${blockW}px 0px, ${barW}px ${dy}px)`;
const side  = `polygon(${barW}px ${dy}px, ${blockW}px 0px, ${blockW}px ${h}px, ${barW}px ${blockH}px)`;
// three absolutely-positioned divs, inset:0, each with one clipPath; cap lightest,
// side darkest, front last so its glow sits on top
```

Bonus: `clip-path` rasterises in the DOM, so unlike a WebGL canvas it composites correctly
inside shader-based transitions.

### 2.2 The shared baseline was never the bars'

Divergent bottoms are not a transform artifact. The flex row is `align-items: flex-end`,
which lines up **column** bottoms — and a one-line label (`GLM-5.2`) makes its column
shorter than a two-line one (`Qwen3.6-27B`), so that bar hangs lower. Give labels a
fixed-height slot (`labelSlotH = barW * 0.19 * 2 * 1.15`) and the columns match.

Verify numerically, not by eye: after the fix all three bars reported
`frontBottom = 1250` identically.

### 2.3 Fixing the geometry broke the labels — check the whole frame again

The first rewrite fixed the blocks and the baseline, and vision immediately caught two
**new** defects on the same frame:

- labels crammed onto one line, shifted off their bars, last column overflowing the safe box
- the values `77` / `81` colliding with the title

Both because the isometric block is **wider and taller than the bar**: it extends `depth`
right and lifts `depth * 0.52` up, but the column was still sized to `barW` and the bar
height was still `plotH * 0.84`. Budget the column first, then derive the bar:

```tsx
const colW = clamp((safe.width - gap*(n-1)) / n, …, safe.width * 0.2);
const barW = Math.round(colW / (1 + DEPTH_RATIO));       // column owns the extrusion
const barMaxH = Math.max(40, plotH - (valueH + labelSlotH + shadowH + dy));
```

Post-fix assertion — count contiguous coloured column groups and check the extent against
the safe box, which catches both the crowding and the overflow in one pass:

```
column groups: [(236,419), (448,631), (660,843)]   -> 3 separate, as authored
coloured x-extent: 236..843                        (safe box 80..1000)  OK
```

**Rule.** After rewriting a preset's geometry, re-verify the *entire* frame, not the thing
you set out to fix. A geometry change silently re-flows every sibling that shared its box.

---

## 3. Mockup fidelity is a separate axis from mockup geometry

Once the geometry was right, the chat still did not read as Telegram. Vision listed
what a real client has that the preset lacked, and it is worth keeping as a checklist
for any messenger mockup:

- system **sans** font (the preset used a serif from the style kit's `fonts.body`)
- bubble **tails** pointing toward the sender's edge (plain rounded rects read as generic)
- a **timestamp** inside every bubble, next to the check marks
- a **status bar** (time / battery / signal) and a **back arrow** in the header
- an avatar with a photo or initials, not a bare gradient circle
- the send button appears only while composing; empty input shows a mic icon

> **Superseded / expanded.** The full rebuild of that preset against a real Android
> screenshot — ranked defect list (font first, bubble colour second), the sampled light
> palette, run-grouping rules, the tail svg that rendered nothing because its ink sat in
> the wrong half of the viewBox, edge-to-edge chrome, stateful mic/send swap, and the
> render→harsh-critique loop — lives in `replicating-real-app-ui-in-presets.md`. Read that
> before touching a messenger mockup; this list is only the first-pass symptom set.

Separately: check the spec for **duplicated content**. A `TgChat` whose
`messages[-1].text` equals its `compose` string renders the same bubble twice after the
send lands — visible in the frame as two identical bubbles bracketing the reply, and
easy to mistake for a preset bug when it is authored data.

---

## 4. Vision prompts must name the candidate defect

A generic "does this look right?" returns "looks like a 3D bar chart" and the shards read
as styling. Prompts that actually worked, and are worth reusing verbatim:

- *"do the extruded top/side faces join the front face, or is there a detached triangular
  shard?"*
- *"do all three bars stand on the same bottom baseline, or does one sit lower?"*
- *"is there a large empty/black region inside the phone screen above the chat header?"*
- *"is any text clipped at the left or right edge of the screen?"*

Two further habits from this pass:

- **Crop before asking.** A full 1080x1920 frame downscaled for the model hides a 2 px
  sliver. A tight crop of the defect region got a precise answer where the full frame got
  "the geometry extends off the top edge of the image" — the crop had cut the caps off, so
  the model correctly described the crop, not the bug. Always include the feature you are
  asking about *inside* the crop.
- **Label legibility is not chart integrity.** On the same broken frame the model names
  (`Qwen3.6-27B`, `Gemma 4 31B`) were 100 % legible while every block was collapsed.

---

## 5. Webfont fetch is a flaky step, not a broken renderer

`remotion still` occasionally dies with `ERR_NO_BUFFER_SPACE` / `NetworkError` while
fetching a Google font, producing no output file. It is transient: the retry loop below
succeeded on attempt 1 immediately afterwards. Do not conclude the preset or the renderer
is broken — check for the artifact and retry.

```python
for attempt in (1, 2, 3):
    run_still(...)
    if os.path.exists(out): break
```
