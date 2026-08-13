---
name: msf-style-kit-authoring
description: Use when adding MSF style kits or palettes. Pixel-proof req.
tags: [msf, remotion, style-kit, palette, pixel-proof]
---
# MSF Style Kit Authoring

Use when: adding new visual themes/kits to the Motion Studio Framework.
Covers `brand.ts` palette extension, `styleKits.ts` kit definitions, and the
mandatory pixel-distinctness verification pipeline.

## File locations

| File | Purpose |
|---|---|
| `remotion/src/presets/brand.ts` | `Theme` type + `THEMES` record (palettes) |
| `remotion/src/theme/styleKits.ts` | `STYLE_KITS` record (kits referencing themes) |

## Step 1 — Add a new palette (`brand.ts`)

Each new kit MUST have its own **dedicated** `Theme` object. Never point two kits
at the same theme key — even with different motion/backdrop/surface settings, two
kits sharing a theme render pixel-identical frames (this happened with `editorial`+`clean`
sharing `noir`, and `neon`+`retro` sharing `sunset`).

```ts
const myTheme: Theme = {
  ...pop,                   // spread defaults so no field is undefined
  bg: '#RRGGBB',            // unique background darkness
  surface: '#RRGGBB',
  gold:  '#RRGGBB',         // ── The accent triad that
  neon:  '#RRGGBB',         //    presets actually READ.
  cyan:  '#RRGGBB',         //    Vary all three; bg-only
  text:  '#RRGGBB',         //    changes do nothing visible.
  muted: '#RRGGBB',
  darkBorder: '#000000',
  shadowColor: '#000000',
  accentCyan:  '#RRGGBB',   // aliases used by 3D presets — mirror cyan
  accentGreen: '#RRGGBB',   // mirror neon
  accentWarm:  '#RRGGBB',   // mirror gold
};
```

Then add the key to `THEMES` at the bottom of the existing map.

## Step 2 — Add a new kit (`styleKits.ts`)

```ts
myKit: {
  name: 'myKit',
  description: '…',
  theme: 'myTheme',      // must match the THEMES key above
  fonts: 'pop',          // 'pop' | 'editorial' | 'modern' | 'news' | 'poster'
  motion: { damping: 14, stiffness: 150, mass: 0.8, tilt: 0, staggerScale: 1 },
  backdrop: 'grid',      // 'grid'|'mesh'|'noise'|'dots'|'scanlines'|'plain'
  effects: { grain: 0.05, vignette: 0.28, bloom: 0.35, chromatic: 0.12, scanlines: 0 },
  transition: 'slide',
  surface: 'soft',       // 'brutal'|'soft'|'glass'|'flat'
},
```

**Differentiation guidelines** — make these orthogonal across kits:
- `backdrop`: each mood-pair should differ (energetic=grid, calm=noise, premium=mesh)
- `effects.bloom`: low for documentary (<0.15), high for neon/gaming (>0.6)
- `effects.grain`: low for clean (<0.06), high for retro/film (>0.12)
- `effects.chromatic`: 0 for editorial/monochrome, high for cyberpunk (>0.2)
- `motion.damping`: high (>20) for slow/calm, low (<10) for aggressive/energetic
- `surface`: brutal=pop/gaming, glass=premium, flat=editorial, soft=warm

## Step 3 — TypeScript check

```bash
cd remotion && npx tsc --noEmit
```
Must return exit 0, empty output. Do this BEFORE any rendering.

## Step 4 — Pixel-distinctness proof (mandatory)

### 4a. Probe JSON files

One per kit, named `probe_kit_<KIT>.json` in `remotion/`:

```json
{
  "width": 1080, "height": 1920, "fps": 60, "format": "vertical",
  "style": "<KIT>",
  "scenes": [{"id":"s1","preset":"RingStats","durationInFrames":120,
    "title":"Стиль: <KIT>",
    "segments":[{"label":"Скорость","value":92},
                {"label":"Точность","value":78},
                {"label":"Цена","value":41}]}]
}
```

### 4b. Render one frame per kit

**CRITICAL: One separate `terminal()` call per kit — NO bash loop with kit
variable in double-quoted Windows path.** MSYS (git-bash) corrupts the output
path when variables expand inside double-quoted strings, silently writing all
frames to the same file or a broken path.

```bash
npx remotion still src/index.ts Main \
  "C:\Users\ANEN\motion-studio-framework\remotion\out\sub_styles\<KIT>.png" \
  --props=probe_kit_<KIT>.json --frame=100 --log=error
```

