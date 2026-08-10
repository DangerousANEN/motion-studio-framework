/**
 * Exit effects — 12 composable wrappers.
 *
 * Contract: intensity=0 → pixel-perfect no-op.
 * Every effect uses resolveMotion(motion, fps) → animate(frame, 0, 1).
 */
import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { resolveMotion } from '../../lib/motion';
import type { EffectProps } from '../../registry/effects';

/** mulberry32 PRNG — deterministic, seeded. */
function mulberry32(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------------------
// 1. FadeOut
// ---------------------------------------------------------------------------
export const FadeOut: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const opacity = 1 - progress;
  return <div style={{ opacity, width: '100%', height: '100%' }}>{children}</div>;
};

// ---------------------------------------------------------------------------
// 2. SlideOutLeft
// ---------------------------------------------------------------------------
export const SlideOutLeft: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const tx = -progress * width * intensity;
  return (
    <div style={{ transform: `translateX(${tx}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 3. SlideOutRight
// ---------------------------------------------------------------------------
export const SlideOutRight: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const tx = progress * width * intensity;
  return (
    <div style={{ transform: `translateX(${tx}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 4. SlideOutUp
// ---------------------------------------------------------------------------
export const SlideOutUp: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, height } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const ty = -progress * height * intensity;
  return (
    <div style={{ transform: `translateY(${ty}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 5. SlideOutDown
// ---------------------------------------------------------------------------
export const SlideOutDown: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, height } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const ty = progress * height * intensity;
  return (
    <div style={{ transform: `translateY(${ty}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 6. ScaleOut
// ---------------------------------------------------------------------------
export const ScaleOut: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const scale = 1 - progress * intensity;
  return (
    <div
      style={{
        transform: `scale(${scale})`,
        transformOrigin: 'center center',
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 7. RotateOut
// ---------------------------------------------------------------------------
export const RotateOut: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const deg = progress * 90 * intensity;
  const opacity = 1 - progress;
  return (
    <div
      style={{
        transform: `rotate(${deg}deg)`,
        transformOrigin: 'center center',
        opacity,
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 8. BlurOut
// ---------------------------------------------------------------------------
export const BlurOut: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const blur = progress * 20 * intensity;
  const opacity = 1 - progress;
  return (
    <div style={{ filter: `blur(${blur}px)`, opacity, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 9. ClipWipeOut — right-to-left wipe out
// ---------------------------------------------------------------------------
export const ClipWipeOut: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeInOut', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  const rightClip = progress * 100 * intensity;
  return (
    <div
      style={{
        clipPath: `inset(0 ${rightClip}% 0 0)`,
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 10. MaskCircleOut — circle closes to center
// ---------------------------------------------------------------------------
export const MaskCircleOut: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  // Radius shrinks from 141% down to 0%
  const radius = (1 - progress * intensity) * 141;
  return (
    <div
      style={{
        clipPath: `circle(${radius}% at 50% 50%)`,
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 11. ShatterOut — stochastic: shatters children into offset tiles
// seed controls tile randomness
// ---------------------------------------------------------------------------
export const ShatterOut: React.FC<EffectProps> = ({ children, intensity = 1, seed = 42 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(30 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);

  // Generate 9 tiles, each with a random displacement direction
  const rng = mulberry32(seed);
  const tiles = Array.from({ length: 9 }, (_, i) => {
    const row = Math.floor(i / 3);
    const col = i % 3;
    const dx = (rng() - 0.5) * 2 * 300 * progress * intensity;
    const dy = (rng() - 0.5) * 2 * 300 * progress * intensity;
    const rot = (rng() - 0.5) * 60 * progress * intensity;
    const tileOpacity = Math.max(0, 1 - progress);
    return { row, col, dx, dy, rot, tileOpacity };
  });

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      {tiles.map(({ row, col, dx, dy, rot, tileOpacity }, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            inset: 0,
            clipPath: `inset(${row * 33.33}% ${(2 - col) * 33.33}% ${(2 - row) * 33.33}% ${col * 33.33}%)`,
            transform: `translate(${dx}px, ${dy}px) rotate(${rot}deg)`,
            opacity: tileOpacity,
          }}
        >
          {children}
        </div>
      ))}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 12. DissolveOut — animated noise-based dissolve (CSS approximation)
// Uses opacity modulated with an SVG turbulence mask
// ---------------------------------------------------------------------------
export const DissolveOut: React.FC<EffectProps> = ({ children, intensity = 1, seed = 42 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const exitDuration = Math.round(24 * intensity);
  const startFrame = durationInFrames - exitDuration;
  const localFrame = Math.max(0, frame - startFrame);
  const animate = resolveMotion({ curve: 'easeIn', duration: exitDuration }, fps);
  const progress = animate(localFrame, 0, 1);
  // Approximate dissolve: fade + slight scale shrink
  const opacity = Math.max(0, 1 - progress);
  const scale = 1 - progress * 0.1 * intensity;
  return (
    <div
      style={{
        opacity,
        transform: `scale(${scale})`,
        transformOrigin: 'center center',
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};
