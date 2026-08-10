/**
 * Entrance effects — 16 composable wrappers.
 *
 * Contract (from EXPANSION_PLAN.md §2):
 *   intensity?: number   // 0..1, defaults to 1
 *   seed?: number        // required when effect is stochastic
 *   intensity=0 MUST produce pixel-perfect no-op (identity transform on children).
 *
 * Every animation goes through resolveMotion(motion, fps) → animate(frame, 0, 1).
 * Never raw frame arithmetic; never Math.random().
 */
import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { resolveMotion } from '../../lib/motion';
import type { EffectProps } from '../../registry/effects';

/** Seeded PRNG — mulberry32. Never use Math.random(). */
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
// 1. FadeIn
// ---------------------------------------------------------------------------
export const FadeIn: React.FC<EffectProps> = ({ children, intensity = 1, seed: _seed }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const opacity = animate(frame, 0, 1);
  return <div style={{ opacity, width: '100%', height: '100%' }}>{children}</div>;
};

// ---------------------------------------------------------------------------
// 2. SlideInLeft
// ---------------------------------------------------------------------------
export const SlideInLeft: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const tx = (progress - 1) * width * intensity;
  return (
    <div style={{ transform: `translateX(${tx}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 3. SlideInRight
// ---------------------------------------------------------------------------
export const SlideInRight: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const tx = (1 - progress) * width * intensity;
  return (
    <div style={{ transform: `translateX(${tx}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 4. SlideInUp
// ---------------------------------------------------------------------------
export const SlideInUp: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const ty = (progress - 1) * height * intensity;
  return (
    <div style={{ transform: `translateY(${ty}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 5. SlideInDown
// ---------------------------------------------------------------------------
export const SlideInDown: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const ty = (1 - progress) * height * intensity;
  return (
    <div style={{ transform: `translateY(${ty}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 6. ScaleIn
// ---------------------------------------------------------------------------
export const ScaleIn: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  // At intensity=1: scale goes 0→1. At partial intensity: scale goes (1-intensity)→1.
  const scale = 1 - intensity + intensity * progress;
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
// 7. ScaleInBounce
// ---------------------------------------------------------------------------
export const ScaleInBounce: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion(
    { curve: 'spring', spring: { damping: 8, stiffness: 200 }, duration: Math.round(30 * intensity) },
    fps
  );
  const progress = animate(frame, 0, 1);
  const scale = 1 - intensity + intensity * progress;
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
// 8. RotateIn
// ---------------------------------------------------------------------------
export const RotateIn: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const deg = (progress - 1) * 90 * intensity;
  const opacity = progress;
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
// 9. FlipInX — rotates around X-axis (perspective + rotateX)
// ---------------------------------------------------------------------------
export const FlipInX: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const deg = (1 - progress) * 90 * intensity;
  return (
    <div style={{ perspective: '800px', width: '100%', height: '100%' }}>
      <div
        style={{
          transform: `rotateX(${deg}deg)`,
          transformOrigin: 'center center',
          width: '100%',
          height: '100%',
        }}
      >
        {children}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// 10. FlipInY — rotates around Y-axis
// ---------------------------------------------------------------------------
export const FlipInY: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const deg = (1 - progress) * 90 * intensity;
  return (
    <div style={{ perspective: '800px', width: '100%', height: '100%' }}>
      <div
        style={{
          transform: `rotateY(${deg}deg)`,
          transformOrigin: 'center center',
          width: '100%',
          height: '100%',
        }}
      >
        {children}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// 11. BlurIn
// ---------------------------------------------------------------------------
export const BlurIn: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const blur = (1 - progress) * 20 * intensity;
  const opacity = progress;
  return (
    <div
      style={{ filter: `blur(${blur}px)`, opacity, width: '100%', height: '100%' }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 12. ClipWipeIn — left-to-right clip-path reveal
// ---------------------------------------------------------------------------
export const ClipWipeIn: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeInOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  // At progress=0: clip reveals 0%. At progress=1: reveals 100%.
  const pct = `${progress * 100}%`;
  return (
    <div
      style={{
        clipPath: `inset(0 ${100 - progress * 100}% 0 0)`,
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 13. MaskCircleIn — circular reveal from centre
// ---------------------------------------------------------------------------
export const MaskCircleIn: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(24 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  // radius grows from 0 to ~141% (diagonal) so we cover the full frame
  const radius = `${progress * 141 * intensity + (1 - intensity) * 141}%`;
  return (
    <div
      style={{
        clipPath: `circle(${radius} at 50% 50%)`,
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 14. TypeIn — children appear via clip, simulating type-on reveal
// ---------------------------------------------------------------------------
export const TypeIn: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion({ curve: 'linear', duration: Math.round(36 * intensity) }, fps);
  const progress = animate(frame, 0, 1);
  const pct = progress * 100;
  return (
    <div
      style={{
        clipPath: `inset(0 ${100 - pct}% 0 0)`,
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 15. StaggerChildren — applies FadeIn + SlideInUp to direct children with stagger
// Note: stochastic in seed usage for jitter offset
// ---------------------------------------------------------------------------
export const StaggerChildren: React.FC<EffectProps> = ({ children, intensity = 1, seed = 42 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;

  const items = React.Children.toArray(children);
  const staggerFrames = Math.round(6 * intensity);

  return (
    <>
      {items.map((child, i) => {
        const delay = i * staggerFrames;
        const localFrame = Math.max(0, frame - delay);
        const animate = resolveMotion({ curve: 'easeOut', duration: Math.round(18 * intensity) }, fps);
        const progress = animate(localFrame, 0, 1);
        const opacity = progress;
        const ty = (1 - progress) * 40 * intensity;
        return (
          <div
            key={i}
            style={{ transform: `translateY(${ty}px)`, opacity, width: '100%', height: '100%' }}
          >
            {child}
          </div>
        );
      })}
    </>
  );
};

// ---------------------------------------------------------------------------
// 16. ElasticPop — scale overshoot spring pop-in
// ---------------------------------------------------------------------------
export const ElasticPop: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;
  const animate = resolveMotion(
    {
      curve: 'spring',
      spring: { damping: 4, stiffness: 300, overshootClamping: false },
      duration: Math.round(36 * intensity),
    },
    fps
  );
  const progress = animate(frame, 0, 1);
  // At intensity=0: scale=1 (no-op via early return). At intensity=1: pop from 0→1+overshoot.
  const scale = 1 - intensity + intensity * progress;
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
