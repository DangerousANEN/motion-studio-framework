# Style Kits & Theme Palettes — authoring, and proving they work

A "style kit" is the video-wide visual language: palette + fonts + motion character +
backdrop texture + post-FX intent, selected by one field (`style: "retro"`). Adding one
is the cheapest way to widen output variety — no React, no new preset.

It is also the easiest place to ship something that looks finished and does nothing.
Three independent failure modes, all of which pass `tsc`, all of which render exit 0.

---

## 1. The whole layer can be dead code — grep for the accessor, not the file

`styleKits.ts` existed with eight complete kits, each specifying palette, fonts, motion,
backdrop, surface treatment and transition. **Nothing imported `getStyleKit`.** The only
inbound reference in the repo was `PostFX.tsx` importing the `EffectProfile` *type*.

So `style: "retro"` changed nothing, because no component ever asked which style was
active and every preset hardcoded its own colours. The feature was fully specified,
committed, documented — and unreachable.

Check for the *accessor* being called, never for the file existing:

```bash
grep -rn "getStyleKit\|useStyle(" src/ --include=*.tsx --include=*.ts | grep -v "theme/"
```

An empty result on a feature the docs describe means the layer is not wired. The fix is a
React context resolved once at the composition root, with the kit's palette folded into
the object presets already read (`theme.neon`), so existing presets honour it without
being rewritten first — that is what makes the wiring incremental instead of a 26-file
refactor.

Corollary: enumerate backdrop kinds the same way. A `dots` backdrop was implemented in
`Backdrop.tsx` and referenced by **no kit**, so it was unreachable while looking complete
in the source.

---

## 2. Kits that share a palette render pixel-identical

Eight kits pointed at five palettes: `editorial` and `clean` both at `noir`, `neon` and
`retro` both at `sunset`. Rendering one identical scene through each kit and comparing
gave a combined bg+accent distance of **0.0** for those pairs. Switching style did
literally nothing visible.

Because presets take their highlight from `theme.neon` and series colours from the
`neon`/`cyan`/`gold` triad, **changing only `bg` is not enough** — the rings, bars and
labels come out the same colour and the kit reads as a re-tint of its parent.

Assert distinctness by rendering, not by reading the palette table:

```python
# one identical scene per kit -> pairwise distance on [bg, accent]
vec = {}
for k in kits:
    a = np.asarray(Image.open(f"out/kits/{k}.png").convert("RGB")).astype(int)
    bg = a[40:120, 40:200].reshape(-1, 3).mean(axis=0)          # frame corner
    band = a[700:1300].reshape(-1, 3)
    sat = band.max(axis=1) - band.min(axis=1)
    accent = band[np.argsort(sat)[-4000:]].mean(axis=0)          # most saturated px
    vec[k] = np.concatenate([bg, accent])

ds = sorted((float(np.linalg.norm(vec[x] - vec[y])), x, y)
            for x, y in itertools.combinations(kits, 2))
assert not [p for p in ds if p[0] < 15], f"indistinguishable kits: {ds[:3]}"
```

Measured after splitting the collided pairs onto their own palettes: closest pair 26.3,
farthest 342.4, no pair under 15 across 91 pairs of 14 kits.

---

## 3. `muted` must clear ~4.5:1 against its own `bg` — the legibility defect class

Distinctness and legibility are different properties, and a distinctness check will
happily pass a kit whose captions are invisible.

Presets use `theme.muted` for sub-labels — ring captions, axis labels, timestamps — at
roughly `0.1×` the cell size. Six kits shipped a `muted` picked to look tasteful as a
swatch:

| kit | muted vs bg | verdict |
|---|---|---|
| `steel` | **2.98** | fails even the 3:1 large-text floor — captions effectively invisible |
| `candy` | 3.37 | below AA |
| `forest` | 3.86 | below AA |
| `mono_warm` | 4.13 | below AA |
| `glass`, `sunrise` | — | same problem, pre-existing kits |

