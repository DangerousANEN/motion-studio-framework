# Remotion Ecosystem Catalogue (verified)

Condensed knowledge bank for building 9:16 shorts with **Remotion** (React/TS renderer).
Every entry was verified in-session via `npm view` or the GitHub API — **not** recalled
from memory. Versions and star counts drift; re-verify before quoting them to a user.

Baseline when captured: Remotion `4.0.507` latest on npm, React 18, Node v24.

---

## 1. Official `@remotion/*` packages — all verified to exist

Confirmed on npm at `4.0.507` via `npm view @remotion/<name> version`:

| Package | What it does | Why it matters for shorts |
|---|---|---|
| `@remotion/transitions` | 20 scene-transition presentations + timings | Kills hard cuts between scenes |
| `@remotion/captions` | `createTikTokStyleCaptions`, caption page model | Word-by-word karaoke subtitles |
| `@remotion/animation-utils` | `makeTransform`, interpolate helpers | Cleaner transform composition |
| `@remotion/motion-blur` | `<Trail>`, `<CameraMotionBlur>` | Biggest single "expensive motion" lever |
| `@remotion/shapes` | Parametric SVG shapes | Badges, bursts, arrows |
| `@remotion/paths` | SVG path morph / measure / evolve | Draw-on paths, morphing icons |
| `@remotion/noise` | Simplex / Perlin noise | Organic wobble, particle fields, grain |
| `@remotion/layout-utils` | `measureText()`, `fitText()` | **Correct fix for text overflow** |
| `@remotion/google-fonts` | Typed per-font loaders + `waitForFonts()` | Deterministic fonts in headless render |
| `@remotion/fonts` | Generic local font loading | Custom / brand fonts |
| `@remotion/lottie` | Lottie playback | After Effects micro-animations |
| `@remotion/gif` | GIF as frame-accurate source | Reaction / meme inserts |
| `@remotion/skia` | React Native Skia integration | GPU 2D effects, shaders |
| `@remotion/rive` | Rive state-machine animations | Interactive-style vector motion |
| `@remotion/media-utils` | `useAudioData`, `visualizeAudio`, `getAudioDurationInSeconds` | **Audio-reactive animation** |
| `@remotion/install-whisper-cpp` | Installs + runs whisper.cpp | Word-level timestamps |
| `@remotion/whisper-web` | Whisper in the browser | Same, no native install |
| `@remotion/three` | React Three Fiber in Remotion | 3D scenes |
| `@remotion/tailwind-v4` | Tailwind v4 support | Utility-class styling |
| `@remotion/enable-scss` | SCSS support | Styling |
| `@remotion/zod-types` | Zod types for props | Typed spec contract |
| `@remotion/player` | Embeddable player | Preview UI |

**Pitfall:** plausible-sounding names (`@remotion/effects`, `@remotion/particles`) were
*not* confirmed to exist. Always `npm view` before recommending or installing a package.

---

## 2. `@remotion/transitions` — all 20 presentations

Read from `remotion-dev/remotion/packages/transitions/src/presentations`:

```
book-flip    clock-wipe   cross-zoom   crosswarp    dissolve
dreamy-zoom  fade         film-burn    flip         iris
linear-blur  none         push-cut     ripple       slide
swap         wipe         zoom-blur    zoom-in-out
```

Use via `<TransitionSeries>` with `springTiming` / `linearTiming`.
Swapping a plain `<Series>` for `<TransitionSeries>` is usually the highest
visual-impact single change in an existing pipeline.

---

## 3. Official Agent Skills — `remotion-dev/skills` (~4.2k ⭐)

Remotion ships **official skills for AI agents** — the highest-leverage discovery for
any agent doing Remotion work. Prefer these over improvising:

```
remotion-best-practices   remotion-captions      remotion-create
remotion-docs             remotion-interactivity remotion-maps
remotion-markup           remotion-multimedia    remotion-render
remotion-saas             remotion-studio        remotion-upgrade
```

Repo: `https://github.com/remotion-dev/skills`
Also shipped as editor plugins: `claude-code-plugin`, `codex-plugin`, `cursor-plugin`,
`kimi-code-plugin`.

---

## 4. Donor repos worth copying from (GitHub API, by stars)

| Repo | ⭐ | Take |
|---|---|---|
| `remotion-dev/template-tiktok` | ~273 | Reference word-by-word captions via Whisper.cpp |
| `template-prompt-to-motion-graphics-saas` | ~250 | Prompt → motion-graphics architecture |
| `remotion-dev/template-code-hike` | ~215 | Beautiful code animations |
| `remotion-dev/html-in-canvas` | ~194 | Render HTML into canvas / 3D |
| `remotion-dev/template-prompt-to-video` | ~131 | Story from images + voiceover |
| `remotion-dev/recorder` / `our-recorder` | ~46 / ~22 | Real production pipeline for social video |
| `remotion-dev/template-music-visualization` | ~24 | Audio-reactive visualisation |
| `remotion-dev/transitions-video` | ~22 | Demo of every transition |
| `remotion-dev/shorts-customizer` | ~14 | Shorts customisation |
| `remotion-dev/light-leak-example` | ~7 | Light leaks — cheap, high-impact "juice" |
| `remotion-dev/animated-captions` | ~5 | Caption styles: `AnimatedBackground`, `ColoredWords`, `ScalingWords` |
| `remotion-dev/gpu-scene` | ~5 | Verify a render is actually GPU-accelerated |

---

## 5. Official starter templates (`remotion.dev/templates`)

Free: Blank, Hello World, Next.js (App dir / Vercel Sandbox / No Tailwind / Pages dir),
Recorder, Prompt to Motion Graphics SaaS, JavaScript, Render Server (Express.js),
Electron, React Router 7, **3D**, Stills, **Audiogram**, **Music Visualization**,
Prompt to Video, **Skia**, Overlay, **Code Hike**, Stargazer, **TikTok**.

Paid: Editor Starter, Watercolor Map, `<Timeline />`.

Scaffold with `npx create-video@latest`.

---

## 6. The bilingual caption trap (non-English narration)

When narration uses phonetic transliteration for TTS there are **two distinct strings**,
and conflating them produces broken on-screen text:

- **Spoken text** — what the TTS model consumes: `элэлэм`, `гитхаб`, `эфпиэс`
- **Displayed text** — what the viewer must read: `LLM`, `GitHub`, `FPS`

Whisper transcribes the *rendered audio*, so its word-level timestamps land on the
**spoken** form. Feeding them straight into captions puts `элэлэм` on screen.
A mapping back to the displayed form is mandatory.

Bonus use of the same loop: diff Whisper's transcript against the intended script to
auto-detect mispronunciations and grow the pronunciation lexicon.

---

## 7. Fast verification recipes

```bash
# Does a package actually exist?
npm view @remotion/transitions version

# Installed vs latest
node -p "require('./node_modules/remotion/package.json').version"

# Which @remotion/* packages are actually installed
ls node_modules/@remotion/

# Enumerate transitions / caption styles straight from source
curl -s "https://api.github.com/repos/remotion-dev/remotion/contents/packages/transitions/src/presentations" | grep '"name"'

# Rank an org's repos by stars
curl -s "https://api.github.com/orgs/remotion-dev/repos?per_page=100&sort=stars" \
  | grep -E '"(full_name|stargazers_count)"' | paste - -
```

Note: `npm view` across many packages in one shell loop is slow and can blow a 60s
timeout. Batch it through `execute_code` with a per-call timeout instead of one long
`for` loop.
