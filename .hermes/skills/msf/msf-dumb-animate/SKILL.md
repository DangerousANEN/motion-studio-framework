---
name: msf-dumb-animate
description: Use when a dumb agent (level <= 2) wants to generate motion video. Enforces the preset-only LangGraph pipeline; no custom React allowed.
---
# MSF Dumb Animate — Preset-Only Video Generation

The ONLY way a "dumb" agent (level ≤ 2) generates motion graphics. You do NOT write
React. You do NOT hand-write the spec JSON. You call the graph and let it do the work.

## Golden rule
Never build `video-spec.json` by hand. `msf.graph.video_graph` owns the spec: it splits
the script, synthesizes per-scene audio, measures real WAV durations, converts to frames,
validates, renders, and runs Vision QA. Hand-writing the spec skips all of that.

## Input
- `text` (str, required) — the voiceover/narration script (Russian is fine)
- `storyboard` (list[dict], optional) — **the way to get a good video.** See below.
- `preset` (str, optional) — starting preset when you pass only `text`
- `accent` (str, optional) — `gold` | `neon` | `cyan`. Default `gold`.
- `reference_audio` (str, optional) — voice-clone reference WAV
- `output_path` (str, optional) — where the final MP4 lands

## READ THIS FIRST: text-only input produces a mediocre video

Passing just `text` gets you the automatic rotation, which cycles the five
presets that plain narration can drive: `HeroKinetic → TypewriterSub →
QuoteCard → GridGridFloor → TokenCloud3D`. All five are typography or abstract
3D. None of them show a chat, a chart, a card, a code block or a comparison —
because narration text alone cannot express `segments`, `cards`, or `messages`.

That is why generated videos kept looking the same: **the interesting 12
presets are only reachable through a `storyboard`.** Rotation is the floor, not
the target.

A short built from 5 title cards is a short nobody watches to the end. Build a
storyboard. It costs you one dict per scene.

## Storyboard: how to actually use the library

Pass a list of scene dicts. Each scene needs `text` (its narration) and names
its own `preset` plus that preset's data. Scenes without a `preset` fall back to
rotation, so you can mix.

```python
result = app.invoke({
    "storyboard": [
        {"text": "Смотри, что умеет новая модель.",
         "preset": "HeroKinetic", "title": "GPT-5 вышла"},

        {"text": "Её спросили — и она ответила за секунду.",
         "preset": "AiChatStream",
         "messages": [{"from": "user", "text": "Объясни квантовую запутанность"}],
         "response": "Две частицы связаны так, что измерение одной мгновенно определяет состояние другой."},

        {"text": "По бенчмаркам — рост в полтора раза.",
         "preset": "StatCounter",
         "statValue": 94.2, "statSuffix": " %", "statLabel": "MMLU"},

        {"text": "Вот из чего состоит её обучение.",
         "preset": "DonutFill",
         "segments": [{"label": "Текст", "value": 62},
                      {"label": "Код", "value": 24},
                      {"label": "Изображения", "value": 14}]},

        {"text": "Раньше это занимало часы. Теперь — минуты.",
         "preset": "CompareSplit",
         "cards": [{"title": "10 часов", "description": "вручную", "tag": "БЫЛО"},
                   {"title": "4 минуты", "description": "с моделью", "tag": "СТАЛО"}]},

        {"text": "Подпишись, чтобы не пропустить разбор.",
         "preset": "QuoteCard",
         "text_quote_note": "QuoteCard uses the scene's own `text` as the quote"},
    ],
})
```

## Pipeline (the only supported entry point)

