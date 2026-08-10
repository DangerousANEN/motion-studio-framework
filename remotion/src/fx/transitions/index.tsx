/**
 * Scene transitions — Section 2.8 of the MSF Expansion Plan.
 *
 * CONTRACT
 * --------
 * Each transition component takes:
 *   { progress: number 0..1, from: React.ReactNode, to: React.ReactNode, seed?: number }
 *
 * - progress=0 → output MUST EQUAL `from` exactly (no pixel deviation)
 * - progress=1 → output MUST EQUAL `to` exactly (no pixel deviation)
 * - progress=0.5 → mid-blend, differs from both
 *
 * These are pure React/CSS composites, no WebGL, so they work in headless CI.
 */
import React from 'react';
import { AbsoluteFill } from 'remotion';

export interface TransitionProps {
  progress: number;
  from: React.ReactNode;
  to: React.ReactNode;
  seed?: number;
}

// Seeded PRNG (mulberry32)
function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------------------
// 1. CutHard — instantaneous hard cut at progress=0.5
//    progress=0: from only. progress=1: to only.
// ---------------------------------------------------------------------------
export const CutHard: React.FC<TransitionProps> = ({ progress, from, to }) => {
  // Hard cut: show `from` until 0.5, then `to`. Identity at endpoints guaranteed.
  if (progress < 0.5) {
    return <AbsoluteFill>{from}</AbsoluteFill>;
  }
  return <AbsoluteFill>{to}</AbsoluteFill>;
};

// ---------------------------------------------------------------------------
// 2. CrossFade — linear opacity blend
//    progress=0: opacity-from=1, opacity-to=0. progress=1: reversed.
// ---------------------------------------------------------------------------
export const CrossFade: React.FC<TransitionProps> = ({ progress, from, to }) => {
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity: 1 - progress }}>{from}</AbsoluteFill>
      <AbsoluteFill style={{ opacity: progress }}>{to}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 3. WipeLinear — horizontal wipe left-to-right
// ---------------------------------------------------------------------------
export const WipeLinear: React.FC<TransitionProps> = ({ progress, from, to }) => {
  const pct = progress * 100;
  return (
    <AbsoluteFill>
      {/* from: shrinks from right */}
      <AbsoluteFill
        style={{
          clipPath: `inset(0 ${pct}% 0 0)`,
          overflow: 'hidden',
        }}
      >
        {from}
      </AbsoluteFill>
      {/* to: grows from left */}
      <AbsoluteFill
        style={{
          clipPath: `inset(0 0 0 ${100 - pct}%)`,
          overflow: 'hidden',
        }}
      >
        {to}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 4. WipeCircle — circular iris wipe expanding from centre
// ---------------------------------------------------------------------------
export const WipeCircle: React.FC<TransitionProps> = ({ progress, from, to }) => {
  // At progress=0: circle radius=0 (only from). At progress=1: circle covers all (only to).
  // Circle radius as a fraction of the diagonal (so it fills at 1.0)
  const radius = progress * 141.5; // 141.5% covers corner-to-corner
  return (
    <AbsoluteFill>
      <AbsoluteFill>{from}</AbsoluteFill>
      <AbsoluteFill
        style={{
          clipPath: `circle(${radius}% at 50% 50%)`,
          overflow: 'hidden',
        }}
      >
        {to}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 5. SlidePush — outgoing slides out left, incoming slides in from right
// ---------------------------------------------------------------------------
export const SlidePush: React.FC<TransitionProps> = ({ progress, from, to }) => {
  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      <AbsoluteFill
        style={{
          transform: `translateX(${-progress * 100}%)`,
        }}
      >
        {from}
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: `translateX(${(1 - progress) * 100}%)`,
        }}
      >
        {to}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 6. ZoomBlurTransition — from zooms in & fades, to zooms from 1.2x to 1
// ---------------------------------------------------------------------------
export const ZoomBlurTransition: React.FC<TransitionProps> = ({ progress, from, to }) => {
  const fromScale = 1 + progress * 0.3;
  const fromOpacity = 1 - progress;
  const toScale = 1.3 - progress * 0.3;
  const toOpacity = progress;
  const blurFrom = progress * 8;
  const blurTo = (1 - progress) * 8;

  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: `scale(${fromScale})`,
          opacity: fromOpacity,
          filter: `blur(${blurFrom}px)`,
        }}
      >
        {from}
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: `scale(${toScale})`,
          opacity: toOpacity,
          filter: `blur(${blurTo}px)`,
        }}
      >
        {to}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 7. GlitchTransition — RGB-split glitch effect mid-transition
