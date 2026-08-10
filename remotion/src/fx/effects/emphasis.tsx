/**
 * Emphasis / loop effects — 16 composable wrappers.
 *
 * Contract: intensity=0 → pixel-perfect no-op.
 * All effects loop continuously while mounted.
 * Stochastic effects use mulberry32(seed) — never Math.random().
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

/** Simple sine-based loop using frame: period in frames. */
function sinLoop(frame: number, period: number): number {
  return Math.sin((frame / period) * Math.PI * 2);
}

// ---------------------------------------------------------------------------
// 1. Pulse — scale pulses rhythmically
// ---------------------------------------------------------------------------
export const Pulse: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const sin = sinLoop(frame, 30);
  const scale = 1 + sin * 0.08 * intensity;
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
// 2. Breathe — slow scale breathe
// ---------------------------------------------------------------------------
export const Breathe: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const sin = sinLoop(frame, 90);
  const scale = 1 + sin * 0.04 * intensity;
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
// 3. Shake — horizontal shake (stochastic seed for phase)
// ---------------------------------------------------------------------------
export const Shake: React.FC<EffectProps> = ({ children, intensity = 1, seed = 42 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const rng = mulberry32(seed + frame);
  // Per-frame seeded noise-like shake
  const tx = (rng() - 0.5) * 2 * 12 * intensity;
  return (
    <div style={{ transform: `translateX(${tx}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 4. Wobble — rotation wobble
// ---------------------------------------------------------------------------
export const Wobble: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const sin = sinLoop(frame, 20);
  const deg = sin * 5 * intensity;
  return (
    <div
      style={{
        transform: `rotate(${deg}deg)`,
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
// 5. Jitter — small random per-frame XY displacement (stochastic)
// ---------------------------------------------------------------------------
export const Jitter: React.FC<EffectProps> = ({ children, intensity = 1, seed = 42 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const rng = mulberry32(seed + frame * 7);
  const tx = (rng() - 0.5) * 2 * 6 * intensity;
  const ty = (rng() - 0.5) * 2 * 6 * intensity;
  return (
    <div style={{ transform: `translate(${tx}px, ${ty}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 6. Bounce — vertical bounce loop
// ---------------------------------------------------------------------------
export const Bounce: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  // |sin| so it only bounces up
  const t = Math.abs(sinLoop(frame, 30));
  const ty = -t * 20 * intensity;
  return (
    <div style={{ transform: `translateY(${ty}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 7. Float — slow vertical float loop
// ---------------------------------------------------------------------------
export const Float: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const sin = sinLoop(frame, 60);
  const ty = sin * 12 * intensity;
  return (
    <div style={{ transform: `translateY(${ty}px)`, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 8. Swing — pendulum rotation
// ---------------------------------------------------------------------------
export const Swing: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const sin = sinLoop(frame, 40);
  const deg = sin * 8 * intensity;
  return (
    <div
      style={{
        transform: `rotate(${deg}deg)`,
        transformOrigin: 'top center',
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 9. HeartBeat — double-pulse scale mimicking heartbeat
// ---------------------------------------------------------------------------
export const HeartBeat: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  // Two peaks per period
  const period = 30;
  const t = (frame % period) / period;
  // Double bump: beat at t=0.1 and t=0.25
  const beat =
    Math.max(0, Math.exp(-((t - 0.1) * (t - 0.1)) / 0.002)) +
    Math.max(0, 0.7 * Math.exp(-((t - 0.25) * (t - 0.25)) / 0.003));
  const scale = 1 + beat * 0.15 * intensity;
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
// 10. Flash — opacity flash on a beat
// ---------------------------------------------------------------------------
export const Flash: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const period = 30;
  const t = (frame % period) / period;
  // Sharp flash at t=0
  const flash = Math.exp(-(t * t) / 0.01);
  const opacity = 1 - flash * 0.6 * intensity;
  return (
    <div style={{ opacity, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
};

// ---------------------------------------------------------------------------
// 11. Glow — animated CSS drop-shadow glow
// ---------------------------------------------------------------------------
export const Glow: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const sin = (sinLoop(frame, 60) + 1) / 2; // 0..1
  const glowSize = (8 + sin * 12) * intensity;
  const glowOpacity = (0.4 + sin * 0.4) * intensity;

  // drop-shadow alone is invisible whenever the child is opaque edge to edge:
  // it blurs the child's alpha silhouette and draws it *behind* the child, so a
  // full-frame opaque layer hides its own shadow and the effect silently does
  // nothing. Pixel proof caught exactly that — Glow was byte-identical to bare
  // at every sampled frame. The additive bloom overlay below is drawn on top,
  // so the effect registers on opaque and transparent content alike, while the
  // drop-shadow still does the nice edge work for cut-out shapes.
  return (
    <div
      style={{
        filter: `drop-shadow(0 0 ${glowSize}px rgba(255,200,100,${glowOpacity}))`,
        width: '100%',
        height: '100%',
        position: 'relative',
      }}
    >
      {children}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          mixBlendMode: 'screen',
          opacity: glowOpacity * 0.5,
          background:
            `radial-gradient(ellipse at 50% 50%, rgba(255,200,100,0.55) 0%, ` +
            `rgba(255,200,100,0.18) 45%, rgba(255,200,100,0) 72%)`,
        }}
      />
    </div>
  );
};

// ---------------------------------------------------------------------------
// 12. Shimmer — animated diagonal highlight sweep
// ---------------------------------------------------------------------------
export const Shimmer: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const period = 60;
  const t = (frame % period) / period;
  const x = t * 200 - 50; // -50% to 150%
  const shimmerOpacity = intensity * 0.6;
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {children}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(105deg, transparent ${x - 15}%, rgba(255,255,255,${shimmerOpacity}) ${x}%, transparent ${x + 15}%)`,
          pointerEvents: 'none',
          mixBlendMode: 'screen',
        }}
      />
    </div>
  );
};

// ---------------------------------------------------------------------------
// 13. Sheen — subtle surface sheen pass
// ---------------------------------------------------------------------------
export const Sheen: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const period = 90;
  const t = (frame % period) / period;
  const x = t * 150 - 25;
  const sheenOpacity = intensity * 0.25;
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {children}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(80deg, transparent ${x - 10}%, rgba(255,255,255,${sheenOpacity}) ${x}%, transparent ${x + 10}%)`,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};

// ---------------------------------------------------------------------------
// 14. Ripple — circular expanding ring from center
// ---------------------------------------------------------------------------
export const Ripple: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const period = 45;
  const t = (frame % period) / period;
  const rippleScale = 1 + t * 0.4 * intensity;
  const rippleOpacity = (1 - t) * intensity * 0.5;
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {children}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            width: '60%',
            paddingBottom: '60%',
            borderRadius: '50%',
            border: `2px solid rgba(255,255,255,${rippleOpacity})`,
            transform: `scale(${rippleScale})`,
            position: 'absolute',
            top: '20%',
          }}
        />
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// 15. Tremble — rapid micro-shake (stochastic)
// ---------------------------------------------------------------------------
export const Tremble: React.FC<EffectProps> = ({ children, intensity = 1, seed = 42 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const rng = mulberry32(seed + frame * 13);
  const tx = (rng() - 0.5) * 2 * 4 * intensity;
  const ty = (rng() - 0.5) * 2 * 4 * intensity;
  const deg = (rng() - 0.5) * 2 * 1.5 * intensity;
  return (
    <div
      style={{
        transform: `translate(${tx}px, ${ty}px) rotate(${deg}deg)`,
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
// 16. Squash — vertical squash-and-stretch loop
// ---------------------------------------------------------------------------
export const Squash: React.FC<EffectProps> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (intensity === 0) return <>{children}</>;
  const sin = sinLoop(frame, 30);
  // Squash: scaleY shrinks, scaleX compensates (volume preservation)
  const squash = sin * 0.15 * intensity;
  const scaleY = 1 - squash;
  const scaleX = 1 + squash * 0.5;
  return (
    <div
      style={{
        transform: `scaleX(${scaleX}) scaleY(${scaleY})`,
        transformOrigin: 'center bottom',
        width: '100%',
        height: '100%',
      }}
    >
      {children}
    </div>
  );
};
