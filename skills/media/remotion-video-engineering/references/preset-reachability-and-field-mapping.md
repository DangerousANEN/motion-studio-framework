# Preset Reachability and the Field-Mapping Boundary

The user says: *"the agent only ever uses 3-4 scenes — update the prompt so the
videos are better."*

The prompt is a **hypothesis**, not a diagnosis. Update it, yes — but check
reachability first. In the session this file comes from, the prompt was the
smaller half: three silent data losses in the Python→wire→Zod boundary meant 11
of 17 presets could not be produced *by any prompt*. Rewriting wording before
fixing that would have produced a beautifully-documented library the generator
still could not reach.

**A preset the pipeline cannot produce is not a prompt problem. Prove reachability
before you write a word of guidance.**

---

## 1. The reachability probe — run this before editing any prompt

One spec per preset, through the **real** builder, diffing keys in against keys
out. Anything that goes in and does not come out is an unreachable preset.

```python
import sys, json
sys.path.insert(0, r"C:\path\to\project")
from msf.graph.video_graph import node_build_remotion_spec as build

CASES = {
    "StatCounter":  {"statValue": 671, "statSuffix": "B", "statLabel": "параметров"},
    "DonutFill":    {"segments": [{"label": "a", "value": 62}, {"label": "b", "value": 38}]},
    "TgChat":       {"messages": [{"from": "A", "text": "hi"}]},
    "AiChatStream": {"messages": [{"from": "u", "text": "q"}], "response": "a"},
    "CryptoWallet": {"balance": 12480.0, "currency": "USDT",
                     "tokens": [{"symbol": "ETH", "amount": 2.4, "change": 3.1}]},
    "BankCard":     {"last4": "4821", "holder": "N. LIPSKY", "expiry": "09/29"},
    "CompareSplit": {"cards": [{"title": "Было"}, {"title": "Стало"}]},
}

for preset, payload in CASES.items():
    scene = {"id": "s1", "text": "n", "preset": preset, **payload}
    st = {"scenes": [scene], "topic": "t", "out_dir": OUT}
    try:
        spec = json.load(open(build(dict(st))["spec_path"], encoding="utf-8"))
        got = spec["scenes"][0]
        lost = [k for k in payload if k not in got]
        print(f"{preset:14} {'OK' if not lost else 'LOST ' + ','.join(lost)}")
    except Exception as e:
        print(f"{preset:14} RAISED {type(e).__name__}: {str(e)[:80]}")
```

`LOST` and `RAISED` rows are presets the generator cannot choose. Fix those, then
tune the prompt.

Do the same round-trip for **aliases**, which fail differently — they survive the
diff but arrive wrong:

```python
for a in ["gold", "neon", "cyan", "#00E5A0", None]:
    print(a, "->", json.load(open(build({... "accent": a})["spec_path"]))["scenes"][0]["accentColor"])
```

`neon -> neon` is a bug. `neon -> #00FF88` is correct.

---

## 2. The three boundary bugs, and why each one is silent

### 2a. Case-mismatched filter drops keys and then blames the caller

A snake_case dataclass filtered against camelCase input:

```python
scene_fields = {f.name for f in dataclasses.fields(Scene)}   # stat_value, point_count
kwargs = {k: v for k, v in sc.items() if k in scene_fields}  # input has statValue
```

`statValue` is not in `scene_fields`, so it is **discarded**. Then the validator
reports `"StatCounter needs one of ['statValue','statLabel']"` — for a key the
caller supplied. This is the worst variety of bug for an LLM caller: it does the
right thing, is told it did the wrong thing, and retreats to the one preset that
happens to work. That retreat is exactly what "only uses 3-4 scenes" looks like
from outside.

Fix by translating both directions from the single existing map, and by making the
mapper shared:

```python
def _scene_kwargs(scene, accent_color, index, default_preset="HeroKinetic"):
    wire_to_snake = {v: k for k, v in Scene._CAMEL.items()}
    scene_fields = {f.name for f in dataclasses.fields(Scene)}
    normalised = {wire_to_snake.get(k, k): v for k, v in scene.items()}
    kwargs = {k: v for k, v in normalised.items() if k in scene_fields and v is not None}
    kwargs.update(
        id=scene.get("id", f"scene-{index+1}"),
        duration_in_frames=normalised.get("duration_in_frames", 90),
        preset=normalised.get("preset", default_preset),
        accent_color=normalised.get("accent_color") or accent_color,
        audio_url=f"scene_{index:02d}.wav",
    )
    return kwargs
```

