import { z } from 'zod';
import { PRESET_NAMES } from './registry/presets';

/**
 * Wire contract between msf/spec.py and the Remotion renderer.
 *
 * Adding a field here alone is not enough — Scene in msf/spec.py must emit it,
 * and validate_spec() should reject specs that would render a placeholder.
 */

/**
 * Preset names come from the registry, not a second hand-maintained list.
 *
 * The two used to be separate, so a preset could validate and then render the
 * UNKNOWN card (in the enum, absent from the dispatcher) or render fine but be
 * rejected by validation (the reverse). Deriving the enum removes the class of
 * bug entirely; audit/registry_probe.ts still asserts it, which catches the
 * case where someone reintroduces a literal list here.
 *
 * z.enum needs a non-empty literal tuple, hence the cast — PRESET_NAMES is
 * built from Object.keys and is never empty.
 */
export const PresetTypeSchema = z.enum(
  PRESET_NAMES as [string, ...string[]]
);

export type PresetType = z.infer<typeof PresetTypeSchema>;

/**
 * Motion contract. Mirrors lib/motion.ts — keep the curve list in sync.
 *
 * A scene declares intent per channel and the preset resolves it:
 *
 *   motion: {
 *     enter: { curve: 'easeOut', duration: 18 },
 *     value: { curve: 'spring', spring: { damping: 12, stiffness: 90 } }
 *   }
 */
/** Named curves. Must stay identical to the `Curve` union in lib/motion.ts. */
export const NamedCurveSchema = z.enum([
  'linear',
  'ease',
  'easeIn',
  'easeOut',
  'easeInOut',
  'spring',
  'bounce',
  'anticipate',
  'overdamped',
]);

/**
 * A custom cubic bezier, as [x1, y1, x2, y2].
 *
 * x controls must stay in [0,1] — those are time, and time outside the segment
 * is meaningless. y controls may exceed [0,1] on purpose: that is how an author
 * asks for overshoot or anticipation. Bounds are deliberately asymmetric.
 */
export const BezierCurveSchema = z
  .tuple([
    z.number().min(0).max(1),
    z.number().min(-5).max(5),
    z.number().min(0).max(1),
    z.number().min(-5).max(5),
  ]);

export const MotionCurveSchema = z.union([NamedCurveSchema, BezierCurveSchema]);

export const SpringConfigSchema = z
  .object({
    damping: z.number().positive().optional(),
    stiffness: z.number().positive().optional(),
    mass: z.number().positive().optional(),
    overshootClamping: z.boolean().optional(),
  })
  .strict();

export const MotionChannelSchema = z
  .object({
    curve: MotionCurveSchema.optional(),
    /** Frames the animation takes. Ignored by 'spring' (physics decides). */
    duration: z.number().positive().optional(),
    /** Frames to wait before starting. */
    delay: z.number().min(0).optional(),
    spring: SpringConfigSchema.optional(),
    /** Per-item stagger, in frames, for list-like presets. */
    stagger: z.number().min(0).optional(),
    staggerFrom: z.enum(['start', 'end', 'center', 'edges', 'random']).optional(),
    /** Replay behaviour once the animation completes. */
    loop: z.enum(['none', 'pingpong', 'repeat']).optional(),
  })
  .strict();

/**
 * Intensity presets — the only motion control a low-capability agent gets.
 *
 * Resolved by MOTION_PRESETS in lib/motion.ts. A weak model must not hand-write
 * bezier control points; it picks a word instead.
 */
export const IntensitySchema = z.enum(['calm', 'normal', 'punchy', 'extreme']);

/** Named channels presets read: entrance, exit, value, reveal, plus free-form. */
export const MotionSpecSchema = z.record(z.string(), MotionChannelSchema);

/** Safe-area profile. Mirrors lib/safeArea.ts. */
export const SafeAreaModeSchema = z.enum(['platform', 'loose', 'none']);

/** Presets a low-capability agent may use without writing any code. */
export const SAFE_PRESETS: PresetType[] = [
  'HeroKinetic',
  'StatCounter',
  'GridGridFloor',
  'SwipePanels',
  'TypewriterSub',
  'CompareSplit',
  'FlowDiagram',
  'CodeReveal',
  'QuoteCard',
  'TokenCloud3D',
  'LayerStack3D',
  'ModelOrbit3D',
];

/** Presets that need structured data and must not be swapped in by rotation. */
export const DATA_DRIVEN_PRESETS: PresetType[] = [
  'StatCounter',
  'SwipePanels',
  'CompareSplit',
  'FlowDiagram',
  'CodeReveal',
  'LayerStack3D',
];

export const VideoFormatSchema = z.enum([
  'vertical',
  'horizontal',
  'square',
  'classic',
  'cinema',
  'custom',
]);

