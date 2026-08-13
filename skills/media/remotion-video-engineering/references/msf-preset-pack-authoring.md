# MSF Preset Pack Authoring — Patterns & Pitfalls

Concrete lessons from authoring the `learn` preset pack (QuizCard, ProgressPath,
DefinitionCard, TimelineReveal). Applies to any new preset pack added to
`motion-studio-framework`.

---

## `resolveMotion` channel — no `'entrance'` channel

`resolveMotion(config, fps, channel)` only accepts channels defined in `ChanneledMotion`
(`lib/motion.ts`). The valid values are:

```
'camera' | 'value' | 'reveal' | 'transform' | 'opacity' | undefined
```

**`'entrance'`** is NOT a valid channel. TypeScript will reject it with TS2345.

**Mapping intent → channel:**

| Animation intent | Use channel |
|---|---|
| Element enters (fade/slide in) | `'reveal'` |
| Number counting / progress | `'value'` |
| Camera pan, dolly, tilt | `'camera'` |
| Scale, rotate, translate | `'transform'` |
| Pure opacity fade | `'opacity'` |

For a **global block fade-in** (entire composition entrance opacity), `'opacity'` works
best. For a per-element staggered entrance, use `'reveal'`.

> **Stage pack note:** In the stage pack (LyricLines, ScoreHud, CountdownHero,
> VersusSplit), `'opacity'` was chosen for the top-level `blockOpacity / globalOpacity`
> and the panel slide effects were expressed with plain `interpolate()` — the motion
> config only governs the global fade envelope.

---

## Pack registration: temporary-add + git-revert pattern

The workflow for verifying a new pack without leaving permanent changes to `presets.ts`:

1. **Add** the pack to `mergeRegistries()` in `src/registry/presets.ts`:
   ```ts
   import { LEARN_PRESETS } from './learn';
   export const PRESETS = mergeRegistries(CORE_PRESETS, UI_MOCK_PRESETS, MEDIA_PRESETS, LEARN_PRESETS);
   ```
2. **Run TypeScript**: `npx tsc --noEmit` — must show 0 errors.
3. **Render all preset frames** (see probe recipe below).
4. **Revert**: `git checkout -- src/registry/presets.ts`

This is the approved subagent workflow. The parent orchestrator wires packs intentionally
at integration time. Do NOT leave `presets.ts` modified.

---

## Concurrent subagent collision on presets.ts

`presets.ts` is the highest-contention file in the MSF repo. When several subagents run
in parallel, each one patches this file and the results can be corrupted:
- Duplicate `import` lines
- Duplicate closing parentheses `)` on `mergeRegistries`
- Competing imports that reference each other's pack name (causing TS/runtime errors)

**Recovery pattern:**
1. Read the current state with `read_file` before writing.
2. If the file is broken, write the full correct content with `write_file` (not `patch`).
3. Include ALL previously-present packs (social, stage, etc.) — don't clobber siblings.
4. After your verification pass, `git checkout --` to restore the original.

**Safe check after writing:** `npx tsc --noEmit 2>&1 | grep "your-file.tsx"` — confirm
only YOUR file's issues appear, not pre-existing foreign errors from sibling agents.

---

## Two-frame verification for state-revealing presets

For presets that have distinct visual states (before/after a reveal, countdown states,
answer-shown vs. answer-hidden), render **two frames** and compare file sizes:

```bash
# Before reveal (frame 40, revealAtProgress=0.45 → reveals at frame 81)
npx remotion still src/index.ts Main "C:\...\QuizCard_before.png" \
  --props=probe.json --frame=40 --log=error

# After reveal
npx remotion still src/index.ts Main "C:\...\QuizCard_after.png" \
  --props=probe.json --frame=90 --log=error

# Compare sizes — after must be larger (more pixels = green highlight + checkmark)
ls -la out/sub_learn/QuizCard_*.png
```

The post-reveal PNG **must be larger** (by visual content: coloured borders, ✓/✗ glyphs).
If sizes are identical, the reveal logic didn't fire. This is pixel-level proof that
exit code 0 alone cannot provide.

---

## Probe JSON recipe for each preset type

### QuizCard
```json
{
  "width": 1080, "height": 1920, "fps": 60,
  "durationInFrames": 180, "format": "vertical",
  "scenes": [{
    "id": "quiz-1", "durationInFrames": 180, "preset": "QuizCard",
    "question": "Ваш вопрос здесь?",
    "options": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"],
    "correctIndex": 0,
    "revealAtProgress": 0.45
  }]
}
```
Render frame 40 (before reveal) and frame 90 (after); compare sizes.