Accepting **both** spellings is deliberate: legacy snake_case specs keep working,
and the documented wire format starts working. Assert both in the regression test,
plus a scene that mixes them.

### 2b. Missing dataclass fields make presets structurally unreachable

Five presets had no `segments` / `messages` / `response` / `tokens` / `last4`
anywhere in `Scene`. No prompt wording reaches them. When adding, mirror the
component's prop names through the camel map rather than renaming on the fly:

```python
"chat_title": "contactName",   # scene caption stays `title`; contact is separate
"card_brand": "brand",         # avoids colliding with a future top-level brand
```

Check the actual component signature before choosing the wire name — reading
`export const BankCard: React.FC<...> = ({ last4, holder, expiry, brand, ... })`
takes one grep and removes the guess.

### 2c. A semantic alias with one special case

```python
accent_color = "#E6C475" if state.get("accent") == "gold" else (state.get("accent") or "#E6C475")
```

Documented values are `gold | neon | cyan`. Only `gold` resolves; `neon` reaches
the DOM as the literal string `neon`, which is invalid CSS, so the browser drops
the declaration and each scene falls back to its own default. Spec validates,
render exits 0, colour is silently wrong. Resolve every documented alias from one
table and pass raw `#RRGGBB` through untouched.

### 2d. Duplicated mapping loops drift

The same scene-mapping loop existed in the build node *and* the repair node, and
only one got the normalisation. A QA repair pass would therefore strip the very
preset data it was meant to preserve — a bug that only appears on the second
render of a video that failed QA once. Whenever a mapping loop is copy-pasted,
extract it before fixing one copy.

---

## 3. Rotation lists silently cap variety

An automatic fallback list is a ceiling on what a text-only caller can ever get:

```python
_TEXT_SAFE_PRESETS = ["HeroKinetic", "TypewriterSub", "GridGridFloor"]
```

Three typography cards, forever, no matter how many presets the registry holds.
Derive the list from the registry's own `dataDriven` flag instead of hand-listing:
anything *not* data-driven is drivable by narration alone. Two presets here
(`QuoteCard`, `TokenCloud3D`) had been text-safe all along and were simply left
out of the array.

Guard the other direction too — never rotate *away* from a data-driven preset the
caller explicitly named, or you silently drop the data they supplied:

```python
if base in _DATA_DRIVEN_PRESETS:
    return base
```

Order the list to alternate silhouette (title → running text → quote → 3D field),
not alphabetically. Consecutive scenes sharing a shape is what reads as cheap.

---

## 3b. The capability gate is a second, larger reachability ceiling

Rotation caps what a *text-only* caller gets. A **capability gate** caps what a whole
class of caller may name at all — and it fails the same silent way. Check it in the same
breath as rotation.

The pattern to look for is a hand-written allow-list guarding a tiered API:

```python
ALLOWED_PRESETS = {"HeroKinetic", "StatCounter", "GridGridFloor", ...}   # 11 names

if level <= 2 and preset not in ALLOWED_PRESETS:
    state["preset"] = "HeroKinetic"          # silent rewrite
```

The library had grown to 26. The list had not. So **15 valid presets were silently
rewritten to `HeroKinetic`** for every low-tier caller — the tier that depends on
finished presets most was locked out of over half of them. From outside this is
indistinguishable from "the agent only uses 3-4 scenes", which is why it must be ruled
out before the prompt is blamed.

Two further lessons from fixing it:

- **Separate the two things a gate conflates.** Its legitimate job is stopping a weak
  caller writing *untested code* into the render path. It has no business restricting
  which *finished* presets they may use. Once stated that way the fix is obvious: derive
  the allow-list from the registry at import time so a new pack is reachable the moment
  it is registered, with no second list to rot.
- **Derive it from the modules the registry index actually imports**, not by globbing the
  registry directory. Effect and transition registries share the same entry shape, so a
  glob produced **134 "presets"** (`Bloom`, `CrossFade`, `FadeIn`) — which would let a
  caller name an effect as a scene and get an error card. Assert the parsed count equals
  the TypeScript truth and that known effect names are absent:

```python
print(len(ALLOWED_PRESETS))                                    # must equal registry
print(any(n in ALLOWED_PRESETS for n in ("Bloom","FadeIn")))    # must be False
```

### The gate guarded one field and ignored the common path

The check ran on the top-level `preset` only. Scenes inside a `storyboard` were never
inspected — so a low-tier caller could name anything, including a preset that does not
exist, and the gate reported success. Since storyboards are the *recommended* way to
drive data presets, the hole covered the common path, not an edge case.

