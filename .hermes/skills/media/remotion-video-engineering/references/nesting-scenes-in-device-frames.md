# Nesting a Scene Inside a Device Frame (or any sub-viewport)

One preset renders another inside a phone / tablet / browser chrome (`PhoneMockup` with
`innerPreset` + `innerProps`, `ScreenRecord`, any "UI on a device" shot). The nested scene
believes it owns a full canvas; the parent has to fit that canvas into a screen rectangle
with a **different aspect ratio**. Every defect in this file comes from that one mismatch.

Concretely: a 1080x1920 canvas (9:16) going into a phone screen of 9:19.5.

---

## 1. Never render the nested scene at screen size

The tempting fix — hand the child the screen's pixel dimensions — destroys it. Presets
derive every size from the canvas (`Math.round(height * 0.03)`), so a child laid out for a
~300px-tall viewport gets microscopic fonts and collapsed padding.

Render the child at **full canvas size** and CSS-`scale()` it into the screen. All the
interesting decisions are then about that scale factor.

---

## 2. The scale factor: cropping is worse than letterboxing

Two candidates, and they fail in opposite directions:

| Scale | Result |
|---|---|
| `max(screenW/width, screenH/height)` | fills the screen, **overflows the sides**, `overflow:hidden` crops them |
| `screenW / width` (fit width) | nothing cropped, leaves an unused band along the screen's long axis |

`max(...)` looks like the safe choice — no empty band, screen always full — and it is the
one to avoid. Do the arithmetic before believing a comment about it:

```python
W, H = 1080, 1920
bodyW = round(W * 0.62); bodyH = round(bodyW * 19.5 / 9)
bezel = max(6, round(bodyW * 0.022))
screenW, screenH = bodyW - 2*bezel, bodyH - 2*bezel      # 640 x 1422
sw, sh = screenW / W, screenH / H
print("fit-width  band :", screenH - H*sw)               # 284 px unused
print("fill  side crop :", (W*sh - screenW) / 2)         #  80 px EACH side
print("crop as % width :", (W*sh - screenW)/2/W*100)     # 7.4 %
```

**80px per side = 7.4% of the canvas width, gone.** In this repo the source comment called
that "a few pixels ... still reads correctly". It does not. It ate the first and last
characters of every line in a nested chat:

| Intended | Rendered |
|---|---|
| `Разбери код` | `Разбери к` |
| `Не могу помочь с этим` | `е могу помочь с этим` |
| `Модель` | `дель` |

That is the whole reason this class of bug survives: **a cropped frame still looks
plausible.** A letterboxed frame looks obviously unfinished and gets fixed on day one; a
frame where every word quietly lost a letter ships. Prefer the failure mode that is
visible.

Corollary for the *content* side: text destined for a device screen is competing for a
~640px-wide viewport, not 1080. Short strings. Verify, don't estimate.

---

## 3. Where to put the leftover band: anchor, don't stretch

Fitting width leaves `screenH - height*scale` unused (284px of 1422 here). Stretching the
wrapper does **not** stretch the child — the child lays out against its own canvas height,
so the slack simply reappears wherever the wrapper puts it. Only two things are real: the
scale factor, and which edge the child is pinned to.

```tsx
<div
  style={{
    position: 'absolute',
    top: screenH - height * (screenW / width),   // bottom-anchored
    left: 0,
    width,
    height,
    transform: `scale(${screenW / width})`,
    transformOrigin: 'top left',
  }}
>
```

Bottom-anchoring is right for any chat / feed / terminal: the input bar lands on the
screen's bottom edge and the slack sits above the first message — which is what a real
conversation looks like. Vertically-centred children (charts, stat rings, hero text) are
unaffected either way.

An intermediate attempt — fit width but give the wrapper `height: screenH / scale` — passed
a pixel probe (background reached within 1px of the screen bottom) and still looked wrong,
because the child's bottom-docked UI sat at *its own* canvas bottom, floating mid-screen
with dead space beneath. Pinning beats resizing.

---

## 4. Two probes, two different truths — you need both

This bug produced a direct contradiction worth internalising:

- **Pixel probe**: "bottom gap = 1px" → screen is full, nothing wrong.
- **Vision**: "large empty region, roughly the bottom third, no UI" → clearly wrong.

Both were accurate. The probe measured *fill* (do pixels differ from the base colour) and
the chat wallpaper did reach the bottom. Vision measured *semantic occupancy* (is there any
UI here) and the interactive row was floating far above the edge. A background that extends
to the edge satisfies every numeric test and still reads as broken.

Rules that follow:
- A "does the content reach the edge" metric cannot see a **wallpaper-only** region. Ask
  what the probe is actually sensitive to before trusting a pass.
- When vision and a number disagree, **neither wins by default** — find the quantity that
  explains both readings (here: fill vs. UI occupancy). Earlier in the same session the
  reverse happened, where vision flagged two style kits as too dim and the *per-word*
  measurement exonerated them; the row-average metric was the liar. Same discipline, other
  direction.
- Crop the exact screen rect and look at it alone. A device frame downscaled into a contact
  sheet hides both defect classes, and my own crop bounds were briefly suspected of causing
  the clipping — rule that out by finding the bright-pixel bbox in **full-frame coordinates**
  before blaming the render.

---

## 5. Parent effects can destroy the nested scene's entire purpose

Effects apply to the parent, including the screen. `RackFocus` on a `PhoneMockup` blurred
the phone screen into illegible smears — and the scene existed *to show a chat*. Same trap
for `TiltShift`, `BlurIn`, heavy `FilmGrain`, `GlitchBlock`.

If the nested content is the message, keep the parent's effects to camera moves that don't
touch focus or detail (`DollyIn`, gentle `HandheldDrift`) and put any texture on
neighbouring scenes instead.

---

## 6. Prove the fix is scoped: byte-identical frames

Changing shared nesting geometry touches every device scene in the project. The cheap proof
that only the intended layouts moved:

1. Render a **centred** nested child (e.g. `RingStats` inside the phone) before and after —
   rings must stay centred and fully visible.
2. Re-render unrelated scenes from another spec and compare file sizes. Here three
   `script3` frames came back **byte-identical** to their pre-change renders, which is
   stronger than "looks the same" — identical bytes mean that code path did not execute
   differently.

Note the inversion of the usual tell: elsewhere in this skill, *identical* PNG sizes across
*different* scenes signal a stale bundle or an error card. Identical sizes for the *same*
scene across a code change are exactly what you want. Same measurement, opposite meaning —
read it against what you changed.

---

## 7. Checklist

- [ ] Child rendered at canvas size, scaled — not laid out at screen size.
- [ ] Scale fits the width; no horizontal crop at any string length.
- [ ] Leftover band anchored to the edge the child's UI expects (bottom for chat/feed).
- [ ] Screen rect cropped out and inspected on its own, not as a thumbnail.
- [ ] Strings sized for the screen width (~60% of canvas), stress-tested with the longest.
- [ ] Parent effects don't blur or texture the screen contents.
- [ ] A centred nested child re-verified; unrelated scenes byte-compared.