```python
import sys
sys.path.insert(0, r"C:\Users\ANEN\motion-studio-framework")
from msf.graph.video_graph import build_msf_graph

app = build_msf_graph()
result = app.invoke({
    "text": "Открытые модели догнали закрытые. Смотри сам.",
    "accent": "neon",
    "agent_level": 1,                     # 1-2 = dumb: presets only
    "reference_audio": r"C:\Users\ANEN\qwen3_1.7B_clone_test.wav",
    "output_path": r"C:\Users\ANEN\motion-studio-framework\output\my_video.mp4",

    # 6 scenes, 6 DIFFERENT presets. This is the shape to copy.
    "storyboard": [
        {"preset": "HeroKinetic",   "title": "Открытые\nдогнали",  "subtitle": "и стоят ноль",
         "badge": "2026", "text": "Открытые модели догнали закрытые."},

        {"preset": "AiChatStream",  "title": "Спроси сам",
         "messages": [{"from": "user", "text": "Объясни attention в двух строках"}],
         "response": "Каждый токен смотрит на все остальные и решает, что важно.",
         "text": "Отвечают не хуже платных."},

        {"preset": "StatCounter",   "statValue": 671, "statSuffix": "B",
         "statLabel": "параметров в открытом весе", "text": "Шестьсот семьдесят один миллиард параметров."},

        {"preset": "DonutFill",     "title": "Что внутри",
         "segments": [{"label": "Текст", "value": 62}, {"label": "Код", "value": 24},
                      {"label": "Изображения", "value": 14}],
         "text": "Больше половины обучения — обычный текст."},

        {"preset": "CompareSplit",  "title": "Цена вопроса",
         "cards": [{"title": "Закрытая", "value": "$20/мес"}, {"title": "Открытая", "value": "$0"}],
         "text": "Разница в цене — двадцать долларов против нуля."},

        {"preset": "QuoteCard",     "text": "Лучшая модель — та, которую можно запустить самому.",
         "author": "LLM Hubs"},
    ],
})

print(result["final_mp4"])       # mastered MP4, 1080x1920, 60 fps, 48 kHz audio
print(result["qa_passed"])       # True only if Vision QA accepted the frames
print(result["qa_report"])       # per-frame diagnostics
```

Graph order: `gate_check → script_split → voice_synthesis → build_spec → render → vision_qa → master_audio`.

When `storyboard` is present, `script_split` uses each scene's `text` for
timing and skips its own preset rotation entirely. `text` is REQUIRED on every
storyboard scene — the graph raises `storyboard[i] has no 'text'` without it.

### Field types are enforced
`statValue`, `balance`, and `segments[].value` must be **numbers, not strings**.
The Zod schema rejects `"671"` and the composition silently falls back to a
120-frame default spec — the render "succeeds" and produces the wrong video.

## Verify before handing off
`qa_passed: True` is not sufficient — it does not check preset variety.

The graph exposes the built spec as a FILE PATH (`spec_path`), not as a dict.
There is no `result["spec"]` key; reading one raises KeyError.

```python
import json
spec = json.load(open(result["spec_path"], encoding="utf-8"))
used = [s["preset"] for s in spec["scenes"]]
assert len(set(used)) >= 4, f"only {len(set(used))} distinct presets: {used}"
assert not any(a == b for a, b in zip(used, used[1:])), f"adjacent repeat: {used}"
data_ui = {"StatCounter","DonutFill","CompareSplit","FlowDiagram","SwipePanels",
           "CodeReveal","TgChat","AiChatStream","CryptoWallet","BankCard","LayerStack3D",
           "RingStats","Bars3D","ImageShowcase","VideoEmbed","ScreenRecord",
           "VoiceMemo","PhoneMockup","MusicPlayer","VinylRecord"}
assert data_ui & set(used), f"all-typography video: {used}"
```

## Style kits — one word that recolours the whole video

`style` on the spec (or on a single scene) selects a visual language: palette +
fonts + motion character + backdrop texture. Eight kits, each with its own
palette — verified distinct by rendering the same scene through all eight and
measuring the pixels.

| Kit | Look | Use for |
|---|---|---|
| `pop` | neo-brutalism, hard shadows, neon green/cyan on grid | default, high-energy |
| `editorial` | warm off-white on charcoal, plain backdrop, calm motion | explainers, analysis |
| `glass` | frosted panels over a luminous gradient mesh | product, premium |
| `blueprint` | cyan technical grid | architecture, diagrams |
| `neon` | saturated coral/pink glow on noise | releases, announcements |
| `news` | red/white broadcast urgency on a dot matrix | breaking-news beats |
| `retro` | VHS pink/cyan, scanlines, chromatic fringing | nostalgia, lo-fi |
| `clean` | pure white on black, zero decoration | dense information |

A scene may override the video's kit: mix an `editorial` explainer with one
`neon` announcement beat. `accentColor` overrides the kit's accent on top.

## Overlays — HUD on top of ANY scene

`scene.overlays[]` draws elements above the scene content. They compose with
every preset, which is the point: a countdown over a screen recording, a payment
toast over a chart.