When an unknown per-scene preset is rejected, **drop the key rather than forcing a
fallback value**. Dropping lets rotation choose a real, varied preset; forcing
`HeroKinetic` turns the whole video into one repeated title card — reintroducing the
sameness the gate was never meant to cause.

Probe every level and both entry points, and check the tier that should be untouched:

```python
node_gate_check({"agent_level": 1, "preset": "TgChat"})["preset"]          # -> TgChat
node_gate_check({"agent_level": 1, "preset": "Nope"})["preset"]            # -> HeroKinetic
node_gate_check({"agent_level": 1, "storyboard": [{"preset": "Fake"}]})    # -> key dropped + error set
node_gate_check({"agent_level": 3, "preset": "Custom"})["preset"]          # -> Custom, untouched
```

### Documentation drifts further than code

The skill describing this gate claimed **5** allowed presets; the code said 11; the
registry said 26. Three numbers, all wrong, none agreeing. When a doc states a
capability list, re-derive it from the source and put the verification command *in* the
doc so the next reader can re-check instead of trusting the prose.

**The follow-up proves the point: the registry later reached 38.** Any count written into
prose — including the ones above — is stale by the next pack. Write the *command*, treat
every number as a timestamped observation, and re-derive before relying on it:

```bash
cd remotion && npx tsx -e \
  "import {PRESET_NAMES} from './src/registry/presets'; console.log(PRESET_NAMES.length)"
```

Guard the parser against the same drift with an equality assertion rather than a literal:
compare the Python-side `len(ALLOWED_PRESETS)` to that TypeScript number and fail loudly
if they diverge. A hardcoded `assert len(...) == 26` becomes a false alarm the day a pack
lands; an equality check against the registry stays correct forever.

### 3a. The gate was fixed; the ROTATION list was still a hardcoded five

Deriving `ALLOWED_PRESETS` from the registry fixed *permission*. It did not fix
*selection* — a separate hand-written list decided what rotation actually substitutes:

| hardcoded list | held | registry | consequence |
|---|---|---|---|
| `_TEXT_SAFE_PRESETS` | 5 | 13 rotation-safe | 8 finished presets could never appear |
| `_DATA_DRIVEN_PRESETS` | 11 | 25 data-driven | 14 eligible for blind rotation → ⚠ placeholder |

The user's report was, again, *"агенты используют первые 5 сцен"* — and again the prompt
was not the cause. **Fixing one derived list does not fix the others.** Grep for every
literal preset-name list before declaring the class closed:

```bash
grep -rn '"HeroKinetic"' --include=*.py . | grep -v test
```

### 3b. `rotation_safe` does not mean "renders the narration"

`dataDriven: false` answers "does this need structured data", not "will this show my
text". Rendering all 13 rotation-safe presets with ONLY `title` + `text` — exactly what
rotation supplies — found a third category:

```
title AND text    QuoteCard, TypewriterSub
title only        HeroKinetic, GridGridFloor, TokenCloud3D, MusicPlayer,
                  VinylRecord, VoiceMemo, ModelOrbit3D
ignores both,     CountdownHero → "СТАРТ"        ScoreHud → PLAYER 1 / СЧЁТ 9750
renders own       SubscribeCTA → TechChannel /   BankCard → ALEXEY NIKITIN / ···· 4242
demo data         142.0K подписчиков
```

The third group is convincing, fictional and unrelated to the script — auto-rotating it
puts invented facts on screen, which is what a fail-closed research node exists to
prevent. Express the final list as `registry_rotation_safe − explicit_blocklist` so the
base still tracks the source, and put the rendered evidence in the blocklist comment.

You cannot read this off a flag. Render each candidate with the props rotation supplies
and look at the frame.

### 3c. Verify the registry parser against node, or you have not verified it

A regex over TypeScript returns **fewer** results when formatting changes, and fewer is
invisible. Three parse bugs, each of which "succeeded":

- `mergeRegistries()` also appears in the file's own doc comment with empty parens — a
  plain search matched the COMMENT, returned zero packs, and produced an **empty
  registry** with no exception. Require a payload in the parens.
- `effects.ts` declares `ENTRANCE_EFFECTS` / `EXIT_EFFECTS` / `EMPHASIS_EFFECTS` as
  module-private `const`, exporting only the merged result. Requiring `^export const`
  dropped 44 of 96 effects.
- `effects_scene.ts` omits `family:` on every entry, so requiring that key dropped all 12
  atmosphere overlays.

