---
name: spec-driven-video-pipelines
description: "Use when a backend spec drives a JS video renderer."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [video, remotion, pipeline, spec, qa, render, motion-graphics, verification]
    related_skills: [qwen3-tts]
---

# Spec-Driven Video Pipelines

Applies to any pipeline shaped like **backend builds a spec → renderer consumes it →
automated QA judges the output**: Remotion/React, Three.js + Playwright, headless
browser capture, ffmpeg compositors. The recurring hazard in this architecture is not
crashes — it is **plausible-looking output that silently ignored the input**.

Companion skill for the narration half: `qwen3-tts` (voice cloning, reference vetting,
Russian pronunciation and stress).

## The core failure mode: silent fallback

A renderer component written like this is the single most expensive mistake in the class:

```tsx
const title = props.title || 'HERO KINETIC';   // ← never do this
```

When the spec fails to arrive, this renders a polished demo placeholder. The video looks
fine. QA passes. Nobody notices the pipeline is completely disconnected from its input —
in one observed case, for an entire release.

**Rule: every missing-data path must render a loud sentinel**, e.g.
`⚠ NO TITLE IN SPEC`, a red card, an obviously-broken swatch. A plumbing bug must fail
visibly rather than masquerade as content. Never put a `.default()` on the `scenes` array
in the validation schema, for the same reason.

The same applies to chrome: hardcoded badges/labels baked into a component (`MSF 3D
SCENE`, `LIVE METRIC`, `'METRIC'`) leak untranslated boilerplate into a localized video.
Make every badge opt-in from the spec.

## Wire contract hygiene

1. **Case convention & field name parity.** Backend `snake_case` reaching a TypeScript renderer that expects
   `camelCase` produces empty props with **no error**. Convert explicitly at one boundary
   (a `to_dict()` on the scene dataclass) and treat the schema file as the single source
   of truth. Also guard against internal key mismatches across pipeline nodes (e.g. state node writing `audio_file` while builder node reads `audio_url`), which silently forces hardcoded fallbacks or drops asset URLs.
2. **Absolute paths for props.** A relative props path leaves `getInputProps()` returning
   `{}`.
3. **Missing audio props in manual CLI renders.** Invoking `remotion render` directly with custom `--props=spec.json` where `audioUrl` / `audio_url` is missing from scenes will cause React to skip rendering `<Audio />` elements without error — producing a zero-volume MP4 render.
4. **Fail closed.** Validate the spec in the backend before invoking the renderer: no
   scenes, an unknown preset name, or a preset missing required data should raise, not
   render. A red error screen beats a pretty wrong video; an exception beats both.
5. **One FPS end to end.** Scene durations are computed in frames, so a TTS/spec module
   assuming 30 FPS against a 60 FPS render desyncs audio and picture by 2x. Fix stale FPS
   values in the docs too, or the next agent reintroduces them.

## Forward the full scene surface

A preset is only reachable if the spec builder forwards the fields it consumes. If the
builder copies only `title/subtitle/text`, every data-driven preset (counters, card decks,
diagrams, code reveals, 3D scenes) becomes **unreachable through the pipeline** — each
renders its own missing-data placeholder, so the failure reads as cosmetic rather than
structural.

When adding a preset, touch all four places:
1. Scene model in the backend.
2. Validation schema in the renderer.
3. The spec-builder node (forward the new fields).
4. The retry/repair node — **mirror the forwarding there too**, or a repair pass silently
   strips the storyboard it is repairing.

A repair step that downgrades a failing scene to a plain text preset must **skip
data-driven scenes**: a headline preset cannot display a numeric stat.

Auto-rotating presets across scenes is the right default (it stops a five-scene short from
being five identical cards), but rotation may only choose **text-safe** presets. Data
presets need an explicit storyboard entry naming the preset and supplying its data.

## Two entry points will diverge — and the fast one loses features

Pipelines in this class grow a second, faster way in: the full orchestrator (graph, CLI
command, `create_video()`) *and* a bare `render --props=spec.json` for iterating on
visuals. The bare path skips every backend node, so anything a node *injects* — audio
URLs, computed durations, resolved accents, asset copies into the static dir — is simply
absent, and the renderer's conditional mounts (`{x && <Component/>}`) silently render
nothing.

Observed: three finished videos delivered with a full-length AAC track at **−91 dB**
because the hand-written specs had no `audioUrl` and the synthesis node never ran. Every
structural check passed; only `volumedetect` caught it.

Do one of these, not neither:
- Make the fast path a thin wrapper that still runs the injection nodes on a loaded spec, or
- Add a spec-completeness assertion (does every scene carry the fields the nodes would have
  injected?) that runs on both paths, or
- Delete the fast path.

The failure is guaranteed to recur otherwise, because the fast path is the one you reach
for while iterating and the one whose output ends up shipped.

## A freshness/research stage must fail closed

When a stage exists to keep generated content current (a research runner, a price fetch, a
model-registry pull), its failure mode is the whole reason it exists. Two traps:

- **Exit code 0 ≠ the work happened.** A research runner returning `0 if summary else 1`
  exits successfully when its search backend was down: the LLM answered from memory,
  `sources=0`, and confident stale facts flow downstream. Assert on the *substantive*
  signal (source count, row count, freshness timestamp), not on the exit code.
