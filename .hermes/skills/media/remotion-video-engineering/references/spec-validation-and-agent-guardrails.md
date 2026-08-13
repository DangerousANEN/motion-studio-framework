# Spec Validation & Agent Guardrails

Two failure classes that cost real time on an MSF/Remotion pipeline, plus the
measured method for deciding whether to restrict an agent or just document better.

Source: MSF v4/v5 session. All numbers below came from executing the commands,
not from recall.

---

## Part 1 — The silent RENDER ERROR class

### What happened

Four promo shorts rendered "successfully": exit code 0, valid MP4s, plausible
~700 KB each, correct durations (25–29 s). Every one was a **full-screen red
Zod error card**. Vision analysis on a contact strip is what caught it — one red
frame of error text followed by four black frames.

### Root cause

Two validators with different strictness:

| Layer | Checks | Misses |
|---|---|---|
| Python `validate_spec()` | preset names, required keys present | **field types** |
| Zod (`VideoSpec.schema.ts`) | names, keys **and types** | — |

A spec with `statValue: "6.8 GB"` (string) and `cards: ["a","b"]` (strings)
passed Python, was rejected by Zod at render time, and Remotion rendered its own
error screen **as normal video output**. A failed render is not an exception —
it is an MP4 that looks like a deliverable.

### Fix 1 — Zod pre-flight before spending render time

Validate against the *real* schema before rendering. The schema is TypeScript,
so bundle it with esbuild (already a Remotion dep) rather than adding ts-node —
`register('ts-node/esm', ...)` fails with `ERR_MODULE_NOT_FOUND` if ts-node
isn't installed, which it usually isn't.

```js
// remotion/validate_spec.mjs  — node validate_spec.mjs spec.json
import { readFileSync, unlinkSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import esbuild from 'esbuild';

const tmp = join(process.cwd(), '.schema.bundle.mjs');
await esbuild.build({
  entryPoints: [join(process.cwd(), 'src', 'VideoSpec.schema.ts')],
  bundle: true, format: 'esm', platform: 'node', outfile: tmp, logLevel: 'error',
});
const { VideoSpecSchema } = await import(pathToFileURL(tmp).href);

for (const file of process.argv.slice(2)) {
  const result = VideoSpecSchema.safeParse(JSON.parse(readFileSync(file, 'utf8')));
  if (!result.success) {
    for (const i of result.error.issues) {
      console.error(`  path=${i.path.join('.')} :: ${i.message}`);
    }
    process.exit(1);
  }
}
unlinkSync(tmp);
```

Wire it into the render path so a bad spec fails *before* TTS and rendering:

```python
check = subprocess.run(["node", "validate_spec.mjs", str(spec_json)],
                       cwd=str(ROOT / "remotion"), capture_output=True, text=True)
if check.returncode != 0:
    raise RuntimeError(f"spec rejected by Zod before render:\n{check.stdout}\n{check.stderr}")
```

Zod reports the exact path (`scenes.0.statValue :: Expected number, received string`),
which is far more actionable than a rendered red rectangle.

### Fix 2 — Post-render frame probe

Pre-flight can't catch every render-time failure, so also reject the error screen
by its colour. Remotion's error card is saturated red:

```python
raw = subprocess.run(["ffmpeg", "-i", str(probe_png), "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-", "-loglevel", "error"],
                     capture_output=True).stdout
px = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(int)
r, g, b = px[:, 0].mean(), px[:, 1].mean(), px[:, 2].mean()
if r > 100 and r > g * 2.0 and r > b * 2.0:
    raise RuntimeError(f"RENDER ERROR screen (mean RGB {r:.0f},{g:.0f},{b:.0f})")
```

Healthy frames measured `32,31,26` / `15,35,35` / `14,25,17` — dark themed
backgrounds sit far from the red trigger, so the threshold is not fragile.

**Generalised rule:** any renderer that draws its own error state produces a
file that passes `ffprobe`. File existence, exit code, size and duration are all
insufficient evidence. Look at pixels.

