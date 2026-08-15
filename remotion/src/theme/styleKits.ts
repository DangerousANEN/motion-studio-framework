/**
 * Style kits: the visual language layer.
 *
 * WHY THIS IS SEPARATE FROM brand.ts
 * ----------------------------------
 * `brand.ts` conflates two independent things: a colour palette and a look.
 * A "style" is more than colours — it is palette + typography + motion
 * character + background texture + which post-effects are appropriate.
 * Splitting them means a new look costs one entry here instead of edits
 * scattered across every preset.
 *
 * The vision audit of v4 output named the palette specifically:
 * "muddy dark mode", "flat solid fills", "zero modern lighting tricks".
 * The kits below therefore carry explicit contrast and lighting intent
 * rather than leaving it to each preset to improvise.
 */
import type { Theme } from '../presets/brand';
import { THEMES } from '../presets/brand';

/** How movement should feel. Presets read this instead of hardcoding springs. */
export type MotionCharacter = {
  /** Spring config for primary entrances. */
  damping: number;
  stiffness: number;
  mass: number;
  /** Extra rotation applied to cards, in degrees. 0 = clean/editorial. */
  tilt: number;
  /** Multiplier on stagger between sibling elements. */
  staggerScale: number;
};

/** Background treatment behind scene content. */
export type BackdropKind =
  | 'grid'        // technical isometric grid (current Pop-Laboratory look)
  | 'mesh'        // animated gradient mesh — the "expensive" modern look
  | 'noise'       // organic drifting noise field
  | 'dots'        // dot matrix
  | 'scanlines'   // retro CRT
  | 'plain';      // flat, for maximum text contrast

/** Post-processing intent. Consumed by the PostFX wrapper in Phase 2. */
export type EffectProfile = {
  grain: number;        // 0..1 film grain opacity
  vignette: number;     // 0..1 edge darkening
  bloom: number;        // 0..1 glow around bright areas
  chromatic: number;    // 0..1 RGB split strength
  scanlines: number;    // 0..1 CRT line overlay
};

export type StyleKit = {
  name: string;
  description: string;
  /** Palette key into THEMES. */
  theme: string;
  /** Font kit key into FONT_KITS. */
  fonts: string;
  motion: MotionCharacter;
  backdrop: BackdropKind;
  effects: EffectProfile;
  /** Default transition between scenes for this style. */
  transition: string;
  /** Card/border treatment: brutalist hard shadows vs soft modern vs none. */
  surface: 'brutal' | 'soft' | 'glass' | 'flat';
};

const NO_FX: EffectProfile = { grain: 0, vignette: 0, bloom: 0, chromatic: 0, scanlines: 0 };