- **`except Exception: continue with empty` defeats the stage.** Swallowing the error
  converts a hard failure into silently unresearched output that looks identical to
  success. If freshness is mandatory, raise.

Also verify the *consumer* can use what the stage produces: wiring a 250-line research
report into a mechanical regex sentence-splitter yields scenes that read like markdown
fragments. Facts → script needs an LLM step or a hand-off to the calling agent; a
splitter downstream will not "make use of the context".

Preserve any confidence grading the source attached (`single source`, `vendor-reported`,
`contradicted`) as a field on each fact, and generate only from corroborated ones. Missing
data is itself a finding — treat a gap as a follow-up query, never as licence to fill it
in plausibly.

## Automated QA has real blind spots

A size / duration / loudness / luminance / diversity suite passed cleanly on both of these:
- a video that had collapsed into **one 13-second scene**;
- a five-scene video where **every scene used an identical template**.

Those checks catch broken renders, silent audio and duration drift. They do **not** catch
weak pacing or visual monotony. Treat QA green as necessary, not sufficient, and keep
frame-level vision inspection in the loop.

QA signals that do earn their place:
- `ffprobe` for dimensions, `r_frame_rate`, sample rate, real vs. expected duration.
- `ffmpeg -af volumedetect` for mean/peak volume — catches silent or clipped audio.
- Per-scene luminance stddev: a flat spread across scenes hints that preset variety
  collapsed.
- Distinct-preset count vs. scene count.

**`ffprobe` cannot detect silence — it reports the container, not the signal.** A track can
be `aac / 48000 Hz / stereo / full duration` and be all-zero PCM. Use
`ffmpeg -hide_banner -i out.mp4 -map a:0 -af volumedetect -f null /dev/null`: the signature
is `mean_volume == max_volume == -91.0 dB` (16-bit silence floor), against ≈ −17/−3 dB for
real speech. The `-map a:0` matters — without it `volumedetect` may attach elsewhere and
print nothing, and an empty grep reads as "no problem found". Note also that a whole-file
mean passes when only one scene of five is voiced, so measure per scene span.

**Confirm any vision defect at full resolution.** A contact-sheet strip with frames
downscaled to ~300 px wide produced a false positive for clipped text; the original
1080x1920 frame showed the text well inside its margin. Strips for overview, full-res
frame before acting on a defect.

## Output geometry is a spec field, not a constant

Hardcoding 1080x1920 blocks horizontal and square delivery. Carry `width`, `height` and
`safeMargin` in the spec, and have presets branch on `height >= width`. See
`references/universal_format_and_preset_architecture.md` for the format table, the
branching pattern, and a preset taxonomy.

## Reporting discipline

Report only what a tool returned **in this session**. Do not state a root cause, a
file/line, a duration, or a "fixed" verdict ahead of the evidence. Long renders and model
loads (a TTS model load alone is ~70s; a full A/B can run many minutes) create pressure to
guess, and guessing forces retractions that cost far more trust than the wait. If a
background job is still running, say so plainly and deliver the real numbers when it
lands. Start long jobs in the background and do other useful work rather than narrating an
outcome you do not have yet.

## Platform notes

- **ffmpeg/ffprobe on Windows are native builds** — pass `C:\...` paths, never MSYS-style
  `/c/Users/...` (fails with `Error opening input: No such file or directory`).
- **FFmpeg filter path escaping** — when passing file paths inside FFmpeg filter strings
  (e.g. `-af loudnorm=...`), backslashes in Windows paths like `output\file.mp4` break
  the FFmpeg filter parser with `Undefined constant or missing '('`. Always convert
  backslashes to forward slashes (`/`) in path strings inside FFmpeg filters.
- **Never split `path:label` pairs with `${pair%%:*}` in bash** — the drive-letter colon
  truncates the path to `C`. Use a delimiter that cannot occur in a path (`|`), or drive
  batch ffmpeg work from Python `subprocess.run([...])` with raw strings.
- **React version pins the 3D stack.** `@react-three/fiber@9` requires React 19; on React
  18 install `@react-three/fiber@^8.17.10`. Match `@remotion/three` to the *exact* Remotion version
  (`npm ls remotion`) rather than taking `@latest`.
- **Deterministic 3D rendering for Remotion.** Remotion renders frames non-sequentially
  across parallel workers. In Three.js / R3F scenes:
  - Do NOT accumulate frame deltas in state inside `useFrame` (desyncs workers). Animate
    camera, rotations, and positions strictly as a function of `frame` / `useCurrentFrame()`.
  - Use deterministic pseudo-random seeds (e.g. Mulberry32 / LCG) for particle clouds or
    mesh layouts so every render worker yields identical geometry.
- Mastering cannot write over its own input — raw and final files need distinct paths.
- `loudnorm` upsamples internally; pin `-ar 48000` on the output.

## Reference files

- `references/universal_format_and_preset_architecture.md`: format table
  (vertical/horizontal/square/cinema), the `height >= width` branching pattern, safe-area
  handling, and a text-safe vs. data-driven preset taxonomy.