Fix by raising each `muted` to the smallest lift that clears ~4.7:1 while keeping the hue
family, so the mood survives:

```
steel      #4A6070 -> #6E8798      candy      #8A5080 -> #A96BA0
forest     #4A7A58 -> #6C9E7C      mono_warm  #8A7060 -> #9C8272
sunrise    #A07850 -> #C09468      glass      #93A2BC -> #A9B6CC
```

Standard WCAG relative-luminance ratio; compute it, do not eyeball it:

```python
def lum(h):
    h = h.lstrip('#'); r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def ratio(fg, bg):
    a, b = lum(fg), lum(bg); hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)
```

Note the theoretical ratio is optimistic: antialiasing at ~0.1×cell darkens the rendered
stroke, so a palette value computing to 4.56 measured lower in pixels. Budget headroom
(target ≈4.7+) and confirm on the render.

---

## 4. Colour probes lie in three specific ways

All three fired in one session. Each produced a confident number that was wrong, and two
would have caused real damage if acted on.

### 4a. A probe returning the same verdict for every input — including a known-good control — is broken

Sampling `y 1290..1400` as "the label row" returned a contrast ratio of **1.0 for all 14
kits**, including `pop`, which was known good. There is no text at that y; the labels were
at `y 1100..1200`.

Generalisable check, cheap enough to always run: **put a known-good input through the
probe.** If the metric cannot separate the control from the suspects, discard the run —
a metric that reports every input as identical is broken, not informative. (Same family
as the RGB sampler that emitted 359 labelled rows from 6 decoded frames.)

### 4b. Averaging a whole row folds non-background into the "background"

Taking the mean of the entire label row as the background pulls in the mesh/gradient glow
and the ring arcs, inflating the denominator. That reported `sunrise` at 2.89 and `glass`
at 3.23 — both *actually* 5.04 and 5.64, i.e. fine. Vision said "clearly legible"; vision
was right and the number was wrong.

Measure **one label word**, glyph stroke against the local paper immediately around it:

```python
reg = a[1120:1180, 150:420].reshape(-1, 3)      # a single word, not the row
o = np.argsort(reg.sum(axis=1))
paper = reg[o[:len(reg)//3]].mean(axis=0)       # darkest third = local background
glyph = reg[o[-len(reg)//20:]].mean(axis=0)     # brightest 5% = stroke core
ratio = cr(glyph, paper)
```

Cross-check: this agreed with vision on all 14 kits (4.67–6.77) where the row-average
method disagreed on two.

### 4c. Averaging the accent of a two-hue kit is meaningless

`cyber_lime` averaged to a warm gold `(209,154,79)` — nearly identical to `mono_warm` —
because it draws acid lime `(160,224,0)` **and** magenta `(224,0,192)`. Opposite hues
cancel in the mean, inventing a colour present nowhere in the frame.

Quantise and cluster instead of averaging when a palette may be multi-hue:

```python
px = band[sat > 90]
uniq, cnt = np.unique(px // 32 * 32, axis=0, return_counts=True)
for i in np.argsort(cnt)[::-1][:5]:
    print(uniq[i], cnt[i])      # lime x16653, magenta x14027 — the real palette
```

---

## 5. Checklist for adding a kit

1. New `Theme` in `THEMES` (`brand.ts`) — change the **accent triad**, not just `bg`.
2. New `StyleKit` in `STYLE_KITS` — every field filled, referencing that palette by name.
3. `ratio(muted, bg) >= 4.7` computed, not eyeballed.
4. Render one identical scene through **every** kit; assert no pairwise distance < 15.
5. Measure sub-label contrast on the rendered pixels, one word, glyph vs local paper.
6. Look at a contact strip of the new kits and confirm the mood matches the intent —
   distinctness and legibility are both satisfiable by something ugly.

Kits need no Zod registration when `style` is a plain string on the spec; adding one
touches exactly two files.