### ProgressPath
```json
{
  "scenes": [{
    "preset": "ProgressPath",
    "title": "Заголовок пути",
    "steps": [
      {"label": "Шаг 1", "description": "Описание"},
      {"label": "Шаг 2", "description": "Описание"}
    ],
    "currentStep": 1,
    "orientation": "vertical"
  }]
}
```

### DefinitionCard
```json
{
  "scenes": [{
    "preset": "DefinitionCard",
    "term": "Термин",
    "definition": "Полное определение термина...",
    "example": "code example here",
    "source": "Источник, автор"
  }]
}
```

### TimelineReveal
```json
{
  "durationInFrames": 240,
  "scenes": [{
    "durationInFrames": 240, "preset": "TimelineReveal",
    "title": "Хронология",
    "events": [
      {"date": "2020", "label": "Событие", "description": "Описание"},
      {"date": "2022", "label": "Следующее", "description": "Описание"}
    ]
  }]
}
```
Use longer durationInFrames (240) to ensure all events have time to appear.

---

## Identical file sizes across different scenes = you are rendering an error card

The single most useful tell in this whole workflow. Eleven "different" presets rendered
to **byte-identical 165 943-byte PNGs**. Exit code was 0, the files existed and were
comfortably over the 50 000-byte threshold, and `tsc` was clean — every signal the
checklist asks for was green.

The frame was a red `RENDER ERROR` card listing the valid preset names. `Root.tsx`
gates the spec through `safeParse`; on failure it renders an error composition instead
of throwing, so **the renderer reports success while producing the same wrong frame for
every input**.

Make this an explicit assertion, because no per-file check can catch it:

```python
sizes = {name: os.path.getsize(png) for name, png in rendered.items()}
dupes = [n for n, v in sizes.items() if list(sizes.values()).count(v) > 1]
assert not dupes, f"identical sizes — suspect a shared error card: {dupes}"
```

Two causes seen, in order of likelihood:

1. **The pack is not wired into the registry** (or a sibling agent reverted it), so the
   Zod enum never learned the new names. Read the error card: it *prints the enum it is
   validating against*. Count the names — if it lists 26 while the registry has 38, the
   spec is being checked against a stale enum.
2. **A stale bundle cache.** A 438 MB `node_modules/.cache` kept serving a module graph
   from before the packs existed, so `npx tsx` reported the new count while the *browser
   bundle* validated against the old one. `rm -rf node_modules/.cache` and re-render;
   a changed byte count confirms the cache was the cause.

Diagnose in Node before touching component code — it separates bundler state from logic:

```ts
// dbg_parse.ts — run with `npx tsx dbg_parse.ts`
import { VideoSpecSchema } from './src/VideoSpec.schema';
import { PRESET_NAMES } from './src/registry/presets';
console.log('names:', PRESET_NAMES.length, '| mine?', PRESET_NAMES.includes('QuizCard'));
const r = VideoSpecSchema.safeParse(JSON.parse(fs.readFileSync('probe.json', 'utf8')));
console.log('parse ok?', r.success);
if (!r.success) console.log(JSON.stringify(r.error.issues[0]).slice(0, 300));
```

Write this to a **file**; `npx tsx -e "..."` silently produced no output at all, and a
heredoc into a non-writable path fails with `Permission denied` while `tsx` then reports
a misleading `ERR_MODULE_NOT_FOUND`.

Note that a wrong *enum value* is only one way to fail this parse. Anything invalid in
the spec does it — including a transition name you assumed existed (`dissolve` is not in
the 18-value list). The composition then falls back to its 120-frame default, so an
11-second video renders as 2 seconds and `ffprobe` shows `nb_frames=120`. **Treat a
suspiciously small output and a duration equal to the default as a failed parse, not a
render bug.**

## Shared schema fields: check for a duplicate before adding one

Adding preset fields to a large `BaseSceneSchema` collides with what is already there.
Two real collisions in one edit: `author` (already present for a quote preset) and
`steps` (already an array of a stricter type). Duplicate keys in a Zod object literal
are a TS1117 error, and *widening* the existing one broke an unrelated preset that
indexed `.detail` on the element without narrowing.

Before adding fields, list what exists:

```bash
grep -nE "^    (author|steps|comments|source|lines):" src/VideoSpec.schema.ts
```

Then reuse rather than redeclare, and say so in a comment so the next author does not
re-add it.

### Two silent data losses in a shared step/item schema

Both bugs were invisible to `tsc` and to every render:

- **A non-passthrough object strips undocumented keys.** `z.object({label, detail})`
  parsed `{label, description}` "successfully" and delivered `{label}` — the
  descriptions vanished with no error anywhere. Add `.passthrough()` *and* declare the
  field the preset documents.
- **A documented shorthand was rejected outright.** Docs advertised `steps: ['a','b']`;
  the schema demanded objects, so the whole spec failed to parse (→ error card, per
  above). Accept both shapes with a union whose string branch **transforms to the full
  object type**, not a narrower one — returning `{label}` alone re-narrows the union and
  breaks consumers reading `.detail`:

```ts
export const StepListSchema = z.array(
  z.union([
    z.string().transform((label): { label: string; detail?: string; description?: string } =>
      ({ label })),
    StepSchema,
  ])
);
```

Verify by parsing both shapes and printing what survived — a successful parse is not
proof the data is still there:

```
objects+description => parse OK  kept: [{"label":"Спек","description":"детали"}]
plain strings       => parse OK  kept: [{"label":"Спек"}]
```

## Layout defects that survive every numeric check

Four defects passed `tsc`, byte thresholds and the children's own review. Each has a
reusable cause:

| Symptom | Cause | Fix |
|---|---|---|
| Blank frame between countdown digits | Exit fade ended at `0.55 + 0.35 = 0.90` of the beat, leaving ~10 % transparent | Derive `exitDur = beatFrames - exitStart` so the exit lands exactly on the boundary |
| Name wraps mid-word and hits a centred label | Font budgeted from `safe.width * 0.44 * 1.8` — 1.8× more room than the column has | Budget from the real column width (`chars * ~0.62em`), and `whiteSpace: 'nowrap'` — an identifier must not break |
| Two columns collide with a centre element | Both used `justifyContent:'center'` over the full safe height, i.e. exactly where the centre label sits | Offset the columns ±`safe.height * 0.17` |
| Scrolling list paints over its own header | Past items translate up unbounded; a flex parent does not clip a transform | Fixed-height window + `overflow: hidden` |
| Counter prints half-cut digits | Travelled a full `fontSize` inside a `fontSize * 1.3` bottom-aligned window | Keep travel < slack (≈`0.34 * fontSize`), centre-align, widen to `1.45` |

The generalisation worth carrying: **an animation whose in/out envelopes are expressed
as independent fractions of a beat will leave a hole unless the fractions are forced to
meet.** Check the arithmetic (`exitStart + exitDur` vs `beatFrames`) rather than
sampling frames and hoping.

## Rendering checklist for a new pack

```bash
# 1. TypeScript — zero errors from YOUR files
npx tsc --noEmit 2>&1 | grep -v "social.tsx\|stage.tsx"

# 2. Create output dir
mkdir -p out/sub_learn

# 3. Render each preset — SEPARATE commands per preset, full Windows path
npx remotion still src/index.ts Main "C:\Users\ANEN\...\out\sub_learn\QuizCard.png" \
  --props=probe_learn_QuizCard.json --frame=70 --log=error

# 4. Verify sizes
ls -la out/sub_learn/*.png   # all must be > 50000 bytes

# 5. Revert presets.ts
git checkout -- src/registry/presets.ts
```

**Do NOT use bash loop variables with Windows absolute paths** — the shell
interpolation breaks the path. Call the command separately for each preset.

---

## `safeArea` props cast: use `SafeAreaMode`, NOT `string`

`getSafeArea(width, height, mode)` expects `SafeAreaMode | undefined` (`'platform' | 'loose' | 'none' | 'custom'`).
Casting `props.safeArea as string` is a TS2345 error. Always import the type and cast to it:

```tsx
import { getSafeArea, type SafeAreaMode } from '../lib/safeArea';

const safe = getSafeArea(
  width, height,
  (props.safeArea as SafeAreaMode | undefined) ?? 'platform'
);
```

---

## Identical file sizes ≠ different presets rendered

When the probe JSON is wrong, ALL different preset probes render as the **same fallback preset**
(e.g. the first scene in the registry like StatCounter or HeroKinetic). They produce the
**exact same byte count** — e.g. all four probes returning 165,943 bytes.

**Root cause:** a probe JSON with scene props at the TOP level (not inside `scenes[]`)
is treated as a `VideoSpec` with no scenes, which falls back to a default or errors silently.

**Detection:** if two structurally different presets produce the same file size, the probe
JSON is wrong or the preset isn't registered.

