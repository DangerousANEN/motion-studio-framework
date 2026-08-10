/**
 * Effects registry — 44 entrance/exit/emphasis effects.
 *
 * Contract (from EXPANSION_PLAN.md §2):
 *
 *   export interface EffectProps {
 *     children: React.ReactNode;
 *     intensity?: number;   // 0..1, 1 = preset default
 *     seed?: number;        // required when stochastic=true
 *   }
 *
 * intensity=0 MUST be a pixel-perfect no-op. A stochastic effect MUST take
 * `seed` and use mulberry32 — never Math.random().
 *
 * Registry shape mirrors PresetRegistry from registry/types.ts:
 *   name → { component, family, summary, stochastic }
 *
 * mergeEffectRegistries() throws on duplicates, same guard as presets.
 */
import React from 'react';

// --------------- EffectProps contract ----------------------------------------

export interface EffectProps {
  children: React.ReactNode;
  /** 0..1; 1 = full-strength preset default. intensity=0 is a strict no-op. */
  intensity?: number;
  /** Required when stochastic=true. Use mulberry32(seed) — never Math.random(). */
  seed?: number;
}

// --------------- Registry types ----------------------------------------------

export type EffectFamily = 'entrance' | 'exit' | 'emphasis';

export interface EffectDefinition {
  component: React.FC<EffectProps>;
  family: EffectFamily;
  summary: string;
  /** true → component uses seeded PRNG; caller should pass seed for reproducibility. */
  stochastic: boolean;
}

export type EffectRegistry = Record<string, EffectDefinition>;

/** Merge helper — throws on duplicate names across packs. */
export const mergeEffectRegistries = (...packs: EffectRegistry[]): EffectRegistry => {
  const out: EffectRegistry = {};
  for (const pack of packs) {
    for (const [name, def] of Object.entries(pack)) {
      if (out[name]) {
        throw new Error(
          `Duplicate effect name "${name}". Two packs declare it; rename one.`
        );
      }
      out[name] = def;
    }
  }
  return out;
};

// --------------- Import components -------------------------------------------

import {
  FadeIn,
  SlideInLeft,
  SlideInRight,
  SlideInUp,
  SlideInDown,
  ScaleIn,
  ScaleInBounce,
  RotateIn,
  FlipInX,
  FlipInY,
  BlurIn,
  ClipWipeIn,
  MaskCircleIn,
  TypeIn,
  StaggerChildren,
  ElasticPop,
} from '../fx/effects/entrance';

import {
  FadeOut,
  SlideOutLeft,
  SlideOutRight,
  SlideOutUp,
  SlideOutDown,
  ScaleOut,
  RotateOut,
  BlurOut,
  ClipWipeOut,
  MaskCircleOut,
  ShatterOut,
  DissolveOut,
} from '../fx/effects/exit';

import {
  Pulse,
  Breathe,
  Shake,
  Wobble,
  Jitter,
  Bounce,
  Float,
  Swing,
  HeartBeat,
  Flash,
  Glow,
  Shimmer,
  Sheen,
  Ripple,
  Tremble,
  Squash,
} from '../fx/effects/emphasis';

// --------------- Entrance pack (16) ------------------------------------------

const ENTRANCE_EFFECTS: EffectRegistry = {
  FadeIn: {
    component: FadeIn,
    family: 'entrance',
    summary: 'Children fade in from transparent to opaque over the entrance window.',
    stochastic: false,
  },
  SlideInLeft: {
    component: SlideInLeft,
    family: 'entrance',
    summary: 'Children slide in from the left edge of the frame.',
    stochastic: false,
  },
  SlideInRight: {
    component: SlideInRight,
    family: 'entrance',
    summary: 'Children slide in from the right edge of the frame.',
    stochastic: false,
  },
  SlideInUp: {
    component: SlideInUp,
    family: 'entrance',
    summary: 'Children slide in from the top edge of the frame.',
    stochastic: false,
  },
  SlideInDown: {
    component: SlideInDown,
    family: 'entrance',
    summary: 'Children slide in from the bottom edge of the frame.',
    stochastic: false,
  },
  ScaleIn: {
    component: ScaleIn,
    family: 'entrance',
    summary: 'Children scale up from zero to full size at the entrance.',
    stochastic: false,
  },
  ScaleInBounce: {
    component: ScaleInBounce,
    family: 'entrance',
    summary: 'Children scale in with a spring bounce overshoot.',
    stochastic: false,
  },
  RotateIn: {
    component: RotateIn,
    family: 'entrance',
    summary: 'Children rotate in from −90° while fading from transparent.',
    stochastic: false,
  },
  FlipInX: {
    component: FlipInX,
    family: 'entrance',
    summary: 'Children flip in around the horizontal (X) axis with perspective.',
    stochastic: false,
  },
  FlipInY: {
    component: FlipInY,
    family: 'entrance',
    summary: 'Children flip in around the vertical (Y) axis with perspective.',
    stochastic: false,
  },
  BlurIn: {
    component: BlurIn,
    family: 'entrance',
    summary: 'Children focus in from a heavy blur to sharp while fading in.',
    stochastic: false,
  },
  ClipWipeIn: {
    component: ClipWipeIn,
    family: 'entrance',
    summary: 'Children are revealed by a left-to-right clip-path wipe.',
    stochastic: false,
  },
  MaskCircleIn: {
    component: MaskCircleIn,
    family: 'entrance',
    summary: 'Children are revealed by a circular mask expanding from the centre.',
    stochastic: false,
  },
  TypeIn: {
    component: TypeIn,
    family: 'entrance',
    summary: 'Children are unveiled left-to-right as if being typed on screen.',
    stochastic: false,
  },
  StaggerChildren: {
    component: StaggerChildren,
    family: 'entrance',
    summary: 'Each direct child fades and slides up with a cascading delay.',
    stochastic: true,
  },
  ElasticPop: {
    component: ElasticPop,
    family: 'entrance',
    summary: 'Children spring-pop in with elastic overshoot on scale.',
    stochastic: false,
  },
};

