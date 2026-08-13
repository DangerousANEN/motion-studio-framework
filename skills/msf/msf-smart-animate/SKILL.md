---
name: msf-smart-animate
description: Use when a smart agent (level >= 3) creates custom Remotion presets as React components. Gate-checked.
---
# MSF Smart Animate — Custom React Video Generation

For smart agents (level ≥ 3) writing CUSTOM Remotion presets. Level < 3 → use `msf-dumb-animate`.

Repo: `C:\Users\ANEN\motion-studio-framework` · Remotion 4.x · React 18 · 1080x1920 @ **60 fps**

## Decide FIRST: customise, or author a new preset?

Your extra freedom is the freedom to **write React**, and that is also the most
expensive thing you can do — a new component is untested code in the render path.
Work down this ladder and stop at the first rung that solves the problem. Most
requests stop at rung 1 or 2.

**Rung 1 — an existing preset with different data. Always try this first.**
The library has 26 presets. Read the catalogue in `msf-dumb-animate` before
concluding something is missing; `RingStats`, `Bars3D`, `PhoneMockup`,
`ScreenRecord`, `VoiceMemo` and the social/learn/stage packs cover most shapes
people assume are absent. Check the registry, don't guess:
```bash
cd remotion && npx tsx -e "import {PRESETS,PRESET_NAMES} from './src/registry/presets'; \
  PRESET_NAMES.forEach(n=>console.log(n.padEnd(16), PRESETS[n].category, '|', PRESETS[n].summary))"
```

**Rung 2 — composition instead of code.** Combine what exists:
- wrap any preset in `effects[]` (96 effects) — camera moves, grades, particles
- add `overlays[]` — timer, notification, money HUD over any scene
- put a preset inside `PhoneMockup` via `innerPreset` / `innerProps`
- pick a different `style` kit, or override `accentColor` per scene
A "new" scene is often an existing preset + `HandheldDrift` + a `notification`.

**Rung 3 — extend an existing preset with a new prop.** If a preset is 90% right
and needs one behaviour, add an **opt-in** prop. This is how `TgChat` got
`compose`. Non-negotiable: the default must reproduce the old behaviour exactly,
so existing specs render identically. Add the field to `VideoSpec.schema.ts`,
`Scene` + `_CAMEL` in `msf/spec.py`, and re-render an OLD spec to prove nothing moved.

**Rung 4 — author a new preset.** Only when ALL of these hold:
1. No existing preset produces the shape, and you verified by listing the registry.
2. Effects + overlays + nesting cannot compose it (rung 2 genuinely fails).
3. It is not a variant of one preset — a variant is a prop (rung 3).
4. It will be reused, or the user explicitly asked for this scene.
5. You can render and visually verify it now, in this session.

If 1–4 hold but 5 does not, **do not write it**. An unverified preset in the
registry is worse than a missing one: the next agent picks it and ships a broken
frame. Say so plainly instead.

### Do NOT author a new preset when…
- …you haven't listed the registry. "I don't remember one" is not evidence.
- …the difference is colour, font, or pacing → that is a **style kit** (14 exist;
  add one in `styleKits.ts` + a palette in `brand.ts`, no React needed).
- …the difference is a camera move, grain, glitch, or particles → that is an **effect**.
- …the difference is one field (a badge, a second value, a toggle) → rung 3.
- …you are mid-render on a deadline and cannot verify pixels.

### Adding a style kit instead of a preset (the cheap win)
Recolouring the whole video needs no component. Add a `Theme` to `THEMES` in
`remotion/src/presets/brand.ts` and a `StyleKit` to `STYLE_KITS` in
`remotion/src/theme/styleKits.ts`. **Change the accent triad (`neon`/`cyan`/`gold`),
not just `bg`** — presets read their accent from `theme.neon` and series colours
from the triad, so a bg-only kit renders nearly identically to its parent. This
already happened: 8 kits shared 5 palettes and two pairs were pixel-identical.
Prove distinctness by rendering the same scene through every kit and measuring:
```bash
# render kit probes, then compare bg + accent vectors pairwise; no pair < 15 apart
```

## The wire contract (get this wrong and nothing renders)

Python emits **camelCase**; the Zod schema in `remotion/src/VideoSpec.schema.ts` is the
single source of truth. There is no snake_case anywhere on the wire.

```ts
type BaseSceneProps = {
  id: string;
  durationInFrames: number;      // NOT duration_in_frames
  preset: string;
  title?: string;
  subtitle?: string;             // NOT sub_text
  text?: string;
  bodyText?: string;
  accentColor?: string;          // a hex string, NOT 'gold' | 'neon' | 'cyan'
  badge?: string;
  statValue?: number; statPrefix?: string; statSuffix?: string; statLabel?: string;
  cards?: { title: string; description?: string; tag?: string; color?: string }[];
  audioUrl?: string;             // bare filename resolved via staticFile()
};
```

`Scene.to_dict()` in `msf/spec.py` performs the snake→camel conversion. Add a new field
in **both** places or it will be silently dropped by Zod.

## Writing a custom preset

Follow the shape of `remotion/src/presets/charts.tsx` — it is the reference for
structure, comments and conventions.