export const ThemeSchema = z.enum(['pop', 'noir', 'glass', 'blueprint', 'sunset']);
export type ThemeName = z.infer<typeof ThemeSchema>;

export const CardSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
  tag: z.string().optional(),
  color: z.string().optional(),
  value: z.string().optional(),
  icon: z.string().optional(),
});

export const NodeSchema = z.object({
  label: z.string(),
  sub: z.string().optional(),
  color: z.string().optional(),
});

export const HotspotSchema = z.object({
  position: z.tuple([z.number(), z.number(), z.number()]),
  label: z.string(),
  description: z.string().optional(),
});

export const StepSchema = z.object({
  label: z.string(),
  detail: z.string().optional(),
});

/** One arc of a DonutFill. `value` is in the same unit across all segments. */
export const SegmentSchema = z.object({
  label: z.string(),
  value: z.number(),
  color: z.string().optional(),
});

/** A chat bubble, for the messaging UI mockups. */
export const ChatMessageSchema = z.object({
  /** Sender name. Shown on incoming messages only. */
  from: z.string().optional(),
  text: z.string(),
  time: z.string().optional(),
  /** Outgoing (right-aligned, accent bubble) rather than incoming. */
  out: z.boolean().optional(),
  /** Read receipt state; only meaningful on outgoing messages. */
  read: z.boolean().optional(),
});

/** A token row in a wallet, or any label/amount/change triple. */
export const TokenRowSchema = z.object({
  symbol: z.string(),
  name: z.string().optional(),
  amount: z.number(),
  /** Fiat value, if the scene shows one. */
  usd: z.number().optional(),
  /** 24h change in percent; sign drives the colour. */
  change: z.number().optional(),
  color: z.string().optional(),
});

/** A bank statement line. Negative `amount` renders as a debit. */
export const TransactionSchema = z.object({
  label: z.string(),
  amount: z.number(),
  time: z.string().optional(),
  category: z.string().optional(),
});

/**
 * Scene-to-scene transition. Mirrors TRANSITION_NAMES in lib/transitions.ts;
 * a name added there must be added here or the spec will be rejected.
 */
export const TransitionTypeSchema = z.enum([
  'none',
  'fade',
  'slide',
  'wipe',
  'flip',
  'clockWipe',
  'iris',
  'pushCut',
  'ripple',
  'crosswarp',
  'crossZoom',
  'swap',
  'linearBlur',
  'zoomInOut',
  'dreamyZoom',
  'filmBurn',
  'zoomBlur',
  'bookFlip',
]);

export const TransitionSpecSchema = z.object({
  type: TransitionTypeSchema.default('fade'),
  /** Overlap in frames. Clamped at render time so it can never exceed a neighbouring scene. */
  durationInFrames: z.number().int().positive().max(120).optional(),
  direction: z.enum(['from-left', 'from-right', 'from-top', 'from-bottom']).optional(),
  timing: z.enum(['spring', 'linear']).optional(),
});

export type TransitionSpec = z.infer<typeof TransitionSpecSchema>;

/**
 * One effect wrapped around a scene. `name` resolves against the merged
 * effects registry (EFFECTS + VISUAL_EFFECTS + SCENE_EFFECTS in
 * src/registry/effects*.ts); intensity 0 is a proven pixel-level no-op.
 */
export const SceneEffectSchema = z.object({
  name: z.string(),
  intensity: z.number().default(1),
  seed: z.number().optional(),
});

/** A HUD element rendered above a scene. See compositions/OverlayStack.tsx. */
export const OverlaySchema = z
  .object({
    type: z.enum(['timer', 'notification', 'money']),
    /** 0..1 scene progress at which it appears. */
    at: z.number().min(0).max(1).optional(),
    /** Seconds on screen. Omitted = until the scene ends. */
    hold: z.number().positive().optional(),
    position: z
      .enum(['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center', 'top', 'bottom'])
      .optional(),
    // timer
    seconds: z.number().positive().optional(),
    countUp: z.boolean().optional(),
    label: z.string().optional(),
    // notification
    appName: z.string().optional(),
    title: z.string().optional(),
    text: z.string().optional(),
    icon: z.string().optional(),
    // money
    amount: z.number().optional(),
    currency: z.string().optional(),
    sender: z.string().optional(),
  })
  .passthrough();

