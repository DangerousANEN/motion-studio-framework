# MSF Expansion Plan — scenes, effects, SFX, music

Target: **104 scenes**, **108 effects**, **112 sound effects**, **16 music beds**.

Every row below is a work order. A row names the component, what it draws, the
spec fields it reads, and how it will be verified. Rows are deliberately
specific because they are handed to parallel authors — anything left implicit
comes back as 104 inconsistent components.

## Ground rules for every component

These are not style preferences. Each one corresponds to a bug class already hit
in this repo.

1. **Safe area from `getSafeArea(width, height, safeArea)`.** Never hardcode
   insets. Platform chrome differs per target and content drifts under the UI.
2. **Sizes derived from `useVideoConfig()`.** A preset that assumes 1080×1920
   silently breaks the horizontal format.
3. **Animation through `resolveMotion(motion, fps, channel)`.** Raw `frame`
   interpolation ignores intensity presets and per-scene overrides.
4. **No text outside the safe box.** Long Russian strings are ~1.4× English;
   test with the longest realistic string, not "Test".
5. **Deterministic.** Seeded randomness only (`mulberry32(seed)`), never
   `Math.random()` — non-deterministic frames make regressions unprovable.
6. **Registered via `tools/msf_add.py`,** never by hand-editing the registry.
7. **Verified by pixels,** not by exit code. A component that throws renders the
   error card and still exits 0.

## Audio architecture

Synthesised procedurally, not sourced from sample libraries. Three reasons:
renders stay reproducible offline, there are no per-file licence audits across
112 files, and a synthesised SFX can be re-tuned parametrically (pitch, length,
brightness) instead of re-recorded.

```
scene SFX ──┐
transition ─┼─► bus ──► sidechain duck (voice-triggered) ──► master ──► -14 LUFS
music bed ──┘              ▲
voice ─────────────────────┘ (never ducked, always the loudest element)
```

- Music sits at **-26 LUFS**, ducking to **-32** under voice. Unobtrusive means
  measurably quiet, not subjectively quiet.
- SFX peak at **-18 dBFS**; transition whooshes at **-20**.
- Ducking uses a 120 ms attack / 400 ms release envelope keyed off the voice
  track's RMS, so speech onset is never clipped by a late duck.

---

# Part 1 — Scenes (104)

## 1.1 UI mockups — messaging (12)

| # | Component | Draws | Reads | Verify |
|---|---|---|---|---|
| 1 | `TgChat` | Telegram chat, bubbles arriving in sequence with tails, timestamps, read ticks | `messages[]{from,text,time,read}` | bubble count == messages.length; no bubble crosses safe edge |
| 2 | `TgChannelPost` | Channel post card: avatar, name, formatted body, view counter ticking | `channel,body,views` | view counter monotonic |
| 3 | `TgTypingIndicator` | Three-dot typing animation then message resolves | `text,typingMs` | dots animate before text appears |
| 4 | `TgVoiceMessage` | Voice bubble with live waveform and progress | `durationSec,waveformSeed` | waveform bars > 20 |
| 5 | `TgPoll` | Poll with bars filling to final percentages | `question,options[]{label,pct}` | bars sum to 100 |
| 6 | `TgForwardChain` | Message forwarded through 3 chats, showing the trail | `chain[]` | each hop visible |
| 7 | `WhatsAppChat` | WhatsApp-styled thread, green bubbles, double ticks | `messages[]` | tick state matches `read` |
| 8 | `DiscordChat` | Discord channel: roles coloured, reactions popping in | `messages[]{author,role,text,reactions}` | role colours distinct |
| 9 | `SlackThread` | Slack thread with reply count and emoji reactions | `messages[]` | thread indent correct |
| 10 | `SmsThread` | iOS-style SMS, blue/grey bubbles | `messages[]` | alignment by sender |
| 11 | `EmailInbox` | Inbox list, unread bold, one row opening | `emails[]{from,subject,unread}` | opened row expands |
| 12 | `NotificationStack` | Push notifications stacking then collapsing | `notifications[]` | stack order preserved |

## 1.2 UI mockups — AI / chat assistants (10)