```jsonc
"overlays": [
  {"type": "timer", "seconds": 10, "at": 0.05, "label": "ОСТАЛОСЬ"},
  {"type": "notification", "appName": "Telegram", "title": "Аня",
   "text": "Смотри, уже работает!", "at": 0.35, "hold": 2.5},
  {"type": "money", "amount": 12480, "currency": "₽", "sender": "Зачисление", "at": 0.4}
]
```
`at` is 0..1 scene progress, `hold` is seconds. `position` accepts the four
corners plus `center`/`top`/`bottom`. The timer turns red in its last 3 seconds.

## The full library — 26 presets

Rotation-safe presets (marked ROT) run on narration alone. Everything else needs
you to supply its data in a storyboard scene — and those are the ones that make
a video worth watching.

### Typography & narrative — the connective tissue
| Preset | What the viewer sees | Required data |
|---|---|---|
| `HeroKinetic` ROT | Big bold title slamming in. Hooks and channel intros | `title` |
| `TypewriterSub` ROT | Text typing out word by word | `text` |
| `QuoteCard` ROT | A quote with attribution | `text`, optional `author`+`role` |
| `GridGridFloor` ROT | Neo-Brutalist 3D grid floor behind a title | `title` |

### Data — the payoff shots
| Preset | What the viewer sees | Required data |
|---|---|---|
| `StatCounter` | A number counting up with a fill bar | `statValue` (number) |
| `DonutFill` | Ring chart, segments sweeping in with % counters | `segments[]` |
| `CompareSplit` | Before/after split. "Было / Стало" | `cards[]` (exactly 2) |
| `FlowDiagram` | Pipeline or stages connecting up | `nodes[]` or `steps[]` |
| `SwipePanels` | Info panels sliding in from the side | `cards[]` |
| `CodeReveal` | Syntax-highlighted code revealing line by line | `code` + `language` |
| `RingStats` | Up to 6 independent rings, each on its OWN 0..max scale | `segments[]` |
| `Bars3D` | Extruded 3D bars rising out of a ground plane | `segments[]` |

`DonutFill` shows shares of ONE whole (they sum to the total). `RingStats` shows
independent percentages — three 90% rings are impossible in a donut. `Bars3D` is
for comparing magnitudes across categories with depth.

### UI mockups — the "wait, that's real?" shots
| Preset | What the viewer sees | Required data |
|---|---|---|
| `TgChat` | A Telegram thread, bubbles arriving with read ticks | `messages[]` |

**TgChat can type and send a message on camera** — the shot that makes a chat
mockup read as live instead of as a screenshot:
```jsonc
{"preset": "TgChat", "text": "…",
 "contactName": "Аня",
 "messages": [{"from": "Аня", "text": "Влезает в 12 гигов?"}],
 "compose": "Влезает, 11.4 ГБ на пике",   // typed into the input field
 "sendAtProgress": 0.72}                   // 0..1: when send is pressed
```
The header shows `печатает…` while typing, a cursor travels to the send button,
presses it, and the bubble launches into the thread. Every part is opt-out:
`typing: false` (text already in the field), `showCursor: false` (no mouse — use
for phone framing where a finger would tap), `showInputBar: false`. Omit
`compose` entirely and the scene behaves exactly as before: no bar, no cursor.
| `AiChatStream` | An LLM reply streaming token by token | `messages[]` + `response` |
| `CryptoWallet` | Wallet card, masked address, balance counting up | `balance`, `tokens[]` |
| `BankCard` | Payment card tilting in; only last 4 digits shown | `last4`, `holder`, `expiry` |

### Media — real material on screen
| Preset | What the viewer sees | Required data |
|---|---|---|
| `ImageShowcase` | Stills with a slow Ken Burns drift | `images[]` or `src` |
| `VideoEmbed` | External clip framed with a progress bar | `src` (video) |
| `ScreenRecord` | Screen capture in browser chrome with a blinking REC | `src` or `images[0]` |
| `VoiceMemo` | Voice-message bubble, waveform playing through | none (`transcript` recommended) |
| `MusicPlayer` | Now-playing card: cover, equaliser, scrubber | `trackTitle`, `artist` |
| `VinylRecord` | Record spinning at real rpm, tonearm dropping in | `trackTitle`, `artist` |

`src`/`images[]` take a URL or a path relative to `remotion/public/`.
`ScreenRecord` accepts a still instead of a video — a screenshot with drift is
often enough and far cheaper than a capture.