export const BaseSceneSchema = z
  .object({
    id: z.string().default('scene-1'),
    durationInFrames: z.number().int().positive(),
    preset: PresetTypeSchema.default('HeroKinetic'),
    title: z.string().optional(),
    subtitle: z.string().optional(),
    text: z.string().optional(),
    bodyText: z.string().optional(),
    accentColor: z.string().optional(),
    badge: z.string().optional(),
    style: z.string().optional(),
    // StatCounter
    statValue: z.number().optional(),
    statPrefix: z.string().optional(),
    statSuffix: z.string().optional(),
    statLabel: z.string().optional(),
    // SwipePanels / CompareSplit / ListReveal
    cards: z.array(CardSchema).optional(),
    // FlowDiagram
    nodes: z.array(NodeSchema).optional(),
    steps: z.array(StepSchema).optional(),
    // DonutFill
    segments: z.array(SegmentSchema).optional(),
    shape: z.enum(['donut', 'pie', 'ring', 'halfDonut']).optional(),
    thickness: z.number().positive().optional(),
    fillMode: z.enum(['fromOrigin', 'simultaneous', 'sequential', 'clockSweep']).optional(),
    centerContent: z.enum(['total', 'leader', 'label', 'empty']).optional(),
    labelPlacement: z.enum(['outside', 'legend', 'none']).optional(),
    percentCounters: z.boolean().optional(),
    gapAngle: z.number().min(0).max(30).optional(),
    highlightSegment: z.number().int().min(0).optional(),
    valueSuffix: z.string().optional(),
    // CodeReveal
    code: z.string().optional(),
    language: z.string().optional(),
    // UI mockup scenes (TgChat, AiChat, CryptoWallet, BankCard, ...)
    messages: z.array(ChatMessageSchema).optional(),
    /**
     * TgChat header identity. Separate from `title` on purpose: `title` is the
     * scene's own caption, and reusing it as the chat partner's name meant a
     * spec that set a caption also silently renamed the contact (and one that
     * set neither fell back to a hardcoded 'Аня'). `contactStatus` accepts ''
     * to render no status line at all.
     */
    contactName: z.string().optional(),
    contactStatus: z.string().optional(),
    /**
     * TgChat compose sequence: the message typed into the input field and sent
     * on camera. Absent = no input bar, no cursor (the original behaviour), so
     * existing specs are unaffected.
     */
    compose: z.string().optional(),
    /** false = the text is already in the field; only the send is animated. */
    typing: z.boolean().optional(),
    /** false = send without a mouse pointer (use for phone/finger framing). */
    showCursor: z.boolean().optional(),
    /** false = keep the typing but hide the input bar entirely. */
    showInputBar: z.boolean().optional(),
    /** 0..1 — when in the scene the send button is pressed. Default 0.72. */
    sendAtProgress: z.number().min(0).max(1).optional(),
    /** AiChatStream: the assistant reply that types out across the scene. */
    response: z.string().optional(),
    tokens: z.array(TokenRowSchema).optional(),
    transactions: z.array(TransactionSchema).optional(),
    balance: z.number().optional(),
    currency: z.string().optional(),
    /** Wallet/card address or number; masked by the scene, never shown whole. */
    address: z.string().optional(),
    // BankCard — the full number is deliberately not a field. Only the last
    // four digits are ever rendered, so a mockup cannot carry a real PAN.
    last4: z.string().optional(),
    holder: z.string().optional(),
    expiry: z.string().optional(),
    brand: z.string().optional(),
    // QuoteCard
    author: z.string().optional(),
    role: z.string().optional(),
    // 3D presets
    modelUrl: z.string().optional(),
    modelScale: z.number().optional(),
    orbitSpeed: z.number().optional(),
    orbit: z.enum(['full360', 'arc', 'figureEight', 'dolly']).optional(),
    orbitDegrees: z.number().optional(),
    startAngle: z.number().optional(),
    elevation: z.number().optional(),
    autoFrame: z.boolean().optional(),
    spinModel: z.boolean().optional(),
    lighting: z.enum(['studio', 'rim', 'dramatic', 'hdri', 'neon']).optional(),
    env: z.enum(['none', 'gradient', 'grid', 'hdri']).optional(),
    groundShadow: z.enum(['off', 'soft', 'contact']).optional(),
    material: z.enum(['original', 'clay', 'glass', 'wireframe', 'xray']).optional(),
    hotspots: z.array(HotspotSchema).optional(),
    audioUrl: z.string().optional(),
    // TokenCloud3D
    pointCount: z.number().int().positive().max(4000).optional(),
    // LayerStack3D
    layers: z.array(z.string()).optional(),
    // Motion + layout (see lib/motion.ts and lib/safeArea.ts)
    motion: MotionSpecSchema.optional(),
    /** Coarse motion control for weak agents. `motion` overrides it per channel. */
    intensity: IntensitySchema.optional(),
    safeArea: SafeAreaModeSchema.optional(),
    /**
     * Transition played BEFORE this scene (i.e. between the previous scene and
     * this one). Ignored on the first scene -- there is nothing to transition
     * from. Each transition shortens the total timeline by its own duration;
     * see lib/transitions.ts getTransitionPlan().
     */
    transition: TransitionSpecSchema.optional(),
    /**
     * Effects wrapped around this scene, applied outermost-first. Each entry
     * names an effect from the merged effects registry (entrance, exit,
     * emphasis, camera, grade, distortion, atmosphere) and carries its own
     * intensity; intensity 0 is a proven pixel-level no-op, so a disabled
     * effect costs nothing visually.
     */
    effects: z.array(SceneEffectSchema).optional(),
    /**
     * HUD elements drawn above this scene: countdown timers, notification
     * banners, money-credited toasts. Composes with ANY preset — that is the
     * point — and sits outside the effect stack so a camera shake or colour
     * grade does not move or tint the HUD.
     */
    overlays: z.array(OverlaySchema).optional(),
    // ---------------------------------------------------------------- media
    /** Image/video asset: a URL, or a path relative to remotion/public/. */
    src: z.string().optional(),
    /** ImageShowcase / ScreenRecord: several stills sharing the scene. */
    images: z.array(z.string()).optional(),
    fit: z.enum(['cover', 'contain']).optional(),
    /** ImageShowcase: false disables the slow scale+pan drift. */
    kenBurns: z.boolean().optional(),
    /** VideoEmbed: skip into the source clip, in frames. */
    startFrom: z.number().int().min(0).optional(),
    showControls: z.boolean().optional(),
    muted: z.boolean().optional(),
    /** ScreenRecord: window chrome style and the text in its address bar. */
    chrome: z.enum(['browser', 'window', 'none']).optional(),
    urlBar: z.string().optional(),
    appName: z.string().optional(),
    showRec: z.boolean().optional(),
    /** VoiceMemo: length in seconds, waveform shape seed, spoken text. */
    duration: z.number().positive().optional(),
    waveformSeed: z.number().optional(),
    transcript: z.string().optional(),
    // --------------------------------------------------------------- device
    /**
     * PhoneMockup: the preset rendered on the phone's screen, plus its props.
     * Deliberately NOT a PresetTypeSchema enum — the schema cannot import the
     * registry without a cycle, so an unknown name is reported at render time
     * inside the phone screen instead of failing validation.
     */
    innerPreset: z.string().optional(),
    innerProps: z.record(z.string(), z.unknown()).optional(),
    device: z.enum(['phone', 'tablet']).optional(),
    /** Idle Y-rotation in degrees. 0 = flat, editorial framing. */
    tilt: z.number().optional(),
    /** Internal recursion guard for nested mockups; callers leave it unset. */
    depth: z.number().int().min(0).optional(),
    // ---------------------------------------------------------------- audio
    trackTitle: z.string().optional(),
    artist: z.string().optional(),
    cover: z.string().optional(),
    /** VinylRecord: revolutions per minute (33, 45, 78) and spin toggle. */
    rpm: z.number().positive().optional(),
    spin: z.boolean().optional(),
    // --------------------------------------------------------------- charts
    /** RingStats: top of each ring's scale. Default 100. */
    ringMax: z.number().positive().optional(),
    /** Bars3D: extrusion depth in px. Defaults to a share of the bar width. */
    barDepth: z.number().min(0).optional(),
  })
  .passthrough();