| # | Component | Draws | Reads | Verify |
|---|---|---|---|---|
| 13 | `AiChatStream` | LLM chat, response streaming token by token with cursor | `prompt,response,tokensPerSec` | text length grows monotonically |
| 14 | `AiThinking` | "Thinking" state: shimmer, elapsed timer, then answer | `prompt,thinkMs,answer` | timer increments |
| 15 | `AiToolCall` | Assistant invoking a tool: call block, args, result collapsing in | `tool,args,result` | all three blocks render |
| 16 | `AiCodeAssist` | Split view: prompt left, generated code typing right | `prompt,code,language` | code syntax-highlighted |
| 17 | `AiCompareModels` | Two model answers side by side, quality badges | `modelA,modelB,answers` | both columns equal width |
| 18 | `AiTokenCost` | Token counter and cost accumulating as text streams | `tokens,pricePerK` | cost == tokens/1000*price |
| 19 | `AiContextWindow` | Context window filling up, old messages sliding out | `used,limit` | fill ratio == used/limit |
| 20 | `AiPromptRefine` | Prompt being rewritten across 3 iterations, diffs highlighted | `versions[]` | diff marks present |
| 21 | `AiAgentLoop` | Agent loop: think → act → observe cycling with a spinner | `steps[]` | cycle visits all steps |
| 22 | `AiRagRetrieval` | Query hitting a vector store, chunks lighting up, answer assembling | `query,chunks[]` | retrieved chunks highlighted |

## 1.3 Finance — crypto (14)

| # | Component | Draws | Reads | Verify |
|---|---|---|---|---|
| 23 | `CryptoWallet` | Wallet card: address (truncated), balance counting, token rows | `address,balance,tokens[]` | address masked mid-string |
| 24 | `CryptoSend` | Send flow: amount, gas estimate, confirm button pressing | `amount,token,gasGwei,to` | gas shown before confirm |
| 25 | `CryptoTxConfirm` | Transaction pending → confirmed, block confirmations ticking | `hash,confirmations` | confirmations increase |
| 26 | `CryptoSeedPhrase` | 12-word seed grid revealing, with a redacted warning banner | `words[]` | exactly 12 cells |
| 27 | `CryptoPriceChart` | Candlestick chart drawing left to right with a live price tag | `candles[]` | candle count matches data |
| 28 | `CryptoOrderBook` | Bid/ask ladder with depth bars pulsing | `bids[],asks[]` | bids below asks |
| 29 | `CryptoSwap` | Token swap: A→B with rate, slippage, route path | `from,to,rate,slippage` | route arrows connect |
| 30 | `CryptoStaking` | Staking position: APY, rewards accruing per second | `staked,apy` | rewards accrue |
| 31 | `CryptoGasTracker` | Gas price gauge: slow/avg/fast needles | `slow,avg,fast` | needle order correct |
| 32 | `CryptoNftCard` | NFT card flipping to reveal traits and rarity | `image,traits[]` | traits listed |
| 33 | `CryptoPortfolioDonut` | Portfolio allocation donut (reuses `DonutFill` motion contract) | `holdings[]` | segments sum to 100% |
| 34 | `CryptoLiquidation` | Leveraged position approaching liquidation, bar going red | `entry,liqPrice,current` | colour shifts on threshold |
| 35 | `CryptoBridge` | Cross-chain bridge: chain A → B with lock/mint steps | `fromChain,toChain,amount` | both chain logos render |
| 36 | `CryptoMiningRig` | Mining dashboard: hashrate graph, temps, accepted shares | `hashrate,temp,shares` | graph scrolls |

## 1.4 Finance — banking / payments (12)

| # | Component | Draws | Reads | Verify |
|---|---|---|---|---|
| 37 | `BankCard` | Payment card with 3D tilt, number revealing, chip highlight | `last4,holder,expiry,brand` | only last4 shown |
| 38 | `BankTransfer` | Transfer form → processing spinner → success check | `from,to,amount` | success state reached |
| 39 | `BankStatement` | Statement rows scrolling, debits red, credits green | `transactions[]` | sign colours correct |
| 40 | `BankBalanceGraph` | Balance over time, area chart filling | `points[]` | line monotone in x |
| 41 | `BankPaymentSuccess` | Full-screen success: check draws, amount, receipt slides up | `amount,merchant` | check path completes |
| 42 | `BankPaymentFailed` | Decline state: cross draws, reason code, retry button | `reason` | reason text visible |
| 43 | `BankQrPay` | QR code rendering then scan line sweeping across | `payload` | QR modules render |
| 44 | `BankInvoice` | Invoice document: line items, VAT, total | `items[],vatPct` | total == sum + VAT |
| 45 | `BankSubscription` | Subscription tiers with a plan being selected | `tiers[]` | selected tier highlighted |
| 46 | `BankCurrencyConvert` | Currency conversion with rate flipping | `from,to,rate,amount` | result == amount*rate |
| 47 | `BankAtm` | ATM screen: PIN entry masked, cash dispensing | `amount` | PIN chars masked |
| 48 | `BankCreditScore` | Score gauge sweeping to value with band colours | `score` | needle at correct arc |

