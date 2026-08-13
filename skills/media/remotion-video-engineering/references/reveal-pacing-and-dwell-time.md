# Reveal pacing: the defect no still frame can show

The complaint was *"some scenes/overlays are shown for too little time."* It is a
real, reproducible, measurable class of bug, and **every** check the pipeline had
passed it: nothing overflowed, nothing clipped, no red card, tsc clean, vision
review called the frames well composed. A still frame cannot express duration.

This reference covers how to measure it, the arithmetic that causes it, and the
three traps that made the first measurements wrong.

---

## 1. The root cause: reveal schedules expressed as fractions of scene length

The pattern to grep for is a reveal delay multiplied by `durationInFrames`:

```ts
const revealFrames = Math.round(durationInFrames * 0.75) - defDelay;  // DefinitionCard
const eventWindowFrames = durationInFrames / count;                   // TimelineReveal
const staggerFrames = Math.round(durationInFrames / (rows.length + 2)); // Leaderboard
```

Each looks safe. Each gives the viewer a **fraction of the scene** to read the
result, so reading time scales with the scene instead of with the text. Measured
at 180 frames (3.0s), the element carrying the payload got the least time:

| preset | payload | settled at | dwell before cut |
|---|---|---|---|
| DefinitionCard | the definition | 89 % | **0.30s** |
| TimelineReveal | newest event | 93 % | **0.18s** |
| Leaderboard | bottom ranked row | 87 % | **0.38s** |

The cruelty is systematic, not random: in a cascade the *last* item always gets
the worst deal, and the last item is usually why the scene exists — the newest
model, the final step, the lowest-ranked entry a "top N" video is counting down
to.

**The bug does not scale away.** At 600 frames the same code leaves 1.0s of a
10-second scene. The fraction is constant; only the absolute number moves.

### Fix: schedule backwards from a dwell guarantee

`remotion/src/lib/pacing.ts`:

```ts
export const MIN_DWELL_SEC = 1.0;
export const REVEAL_TAIL_SEC = 0.25;

export const settleBy = (durationInFrames, fps, dwellSec = MIN_DWELL_SEC) =>
  Math.max(0, Math.round(durationInFrames - (dwellSec + REVEAL_TAIL_SEC) * fps));

export const paceSequence = (startFrame, settleFrame, weights) => { /* ... */ };
```

Presets then derive their schedule from `settleBy()` instead of from the raw
duration:

```ts
const cascadeUnits = rows.length + 2;               // arrival + 2 units of bar fill
const staggerFrames = Math.max(3, Math.floor(settleBy(durationInFrames, fps) / cascadeUnits));
```

Two properties matter more than the formula:

- **`REVEAL_TAIL_SEC` is not padding.** My first version subtracted only the
  dwell, which schedules the reveal to *start* at `duration - dwell` and
  therefore leaves `dwell` minus the animation's own duration. Asking for 1.0s
  measured **0.77s**; the missing 0.23s was exactly the spring settling. If you
  schedule by start frame, subtract the animation length too.
- **When the scene cannot afford the dwell, collapse to frame 0** — everything
  visible immediately, maximum reading time — rather than silently shortening the
  dwell. Silently shortening it *is* the original bug.

Measured after, at 180 frames: 0.30 → 0.98s, 0.18 → 1.12s, 0.38 → 1.48s.

### Verify across durations, not at one

A pacing helper that only works at the duration you tested is the original bug
wearing a helper's clothes. `tests/test_pacing.py` asserts the contract at
**90 / 180 / 600 / 1800** frames. At 90 frames DefinitionCard still falls short —
and that is the correct answer, not a failure: 1.5s cannot hold 176 characters
and no layout change fixes it. Which is why the probe reports two independent
verdicts (below).

---

## 2. Measuring it: frame sequence + per-band settle detection

`remotion/scripts/timing.mjs` renders one scene as a frame sequence
(`remotion render --sequence --scale=0.5`). One bundle, half scale — a 180-frame
scene costs about what a single still costs. Sampling stills frame-by-frame costs
30x more.

Two pitfalls in the script itself:

- `--sequence` needs an **output directory** and refuses a non-empty one. Remove
  it first.
- Remotion writes `element-000.jpeg` (JPEG, not PNG) for sequences. Filtering on
  `.png` reports `0 frames` while the render succeeded.

`tools/timing_probe.py` splits each frame into 12 horizontal bands and reports,
per band: first frame with content, first frame it **stops changing**, and how
long it stays settled before the sequence ends.

