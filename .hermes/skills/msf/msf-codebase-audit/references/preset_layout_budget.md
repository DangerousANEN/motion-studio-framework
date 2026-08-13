# Preset Layout Budgets — when text goes INVISIBLE, not clipped

Findings from stress-testing MSF presets with the input the pipeline actually produces (2026
model names like `Qwen3.6-235B-A22B`) instead of the short demo strings they were built
around. Commits `e986673`, `14bd6c6`, `da047fd`, `5ad56db`.

## Rule 0 — stress with REAL input, not the defaults

Every bug below was invisible with the default rows (`Aria Chen`, `Скорость`, `Янв`). The
defaults are short by accident of authorship. Always re-render a preset with the longest
strings the pipeline can emit before calling it done.

## The failure mode that looks like a missing feature

`flex: 1` on a text column turns overflow into DELETION. In `Leaderboard` every element was
sized as its own fraction of the table and at 5 rows they summed to 977 px inside a 920 px
table (rank 92 + avatar 114 + bar 350 + value 166 + gaps 158 + padding 97). The name column
was `flex: 1`, absorbed the whole 57 px overflow and **collapsed to zero width**. With
`whiteSpace: nowrap` there is no ellipsis and no hint — the rows simply have no text, and it
reads as "this preset doesn't render names" rather than "this row overflows".

**Fix pattern — solve the budget, don't hope:**
1. reserve the TEXT column first at a fixed width
2. give the elastic decoration (bar, chart) whatever is genuinely left:
   `barMaxW = Math.max(floor, tableW - fixed)`
3. `width: nameW; flexShrink: 0` — never `flex: 1` for content that carries meaning

Rationale to keep: a stub bar still reads as a bar; a missing name is zero information.

## Fixed-height label slots (Bars3D, RingStats — same root cause twice)

Containers align on the item BOX, not on the graphic inside it. A one-line label makes its
column shorter/taller than a two-line one, so the graphic drifts off the shared axis:
- `Bars3D` (`flex-end` row): the gold bar sat visibly BELOW the others' baseline
- `RingStats` (centred wrap): a wrapping name lifted its ring ABOVE its neighbours

Reserve the same slot height for every label (`labelFont * lineHeight * maxLines`) and size
the font with `fitWrapped(maxLines: 2)`. Measured proof, three ring centres:
`974/977/974` before → `959/963/959` after.

When you reserve label height, also shrink the graphic's height budget (RingStats cell went
to `*0.8`) or a 6-item two-row layout overflows the safe box.

## `label` vs `name` — silent alias failures

Every data preset keys items on `segments[].label` (RingStats, Bars3D, DonutFill), so callers
naturally write `label` for `Leaderboard.rows[]` too — where it was `name` and silently
`undefined`. That `undefined` also fed `AvatarCircle`, so all five avatars showed the letter
**"U"**: the chart read as an unfinished template, not as bad input. Accept both keys and
normalise. When adding any new item-list preset, accept `label` as the alias.

## Ordering is a correctness claim, not a preference

`Leaderboard` painted 🥇 on row 0 while trusting caller order, so a row scoring 81 sat fifth
with no medal while a 77 took gold — a false statement on screen. If a preset renders rank
badges or medals, it must sort; offer `sortRows: false` for when the given order IS the
ranking (alphabetical, chronological).

## Nested scenes must inherit the CANVAS aspect

`PhoneMockup` hard-coded a 19.5:9 screen while the nested scene lays out for the full canvas
(`useVideoConfig()` returns the COMPOSITION size, not the wrapper's). A uniform scale into a
different aspect always leaves slack, and every way of spending it is a defect:
- fit height → letters sliced off the sides
- fit width, centred → letterbox bars
- fit width, bottom-anchored → a dead 242 px band above the chat header (26 % of the screen)

Derive the screen from the canvas: `screenH = screenW * (height / width)`. No slack exists,
so there is nothing to spend. Two prior "fixes" just traded one artifact for another.

## CSS 3D faces cannot be trusted; clip-path can

`Bars3D` extrusion faces were `rotateX(-90deg)`/`rotateY(90deg)` children of a parent tilted
only `rotateX(6deg)` → ~84° to camera, so the cap flattened to a 1–2 px sliver. Worse,
`perspectiveOrigin: 50% 78%` sat BELOW the bars, so the camera saw the cap's BACKFACE — the
"detached triangular shard" in review. Rebuilt as three `clip-path` polygons cut from one box
with fixed dx/dy offsets: isometric, no perspective, no backface to expose.

## Verification loop that actually catches these

1. render stills at the RIGHT frames — scenes of 150 frames mean frames 120/130/140 are ALL
   scene 0. I diagnosed "RingStats renders bar rows" off exactly this mistake before checking
   the frame maths. Sample scene N at `sum(previous durations) + offset`.
2. pixel-measure the geometric claim (group extents, baselines, centre lines, edge-to-edge
   coverage) — numbers, not impressions
3. vision A/B before-vs-after side by side, asking harshly and item by item
4. zoom to native or NEAREST-upscale for small features (bubble tails, bar caps); a
   full-frame view will not resolve them

Vision review earns its keep here: it caught that the "fixed" Bars3D had merged its labels
into one line and pushed values into the title, and that green outgoing bubbles read as
WhatsApp rather than Telegram. Probes did not.