## 1.5 Device frames (8)

| # | Component | Draws | Reads |
|---|---|---|---|
| 49 | `PhoneFrame` | Phone bezel wrapping arbitrary child content, notch and status bar | `child,os` |
| 50 | `PhoneScroll` | Phone with content scrolling under a fixed header | `screens[]` |
| 51 | `LaptopFrame` | Laptop with a screen and reflection sheen | `child` |
| 52 | `BrowserFrame` | Browser chrome: URL bar typing, tabs, favicon | `url,child` |
| 53 | `TabletSplit` | Tablet in landscape, split view of two panes | `left,right` |
| 54 | `WatchFrame` | Smartwatch face with a complication updating | `child` |
| 55 | `TerminalWindow` | Terminal: prompt, command typing, output streaming | `commands[]{cmd,out}` |
| 56 | `MultiDeviceFan` | Three devices fanning out showing the same app | `screens[]` |

## 1.6 Data visualisation (14)

| # | Component | Draws | Reads |
|---|---|---|---|
| 57 | `BarRace` | Horizontal bar chart race reordering over time | `series[]` |
| 58 | `LineChartDraw` | Multi-series line chart drawing with a legend | `series[]` |
| 59 | `AreaStack` | Stacked area chart building bottom up | `series[]` |
| 60 | `ScatterCluster` | Scatter plot with points clustering into groups | `points[]` |
| 61 | `HeatmapGrid` | Heatmap cells filling by intensity | `matrix[][]` |
| 62 | `GaugeCluster` | Three gauges sweeping to their values together | `gauges[]` |
| 63 | `FunnelChart` | Conversion funnel narrowing with drop-off labels | `stages[]` |
| 64 | `SankeyFlow` | Sankey diagram, flows widening as they animate | `nodes[],links[]` |
| 65 | `TreemapBoxes` | Treemap rectangles subdividing | `items[]` |
| 66 | `RadarSpider` | Radar chart axes extending to values | `axes[]` |
| 67 | `WaterfallBars` | Waterfall chart with running total connectors | `steps[]` |
| 68 | `BulletKpi` | KPI bullet bars against targets | `kpis[]` |
| 69 | `SparklineRow` | Row of sparklines with delta badges | `metrics[]` |
| 70 | `WorldMapPins` | World map with pins dropping and arcs connecting | `pins[],arcs[]` |

## 1.7 Diagram / process (10)

| # | Component | Draws | Reads |
|---|---|---|---|
| 71 | `TimelineHorizontal` | Timeline with milestones popping along a track | `milestones[]` |
| 72 | `SwimlaneFlow` | Multi-lane process flow with handoffs between lanes | `lanes[]` |
| 73 | `StateMachine` | State nodes with a token travelling along transitions | `states[],edges[]` |
| 74 | `ArchLayers` | Layered architecture stack highlighting one layer | `layers[]` |
| 75 | `NetworkGraph` | Force-directed node graph settling | `nodes[],edges[]` |
| 76 | `SequenceDiagram` | Lifelines with messages drawing between actors | `actors[],messages[]` |
| 77 | `MindMapRadial` | Radial mind map branching outward | `root,branches[]` |
| 78 | `KanbanBoard` | Kanban columns with a card moving across | `columns[]` |
| 79 | `GitBranchGraph` | Git commit graph with branch and merge | `commits[]` |
| 80 | `DecisionTree` | Decision tree with the chosen path lighting up | `nodes[],path[]` |

## 1.8 Typography / narrative (12)