export const STYLE_KITS: Record<string, StyleKit> = {
  /**
   * The channel's signature look. Kept as default so existing videos do not
   * silently change identity — but with grain/vignette/bloom dialled in to
   * fix the "flat solid fills" complaint.
   */
  pop: {
    name: 'pop',
    description: 'Pop-Laboratory neo-brutalism: hard shadows, bold tilt, high energy.',
    theme: 'pop',
    fonts: 'pop',
    motion: { damping: 10, stiffness: 180, mass: 0.6, tilt: -2, staggerScale: 1 },
    backdrop: 'grid',
    effects: { grain: 0.05, vignette: 0.28, bloom: 0.35, chromatic: 0.12, scanlines: 0 },
    transition: 'slide',
    surface: 'brutal',
  },

  /** Calm, authoritative, text-first. For explainer and analysis content. */
  editorial: {
    name: 'editorial',
    description: 'Swiss editorial: generous whitespace, restrained motion, typographic hierarchy.',
    // `paper`, not `noir`: `clean` also used noir, and the two kits rendered
    // pixel-identical backdrops (measured distance 0.0).
    theme: 'paper',
    fonts: 'editorial',
    motion: { damping: 20, stiffness: 120, mass: 1, tilt: 0, staggerScale: 1.3 },
    backdrop: 'plain',
    effects: { grain: 0.04, vignette: 0.2, bloom: 0.1, chromatic: 0, scanlines: 0 },
    transition: 'fade',
    surface: 'flat',
  },

  /** Frosted panels over a luminous mesh — the modern "expensive" look. */
  glass: {
    name: 'glass',
    description: 'Glassmorphism: frosted surfaces, gradient mesh light, soft depth.',
    theme: 'glass',
    fonts: 'modern',
    motion: { damping: 16, stiffness: 140, mass: 0.9, tilt: 0, staggerScale: 1.15 },
    backdrop: 'mesh',
    effects: { grain: 0.03, vignette: 0.3, bloom: 0.55, chromatic: 0.08, scanlines: 0 },
    transition: 'dreamyZoom',
    surface: 'glass',
  },

  /** Cyan technical blueprint. For architecture and system diagrams. */
  blueprint: {
    name: 'blueprint',
    description: 'Technical blueprint: cyan grid, precise motion, diagram-friendly.',
    theme: 'blueprint',
    fonts: 'modern',
    motion: { damping: 18, stiffness: 150, mass: 0.8, tilt: 0, staggerScale: 1.1 },
    backdrop: 'grid',
    effects: { grain: 0.06, vignette: 0.32, bloom: 0.4, chromatic: 0.1, scanlines: 0.08 },
    transition: 'wipe',
    surface: 'soft',
  },

  /** High-contrast neon for release/announcement energy. */
  neon: {
    name: 'neon',
    description: 'Cyberpunk neon: saturated glow, aggressive motion, dark base.',
    theme: 'sunset',
    fonts: 'pop',
    motion: { damping: 9, stiffness: 200, mass: 0.55, tilt: -3, staggerScale: 0.85 },
    backdrop: 'noise',
    effects: { grain: 0.08, vignette: 0.35, bloom: 0.7, chromatic: 0.22, scanlines: 0.05 },
    transition: 'zoomBlur',
    surface: 'brutal',
  },

  /** LLM Hubs release look: technical near-black, neon green and readable motion. */
  llm_hubs_neon: {
    name: 'llm_hubs_neon',
    description: 'LLM Hubs: near-black glass, neon-green hierarchy, aqua data, readable release-safe motion.',
    theme: 'llm_hubs',
    fonts: 'modern',
    // Settled, overdamped entrances. Pace comes from cuts and sound design,
    // never from text wobble, looping tilt or chromatic jitter.
    motion: { damping: 24, stiffness: 115, mass: 0.85, tilt: 0, staggerScale: 1.0 },
    backdrop: 'grid',
    effects: { grain: 0.015, vignette: 0.32, bloom: 0.5, chromatic: 0, scanlines: 0 },
    transition: 'fade',
    surface: 'glass',
  },

  /** Product tutorial: calm technical UI, ideal for screen guides and click paths. */
  product_tutorial: {
    name: 'product_tutorial',
    description: 'Product tutorial: blueprint contrast, precise cursor-friendly guides and calm information pacing.',
    theme: 'blueprint',
    fonts: 'modern',
    motion: { damping: 22, stiffness: 120, mass: 0.95, tilt: 0, staggerScale: 1.15 },
    backdrop: 'grid',
    effects: { grain: 0.01, vignette: 0.18, bloom: 0.24, chromatic: 0, scanlines: 0 },
    transition: 'wipe',
    surface: 'soft',
  },

  /** Terminal / CLI demo: monospace hierarchy over a controlled dark grid. */
  terminal: {
    name: 'terminal',
    description: 'Terminal: lime command-line energy, precise code-first motion and restrained glow.',
    theme: 'cyber_lime',
    fonts: 'modern',
    motion: { damping: 20, stiffness: 135, mass: 0.9, tilt: 0, staggerScale: 0.95 },
    backdrop: 'dots',
    effects: { grain: 0.025, vignette: 0.34, bloom: 0.46, chromatic: 0, scanlines: 0 },
    transition: 'pushCut',
    surface: 'glass',
  },

  /** Creator / launch identity: luminous mesh and high-end glass media cards. */
  creator_glass: {
    name: 'creator_glass',
    description: 'Creator glass: cinematic mesh light, premium media framing and soft depth.',
    theme: 'glass',
    fonts: 'modern',
    motion: { damping: 18, stiffness: 135, mass: 0.9, tilt: 0, staggerScale: 1.05 },
    backdrop: 'mesh',
    effects: { grain: 0.02, vignette: 0.28, bloom: 0.6, chromatic: 0.035, scanlines: 0 },
    transition: 'dreamyZoom',
    surface: 'glass',
  },

  /** Platform-native social: compact UI hierarchy, clear cards and quiet effects. */
  social_native: {
    name: 'social_native',
    description: 'Social native: compact feed-like UI, clean hierarchy and subtle card interaction.',
    theme: 'steel',
    fonts: 'modern',
    motion: { damping: 21, stiffness: 125, mass: 0.95, tilt: 0, staggerScale: 1.1 },
    backdrop: 'plain',
    effects: { grain: 0, vignette: 0.12, bloom: 0.16, chromatic: 0, scanlines: 0 },
    transition: 'fade',
    surface: 'flat',
  },

  /** Condensed news-ticker urgency. For breaking-news style shorts. */
  news: {
    name: 'news',
    description: 'Broadcast news: condensed type, ticker motion, urgent pacing.',
    // `broadcast`, not `pop`: sharing pop's palette made the two kits render a
    // combined bg+accent distance of 0.8 — indistinguishable.
    theme: 'broadcast',
    fonts: 'news',
    motion: { damping: 14, stiffness: 190, mass: 0.65, tilt: 0, staggerScale: 0.8 },
    // `dots`: the kind was implemented in Backdrop.tsx but no kit referenced it,
    // so it was unreachable. A dot matrix suits a ticker/news look and gives
    // `news` its own texture instead of duplicating `editorial`'s plain wash.
    backdrop: 'dots',
    effects: { grain: 0.05, vignette: 0.25, bloom: 0.25, chromatic: 0.06, scanlines: 0 },
    transition: 'pushCut',
    surface: 'flat',
  },

  /** Retro CRT/VHS. Deliberately lo-fi. */
  retro: {
    name: 'retro',
    description: 'Retro CRT: scanlines, chromatic fringing, analogue warmth.',
    // `vhs`, not `sunset`: `neon` also used sunset and the pair was
    // indistinguishable in a rendered frame.
    theme: 'vhs',
    fonts: 'poster',
    motion: { damping: 12, stiffness: 160, mass: 0.7, tilt: -1.5, staggerScale: 1 },
    backdrop: 'scanlines',
    effects: { grain: 0.16, vignette: 0.45, bloom: 0.3, chromatic: 0.3, scanlines: 0.35 },
    transition: 'filmBurn',
    surface: 'brutal',
  },

  /** Maximum legibility, minimum decoration. Accessibility-first fallback. */
  clean: {
    name: 'clean',
    description: 'Maximum contrast, no decoration. Safest for dense information.',
    theme: 'ink',
    fonts: 'modern',
    motion: { damping: 22, stiffness: 130, mass: 1, tilt: 0, staggerScale: 1.2 },
    backdrop: 'plain',
    effects: NO_FX,
    transition: 'fade',
    surface: 'flat',
  },

  // ─── Шесть новых китов ────────────────────────────────────────────────────

  /**
   * «Рассвет» — тёплый оптимистичный. Мотивационный и лайфстайл контент.
   * Глубокий янтарный фон, оранжевые акценты, плавное движение.
   */
  sunrise: {
    name: 'sunrise',
    description: 'Восход: оранжево-золотые акценты, тёплый янтарный фон, плавное мотивационное движение.',
    theme: 'sunrise',
    fonts: 'editorial',
    motion: { damping: 18, stiffness: 130, mass: 0.85, tilt: 0.5, staggerScale: 1.2 },
    backdrop: 'mesh',
    effects: { grain: 0.04, vignette: 0.22, bloom: 0.5, chromatic: 0.04, scanlines: 0 },
    transition: 'dreamyZoom',
    surface: 'soft',
  },

  /**
   * «Лес» — спокойный изумрудный. Эко, здоровье, медленный вдумчивый контент.
   * Глубокий зелёный фон, живые мятные акценты, slow-motion.
   */
  forest: {
    name: 'forest',
    description: 'Лес: изумрудный фон, мятно-бирюзовые акценты, органичное медленное движение.',
    theme: 'forest',
    fonts: 'modern',
    motion: { damping: 24, stiffness: 100, mass: 1.1, tilt: 0, staggerScale: 1.4 },
    backdrop: 'noise',
    effects: { grain: 0.07, vignette: 0.3, bloom: 0.3, chromatic: 0.02, scanlines: 0 },
    transition: 'fade',
    surface: 'soft',
  },

  /**
   * «Монохром» — тёплая сепия, документальный и исторический тон.
   * Кофейно-тёмный фон, охровые акценты, тяжёлая неспешная типографика.
   */
  mono_warm: {
    name: 'mono_warm',
    description: 'Монохром-тепло: сепийный фон, охровые акценты, документальный нарратив.',
    theme: 'mono_warm',
    fonts: 'poster',
    motion: { damping: 26, stiffness: 110, mass: 1.2, tilt: 0, staggerScale: 1.5 },
    backdrop: 'plain',
    effects: { grain: 0.14, vignette: 0.4, bloom: 0.08, chromatic: 0, scanlines: 0 },
    transition: 'fade',
    surface: 'flat',
  },

  /**
   * «Кибер-лайм» — максимальная энергия, тех-хайп, гейминг.
   * Почти чёрный фон, кислотный лайм + пурпур, агрессивный наклон.
   */
  cyber_lime: {
    name: 'cyber_lime',
    description: 'Кибер-лайм: кислотный лайм + магента, максимальная энергия, гейминг-эстетика.',
    theme: 'cyber_lime',
    fonts: 'pop',
    motion: { damping: 8, stiffness: 220, mass: 0.5, tilt: -3.5, staggerScale: 0.75 },
    backdrop: 'grid',
    effects: { grain: 0.06, vignette: 0.3, bloom: 0.8, chromatic: 0.28, scanlines: 0.04 },
    transition: 'zoomBlur',
    surface: 'brutal',
  },

  /**
   * «Конфета» — пастельный поп. Детский, развлекательный, лёгкий контент.
   * Тёмный ягодный фон, розовые и лавандовые акценты, мягкое игривое движение.
   */
  candy: {
    name: 'candy',
    description: 'Конфета: розово-лавандовые акценты на тёмном ягодном фоне, лёгкое игривое настроение.',
    theme: 'candy',
    fonts: 'modern',
    motion: { damping: 12, stiffness: 160, mass: 0.7, tilt: 1, staggerScale: 1.0 },
    backdrop: 'dots',
    effects: { grain: 0.03, vignette: 0.2, bloom: 0.6, chromatic: 0.1, scanlines: 0 },
    transition: 'slide',
    surface: 'glass',
  },

  /**
   * «Сталь» — промышленный холодный. B2B, инженерия, серьёзный тон.
   * Тёмно-стальной фон, холодные синие акценты, строгое прямое движение.
   */
  steel: {
    name: 'steel',
    description: 'Сталь: холодный стальной синий, промышленный тон, строгая B2B-эстетика.',
    theme: 'steel',
    fonts: 'news',
    motion: { damping: 20, stiffness: 155, mass: 0.9, tilt: 0, staggerScale: 1.1 },
    backdrop: 'grid',
    effects: { grain: 0.05, vignette: 0.35, bloom: 0.2, chromatic: 0.05, scanlines: 0.06 },
    transition: 'wipe',
    surface: 'soft',
  },

  aurora_flux: { name: 'aurora_flux', description: 'Aurora flux: teal-violet luminous mesh for premium launches and abstract technology.', theme: 'aurora_flux', fonts: 'modern', motion: { damping: 19, stiffness: 128, mass: 0.9, tilt: 0, staggerScale: 1.08 }, backdrop: 'mesh', effects: { grain: 0.02, vignette: 0.27, bloom: 0.68, chromatic: 0.025, scanlines: 0 }, transition: 'dreamyZoom', surface: 'glass' },
  cobalt_command: { name: 'cobalt_command', description: 'Cobalt command: controlled enterprise blue for B2B systems, data and browser tours.', theme: 'cobalt_command', fonts: 'modern', motion: { damping: 23, stiffness: 120, mass: 1, tilt: 0, staggerScale: 1.18 }, backdrop: 'grid', effects: { grain: 0.015, vignette: 0.24, bloom: 0.28, chromatic: 0, scanlines: 0 }, transition: 'wipe', surface: 'soft' },
  infrared_alert: { name: 'infrared_alert', description: 'Infrared alert: red breaking-update hierarchy for release windows, changes and deadlines.', theme: 'infrared_alert', fonts: 'news', motion: { damping: 16, stiffness: 175, mass: 0.7, tilt: 0, staggerScale: 0.82 }, backdrop: 'dots', effects: { grain: 0.045, vignette: 0.34, bloom: 0.52, chromatic: 0.05, scanlines: 0 }, transition: 'pushCut', surface: 'flat' },
  violet_luxe: { name: 'violet_luxe', description: 'Violet luxe: cinematic violet and ice glass for premium creator narratives.', theme: 'violet_luxe', fonts: 'editorial', motion: { damping: 20, stiffness: 116, mass: 1, tilt: 0, staggerScale: 1.2 }, backdrop: 'mesh', effects: { grain: 0.028, vignette: 0.35, bloom: 0.58, chromatic: 0.02, scanlines: 0 }, transition: 'dreamyZoom', surface: 'glass' },
  porcelain: { name: 'porcelain', description: 'Porcelain: light high-legibility educational surface with calm ink typography.', theme: 'porcelain', fonts: 'editorial', motion: { damping: 25, stiffness: 105, mass: 1.08, tilt: 0, staggerScale: 1.25 }, backdrop: 'plain', effects: { grain: 0.01, vignette: 0.03, bloom: 0, chromatic: 0, scanlines: 0 }, transition: 'fade', surface: 'flat' },
  liquid_chrome: { name: 'liquid_chrome', description: 'Liquid chrome: graphite and cyan reflective product-reveal surfaces.', theme: 'liquid_chrome', fonts: 'modern', motion: { damping: 18, stiffness: 142, mass: 0.85, tilt: 0.5, staggerScale: 1.0 }, backdrop: 'mesh', effects: { grain: 0.035, vignette: 0.38, bloom: 0.62, chromatic: 0.04, scanlines: 0 }, transition: 'zoomBlur', surface: 'glass' },
  kinetic_poster: { name: 'kinetic_poster', description: 'Kinetic poster: acid poster-scale hooks with brutal high-contrast panels.', theme: 'kinetic_poster', fonts: 'poster', motion: { damping: 19, stiffness: 165, mass: 0.72, tilt: -0.8, staggerScale: 0.84 }, backdrop: 'plain', effects: { grain: 0.035, vignette: 0.3, bloom: 0.35, chromatic: 0, scanlines: 0 }, transition: 'pushCut', surface: 'brutal' },
  midnight_orbit: { name: 'midnight_orbit', description: 'Midnight orbit: navy orbital depth for model ecosystems, research and roadmaps.', theme: 'midnight_orbit', fonts: 'modern', motion: { damping: 24, stiffness: 110, mass: 1.05, tilt: 0, staggerScale: 1.25 }, backdrop: 'noise', effects: { grain: 0.022, vignette: 0.4, bloom: 0.48, chromatic: 0.015, scanlines: 0 }, transition: 'fade', surface: 'glass' },
  pixel_arcade: { name: 'pixel_arcade', description: 'Pixel arcade: playful lime-purple challenge and onboarding language.', theme: 'pixel_arcade', fonts: 'pop', motion: { damping: 17, stiffness: 170, mass: 0.72, tilt: -1.2, staggerScale: 0.9 }, backdrop: 'dots', effects: { grain: 0.04, vignette: 0.31, bloom: 0.58, chromatic: 0.08, scanlines: 0.08 }, transition: 'slide', surface: 'brutal' },
  coral_creator: { name: 'coral_creator', description: 'Coral creator: warm social storytelling cards with soft creator energy.', theme: 'coral_creator', fonts: 'modern', motion: { damping: 21, stiffness: 126, mass: 0.95, tilt: 0, staggerScale: 1.1 }, backdrop: 'noise', effects: { grain: 0.025, vignette: 0.26, bloom: 0.48, chromatic: 0.015, scanlines: 0 }, transition: 'dreamyZoom', surface: 'soft' },
};

export const DEFAULT_STYLE_KIT = 'pop';

export const getStyleKit = (name?: string): StyleKit =>
  STYLE_KITS[name ?? DEFAULT_STYLE_KIT] ?? STYLE_KITS[DEFAULT_STYLE_KIT];

/** Resolve the palette a style kit points at. */
export const getStyleTheme = (kit: StyleKit): Theme => THEMES[kit.theme] ?? THEMES.pop;

export const STYLE_KIT_NAMES = Object.keys(STYLE_KITS);
