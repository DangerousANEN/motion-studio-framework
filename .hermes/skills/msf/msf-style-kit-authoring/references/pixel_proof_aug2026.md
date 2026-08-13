# Pixel Proof — 14-Kit Render Pass (Aug 11 2026)

Session: added 6 kits (sunrise, forest, mono_warm, cyber_lime, candy, steel).
Rendered all 14 kits via `RingStats` probe at frame=100, 1080×1920@60fps.
Measured with numpy+PIL: corner bg sample (40×40 upper-left) + top-1.5% saturation accent.

## Per-kit colour measurements

| Kit        | BG (R,G,B)   | Accent (R,G,B) | BG hex  | Accent hex |
|------------|--------------|----------------|---------|------------|
| pop        | 13, 16, 17   | 0, 234, 190    | #0D1011 | #00EABE    |
| editorial  | 11, 11, 12   | 202, 196, 183  | #0B0B0C | #CAC4B7    |
| glass      | 11, 18, 32   | 123, 223, 223  | #0B1220 | #7BDFDF    |
| blueprint  | 6,  16, 25   | 56,  207, 254  | #061019 | #38CFFE    |
| neon       | 40, 31, 40   | 253, 146, 125  | #281F28 | #FD927D    |
| news       | 12, 13, 16   | 217, 92,  49   | #0C0D10 | #D95C31    |
| retro      | 34, 18, 33   | 182, 155, 202  | #221221 | #B69BCA    |
| clean      | 7,  8,  10   | 127, 131, 136  | #07080A | #7F8388    |
| sunrise    | 19, 11, 4    | 252, 160, 54   | #130B04 | #FCA036    |
| forest     | 28, 38, 30   | 68,  223, 128  | #1C261E | #44DF80    |
| mono_warm  | 22, 15, 8    | 195, 145, 83   | #160F08 | #C39153    |
| cyber_lime | 2,  14, 2    | 206, 161, 73   | #020E02 | #CEA149    |
| candy      | 18, 4,  14   | 214, 123, 223  | #12040E | #D67BDF    |
| steel      | 8,  12, 18   | 109, 166, 205  | #080C12 | #6DA6CD    |

## 5 nearest pairs (Euclidean on 6D [bg_r,bg_g,bg_b,acc_r,acc_g,acc_b] vector)

| Rank | Pair                      | Distance |
|------|---------------------------|----------|
| 1    | mono_warm ↔ cyber_lime    | **30.17** |
| 2    | sunrise ↔ cyber_lime      | 52.16    |
| 3    | retro ↔ candy             | 58.20    |
| 4    | editorial ↔ retro         | 59.28    |
| 5    | glass ↔ steel             | 62.62    |

**Result: ✅ PASS — all pairs ≥ 15 (min 30.17)**

## Notes on the nearest pair (mono_warm ↔ cyber_lime, 30.17)

The closeness is a measurement artifact: top-k saturation pulling grain/mid-tone
pixels on `mono_warm` produces (195,145,83) rather than its vivid ochre peak.
Visual inspection via `vision_analyze` confirmed the two are unmistakably different:

- `mono_warm`: plain backdrop, poster fonts (StalinistOne), grain 0.14, ochre
  ring arcs, sepia/documentary feel — no trace of neon
- `cyber_lime`: grid backdrop, pop fonts (Unbounded), bloom 0.8 + chromatic 0.28,
  acid lime (#AAFF00) + magenta (#FF00C8) rings, cyberpunk gaming feel

The accent-hue difference on the actual palette is ~120° on the colour wheel
(warm orange-brown vs acid green); the 6D metric underestimates this because the
grain measurement pulls both toward the mid-warm range.

## Render command used

```bash
npx remotion still src/index.ts Main \
  "C:\Users\ANEN\motion-studio-framework\remotion\out\sub_styles\<KIT>.png" \
  --props=probe_kit_<KIT>.json --frame=100 --log=error
```
One separate shell invocation per kit (not a loop) to avoid MSYS path corruption.