| # | Component | Draws | Reads |
|---|---|---|---|
| 81 | `BigNumberDrop` | One huge number slamming in with a shockwave | `value,label` |
| 82 | `WordByWord` | Sentence assembling word by word with emphasis | `text,emphasis[]` |
| 83 | `TextMaskReveal` | Headline revealed through a moving mask | `text` |
| 84 | `SplitHeadline` | Headline splitting into two halves that separate | `text` |
| 85 | `CountdownTimer` | Countdown with digits flipping | `fromSec` |
| 86 | `ChecklistTicks` | Checklist items ticking one by one | `items[]` |
| 87 | `BeforeAfterSlider` | Before/after wipe with a draggable handle | `before,after` |
| 88 | `PriceTagReveal` | Old price crossing out, new price stamping | `oldPrice,newPrice` |
| 89 | `TestimonialCard` | Testimonial with avatar, stars filling, quote | `author,stars,text` |
| 90 | `LowerThird` | Broadcast lower-third bar sliding in | `name,role` |
| 91 | `EndCardCta` | End card: logo, CTA button pulsing, handle | `cta,handle` |
| 92 | `ChapterTitle` | Chapter divider with a number and rule | `number,title` |

## 1.9 3D (12)

| # | Component | Draws | Reads |
|---|---|---|---|
| 93 | `CoinSpin3D` | Coin spinning with metallic PBR and rim light | `symbol` |
| 94 | `PhoneOrbit3D` | 3D phone orbiting with a screen texture | `screenTexture` |
| 95 | `NetworkGlobe3D` | Globe with arcs between geo points | `arcs[]` |
| 96 | `CardFlip3D` | Card flipping in 3D revealing its back | `front,back` |
| 97 | `TowerBuild3D` | Blocks stacking into a tower | `blocks[]` |
| 98 | `TunnelFly3D` | Camera flying through a neon tunnel | `speed` |
| 99 | `TextExtrude3D` | Extruded 3D text rotating | `text` |
| 100 | `ParticleBurst3D` | Particle explosion resolving into a shape | `shape` |
| 101 | `DataBars3D` | 3D bar chart with camera dolly | `bars[]` |
| 102 | `LiquidBlob3D` | Metaball blob morphing | `seed` |
| 103 | `ChipCloseup3D` | Macro shot over a chip with traces glowing | `label` |
| 104 | `RoomIsometric3D` | Isometric room with objects popping in | `objects[]` |

---

# Part 2 — Effects (108)

Effects are composable wrappers, not scenes. Contract:

```ts
export interface EffectProps {
  children: React.ReactNode;
  intensity?: number;      // 0..1, 1 = preset default
  seed?: number;           // required if the effect is stochastic
}
```

An effect must be a no-op at `intensity: 0` — that is the property the audit
asserts, because a "subtle" effect that still alters pixels at zero cannot be
disabled by a caller.

## 2.1 Entrance (16)
`FadeIn` · `SlideInLeft` · `SlideInRight` · `SlideInUp` · `SlideInDown` ·
`ScaleIn` · `ScaleInBounce` · `RotateIn` · `FlipInX` · `FlipInY` ·
`BlurIn` · `ClipWipeIn` · `MaskCircleIn` · `TypeIn` · `StaggerChildren` ·
`ElasticPop`

## 2.2 Exit (12)
`FadeOut` · `SlideOutLeft` · `SlideOutRight` · `SlideOutUp` · `SlideOutDown` ·
`ScaleOut` · `RotateOut` · `BlurOut` · `ClipWipeOut` · `MaskCircleOut` ·
`ShatterOut` · `DissolveOut`

## 2.3 Emphasis / loop (16)
`Pulse` · `Breathe` · `Shake` · `Wobble` · `Jitter` · `Bounce` · `Float` ·
`Swing` · `HeartBeat` · `Flash` · `Glow` · `Shimmer` · `Sheen` · `Ripple` ·
`Tremble` · `Squash`

## 2.4 Camera (12)
`ZoomPunch` · `ZoomSlow` · `PanLeft` · `PanRight` · `DollyIn` · `DollyOut` ·
`HandheldDrift` · `WhipPan` · `RackFocus` · `ParallaxLayers` · `OrbitAround` ·
`TiltShift`