Check all PNG files are non-zero bytes before proceeding.

### 4c. Distance measurement (numpy + PIL)

```python
import numpy as np; from PIL import Image
import math, os; from itertools import combinations

PNG_DIR = r'C:\Users\ANEN\motion-studio-framework\remotion\out\sub_styles'
KITS = [...]  # all kit names, old + new

def sample_bg(arr, region=40):
    return arr[:region, :region, :3].reshape(-1,3).mean(axis=0).astype(float)

def sample_accent(arr, frac=0.015):
    px = arr[:,:,:3].reshape(-1,3).astype(float)
    sat = px.max(axis=1) - px.min(axis=1)
    n = max(1, int(len(sat)*frac))
    return px[np.argpartition(sat,-n)[-n:]].mean(axis=0)

results = {k: {'bg': sample_bg(a:=np.array(Image.open(
    os.path.join(PNG_DIR,f'{k}.png')).convert('RGBA'))),
    'acc': sample_accent(a)} for k in KITS}

def dist(k1,k2):
    v1=np.concatenate([results[k1]['bg'],results[k1]['acc']])
    v2=np.concatenate([results[k2]['bg'],results[k2]['acc']])
    return math.sqrt(float(np.sum((v1-v2)**2)))

pairs = sorted([(dist(a,b),a,b) for a,b in combinations(KITS,2)])
for d,a,b in pairs[:5]: print(f"  {a} ↔ {b}: {d:.2f}")
assert pairs[0][0] >= 15, f"FAIL: {pairs[0]}"
```

**Threshold: all pairs ≥ 15.** If any fail: shift accent hue ≥ 30° or change bg
darkness, re-render only the failing kit(s), re-run.

### 4d. Visual spot-check

`vision_analyze` on at least the 3 nearest pairs. Numerics are necessary but not
sufficient — same backdrop + same fonts can look identical even at dist=30.

## Known pitfalls

- **Heavy grain fools top-k accent sampling.** `retro`, `mono_warm` pull warm
  neutral tones as "accent" due to grain pixels. Trust dist ≥ 15 as the gate.

- **`mono_warm` vs `cyber_lime` measure ≈ dist 30 but look obviously different.**
  The backdrop+effects combo (plain+grain vs grid+bloom) is what distinguishes
  them. Don't chase the number if dist ≥ 15 and visual passes.

- **Pre-existing syntax errors in `registry/presets.ts` surface on cache bust.**
  First N kit renders use the cached bundle and succeed. After any source change
  clears the cache, esbuild hits a pre-existing `Unexpected ")"` or duplicate
  import and exits 1. Inspect and fix `registry/presets.ts` before blaming the
  new palette code. Look for: duplicate `import` lines, extra `);` after the
  `mergeRegistries(…)` closing paren.

- **Reusing a theme key across two kits = pixel-identical frames** regardless of
  motion/backdrop/surface differences. One theme → one kit, always.

- **bg-only palette changes do nothing visible.** `Backdrop` glow and ring colours
  both read `theme.neon`/`cyan`/`gold`. Vary the full accent triad.

## Validation checklist

- [ ] `npx tsc --noEmit` → exit 0, empty output
- [ ] All kit PNGs rendered, non-zero bytes
- [ ] All pairwise distances ≥ 15
- [ ] `vision_analyze` spot-check on ≥ 3 nearest pairs passes visually
- [ ] Each new theme key is unique in `THEMES`
- [ ] Each new kit's `theme` field matches an existing `THEMES` key exactly

## Established kit catalogue (as of Aug 2026)

| Kit | Theme key | Mood | Backdrop | Fonts |
|---|---|---|---|---|
| pop | pop | neo-brutalism | grid | pop |
| editorial | paper | swiss editorial | plain | editorial |
| glass | glass | glassmorphism | mesh | modern |
| blueprint | blueprint | technical | grid | modern |
| neon | sunset | cyberpunk | noise | pop |
| news | broadcast | ticker/urgent | dots | news |
| retro | vhs | CRT/VHS | scanlines | poster |
| clean | ink | max legibility | plain | modern |
| sunrise | sunrise | warm/optimistic | mesh | editorial |
| forest | forest | eco/calm green | noise | modern |
| mono_warm | mono_warm | sepia/documentary | plain | poster |
| cyber_lime | cyber_lime | gaming/hype | grid | pop |
| candy | candy | pastel pop | dots | modern |
| steel | steel | B2B/industrial | grid | news |

See `references/pixel_proof_aug2026.md` for the full pairwise distance matrix.
