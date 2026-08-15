/**
 * Visual effects registry — 2.4 Camera (12) + 2.5 Colour/grade (14) + 2.6 Distortion (14)
 *
 * Exported as VISUAL_EFFECTS with the same shape as effects.ts:
 *   { component, family, summary, stochastic }
 *
 * This file is owned by the visual-effects author. Do NOT merge with effects.ts.
 * The local EffectEntry interface is a deliberate duplicate to avoid merge conflicts.
 */

// Camera effects
import {
  ZoomPunch,
  ZoomSlow,
  PanLeft,
  PanRight,
  DollyIn,
  DollyOut,
  HandheldDrift,
  WhipPan,
  RackFocus,
  ParallaxLayers,
  OrbitAround,
  TiltShift,
} from '../fx/effects/camera';

// Colour / grade effects
import {
  Vignette,
  FilmGrain,
  ChromaticAberration,
  Bloom,
  ColorGradeWarm,
  ColorGradeCool,
  Duotone,
  Invert,
  Saturate,
  Desaturate,
  Contrast,
  Posterize,
  HalationGlow,
  LightLeak,
} from '../fx/effects/grade';

// Distortion effects
import {
  GlitchRgb,
  GlitchBlock,
  ScanLines,
  CrtCurve,
  VhsTracking,
  WaveWarp,
  RippleDistort,
  LensDistort,
  PixelSort,
  Displace,
  MotionBlurTrail,
  EchoTrail,
  Kaleidoscope,
  MirrorSplit,
} from '../fx/effects/distort';

// Studio effects
import { FocusPulse } from '../fx/effects/studio';

import React from 'react';

// ---------------------------------------------------------------------------
// Local EffectEntry — duplicate of the shape in effects.ts (deliberate, to
// avoid merge conflicts when two agents work on different files).
// ---------------------------------------------------------------------------
interface EffectEntry {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  component: React.FC<any>;
  family: 'camera' | 'grade' | 'distortion';
  summary: string;
  /** true if the component uses seeded randomness */
  stochastic: boolean;
}