### Device — a screen inside the frame
| Preset | What the viewer sees | Required data |
|---|---|---|
| `PhoneMockup` | Phone body with **another preset running on its screen** | `innerPreset` + `innerProps` |
| `BankCard` | Payment card tilting in; only last 4 digits shown | `last4`, `holder`, `expiry` |

`PhoneMockup` is the strongest "that's a real app" shot in the library:
```jsonc
{"preset": "PhoneMockup", "text": "…",
 "innerPreset": "TgChat",
 "innerProps": {"contactName": "Аня",
                "messages": [{"from": "Аня", "text": "Готово?"},
                             {"text": "Ага, смотри", "out": true, "read": true}]},
 "title": "Работает на телефоне"}
```
Any preset can go inside. Nesting is capped at depth 2.

### 3D
| Preset | What the viewer sees | Required data |
|---|---|---|
| `TokenCloud3D` ROT | Drifting point cloud / embedding field | none (`pointCount` defaults 900) |
| `LayerStack3D` | Transformer layers stacked in depth | `layers[]` (strings) |
| `ModelOrbit3D` | A 3D model orbiting under studio light | `modelUrl` (asset required) |

## The selection algorithm — run this, do not improvise

You have all 26 presets at level 1. The failure mode is not permission, it is
defaulting to the three you remember. Work the list mechanically:

**Step 1 — split the script into beats.** One sentence or claim = one scene.
6-10 scenes for 20-30s.

**Step 2 — label every beat with its content type.** Exactly one label each:

| The beat is… | Label |
|---|---|
| a claim, a hook, a title | TEXT |
| a number, a percentage, a comparison of magnitudes | NUMBER |
| a dialogue, a message, a reply | CHAT |
| a screen, an app, a website, a product UI | SCREEN |
| a photo, a clip, a recording | MEDIA |
| a quote, someone's words | QUOTE |
| code, a command, a config | CODE |
| a process, stages, a pipeline | FLOW |
| a track, a song, audio | AUDIO |
| a wallet, a payment, a card | MONEY |

**Step 3 — map each label to its preset.** Take the first that fits the data
you actually have:

- TEXT → `HeroKinetic` (short) · `TypewriterSub` (long) · `GridGridFloor` (needs texture)
- NUMBER → one number `StatCounter` · shares of one whole `DonutFill` ·
  independent percentages `RingStats` · categories compared `Bars3D` ·
  before/after `CompareSplit`
- CHAT → `TgChat` (add `compose` to type it live) · LLM reply `AiChatStream`
- SCREEN → `ScreenRecord` (browser chrome) · `PhoneMockup` (on a phone, with `innerPreset`)
- MEDIA → stills `ImageShowcase` · clip `VideoEmbed`
- QUOTE → `QuoteCard`
- CODE → `CodeReveal`
- FLOW → `FlowDiagram` (connected) · `SwipePanels` (independent features)
- AUDIO → `MusicPlayer` · `VinylRecord` · voice `VoiceMemo`
- MONEY → `CryptoWallet` · `BankCard` · or any scene + `money` overlay

**Step 4 — enforce the four hard rules.** Check each, fix violations:

1. **No preset twice in a row.** Two identical shapes back to back reads as a
   stuck video. Swap one for another preset of the same label.
2. **≥ 5 distinct presets in a 6-scene video.** Four or fewer means you
   defaulted. Re-check step 3 for beats you lazily labelled TEXT.
3. **≥ 2 non-TEXT scenes per 4 scenes.** All-typography means the library is unused.
4. **Every data/UI preset gets real data.** A `DonutFill` with no `segments`,
   a `TgChat` with no `messages` renders empty chrome. If you don't have the
   data, pick a different preset — do not ship an empty one.

**Step 5 — pick one style kit for the video** from the table above, matched to
subject matter. Override on a single scene only for a deliberate contrast beat.

**Step 6 — add overlays where they earn attention:** a `timer` on urgency, a
`notification` on social proof, `money` on a payment claim. Optional; do not add
one to every scene.

### Worked example

Script: "Нейросеть пишет код за секунды. 40% быстрее ручной разработки.
Смотри, как это выглядит в редакторе. Вот отзыв разработчика."

