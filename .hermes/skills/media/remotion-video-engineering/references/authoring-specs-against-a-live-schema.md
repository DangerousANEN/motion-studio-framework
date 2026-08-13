# Authoring Spec JSON Against a Live Schema

Writing a `props.json` / spec file for an existing Remotion pipeline — a demo reel, a
showcase, a regression fixture. The pipeline already has a Zod schema and a preset
registry, so every field name is *already decided*. The failure mode is writing the
spec from what the field names **ought** to be.

---

## 1. The trap: plausible prop names that don't exist

Composing a demo spec for eight presets, the following were written from intuition and
all of them were wrong:

| Written | Actual schema |
|---|---|
| `messages[].author` | `from` |
| `messages[].outgoing: true` | `out: true` |
| `messages[].status: "read"` | `read: true` |
| `tokens[].amount: "9 500.00"` | `amount: z.number()` |
| `tokens[].fiat: "$9 500"` | `usd: z.number()` |

Every one is a *reasonable* name. That is exactly why guessing feels safe here and isn't:
the spec parses as JSON, the file writes cleanly, and nothing objects until Zod runs —
or worse, until a lenient schema drops the fields silently and the scene renders empty.

Note the shape of the numeric errors: strings that were pre-formatted for display
(`"9 500.00"`, `"$9 500"`). Presentation belongs to the component, not the spec. If a
field wants a formatted string, the schema will say so; assume raw numbers otherwise.

**Rule: before writing a single scene object, extract the leaf schemas for the presets
you're using.** Nested item schemas (`ChatMessageSchema`, `TokenRowSchema`,
`SegmentSchema`) are where the guessing happens — top-level keys like `title` and
`durationInFrames` are usually obvious and correct.

```bash
grep -n -A10 "ChatMessageSchema = z.object\|TokenRowSchema = z.object" src/VideoSpec.schema.ts
```

Cheap, mechanical, and it answers the question the guess was going to get wrong. Do it
for every array-of-objects field the spec touches.

### 1a. Wrong keys inside a `.passthrough()` object are *silently dropped*

The table above assumes Zod rejects the spec. It often doesn't. A `.passthrough()` schema
(the project uses it on `BaseSceneSchema` so agents can iterate without editing the schema)
accepts unknown keys — and a nested item schema *strips* them. The combination is nasty:

`messages: [{author: "Ты", text: "…", side: "right"}]` — `author` and `side` don't exist
(`from` / `out` do). The spec **parsed clean**, `tsc` was clean, the render exited 0, and
the scene drew empty chat bubbles. I diagnosed that as a broken render (dark phone screen,
max brightness 165/255) and started reading the *component* before checking my own keys.

Tells that you have stripped keys rather than a broken component:
- Container chrome renders (bubbles, cards, frames) but the content inside is missing.
- `safeParse` succeeds — so success is **not** evidence your field names are right.

Cheap discriminator: parse the spec and print what came *out*, not just whether it parsed.

```ts
const r = VideoSpecSchema.safeParse(raw);
if (r.success) {
  const s = (r.data as any).scenes[1];
  console.log(JSON.stringify(s.innerProps ?? s, null, 1));  // did my keys survive?
}
```

Two-line version of the same idea for whole-spec sanity: after parsing, log per scene the
`preset`, `durationInFrames`, and the **count** of `effects` / `overlays`. A zero where you
wrote three means the array was dropped or renamed.

### 1b. Different sub-namespaces have different naming conventions

Within one schema, `transition.type` values are lowercase identifiers
(`fade`, `slide`, `wipe`, `iris`, `crossZoom`, `dreamyZoom`, `zoomBlur`, `bookFlip`) while
*effect* names are PascalCase registry keys (`CrossFade`, `ZoomPunch`, `GlitchRgb`).
Passing `{"type": "CrossFade"}` — an effect name, in the transition slot — invalidates the
whole spec, which renders as the error card at exit code 0. `dissolve` failed the same way:
plausible, and simply not in the enum.

Never infer one namespace's vocabulary from another's. The Zod error is the fastest lookup
available — it prints the full enum of valid values.


---

## 2. Dedupe Zod issues by normalised path, or you only see one array row

`safeParse` on an array-heavy spec emits one issue **per element per bad field**. Three
malformed token rows produce three identical-looking `expected number, received string`
issues, and printing `issues.slice(0, 10)` or piping through `tail` shows the tail of one
array while hiding every *other* defect class in the file.

Collapse array indices to a single token and dedupe:

```ts
import fs from 'fs';
import { VideoSpecSchema } from './src/VideoSpec.schema';

const raw = JSON.parse(fs.readFileSync('public/demo_spec.json', 'utf8'));
const r = VideoSpecSchema.safeParse(raw);

if (!r.success) {
  const seen = new Set<string>();
  for (const i of r.error.issues) {
    const p = i.path.join('.');
    const key = p.replace(/\d+/g, 'N');       // scenes.3.tokens.1.amount -> scenes.N.tokens.N.amount
    if (seen.has(key)) continue;
    seen.add(key);
    console.log(`${p} -> ${i.message}`);
  }
} else {
  console.log('OK scenes=' + r.data.scenes.length);
}
```

One line per distinct defect, with a real index retained so it's still navigable. Run it
with `npx tsx` (already available in a Remotion project) and delete the throwaway after.

**Iterate to a clean parse before rendering anything.** Each round-trip is seconds; a
render is minutes and can still produce Remotion's error card as video (Rule 1b).

---

## 3. Assets named in a spec may be generated, not stored

