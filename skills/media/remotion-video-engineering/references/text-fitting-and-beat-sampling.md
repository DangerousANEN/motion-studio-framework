# Hero text that doesn't fit, and the sample point that hides it

Two defects from one session, same root: **geometry computed from a fraction of the
canvas instead of from the content that has to fit inside it.** Both shipped through
`tsc`, Zod, a red-frame probe, and a per-scene still-frame pass with a vision review.

| Preset | Sized by | What broke |
|---|---|---|
| `PhoneMockup` | `max(screenW/width, screenH/height)` | cropped **80 px per side** (7.4 % of canvas width) — ate the first and last character of every nested line |
| `CountdownHero` | `finalFontSize = height * 0.14` | 7-glyph hero word spanned **x0..x1079 in a 1080 px frame** — read `ОГНАЛ` instead of `ДОГНАЛИ` |

Detail on the first is in `nesting-scenes-in-device-frames.md`. This file is the
second plus the sampling lesson, because the sampling lesson is why the second one
survived a full verification pass.

---

## 1. Never size a hero string by a fraction of height

`height * 0.14` is 269 px at 1920. That fits about **six** wide caps across the safe
area. Anything longer overflows the viewport, and the middle of the word still looks
correct — so the frame reads as deliberate.

Measured on `CountdownHero` with `finalWord: "ДОГНАЛИ"`:

```
bright-pixel bbox: x 0 - 1079   (frame is 1080 wide)
touches left edge? True   touches right edge? True
```

Both edges touching is the signature. A word that fits leaves margin on both sides.

### The fix — measure, and only ever shrink

`theme/layout.ts` already exports `fitOneLine` (wrapping `@remotion/layout-utils`
`fitText`). Use it as a **ceiling reducer**, not as the size itself, so a short word
keeps the designed display size:

```tsx
import { fitOneLine } from '../theme/layout';

const finalFontSize = Math.min(
  Math.round(height * 0.14),                 // designed ceiling
  fitOneLine({
    text: finalWord,
    maxWidth: safe.width,                    // safe area, not frame width
    fontFamily: fonts.display,
    fontWeight: 900,
    maxFontSize: Math.round(height * 0.14),
    minFontSize: Math.round(height * 0.05),  // floor: below this, rethink the copy
  })
);
```

After: `x 83 - 991` — 83 px left margin, 88 px right, word complete.

### Verification (no OCR needed)

The bbox test is the whole check, and it is reference-free:

```python
a = np.asarray(Image.open(png).convert("RGB")).astype(int)
h, w, _ = a.shape
ink = (a[:, :, 1] > 200) & (a[:, :, 0] < 180)   # tune to the accent, not to grey
ys, xs = np.where(ink)
assert xs.min() > 2 and xs.max() < w - 3, f"hero text touches frame edge: {xs.min()}..{xs.max()}"
```

Then confirm the *word* with one vision call — the bbox proves it fits, only reading
it proves it is the right word.

### Audit the rest of the library in the same pass

```bash
grep -rn "Math.round(height \* 0\.1[0-9])" src/presets/
```

Any hit that feeds a `fontSize` for **user-supplied** text is the same bug waiting.
Hits that size avatars, rows or gaps are fine. In the audited library only
`CountdownHero` had it; every other hero used a fit helper or wrapped.

**Rule of thumb:** a fixed fraction is legitimate for geometry the author controls
(ring diameter, row height, avatar). It is never legitimate for a dimension that
must contain a string the *spec* supplies.

---

## 2. A single mid-scene sample cannot see a beat-divided preset

`verifying-rendered-video.md` §11 covers the progressive-reveal trap: a midpoint
frame shows a reveal half-finished, so re-sample near the scene end. This is the
sibling case and the advice is different again.

Some presets **subdivide their duration into beats that hold different content**.
`CountdownHero` divides into `from + 1` equal beats:

```
durationInFrames = 102, from = 3  ->  totalBeats = 4, beatFrames = 25.5
beat 0: frames  0.0 - 25.5   digit "3"
beat 1: frames 25.5 - 51.0   digit "2"
beat 2: frames 51.0 - 76.5   digit "1"
beat 3: frames 76.5 - 102    finalWord   <- the payoff, 25 % of the scene
```

The house habit of sampling **72 % into each scene** puts frame 73 in beat 2 — a
digit. The final word, the entire reason the scene exists, is never sampled. The
truncation survived a 15-frame still pass *and* a vision review of every scene,
and only surfaced when the whole script was rendered to mp4 and frames near the
cut were pulled.

### Sample per beat, not per scene

For any preset whose duration is divided (countdowns, step reveals, quiz
reveal-at-progress, karaoke lines, versus intro/compare/verdict):

```python
# derive beats from the preset's own contract, then sample the LAST one
total_beats = int(scene.get("from", 3)) + 1
beat = scene["durationInFrames"] / total_beats
frames = [int(beat * (i + 0.72)) for i in range(total_beats)]   # 72% into each beat
```

Cheaper heuristic when you don't want to model the preset: sample **three** frames
per scene at 30 % / 72 % / 92 %. The 92 % sample catches final-beat and
reveal-state content; it costs one extra `still` per scene.

Presets whose contract implies beats — check for a field that divides time:
`from` (CountdownHero), `revealAtProgress` (QuizCard), `sendAtProgress` (TgChat
compose), `startAt` per line (LyricLines), `steps[]` (ProgressPath, FlowDiagram).

### Render the whole thing before delivering

Per-scene stills answer "can this scene draw". They do not answer "does the
delivered file contain the payoff". The mp4 render is what exposed this, and it
costs ~40 s for a 10 s vertical short — cheaper than shipping a hook that reads
`ОГНАЛ`. Pull frames from the **encoded file** (`ffmpeg -vf "select=eq(n\,94)"
-vsync 0`), never a fresh `still`.

---

## 3. Why both defects looked fine

Worth stating because it is the reusable part: **a truncated frame ships and a
letterboxed frame gets fixed on day one.** Cropping leaves plausible-looking
output — a centred word missing one glyph each side, a chat bubble missing its
first letter — while a black band screams. Any geometry choice whose failure mode
is "silently cuts content" needs an assertion, because no human glance will catch
it and no global probe (safe area, red card, byte equality, luminance) looks at
element-vs-container fit.