// ---------------------------------------------------------------------------
export const GlitchTransition: React.FC<TransitionProps> = ({
  progress,
  from,
  to,
  seed = 42,
}) => {
  // At 0: from. At 1: to. Glitch peaks near 0.5.
  const glitchIntensity = Math.sin(progress * Math.PI); // 0→1→0

  const rng = mulberry32(seed + Math.floor(progress * 20));
  const offsetX = (rng() - 0.5) * 30 * glitchIntensity;
  const offsetY = (rng() - 0.5) * 10 * glitchIntensity;

  // Which scene is winning
  const fromOpacity = 1 - progress;
  const toOpacity = progress;

  return (
    <AbsoluteFill>
      {/* base blend */}
      <AbsoluteFill style={{ opacity: fromOpacity }}>{from}</AbsoluteFill>
      <AbsoluteFill style={{ opacity: toOpacity }}>{to}</AbsoluteFill>
      {/* glitch R channel from-scene offset */}
      <AbsoluteFill
        style={{
          opacity: fromOpacity * glitchIntensity * 0.5,
          transform: `translate(${offsetX}px, ${offsetY}px)`,
          mixBlendMode: 'screen',
          filter: 'url(#glitch-r)',
        }}
      >
        {from}
      </AbsoluteFill>
      {/* glitch B channel to-scene offset */}
      <AbsoluteFill
        style={{
          opacity: toOpacity * glitchIntensity * 0.5,
          transform: `translate(${-offsetX}px, ${-offsetY}px)`,
          mixBlendMode: 'screen',
          filter: 'url(#glitch-b)',
        }}
      >
        {to}
      </AbsoluteFill>
      {/* SVG channel filters */}
      <svg style={{ position: 'absolute', width: 0, height: 0 }}>
        <defs>
          <filter id="glitch-r">
            <feColorMatrix
              type="matrix"
              values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"
            />
          </filter>
          <filter id="glitch-b">
            <feColorMatrix
              type="matrix"
              values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"
            />
          </filter>
        </defs>
      </svg>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 8. WhipPanTransition — fast horizontal blur pan
// ---------------------------------------------------------------------------
export const WhipPanTransition: React.FC<TransitionProps> = ({
  progress,
  from,
  to,
}) => {
  // Motion blur peaks at mid-point
  const blur = Math.sin(progress * Math.PI) * 20;
  const fromX = -progress * 60;
  const toX = (1 - progress) * 60;
  const fromOpacity = 1 - progress;
  const toOpacity = progress;

  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      <AbsoluteFill
        style={{
          transform: `translateX(${fromX}px)`,
          opacity: fromOpacity,
          filter: `blur(${blur}px)`,
        }}
      >
        {from}
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: `translateX(${toX}px)`,
          opacity: toOpacity,
          filter: `blur(${blur}px)`,
        }}
      >
        {to}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 9. MorphShape — circular mask morphs between scenes
// ---------------------------------------------------------------------------
export const MorphShape: React.FC<TransitionProps> = ({ progress, from, to }) => {
  // Starts as a circle that morphs to a square clip around the whole frame
  // At progress=0: clip = 0% circle (only from visible). At 1: full rect (only to).
  const ease = progress < 0.5
    ? 2 * progress * progress
    : 1 - Math.pow(-2 * progress + 2, 2) / 2;

  const r = ease * 100;
  const corner = (1 - ease) * 50; // % border-radius on the clip box

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity: 1 - ease }}>{from}</AbsoluteFill>
      <AbsoluteFill
        style={{
          clipPath: `inset(${(1 - ease) * 30}% round ${corner}%)`,
          opacity: ease > 0.01 ? 1 : 0,
        }}
      >
        {to}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 10. LiquidWarp — wavy distortion dissolve using SVG feTurbulence displacement
// ---------------------------------------------------------------------------
export const LiquidWarp: React.FC<TransitionProps> = ({
  progress,
  from,
  to,
  seed = 42,
}) => {
  // Scale displacement from 0 at endpoints to max at midpoint
  const warpAmount = Math.sin(progress * Math.PI) * 30;
  const noiseSeed = (seed + Math.floor(progress * 10)) & 0xffff;

  return (
    <AbsoluteFill>
      {/* Hidden SVG filter */}
      <svg style={{ position: 'absolute', width: 0, height: 0 }}>
        <defs>
          <filter id={`liquid-${noiseSeed}`}>
            <feTurbulence
              type="turbulence"
              baseFrequency="0.015"
              numOctaves={3}
              seed={noiseSeed}
            />
            <feDisplacementMap
              in="SourceGraphic"
              scale={warpAmount}
              xChannelSelector="R"
              yChannelSelector="G"
            />
          </filter>
        </defs>
      </svg>

      <AbsoluteFill
        style={{
          opacity: 1 - progress,
          filter: warpAmount > 0.5 ? `url(#liquid-${noiseSeed})` : undefined,
        }}
      >
        {from}
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          opacity: progress,
          filter: warpAmount > 0.5 ? `url(#liquid-${noiseSeed})` : undefined,
        }}
      >
        {to}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 11. FilmBurn — orange/red burn wipe from centre
// ---------------------------------------------------------------------------
export const FilmBurn: React.FC<TransitionProps> = ({ progress, from, to }) => {
  // Burn expands from the centre: a hot orange oval that covers from then reveals to
  const burnProgress = progress;
  const burnRadius = burnProgress * 141.5;
  const burnOpacity = Math.sin(burnProgress * Math.PI) * 0.8;

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity: 1 - progress }}>{from}</AbsoluteFill>
      <AbsoluteFill
        style={{
          clipPath: `circle(${burnRadius}% at 50% 50%)`,
          opacity: progress > 0 ? 1 : 0,
        }}
      >
        {to}
      </AbsoluteFill>
      {/* Film burn flare */}
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          opacity: burnOpacity,
          background:
            'radial-gradient(ellipse at 50% 50%, rgba(255,140,0,0.8) 0%, rgba(255,60,0,0.4) 40%, rgba(255,0,0,0) 70%)',
          mixBlendMode: 'screen',
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// 12. LightFlashCut — white flash then cut
// ---------------------------------------------------------------------------
export const LightFlashCut: React.FC<TransitionProps> = ({
  progress,
  from,
  to,
}) => {
  // 0..0.5: from + flash building; 0.5..1: to + flash fading
  // Flash peaks exactly at 0.5
  const flashOpacity = Math.sin(progress * Math.PI);
  const showTo = progress >= 0.5;

  return (
    <AbsoluteFill>
      <AbsoluteFill>{showTo ? to : from}</AbsoluteFill>
      {/* White flash overlay */}
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          backgroundColor: `rgba(255,255,255,${flashOpacity})`,
        }}
      />
    </AbsoluteFill>
  );
};