export const VISUAL_EFFECTS: Record<string, EffectEntry> = {
  FocusPulse: {
    component: FocusPulse,
    family: 'grade',
    summary: 'Subtle deterministic centre glow that emphasizes a key reveal without moving layout.',
    stochastic: false,
  },
  // ── 2.4  Camera ────────────────────────────────────────────────────────
  ZoomPunch: {
    component: ZoomPunch,
    family: 'camera',
    summary: 'Fast zoom-in spike then ease back — adds punch to beat hits.',
    stochastic: false,
  },
  ZoomSlow: {
    component: ZoomSlow,
    family: 'camera',
    summary: 'Gentle continuous zoom-in across the clip duration.',
    stochastic: false,
  },
  PanLeft: {
    component: PanLeft,
    family: 'camera',
    summary: 'Continuous camera pan to the left (content shifts right → left).',
    stochastic: false,
  },
  PanRight: {
    component: PanRight,
    family: 'camera',
    summary: 'Continuous camera pan to the right (content shifts left → right).',
    stochastic: false,
  },
  DollyIn: {
    component: DollyIn,
    family: 'camera',
    summary: 'Progressive zoom toward the camera — classic dolly-in move.',
    stochastic: false,
  },
  DollyOut: {
    component: DollyOut,
    family: 'camera',
    summary: 'Progressive zoom away from the camera — classic dolly-out move.',
    stochastic: false,
  },
  HandheldDrift: {
    component: HandheldDrift,
    family: 'camera',
    summary: 'Organic handheld shake using seeded low-frequency noise.',
    stochastic: true,
  },
  WhipPan: {
    component: WhipPan,
    family: 'camera',
    summary: 'Fast horizontal whip-pan with motion blur at the apex.',
    stochastic: false,
  },
  RackFocus: {
    component: RackFocus,
    family: 'camera',
    summary: 'Blur-in → sharp → blur-out simulating a rack-focus pull.',
    stochastic: false,
  },
  ParallaxLayers: {
    component: ParallaxLayers,
    family: 'camera',
    summary: 'Subtle oscillating offset to simulate multi-layer depth parallax.',
    stochastic: false,
  },
  OrbitAround: {
    component: OrbitAround,
    family: 'camera',
    summary: 'Slow elliptical orbit panning around the content centre.',
    stochastic: false,
  },
  TiltShift: {
    component: TiltShift,
    family: 'camera',
    summary: 'Miniature-world tilt-shift: sharp centre band, blurred top/bottom.',
    stochastic: false,
  },

  // ── 2.5  Colour / grade ────────────────────────────────────────────────
  Vignette: {
    component: Vignette,
    family: 'grade',
    summary: 'Radial edge darkening to focus the eye on the centre.',
    stochastic: false,
  },
  FilmGrain: {
    component: FilmGrain,
    family: 'grade',
    summary: 'Organic per-frame seeded noise grain (mulberry32-driven).',
    stochastic: true,
  },
  ChromaticAberration: {
    component: ChromaticAberration,
    family: 'grade',
    summary: 'RGB channel split via SVG colour matrices for lens fringing.',
    stochastic: false,
  },
  Bloom: {
    component: Bloom,
    family: 'grade',
    summary: 'Screen-blended blurred copy of content for glow bloom.',
    stochastic: false,
  },
  ColorGradeWarm: {
    component: ColorGradeWarm,
    family: 'grade',
    summary: 'Warm orange/amber colour grade overlay.',
    stochastic: false,
  },
  ColorGradeCool: {
    component: ColorGradeCool,
    family: 'grade',
    summary: 'Cool cyan/blue colour grade overlay.',
    stochastic: false,
  },
  Duotone: {
    component: Duotone,
    family: 'grade',
    summary: 'Two-colour tone map from shadow colour to highlight colour.',
    stochastic: false,
  },
  Invert: {
    component: Invert,
    family: 'grade',
    summary: 'CSS invert filter — full or partial colour inversion.',
    stochastic: false,
  },
  Saturate: {
    component: Saturate,
    family: 'grade',
    summary: 'Boost colour saturation beyond natural for vibrant look.',
    stochastic: false,
  },
  Desaturate: {
    component: Desaturate,
    family: 'grade',
    summary: 'Drain colour saturation toward greyscale.',
    stochastic: false,
  },
  Contrast: {
    component: Contrast,
    family: 'grade',
    summary: 'Increase contrast via CSS contrast() filter.',
    stochastic: false,
  },
  Posterize: {
    component: Posterize,
    family: 'grade',
    summary: 'Discrete colour steps via SVG feComponentTransfer for poster effect.',
    stochastic: false,
  },
  HalationGlow: {
    component: HalationGlow,
    family: 'grade',
    summary: 'Warm red glow bleeding from bright areas — film halation look.',
    stochastic: false,
  },
  LightLeak: {
    component: LightLeak,
    family: 'grade',
    summary: 'Animated warm light sweep across the frame (seeded sweep origin).',
    stochastic: true,
  },

  // ── 2.6  Distortion ───────────────────────────────────────────────────
  GlitchRgb: {
    component: GlitchRgb,
    family: 'distortion',
    summary: 'Per-frame seeded random RGB channel offset (mulberry32).',
    stochastic: true,
  },
  GlitchBlock: {
    component: GlitchBlock,
    family: 'distortion',
    summary: 'Random rectangular slices shifted horizontally (seeded per frame).',
    stochastic: true,
  },
  ScanLines: {
    component: ScanLines,
    family: 'distortion',
    summary: 'CRT horizontal scan-line overlay at configurable line gap.',
    stochastic: false,
  },
  CrtCurve: {
    component: CrtCurve,
    family: 'distortion',
    summary: 'Barrel distortion and rounded corners simulating a CRT screen.',
    stochastic: false,
  },
  VhsTracking: {
    component: VhsTracking,
    family: 'distortion',
    summary: 'VHS tracking-error band: random horizontal slice shift (seeded).',
    stochastic: true,
  },
  WaveWarp: {
    component: WaveWarp,
    family: 'distortion',
    summary: 'Horizontal sine-wave distortion via SVG feDisplacementMap.',
    stochastic: false,
  },
  RippleDistort: {
    component: RippleDistort,
    family: 'distortion',
    summary: 'Concentric water-ripple distortion via animated SVG turbulence.',
    stochastic: false,
  },
  LensDistort: {
    component: LensDistort,
    family: 'distortion',
    summary: 'Barrel lens distortion via SVG displacement map.',
    stochastic: false,
  },
  PixelSort: {
    component: PixelSort,
    family: 'distortion',
    summary: 'Column-based vertical pixel-sort artefact (seeded, deterministic).',
    stochastic: true,
  },
  Displace: {
    component: Displace,
    family: 'distortion',
    summary: 'SVG turbulence-based displacement for organic warping (seeded).',
    stochastic: true,
  },
  MotionBlurTrail: {
    component: MotionBlurTrail,
    family: 'distortion',
    summary: 'Directional motion-blur trail ghost copies at configurable angle.',
    stochastic: false,
  },
  EchoTrail: {
    component: EchoTrail,
    family: 'distortion',
    summary: 'Fading after-image echo trail offset horizontally.',
    stochastic: false,
  },
  Kaleidoscope: {
    component: Kaleidoscope,
    family: 'distortion',
    summary: '4-way mirror rotation creating a kaleidoscope mandala effect.',
    stochastic: false,
  },
  MirrorSplit: {
    component: MirrorSplit,
    family: 'distortion',
    summary: 'Mirror the frame on the horizontal or vertical axis.',
    stochastic: false,
  },
};
