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
};

export const DEFAULT_STYLE_KIT = 'pop';

export const getStyleKit = (name?: string): StyleKit =>
  STYLE_KITS[name ?? DEFAULT_STYLE_KIT] ?? STYLE_KITS[DEFAULT_STYLE_KIT];

/** Resolve the palette a style kit points at. */
export const getStyleTheme = (kit: StyleKit): Theme => THEMES[kit.theme] ?? THEMES.pop;

export const STYLE_KIT_NAMES = Object.keys(STYLE_KITS);