**Dwell is measured from settle, not from appear.** A typewriter reveal "appears"
at frame 24 and is still spelling itself out at frame 140; the viewer can only
read it from the settle point on.

### Trap: absolute settle thresholds versus perpetual animation

ProgressPath pulses its current dot with an endless sine; TimelineReveal pulses
its active dot. A perpetual 12 %-scale wobble never falls below a fixed motion
floor, so those bands measured **"never settles, dwell 0.00s"** and looked like
catastrophic late reveals when nothing was wrong. ProgressPath was reported
`REVEALS_TOO_LATE` before any code was touched.

Make settle **relative to each band's own peak motion**:

```python
peak = float(step[appear_i:].max())
floor = max(SETTLE_FRAC, peak * 0.08)   # 8 % of this band's largest change
quiet = step < floor
```

Once change drops under 8 % of the largest change that band ever saw, the reveal
is done and what remains is decoration. A viewer reads straight through a subtle
pulse.

### Trap, second order: the carve-out that masked the defect it existed for

The peak-relative floor is not sufficient. `ScoreHud` reseeds its combo sparks
with `frame`, so ~990 pixels change *every* frame from the first to the last — the
change is large, not subtle, so no relative floor dismisses it. It needs an
explicit "perpetual animation" classification, excluded from the dwell verdict.

**That exclusion is where I broke the probe.** My first discriminator was "motion
in the final third exceeds 0.5× the first third". Measured profiles:

| band | last/first | coefficient of variation |
|---|---|---|
| score roll (a REAL late reveal) | 0.54 | 1.37 |
| combo sparks (true shimmer) | 1.02 | 0.43 |

At `> 0.5` the score roll was classified as perpetual, so the probe reported
`ScoreHud: OK` while the score was still counting at 99.4 % of the scene. The
carve-out hid exactly the defect it existed to distinguish itself from, and it did
so *silently*, by upgrading a verdict.

Require **both** near-constant energy (`ratio >= 0.8`) and low variability
(`cv < 0.8`). A reveal decelerates and is bursty; a shimmer is flat and steady.

Two general rules fall out of this:

- **Validate any probe exclusion rule against a known-BAD case, not just a
  known-good one.** Keep the pre-fix frame sequences and re-grade both directories
  side by side after every probe change — the failures must still fail. This is the
  only reason I caught it.
- **Confirm what a suspicious band actually contains before calling it a bug.**
  Cropping and reading it ("КОМБО ×3" with sparkles) established that nothing there
  needed slowing down. Two of the three flagged ScoreHud bands were a genuine
  defect and one was decoration; a blanket verdict would have been wrong either way.

### Clock semantics: freeze the value, don't compress the world

`ScoreHud`'s round timer was `timeLeft * (1 - sceneProgress)` — a whole 60-second
round clock elapsing over a 3-second shot, always landing on `00`. Two defects in
one line:

- **It lies.** A 3-second clip does not contain a minute of play.
- **`00` on a round timer reads as *time up*,** so the frame looked like an
  unfinished placeholder. Vision review flagged it as a "placeholder/logic issue"
  and was right for the wrong reason.

For any element representing real-world time, one video frame is one frame of that
world (`timeLeft - floor(frame / fps)`), and the value freezes at `settleBy()` so
the final state is held rather than still moving at the cut. Prefer remapping the
clock once (`hudFrame = min(frame, settleFrame)`, then feed *that* to every
animation) over rescaling each animation separately — one line fixed the score
roll, the health bar and the timer together.

### Presets fixed by this pattern

All were `durationInFrames * k`; dwell at 180 frames, before → after:

```
DefinitionCard   definition finished typing   89%   0.30 -> 0.98
TimelineReveal   newest event                 93%   0.18 -> 1.12
Leaderboard      bottom ranked row            87%   0.38 -> 1.48
CommentWall      newest comment               90%   0.28 -> 1.72
PostCard         metric counters              79%   0.60 -> 1.58
SubscribeCTA     subscribed state + bell      77%   0.68 -> 1.55
AiChatStream     stream ended 4 frames early  98%   0.07 -> 1.23
ScoreHud         score / health / timer       99%   0.00 -> 1.98
```

`AiChatStream` deserves a note: an unfinished stream is indistinguishable from a
*truncation bug* to a viewer, and the only thing distinguishing them — the typing
cursor — blinks off half the time. Vision review of the pre-fix frame called it
"broken/truncated text" and then listed missing UI affordances that were not the
problem. Land the last character before the cut and the completion footer
(`✓ N токенов`) becomes the proof it finished.