export const VideoSpecSchema = z.object({
  width: z.number().int().default(1080),
  height: z.number().int().default(1920),
  fps: z.number().int().default(60),
  durationInFrames: z.number().int().optional(),
  format: VideoFormatSchema.default('vertical'),
  safeMargin: z.number().default(120),
  theme: ThemeSchema.default('pop'),
  /**
   * Style kit name — the video-wide visual language (palette + fonts + motion
   * character + backdrop + post-FX intent). See theme/styleKits.ts.
   *
   * Deliberately a plain string, not an enum: STYLE_KITS resolves unknown names
   * to the default instead of throwing, so adding a kit does not require a
   * schema change, and a typo degrades to the default look rather than failing
   * a whole render. A scene may override it with its own `style`.
   */
  style: z.string().optional(),
  brandColors: z
    .object({
      bg: z.string().default('#0E0F11'),
      surface: z.string().default('#16181C'),
      gold: z.string().default('#E6C475'),
      neon: z.string().default('#00FF88'),
      cyan: z.string().default('#00D4FF'),
      text: z.string().default('#FFFFFF'),
      muted: z.string().default('#8B92A0'),
    })
    .default({
      bg: '#0E0F11',
      surface: '#16181C',
      gold: '#E6C475',
      neon: '#00FF88',
      cyan: '#00D4FF',
      text: '#FFFFFF',
      muted: '#8B92A0',
    }),
  audioUrl: z.string().optional(),
  scenes: z.array(BaseSceneSchema).min(1),
});

export type BaseSceneProps = z.infer<typeof BaseSceneSchema>;
export type VideoSpec = z.infer<typeof VideoSpecSchema>;
export type Card = z.infer<typeof CardSchema>;
export type FlowNode = z.infer<typeof NodeSchema>;
export type FlowStep = z.infer<typeof StepSchema>;