| Beat | Label | Preset | Data |
|---|---|---|---|
| «Нейросеть пишет код за секунды» | TEXT | `HeroKinetic` | title |
| «40% быстрее» | NUMBER | `StatCounter` | statValue 40, statSuffix "%" |
| «как это выглядит» | SCREEN | `ScreenRecord` | src + urlBar |
| «пишет код» | CODE | `CodeReveal` | code + language |
| «отзыв разработчика» | QUOTE | `QuoteCard` | text + author |

5 beats, 5 distinct presets, 4 non-TEXT, no repeats, every preset has data.
Style `pop`. That passes all four rules.

## How to pick — think in shots, not in presets

A short that holds attention alternates **register**. Same-shaped scenes back to
back are what makes a video feel cheap, even when every scene is correct.

Working structure for a 20-30s short:

1. **Hook** (0-3s) — `HeroKinetic`. One claim, big type.
2. **Proof** — the concrete shot: `AiChatStream` / `TgChat` (with `compose`) /
   `ScreenRecord` / `PhoneMockup`. Show the thing, don't describe it.
3. **Number** — `StatCounter`, `RingStats` or `Bars3D`. One metric that
   justifies the hook.
4. **Contrast** — `CompareSplit`. Before/after is the strongest retention beat.
5. **Texture** — `GridGridFloor` / `TokenCloud3D` / `ImageShowcase`. Eye rest.
6. **Close** — `QuoteCard` or `HeroKinetic`. The ask.

Content type → the presets that fit:
- **educational**: `TypewriterSub`, `FlowDiagram`, `CodeReveal`, `Bars3D`, `ScreenRecord`
- **entertainment**: `TgChat` + `compose`, `PhoneMockup`, `ImageShowcase`, overlays
- **advertising**: `CompareSplit`, `PhoneMockup`, `RingStats`, money overlay
- **musical**: `MusicPlayer`, `VinylRecord`, `VoiceMemo` + `neon`/`retro` kit
- **gaming**: `ScreenRecord`, `VideoEmbed`, `Bars3D`, timer overlay, `retro` kit

Rules that matter more than the order:
- **Never repeat a preset in adjacent scenes.** Two `HeroKinetic` in a row reads
  as a stuck video.
- **At least one data or UI-mock preset per 4 scenes.** If a video is all
  typography, the library isn't being used.
- **Aim for 5+ distinct presets** in a 6-scene short. Fewer than 4 means you
  defaulted to rotation.
- Match preset to content: a number → `StatCounter`, a breakdown → `DonutFill`,
  a dialogue → `TgChat`, a claim about speed → `CompareSplit`. Forcing a preset
  onto content it doesn't fit is worse than rotation.

If unsure → `HeroKinetic` + `gold`.

## Preset rotation (the fallback, not the plan)
When a scene has no `preset` of its own, the graph rotates it through the
text-safe list: `HeroKinetic → TypewriterSub → QuoteCard → GridGridFloor →
TokenCloud3D`. That guarantees a 15-second short isn't one static card, but it
can only ever produce typography and abstract 3D.

Data-driven presets are excluded from rotation because plain narration doesn't
carry `statValue` / `cards` / `messages` — they'd render their `⚠ NO ... IN SPEC`
marker. A data-driven preset you name explicitly is never rotated away from.

## Field types that agents get wrong (measured, not guessed)

A sweep of `audit/agent_error_probe.py` over `gemini-3.6-flash-medium` and
`-high` scored **2/5 clean specs** on both. Adding the block below to the brief
took both models to **5/5**. Same models, same tasks — the gap was documentation,
not capability. Reproduce with `--brief v1` vs `--brief v2`.

Both failure modes were type errors, not bad judgement — the models picked the
right preset and wrote good copy, then filled the fields with the wrong shape:

1. **`statValue` is a NUMBER.** Units belong in `statSuffix`.
   ```jsonc
   "statValue": "6.8 ГБ"                                   // ✗ Zod rejects
   "statValue": "6.8"                                      // ✗ still a string
   "statValue": 6.8, "statSuffix": " ГБ", "statLabel": "Видеопамяти"  // ✓
   ```
2. **`steps` and `nodes` are arrays of OBJECTS**, not strings.
   ```jsonc
   "steps": ["Текст", "Токены"]                                        // ✗
   "steps": [{"label": "Текст", "detail": "на входе"}]                 // ✓
   "nodes": [{"label": "Attention", "sub": "8 голов"}]                 // ✓ sub, not detail
   ```