## 2.5 Colour / grade (14)
`Vignette` · `FilmGrain` · `ChromaticAberration` · `Bloom` · `ColorGradeWarm` ·
`ColorGradeCool` · `Duotone` · `Invert` · `Saturate` · `Desaturate` ·
`Contrast` · `Posterize` · `HalationGlow` · `LightLeak`

## 2.6 Distortion (14)
`GlitchRgb` · `GlitchBlock` · `ScanLines` · `CrtCurve` · `VhsTracking` ·
`WaveWarp` · `RippleDistort` · `LensDistort` · `PixelSort` · `Displace` ·
`MotionBlurTrail` · `EchoTrail` · `Kaleidoscope` · `MirrorSplit`

## 2.7 Overlay / atmosphere (12)
`ParticlesDust` · `ParticlesSnow` · `ParticlesSparks` · `Confetti` ·
`RainStreaks` · `SmokeWisps` · `NoiseOverlay` · `GridOverlay` ·
`ScanSweep` · `SpotlightFollow` · `CausticsLight` · `BokehLights`

## 2.8 Transitions between scenes (12)
`CutHard` · `CrossFade` · `WipeLinear` · `WipeCircle` · `SlidePush` ·
`ZoomBlurTransition` · `GlitchTransition` · `WhipPanTransition` ·
`MorphShape` · `LiquidWarp` · `FilmBurn` · `LightFlashCut`

---

# Part 3 — Sound effects (112)

Every SFX is a function `(sampleRate, params) -> Float32Array`, synthesised from
oscillators, noise, and envelopes. Each has a **maximum length** because long
tails collide with the next scene's audio.

## 3.1 UI / interaction (20)
`click_soft` 40 ms · `click_hard` 60 ms · `tap_bubble` 80 ms · `toggle_on` 90 ms ·
`toggle_off` 90 ms · `hover_tick` 30 ms · `keypress` 25 ms · `keyboard_run` 600 ms ·
`send_swoosh` 220 ms · `receive_pop` 140 ms · `notify_ding` 400 ms ·
`notify_double` 500 ms · `error_buzz` 260 ms · `success_chime` 600 ms ·
`unlock_click` 180 ms · `scroll_tick` 20 ms · `swipe_soft` 200 ms ·
`focus_ring` 120 ms · `dropdown_open` 160 ms · `modal_in` 240 ms

## 3.2 Money / finance (18)
`coin_single` 300 ms · `coin_stack` 700 ms · `cash_register` 800 ms ·
`card_tap` 200 ms · `card_swipe` 350 ms · `atm_dispense` 900 ms ·
`transfer_send` 500 ms · `transfer_receive` 500 ms · `payment_ok` 700 ms ·
`payment_fail` 600 ms · `balance_up` 400 ms · `balance_down` 400 ms ·
`counter_tick` 30 ms · `counter_run` 1200 ms · `stamp_hit` 200 ms ·
`receipt_print` 900 ms · `vault_close` 800 ms · `bell_profit` 600 ms

## 3.3 Crypto / tech (16)
`tx_pending` 400 ms · `tx_confirm` 600 ms · `block_mined` 700 ms ·
`hash_pulse` 150 ms · `wallet_open` 350 ms · `swap_whoosh` 400 ms ·
`bridge_warp` 700 ms · `mint_sparkle` 800 ms · `liquidation_alarm` 900 ms ·
`gas_hiss` 500 ms · `chain_link` 250 ms · `node_ping` 120 ms ·
`data_burst` 300 ms · `encrypt_scramble` 500 ms · `sync_sweep` 600 ms ·
`server_hum` 1000 ms

## 3.4 Transitions / whooshes (18)
`whoosh_short` 250 ms · `whoosh_long` 600 ms · `whoosh_reverse` 500 ms ·
`whip_pan` 300 ms · `riser_short` 700 ms · `riser_long` 1500 ms ·
`impact_soft` 300 ms · `impact_hard` 500 ms · `boom_sub` 800 ms ·
`glitch_tear` 300 ms · `digital_scramble` 400 ms · `tape_stop` 500 ms ·
`vinyl_scratch` 400 ms · `film_burn` 700 ms · `light_flash` 250 ms ·
`wipe_swipe` 200 ms · `morph_bend` 600 ms · `zoom_rush` 450 ms

