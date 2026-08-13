# Universal format handling and preset architecture

How to make a video pipeline aspect-agnostic, and how to organize presets so an agent
can pick one safely.

## 1. Format registry

Put geometry in the spec, never in a component. A single registry keyed by a short name
lets an agent select delivery format per job.

| name | dimensions | aspect | safeMargin | use |
|---|---|---|---|---|
| `vertical` | 1080x1920 | 9:16 | 120 | Shorts / Reels / TikTok / Telegram |
| `horizontal` | 1920x1080 | 16:9 | 90 | YouTube landscape, embeds |
| `square` | 1080x1080 | 1:1 | 90 | feed posts |
| `cinema` | 2560x1080 | 21:9 | 100 | ultrawide showcase |

```python
FORMATS = {
    "vertical":   dict(width=1080, height=1920, safe_margin=120),
    "horizontal": dict(width=1920, height=1080, safe_margin=90),
    "square":     dict(width=1080, height=1080, safe_margin=90),
    "cinema":     dict(width=2560, height=1080, safe_margin=100),
}
```

The spec carries the resolved values (`width`, `height`, `safeMargin`, `fps`) so the
renderer never has to know the registry, and an unknown format name fails in the backend
rather than producing a mis-sized render.

## 2. The branching pattern

Every preset asks the renderer for its actual dimensions and branches once:

```tsx
const { width, height } = useVideoConfig();
const vertical = height >= width;
```

Then derive layout from that flag — never from magic pixel constants:

| aspect | direction | type scale | padding |
|---|---|---|---|
| vertical | `flexDirection: column`, stacked | large (hero ~92px) | tall vertical padding |
| horizontal | `flexDirection: row` where sensible | smaller (hero ~76px) | wide side padding |
| square | column, tighter | medium | even |

```tsx
padding: vertical ? '70px 56px' : '60px 120px',
fontSize: vertical ? '40px' : '38px',
```

Rules:
- Respect `safeMargin` for **all** text so captions and UI never clip on any aspect.
- Scale `fontSize` by string length for long Russian text and set
  `overflowWrap: 'break-word'` — Cyrillic runs longer than English for the same content.
- Derive animation timing from `durationInFrames`, never hardcoded frame counts. At
  60 fps a hardcoded 30-frame delay is half the duration it was at 30 fps.
- **Test at least one non-vertical format before calling a preset done.** A preset that
  only works at 9:16 is half-finished.

## 3. Preset taxonomy

The split that matters operationally is **what data a preset needs**, because it decides
whether an auto-rotator may select it.

### Text-safe (rotation may pick these freely)
Need only `title` / `subtitle` / `text`, all derivable from narration.

| preset | purpose |
|---|---|
| `HeroKinetic` | headline, word-by-word scale-in |
| `TypewriterSub` | typewriter body copy / subtitles |
| `QuoteCard` | pull quote with optional `author` / `role` |
| `GridGridFloor` | 3D isometric grid backdrop with title |
| `ListReveal` | staggered bullet reveal |

### Data-driven (require explicit storyboard entry)
Cannot be filled from prose; rotation must never auto-select them.

| preset | required data |
|---|---|
| `StatCounter` | `statValue` (+ `statPrefix`/`statSuffix`/`statLabel`) |
| `SwipePanels` | `cards[]` |
| `CompareSplit` | two labeled sides |
| `FlowDiagram` | `nodes[]` / edges |
| `CodeReveal` | `code` string (+ language) |
| 3D model scenes | `modelUrl` and camera params |

Validation should encode this: a scene naming a data-driven preset without its data is a
spec error, not a render-time placeholder.

## 4. Storyboard vs. auto-rotation

Support both entry points:

- **Auto-rotation (default).** Given narration only, cycle text-safe presets across
  scenes so a five-scene short is not five identical cards. Rotate on a fixed order and
  avoid repeating the immediately previous preset.
- **Explicit storyboard.** The caller supplies a list of `{preset, data}` per scene.
  Required for any data-driven preset, and preferable whenever the content has real
  structure (a benchmark table wants `StatCounter`, a before/after wants `CompareSplit`).

A retry/repair pass must preserve storyboard intent: downgrading a failing scene to a
text preset is acceptable only for scenes that were text-safe to begin with.

## 5. 3D scene notes

- Match `@remotion/three` to the exact Remotion version; check with `npm ls remotion`
  rather than installing `@latest`.
- `@react-three/fiber@9` requires React 19. On React 18, install fiber v8 — the peer
  conflict is the failure, not the library.
- Keep 3D scenes deterministic: drive animation from the frame number, never from
  `Date.now()` or a random seed, or frames will not reproduce across a re-render.
- Load models from `staticFile()` and pre-check the asset exists in the backend; a
  missing `modelUrl` should be a spec validation error, not a blank scene.
