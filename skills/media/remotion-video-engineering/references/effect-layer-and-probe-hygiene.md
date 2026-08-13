# Effect Layer: the no-op contract, probe hygiene, and defects only pixels find

Companion to `references/transitions-and-motion-layer.md`. That file proves a
*transition* composites. This one covers a **library of composable effects**
(entrance / exit / emphasis / visual / scene / transition families) and how to
prove each one actually does something — and, just as important, does *nothing*
when asked to.

---

## The contract worth enforcing: `intensity = 0` is a byte-exact no-op

Every effect takes an `intensity` prop. The contract:

- `intensity === 0` → output is **byte-identical** to rendering the same frame
  with no effect wrapper at all.
- `intensity === 1` → output **differs** from that bare render.

This one property is worth more than any amount of visual review, because it is
the only cheap check that separates *"the effect is wired in and reaching the
pixels"* from *"the effect is dead code that compiles"*. Both look the same in
`tsc`, in a screenshot, and in a subagent's summary.

Implement it as an early return so it's genuinely free, not merely small:

```tsx
export const Glow: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  if (intensity === 0) return <>{children}</>;   // no wrapper div at all
  ...
};
```

Returning a wrapper `<div>` with neutral styles is **not** a no-op — an extra
stacking context or `width:100%` box shifts layout and the sha1 changes.

Proof shape (see `templates/effect_noop_proof.py`):

```
effect                 i=0 sha   no-op?       i=1 sha  changes?
----------------------------------------------------------------
FadeIn            eb561643b993      YES  860e5653136a       YES
Glow              eb561643b993      YES  4da350ed1a06       YES
```

`i=0 sha` must equal the bare control sha for every row. Cover **every family**
with at least a few representatives; a family that shares a base wrapper tends
to pass or fail as a group.

---

## Sampling-frame arithmetic: correct behaviour that looks like breakage

**The single biggest time sink.** An effect sampled outside its active window is
*correctly* doing nothing, which is indistinguishable from being broken.

| Family | Active window (duration 90, `EFFECT_FRAMES` 24) | Safe sample |
|---|---|---|
| entrance (`FadeIn`, `ScaleIn`) | frames `0 … 24` | **8** |
| exit (`FadeOut`, `SlideOutLeft`, `ScaleOut`, `BlurOut`) | frames `66 … 90` (`duration − 24`) | **78** |
| emphasis / loops (`Pulse`, `Breathe`, `Glow`) | entire clip | any |

Two real misdiagnoses from one session, both from a bad sample frame:

- Sampled entrance effects at **frame 30**. The 24-frame animation had already
  settled back to its resting state, so `i=1` matched `i=0` and six effects
  looked simultaneously broken. Six effects failing at once is itself the tell —
  suspect the harness, not the library.
- Sampled exit effects at **frame 8**, 58 frames before they start. Same false
  alarm.

Bake the frame per suite into the harness so the arithmetic can't be
re-derived wrong later, and comment *why*:

```python
{
    # Exit effects start at durationInFrames - 24, i.e. frame 66 of 90.
    # Sampled any earlier they are correctly doing nothing, which is
    # indistinguishable from being broken.
    "label": "exit (sampled inside the exit window)",
    "frame": 78,
    "effects": ["FadeOut", "SlideOutLeft", "ScaleOut", "BlurOut"],
},
```

Also namespace output files by frame (`{effect}_f{frame}_{intensity}.png`,
`bare_{probe}_f{frame}.png`). Two suites sharing a bare-control filename
overwrite each other's PNG and silently compare against the wrong baseline.

---

## Four traps that eat a subagent's entire iteration budget

All four produce *misleading* errors, which is why they are expensive.

1. **`Root.tsx` gates probe compositions behind spec validation.** If the root
   registers probes only when `VideoSpecSchema.safeParse(props)` succeeds, an
   invalid `--props` leaves **only `Main`** registered and the failure reads
   `Could not find composition "EffectProbe"`. The message points at the
   composition; the bug is in the props. Build probe props as *a valid spec plus
   the probe's own fields* — a real `scenes[]` entry with a real preset name.
   (Passing a preset that doesn't exist, e.g. `HeroTitle` when the registry has
   `HeroKinetic`, fails the same misleading way.)

2. **`--props` rejects MSYS paths.** Node does not understand `/c/Users/...`.
   Use a path relative to the Remotion project dir (`--props=out/probe/_p.json`)
   and `cwd` into it. This alone stalled two subagents.

3. **`npx remotion still` exits 0 on a throwing component.** Exit code, file
   existence, and file size are all worthless as evidence. Only the pixels are
   evidence. Corollary: `sha = hash(p.read_bytes()) if p.exists() else None`
   silently yields `None == None` → a bogus `True` "match". Assert the file
   exists before comparing.