### Fix 3 — Validate the shape of items INSIDE list fields

Part 1 covers wrong *types* on scalar fields. There is a distinct sub-case the
Python validator still let through months later: a list-valued field that is
**present** but whose items are the wrong shape.

```jsonc
"tokens": [{"name": "Ethereum", "symbol": "ETH", "value": 64200, "change": 4.2}]
```

Entirely plausible, and `value` is not `amount`. All three rows failed
`invalid_type`, Zod rejected the spec, and Remotion rendered a red card **for the
whole video** — not one placeholder scene. A `_DATA_REQUIREMENTS`-style table that
only asks "is the list there" cannot see this.

**Split the table by blast radius, and check each field against the schema rather
than assuming:**

```python
# HARD — item keys the TS schema declares REQUIRED (no `.optional()`).
# A missing one red-cards the entire render.
_ROW_SHAPES_HARD = {
    "tokens":       ("symbol", "amount"),   # TokenRowSchema
    "transactions": ("label", "amount"),    # TransactionSchema
    "segments":     ("label", "value"),     # SegmentSchema
    "messages":     ("text",),              # ChatMessageSchema
}

# SOFT — all-optional keys plus `.passthrough()`. Zod accepts these and the render
# succeeds; it just draws a blank row. Raising here would be a lie.
_ROW_SHAPES_SOFT = {
    "rows":     ("name",),     # `label` is an accepted alias
    "comments": ("text",),
    "events":   ("label",),
}
```

Getting the split wrong fails in both directions: treating a soft field as hard
**rejects valid specs**; treating a hard field as soft **ships red cards**. So
assert the split against the schema source itself, not against memory —
`tests/test_row_shapes.py` greps `VideoSpec.schema.ts` for each key and fails if a
HARD key carries `.optional()` or a SOFT key does not:

```python
m = re.search(rf"\b{key}:\s*z\.[^,\n]*", item_object_body)
assert ".optional()" not in m.group(0), f"{field}[].{key} is optional — move it to SOFT"
```

Three more requirements on this check, each learned by getting it wrong:

- **Skip non-dict items.** Several fields accept `['a','b']` shorthand via a Zod
  transform (`options`, `steps`, `lines`). Demanding keys of a string breaks valid
  specs.
- **Honour documented aliases.** `Leaderboard` rows accept `label` for `name`.
  Requiring the canonical key alone rejects a spec the renderer handles fine.
- **The error message must be actionable**: which field, which index, which key is
  missing, *which keys were actually supplied*, and that the consequence is a
  whole-video red card. Assert on those substrings in the test — an error the
  author cannot act on wastes the check.

### `is not None` is the wrong emptiness test for list fields

Same session, adjacent bug in the older guard:

```python
if required and not any(sc.get(k) is not None for k in required):  # WRONG
```

`tokens: []` and `rows: []` are not `None`, so an empty list sailed through the
very guard that exists to prevent empty chrome. Truthiness is the right test — but
naive truthiness then rejects a legitimate `statValue: 0` or `health: 0`, which a
counter may well want to display. Numbers (and bools) count as content; only empty
containers and empty strings do not:

```python
def _has_content(v):
    if isinstance(v, bool):        return True
    if isinstance(v, (int, float)): return True   # 0 is a real value
    return bool(v)
```

---

## Part 2 — Deciding guardrails by measurement, not intuition

### The question

When weak models write bad specs, should you restrict what they can do, or
document the contract better? Guessing produces permanent over-restriction.

### Method

Build a probe that scores model output against the real schema plus semantic
checks Zod can't express (preset chosen but its data absent, all scenes using an
identical preset, seconds passed where frames are expected).

Key mechanics:

- **Gateway may always stream.** OmniRoute returns SSE `data:` chunks even when
  `stream` isn't requested — `json.load(resp)` dies with
  `Expecting value: line 1 column 1`. Parse chunks, fall back to plain JSON.
