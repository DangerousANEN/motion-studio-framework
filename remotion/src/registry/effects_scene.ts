/**
 * Scene-effects registry — Section 2.7 Overlay/atmosphere (12) and
 * 2.8 Transitions between scenes (12) of the MSF Expansion Plan.
 *
 * DO NOT EDIT the other two effect registry files (effects.ts / effects_visual.ts).
 * This file is owned by the scene-effects author and exports two named registries:
 *   SCENE_EFFECTS   — atmosphere/overlay wrappers
 *   TRANSITIONS     — scene-to-scene transition components
 *
 * EffectProps is declared locally; do not import from a shared location.
 */
import React from 'react';

import {
  ParticlesDust,
  ParticlesSnow,
  ParticlesSparks,
  Confetti,
  RainStreaks,
  SmokeWisps,
  NoiseOverlay,
  GridOverlay,
  ScanSweep,
  SpotlightFollow,
  CausticsLight,
  BokehLights,
} from '../fx/effects/overlay';

import {
  CutHard,
  CrossFade,
  WipeLinear,
  WipeCircle,
  SlidePush,
  ZoomBlurTransition,
  GlitchTransition,
  WhipPanTransition,
  MorphShape,
  LiquidWarp,
  FilmBurn,
  LightFlashCut,
} from '../fx/transitions/index';

// ---------------------------------------------------------------------------
// Local EffectProps — mirrors the contract in overlay.tsx
// ---------------------------------------------------------------------------
export interface EffectProps {
  children: React.ReactNode;
  intensity?: number;
  seed?: number;
}

// ---------------------------------------------------------------------------
// Local TransitionProps — mirrors the contract in transitions/index.tsx
// ---------------------------------------------------------------------------
export interface SceneTransitionProps {
  progress: number;
  from: React.ReactNode;
  to: React.ReactNode;
  seed?: number;
}

// ---------------------------------------------------------------------------
// OverlayDefinition — metadata for each atmosphere overlay
// ---------------------------------------------------------------------------
export interface OverlayDefinition {
  component: React.FC<EffectProps>;
  summary: string;
  stochastic: boolean;
  /** intensity=0 must be a pixel-perfect no-op */
  noOpAtZero: true;
}

// ---------------------------------------------------------------------------
// TransitionDefinition — metadata for each scene transition
// ---------------------------------------------------------------------------
export interface TransitionDefinition {
  component: React.FC<SceneTransitionProps>;
  summary: string;
  /** progress=0 → from only; progress=1 → to only */
  identityAtEndpoints: true;
}

// ---------------------------------------------------------------------------
// SCENE_EFFECTS — 12 atmosphere overlays (Section 2.7)
// ---------------------------------------------------------------------------
export const SCENE_EFFECTS: Record<string, OverlayDefinition> = {
  ParticlesDust: {
    component: ParticlesDust,
    summary: 'Floating dust motes drifting across the scene deterministically.',
    stochastic: true,
    noOpAtZero: true,
  },
  ParticlesSnow: {
    component: ParticlesSnow,
    summary: 'Snowflakes falling at varying speeds and sizes.',
    stochastic: true,
    noOpAtZero: true,
  },
  ParticlesSparks: {
    component: ParticlesSparks,
    summary: 'Orange spark trails rising and fading.',
    stochastic: true,
    noOpAtZero: true,
  },
  Confetti: {
    component: Confetti,
    summary: 'Multicolour confetti rectangles tumbling downward.',
    stochastic: true,
    noOpAtZero: true,
  },
  RainStreaks: {
    component: RainStreaks,
    summary: 'Diagonal rain streaks falling across the screen.',
    stochastic: true,
    noOpAtZero: true,
  },
  SmokeWisps: {
    component: SmokeWisps,
    summary: 'Soft blurred smoke ellipses drifting upward.',
    stochastic: true,
    noOpAtZero: true,
  },
  NoiseOverlay: {
    component: NoiseOverlay,
    summary: 'Animated film-grain noise overlay via SVG feTurbulence.',
    stochastic: true,
    noOpAtZero: true,
  },
  GridOverlay: {
    component: GridOverlay,
    summary: 'Fine grid lines over the scene.',
    stochastic: false,
    noOpAtZero: true,
  },
  ScanSweep: {
    component: ScanSweep,
    summary: 'Horizontal luminous scan-bar sweeping top-to-bottom periodically.',
    stochastic: false,
    noOpAtZero: true,
  },
  SpotlightFollow: {
    component: SpotlightFollow,
    summary: 'A warm spotlight following a slow Lissajous path.',
    stochastic: false,
    noOpAtZero: true,
  },
  CausticsLight: {
    component: CausticsLight,
    summary: 'Caustic light blobs screened over the scene.',
    stochastic: true,
    noOpAtZero: true,
  },
  BokehLights: {
    component: BokehLights,
    summary: 'Soft out-of-focus bokeh circles floating gently.',
    stochastic: true,
    noOpAtZero: true,
  },
};

// ---------------------------------------------------------------------------
// TRANSITIONS — 12 scene transitions (Section 2.8)
// ---------------------------------------------------------------------------
export const TRANSITIONS: Record<string, TransitionDefinition> = {
  CutHard: {
    component: CutHard,
    summary: 'Instantaneous hard cut at the midpoint.',
    identityAtEndpoints: true,
  },
  CrossFade: {
    component: CrossFade,
    summary: 'Linear opacity cross-dissolve between scenes.',
    identityAtEndpoints: true,
  },
  WipeLinear: {
    component: WipeLinear,
    summary: 'Left-to-right wipe clip transition.',
    identityAtEndpoints: true,
  },
  WipeCircle: {
    component: WipeCircle,
    summary: 'Circular iris wipe expanding from the centre.',
    identityAtEndpoints: true,
  },
  SlidePush: {
    component: SlidePush,
    summary: 'Outgoing scene pushed off left by incoming from right.',
    identityAtEndpoints: true,
  },
  ZoomBlurTransition: {
    component: ZoomBlurTransition,
    summary: 'From zooms in with blur; to zooms in from large.',
    identityAtEndpoints: true,
  },
  GlitchTransition: {
    component: GlitchTransition,
    summary: 'RGB-split glitch with seeded horizontal offsets.',
    identityAtEndpoints: true,
  },
  WhipPanTransition: {
    component: WhipPanTransition,
    summary: 'Fast horizontal motion-blur pan cut.',
    identityAtEndpoints: true,
  },
  MorphShape: {
    component: MorphShape,
    summary: 'Rounded-rect mask morphing to reveal the next scene.',
    identityAtEndpoints: true,
  },
  LiquidWarp: {
    component: LiquidWarp,
    summary: 'Turbulence-displacement liquid warp dissolve.',
    identityAtEndpoints: true,
  },
  FilmBurn: {
    component: FilmBurn,
    summary: 'Orange film-burn circle expanding from centre with flare.',
    identityAtEndpoints: true,
  },
  LightFlashCut: {
    component: LightFlashCut,
    summary: 'White flash peaks at midpoint then cuts to incoming scene.',
    identityAtEndpoints: true,
  },
};

// Convenience: all 24 names in one list for audit probes
export const SCENE_EFFECT_NAMES = Object.keys(SCENE_EFFECTS).sort();
export const TRANSITION_NAMES = Object.keys(TRANSITIONS).sort();
