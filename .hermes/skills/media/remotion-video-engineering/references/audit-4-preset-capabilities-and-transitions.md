# Audit #4: Preset Capabilities, Capacity Boundaries, Fixed Font Sizes & Transition Defects

This document records the exact findings from Audit #4 of the Motion Studio Framework (MSF) Remotion rendering engine, covering prop contracts, component capacity limits, fixed font risks, layout formulas, Zod passthrough behavior, and `@remotion/transitions` fade mechanics.

---

## 1. Preset Prop Mapping & Capacities

| Preset | File | Key Props & Defaults | Capacity Boundaries & Risk Points |
|---|---|---|---|
| **CountdownHero** | `src/presets/stage.tsx` | `from=3`, `finalWord='СТАРТ'`, `subtitle` | Calculated beats: `fromProp + 1`. Requires exit to land exactly on beat boundary to avoid black gaps. |
| **VersusSplit** | `src/presets/stage.tsx` | `left={name:'КОМАНДА А'}`, `right={name:'КОМАНДА Б'}`, `vsLabel='VS'` | `nameFontSize` uses `colWidth / (longestName * 0.62)`. Multi-word/long model names ("Qwen3.6-35B-A3B") wrap and collide with central VS label. |
| **Bars3D** | `src/presets/charts.tsx` | `segments` (default 4 items), `valueSuffix=''`, `barDepth` | Hard slice: `items.slice(0, 8)`. Items >8 are silently dropped. Labels under narrow bars (`barW`) clip when string length > 10 chars. |
| **Leaderboard** | `src/presets/social.tsx` | `rows` (default 5 rows), `title='Leaderboard'`, `valueSuffix='pts'` | Row height `rowH` scales down with `rows.length`, but `fName` (40px) and `fRank` (42px) do **NOT** scale down. At **>7-8 rows**, text overflows row height and overlaps. |
| **SubscribeCTA** | `src/presets/social.tsx` | `channelName='TechChannel'`, `subscribers=142000`, `buttonText='Subscribe'`, `subscribedText='Subscribed'` | Multi-phase animation anchored to fractions of `durationInFrames` (0.25, 0.55, 0.65, 0.72, 0.75). |
| **HeroKinetic** | `src/presets/HeroKinetic.tsx` | `title`, `text`, `subtitle`, `badge`, `accentColor` | Uses `fitOneLine` for title sizing against `safe.width`. |
| **PhoneMockup** | `src/presets/device.tsx` | `innerPreset`, `innerProps`, `device='phone'`, `tilt=-2`, `depth=0` | Scales canvas-sized nested scene to fit phone screen. Avoids micro-font layout. |
| **TgChat** | `src/presets/TgChat.tsx` | `messages` (default 3), `contactName` (`title ?? 'Аня'`), `contactStatus='в сети'`, `compose`, `typing=true`, `showCursor=true`, `showInputBar=true`, `sendAtProgress=0.72` | Input field wraps with `textOverflow: 'ellipsis'` for typing animation. High character count increases typing speed dynamically. |
| **CodeReveal** | `src/presets/CodeReveal.tsx` | `code`, `language`, `title` | Dynamic `fitOneLine` calculation based on the longest line in `code`. |
| **QuizCard** | `src/presets/learn.tsx` | `question`, `options` (4 defaults), `correctIndex=0`, `revealAtProgress=0.55` | Fixed vertical stack height (`4 * cardH + 3 * cardGap`). **>4 options** spill outside `safeArea` and clip. |
| **TokenCloud3D** | `src/presets/three/TokenCloud3D.tsx` | `pointCount=900`, `title`, `subtitle` | Three.js point cloud render with DOM text overlay. |
| **LayerStack3D** | `src/presets/three/LayerStack3D.tsx` | `layers` (default 1), `title`, `subtitle` | **>6 layers** extend beyond Three.js camera FOV (`position: [0, 1.6, 10.5]`) and overlap DOM sidebar labels with header text. |
| **RingStats** | `src/presets/charts.tsx` | `segments` (default 3), `valueSuffix='%'`, `ringMax=100` | Hard slice: `items.slice(0, 6)`. Grid switches to 2 rows at 4-6 items. Label font size is fixed (36px); cell width shrinking causes label text overflow. |

---

## 2. Fixed Font Size Risks vs Variable-Length Content

Presets that use `Math.round(height * fraction)` without `fitOneLine` or bounds checking risk text clipping / overlap:

1. **Leaderboard (`src/presets/social.tsx`)**: `fName` is hardcoded to `Math.round(height * 0.021)` (40px on 1080x1920) with `textOverflow: 'ellipsis'`. Long model/channel names (e.g. `Qwen3.6-35B-A3B`) are prematurely truncated.
2. **VersusSplit (`src/presets/stage.tsx`)**: `nameFontSize` divides by `longestName * 0.62`. The 0.62 factor assumes narrow Latin glyphs; wide Cyrillic or multi-token names wrap onto 2 lines and hit the `VS` graphic.
3. **Bars3D & RingStats (`src/presets/charts.tsx`)**: `RingStats` labels use fixed 36px (`height * 0.019`), which overflows when 6 items shrink the cell width to ~270px.
4. **QuizCard (`src/presets/learn.tsx`)**: `optFontSize` is fixed at 54px (`height * 0.028`), causing long multiline option texts to overflow option cards.

---

## 3. Transition Fade Defect & Fix

### Defect: Visual Pop/Cut in `@remotion/transitions` `fade()`
When using `fade()` from `@remotion/transitions`, scenes appear to cut or pop abruptly rather than smoothly blending.

### Root Cause
In `@remotion/transitions/dist/presentations/fade.js`, the default options leave `passedProps.shouldFadeOutExitingScene` as `undefined` (falsy):
```js
style = {
  opacity: isEntering
    ? presentationProgress
    : passedProps.shouldFadeOutExitingScene
        ? 1 - presentationProgress
        : 1
}
```
As a result, the exiting scene remains at `opacity: 1.0` throughout the transition duration while the entering scene fades in over top. When the transition window ends, the exiting scene is suddenly removed from the DOM, causing a visual flash/cut if the top scene has any transparency or during complex composite layers.

### Fix
In `src/lib/transitions.ts`, update the `fade` case to explicitly request exiting scene fade-out:
```ts
case 'fade':
  return fade({ shouldFadeOutExitingScene: true });
```

### Verified — and it retires an earlier prohibition
Applied and **proven** on a rendered mp4: before, 0 of 57 frames in a 48-frame overlap
window showed both scenes; after, vision confirms both captions superimposed at equal
opacity mid-window. Probe design — including the colour mask that goes blind at exactly
the crossover — is in `references/wiring-voiceover-and-proving-a-crossfade.md` §7.

Consequence for scripting: the house rule "never use `fade` between key scenes, build all
dynamics from per-scene effects" was a workaround for this bug and no longer applies.
Transitions are usable again; anything still forbidding them on these grounds is stale.

---

## 4. Zod Schema Passthrough Behavior (`VideoSpec.schema.ts`)

`BaseSceneSchema` and sub-schemas (e.g., `ChatMessageSchema`, `CardSchema`) employ `.passthrough()`:
* **Effect**: Unknown or misspelled keys (e.g., `message` instead of `messages`, `name` instead of `contactName`) pass Zod validation without throwing errors or being stripped.
* **Consequence**: The React preset receives `undefined` for expected props and silently falls back to hardcoded default values.
* **Recommendation**: Ensure validator tools check for unexpected keys or verify that emitted JSON spec keys strictly match expected preset prop names before passing to the renderer.
