/**
 * Camera effects — 2.4 (12 effects)
 *
 * ZoomPunch · ZoomSlow · PanLeft · PanRight · DollyIn · DollyOut ·
 * HandheldDrift · WhipPan · RackFocus · ParallaxLayers · OrbitAround · TiltShift
 *
 * Contract:
 *   - intensity=0  → pixel-perfect no-op (no style applied)
 *   - intensity=1  → full effect
 *   - Stochastic effects use mulberry32(seed) — never Math.random()
 *   - Animation via resolveMotion(motion, fps, channel) with range (frame, 0, 1)
 */

import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { resolveMotion, type MotionConfig } from '../../lib/motion';

// ---------------------------------------------------------------------------
// Local EffectProps — duplicate declaration is deliberate (avoids merge conflict
// with the other agent's effects.ts).
// ---------------------------------------------------------------------------
export interface EffectProps {
  /** 0 = no-op, 1 = full effect. Default: 1. */
  intensity?: number;
  /** Seeded PRNG seed for stochastic effects. */
  seed?: number;
  /** Optional motion config forwarded to resolveMotion. */
  motion?: MotionConfig;
  /** Content to wrap. */
  children: React.ReactNode;
}

// ---------------------------------------------------------------------------
// Seeded PRNG — mulberry32
// ---------------------------------------------------------------------------
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------------------
// 2.4.1  ZoomPunch — fast zoom-in spike then ease back
// ---------------------------------------------------------------------------
export const ZoomPunch: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  // Punch on the first half, settle on the second
  const halfDur = durationInFrames / 2;
  const t = frame < halfDur
    ? animate(frame, 0, 1)
    : 1 - animate(frame - halfDur, 0, 1);
  const scale = 1 + intensity * 0.12 * t;

  return (
    <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.2  ZoomSlow — gentle zoom in from 1x to 1+intensity*0.08
// ---------------------------------------------------------------------------
export const ZoomSlow: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);
  const scale = 1 + intensity * 0.08 * t;

  return (
    <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.3  PanLeft — translate the frame rightward (content moves left)
// ---------------------------------------------------------------------------
export const PanLeft: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);
  const tx = -intensity * width * 0.06 * t;

  return (
    <AbsoluteFill style={{ transform: `translateX(${tx}px)` }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.4  PanRight — translate the frame leftward (content moves right)
// ---------------------------------------------------------------------------
export const PanRight: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);
  const tx = intensity * width * 0.06 * t;

  return (
    <AbsoluteFill style={{ transform: `translateX(${tx}px)` }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.5  DollyIn — progressive zoom toward camera (scale up)
// ---------------------------------------------------------------------------
export const DollyIn: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);
  const scale = 1 + intensity * 0.15 * t;

  return (
    <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.6  DollyOut — progressive zoom away from camera (scale down)
// ---------------------------------------------------------------------------
export const DollyOut: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);
  const scale = 1 - intensity * 0.12 * t;

  return (
    <AbsoluteFill style={{ transform: `scale(${Math.max(0.1, scale)})`, transformOrigin: 'center center' }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.7  HandheldDrift — low-frequency organic camera shake
//        Uses seeded PRNG so it is frame-reproducible.
// ---------------------------------------------------------------------------

/** Frames between noise nodes. Handheld motion is low-frequency; sampling the
 *  lattice this far apart puts the drift around 2.5 Hz at 60fps. */
const DRIFT_LATTICE = 24;

/**
 * Smooth 1-D value noise: seeded lattice nodes with smoothstep between them.
 *
 * The previous implementation reseeded per frame — `mulberry32(seed + frame*7)`
 * — so adjacent frames drew INDEPENDENT samples. That is white noise, not
 * drift: measured on a settled TgChat scene the picture jumped a mean 0.62px
 * (max 1.41px) every frame and reversed horizontal direction in 5 of 39 frame
 * pairs. On screen that is per-pixel dither, which reads as a bad encode
 * rather than a camera operator breathing. Real handheld motion is continuous
 * in time, so the noise has to be a continuous function OF time: sample sparse
 * nodes and ease between them.
 */
const driftNoise = (seed: number, frame: number, channel: number): number => {
  const x = frame / DRIFT_LATTICE;
  const i = Math.floor(x);
  const f = x - i;
  // Each (channel, node) pair gets its own stream; large odd multipliers keep
  // the x and y channels from correlating into a diagonal-only wobble.
  const node = (n: number) =>
    mulberry32(seed * 7919 + channel * 104729 + n * 31)() * 2 - 1;
  const a = node(i);
  const b = node(i + 1);
  const s = f * f * (3 - 2 * f); // smoothstep: zero slope at both nodes
  return a + (b - a) * s;
};

export const HandheldDrift: React.FC<EffectProps> = ({
  intensity = 1,
  seed = 42,
  children,
}) => {
  const frame = useCurrentFrame();

  if (intensity === 0) return <>{children}</>;

  // Continuous-in-time noise, so consecutive frames differ by a fraction of a
  // pixel instead of a full pixel in a random direction.
  const nx = driftNoise(seed, frame, 0);
  const ny = driftNoise(seed, frame, 1);

  // Layered slow drift: eased noise plus a slower sine so the motion does not
  // settle into an obvious loop.
  const px = intensity * (nx * 5 + Math.sin(frame * 0.04) * 6);
  const py = intensity * (ny * 3 + Math.cos(frame * 0.03) * 4);
  const rot = intensity * (nx * 0.4);

  return (
    <AbsoluteFill
      style={{
        transform: `translate(${px}px, ${py}px) rotate(${rot}deg)`,
        transformOrigin: 'center center',
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.8  WhipPan — fast horizontal blur sweep across the full clip
// ---------------------------------------------------------------------------
export const WhipPan: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, durationInFrames } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);

  // Peak whip at mid-point
  const whipT = Math.sin(t * Math.PI);
  const tx = intensity * width * 0.4 * whipT;
  const blur = intensity * 20 * whipT;

  return (
    <AbsoluteFill
      style={{
        transform: `translateX(${tx}px)`,
        filter: blur > 0.5 ? `blur(${blur}px)` : undefined,
        transformOrigin: 'center center',
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.9  RackFocus — blur in → sharp → blur out simulating lens rack
// ---------------------------------------------------------------------------
export const RackFocus: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);

  // Triangle: blurry → sharp (t=0.5) → blurry
  const blurAmount = intensity * 16 * Math.abs(t - 0.5) * 2;

  return (
    <AbsoluteFill style={{ filter: blurAmount > 0.1 ? `blur(${blurAmount}px)` : undefined }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.10  ParallaxLayers — applies a subtle offset to simulate depth
//         Wraps children and shifts the whole layer slightly.
// ---------------------------------------------------------------------------
export const ParallaxLayers: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);

  // Foreground layer drifts more than background
  const tx = intensity * width * 0.04 * Math.sin(t * Math.PI * 2);
  const ty = intensity * 20 * Math.cos(t * Math.PI * 1.3);

  return (
    <AbsoluteFill
      style={{
        transform: `translate(${tx}px, ${ty}px)`,
        transformOrigin: 'center center',
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.11  OrbitAround — slow circular pan (content orbits the centre)
// ---------------------------------------------------------------------------
export const OrbitAround: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'camera');
  const t = animate(frame, 0, 1);

  const angle = t * 2 * Math.PI;
  const radius = intensity * 40;
  const tx = Math.cos(angle) * radius;
  const ty = Math.sin(angle) * radius * 0.5; // elliptical orbit

  return (
    <AbsoluteFill
      style={{
        transform: `translate(${tx}px, ${ty}px)`,
        transformOrigin: 'center center',
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.4.12  TiltShift — miniature-world focus band: blur top and bottom
// ---------------------------------------------------------------------------
export const TiltShift: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  const blurPx = intensity * 10;

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {/* Sharp centre layer */}
      <AbsoluteFill>{children}</AbsoluteFill>

      {/* Blurred overlay — top gradient mask */}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          background: `linear-gradient(
            to bottom,
            rgba(0,0,0,${intensity * 0.7}) 0%,
            transparent 30%,
            transparent 70%,
            rgba(0,0,0,${intensity * 0.7}) 100%
          )`,
          backdropFilter: `blur(${blurPx}px)`,
          WebkitBackdropFilter: `blur(${blurPx}px)`,
          // Only blur the top / bottom bands
          maskImage: `linear-gradient(
            to bottom,
            black 0%,
            black 25%,
            transparent 35%,
            transparent 65%,
            black 75%,
            black 100%
          )`,
          WebkitMaskImage: `linear-gradient(
            to bottom,
            black 0%,
            black 25%,
            transparent 35%,
            transparent 65%,
            black 75%,
            black 100%
          )`,
        }}
      />
    </AbsoluteFill>
  );
};
