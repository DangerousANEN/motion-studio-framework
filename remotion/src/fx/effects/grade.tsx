/**
 * Colour / grade effects — 2.5 (14 effects)
 *
 * Vignette · FilmGrain · ChromaticAberration · Bloom · ColorGradeWarm ·
 * ColorGradeCool · Duotone · Invert · Saturate · Desaturate ·
 * Contrast · Posterize · HalationGlow · LightLeak
 *
 * Contract:
 *   - intensity=0  → pixel-perfect no-op (children rendered unchanged)
 *   - intensity=1  → full effect
 *   - Stochastic effects use mulberry32(seed) — never Math.random()
 *   - SVG filters for CA and glow; CSS filters for the rest
 */

import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { resolveMotion, type MotionConfig } from '../../lib/motion';

// ---------------------------------------------------------------------------
// Local EffectProps — duplicate declaration is deliberate (avoids merge
// conflict with other agent's effects.ts).
// ---------------------------------------------------------------------------
export interface EffectProps {
  intensity?: number;
  seed?: number;
  motion?: MotionConfig;
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
// 2.5.1  Vignette — edge darkening
// ---------------------------------------------------------------------------
export const Vignette: React.FC<EffectProps> = ({ intensity = 1, children }) => {
  if (intensity === 0) return <>{children}</>;

  return (
    <AbsoluteFill>
      {children}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          background: `radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,${intensity * 0.8}) 100%)`,
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.2  FilmGrain — per-frame seeded noise overlay
// ---------------------------------------------------------------------------
export const FilmGrain: React.FC<EffectProps> = ({
  intensity = 1,
  seed = 0,
  children,
}) => {
  const frame = useCurrentFrame();

  if (intensity === 0) return <>{children}</>;

  // Reseed every frame so the grain shimmers; use provided seed + frame
  const noiseSeed = (seed * 100003 + frame * 7) & 0x7fffffff;

  return (
    <AbsoluteFill>
      {children}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          opacity: intensity * 0.35,
          mixBlendMode: 'overlay',
        }}
      >
        <svg width="100%" height="100%">
          <filter id={`fg-grain-${noiseSeed}`}>
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.75"
              numOctaves={4}
              seed={noiseSeed}
              stitchTiles="stitch"
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect
            width="100%"
            height="100%"
            filter={`url(#fg-grain-${noiseSeed})`}
          />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.3  ChromaticAberration — RGB channel split via SVG colour matrices
// ---------------------------------------------------------------------------
export const ChromaticAberration: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  const px = intensity * 8;
  const filterId = `ca-r-${px}`;
  const filterIdB = `ca-b-${px}`;

  return (
    <>
      {/* SVG defs — mounted once; IDs include the px value so they don't collide */}
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={filterId}>
          <feColorMatrix
            type="matrix"
            values="1 0 0 0 0
                    0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 1 0"
          />
        </filter>
        <filter id={filterIdB}>
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0
                    0 0 0 0 0
                    0 0 1 0 0
                    0 0 0 1 0"
          />
        </filter>
      </svg>

      <AbsoluteFill style={{ position: 'relative' }}>
        {/* Red channel shifted left */}
        <AbsoluteFill
          aria-hidden
          style={{
            transform: `translateX(${-px}px)`,
            filter: `url(#${filterId})`,
            opacity: 0.6,
            mixBlendMode: 'screen',
            pointerEvents: 'none',
          }}
        >
          {children}
        </AbsoluteFill>

        {/* Main (unshifted) content */}
        {children}

        {/* Blue channel shifted right */}
        <AbsoluteFill
          aria-hidden
          style={{
            transform: `translateX(${px}px)`,
            filter: `url(#${filterIdB})`,
            opacity: 0.6,
            mixBlendMode: 'screen',
            pointerEvents: 'none',
          }}
        >
          {children}
        </AbsoluteFill>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2.5.4  Bloom — screen-blended blurred copy of content
// ---------------------------------------------------------------------------
export const Bloom: React.FC<EffectProps> = ({ intensity = 1, children }) => {
  if (intensity === 0) return <>{children}</>;

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {children}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          filter: `blur(${intensity * 22}px) brightness(1.3)`,
          opacity: Math.min(0.8, intensity * 0.7),
          mixBlendMode: 'screen',
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.5  ColorGradeWarm — warm orange/amber colour shift
// ---------------------------------------------------------------------------
export const ColorGradeWarm: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {children}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          background: `rgba(255, 140, 40, ${intensity * 0.18})`,
          mixBlendMode: 'multiply',
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.6  ColorGradeCool — cool cyan/blue colour shift
// ---------------------------------------------------------------------------
export const ColorGradeCool: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {children}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          background: `rgba(40, 120, 255, ${intensity * 0.16})`,
          mixBlendMode: 'multiply',
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.7  Duotone — two-colour map (shadow → highlight)
//        Default: deep blue shadow → gold highlight
// ---------------------------------------------------------------------------
export const Duotone: React.FC<
  EffectProps & { shadowColor?: string; highlightColor?: string }
> = ({
  intensity = 1,
  shadowColor = '#0d1b4b',
  highlightColor = '#f5c518',
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  const filterId = 'duotone-filter';

  return (
    <>
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={filterId} colorInterpolationFilters="sRGB">
          <feColorMatrix type="saturate" values="0" result="grey" />
          {/* Map grey [0,1] → shadow .. highlight in RGB */}
          <feComponentTransfer>
            <feFuncR
              type="linear"
              slope={
                parseInt(highlightColor.slice(1, 3), 16) / 255 -
                parseInt(shadowColor.slice(1, 3), 16) / 255
              }
              intercept={parseInt(shadowColor.slice(1, 3), 16) / 255}
            />
            <feFuncG
              type="linear"
              slope={
                parseInt(highlightColor.slice(3, 5), 16) / 255 -
                parseInt(shadowColor.slice(3, 5), 16) / 255
              }
              intercept={parseInt(shadowColor.slice(3, 5), 16) / 255}
            />
            <feFuncB
              type="linear"
              slope={
                parseInt(highlightColor.slice(5, 7), 16) / 255 -
                parseInt(shadowColor.slice(5, 7), 16) / 255
              }
              intercept={parseInt(shadowColor.slice(5, 7), 16) / 255}
            />
          </feComponentTransfer>
        </filter>
      </svg>

      <AbsoluteFill style={{ position: 'relative' }}>
        {/* Original at reduced opacity */}
        <AbsoluteFill style={{ opacity: 1 - intensity }}>{children}</AbsoluteFill>
        {/* Duotone overlay */}
        <AbsoluteFill
          aria-hidden
          style={{
            filter: `url(#${filterId})`,
            opacity: intensity,
            mixBlendMode: 'normal',
            pointerEvents: 'none',
          }}
        >
          {children}
        </AbsoluteFill>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2.5.8  Invert — CSS invert filter
// ---------------------------------------------------------------------------
export const Invert: React.FC<EffectProps> = ({ intensity = 1, children }) => {
  if (intensity === 0) return <>{children}</>;

  return (
    <AbsoluteFill style={{ filter: `invert(${intensity})` }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.9  Saturate — boost colour saturation
// ---------------------------------------------------------------------------
export const Saturate: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  // saturate(1) = no change; saturate(3) = heavy boost
  const sat = 1 + intensity * 2;

  return (
    <AbsoluteFill style={{ filter: `saturate(${sat})` }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.10  Desaturate — drain colour saturation toward grey
// ---------------------------------------------------------------------------
export const Desaturate: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  // saturate(1)=normal, saturate(0)=greyscale
  const sat = 1 - intensity;

  return (
    <AbsoluteFill style={{ filter: `saturate(${sat})` }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.11  Contrast — increase contrast
// ---------------------------------------------------------------------------
export const Contrast: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  // contrast(1)=normal; contrast(2)=heavy
  const c = 1 + intensity * 1.0;

  return (
    <AbsoluteFill style={{ filter: `contrast(${c})` }}>
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.12  Posterize — discrete colour steps (SVG feComponentTransfer)
// ---------------------------------------------------------------------------
export const Posterize: React.FC<EffectProps & { steps?: number }> = ({
  intensity = 1,
  steps = 4,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  const effectiveSteps = Math.max(2, Math.round(steps));
  const filterId = `posterize-${effectiveSteps}`;

  // Build discrete step table for feComponentTransfer
  const tableValues = Array.from({ length: effectiveSteps }, (_, i) =>
    (i / (effectiveSteps - 1)).toFixed(4)
  ).join(' ');

  return (
    <>
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={filterId} colorInterpolationFilters="sRGB">
          <feComponentTransfer>
            <feFuncR type="discrete" tableValues={tableValues} />
            <feFuncG type="discrete" tableValues={tableValues} />
            <feFuncB type="discrete" tableValues={tableValues} />
          </feComponentTransfer>
        </filter>
      </svg>

      <AbsoluteFill style={{ position: 'relative' }}>
        {/* Lerp between original and posterized */}
        <AbsoluteFill style={{ opacity: 1 - intensity }}>{children}</AbsoluteFill>
        <AbsoluteFill
          aria-hidden
          style={{
            filter: `url(#${filterId})`,
            opacity: intensity,
            pointerEvents: 'none',
          }}
        >
          {children}
        </AbsoluteFill>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2.5.13  HalationGlow — warm red glow bleeding from bright areas
// ---------------------------------------------------------------------------
export const HalationGlow: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {children}
      {/* Red-shifted blurred copy screened over */}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          filter: `blur(${intensity * 30}px) saturate(2) hue-rotate(-20deg)`,
          opacity: intensity * 0.5,
          mixBlendMode: 'screen',
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.5.14  LightLeak — animated warm light sweep across the frame
// ---------------------------------------------------------------------------
export const LightLeak: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  seed = 0,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'opacity');
  const t = animate(frame, 0, 1);

  // Sweep a warm gradient across the frame
  const rand = mulberry32(seed + 1);
  const hue = 20 + rand() * 30; // warm orange to yellow
  const x = t * 120 - 10; // sweep from left to right (percent)

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {children}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          background: `radial-gradient(
            ellipse 60% 80% at ${x}% 30%,
            hsla(${hue}, 100%, 75%, ${intensity * 0.45}) 0%,
            transparent 70%
          )`,
          mixBlendMode: 'screen',
        }}
      />
    </AbsoluteFill>
  );
};
