---
name: remotion-video-engineering
description: "Build/upgrade Remotion pipelines, 9:16 shorts, spec validation, scene variety."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [remotion, video, shorts, reels, tiktok, motion-graphics, react, typescript, captions, audit]
    related_skills: [qwen3-tts, short-video-scriptwriter, video-quality-assessment]
---

# Remotion Video Engineering

Building, auditing, and upgrading **Remotion** (React/TypeScript) video pipelines —
especially automated 9:16 vertical shorts.

Covers two things a future session keeps needing:
1. **How to ground an upgrade plan in measured reality** instead of assumptions.
2. **A verified catalogue** of the Remotion ecosystem, so you don't invent packages.

> **A web panel / dashboard over the pipeline** — `references/pipeline-control-panel.md`.
> The request ("следить за процессом, видеть какие голоса, сцены, эффекты есть") is an
> observability fix for the invisible-library bug class, so the panel must be a **view over
> the same registries the pipeline reads**, never a second catalogue that can drift. Covers:
> previews routed through the pipeline's own render paths (and validated first, or a red
> ERROR card displays as a working preview); long jobs as **subprocesses drained by a reader
> thread**, because `readline()` on a blocking pipe hangs the HTTP handler for the whole
> quiet stretch of a render; status checks that probe and report what they inspected;
> path-traversal hardening for file-serving routes when there is no auth; and the
> **"plausible wrong answer"** bug class this work generates — reading a dataclass field
> that does not exist, guessing a builder function name behind a bare `except`, passing a
> parameter key the callee ignores, and `replaceChildren()` stringifying `null` onto the
> page.

