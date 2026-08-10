/**
 * Distortion effects — 2.6 (14 effects)
 *
 * GlitchRgb · GlitchBlock · ScanLines · CrtCurve · VhsTracking ·
 * WaveWarp · RippleDistort · LensDistort · PixelSort · Displace ·
 * MotionBlurTrail · EchoTrail · Kaleidoscope · MirrorSplit
 *
 * Contract:
 *   - intensity=0  → pixel-perfect no-op (children rendered unchanged)
 *   - intensity=1  → full effect
 *   - All stochastic effects use mulberry32(seed) — never Math.random()
 *   - CSS/SVG only; no canvas/WebGL
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
// 2.6.1  GlitchRgb — per-frame random RGB channel offset
// ---------------------------------------------------------------------------
export const GlitchRgb: React.FC<EffectProps> = ({
  intensity = 1,
  seed = 0,
  children,
}) => {
  const frame = useCurrentFrame();

  if (intensity === 0) return <>{children}</>;

  const rand = mulberry32(seed + frame * 31337);
  const rx = (rand() - 0.5) * intensity * 20;
  const bx = (rand() - 0.5) * intensity * 20;
  const ry = (rand() - 0.5) * intensity * 6;
  const by = (rand() - 0.5) * intensity * 6;

  const rId = `glitch-r-${frame}-${seed}`;
  const bId = `glitch-b-${frame}-${seed}`;

  return (
    <>
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={rId}>
          <feColorMatrix
            type="matrix"
            values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"
          />
        </filter>
        <filter id={bId}>
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"
          />
        </filter>
      </svg>

      <AbsoluteFill style={{ position: 'relative' }}>
        <AbsoluteFill
          aria-hidden
          style={{
            transform: `translate(${rx}px, ${ry}px)`,
            filter: `url(#${rId})`,
            opacity: 0.7,
            mixBlendMode: 'screen',
            pointerEvents: 'none',
          }}
        >
          {children}
        </AbsoluteFill>
        {children}
        <AbsoluteFill
          aria-hidden
          style={{
            transform: `translate(${bx}px, ${by}px)`,
            filter: `url(#${bId})`,
            opacity: 0.7,
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
// 2.6.2  GlitchBlock — random rectangular colour-shifted slice glitches
// ---------------------------------------------------------------------------
export const GlitchBlock: React.FC<EffectProps & { blockCount?: number }> = ({
  intensity = 1,
  seed = 0,
  blockCount = 4,
  children,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const rand = mulberry32(seed + frame * 999983);

  // Only glitch on certain frames for authenticity
  const glitchActive = rand() < intensity * 0.6;

  const blocks: React.ReactNode[] = [];
  if (glitchActive) {
    for (let i = 0; i < blockCount; i++) {
      const top = rand() * height;
      const h = rand() * height * 0.08 * intensity;
      const dx = (rand() - 0.5) * width * 0.12 * intensity;
      const opacity = rand() * 0.8;

      blocks.push(
        <AbsoluteFill
          key={i}
          aria-hidden
          style={{
            top,
            height: h,
            bottom: 'auto',
            transform: `translateX(${dx}px)`,
            overflow: 'hidden',
            opacity,
            mixBlendMode: 'normal',
            pointerEvents: 'none',
            clipPath: `inset(${top}px 0 ${height - top - h}px 0)`,
          }}
        >
          {children}
        </AbsoluteFill>
      );
    }
  }

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {children}
      {blocks}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.6.3  ScanLines — CRT horizontal scan lines
// ---------------------------------------------------------------------------
export const ScanLines: React.FC<EffectProps & { lineGap?: number }> = ({
  intensity = 1,
  lineGap = 4,
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
          opacity: intensity,
          backgroundImage: `repeating-linear-gradient(
            to bottom,
            rgba(0,0,0,0.55) 0px,
            rgba(0,0,0,0.55) 1px,
            transparent 1px,
            transparent ${lineGap}px
          )`,
          mixBlendMode: 'multiply',
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.6.4  CrtCurve — barrel distortion simulation via SVG feMorphology+scale
// ---------------------------------------------------------------------------
export const CrtCurve: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  // CSS-only approach: slight perspective transform for barrel feel
  const persp = Math.max(100, 2000 - intensity * 1500);
  const rot = intensity * 4; // degrees of subtle curve

  return (
    <AbsoluteFill
      style={{
        perspective: `${persp}px`,
        position: 'relative',
      }}
    >
      <AbsoluteFill
        style={{
          transform: `rotateX(${rot * 0.3}deg) scale(${1 + intensity * 0.04})`,
          transformOrigin: 'center center',
          borderRadius: `${intensity * 20}px`,
          overflow: 'hidden',
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.6.5  VhsTracking — horizontal band shift (VHS tracking artifact)
// ---------------------------------------------------------------------------
export const VhsTracking: React.FC<EffectProps> = ({
  intensity = 1,
  seed = 0,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'transform');
  const t = animate(frame, 0, 1);

  const rand = mulberry32(seed + frame * 6271);
  const active = rand() < intensity * 0.5;

  if (!active) return <>{children}</>;

  const bandTop = rand() * height * 0.8;
  const bandH = rand() * height * 0.1 + 10;
  const dx = (rand() - 0.5) * width * 0.06 * intensity;

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {/* Main content */}
      {children}
      {/* Shifted band */}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          clipPath: `inset(${bandTop}px 0 ${height - bandTop - bandH}px 0)`,
          transform: `translateX(${dx}px)`,
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.6.6  WaveWarp — horizontal sine-wave distortion via SVG feTurbulence
// ---------------------------------------------------------------------------
export const WaveWarp: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'transform');
  const t = animate(frame, 0, 1);

  const amplitude = intensity * 15;
  const freq = 0.006;
  const phase = t * Math.PI * 2;

  const filterId = `wave-warp-${frame}`;

  return (
    <>
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={filterId} x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency={`0 ${freq}`}
            numOctaves={1}
            seed={Math.round(phase * 1000) & 0xffff}
            result="noise"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="noise"
            scale={amplitude}
            xChannelSelector="R"
            yChannelSelector="G"
          />
        </filter>
      </svg>
      <AbsoluteFill style={{ filter: `url(#${filterId})` }}>
        {children}
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2.6.7  RippleDistort — concentric ripple from centre
// ---------------------------------------------------------------------------
export const RippleDistort: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'transform');
  const t = animate(frame, 0, 1);

  const scale = intensity * 25;
  const freq = 0.012 + t * 0.004;
  const filterId = `ripple-${frame}`;

  return (
    <>
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={filterId} x="-5%" y="-5%" width="110%" height="110%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency={`${freq} ${freq * 0.5}`}
            numOctaves={2}
            seed={Math.round(t * 10000) & 0xffff}
            result="noise"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="noise"
            scale={scale}
            xChannelSelector="R"
            yChannelSelector="G"
          />
        </filter>
      </svg>
      <AbsoluteFill style={{ filter: `url(#${filterId})` }}>
        {children}
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2.6.8  LensDistort — barrel lens distortion (CSS perspective warp)
// ---------------------------------------------------------------------------
export const LensDistort: React.FC<EffectProps> = ({
  intensity = 1,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  const filterId = 'lens-distort';
  const k = intensity * 0.4; // barrel coefficient

  return (
    <>
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={filterId} x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.002 0.002"
            numOctaves={1}
            seed={1}
            result="noise"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="noise"
            scale={k * 60}
            xChannelSelector="R"
            yChannelSelector="G"
          />
        </filter>
      </svg>
      <AbsoluteFill
        style={{
          filter: `url(#${filterId})`,
          transform: `scale(${1 + intensity * 0.06})`,
          transformOrigin: 'center center',
        }}
      >
        {children}
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2.6.9  PixelSort — column-based horizontal pixel sorting artefact
//        Achieved with a clipped, offsetting copy of columns
// ---------------------------------------------------------------------------
export const PixelSort: React.FC<EffectProps & { columns?: number }> = ({
  intensity = 1,
  seed = 0,
  columns = 12,
  children,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const rand = mulberry32(seed + frame * 17);
  const colW = width / columns;

  const strips = Array.from({ length: columns }, (_, i) => {
    const active = rand() < intensity * 0.5;
    if (!active) return null;
    const dy = (rand() - 0.5) * height * 0.08 * intensity;
    const x = i * colW;
    return (
      <AbsoluteFill
        key={i}
        aria-hidden
        style={{
          pointerEvents: 'none',
          transform: `translateY(${dy}px)`,
          clipPath: `inset(0 ${width - x - colW}px 0 ${x}px)`,
          opacity: 0.9,
        }}
      >
        {children}
      </AbsoluteFill>
    );
  });

  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {children}
      {strips}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.6.10  Displace — SVG turbulence-based displacement
// ---------------------------------------------------------------------------
export const Displace: React.FC<EffectProps> = ({
  intensity = 1,
  seed = 0,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'transform');
  const t = animate(frame, 0, 1);

  const scale = intensity * 40;
  const noiseSeed = (seed + frame) & 0xffff;
  const filterId = `displace-${noiseSeed}`;

  return (
    <>
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={filterId} x="-5%" y="-5%" width="110%" height="110%">
          <feTurbulence
            type="turbulence"
            baseFrequency="0.015 0.01"
            numOctaves={3}
            seed={noiseSeed}
            result="noise"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="noise"
            scale={scale}
            xChannelSelector="R"
            yChannelSelector="G"
          />
        </filter>
      </svg>
      <AbsoluteFill style={{ filter: `url(#${filterId})` }}>
        {children}
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2.6.11  MotionBlurTrail — directional blur in motion direction
// ---------------------------------------------------------------------------
export const MotionBlurTrail: React.FC<EffectProps & { angle?: number }> = ({
  intensity = 1,
  angle = 0,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  const blurPx = intensity * 18;
  const rad = (angle * Math.PI) / 180;
  const dx = Math.cos(rad) * blurPx;
  const dy = Math.sin(rad) * blurPx;

  const filterId = `motion-blur-${angle}-${Math.round(blurPx)}`;

  return (
    <>
      <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
        <filter id={filterId} x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation={`${Math.abs(dx)} ${Math.abs(dy)}`} />
        </filter>
      </svg>
      <AbsoluteFill style={{ position: 'relative' }}>
        {/* Blurred ghost copies */}
        {[0.4, 0.25, 0.15].map((opacity, i) => (
          <AbsoluteFill
            key={i}
            aria-hidden
            style={{
              filter: `url(#${filterId})`,
              opacity,
              transform: `translate(${-dx * (i + 1) * 0.4}px, ${-dy * (i + 1) * 0.4}px)`,
              mixBlendMode: 'normal',
              pointerEvents: 'none',
            }}
          >
            {children}
          </AbsoluteFill>
        ))}
        {children}
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2.6.12  EchoTrail — ghost after-image frames
// ---------------------------------------------------------------------------
export const EchoTrail: React.FC<EffectProps & { echoCount?: number }> = ({
  intensity = 1,
  echoCount = 4,
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  // Render multiple translucent copies with increasing offset/fade
  return (
    <AbsoluteFill style={{ position: 'relative' }}>
      {Array.from({ length: echoCount }, (_, i) => {
        const frac = (i + 1) / echoCount;
        const opacity = intensity * (1 - frac) * 0.5;
        const tx = -(i + 1) * intensity * 8;
        return (
          <AbsoluteFill
            key={i}
            aria-hidden
            style={{
              opacity,
              transform: `translateX(${tx}px)`,
              mixBlendMode: 'screen',
              pointerEvents: 'none',
            }}
          >
            {children}
          </AbsoluteFill>
        );
      })}
      {children}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.6.13  Kaleidoscope — mirror the frame into a symmetrical mandala
//         CSS-only: 4-way mirror via clipping + rotation
// ---------------------------------------------------------------------------
export const Kaleidoscope: React.FC<EffectProps> = ({
  intensity = 1,
  motion,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity === 0) return <>{children}</>;

  const animate = resolveMotion(motion, fps, 'transform');
  const t = animate(frame, 0, 1);

  const rot = t * 360 * intensity * 0.5;

  return (
    <AbsoluteFill style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Original quadrant */}
      <AbsoluteFill
        style={{
          transform: `rotate(${rot}deg)`,
          transformOrigin: 'center center',
        }}
      >
        {children}
      </AbsoluteFill>

      {/* 3 mirrored quadrants */}
      {[90, 180, 270].map((deg) => (
        <AbsoluteFill
          key={deg}
          aria-hidden
          style={{
            transform: `rotate(${deg + rot}deg) scaleX(-1)`,
            transformOrigin: 'center center',
            opacity: 1 - intensity * 0.1,
            mixBlendMode: 'screen',
            pointerEvents: 'none',
          }}
        >
          {children}
        </AbsoluteFill>
      ))}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 2.6.14  MirrorSplit — horizontal mirror: left half reflects to right half
// ---------------------------------------------------------------------------
export const MirrorSplit: React.FC<EffectProps & { axis?: 'horizontal' | 'vertical' }> = ({
  intensity = 1,
  axis = 'horizontal',
  children,
}) => {
  if (intensity === 0) return <>{children}</>;

  const isH = axis === 'horizontal';
  const blendOpacity = intensity;

  return (
    <AbsoluteFill style={{ position: 'relative', overflow: 'hidden' }}>
      {children}

      {/* Mirrored half */}
      <AbsoluteFill
        aria-hidden
        style={{
          transform: isH ? 'scaleX(-1)' : 'scaleY(-1)',
          transformOrigin: 'center center',
          opacity: blendOpacity,
          mixBlendMode: 'screen',
          pointerEvents: 'none',
          // Clip to the mirrored half only
          clipPath: isH
            ? 'inset(0 0 0 50%)'
            : 'inset(50% 0 0 0)',
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
