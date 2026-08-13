# Replicating a real app's UI as a preset (messenger mockups)

A `TgChat`-class preset is not "a chat-shaped scene" — it is an **imitation of a specific
build of a specific app**, and it is judged against a screenshot the user can pull up in
two seconds. This file is the checklist and the failure log from bringing one from
"obviously fake" to "recognisably Telegram", verified against a real Android screenshot
the user supplied.

Related: `css-3d-faces-and-relocated-slack.md` §3 lists the first-pass fidelity gaps and
the duplicated-`compose` data trap. This file supersedes it on colour (§1) and on where
the chrome sits (§3).

---

## 0. Get the reference first, and mine it in ONE vision pass

Do not iterate on memory of what the app looks like. Ask the vision model to extract a
spec from the user's screenshot before writing any code — one call, many answers:

> *"Report precise visual details: exact hex of outgoing bubble / incoming bubble /
> background / header / timestamps / checkmarks; bubble corner radius; is there a tail and
> on which corner; do consecutive messages from one sender have different corners; where do
> timestamp and ticks sit relative to the text; header layout; input bar icon order; date
> pill shape and opacity; which font family; text size relative to bubble height."*

That returns hex values, radii, grouping rules and icon order in one shot. Everything
below came out of that single pass plus four render/critique rounds.

---

## 1. Ranked defect list — what actually makes a mockup read as fake

Vision consistently reported these in the same order of obviousness. Fix them in this
order; the first two are worth more than all the rest combined.

| # | Defect | Fix |
|---|---|---|
| 1 | **Wrong font.** Preset set no `fontFamily`, inheriting the composition's serif display face | Pin a system-sans stack explicitly |
| 2 | **Wrong bubble colour.** | Sample from the reference. See the WhatsApp trap below |
| 3 | Tail on *every* bubble; no run grouping | Tail on last-of-run only, square that corner, small radius on inner corners, tighter gap within a run |
| 4 | Timestamp/ticks on their own line under the text | Inline via a reserved spacer, so short messages are one line tall |
| 5 | Missing header chrome (back arrow, call, menu, avatar initial) | Add all of it |
| 6 | Header/composer as floating rounded cards inset by the safe area | Edge to edge, full canvas width |
| 7 | Send arrow visible over an empty input | Mic icon until text exists |
| 8 | Sender name inside a 1-on-1 bubble | Gate behind an `isGroup` flag |
| 9 | Flat or polka-dot wallpaper | Tiled line-art doodles |

### The font is the loudest tell

```tsx
const TG_FONT = '"Inter", "Segoe UI", Roboto, "Helvetica Neue", "SF Pro Text", Arial, sans-serif';
```

A style kit's `fonts.body` is a *brand* face chosen for the video. An app mockup must
ignore it and use the platform UI font — a serif chat bubble is identifiable as fake at
thumbnail size, before any layout detail registers.

### The WhatsApp trap