**Fix:** always structure probes as:
```json
{
  "width": 1080, "height": 1920, "fps": 60,
  "durationInFrames": 150, "format": "vertical",
  "scenes": [
    { "id": "probe-1", "durationInFrames": 150, "preset": "MyPreset", ...fields }
  ]
}
```

After re-rendering with corrected probe JSON, each preset will typically produce **different**
byte counts because they have different visual content. Confirm with `vision_analyze` on at
least one frame.

---

## Social pack probe recipes (PostCard, CommentWall, SubscribeCTA, Leaderboard)

### PostCard
```json
{
  "width": 1080, "height": 1920, "fps": 60,
  "durationInFrames": 150, "format": "vertical",
  "scenes": [{
    "id": "postcard-probe", "durationInFrames": 150, "preset": "PostCard",
    "author": "Aria Nova", "handle": "@arianova",
    "text": "Just built something that will change how we create video content forever 🚀",
    "likes": 48200, "reposts": 6700, "comments": 2150, "verified": true
  }]
}
```
Frame 70 shows metric counters mid-scroll. Frame 30 shows card just appeared with counters near 0.
Two-frame check proves counter animation fires.

### CommentWall
```json
{
  "width": 1080, "height": 1920, "fps": 60,
  "durationInFrames": 180, "format": "vertical",
  "scenes": [{
    "id": "commentwall-probe", "durationInFrames": 180, "preset": "CommentWall",
    "title": "Live Comments 💬",
    "comments": [
      {"author": "Maria K",    "text": "This is absolutely incredible! 🔥", "likes": 142},
      {"author": "Dev_John",   "text": "Been waiting for this moment!",      "likes": 87},
      {"author": "Sophie_ML", "text": "Game changer right here 🚀",          "likes": 201},
      {"author": "Alexei_D",  "text": "How did you even build this?",        "likes": 55},
      {"author": "TechTina",  "text": "Sharing this everywhere immediately!", "likes": 319},
      {"author": "Ryan_Code", "text": "The animation quality is top tier",   "likes": 76}
    ]
  }]
}
```

### SubscribeCTA
```json
{
  "width": 1080, "height": 1920, "fps": 60,
  "durationInFrames": 150, "format": "vertical",
  "scenes": [{
    "id": "subscribecta-probe", "durationInFrames": 150, "preset": "SubscribeCTA",
    "channelName": "TechWave Studio", "subscribers": 285000,
    "buttonText": "Subscribe", "subscribedText": "Subscribed"
  }]
}
```
Frame 70 is mid-cursor-travel. Frame 110 shows subscribed state + bell.

### Leaderboard
```json
{
  "width": 1080, "height": 1920, "fps": 60,
  "durationInFrames": 150, "format": "vertical",
  "scenes": [{
    "id": "leaderboard-probe", "durationInFrames": 150, "preset": "Leaderboard",
    "title": "Top Performers 🏆", "valueSuffix": "pts",
    "rows": [
      {"name": "Aria Chen",    "value": 9840},
      {"name": "Marcus Webb",  "value": 8120},
      {"name": "Lena Vogt",    "value": 6950},
      {"name": "Sam Park",     "value": 5300},
      {"name": "Javi Morales", "value": 4100}
    ]
  }]
}
```

---

## BaseSceneProps for learn-pack fields (passthrough pattern)

Since `BaseSceneSchema` is `.passthrough()`, you can pass custom props without
touching the schema. The safe pattern is a local type cast:

```tsx
type QuizProps = BaseSceneProps & {
  question?: string;
  options?: string[];
  correctIndex?: number;
  revealAtProgress?: number;
};

export const QuizCard: React.FC<BaseSceneProps> = (props) => {
  const { question, correctIndex = 0 } = props as QuizProps;
  // ...
};
```

The component signature stays `React.FC<BaseSceneProps>` (required by `PresetDefinition`).
The cast is local and safe because `.passthrough()` guarantees the extra keys arrive at runtime.

---

---

## Stage pack recipes (LyricLines, ScoreHud, CountdownHero, VersusSplit)

### LyricLines
```json
{
  "width": 1080, "height": 1920, "fps": 60,
  "durationInFrames": 180, "format": "vertical",
  "scenes": [{
    "id": "lyric-scene", "durationInFrames": 180, "preset": "LyricLines",
    "title": "Моя Музыка",
    "artist": "Исполнитель",
    "lines": [
      {"text": "Первая строфа песни",    "startAt": 0.0},
      {"text": "Вторая строфа здесь",    "startAt": 0.28},
      {"text": "Третья активная строка", "startAt": 0.55},
      {"text": "Финальный куплет",        "startAt": 0.78}
    ]
  }]
}
```
Two-frame check: frame 30 → active line 1 ("Первая строфа"), frame 110 → active
line 3 ("Третья активная строка"). File sizes differ because word-fill state changes.