- **Verify model IDs first.** `GET /v1/models` before assuming a tier exists.
  In this session `gemini-3.6-flash-low` did not exist and `gemini-3-5-pro`
  returned 404; only `-medium` and `-high` were real.
- **A/B the brief, not the model.** Same tasks, same models, one variable: the
  instruction text. That isolates documentation as the cause.

`scripts/agent_spec_probe.py` in this skill is a runnable generic version.

### Result

| Model | Brief v1 (original) | Brief v2 (+ type rules) |
|---|---|---|
| `gemini-3.6-flash-medium` | 2 / 5 | **5 / 5** |
| `gemini-3.6-flash-high` | 2 / 5 | **5 / 5** |

**`high` scored identically to `medium`.** Both picked correct presets and wrote
sensible copy, then filled fields with wrong types:

```jsonc
"statValue": "6.8"                        // string, schema wants number
"steps": ["Текст", "Токены", "Векторы"]   // strings, schema wants objects
```

These were the *same two mistakes a human made by hand* on the same contract —
strong evidence the contract was under-documented rather than the models weak.

### The documentation block that closed the gap

Show a wrong/right pair per rule. Abstract prose ("statValue must be numeric")
did not work as well as a visible contrast:

```
1. statValue is a NUMBER, never a string. Units go in statSuffix.
   WRONG: "statValue": "6.8 GB"
   WRONG: "statValue": "6.8"
   RIGHT: "statValue": 6.8, "statSuffix": " GB", "statLabel": "VRAM"

2. steps and nodes are arrays of OBJECTS, never arrays of strings.
   WRONG: "steps": ["Текст", "Токены"]
   RIGHT: "steps": [{"label": "Текст", "detail": "на входе"}]
   nodes uses {"label", "sub"} — not {"label", "detail"}.

3. cards is an array of OBJECTS with a required "title".
   WRONG: "cards": [{"label": "Было", "value": "10 часов"}]
   RIGHT: "cards": [{"title": "10 часов", "description": "вручную", "tag": "БЫЛО"}]

4. layers is an array of plain STRINGS (the one field that is not objects).

5. durationInFrames counts FRAMES, not seconds. At 60fps, 3 seconds = 180.
```

Near-miss shapes are the dangerous ones: `{label, value}` vs `{title, description}`
is exactly the kind of thing a model invents confidently.

### Execute the brief's example — it is code, not prose

The worked example is the highest-leverage text in a brief because the next agent
copies it verbatim, inheriting every bug it carries. Treat it as production code
and actually run it. Three defects in one hand-written example, none visible on
reading:

| Defect | How it surfaced |
|---|---|
| Per-scene text keyed as `narration:` | The graph requires `text` and raises `storyboard[i] has no 'text'` |
| Duplicate `"text"` key after a blind rename | Python keeps the last value — the quote silently became the narration |
| `balance: "12 480"`, `amount: "2.4"` | Zod wants numbers; `safeParse` fails |

That last row has a nasty tail on the Remotion side: **a failed `safeParse` in
`Root.tsx` does not throw.** It falls through to a default composition, so the
only symptom is an unrelated-looking duration error
(`Cannot use frame 240: duration is 120`) — or a silently wrong video.

Static check first, then a real run:

```python
ast.parse(code)                      # duplicate keys, syntax errors
sb = ast.literal_eval(storyboard)    # extract the literal
assert all(s.get("text") for s in sb)
used = [s["preset"] for s in sb]
assert len(set(used)) >= 4 and not any(a == b for a, b in zip(used, used[1:]))
```

Also **verify every API name the brief quotes.** A checklist that reads
`result["spec"]` when the pipeline only sets `result["spec_path"]` raises
`KeyError`, which teaches the next agent to skip the check entirely:

```bash
grep -n 'state\["spec_path"\]' msf/graph/video_graph.py
grep -rn "has no 'text'" msf/graph/video_graph.py   # confirm quoted error strings
```

### Editing a long brief without corrupting it

Two self-inflicted failures worth avoiding when patching a large SKILL.md or prompt:

- **A patch anchor that lands inside a fenced code block** injects prose into the
  fence and can duplicate whole sections. Audit structure after any large patch
  instead of eyeballing — fences must be even, headers unique:
  ```python
  hs = re.findall(r'^#{1,4} .*$', text, re.M)
  print("fences:", text.count("```"), "dups:", {k: v for k, v in Counter(hs).items() if v > 1})
  ```
- **Over-narrow patch anchors silently truncate.** Anchoring on a two-line
  fragment and replacing it with one line deletes the rest of the entry. Include
  the full block being replaced, then re-read to confirm.

### Conclusion

Documentation closed **100 %** of observed errors, so no capability was removed.
Restrict only where a mistake is *irreversible*:

| Level | May | May not |
|---|---|---|
| ≤ 2 | every preset, every setting, every transition | write React, edit primitives, change the schema |
| ≥ 3 | all of the above + new components | break the wire contract, bypass Zod pre-flight |

The line is the right to write code, not the length of the preset list. A wrong
field type is caught by a validator; a broken component is not.

---

## Part 3 — Companion pitfalls seen in the same session

- **A skill that under-reports capability causes visible sameness.** The skill
  listed 5 presets when the schema had 11, hiding 6 from every agent that read
  it — a direct contributor to "all the videos look identical". Re-read the
  constant in code; don't trust prose lists.
- **`Math.round` on an animated counter destroys precision.** `6.8` displayed as
  `6 GB`. Keep decimals when the target value is fractional:
  ```ts
  const decimals = Number.isInteger(statValue)
    ? 0 : Math.min(2, (String(statValue).split('.')[1] ?? '').length);
  const currentValue = decimals === 0
    ? Math.round(raw) : Number(raw.toFixed(decimals));
  ```
- **A stray token in JSX fails `tsc` far from its cause.** A literal word left in
  an element (`literal            stitchTiles="stitch"`) surfaced as
  `Property 'literal' does not exist on type 'SVGProps<...>'`. Run
  `npx tsc --noEmit` after edits, not only before shipping.
- **ffmpeg filter args need forward slashes on Windows.** Backslash paths inside
  `-filter_complex` / `loudnorm` break the filter parser; normalise with
  `str(path).replace("\\", "/")`.
- **Check the signature before passing three paths to a two-path function.**
  `master_video_audio(in, out, target_lufs)` silently misused as
  `(raw, wav, final)` wastes a whole render cycle.
- **English defaults in a Russian-language pack are a content bug, not cosmetics.**
  `SubscribeCTA` defaulted to `buttonText: 'Subscribe'` / `'Subscribed'` and hard-coded
  the literal `subscribers` in the JSX, so a fully Russian spec rendered an English
  button — the single element the scene exists to show. Grep every preset for
  hard-coded English UI copy, not just for missing props.
- **Localising a default immediately breaks any fixed-width control sized around
  it.** The moment the caption became `Вы подписаны` (12 Cyrillic chars vs 9 Latin),
  the flat `btnW = cardW * 0.52` pill wrapped it to two lines and the second line
  spilled outside the rounded background. Measure the *longest of all captions the
  control can display* — a control that switches text mid-scene must fit both
  states, or it visibly resizes on the transition — reserve any icon in **both**
  states so the pill does not grow when the bell appears, then shrink type only if
  it still does not fit. See `measured-text-geometry.md`.
- **Russian counters need real pluralisation once the number is dynamic.**
  `+1 подписчик` is wrong for most values: 1 → подписчик, 2–4 → подписчика,
  0 / 5–20 and anything ending 11–14 → подписчиков. An abbreviated count
  (`12.4K`) reads as plural regardless of the number behind it.
- **A shared fallback colour makes distinct data look like a failed asset load.**
  `CryptoWallet` used `t.color ?? accentColor`, so ETH/BTC/SOL rendered three
  identical green dots and vision review reported it as "placeholder icons".
  Resolve a per-item colour from the item's own key (a brand table plus a
  deterministic hash for unknowns); *different* matters more than *correct*.