A spec field like `"audioUrl": "audio/demo_mix.wav"` is a *promise about the filesystem*,
and in a procedurally-generated pipeline that promise is usually unkept. In this project
`public/audio/` held three narration WAVs; the "112 SFX and 16 music beds" existed only
as Python generators (`msf/audio/sfx.py`, `sfx_extra.py`, `music.py`, `mixer.py`).
Nothing is wrong — synthesis is the design (see `procedural-audio-synthesis` Rule 1) —
but the demo has to *render* the mix before the spec can reference it.

Check, don't assume:

```bash
ls remotion/public/audio                                          # what actually exists
find . -iname "*sfx*" -o -iname "*music*" | grep -v node_modules   # what generates it
```

If only generators come back, add a render step ahead of the video render: build a
`Timeline`, `add_music` / `add_sfx` / `add_voice`, `render(duration)`, `write_wav` into
`public/`. Confirm the file exists on disk before naming it in the spec.

Generalises past audio: 3D models, fonts, LUTs and lottie files can all be
fetch-on-demand or generated. Any spec field holding a path is a claim to verify.

---

## 4. Order of operations for a showcase spec

1. Enumerate what's real — presets and effects from the registries, not from a plan doc.
   ```bash
   npx tsx -e "import {PRESETS} from './src/registry/presets'; console.log(Object.keys(PRESETS).sort().join(','))"
   ```
   Do the same for the merged effect registries; a name that isn't in the map is a
   runtime lookup failure regardless of how well-documented it is elsewhere.
2. Read the leaf schemas for the presets chosen (§1).
3. Verify or generate every asset the spec will reference (§3).
4. Write the spec; parse-loop it clean with the deduped reporter (§2).
5. `npx tsc --noEmit`, then render, then the post-render probes
   (`scripts/verify_render.py`, red-frame check).

Steps 1–3 are all reads and can be batched in one turn. Skipping them doesn't save time,
it moves the failure later — to Zod at best, to a silently-empty scene at worst.

---

## 5. A showcase is a coverage test

Picking one scene per preset family and stacking two or three effects on each is the
first run that exercises presets, the effect layer, transitions and audio *together*.
Treat surprises as findings about the pipeline, not obstacles to the demo — the schema
mismatches above were latent for every preset nobody had specced by hand yet.

If the schema turns out to be missing a field the showcase needs (e.g. no per-scene
`effects` array), that's a real gap: add it to the schema and to the component that
applies it, run `tsc`, and say plainly that the demo required a pipeline change rather
than folding it into the render report.

---

## 6. "Write me some scripts / scenarios" is a spec task, not a copywriting task

A request for video *scripts* (hooks, scene beats, CTA) is tempting to answer in prose.
Don't — deliver **renderable spec JSON**, because prose can't be validated and quietly
encodes impossible scenes. Everything in §1–§4 applies, plus:

- **Enumerate the library first.** Presets, style kits, effects, overlay types — from the
  registries. Writing beats around a scene that doesn't exist wastes the whole draft.
- **Every scene needs its narration field** if the pipeline does TTS (`text` here); the
  graph raises on a scene without it. Check before rendering, not after.
- **Run the spec through the capability gate at the *lowest* level** it might be invoked
  with (`agent_level: 1`). A scene silently rewritten to a fallback is a script that
  doesn't say what you wrote. See `msf-gate` and
  `references/preset-reachability-and-field-mapping.md` §3b.
- **Pacing is arithmetic, not vibes.** Print per-scene seconds and confirm each cut lands
  in the target window (1.5–2.0s for retention-shaped shorts) instead of eyeballing frame
  counts:
  ```python
  for sc in spec["scenes"]:
      print(f"{sc['id']:<4}{sc['preset']:<16}{sc['durationInFrames']/60:5.2f}s")
  ```
- **Vary the style kit per scene** to get a palette change on every cut — one field, no
  component work, and it's the cheapest visual variety available (see
  `references/style-kit-palette-authoring.md`).
- **Carry the motion in per-scene `effects`** when the transition layer is known-broken
  (see `references/transitions-and-motion-layer.md` for the probe that decides this).
  Don't design a script around a blend that cuts.
- **Placeholder numbers must be labelled as such.** Benchmark scores, subscriber counts and
  prices invented to make a scene concrete are fine as scaffolding, but say so in the
  hand-off — an unmarked plausible number gets published as fact.
- **Deliver the rendered files, not just the spec paths.** A script request is satisfied by
  something the user can watch. Render every script to mp4 and attach the files
  (`MEDIA:/abs/path.mp4` on a messaging platform); a table of JSON paths reads as unfinished
  work and reliably draws a one-line "send everything" follow-up. Copy the mp4s out of
  `remotion/out/` to stable, human-named paths first — build directories get cleaned.

Verification bar before hand-off: every spec parses, the gate keeps every preset at level 1,
every scene has narration, one frame per scene rendered *and looked at*, and — this is the
part that is not optional — **every script rendered end-to-end**, with verification frames
pulled from the encoded mp4 rather than fresh `still` calls.

One-still-per-scene is a weaker bar than it looks. A scene that subdivides its duration into
beats holds *different content* per beat, so the house 72 %-of-scene sample can land on a
countdown digit and never once render the payoff word. In this session that let a truncated
hook (`ОГНАЛ` instead of `ДОГНАЛИ`) pass a 15-frame still pass **and** a per-scene vision
review, surfacing only when all three scripts were rendered to mp4 and frames near the cuts
were extracted. A 10 s vertical short renders in ~40 s — always cheaper than shipping a
broken hook. See `references/text-fitting-and-beat-sampling.md` §2 for the per-beat frame
derivation and the fields that imply beats.