4. **A component imported in `Root.tsx` but never wrapped in `<Composition>`
   cannot be caught by `tsc`** — the import *is* used, just not registered. Two
   probe compositions were written, imported, type-checked clean, and invisible
   to the renderer. Whenever a composition "doesn't exist", grep for its
   `<Composition id=` before touching anything else.

---

## Mutation-test the probe before trusting `ALL PASS`

`ALL PASS` across 112 sounds or 108 effects is not a result — it's a claim about
the probe. Prove the probe **fails on bad input** by injecting known defects one
at a time and confirming each is caught:

```python
mutations = [
    ("silent sound",     <return zeros>),
    ("overlong sound",   <return 2.0s buffer>),
    ("clipping",         <return ones * 3.0>),
    ("edge click",       <return un-faded sine>),
    ("nondeterministic", <default_rng() with no seed>),
]
for label, mutated_src in mutations:
    src.write_text(mutated_src)
    caught = "ISSUES" in run_probe().stdout
    print(label, "YES" if caught else "NO -- BLIND SPOT")
src.write_text(original)          # always restore
assert "ALL PASS" in run_probe().stdout   # and verify the restore
```

A real run of exactly this caught 4 of 5 and exposed one **blind spot** (the
edge-click check did not fire on an un-faded tone). Verdict: `PROBE HAS BLIND
SPOTS` — which is a far more useful thing to know than `ALL PASS`. Always
restore the original and re-run to confirm the restore, or the mutation harness
leaves the codebase broken.

---

## Defects this class of check actually found

Each of these passed `tsc` and looked plausible in review.

- **`drop-shadow` glow is invisible on opaque content.** `filter:
  drop-shadow(0 0 Npx …)` blurs the element's *alpha silhouette* and draws it
  **behind** the element. A full-frame opaque child therefore hides its own
  shadow, and the effect is byte-identical to bare at **every** frame. Fix: keep
  the drop-shadow for cut-out shapes, and additionally layer an additive bloom
  *on top* (`position:absolute; inset:0; mixBlendMode:'screen'` with a radial
  gradient) so the effect registers regardless of child alpha.
  Note the smell: an effect that fails at *all* sampled frames is a wiring or
  compositing bug, not a timing bug.

- **Round line caps draw a half-disc at zero length.** An animated donut/arc
  with `strokeLinecap:'round'` renders visible stub dots at the start position
  of every not-yet-grown segment, spoiling frame 0. Use `butt` until length > 0,
  or gate the cap on progress.

- **Centering with `left: cx` and no compensation overflows.** `left: cx` places
  the element's *left edge* at the centre; without
  `transform: translateX(-50%)` (or `left: cx - w/2`) a wide card ran 3935 px
  past the right edge while every schema check stayed green. A safe-area probe
  catches this; review does not.

---

## Verifying a subagent's effect work

Subagent summaries are self-reports and were wrong in both directions in one
session:

- Five children reported `completed` having written **nothing**. The tell was
  wall-clock: each "finished" in ~4 s because the configured delegation model
  no longer existed upstream and every call 400'd immediately. **A child that
  completes a code-writing task in seconds did not do it.** Before dispatching a
  large batch, send one throwaway child and confirm it produced a file.
- Three children wrote 3758 lines that compiled cleanly, yet **none** completed
  the pixel proof — reports contained `sha1=ERROR` and `MISSING` while still
  reading as success. They had each burned their budget on traps 1–3 above.

Verify by artifact, never by summary, and prefer a count you can compare to the
plan:

```bash
# registry counts, straight from the source of truth
npx tsx -e "import {EFFECTS} from './src/registry/effects'; \
            console.log(Object.keys(EFFECTS).length)"
python -c "from msf.audio.sfx import SFX_REGISTRY; print(len(SFX_REGISTRY))"
```

Export names are easy to guess wrong (`SFX_REGISTRY` / `MUSIC_REGISTRY`, not
`REGISTRY` / `MUSIC`) and a wrong guess raises `ImportError`, which reads like a
missing feature rather than a typo. Grep the module for its actual exports
before concluding anything is absent. Where effects live across several registry
modules, sum them all — a single-module count under-reports and looks like the
subagents did less than they did.

Report the split honestly: "audio 112/112, effects 108/108, scenes 17/104" is
useful; "all done" is not.

---

## Cheap invariant probes worth keeping alongside the pixel proof

- **Coverage / uniqueness.** Every registered name is reachable exactly once,
  no two entries share a summary or key. Catches copy-paste registration.
- **Safe-area containment.** Every scene's bounding box within
  `top 280 / bottom 380 / l-r 80` (see `references/vertical-scene-design.md`).
- **Geometry assertions on data-driven presets.** For a donut, assert measured
  gap angles equal the requested gap and that per-segment arc length matches the
  data share (measured `219.5 / 85.0 / 49.6°` against `62 / 24 / 14 %`). Vision
  cannot do this; arithmetic can.
- **Determinism.** Render the same frame twice, same sha1. Catches unseeded RNG
  in generative effects.