## 3.5 Mechanical / physical (16)
`switch_flip` 100 ms · `latch_close` 150 ms · `gear_turn` 400 ms ·
`spring_boing` 350 ms · `paper_slide` 250 ms · `paper_tear` 300 ms ·
`glass_tap` 180 ms · `glass_break` 700 ms · `metal_ping` 400 ms ·
`wood_knock` 150 ms · `rubber_squeak` 200 ms · `chain_rattle` 500 ms ·
`door_slide` 600 ms · `lock_turn` 350 ms · `stamp_press` 250 ms ·
`typewriter_return` 400 ms

## 3.6 Ambience / texture (14)
`room_tone` loop · `city_hum` loop · `office_murmur` loop · `rain_soft` loop ·
`wind_low` loop · `electric_buzz` loop · `fan_whirr` loop · `crowd_distant` loop ·
`water_flow` loop · `fire_crackle` loop · `night_crickets` loop ·
`keyboard_office` loop · `traffic_far` loop · `datacenter_drone` loop

## 3.7 Musical stingers (10)
`sting_up_major` 800 ms · `sting_down_minor` 800 ms · `sting_reveal` 1200 ms ·
`sting_tension` 1000 ms · `sting_resolve` 1400 ms · `arp_up` 600 ms ·
`arp_down` 600 ms · `chord_stab` 400 ms · `bell_reveal` 1000 ms ·
`pad_swell` 2000 ms

---

# Part 4 — Music beds (16)

Each is a procedurally generated loop with a defined key, BPM, and instrument
set. All are built to sit under speech: no content above 4 kHz competing with
consonants, no melodic movement in the 200 Hz–2 kHz vocal band during speech.

| # | Name | BPM | Key | Character | Use |
|---|---|---|---|---|---|
| 1 | `minimal_pulse` | 90 | Am | Muted pulse, soft sub | Default explainer bed |
| 2 | `warm_keys` | 84 | F | Felt piano, tape hiss | Narrative, testimonial |
| 3 | `tech_drift` | 100 | Cm | Filtered saw pad, ticks | Product / tech |
| 4 | `crypto_dark` | 96 | Dm | Deep sub, sparse blips | Finance, risk |
| 5 | `upbeat_clean` | 112 | G | Plucks, light kick | Growth, positive stats |
| 6 | `lofi_soft` | 76 | Ebm | Dusty keys, vinyl noise | Casual, personal |
| 7 | `corporate_calm` | 92 | Bb | Marimba, strings pad | Business, B2B |
| 8 | `neon_synth` | 108 | Fm | Retro synth arp | Gaming, hype |
| 9 | `ambient_wide` | 70 | A | Long pads, no drums | Intro, contemplative |
| 10 | `percussive_tick` | 104 | Em | Woodblocks, shaker | Process, tutorial |
| 11 | `cinematic_build` | 88 | Gm | Strings rising | Reveal, climax |
| 12 | `glass_bells` | 80 | D | Bell tones, reverb | Elegant, premium |
| 13 | `sub_bass_focus` | 98 | Am | Sub + hats only | Under heavy voiceover |
| 14 | `hopeful_rise` | 106 | C | Piano arp ascending | Conclusion, CTA |
| 15 | `tension_hold` | 94 | Bbm | Drone, tremolo | Problem statement |
| 16 | `silence_bed` | — | — | Room tone only | When music would intrude |

---

# Execution order

Dependencies first — a scene cannot be verified before the audit harness that
verifies it exists.

1. **Audio engine** (`msf/audio/`): synth primitives, SFX registry, music
   generator, mixer with sidechain ducking.
2. **Effects layer** (`remotion/src/fx/effects/`): the `EffectProps` contract
   plus the 108 effects, batched by family.
3. **Scenes**: 104 components in batches of 8–12 by family, so authors within a
   batch share conventions and reviewers compare like with like.
4. **Verification**: render every preset, probe pixels, assert no blanks, no
   safe-area violations, no non-determinism.
5. **Showcase render**: one long-form video exercising every scene family, every
   transition family, SFX, and a music bed with ducking.
6. **Docs and release**: component gallery with a still per preset, authoring
   guide, audio guide, GitHub release.

## What "checked" means here

A batch is accepted only when: `tsc --noEmit` is clean, the registry probe
passes, every new preset renders a still with ink above the blank-frame
threshold, and the still has been looked at. Self-reported completion from an
author is not evidence — the ink probe and the rendered frame are.