// --------------- Exit pack (12) ----------------------------------------------

const EXIT_EFFECTS: EffectRegistry = {
  FadeOut: {
    component: FadeOut,
    family: 'exit',
    summary: 'Children fade out to transparent at the end of their duration.',
    stochastic: false,
  },
  SlideOutLeft: {
    component: SlideOutLeft,
    family: 'exit',
    summary: 'Children slide out to the left edge at the end of their duration.',
    stochastic: false,
  },
  SlideOutRight: {
    component: SlideOutRight,
    family: 'exit',
    summary: 'Children slide out to the right edge at the end of their duration.',
    stochastic: false,
  },
  SlideOutUp: {
    component: SlideOutUp,
    family: 'exit',
    summary: 'Children slide out upward at the end of their duration.',
    stochastic: false,
  },
  SlideOutDown: {
    component: SlideOutDown,
    family: 'exit',
    summary: 'Children slide out downward at the end of their duration.',
    stochastic: false,
  },
  ScaleOut: {
    component: ScaleOut,
    family: 'exit',
    summary: 'Children scale down to zero at the end of their duration.',
    stochastic: false,
  },
  RotateOut: {
    component: RotateOut,
    family: 'exit',
    summary: 'Children rotate out to 90° while fading to transparent.',
    stochastic: false,
  },
  BlurOut: {
    component: BlurOut,
    family: 'exit',
    summary: 'Children blur out to heavy blur while fading to transparent.',
    stochastic: false,
  },
  ClipWipeOut: {
    component: ClipWipeOut,
    family: 'exit',
    summary: 'Children are removed by a right-to-left clip-path wipe.',
    stochastic: false,
  },
  MaskCircleOut: {
    component: MaskCircleOut,
    family: 'exit',
    summary: 'Children are hidden by a circular mask closing to the centre.',
    stochastic: false,
  },
  ShatterOut: {
    component: ShatterOut,
    family: 'exit',
    summary: 'Children shatter into offset tiles that scatter outward (seeded).',
    stochastic: true,
  },
  DissolveOut: {
    component: DissolveOut,
    family: 'exit',
    summary: 'Children dissolve out with opacity fade and slight scale shrink.',
    stochastic: true,
  },
};

// --------------- Emphasis pack (16) ------------------------------------------

const EMPHASIS_EFFECTS: EffectRegistry = {
  Pulse: {
    component: Pulse,
    family: 'emphasis',
    summary: 'Children pulse in scale rhythmically on a 30-frame sine loop.',
    stochastic: false,
  },
  Breathe: {
    component: Breathe,
    family: 'emphasis',
    summary: 'Children slow-breathe with a subtle scale rise and fall.',
    stochastic: false,
  },
  Shake: {
    component: Shake,
    family: 'emphasis',
    summary: 'Children jerk horizontally with per-frame seeded noise (seeded).',
    stochastic: true,
  },
  Wobble: {
    component: Wobble,
    family: 'emphasis',
    summary: 'Children rock left–right around their centre on a rotation sine.',
    stochastic: false,
  },
  Jitter: {
    component: Jitter,
    family: 'emphasis',
    summary: 'Children jitter with small random XY per-frame displacement (seeded).',
    stochastic: true,
  },
  Bounce: {
    component: Bounce,
    family: 'emphasis',
    summary: 'Children bounce vertically using an absolute-sine loop.',
    stochastic: false,
  },
  Float: {
    component: Float,
    family: 'emphasis',
    summary: 'Children float slowly up and down on a slow sine period.',
    stochastic: false,
  },
  Swing: {
    component: Swing,
    family: 'emphasis',
    summary: 'Children swing like a pendulum around the top-centre origin.',
    stochastic: false,
  },
  HeartBeat: {
    component: HeartBeat,
    family: 'emphasis',
    summary: 'Children scale with a double-pulse heartbeat rhythm every 30 frames.',
    stochastic: false,
  },
  Flash: {
    component: Flash,
    family: 'emphasis',
    summary: 'Children flash bright then dim on a sharp repeating beat.',
    stochastic: false,
  },
  Glow: {
    component: Glow,
    family: 'emphasis',
    summary: 'Children emit an animated warm drop-shadow glow that pulses.',
    stochastic: false,
  },
  Shimmer: {
    component: Shimmer,
    family: 'emphasis',
    summary: 'A diagonal highlight band sweeps across children repeatedly.',
    stochastic: false,
  },
  Sheen: {
    component: Sheen,
    family: 'emphasis',
    summary: 'A subtle surface sheen passes across children on a slow loop.',
    stochastic: false,
  },
  Ripple: {
    component: Ripple,
    family: 'emphasis',
    summary: 'An expanding circular ring emanates from the centre of children.',
    stochastic: false,
  },
  Tremble: {
    component: Tremble,
    family: 'emphasis',
    summary: 'Children tremble with rapid micro-displacement and micro-rotation (seeded).',
    stochastic: true,
  },
  Squash: {
    component: Squash,
    family: 'emphasis',
    summary: 'Children squash and stretch vertically on a spring-like sine loop.',
    stochastic: false,
  },
};

// --------------- Assembled registry ------------------------------------------

export const EFFECTS: EffectRegistry = mergeEffectRegistries(
  ENTRANCE_EFFECTS,
  EXIT_EFFECTS,
  EMPHASIS_EFFECTS
);

/** Sorted list of all effect names. */
export const EFFECT_NAMES: string[] = Object.keys(EFFECTS).sort();