Pale green `#EFFDDE` bubbles were the first attempt (a plausible memory of "messenger
light theme"). Vision's verdict: *"resembles WhatsApp or a custom theme"*, listed as the
single most obvious difference. Telegram's outgoing bubble is **blue with white text**
(`#3996EC` sampled from the reference); ticks and timestamps become translucent white.

Sampled light palette that passed review:

```
bg #D3ECFA · doodle rgba(120,178,220,0.22) · bubbleIn #FFFFFF · bubbleOut #3996EC
textIn #000 · textOut #FFF · metaIn rgba(0,0,0,.35) · metaOut rgba(255,255,255,.78)
header/bar #FFFFFF · headerText #1D242D · headerMeta #82919E · accent #3390EC
pill rgba(125,160,190,.55)
```

Keep the old dark palette behind a `tgTheme: 'light' | 'dark'` enum so existing specs
don't change. Default to **light**: a screenshot-inside-a-video usually is.

---

## 2. Run grouping is the structural rule, not decoration

A burst of messages from one sender is **one visual block**. Three coupled behaviours:

```tsx
const prev = thread[i - 1], next = thread[i + 1];
const firstOfRun = !prev || Boolean(prev.out) !== out;
const lastOfRun  = !next || Boolean(next.out) !== out;

// outer corners keep the full radius; inner corners of a run shrink;
// the tail corner is SQUARE (0) or a notch shows between bubble and nib
borderBottomRightRadius: out ? (lastOfRun ? 0 : rSmall) : R
marginTop: firstOfRun ? height * 0.0062 : height * 0.0016   // between runs vs within
{lastOfRun && <Tail out={out} color={bubbleBg} size={tailSize} />}
```

### The tail that rendered nothing

First attempt: `right: -size * 0.52` with the path drawn in the left half of a
`0 0 12 16` viewBox. Result: the visible ink sat back **inside** the bubble and no tail
appeared at all. The pixel probe caught it where a glance would not:

```python
rights = [np.where(row)[0].max() for row in bubble_mask]
# tail present  -> max-x increases over the last few rows
# tail missing  -> identical max-x on every row (plain rounded corner)
```

Working geometry — svg's left edge on the bubble's right edge, ink in the *right* half:

```tsx
<svg width={size} height={size} viewBox="0 0 12 12"
     style={{ position:'absolute', bottom:0, [out?'right':'left']: -size + 0.5,
              transform: out ? undefined : 'scaleX(-1)' }}>
  <path d="M0 0V12H8.4C4.2 11 1.6 7.4 0.6 2.4Z" fill={color} />
</svg>
```

Because the nib hangs outside the box, inset the whole run by `tailSize` (`marginRight`
for outgoing, `marginLeft` for incoming) or the thread column clips it.

---

## 3. App chrome is edge-to-edge and anchored to the SCREEN, not the safe area

Two separate mistakes with the same root cause — treating the video's safe area as the
app's layout box:

- Header and composer were rounded cards inset by `safe.left`. A real Android action bar
  spans the full width flush with the top. Render them **outside** the safe-area column at
  `left: 0, width` and pad the thread by `headerH`.
- The composer was pinned to `safe.top + safe.height - barHeight`, leaving roughly a
  fifth of the frame as bare wallpaper below it. Anchor to `height - barHeight`.

Nested in a `PhoneMockup` the child's safe area is `'loose'`, so screen-edge anchoring
lands on the phone's screen edge, which is what you want.

Verify numerically, not by eye:

```python
white = (np.abs(frame - 255).sum(2) < 14)
assert white[10].sum() == W            # header spans the full width
assert white[H - 1].sum() == W         # composer reaches the bottom row
```

---

## 4. Stateful chrome must track the state

Every one of these was flagged as a tell:

- **Empty field shows a microphone**, not a send arrow. Swap on `!sent && typedChars > 0`.
  Keep the same circle as the click target so the cursor animation still lands on it.
- **After sending, the field returns to the placeholder.** `opacity: 0` on the typed text
  left a blank composer, which no real screenshot shows.
- **The composed bubble needs a timestamp.** Injecting it with `time: ''` produced a bare
  tick with no clock. Inherit the previous message's time.
- **Sender name only in groups.** Labelling the other party in a DM is instantly wrong —
  their name is already in the header.

---

## 5. Bubble width: the text-wrap tell

At `maxBubble = safe.width * 0.76`, a line the real client fits on one row wrapped onto
two. That is a subtle but real fidelity break, and it also changes the visual rhythm of
the whole thread. `0.84` matched. When a reference screenshot is available, check the
wrap point of the longest message explicitly — vision will report it if asked.

---

## 6. Iterate render → harsh vision critique → fix, and expect regressions

Four rounds were needed. Each round's critique found *new* defects introduced or exposed
by the previous fix (the composer-anchor bug only became visible once the bar was
full-width). Two habits:

- **Ask for harshness explicitly**: *"Judge it harshly against the real client… list every
  remaining difference, ordered by obviousness"*. A neutral "does this look right?" returns
  a description, not a defect list.
- **Build the A/B side by side** with the user's screenshot at matched height and hand it
  to vision. Direct comparison surfaces colour and proportion errors that a solo view of
  the mockup rates as fine.
- **Trust a crop over a full frame** for small features (tails, corner radii): downscaling
  1080x1920 for the model erases a 6 px nib. Zoom with `Image.NEAREST` at 6x.

State plainly which deviations remain deliberate (no avatar photo available, no Android
status bar because the phone frame plays that role) rather than leaving the user to spot
them.

### 6.1 The critique itself contains false positives — check each item before "fixing" it

A harsh vision critique is a list of *candidates*, not findings. On the round after the
tails landed, the model reported: *"the LAST bubble of the second outgoing run is missing
its tail — compare it to the first run, which correctly displays one."* Confident, specific,
and **wrong**. A max-x-per-row probe on that bubble showed the same tail signature as the
first run:

```
group y965-1175 : maxRight=993  lastRows=[989, 990, 991, 993]   # tail present
group y1268-1531: maxRight=993  lastRows=[989, 990, 991, 993]   # identical
```

A 6x `Image.NEAREST` crop of that exact corner then got an unambiguous *"yes, a tail/nib
IS present"* from the same model. The full-frame downscale had erased a 6 px nib in one
place and not another, and the model rationalised the difference into a defect.

Two other items from the same critique that were not defects either:

- *"the long line still wraps onto two lines"* — the **text** was one line; the timestamp
  had wrapped. Different bug, and it had already been fixed by the inline spacer.
- *"the text differs: `но не шарю особ` vs `но не шарю особо`"* — the reference screenshot
  was itself truncated. Not a mockup error.

Practical rule: for every item in a critique, decide whether a **probe can settle it**
(colour, extent, presence, alignment → yes) or whether it is genuinely semantic (does this
read as Telegram → no). Run the probe on the yes items before writing code. Acting on all
of them uncritically is how a fix round introduces regressions into parts of the frame that
were already correct — and the earlier habit of "trust the probe over the eye" cuts **both**
ways, not only in the direction of finding defects.