### ScoreHud
```json
{
  "scenes": [{
    "preset": "ScoreHud",
    "score": 12500,
    "health": 65,
    "combo": 4,
    "timeLeft": 60,
    "playerName": "ИГРОК 1"
  }]
}
```
Single frame 70 suffices; health bar and rolling score are clearly mid-animation.

### CountdownHero
```json
{
  "width": 1080, "height": 1920, "fps": 60,
  "durationInFrames": 240, "format": "vertical",
  "scenes": [{
    "durationInFrames": 240, "preset": "CountdownHero",
    "from": 3,
    "finalWord": "СТАРТ",
    "subtitle": "Начинаем раунд"
  }]
}
```
Two-frame check: frame 30 → digit «3», frame 150 → digit «1». Scene divides into
`(from+1)` equal beats; each digit occupies one beat; ring pulse radiates each beat.

### VersusSplit
```json
{
  "scenes": [{
    "preset": "VersusSplit",
    "left":  {"name": "КОМАНДА А", "value": "1500 очков"},
    "right": {"name": "КОМАНДА Б", "value": "1350 очков"},
    "vsLabel": "VS"
  }]
}
```
Both panels slide from opposite edges; VS label mid-scale at frame 40, settled at 70.

### Stage pack confirmed PNG sizes (1080x1920 @ 60fps)

| Preset | Frame | Bytes |
|---|---|---|
| LyricLines | 70 | 154 600 |
| LyricLines | 30 | 171 704 |
| LyricLines | 110 | 153 426 |
| ScoreHud | 70 | 294 046 |
| CountdownHero | 70 | 276 213 |
| CountdownHero | 30 (digit 3) | 240 557 |
| CountdownHero | 150 (digit 1) | 225 152 |
| VersusSplit | 70 | 253 274 |

All > 50 000 bytes threshold. Different sizes across CountdownHero frames prove
state change; different active-line bytes in LyricLines prove karaoke fill fires.

---

## Stage pack design patterns

### Beat-division pattern (CountdownHero)
Divide `durationInFrames` into `N+1` equal beats (N digits + 1 final word beat):
```tsx
const totalBeats = Math.max(1, Math.round(fromProp)) + 1;
const beatFrames = durationInFrames / totalBeats;
const beatIndex  = Math.min(Math.floor(frame / beatFrames), totalBeats - 1);
const beatFrame  = frame - beatIndex * beatFrames;
```
Makes timing self-adjusting to any durationInFrames — no hardcoded frame values.

### Karaoke word-fill pattern (LyricLines)
Map `lineProgress` (0..1 within the active line) to per-word fill:
```tsx
const wordStart = wi / nWords;
const wordEnd   = (wi + 1) / nWords;
const wordFill  = clamp01((lineProgress - wordStart) / Math.max(wordEnd - wordStart, 0.01));
// wordFill > 0.5 → word is "sung", switch to accent colour
const wordColor = wordFill > 0.5 ? accent : theme.muted;
```

### Deterministic particle sparks (ScoreHud combo)
Use `mulberry32(combo * 31 + frame)` to seed particle positions — they shift each
frame, creating flicker without `Math.random()` breaking parallel render workers.

### Diagonal panel clip + panel slide (VersusSplit)
Two complementary `clipPath: polygon(...)` values cut the canvas diagonally.
Each panel slides from ±width → 0:
```tsx
const diagOffset = Math.round(width * 0.04);
const leftClip  = `polygon(0 0, calc(50% + ${diagOffset}px) 0, calc(50% - ${diagOffset}px) 100%, 0 100%)`;
const rightClip = `polygon(calc(50% + ${diagOffset}px) 0, 100% 0, 100% 100%, calc(50% - ${diagOffset}px) 100%)`;
```
The VS label sits in its own full-canvas div on top of both panels (unaffected by clips).

---

## Semantic colour exceptions

Educational presets may hardcode semantic state colours (correct/wrong) as a deliberate
exception to the "read all colours from theme" rule:

```tsx
const CORRECT_GREEN = '#22C55E'; // semantic, not decorative
const WRONG_RED = '#EF4444';     // semantic, not decorative
```

Document this exception with a comment in the source. All other colours must still come
from `useStyle()` → `theme`, `accent`.