Bundle the same TS with esbuild, run it under node, and diff the sets (skip, do not pass,
when node is unavailable). And **never fall back to a short hardcoded list on an empty
parse** — that silent fallback is the original bug. Assert non-emptiness instead:
`assert len(preset_names()) > 20`.

Note also that a preset registry and an effect registry are different namespaces:
`EffectStack` resolves `EFFECTS ∪ VISUAL_EFFECTS ∪ SCENE_EFFECTS`, while transitions live
in the same file but take different props and are silently skipped if named as an effect.


## 4. Writing the prompt half

Once reachability is proven, the prompt work is worth doing. What mattered:

- **Name the fallback as a failure mode, not a default.** "A video built from
  `HeroKinetic + TypewriterSub + GridGridFloor` is the automatic fallback and the
  signature of a lazy video" beats listing presets neutrally.
- **Say what the viewer sees**, not what the component is called. "A Telegram
  thread, bubbles arriving with read ticks" is choosable; "TgChat — chat preset"
  is not.
- **Give a shot structure**: hook → proof → number → contrast → texture → close.
- **Make the quality bar checkable**, so it can be enforced instead of hoped for:
  no adjacent repeats, ≥1 data/UI preset per 3-4 scenes, 5+ distinct presets in a
  6-scene short.
- **Ship a copyable working example** — one full storyboard with six different
  presets, each carrying real data.

### The prompt example must be executed, not just written

An example in a prompt is code the next agent will copy verbatim, so it inherits
every bug it contains. Three defects were found only by running it:

| Defect | How it surfaced |
|---|---|
| Used `narration:` for the per-scene text | Graph requires `text`; would raise `storyboard[i] has no 'text'` |
| Duplicate `"text"` key after a blind rename | Python keeps the last value — the quote silently became the narration |
| `balance: "12 480"`, `amount: "2.4"` | Zod wants numbers; `safeParse` fails and the composition falls back to a 120-frame default |

That last one deserves emphasis: **a failed `safeParse` in `Root.tsx` does not
throw.** It falls through to a default composition, and the only visible symptom
is a wrong duration (`Cannot use frame 240: duration is 120`). Render "succeeds",
wrong video ships.

Verify a prompt example the same way as production code:

```python
ast.parse(code)                     # catches duplicate keys, syntax errors
sb = ast.literal_eval(storyboard)   # extract the literal
assert all(s.get("text") for s in sb)
used = [s["preset"] for s in sb]
assert len(set(used)) >= 4 and not any(a == b for a, b in zip(used, used[1:]))
```

Then run it through the real graph and render a frame or two.

### Verify every API the prompt names

The doc claimed `result["spec"]`; the graph only ever sets `result["spec_path"]`.
A checklist snippet that raises `KeyError` teaches the next agent to skip the
check. Grep for each key and error string quoted in a prompt:

```bash
grep -n 'state\["spec_path"\]' msf/graph/video_graph.py
grep -rn "has no 'text'" msf/graph/video_graph.py
```

---

## 5. Editing a long SKILL.md/prompt without corrupting it

Two self-inflicted problems worth avoiding:

- **A patch whose anchor sits inside a fenced code block** silently injects prose
  into the fence and duplicates whole sections. After any large patch to a doc,
  audit structure rather than eyeballing: count fences (must be even) and check
  for duplicate headers.

  ```python
  hs = re.findall(r'^#{1,4} .*$', text, re.M)
  print("fences:", text.count("```"), "dups:", {k: v for k, v in Counter(hs).items() if v > 1})
  ```

- **Blind global replace creates duplicate JSON/dict keys.** Renaming
  `"narration"` → `"text"` collided with a scene that already had `"text"`. Parse
  the result (`ast.parse`) rather than trusting the replacement.

---

## 6. Measurement hygiene that applies here

Two false alarms from this session, both caused by the *measuring* code:

- A "missing field" was really the test script's own print filter excluding
  `text`. Before reporting data loss, check whether the diff is hiding it.
- A vision model asserted a chart's legend colours mismatched its arcs and that a
  card was "compressed horizontally". Pixel measurement showed legend swatches and
  arcs identical (`#00FF88`/`#00D4FF`/`#FF4D9D`) and aspect 1.612 vs ISO 1.586.
  **Vision is a defect *detector*, not an oracle** — it finds things numbers miss
  (a chat contact named "Telegram", an invented `%` suffix) and also invents
  defects. Confirm each claim with a measurement before changing code, and drop
  the ones that don't survive.