1. Component goes in `remotion/src/presets/custom/` (one-off) or its own pack
   file like `presets/social.tsx` (a themed group).
2. **Read palette and fonts from the style context, never hardcode them.** This
   is what makes a preset respond to all 14 style kits:
   ```tsx
   import { useStyle } from '../theme/StyleContext';
   import { Backdrop } from '../theme/Backdrop';
   const { theme, fonts, accent, surface } = useStyle();
   ```
   `<Backdrop />` first, then your content. Importing `BRAND` directly pins the
   preset to the `pop` palette and it will ignore the video's style.
3. Signature and animation:
   ```tsx
   export const MyPreset: React.FC<BaseSceneProps> = (props) => {
     const { width, height, fps, durationInFrames } = useVideoConfig();
     const frame = useCurrentFrame();
     const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
     const ease = resolveMotion(props.motion ?? props.intensity, fps, 'reveal');
     const v = ease(frame, 0, 1);   // (frame, from, to)
   ```
   The motion channel must be one of `camera | value | reveal | transform | opacity`
   (see `ChanneledMotion` in `lib/motion.ts`). There is **no** `'entrance'` channel —
   passing it is a TypeScript error. Use `reveal` for entrances, `value` for counting
   numbers, `camera` for moves, `opacity` for fades.
   All content stays inside `safe`. All sizes derive from `height`/`width`
   (`Math.round(height * 0.03)`), never absolute px.
4. **Registration — in a registry pack, NOT in SceneDispatcher.** The dispatcher
   resolves components from `PRESETS` now; adding a manual `switch` entry is
   obsolete. Create/extend a `remotion/src/registry/<pack>.ts` exporting a
   `PresetRegistry` (`component`, `category`, `summary`, `fields`, `dataDriven`)
   and merge it in `registry/presets.ts`. `PresetTypeSchema` derives its enum
   from `PRESET_NAMES` automatically — do not hand-edit the enum. Use an existing
   `PresetCategory`; a new category also needs `registry/types.ts`.
5. **New props: extend the schema, or read them through a local cast.** Official
   fields go in `BaseSceneSchema` (`VideoSpec.schema.ts`) **and** `Scene` +
   `_CAMEL` in `msf/spec.py` — both, or Python silently drops them. While
   iterating, `BaseSceneSchema` is `.passthrough()`, so
   `const { myField } = props as BaseSceneProps & { myField?: string }` works
   without touching the schema.
6. Timing must scale with the scene: derive from `durationInFrames`, never hardcode
   frame counts. At 60 fps a hardcoded 30-frame delay is half the length it was at 30 fps.
7. **Randomness must be seeded** (`mulberry32`, see `fx/effects/camera.tsx`).
   `Math.random()` flickers because Remotion renders frames out of order.
8. Long Russian strings must not overflow 1080px — scale `fontSize` by text length and
   set `overflowWrap: 'break-word'`.

### Verify a new preset before registering it as done
```bash
cd remotion && npx tsc --noEmit
npx remotion still src/index.ts Main "C:\...\out\probe.png" --props=probe.json --frame=70 --log=error
```
Then check the **file size in bytes** and look at it with `vision_analyze`.
`remotion still` exits 0 even when the component threw and the frame is blank —
exit code is not evidence, bytes and pixels are. For a preset with distinct
states (a reveal, a countdown), render two frames and confirm they differ.

## Brand palette
`bg #0E0F11` · `surface #16181C` · `gold #E6C475` · `neon #00FF88` · `cyan #00D4FF` · `text #FFFFFF` · `muted #8B92A0`

## Rendering
Always go through the graph — it handles TTS, real WAV-derived durations, validation,
mastering and QA:
```python
from msf.graph.video_graph import build_msf_graph
result = build_msf_graph().invoke({"text": "...", "preset": "MyPreset", "agent_level": 3,
                                   "output_path": r"...\out.mp4"})
```
Rendering directly with `npx remotion render` is for isolated preset debugging only —
`--props=<abs path to props.json>` is mandatory, otherwise `getInputProps()` returns `{}`.

## Verification before reporting done
```bash
npx tsc --noEmit -p remotion/tsconfig.json
ffprobe -v error -show_entries stream=width,height,r_frame_rate,sample_rate \
        -of default=noprint_wrappers=1 <final_mp4>
ffmpeg -hide_banner -nostats -i <final_mp4> -af volumedetect -f null -
```
Then inspect a QA frame with `vision_analyze`. A TypeScript-clean render can still be a
blank or placeholder frame — pixels are the only proof.

## Pitfalls
- **`getInputProps()` returns `{}` without `--props`.** The schema used to carry a demo
  default, so a totally disconnected pipeline still produced a polished-looking reel.
  Never restore a `.default()` on `scenes` — it hides exactly this class of bug.
- **Mastering cannot write over its own input** — raw and final MP4 must be distinct paths.
- **`loudnorm` upsamples internally**; pin `-ar 48000` on the output.
- **`BRAND.muted` used to be undefined**, silently yielding `color: undefined`. Import
  from `presets/brand.ts` rather than re-deriving the palette.