Note the two shapes of fix. Cascades (`CommentWall`, `Leaderboard`, `TimelineReveal`)
divide `settleBy()` by their item count **plus the trailing units their own
entrance animation needs** — `rows.length + 2`, not `rows.length`. Choreographies
with named phases (`SubscribeCTA`'s 0.25/0.55/0.65/0.72/0.75, `PostCard`'s
0.25+0.55) need only their base rescaled: `const D = settleBy(durationInFrames,
fps)` preserves every proportion and simply finishes early enough to be seen.

### Report two verdicts, because they have different owners

```
pacing:   OK | REVEALS_TOO_LATE          -> preset bug, fix the schedule
duration: OK | SCENE_TOO_SHORT_FOR_TEXT  -> spec bug, fix the script upstream
```

Collapsing them into one `TOO_FAST` verdict sends you editing a preset when the
actual problem is 176 characters in a 3-second scene. `validate_spec` warns on
the second case before a render is ever attempted; warn, never block — duration
comes from the narration length, and a decorative scene with a long caption
nobody needs to read is legitimate.

### Keep the constants in sync, and assert it

Three places grade this contract: `pacing.ts` (what presets target),
`timing_probe.py` (what the pixels are graded against), `spec.py` (what the
author is warned about). If they drift, the probe passes presets that are too
fast or fails ones that are fine. `test_pacing.py` greps all three files and
asserts the numbers match.

### Prove the test can fail

Revert `settleBy` to the buggy form and confirm
`test_settle_leaves_dwell_plus_animation` fails, then restore. A pacing test that
passes against the bug it was written for is decoration.

---

## 3. Translucent fills over painted-behind decoration

Adjacent defect, same "renders fine, looks wrong" family. Presets express subtle
fills as an alpha suffix on a theme hex:

```ts
backgroundColor: `${theme.muted}33`
```

Correct only when nothing sits behind the element. ProgressPath and
TimelineReveal draw their connector track **first**, then the dots on top — so
the track stayed visible as a faint vertical stripe crossing the inside of every
pending circle. The user spotted it; no probe did.

Probe signature: sample the interior pixel row across the dot and count distinct
colours. It held **4** (fill, track, two grid lines) where it should hold **1**.

```python
row = a[dot_center_y, x0:x1]
assert len(np.unique(row.reshape(-1, 3), axis=0)) == 1
```

Fix — `remotion/src/theme/color.ts`:

```ts
export const blend = (fg: string, bg: string, amount: number): string => { /* opaque hex */ };

let dotBg = blend(theme.muted, theme.bg, 0.2);   // was `${theme.muted}33`
let dotBorder = blend(theme.muted, theme.bg, 0.33);
```

Same visual tone, resolved against the known backdrop, returned as **opaque**
hex, so the fill covers what is behind it. Keep alpha suffixes where see-through
is the actual intent (glass surfaces, overlay scrims). Verify the circle still
reads as a subtle outline afterwards, not a solid blob — `0.2` against `#0E0F11`
keeps it near-background.

Grep for the whole class: `grep -rn '}33`\|}44`\|}55`\|}66`\|}88`' src/presets/`,
then ask of each hit whether anything is painted underneath it.

---

## 4. Vertical budgets that add a gap after dividing the space

Found while re-verifying the timing fixes hadn't disturbed layout. Leaderboard:

```ts
const rowH = Math.round(Math.min((safe.height - height * 0.12) / rows.length, height * 0.115));
// ...later, in the JSX:
gap: Math.round(rowH * 0.12)
```

The column is divided by the row count, and *then* a gap is added between every
pair — 4 gaps of 26px that came out of nowhere. Card 5 ended at y=1618, 78px
inside the 380px band the platform reserves for its caption and action rail.

Solve the stack as **one equation**:

```ts
const rowH = Math.round(
  Math.min(rowsAvail / (rows.length + gapRatio * (rows.length - 1)), height * 0.115)
);
```

and pass `gapRatio` into the `gap` style so the two cannot drift.

**The title block's line count must be measured too.** My first fix assumed one
line; "ТОП ОТКРЫТЫХ МОДЕЛЕЙ" wraps to two at that size, under-reserving 77px, and
the stack overflowed again (1556 vs the 1540 limit). `fitWrapped` with
`maxFontSize === minFontSize` pins the size and returns the real line breakdown.
Last card bottom: 1618 → 1540.

This is the same lesson as `measured-text-geometry.md` §5, arriving from a
different direction: **any budget that spends space must account for every
consumer of that space, including the ones added later in the JSX.**