3. **`cards` are objects with a required `title`.**
   ```jsonc
   "cards": [{"label": "Было", "value": "10 часов"}]                   // ✗ no title
   "cards": [{"title": "10 часов", "description": "вручную", "tag": "БЫЛО"}]  // ✓
   ```
4. **`layers` is an array of plain strings** — the one field that is not objects.
5. **`durationInFrames` counts FRAMES.** At 60 fps, 3 seconds = `180`.
6. **`segments` (DonutFill) are objects with `label` + numeric `value`.**
   ```jsonc
   "segments": [{"label": "Текст", "value": "62%"}]        // ✗ value is a string
   "segments": [{"label": "Текст", "value": 62},           // ✓ number, no % sign
                {"label": "Код", "value": 24}]
   ```
   Values do not have to sum to 100 — shares are computed from the total.
7. **`messages` (TgChat / AiChatStream) are objects.** `out: true` marks your own
   outgoing bubble; incoming ones carry `from`.
   ```jsonc
   "messages": ["Привет"]                                                  // ✗
   "messages": [{"from": "Аня", "text": "Видел новую модель?"},            // ✓
                {"text": "Уже запустил", "out": true, "read": true}]
   ```
   `AiChatStream` also needs `response` — the reply that streams out.
8. **`tokens` (CryptoWallet) are objects** with `symbol`, `amount`, `change`.

Rule of thumb: `label`+`detail` for `steps`, `label`+`sub` for `nodes`,
`title`+`description`+`tag` for `cards`, `label`+`value` for `segments`.

## Rules
- NEVER edit `remotion/src/presets/` or `remotion/src/parts/`
- NEVER create new React components (that's `msf-smart-animate`, level ≥ 3)
- NEVER write `video-spec.json` yourself
- NEVER set `agent_level` above your real level to unlock custom code

## Verification (mandatory before reporting success)
Do not report a video as done on the graph's return value alone. Check the artifact:
```bash
ffprobe -v error -show_entries stream=width,height,r_frame_rate,sample_rate \
        -show_entries format=duration -of default=noprint_wrappers=1 <final_mp4>
ffmpeg -hide_banner -nostats -i <final_mp4> -af volumedetect -f null -   # expect mean_volume around -18 dB, not -91
```
Then look at a QA frame with `vision_analyze` — it is the only check that catches a
video that is technically valid but visually blank.

## Diversity gate — do not ship a monotone video
Before declaring success, list the presets your storyboard produced:
```python
import json
spec = json.load(open(result["spec_path"], encoding="utf-8"))
presets = [s["preset"] for s in spec["scenes"]]
print("presets used:", presets)
```
Ship only if **all** hold:
- no preset repeats on adjacent scenes
- at least one data/UI-mock preset per 4 scenes (StatCounter, DonutFill,
  CompareSplit, FlowDiagram, SwipePanels, CodeReveal, TgChat, AiChatStream,
  CryptoWallet, BankCard, LayerStack3D)
- 5+ distinct presets in a 6-scene video

If any fails, rebuild the storyboard with more variety before rendering again.
A correct video that is 6 title cards is a bug, not a deliverable.

## Pitfalls learned the hard way
- **The ffprobe flag is `-of default=noprint_wrappers=1`.** Writing `noprintwrappers`
  silently breaks duration parsing instead of erroring out.
- **Mastering cannot write over its own input.** `raw_mp4` and `final_mp4` must be
  different files or ffmpeg produces a 0-byte output. The graph now always suffixes raw.
- **`loudnorm` upsamples internally** and leaves the output upsampled. Pin `-ar 48000`
  explicitly or you ship a 96 kHz file that some players reject.
- **A red Zod ERROR screen is a rendered video, not an exception.** An invalid spec used
  to render "successfully". Python-side `validate_spec()` now raises first — keep it that way.
- **Scene durations must come from the real WAV length**, never a hardcoded 90 frames,
  or the voiceover gets cut mid-word.
- **Scene splitting drives pacing.** The splitter targets ~10 words per scene on clause
  boundaries. A high word limit merges the whole script into one card that sits still for
  the entire video — technically passing QA while being unwatchable.
- **QA passing is not the same as good.** Every automated check can pass on a video that
  is five identical frames. Always look at the frame strip before declaring success.