> **New preset pack authoring** (QuizCard, ProgressPath, DefinitionCard, TimelineReveal,
> LyricLines, ScoreHud, CountdownHero, VersusSplit, PostCard, CommentWall, SubscribeCTA,
> Leaderboard patterns; `resolveMotion` valid channel list; `'entrance'` pitfall + correct
> mappings; `safeArea as SafeAreaMode` cast pattern; concurrent presets.ts collision
> recovery; identical-file-size false-positive detection; probe JSON VideoSpec wrapper
> requirement; two-frame reveal/countdown/karaoke state verification; beat-division,
> karaoke-word-fill, deterministic-spark, diagonal-clip-slide design patterns;
> temporary-register + git-revert workflow) lives in `references/msf-preset-pack-authoring.md`.
>
> **Style kits / theme palettes** (the layer that recolours a whole video from one
> field) live in `references/style-kit-palette-authoring.md`: the dead-code check —
> grep for the *accessor* being called, since eight fully-specified kits shipped with
> nothing importing `getStyleKit`; why kits sharing a palette render pixel-identical
> (distance 0.0) unless the **accent triad** changes and not just `bg`; the `muted`
> ≥4.5:1 legibility class (one kit at 2.98 had invisible captions); and the three ways
> a colour probe lies — a metric that can't separate a known-good control, a row-average
> that folds mesh glow into the "background", and averaging a two-hue accent into a
> colour present nowhere in the frame.
>
> **Nesting one scene inside another** — a preset rendered on a phone/browser screen via
> `innerPreset` — lives in `references/nesting-scenes-in-device-frames.md`: render the child
> at canvas size and *scale* it, never lay it out at screen size; the scale-factor decision
> where `max(w,h)` silently cropped **80px per side (7.4 % of canvas width)** and ate the
> first and last character of every line, versus fitting width and anchoring the leftover
> band to the edge the child's UI expects; why a cropped frame ships and a letterboxed one
> gets fixed on day one; parent effects (`RackFocus`, `TiltShift`) destroying the very
> content the shot exists to show; and the case where a pixel probe ("bottom gap 1 px") and
> vision ("empty bottom third") were **both right** because one measured fill and the other
> semantic occupancy. **Superseded on one point:** the "which edge gets the slack" framing is
> itself the bug — derive the device screen from the *canvas* aspect so the fit is exact and
> no slack exists. See `references/css-3d-faces-and-relocated-slack.md` §1.1.
>
> **Hero text that overflows, and the sample point that hides it** lives in
> `references/text-fitting-and-beat-sampling.md`: sizing a hero string by a fixed
> `height * 0.14` fitted only ~6 wide caps, so a 7-glyph word spanned x0..x1079 of a 1080 px
> frame and read `ОГНАЛ` instead of `ДОГНАЛИ` — with the reference-free bbox assertion
> (ink touching *both* edges is the signature), the `fitOneLine` ceiling-reducer fix, and the
> `grep` audit that separates legitimate fixed fractions (avatars, rows) from illegitimate
> ones (any dimension containing spec-supplied text). Plus the sampling lesson that let it
> survive a full per-scene still pass with vision review: **beat-divided presets**
> (`from`, `revealAtProgress`, `sendAtProgress`, `steps[]`) hold different content per beat,
> so one mid-scene frame at 72 % lands on a countdown digit and never sees the payoff —
> sample per beat, or 30/72/92 %, and always pull frames from the encoded mp4 before
> delivering.
>
> **Audit #4: Preset capacities, fixed-font risks, Zod passthrough & transition fade pop fix**
> live in `references/audit-4-preset-capabilities-and-transitions.md`: full 13-preset prop & default mapping, capacity limits (Leaderboard >7 rows overflow, QuizCard >4 options clip, LayerStack3D >6 layers camera OOB), fixed font size truncation risks (Leaderboard 40px, RingStats 36px, VersusSplit 0.62 Cyrillic factor), Zod `.passthrough()` silent fallback trap, and the `@remotion/transitions` `fade({ shouldFadeOutExitingScene: true })` root-cause fix.
>
> **Row/column width budgets, and the `flex: 1` that DELETES text** — `references/chart-and-widget-visual-design.md`
> §1c-bis/§1f/§1g/§3a. A `Leaderboard` row summed to 977 px inside a 920 px table, so the
> `flex: 1` name column absorbed the overflow and collapsed to **zero width**: with
> `nowrap` there is no ellipsis, the rows simply had no text, and the frame impersonated a
> *missing feature* rather than a layout bug. Reserve the text column first, make the
> decoration elastic (a stub bar still reads as a bar; a missing name is zero information).
> Same section: `label` silently ignored as an alias for `name` (its `undefined` also fed
> the avatar, so every row showed **"U"** and read as an unfinished template); rank badges
> make ordering a *correctness* claim, so a widget drawing 🥇 must sort its own data (an 81
> sat fifth while a 77 took gold); and fixed-height label slots, because flex aligns on the
> item box — a wrapping name lifted its RingStats ring off the shared centre line
> (`974/977/974` → `959/963/959`) exactly as it dropped a Bars3D bar below the baseline.
> **Brand logo assets, and the row that had to be STACKED** — `references/brand-icon-assets-and-row-stacking.md`,
> plus the runnable `scripts/sync_model_icons.mjs`. Picks up where §1c-bis leaves off:
> reserving the text column only moved the starvation, so the bar clamped to a 74 px
> stub and the next report was *«полоска слишком маленькая»*. Key traps: `fitOneLine`
> **CLAMPS at `minFontSize` and does not promise a fit**, so with `overflow: hidden`
> the text is sheared mid-glyph — the signature is several long strings ending at
> *exactly* the same x, rendering `Claude-Opus-4.` with the 6 gone; four separate
> splits of one row each shipped their own defect before the arithmetic got written
> out (500 px available, bar needs ~250, an 18-char name ~310), and the answer was to
> spend the **unused vertical space** — the row was 206 px tall using ~40 (bar fill
> 203 → 488 px, thickness 29 → 75 px). Asset side: `@lobehub/icons-static-svg` must be
> **copied into `public/`**, since `staticFile()` ignores `node_modules` and a
> node_modules path is green in the dev bundler and 404s in the render; `currentColor`
> resolves to **BLACK inside `<img>`** (8 of 42 icons), an invisible logo with no error
> anywhere; match the brand **substring** not the exact name, because nothing upstream
> emits vendor slugs and a lookup table degrades silently to a letter avatar on the
> next release. Also: corrections **oscillate** — the same margin went 21 px (cramped)
> → 79 px (excessive) → 48 px, because fixing an upstream overflow changes every
> downstream margin.
>
> Two habits to keep: **re-render with the longest string the pipeline can emit** (every one
> of these was invisible with the built-in `Aria Chen` / `Скорость` defaults), and **check
> the frame maths before diagnosing** — with 150-frame scenes, frames 120/130/140 are all
> scene 0, and I wrote a paragraph about the wrong preset before noticing.
>
> **Imitating a real app's UI** (a messenger/browser mockup judged against a screenshot the
> user can pull up in seconds) lives in `references/replicating-real-app-ui-in-presets.md`:
> mine the reference in ONE vision pass for hex/radii/grouping/icon order before writing
> code; the ranked defect list where **font is the loudest tell** (the preset inherited the
> style kit's serif `fonts.body` — a serif chat bubble is fake at thumbnail size) and bubble
> colour is second (pale green read as *WhatsApp*; Telegram's outgoing is blue `#3996EC` with
> white text); run-grouping rules (nib on last-of-run only, that corner squared, tighter gap
> within a run); the tail svg that rendered **nothing** because its ink sat in the wrong half
> of the viewBox, caught by a max-x-per-row probe rather than by eye; app chrome anchored to
> the *screen* edge and not the video safe area (the composer left a fifth of the frame as
> bare wallpaper); stateful chrome (mic until text exists, placeholder returns after send,
> composed bubble inherits a timestamp); sender name gated behind `isGroup`; and the
> render → *harsh* vision critique → fix loop, which took four rounds because each fix
> exposed the next defect. §6.1 adds the other half of that loop: a critique is a list of
> **candidates, not findings** — one round confidently reported a missing bubble tail that a
> max-x-per-row probe proved was present and identical to its sibling, and two more items
> were a wrapped *timestamp* and a truncation in the user's own reference. Decide per item
> whether a probe can settle it, and run the probe before writing code.
>
> **Mixing music beds and SFX in** (an audio package that exists in the tree but was never
> imported — `grep` the *import*, not the file) lives in
> `references/mixing-a-soundtrack-layer.md`: why the mix has to be ONE root track with
> per-scene urls cleared, the 24 kHz→48 kHz half-speed trap, cue timing that must subtract
> transition overlap, degrade-vs-raise policy, and three-window verification where the gap
> between clips proves the bed exists.
>
> **A rendered mp4 whose audio track is digital silence** lives in
> `references/audio-track-silence-diagnosis.md`: why `ffprobe` clears a broken file (it
> reports the container, not the signal) and `ffmpeg -map a:0 -af volumedetect` is the only
> honest check — `mean == max == -91.0 dB` is the all-zero-PCM signature versus ≈ −17/−3 dB
> for real speech; why `loudnorm` exonerates itself but is useless as a net (a normaliser
> cannot manufacture signal); the **two-path divergence** that caused it, where the fast
> `--props=spec.json` CLI render skips the synthesis node so `{audioUrl && <Audio/>}` never
> mounts and the encoder still emits a full-length silent AAC track; the one probe that
> settles it (inject `audioUrl` pointing at wavs already on disk → −16.7 dB); the
> write-under-one-key/read-under-another field drift that works only while both sides derive
> the same string from the same index; root+per-scene tracks double-playing; and TTS
> wall-clock as a planning input (62 s per sentence, 24 kHz into a 48 kHz container).
>
> **Repairing that silence, and proving a cross-fade blends** live in
> `references/wiring-voiceover-and-proving-a-crossfade.md`: the three-case assertion that
> catches an unconditional `audio_url=f"scene_{i:02d}.wav"` making caller-supplied paths
> unreachable; a `DEFAULT_VOICE` naming a key absent from the registry, which fell through to
> a transcript-free path and silently downgraded every render from ICL prosody to x-vector
> timbre-only *at normal loudness*; why the 62 s/sentence figure was cold-start and not
> per-phrase (96.4 s then 22.2 s through one process — never benchmark TTS with one call, nor
> with a repeated string); the design of a tool that voices an already-authored spec
> (validate-before-model-load, retime scenes to narration length, name wavs after the spec);
> per-scene audibility where `-ss/-to` returned **identical means to 0.1 dB** for two
> different windows and `atrim` inside the filter chain was the honest scoping; and the
> cross-fade probe trap where a strict colour mask reports `BOTH: 0` *both* before and after
> the fix, because a 50 % blend of two saturated hues matches neither mask — pair it with a
> continuous statistic (mean-RGB ramp) that cannot go blind at the crossover. Plus the
> `git stash` check that separates your regression from pre-existing test debt.
>
> Detailed catalogue lives in `references/remotion-ecosystem-catalogue.md`.
> Validation + agent-guardrail detail lives in
> `references/spec-validation-and-agent-guardrails.md`, with a runnable harness at
> `scripts/agent_spec_probe.py`.
> Safe zones, chart readability, the 8-category scene taxonomy, micro-primitives,
> the anti-sameness script graph, the scene-design doctrine (carriers not
> illustrations), the unified `motion` interpolation contract (with staggered reveal/transform channels via `calculateStagger`), and programmatic 3D
> model sourcing live in `references/vertical-scene-design.md`.
> Transitions wiring (`TransitionSeries` timeline math, per-presentation
> signatures, the z-index stacking-context trap, and the pixel probe that proves
> a transition composites) plus verified Remotion API behaviour and the zod4
> upgrade path live in `references/transitions-and-motion-layer.md`.
> The effect-layer no-op contract (`intensity=0` is byte-exact), the sampling-frame
> trap (finished animations look identical to bare), the four `--props`/composition
> registration traps that stall subagents, mutation-testing a probe, and the
> defects only pixels find (invisible drop-shadow glow, round-cap stubs, off-centre
> cards) live in `references/effect-layer-and-probe-hygiene.md`, with a runnable
> harness at `templates/effect_noop_proof.py`.
> **Fixing** the semantic defect class — the fix pattern per class, the A/B
> differential render that proves a *text* fix landed with no vision tooling and no
> OCR, and the layout-collision patterns (band table, tracking in units of the
> face) — lives in `references/fixing-semantic-scene-defects.md`.
> The **aesthetic** defect class — a widget that measures exactly right and still
> gets rejected — lives in `references/chart-and-widget-visual-design.md`: the five
> ratio defects behind one "ugly" (widget claiming the full safe width, stroke at
> 30 % of radius, `flex:1` separating a label from its value, a default that can only
> print a tautology, a metallic brand token used as a data colour), plus the ring
> measurement hygiene that stops you inventing defects (settled-frame check, radial
> profile for the mid-line, hue classification that survives a colour grade, the
> `2n−1` transition cross-check) and a pre-flight ratio checklist.

---

## When to use

- Asked to improve/extend an existing Remotion project (quality, styles, presets, captions).
- Asked to write a plan or roadmap for a video-generation pipeline.
- Choosing which Remotion packages/templates to adopt.
- Diagnosing why rendered output "looks cheap" or amateur.
- Building or auditing a **library of composable effects** (entrance/exit/emphasis/
  camera/grade/distortion/overlay), or verifying work a subagent claims to have
  finished — see Rule 1g and `references/effect-layer-and-probe-hygiene.md`.
- The user rejects a frame on **looks** ("this chart is rubbish", "ugly", "неоч")
  even though every probe passes — see Rule 1b3 and
  `references/chart-and-widget-visual-design.md`.
- The user says the generator **"only ever uses 3-4 scenes"** and asks you to fix
  the prompt. Treat the prompt as a hypothesis: run the reachability probe in
  `references/preset-reachability-and-field-mapping.md` first, because a preset the
  pipeline cannot physically produce is not a wording problem. Check the
  **capability gate** in the same pass (§3b there) — a hand-written allow-list that
  never grew with the library silently rewrites valid presets to a fallback, and from
  outside that is indistinguishable from a lazy prompt.
- Asked to **widen what weak vs. strong agents may do**. A gate's job is stopping a
  weak caller writing untested code, *not* restricting which finished presets it may
  use; conflating the two starves the tier that depends on presets most. Guidance
  side: weak agents need a mechanical selection algorithm (label each beat by content
  type → map label to preset → enforce checkable rules), strong agents need a ladder
  that makes authoring new React the **last** rung, after existing-preset,
  composition (effects/overlays/nesting), and add-an-opt-in-prop.
- Asked to **add visual variety without new components** — more styles, more moods,
  "чтобы стили авторедачили цвета сцен". That is a style kit, not a preset: see
  `references/style-kit-palette-authoring.md`. Check first whether the style layer is
  even wired (a fully-specified kit set can exist with nothing importing its accessor),
  then prove each new kit is both *distinct* (pairwise pixel distance) and *legible*
  (`muted` contrast against its own `bg`) — those are different properties and a
  distinctness check happily passes a kit whose captions are invisible.
- Asked to **write video scripts / scenarios / storyboards** ("сценарии", hooks + beats +
  CTA), especially aimed at driving traffic to a channel. Deliver **renderable spec JSON**,
  not prose — prose cannot be validated and quietly encodes scenes that don't exist. See
  `references/authoring-specs-against-a-live-schema.md` §6 for the pacing arithmetic,
  the per-scene style-kit variety trick, the narration-field requirement, and the
  run-it-through-the-gate-at-level-1 check.
- Building a shot where **one scene renders inside another** (a UI on a phone/tablet/browser
  via `innerPreset`, or any sub-viewport with a different aspect ratio than the canvas) —
  see `references/nesting-scenes-in-device-frames.md`.
- **Every rendered scene came out the same file size.** That is a shared error card,
  not a coincidence — see the identical-file-size section in
  `references/msf-preset-pack-authoring.md`. A `safeParse` failure in `Root.tsx`
  renders an error composition instead of throwing, so the renderer reports success
  and every input yields the same frame.

---

## Rule 1 — Measure before you plan

A plan written from assumptions about a codebase is worthless. Before proposing anything,
gather **four kinds of evidence**, and cite them in the plan:

1. **Installed versions, not assumed ones.**
   ```bash
   node -p "require('./node_modules/remotion/package.json').version"
   node -p "require('./node_modules/react/package.json').version"
   node -v
   npm view remotion version          # compare installed vs latest
   ```

2. **Actual code shape.** Read the composition root, the scene dispatcher, the spec
   schema, and the theme file. Count presets with `wc -l` rather than trusting docs.

3. **The rendered output, judged visually.** Run `vision_analyze` on a rendered frame
   or contact strip and explicitly ask for a *brutal* critique of typography, contrast,
   depth, dead space, and readability at phone size. Ask it to score the frames as
   short-form content. This converts vague "make it prettier" into a concrete
   defect list you can turn into phases, and gives an objective before/after metric.

4. **Which packages are actually installed** (`ls node_modules/@remotion/`) versus which
   exist upstream. The delta is usually where the biggest wins hide.

Then state findings as *facts with provenance* ("verified via `npm view`"), and separate
them from recommendations. Where a doc/config contradicts the code, say so plainly —
a config or skill that lies about the system is worse than none.

## Rule 1b — A successful render is not a correct render

Remotion draws its **own error card as video**. A spec Zod rejects still yields
exit code 0, a valid MP4, a plausible file size and a correct duration. Four
promo shorts once shipped as full-screen red error screens with every
file-level check passing.

Two guards, both cheap:

1. **Zod pre-flight before rendering.** Python-side validators typically check
   preset names and required keys but *not field types*, so they pass specs Zod
   fails. Bundle the real `.ts` schema with esbuild (already a Remotion dep) and
   validate the spec JSON before spending TTS + render time. Zod names the exact
   path — `scenes.0.statValue :: Expected number, received string`.
2. **Post-render frame probe.** Remotion's error card is saturated red; sample a
   frame's mean RGB and reject `r > 100 and r > g*2 and r > b*2`. Dark themed
   frames measured `32,31,26` and `14,25,17`, nowhere near the trigger.

Never accept file existence, exit code, size or duration as proof of a good
render. Code in `references/spec-validation-and-agent-guardrails.md`.

## Rule 1b2 — Probes prove *presence*; only a watch-through proves *meaning*

Every probe in this skill answers "did pixels arrive, move, and stay in the box".
None answers "is the right thing on screen". A demo reel once passed Zod, `tsc`,
the red-frame probe, safe-area bounds, `intensity=0` byte proofs, span arithmetic
and 159 frames of numeric sampling — and the user found **five defects by watching
it once**: a chat header naming the contact "Telegram", two donut segments in an
identical hex, a plain count rendered as "108%", a scene vibrating at 60 Hz, and
segment gaps wider than requested.

Three authoring rules follow, all cheap:

1. **Defaults must not invent meaning.** A default supplying *units, names, labels
   or identity* fabricates content when the spec omits the field, and looks
   deliberate on screen — `statSuffix = '%'` turned "108 effects" into "108%".
   Default such fields to `''`/`undefined`; reserve defaults for geometry and
   timing, where a fallback is harmless.
2. **Derive palettes, then assert distinctness.** Semantic aliases (`neon`,
   `accentGreen`, `primary`) frequently resolve to the same hex, so any
   `[accentColor, ...BRAND_COLOURS]` list can repeat. De-duplicate
   case-insensitively against the resolved accent and assert
   `len(set(colours)) == n_segments`.
3. **A per-frame reseeded RNG is jitter, not drift.** `mulberry32(seed + frame*k)`
   gives neighbouring frames independent noise — measured ±1.4 px with direction
   reversing almost every frame. Organic motion must be a *continuous* function of
   time (layered sines, or value noise sampled at `frame/N` and interpolated).
   Seed once, outside the frame term.

Before delivering, run the five-question semantic pass in
`references/verifying-rendered-video.md` §10 (also: measurement recipes for
reference-free structure, jitter quantification, and ring colour runs). When
vision tooling is unavailable, say so rather than presenting numeric probes as
equivalent coverage — they are blind to this whole class. When a user-reported
defect has no proven cause yet, ask what they saw instead of pattern-matching a
plausible one.

## Rule 1b3 — An aesthetic rejection is a bug report; answer it with ratios

Rule 1b2 covers defects a watch-through *names* ("the header says Telegram").
This covers the harder case: the user rejects the frame and names nothing. A donut
chart measured 221.4 / 84.3 / 47.3° against 219.5 / 85.0 / 49.6 expected for
`62/24/14` after three 2° gaps — arithmetically exact — and the entire review was
*"бублик неооооч"* (the donut's rubbish). Correct geometry, rejected frame.

Treat it as a complete bug report that needs translating, not as vague taste:

1. **Do not re-run the probes that already passed, and do not answer with them.**
   They measured a different question. "But the segments are exact" argues with the
   user instead of looking at what they saw.
2. **Get a critique, then convert every complaint into a ratio.** Widget width ÷
   frame width, stroke ÷ radius, cap overhang in degrees, label-to-value distance.
   Ratios make an aesthetic verdict reproducible, diffable, and checkable next time.
3. **Verify each claimed defect before writing a fix.** A critique invents things —
   one confidently reported "a break in the green segment at 6 o'clock" on an arc
   that measurement showed ran continuously for 221.4°. Report a phantom as a
   phantom; claiming to have fixed it is worse than the phantom.
4. **Audit defaults for tautology and tokens for role.** `centerContent: 'total'` on
   a percentage breakdown can only ever print "100%"; a metallic brand colour used
   as a data series reads as dirty. Both pass every probe in this skill.

The five-defect breakdown, the ring-measurement hygiene that stops you inventing
fragments (settled-frame check, radial profile for the mid-line, hue classification
that survives a colour grade, the `2n−1` transition cross-check), and a pre-flight
ratio checklist are in `references/chart-and-widget-visual-design.md`.

## Rule 1c — A tool error is not evidence about the artifact

Calling a tool that does not exist returns a refusal that looks exactly like a
permissions failure. The pull to escalate from "this call failed" to "my access is
broken, so my earlier report may have been fabricated" is strong and it is wrong.
Acting on it once meant retracting a status report that was in fact backed by a
commit in `git log` and two artifacts on disk, then re-verifying everything from
scratch — and it makes every later report read as less trustworthy.

Before doubting the environment or your own prior findings:

1. Re-read the tool list and check the **name**. Wrong-name errors are
   indistinguishable from access errors at a glance.
2. Re-run the one check that produced the earlier claim. A SHA, an `ffprobe`
   line, or a byte count either reproduces or it does not.
3. Only then report a blocker, scoped to the single capability that failed —
   not to your ability to work.

Verified work stays verified until a probe contradicts it. Equally: when a
capability really is unavailable (e.g. `vision_analyze` returning provider
errors), say so plainly, state which checks you substituted, and do not present
numeric probes as if they covered what vision would have.

**Distinguish a wrong tool name from a broken environment.** A rejection reading
"Tool X does not exist" — for a tool you believe exists — is almost always a
typo in the *name* (`Read` vs `read_file`, `PowerShell` vs `terminal`) or a
wrong-case/wrong-host path. It looks identical to a permissions failure. Twice in
one session such an error was read as total loss of tooling, prompting a message
that withdrew previously *verified* findings (a commit SHA, two artifacts on
disk) — all of which reproduced immediately afterwards. Wrong-name errors leave
the environment untouched by definition. Re-read the tool list, fix the name,
re-run the same call; never escalate a single one into "I cannot work" or "my
earlier results may be fabricated".

## Rule 1d — Platform UI overlays the frame; reserve for it

A frame that passes `tsc`, Zod, ffprobe, volume, luminance *and* a red-frame probe
can still be broken, because the platform draws its handle, description, sound row,
like/share rail and progress bar **inside** your 1080×1920. No automated check in
this skill catches it — only looking at a frame with the UI in mind does.

Working reserve: **top 280, bottom 380, right 140, l/r base 80**. The readable band
is `y ∈ [280, 1540]`, about 66 % of height — compose for that box. Burned-in
captions below 380 px from the bottom get covered by the description.

When auditing, `grep` for **all** margin constants before trusting the first hit.
A real case had three disagreeing sets — schema `safeMargin: 120`, a
`typography_library.py` with `top 140 / bottom 240` that the graph never imported,
and platform reality needing 280/380. All three under-reserved the bottom, so
subtitles collided with platform UI on every render while checks stayed green. A
dead second definition is a hint someone already tried this fix and miswired it.
Keep exactly one `SafeArea`, exported from the schema module.

Full budget table, chart-readability verdicts and the taxonomy live in
`references/vertical-scene-design.md`.

## Rule 1f — Match the instrument to the defect: vision or pixel probe

Vision analysis is the right tool for layout, legibility, overflow, "is this an
error card", and text clipping. It is **unreliable for blending, opacity and
precise timing** — asked to judge 11 transitions from a tiled contact sheet it
reported 7 as broken when all 11 were compositing. `select` renumbers frames
before `tile`, so reasoned-about frame indices no longer match the tiles, and
semi-transparent compositing is hard to read from a still anyway.

For anything about *how pixels combine over time*, measure instead:

```bash
ffmpeg -v error -i out.mp4 \
  -vf "signalstats,metadata=print:key=lavfi.signalstats.VAVG:file=-" \
  -f null - 2>&1 | grep -o 'VAVG=[0-9.]*' | cut -d= -f2
```

Judge the **largest single-frame delta as a share of total range**: ~80–90 % in
one frame means a hard cut, ≲20 % spread across the overlap means a real blend.
Whole-frame averages are dominated by the shared background (a real fade moved
`UAVG` by only 0.36) — use the channel that separates the two scenes' accent
colours, and A/B the identical spec against `{"type":"none"}` as the control.

When a vision verdict and a measurement disagree, re-derive the measurement, but
don't discard it for the narrative — here the numbers were right *and* pointed at
the real root cause that vision had misattributed.

**A vision finding is a lead, not a verdict — and the traffic runs both ways.**
In one session vision caught three real layout defects the entire numeric gate had
passed (two elements overlapping inside a card, plus a card number clipped by
`overflow: hidden`), and in the *same* pass wrongly reported the card as "squeezed
horizontally" — measured aspect 1.612 vs ISO 7810's 1.586, a 1.6 % deviation. So:
reproduce each vision claim as a number before writing a fix, and re-look after
every fix, because fixing the collision is what exposed the clipping underneath.

**A dim or half-drawn element at mid-scene is usually the animation, not a bug.**
Pipeline QA that grabs one frame per scene at its *midpoint* systematically
misrepresents progressive-reveal presets. On a word-by-word `TypewriterSub`
scene the mid-frame legitimately shows spoken words bright and unspoken words in
the dim pending colour. Vision read exactly that as a render fault on 2 of 8
scenes — "lost alpha channel / opacity dropped to 10–15 %, these words merge
into the background" — confident, specific, and wrong, complete with a suggested
recolour.

Re-extracting the same scenes ~0.3–0.5 s before their end showed every word at
full brightness. Nothing was broken, and recolouring on that verdict would have
destroyed the reveal effect the preset exists to produce.

Note this **inverts Rule 1g's sampling advice**: for a timed *reveal* the
finished state is the one to judge, because mid-animation is supposed to look
incomplete. Entrance/exit *effects* still want a mid-animation sample. Match the
sample point to what the preset is doing, and never accept a "text too dim /
element missing" verdict on a reveal until it survives a second sample near the
scene end.

## Rule 1k — Element-vs-element geometry is its own defect class

Every probe in this skill checks a *global* property: frame edges (safe area),
hue (red card), byte equality (`intensity=0`), time (span arithmetic), motion
(frame hashes). **None checks whether two elements inside the same container
overlap each other**, and none notices text amputated at a *container* edge —
`overflow: hidden` deletes the evidence a bounds check would need.

Two authoring rules prevent the whole class:

1. **Position rows from one declared band table, never from independent magic
   percentages.** `top: cardH*0.52` and `bottom: cardH*0.14` cannot know about
   each other; a `band` object of `{top, h}` per row makes overlap arithmetically
   checkable. Two rows may share a `top` only when they hold disjoint horizontal
   columns — assert that, don't imply it.
2. **Express tracking in units of the face it tracks.** A fixed
   `letterSpacing: cardW * 0.012` silently overflows the moment the type size
   changes; 19 monospace chars at a 63.7 px face plus 9.48 px tracking measured
   906 px against 664 px available, and the last four digits of a card number
   vanished. Derive the face from the width budget (monospace advance ≈ 0.60em),
   then set tracking as a small fraction *of the face*.

When a crowded band forces a move, prefer where the real artefact puts it (the
scheme mark belongs top-right on a card). Shrinking type to resolve a collision
trades a geometry bug for a legibility one.

Fix patterns: `references/fixing-semantic-scene-defects.md` §2f–2h. Measurement
recipe (card-rect detection, per-row ink bbox, the
`cardRight - inkRight > cardW*0.05` assertion):
`references/verifying-rendered-video.md` Recipe D.

## Rule 1e — A scene list is judged as a contract, not a menu

Two scene-list drafts (48 items, then 20) were both rejected on the same two
grounds. Apply these before proposing any catalogue, or expect a rewrite:

1. **Scenes must be carriers, not illustrations.** If a component can only serve
   one narrow subject (a dial for one metric, a shell session), it is a variant of
   something broader — not its own entry. Test: *could this carry two videos on
   incompatible topics?*
2. **Every parameter must visibly change the frame.** Micro-flags nobody will set
   are noise in the contract and extra surface for weak models to get wrong.
3. **Interpolation is one shared contract, not per-scene flags.** ~30 scattered
   `*Ease` / `*Speed` / `*Curve` fields collapse into a single `motion` object with
   channels (`camera`, `value`, `reveal`, `transform`, `opacity`). Default
   `easeInOut`; **never default to linear**. Weak agents get an `intensity` enum
   only — the raw numeric object stays validator-gated.

Also state plainly which scenes already exist versus which are aspirational. A list
that mixes shipped and planned items reads as a status report and misleads.

Doctrine, the `motion` type and the coupling rules (camera position vs look-at;
counter curve vs the shape it annotates) are in
`references/vertical-scene-design.md`.

## Rule 1c — Set agent guardrails from a measurement, not a hunch

Before restricting what a weaker model may do, test whether **documentation**
fixes it. Run identical spec-authoring tasks against the same models with only
the brief changed, and score output against the real schema plus semantic checks.

Measured on this pipeline with `scripts/agent_spec_probe.py`:

| Model | Original brief | Brief + explicit type rules |
|---|---|---|
| `gemini-3.6-flash-medium` | 2 / 5 clean | **5 / 5** |
| `gemini-3.6-flash-high` | 2 / 5 clean | **5 / 5** |

Findings worth carrying forward:

- **A higher tier is not automatically better at contract-following.** `high`
  scored identically to `medium`. Both chose sensible presets and wrote good
  copy, then supplied wrong *types* (`statValue: "6.8"`, `steps: ["a","b"]`).
- **The same mistakes a human makes on that contract signal under-documentation,
  not weak models.** Fix the contract's docs first.
- **Wrong/right pairs beat prose.** `WRONG: "statValue": "6.8 GB"` next to
  `RIGHT: "statValue": 6.8, "statSuffix": " GB"` outperformed a sentence saying
  the field is numeric. Near-miss shapes (`{label,value}` vs
  `{title,description}`) need showing explicitly — models invent them confidently.
- **Restrict only what is irreversible.** Docs closed 100 % of observed errors,
  so no capability was removed. The real line is the right to *write code*
  (level ≥ 3), not the length of the preset list — a wrong field type is caught
  by a validator, a broken React component is not.
- **Verify model IDs before designing a sweep.** `GET /v1/models` first; a tier
  you assume exists may not, and a 404 mid-sweep wastes the run.

## Rule 1e — Delegated research is a lead, not evidence

Fanning research out to subagents is useful for breadth, with two caveats learned
the hard way on this pipeline:

- **`status=completed` only means the process exited.** One research task returned
  a fragment of a crashed script (`Failed to fetch {doc}: {e}")`) as its whole
  summary. Read a summary for *shape* — truncated mid-sentence, unstructured, or
  code where prose was asked for means the task failed. Oversized summaries are
  trimmed to a file path in the footer; `read_file` it before assuming an omission.
- **Re-verify before anything enters a plan.** Every borrowed claim got checked
  here — `npm view` for versions, HTTP status for the donor repos, reading the
  constant in code for preset lists. Keep only what survives, and label provenance
  so a later session can distinguish checked facts from inherited ones.

Dispatch research *before* the work it informs. Results that arrive after you have
independently verified the same ground are wasted spend, and merging them into a
file you have since edited risks clobbering newer work.

## Rule 1i — Sample the delivered artifact, and compute scene spans first

Two habits, both cheap, both caught real problems.

**Extract frames from the encoded mp4, not with a fresh `remotion still`.**
`still` re-renders from source: it proves the code *can* draw a frame and says
nothing about what survived into the file you are handing over. Use
`ffmpeg -i out.mp4 -vf "select=eq(n\,140)" -vsync 0 -frames:v 1 f.png` — omit
`-vsync 0` and ffmpeg may hand back frame 0 regardless of `select`. Then
`sha1sum` a few sampled frames: distinct hashes prove motion survived the encode,
and identical ones exposed a frozen orbit that `tsc`, exit code, luminance and a
content probe all passed (see Rule 1h).

**Compute scene spans before choosing which frames to sample.**
`TransitionSeries` overlaps neighbours, so scene starts are NOT cumulative
durations — each transition pulls the next scene earlier by its own length:

```
d=[150,120,120], t=[18,18]  ->  scene1 0..150, scene2 132..252, scene3 234..354
total = sum(d) - sum(t) = 354        # compare to ffprobe nb_frames -- free oracle
```

Frame 140 therefore belongs to scenes 1 **and** 2. Sampled as "the end of scene
1" it read 18.1 % centre-band ink against 68–80 % elsewhere, and vision reported
two scenes stacked — a correct crossfade 8 frames in, which nearly got "fixed".

So: never assert per-scene content from a frame inside a transition window —
sample from `[start+N, end-N]`. When a probe flags an anomaly, let vision explain
what is on the frame and let the span arithmetic adjudicate whether it is legal,
**before** touching code. Report the adjudication too; silently dropping a scary
intermediate reading looks like hiding it.

**Validate the probe itself.** One RGB sampler emitted 359 labelled rows
(`t=0s … t=358s`) from 6 actually-decoded frames — the labels were fabricated by
enumerating a byte buffer. If row count ≠ expected sample count, discard the run
rather than believing it.

Full recipes, the span calculator, the three-instrument table (container facts →
pixel probe → vision, and what each is blind to) and probe-hygiene checks:
`references/verifying-rendered-video.md`.

## Rule 1g — In a 3D scene, an async asset must exist BEFORE the canvas mounts

`<ThreeCanvas>` (and r3f generally, under Remotion) runs `frameloop="demand"`:
it rasterises **once per Remotion frame**, then stops. Anything that joins the
scene graph after that single draw is in memory, correct, and invisible.

This makes `useGLTF` + `<Suspense fallback={null}>` — the pattern every r3f
tutorial shows — silently wrong here. Measured on a 3.7 MB `DamagedHelmet.glb`
from the verbose render log:

```
"Waiting for R3F to render frame 10" cleared after   94ms   <- the only draw
[FETCH] status=200 bytes=3773916 magic=glTF        at +168ms  <- model arrives
```

The frame rendered, exit code 0, `YMAX=235`, no error in the console — and the
centre of the frame measured **0.0 % ink, 0 distinct colours**. Nothing was there.

Load outside the canvas, hold the render, and gate the canvas on the result:

```tsx
const [handle] = useState(() => delayRender('loading GLB'));
const [scene, setScene] = useState<THREE.Group | null>(null);
useEffect(() => {
  new GLTFLoader().load(url,
    (gltf) => { setScene(gltf.scene); continueRender(handle); },
    undefined,
    (err) => { console.error(err); continueRender(handle); }); // never hang
}, [url, handle]);

if (!scene) return <Background />;   // canvas not mounted yet
return <ThreeCanvas …><primitive object={scene} /></ThreeCanvas>;
```

Same frame after the fix: **80.3 % ink, 598 colours**.

Corollaries, both from the same ordering rule:

- **Don't animate the camera in `useFrame`.** It is not guaranteed to run before
  the demand-mode draw. Derive the transform from `useCurrentFrame()` during
  render and write it via `useThree(s => s.camera)`.
- **Always `continueRender` in the loader's error branch**, or a missing asset
  turns into a 30 s timeout instead of a visibly empty subject.

### Proving a 3D subject is actually on screen

`YMAX` only proves the frame is not black — a text overlay satisfies it. So does
a `gridHelper`: an early "object present" reading here was entirely the floor
grid, and the model was absent. Turn decorative layers **off** and measure the
centre band for (a) ink coverage vs the sampled background and (b) count of
distinct quantised colours. A shaded PBR mesh yields hundreds of colours; flat UI
yields a handful. Probe: `audit/orbit_content_probe.py`.

## Rule 1h — `resolveMotion(frame, from, to)`: from/to is the OUTPUT range

Not a frame window. `resolveMotion(...)(frame, 0, durationInFrames)` returns
`0..120`, so a consumer expecting `0..1` multiplies its effect by up to 120×.

Worse, `MotionConfig.duration` defaults to **24 frames**, and every intensity
preset is shorter than a typical scene (`calm` 60, `normal` 36, `punchy` 24,
`extreme` 18). Past `duration` the resolver returns `to` verbatim — so a camera
move built on it **freezes** partway through the shot and every later frame
shares one bearing. Detected because frames 0 and 60 of a "360° orbit" were
byte-identical PNGs (`sha1sum` on sampled frames: 7 distinct out of 8).

A camera move is not an entrance animation. Force the scene length as its
duration and map to `0..1`, letting an explicit `motion.camera.duration` win:

```tsx
const channel = (motion as any)?.camera;
const cameraMotion = resolveMotion(
  { curve: 'easeInOut', ...channel, duration: channel?.duration ?? durationInFrames },
  fps, 'camera');
const p = cameraMotion(frame, 0, 1);
```

**Hash sampled frames to prove motion.** `sha1sum` across 8 points of an orbit is
a one-line check that catches a frozen animation which every content probe,
`tsc`, and luminance check happily passes.

## Rule 2 — Never invent a package

Plausible-sounding names (`@remotion/effects`, `@remotion/particles`) may not exist.
Verify each one before recommending or installing:

```bash
npm view @remotion/transitions version
```

Batch many checks through `execute_code` with a short per-call timeout — a long
`for` loop of `npm view` in one shell call is slow and will blow a 60s timeout.

## Rule 3 — Enumerate from source, not memory

Get real lists from the API instead of recalling them:

```bash
# every transition presentation
curl -s "https://api.github.com/repos/remotion-dev/remotion/contents/packages/transitions/src/presentations" | grep '"name"'

# an org's repos ranked by stars
curl -s "https://api.github.com/orgs/remotion-dev/repos?per_page=100&sort=stars" \
  | grep -E '"(full_name|stargazers_count|description)"' | paste - - -
```

---

## Start here: official Remotion Agent Skills

Remotion publishes **official skills for AI agents** (`remotion-dev/skills`, ~4.2k ⭐):

```
remotion-best-practices   remotion-captions      remotion-create
remotion-docs             remotion-interactivity remotion-maps
remotion-markup           remotion-multimedia    remotion-render
remotion-saas             remotion-studio        remotion-upgrade
```

`https://github.com/remotion-dev/skills` — also shipped as editor plugins
(`claude-code-plugin`, `codex-plugin`, `cursor-plugin`, `kimi-code-plugin`).
Consult these before improvising Remotion technique.

---

## High-impact upgrade levers (ordered by payoff)

1. **`<Series>` → `<TransitionSeries>`.** A pipeline using plain `<Series>` hard-cuts
   between every scene. `@remotion/transitions` 4.0.507 exports **19** scene
   presentations (`fade`, `slide`, `wipe`, `iris`, `flip`, `clock-wipe`, `zoom-blur`,
   `cross-zoom`, `dreamy-zoom`, `film-burn`, `ripple`, `crosswarp`, `linear-blur`,
   `push-cut`, `book-flip`, `dissolve`, `swap`, `zoom-in-out`, `none`) — the
   `dist/presentations` directory has 20 files but one is not a transition, so read
   `package.json` `exports`, not the folder. Usually the single biggest visual win
   available — but it is **not** a drop-in swap; two traps below bite hard, and both
   let a broken result pass every file-level check:
   - **It shortens the timeline.** Each transition consumes its `timing` frames, so
     a continuous voice-over desyncs and loses its tail unless composition duration
     subtracts the overlap. One shared planner must feed `Root.tsx`, `Main.tsx`, the
     Python spec builder, and any duration QA check.
   - **Presets that leak `zIndex` defeat the crossfade.** The outgoing scene's card
     paints over the incoming one for the whole overlap, so correct wiring still
     looks like a hard cut. Wrap each scene in `isolation: 'isolate'`.
   Full detail, signatures per presentation, and the pixel probe that proves a
   transition composites: `references/transitions-and-motion-layer.md`.
2. **Deterministic fonts.** System fonts like `Impact`/`Arial Black` are not guaranteed
   in headless Chromium and break on Cyrillic. Use `@remotion/google-fonts` and gate the
   first frame on `waitForFonts()`.
3. **Real text fitting.** Replace `len > 60 ? '48px' : '64px'` ladders with
   `measureText()` / `fitText()` from `@remotion/layout-utils`. Length-based guessing
   always breaks on long compound words in non-English text.
4. **Motion blur.** `<Trail>` / `<CameraMotionBlur>` from `@remotion/motion-blur` is the
   cheapest route from "jerky" to "expensive-looking".
5. **Audio-reactive motion.** `useAudioData` + `visualizeAudio` from
   `@remotion/media-utils` so animation breathes with the narration instead of
   running on an independent clock.
6. **Word-level captions.** `@remotion/captions` (`createTikTokStyleCaptions`) fed by
   whisper timestamps, not `durationInFrames / wordCount` linear division.

---

## Diagnosing "every video looks the same"

A frequent complaint on generated-shorts pipelines. It is four separable causes,
and treating it as one ("add more styles") fixes none of them.

**Cause 0 — the presets are unreachable, and the prompt is innocent.** Check this
*first*, because it is invisible from the prompt and it makes work on causes 1–3
worthless. When the user says "the agent only uses 3-4 scenes, update the prompt",
the prompt is a hypothesis, not a diagnosis. In one session it was the *smaller*
half of the problem: three silent data losses in the Python→Zod boundary meant 11
of 17 presets could not be produced no matter what any prompt asked for.

- A snake_case dataclass (`stat_value`) filtered against camelCase input
  (`statValue`) with `k in scene_fields` **discards the key**, then the validator
  blames the caller — `"StatCounter needs one of ['statValue','statLabel']"` for a
  key that was supplied. Perfect trap: the agent complies, gets an error, and falls
  back to the one preset that works.
- Fields that the dataclass simply lacks make presets unreachable regardless of
  input. Five presets here had no `segments` / `messages` / `tokens` / `last4` at all.
- A semantic alias (`accent: "neon"`) that only special-cases one value passes the
  rest through as literal CSS. The browser drops the invalid colour, the scene takes
  its own default, exit code is 0.

Diagnose by **round-tripping one spec per preset through the real graph and
diffing keys in vs keys out** — not by reading the prompt. Anything missing on the
way out is a preset the generator cannot choose. Then fix the boundary, and only
then tune wording. Detail, the fix, and the reachability probe:
`references/preset-reachability-and-field-mapping.md`.

The remaining three are genuine prompt/architecture causes:

1. **Structure is a constant.** One hand-written storyboard shape —
   hook → mechanism → number → comparison → CTA — reused for every topic. Fix:
   a set of *narrative archetypes* (problem/solution, myth-bust, number-story,
   how-it-works, comparison, timeline, mistake-list, build-along) and a variable
   beat count (4–8), not a fixed 5.
2. **Scene choice ignores meaning.** Presets assigned by round-robin rotation
   land a 3D embedding cloud under a line about saving time. Fix: select by the
   *data shape of the beat* — numeric series → bar/line; single number →
   counter/ring; two things → split/versus; ordered stages → flow/steps; code →
   code/terminal/diff — then exclude presets already used in this video.
3. **Genuinely too few scenes.** With ~6 data-bearing presets, a 5–7 scene video
   exhausts the catalogue, so video #2 must repeat video #1. Fix: build a real
   catalogue and, crucially, a **primitive layer** (layout / text / shape / chart
   / three / fx / motion) so a new scene is a 30–40 line composition instead of
   a 164-line monolith that redraws its own background.

Add per-scene modifiers (`theme`, `intensity`, `density`, `entrance`, `exit`,
`transitionIn`, `cameraMove`, `audioReactive`, `emphasis`) so combinatorics carry
variety even on a fixed scene set. Then enforce it: fail the script if one scene
repeats 3+ times, if two consecutive scenes share a category, or if every beat
landed in the text category (a tell that research produced no facts).

Facts feeding scripts should arrive with sources — a copy node must not be free
to invent a number that no research result contains.

## Pitfalls

- **Docs/skills that under-report capability cause the sameness above.** A skill
  listing 5 allowed presets when the schema has 11 hides 6 from every agent that
  reads it. Enumerate from the constant in code, never from prose.
- **`Math.round` on an animated counter silently destroys precision.** `6.8`
  renders as `6 GB`. Derive decimals from the target value instead:
  `Number.isInteger(v) ? 0 : Math.min(2, decimalsOf(v))`.
- **A stray token in JSX fails `tsc` far from its cause.** A word left inside an
  element surfaced as `Property 'literal' does not exist on type 'SVGProps<…>'`
  in an unrelated component. Re-run `npx tsc --noEmit` after every edit round.
- **Slicing a doc by string index silently drops the tail.** Relocating a block
  with `s[:start] + s[end:]` truncated a plan at the end of one section and took
  the whole next section with it; the write reported success. Markdown has no
  compiler, so add one: after restructuring, assert the *structural invariants* —
  every expected heading present, row counts per table, the file still ends on its
  last known line. Recover a lost tail from git (`git show <sha>:<path>`) rather
  than retyping it. Same trap as large `patch` insertions in code.
- **Counting rows by prefix picks up foreign rows.** Inserting a non-scene table
  inside a scene table made a 48-item catalogue count as 50. Scope the count to
  the section (split on the next heading) before believing the number — and if a
  count surprises you, verify before "fixing" it; the document was right and the
  counting was wrong.
- **`read_file` output is line-numbered.** Round-tripping it through an editing
  script writes `12|text` into the file. Strip the `^\d+\|` prefix, then assert it
  is gone afterwards.
- **ffmpeg filter arguments need forward slashes on Windows.** Backslashes inside
  `-filter_complex` / `loudnorm` break the parser even when the path is right:
  `str(p).replace("\\", "/")`.
- **ffmpeg is a native Windows binary and cannot open MSYS paths.** `/c/Users/...`
  fails with "No such file or directory" though the file exists. `cd` first and
  pass relative paths, or use native `C:\...`. Related: Remotion resolves a
  relative `--output` against the **Remotion project dir**, not the shell cwd.
- **Trust `package.json` `exports` over a `dist/` listing** when counting what a
  package provides. `@remotion/transitions` has 20 presentation files but 19 real
  transitions. Same class of error as the section-scoping miscount below.
- **Probing a JS API's members with `Object.keys` can return `[]`.** Remotion's
  `Easing` is a function with non-enumerable statics — enumeration says empty,
  `typeof Easing.bounce` says `function`. Probe members directly before concluding
  a feature is missing, and check a return type before destructuring it
  (`measureSpring()` returns a bare `number`).
- **Two implementations of the same arithmetic will drift.** When frame math lives
  in both Python and TypeScript, don't re-read one against the other — execute the
  real TS via the project's own esbuild and assert equality on shared fixtures,
  pinning expected numbers so a coordinated change still fails.
- **A dependency version warning on every render is a real cost.** It buries
  genuine errors in output. Fix the source (`npm ls <pkg>` to find who pins what),
  and prove the upgrade at *runtime*, not just under `tsc`.
- **Check a helper's signature before passing extra paths.** A two-path
  `master_video_audio(in, out, target_lufs)` called as `(raw, wav, final)` costs
  a whole render cycle before the mistake shows.
- **Config drift.** A `config.yml` claiming `fps: 30` while the code renders 60, or
  naming a TTS provider the pipeline no longer uses, silently misleads every future
  session. Treat the code as truth, then make the config fail fast on mismatch.
- **Skills/docs that outlive the code.** When you find one, flag it; if it is
  user-owned, recommend `hermes curator adopt <name>` rather than trying to patch
  it — autonomous curation writes to user-owned skills are refused.
- **Bilingual caption trap.** With phonetic transliteration for TTS there are two
  strings: *spoken* (`элэлэм`, `гитхаб`) and *displayed* (`LLM`, `GitHub`). Whisper
  transcribes rendered audio, so its timestamps land on the **spoken** form — feeding
  them straight to captions puts `элэлэм` on screen. Map back to the displayed form.
  Same loop doubles as a pronunciation check: diff transcript vs intended script.
- **"PowerPoint 3D".** Extruded flat rectangles with no bevel, depth of field, or real
  lighting read as slides, not motion graphics. Likewise sparse point clouds read as
  scatter plots. If vision analysis says this, the fix is lighting and density.
- **Don't rewrite working QA.** Fail-closed render QA (volume floor check, frame
  luminance stddev, duration tolerance, scene-frames-not-identical) is hard-won and
  rare. Extend it; never trade it for a prettier abstraction.
- **Preserve public API + wire contract.** Keep entrypoint signatures stable and keep
  the Python↔Zod spec contract as the single source of truth (one casing convention,
  one place that emits it).
- **A user's diagnosis in the request is a symptom report, not the cause.** "Update
  the prompt, it only uses 3-4 scenes" names a *fix*; the observation is the 3-4
  scenes. Do the named fix, but probe for the cause first — here the prompt was the
  smaller half and 11 presets were structurally unreachable. Doing only what was
  asked would have shipped a better prompt and the same three scenes.
- **Suspect your measuring code before reporting a defect.** A "missing `text`
  field" was the test script's own print filter excluding `text`; the data had been
  intact the whole time. Before announcing a root cause, check whether the
  instrument is hiding the evidence — and don't state a cause until a probe has
  ruled out the alternatives.
- **Report the split, not the total.** "17 of 104 scenes; audio 112/112; effects
  108/108" is usable; "all done" is not, and gets caught. When a verification step
  could not run at all (no test runner installed, provider down), say which one and
  what you substituted rather than letting the green items imply full coverage.

## Rule 1g — Prove the switch-off, and mutation-test the prover

For a library of composable effects, the cheapest high-value invariant is:
**`intensity = 0` must be byte-identical to no effect at all**, and
`intensity = 1` must differ. Nothing else separates "wired in and reaching the
pixels" from "dead code that compiles" — `tsc`, a screenshot, and a subagent's
summary all look the same either way. Implement it as an early
`return <>{children}</>`; a wrapper div with neutral styles still shifts layout
and breaks the hash.

Two habits make the result trustworthy:

- **Sample inside the effect's active window.** An animation that has finished
  is back at its resting state and reads as broken. Entrance effects: mid-
  animation. Exit effects: after `durationInFrames − EFFECT_FRAMES`. A whole
  family failing at once is the signature of a wrong sample frame or a wrong prop
  key — suspect the harness before the library. An effect failing at *every*
  frame is the opposite: a real wiring or compositing bug.
- **Mutation-test the probe before believing `ALL PASS`.** Inject known defects
  one at a time (silent buffer, over-long clip, clipping, missing fade, unseeded
  RNG) and confirm each is caught, then restore and re-verify. A real run caught
  4 of 5 and exposed one blind spot; `PROBE HAS BLIND SPOTS` is more useful than
  a green tick over 108 items.

**Verify subagent effect work by artifact, never by summary.** Both failure
directions happened in one session: five children reported `completed` having
written nothing (tell: each "finished" in ~4 s, because the configured
delegation model no longer existed upstream), and three wrote 3758 clean-
compiling lines while reporting `sha1=ERROR`/`MISSING` as success. Count the
registry from the source of truth, sum across *all* registry modules, and report
the split honestly — "audio 112/112, effects 108/108, scenes 17/104" beats "all
done". Before a large batch, send one throwaway child and confirm it produced a
file.

Harness and the full trap list: `references/effect-layer-and-probe-hygiene.md`,
`templates/effect_noop_proof.py`.

---

## Phasing an upgrade

Sequence so later work lands on a fixed foundation:

```
foundation (versions, fonts, text fitting, config truth)
  → visual quality (transitions, camera, post-FX, motion blur)
    → style system (palette + typography + motion character + background layer)
      → audio (voices, sound design, audio-reactivity)
      → captions (whisper word timing, caption styles)
        → QA loop (vision scoring, regression gallery)
          → docs/skills LAST — they must describe what already works
```

Document skills last on purpose: written first, they drift from the code immediately.

Acceptance criteria should be *measurable* — vision score improved, no hard cuts,
no text overflow on a long-text render, captions show display form, `npx tsc --noEmit`
clean, QA still fails closed on a deliberately broken spec.

---

## Reference

- `references/remotion-ecosystem-catalogue.md` — verified `@remotion/*` package table,
  all 20 transitions, official agent skills, donor repos by star count, starter
  templates, and copy-paste verification recipes.
- `references/spec-validation-and-agent-guardrails.md` — the silent RENDER ERROR
  class (Zod pre-flight + red-frame probe, with code), the measured
  docs-vs-restriction experiment, and companion pitfalls.
- `references/vertical-scene-design.md` — safe-zone budget, chart readability on a
  phone, the 8-category taxonomy, micro-primitives, the anti-sameness script graph,
  the carriers-not-illustrations doctrine, the unified `motion` contract, and which
  3D model hosts actually allow keyless download.
- `references/transitions-and-motion-layer.md` — the 19 real transitions and their
  three constructor shapes, the `TransitionSeries` timeline math (one planner for
  Root/Main/Python/QA), the z-index stacking-context trap and its fix, the pixel
  probe that proves a transition composites, **probe hygiene: validate the probe
  before trusting the result** (frame-count oracle, error-card detection, A/B
  distance floor, stale-bundle check), verified Remotion API behaviour
  (`Easing`, `spring`, `measureSpring`), the zod3→4 upgrade path, and the
  closed-enum + validator-cwd silent-failure guards.
- Audio cue timing — in the sibling skill `procedural-audio-synthesis`, file
  `references/audio-timeline-and-cue-placement.md`: the transition-overlap trap
  for SFX/music generators (track 2.5 s longer than the picture, last hit 2.57 s
  late) and the `ffprobe` audio-vs-video duration oracle.
- `references/verifying-rendered-video.md` — proving a finished mp4 is correct:  extracting frames from the encoded file (`-vsync 0`), hashing sampled frames to
  prove motion, the `TransitionSeries` span calculator that says which scene a
  frame belongs to, the four-instrument table (container facts / pixel probe /
  vision / semantic pass) with each one's blind spot, probe-hygiene self-checks,
  why a subagent's `YMAX`-based success report is not evidence, and **§10 the
  defect class no numeric probe can see** — the five-defect table (wrong contact
  name, duplicate palette hex, invented `%` suffix, per-frame RNG jitter,
  compounding gap geometry), the five-question pre-delivery checklist, and three
  measurement recipes: reference-free structural metric (for when the corner
  background sample itself moves), integer-shift jitter search scored by
  *direction reversals*, angular run-length sampling of a ring, plus the
  `-ss`-before-`-i` keyframe trap and `-frame_pts 1` for self-labelling frames,
  plus Recipe D — the element-vs-element collision measurement (isolate the
  card, ink-bbox every row, assert `cardRight - inkRight > cardW * 0.05`),
  and **§11 the mid-scene sampling trap** — why default midpoint QA frames make
  progressive-reveal presets look like alpha-channel failures, the sample-point
  table per preset behaviour, the re-sample-near-scene-end recipe, the
  contact-strip one-liner that batches suspects into a single vision call, and
  the `-frames:v 1 -update 1` requirement for single-PNG output.
- `references/effect-layer-and-probe-hygiene.md` — the `intensity=0` byte-exact  no-op contract; the sampling-frame table (entrance/exit/loop active windows)
  that explains why correct effects look broken; the four traps that stall
  subagents (spec-gated probe registration, MSYS `--props` paths, `still`
  exiting 0 on a throw, imported-but-unregistered compositions); how to
  mutation-test a probe; and defects only pixels find — `drop-shadow` glow
  invisible on opaque children, round line caps drawing stubs at zero length,
  `left: cx` centring that overflows by thousands of pixels.
- `references/chart-and-widget-visual-design.md` — the aesthetic defect class: a
  widget that measures exactly right and is still rejected. The five ratio defects
  behind one "ugly" (widget claiming the full safe width at 85 % of frame; stroke at
  30 % of radius turning arcs into capsules; `flex:1` throwing a legend value to the
  far edge, away from its own label; `centerContent:'total'` that can only ever print
  "100%"; a muted metallic brand token used as a data-series colour), each with the
  measured before/after and a working band. Plus ring-measurement hygiene that stops
  you inventing defects — settled-frame check (a transition frame reads 2 698 vs
  126 145 saturated px), radial profile to find the stroke mid-line instead of
  guessing a radius, hue classification that survives a colour grade where a
  brightness threshold splits one arc into 22 phantom fragments, and the `2n−1`
  raw-transition cross-check — and a six-item pre-flight ratio checklist.
- `references/preset-reachability-and-field-mapping.md` — when the user says the generator
  only ever picks 3-4 presets, prove **reachability** before touching the prompt: the
  round-trip probe through the real builder, the case-mismatched filter that discards
  `statValue` and then blames the caller for omitting it, missing dataclass fields,
  half-resolved colour aliases, and duplicated mapping loops that drift. §3a-3c extend it
  with the sequel: fixing the *permission* list (`ALLOWED_PRESETS`) does not fix the
  *selection* lists — a separate hardcoded five still governed rotation — plus why
  `rotation_safe` ≠ "renders my narration" (four presets render convincing fictional demo
  data) and how to verify a TS-registry regex parser against a real node evaluation instead
  of trusting that it "worked".
  agent only uses 3-4 scenes, fix the prompt": the reachability probe that decides
  whether the prompt is even the problem (round-trip one spec per preset through the
  real builder, diff keys in vs keys out), the three silent boundary bugs that made
  11 of 17 presets unreachable (camelCase filtered against a snake_case dataclass so
  the validator blames the caller for a key it supplied; missing dataclass fields;
  a semantic accent alias that resolves only one of its documented values and sends
  the rest to the DOM as invalid CSS), the duplicated mapping loop that strips data
  on a QA repair pass, deriving the text-safe rotation list from the registry instead
  of hand-listing three presets, and how to write the prompt half — plus why a prompt
  example must be executed (a failed `safeParse` in `Root.tsx` does not throw, it
  falls through to a default composition and the only symptom is a wrong duration).
  **§3b: the capability gate** — a second, larger reachability ceiling. A hand-written
  tier allow-list of 11 names against a 26-preset library silently rewrote 15 valid
  presets to a fallback for every low-tier caller; deriving it from the registry index
  (not a directory glob, which also matches effect/transition registries and yields
  134 bogus "presets"); the gate that guarded only the top-level field while ignoring
  storyboard scenes — the recommended path; why an unknown per-scene preset should be
  **dropped** rather than forced to a fallback; and the doc that claimed 5 where the
  code said 11 and the registry said 26.
- `references/style-kit-palette-authoring.md` — the style/theme layer: adding a kit,
  and the three ways it silently does nothing. (1) The layer can be **dead code** —
  eight kits with palette, fonts, motion, backdrop and transition all specified, and
  the only inbound reference was a *type* import, so `style:"retro"` changed nothing;
  grep for the accessor being called, not the file existing. Same check found an
  implemented `dots` backdrop no kit referenced. (2) Kits **sharing a palette render
  pixel-identical** (measured distance 0.0 for two pairs) because presets read their
  highlight from `theme.neon` and series colours from the `neon`/`cyan`/`gold` triad —
  changing only `bg` re-tints nothing; includes the render-every-kit pairwise assertion
  (91 pairs, closest 26.3 after fixing). (3) The **`muted` legibility class**: sub-labels
  at ~0.1×cell need ≥4.5:1 against their own `bg`, and six kits shipped between 2.98 and
  4.13 — one with effectively invisible captions — with the WCAG helper, the six
  before/after hex lifts, and why antialiasing makes the theoretical ratio optimistic.
  Plus §4, three probe failure modes worth generalising: a metric returning the same
  verdict for a known-good control is broken; averaging a whole row folds mesh glow and
  ring arcs into the "background" and under-reported two fine kits (vision disagreed and
  vision was right); averaging a two-hue accent invents a colour present nowhere in the
  frame (lime + magenta → gold).
- `references/nesting-scenes-in-device-frames.md` — one scene rendered inside another's
  sub-viewport (`PhoneMockup` + `innerPreset`, `ScreenRecord`, any device shot). The whole
  defect class comes from one aspect-ratio mismatch: a 9:16 canvas going into a 9:19.5
  screen. Covers why the child must be rendered at **canvas** size and CSS-scaled (laying it
  out at screen size makes every `height * 0.03` font microscopic); the scale-factor
  decision with the arithmetic to run before trusting a source comment — `max(w-ratio,
  h-ratio)` fills the screen but crops **80 px per side, 7.4 % of canvas width**, which ate
  the first and last character of every line (`Разбери код` → `Разбери к`, `Модель` →
  `дель`) while the frame still looked plausible, versus fit-width which leaves 284 px of
  1422 unused; why you should **anchor** the leftover band to the edge the child's UI expects
  rather than stretch the wrapper (stretching does not stretch the child — an intermediate
  attempt passed a 1 px pixel probe and still looked broken); parent effects that destroy the
  nested content (`RackFocus` blurring the chat the scene exists to show); and proving a
  shared-geometry fix is scoped via a centred-child re-render plus **byte-identical** frames
  from unrelated specs. Also §4, the probe-disagreement case worth generalising: a pixel
  metric said "bottom gap = 1 px" and vision said "empty bottom third" and **both were
  correct** — one measured pixel fill, the other semantic UI occupancy; when a number and
  vision disagree, find the quantity that explains both readings instead of picking a winner.
- `references/css-3d-faces-and-relocated-slack.md` — two defects that pass schema
  validation, a still render and a generic vision review, and only surface when someone
  looks at the frame with intent. §1 **relocated slack**: fixing an overflow by changing
  which axis drives a nested scene's scale does not remove the leftover band, it moves it —
  the earlier `PhoneMockup` crop fix (scale by width, anchor bottom) traded 80 px of side
  crop for a **26 % dead band above the chat header**; includes the contiguous-dark-run
  assertion on the *lit screen interior* and the trap where a full-canvas ink bbox reports
  `y 123..1919` and looks like edge cropping because the drop shadow is not black. §2 **CSS
  3D faces detaching**: front/top/right divs rotated inside a `preserve-3d` wrapper whose
  `perspective` lives on the flex row two levels up render as flat rects with detached
  triangular shards and divergent baselines; ask vision specifically about face joins, since
  perfectly legible labels on the same frame are not evidence of chart integrity. §3
  **messenger-mockup fidelity checklist** (sans not serif, bubble tails, timestamps, status
  bar, back arrow, mic-vs-send) plus the authored-data trap where `messages[-1].text ==
  compose` renders the same bubble twice and reads as a preset bug.
- `references/mixing-a-soundtrack-layer.md` — the layer above narration: wiring an audio
  package (ducking mixer, music beds, SFX) that exists in the tree but was never imported —
  `grep -rn "msf.audio" msf/graph/` returned **nothing** while the package shipped 10 beds
  and ~70 SFX, so every video was dry narration over silence. Why the mix must be ONE track
  at the spec root with per-scene urls cleared (a bed restarting on every cut, and a duck
  envelope needing the whole voice track), and why the repair/QA-retry builder must thread
  the root track too or the retry ships mute. The 24 kHz TTS into a 48 kHz mixer that plays
  the voice at **half speed** (assert duration equality, never frame-count equality); cue
  timing that must subtract transition overlap and accept both key spellings; the case where
  my *test* was wrong and the code right (total = last start + its length, not the running
  sum); the degrade-vs-raise policy (typo'd bed name falls back, clipping raises); the
  three-window verification where the **gap between clips** at −44 dB is what proves the bed
  exists; and why measured duck depth (7.39 dB real / 2.65 dB on a short clip) is not the
  configured 6 dB — assert direction, not the constant. Plus: bisect a hanging suite by file
  when `pytest tests/` never prints a summary line.
- `references/research-gated-content-pipelines.md` — making a pipeline research before it  generates, without the gate becoming a no-op. The runner's exit code is **not** a research
  check (`return 0 if summary else 1` → a zero-source run answering from model memory exits
  0), so gate on the source count and **raise**; two independent code-writing subagents
  produced fail-open nodes with zero `raise` statements in a 553-line plan. Prefer reading the
  count from `ldr_last_raw.json` over regexing stdout — but that file is **shared mutable
  state**, so two guards are mandatory: stamp its mtime *before* launching (the runner
  overwrites it only on success, so after a crash a `sources=60` file from the previous run
  sails straight through the gate), and compare the **echoed query** against the asked one
  (concurrent runs share the file). Probe the search backend's `?format=json` endpoint, never
  its root: `/` returns 200 while the JSON endpoint returns 403 when the format is disabled,
  and that 403 *is* the silent-degradation path. Make the node **opt-in** so unrelated renders
  don't newly depend on a search container, which is not the same as fail-open. Machine output
  lives in the **cwd**, never stdout — there is no JSON mode, so `json.loads(stdout)` cannot
  work. Also: subagents invent CLI flags for local runners (`--query`, `--format json` on a
  script whose query is positional), so hand them a verified flag table or read the script
  yourself; carry a `confirmed/disputed/single_source/vendor` confidence field so a report's
  own ⚠ flags are not laundered into clean facts; cache by query hash; a mechanical text
  splitter cannot use a report, so the node needs its own LLM step with a **blunt** grounding
  rule (and a caller-supplied storyboard wins — attach sources as verification instead of
  rewriting it). Finally: the happy path is the one case that cannot regress unnoticed, so the
  file lists the eleven **refusal-path** tests plus the graph-edge assertion, and the
  one-env-var experiment (`…SEARXNG_URL=http://localhost:9`) that proves the gate actually
  fails closed rather than merely claiming to.
- `templates/effect_noop_proof.py` — runnable no-op prover. Renders a bare
  control plus each effect at intensity 0 and 1, byte-compares sha1s, samples
  each family inside its active window, and exits non-zero on failure.
- `scripts/verify_render.py` — runnable QA gate for a finished mp4:
  `spans` prints scene spans, overlap windows and safe sample frames;
  `check` verifies the frame-count oracle, detects the subject per scene outside
  overlaps, and hashes frames to prove motion survived the encode; `probe` scores
  loose PNGs. Non-zero exit on failure.
- `scripts/agent_spec_probe.py` — runnable A/B harness: same tasks and models,
  two briefs, scored against the real schema plus semantic checks. Use it to
  decide guardrails from evidence instead of intuition.
- `scripts/sync_model_icons.mjs` — runnable asset sync: copies a curated set of
  `@lobehub/icons-static-svg` brand marks into `public/model-icons/`, rewriting
  `currentColor` to white and `1em` to real pixels so the SVGs actually work
  inside an `<img>`. Exits non-zero on a missing vendor icon.
- `scripts/stress_presets.mjs` — drop-in `remotion/scripts/stress.mjs`: renders a
  JSON list of hostile-data cases (one scene each, wrapped into a full spec) to
  PNGs, one attributable log line per case. Use it to review a preset with the
  strings the pipeline really emits instead of the demo strings; frame defaults to
  90 % of the duration, and beat-divided presets need one case per beat.
- `references/reveal-pacing-and-dwell-time.md` — **duration defects, which no still
  frame can express.** Reveal schedules written as `durationInFrames * k` give the
  viewer a fraction of the *scene* to read rather than time proportional to the
  *text*, and in a cascade the last item — the newest event, the lowest-ranked row,
  the payload — always gets the worst deal: measured 0.30s / 0.18s / 0.38s of dwell
  on DefinitionCard / TimelineReveal / Leaderboard at 180 frames, all passing every
  layout check, tsc, and vision review. Covers the `settleBy`/`paceSequence` fix and
  why subtracting only the dwell still under-delivers (asking 1.0s measured 0.77s —
  the animation's own tail); why the contract must be asserted at 90/180/600/1800
  frames, since a helper tuned at one duration is the same bug in disguise; the
  frame-sequence measurement rig (`--sequence --scale=0.5`, one bundle, and the JPEG
  filename that reports `0 frames`); the settle-detection trap where an absolute
  motion threshold graded ProgressPath's perpetual dot pulse as "never settles,
  dwell 0.00s" and the peak-relative floor that fixes it; splitting the verdict into
  `REVEALS_TOO_LATE` (preset bug) vs `SCENE_TOO_SHORT_FOR_TEXT` (script bug, warn
  never block); and keeping the three graders — pacing.ts, timing_probe.py, spec.py —
  asserted in sync. §3 adds the adjacent alpha-suffix defect: `${theme.muted}33` on a
  dot with a connector track painted *behind* it let the track show through as a
  stripe inside every circle (interior held 4 distinct colours where it should hold
  1), fixed with an opaque `blend()`. §4: a vertical budget that divides the column
  by row count and *then* adds a gap between every pair (4 × 26px from nowhere,
  overflowing the reserved bottom band), plus the title whose line count must be
  measured rather than assumed to be 1. Also: the second-order probe trap where the
  "perpetual decorative animation" carve-out (added so ScoreHud's frame-reseeded
  combo sparks stop reading as "never settles") was thresholded at `last/first > 0.5`
  and thereby classified a real score-roll defect (ratio 0.54, cv 1.37) as shimmer,
  silently UPGRADING the verdict to OK — fixed by requiring both `ratio >= 0.8` and
  `cv < 0.8`, and by the standing rule that any probe exclusion must be re-graded
  against the retained pre-fix renders so known failures still fail; the clock-semantics
  fix (`timeLeft * (1 - sceneProgress)` compressed a 60s round into a 3s shot and always
  landed on `00`, which reads as *time up* — tick real time and freeze at `settleBy()`,
  remapping the clock once rather than rescaling each animation); and the eight presets
  fixed, split into cascades (divide `settleBy()` by item count *plus* the trailing units
  their own entrance needs) versus named-phase choreographies (rescale only the base `D`).
- `scripts/timing_probe.py` — runnable per-band appear/settle/dwell probe for a rendered
  frame sequence, with the peak-relative settle floor and the perpetual-animation
  discriminator already tuned. Pair with a `remotion render --sequence --scale=0.5` pass.
- `references/measured-text-geometry.md` — the umbrella rule for the single most
  recurrent preset defect: **any dimension that must contain spec-supplied text is
  derived from `measureText`/`fitText`, never from `text.length`, a fixed
  `height * k`, or a share of the container.** Four failure shapes, each needing a
  different assertion: the character-count ladder that sized `Квантизация` at 118 px
  when 11 Cyrillic glyphs at weight 900 need ~1090 (rendered `Квантизаци`, final
  letter outside the canvas — plus decorations inheriting the same proxy, and the
  reminder to subtract sibling widths before sizing against `safe.width`);
  `fitOneLine` clamping to `minFontSize` rather than promising a fit, whose probe
  signature is *several rows' ink ending at the identical x*; `ceil(width / colW)`
  line-count estimates being wrong in **both** directions because CSS breaks on word
  boundaries, and `measureText` defaulting to normal weight so 600–800 labels
  under-measure; and the percentage split that cannot satisfy two hard minimums, where
  the fix is to spend the unused vertical axis. §5 adds the vertical-budget twin:
  absolutely-positioned rows grow *down*, `alignItems: 'center'` does not centre a row
  on its dot (and makes dot spacing depend on each row's wrapped text — measured
  237/261/285 px at constant `stepSpacing`), and safe-area overflow is invisible to
  clipping/red-card/byte checks so it needs its own three-line `y_max <= 1540`
  assertion. §6 lists the probe-reading traps that produced wrong diagnoses:
  accent-tinted leader rows fooling green-channel probes, a restricted probe window
  measuring itself, `measure()` advance-width slack ≠ visual margin, and vision plus a
  pixel probe both being right about different things.
- `references/text-fitting-and-beat-sampling.md` — the two-defect class where geometry is
  computed from a fraction of the canvas rather than from the content that must fit inside
  it, plus the sampling blind spot that hides it. §1: a hero word sized at `height * 0.14`
  fits ~6 wide caps, so `ДОГНАЛИ` spanned the full 1080 px frame and rendered `ОГНАЛ` for its
  entire 25 %-of-scene beat; includes the reference-free assertion (ink bbox touching *both*
  edges), the `fitOneLine` fix applied as a `Math.min` ceiling-reducer so short words keep the
  designed size, and the `grep -rn "Math.round(height \* 0\.1[0-9])"` audit with the rule that
  separates author-controlled geometry (fine) from spec-supplied text (never). §2: presets
  that **subdivide duration into beats** hold different content per beat, so the house habit
  of one still at 72 % of the scene lands on a countdown digit and never samples the payoff —
  the defect survived a 15-frame still pass *and* a per-scene vision review and only surfaced
  on full mp4 render; gives the per-beat frame derivation, the cheap 30/72/92 % fallback, the
  list of fields that imply beats, and the rule to pull verification frames from the encoded
  file rather than a fresh `still`. §3: why cropping ships and letterboxing gets fixed — any
  geometry whose failure mode is silent truncation needs an explicit assertion, because no
  global probe (safe area, red card, byte equality, luminance) measures element-vs-container
  fit.
