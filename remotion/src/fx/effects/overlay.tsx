/**
 * Atmosphere / overlay effects — Section 2.7 of the MSF Expansion Plan.
 *
 * CONTRACT
 * --------
 * interface EffectProps {
 *   children: React.ReactNode;
 *   intensity?: number;   // 0..1, default 1; intensity=0 MUST be a pixel-perfect no-op
 *   seed?: number;        // required for stochastic effects
 * }
 *
 * All particle overlays use mulberry32(seed) — a seeded, pure function of
 * (frame, seed). State is never accumulated across frames because Remotion
 * renders frames out of order and in parallel.
 */
import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';

export interface EffectProps {
  children: React.ReactNode;
  intensity?: number;
  seed?: number;
}

// ---------------------------------------------------------------------------
// Seeded PRNG — mulberry32
// Returns a deterministic pseudo-random number generator seeded once per call.
// ---------------------------------------------------------------------------
function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Derive a deterministic pseudo-random sequence for a given frame + seed. */
function frameRng(frame: number, seed: number, count: number): number[] {
  const rng = mulberry32(seed * 999983 + frame * 2654435761);
  const out: number[] = [];
  for (let i = 0; i < count; i++) out.push(rng());
  return out;
}

// ---------------------------------------------------------------------------
// 1. ParticlesDust
// ---------------------------------------------------------------------------
export const ParticlesDust: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  const count = Math.round(60 * intensity);
  const rng = mulberry32(seed * 7 + frame * 6364136223846793005);
  const particles = Array.from({ length: count }, () => ({
    x: rng() * width,
    y: rng() * height,
    r: rng() * 2 + 0.5,
    a: rng() * intensity * 0.6,
  }));

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          {particles.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r={p.r}
              fill={`rgba(210,195,160,${p.a})`}
            />
          ))}
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 2. ParticlesSnow
// ---------------------------------------------------------------------------
export const ParticlesSnow: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  const count = Math.round(80 * intensity);
  // Each flake has a fixed horizontal lane derived from seed; vertical position drifts with frame
  const flakes = Array.from({ length: count }, (_, i) => {
    const laneRng = mulberry32(seed * 13 + i * 99991);
    const x = laneRng() * width;
    const speed = 0.5 + laneRng() * 1.5;
    const r = 1 + laneRng() * 3 * intensity;
    const phase = laneRng() * height;
    const y = (phase + frame * speed) % height;
    const a = 0.4 + laneRng() * 0.5 * intensity;
    return { x, y, r, a };
  });

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          {flakes.map((f, i) => (
            <circle key={i} cx={f.x} cy={f.y} r={f.r} fill={`rgba(255,255,255,${f.a})`} />
          ))}
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 3. ParticlesSparks
// ---------------------------------------------------------------------------
export const ParticlesSparks: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  const count = Math.round(40 * intensity);
  const sparks = Array.from({ length: count }, (_, i) => {
    const laneRng = mulberry32(seed * 17 + i * 131071);
    const x0 = laneRng() * width;
    const y0 = height * (0.5 + laneRng() * 0.5);
    const vx = (laneRng() - 0.5) * 4;
    const vy = -(2 + laneRng() * 4);
    const life = 20 + Math.round(laneRng() * 20);
    const phase = Math.round(laneRng() * 60);
    const t = ((frame - phase) % life + life) % life;
    const alpha = Math.max(0, 1 - t / life) * intensity;
    return {
      x: x0 + vx * t,
      y: y0 + vy * t + 0.1 * t * t,
      a: alpha,
      len: 4 + laneRng() * 6,
      vx,
      vy,
    };
  });

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          {sparks.map((s, i) => (
            <line
              key={i}
              x1={s.x}
              y1={s.y}
              x2={s.x + s.vx * 3}
              y2={s.y + s.vy * 3}
              stroke={`rgba(255,220,80,${s.a})`}
              strokeWidth={1.5}
            />
          ))}
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 4. Confetti
// ---------------------------------------------------------------------------
const CONFETTI_COLORS = [
  '#FF6B6B',
  '#FFE66D',
  '#4ECDC4',
  '#45B7D1',
  '#96CEB4',
  '#FFEAA7',
  '#DDA0DD',
  '#98FB98',
];

export const Confetti: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  const count = Math.round(100 * intensity);
  const pieces = Array.from({ length: count }, (_, i) => {
    const r = mulberry32(seed * 23 + i * 524287);
    const x0 = r() * width;
    const vy = 2 + r() * 4;
    const vx = (r() - 0.5) * 2;
    const rot = r() * 360;
    const rotSpeed = (r() - 0.5) * 8;
    const size = 6 + r() * 10 * intensity;
    const color = CONFETTI_COLORS[Math.floor(r() * CONFETTI_COLORS.length)];
    const phase = Math.round(r() * 60);
    const t = (frame + phase) % (height / vy + 1);
    const x = x0 + vx * t;
    const y = (t * vy) % height;
    const angle = (rot + rotSpeed * t) % 360;
    return { x, y, size, color, angle };
  });

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          {pieces.map((p, i) => (
            <rect
              key={i}
              x={p.x - p.size / 2}
              y={p.y - p.size / 4}
              width={p.size}
              height={p.size / 2}
              fill={p.color}
              transform={`rotate(${p.angle} ${p.x} ${p.y})`}
              opacity={intensity}
            />
          ))}
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 5. RainStreaks
// ---------------------------------------------------------------------------
export const RainStreaks: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  const count = Math.round(120 * intensity);
  const streaks = Array.from({ length: count }, (_, i) => {
    const r = mulberry32(seed * 31 + i * 131071);
    const x = r() * width;
    const speed = 12 + r() * 8;
    const len = 20 + r() * 40;
    const phase = r() * height;
    const y = (phase + frame * speed) % (height + len);
    const a = 0.1 + r() * 0.4 * intensity;
    return { x, y, len, a };
  });

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          {streaks.map((s, i) => (
            <line
              key={i}
              x1={s.x}
              y1={s.y - s.len}
              x2={s.x + s.len * 0.1}
              y2={s.y}
              stroke={`rgba(180,210,255,${s.a})`}
              strokeWidth={1}
            />
          ))}
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 6. SmokeWisps
// ---------------------------------------------------------------------------
export const SmokeWisps: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  const count = Math.round(8 * intensity);
  const wisps = Array.from({ length: count }, (_, i) => {
    const r = mulberry32(seed * 37 + i * 86243);
    const cx = r() * width;
    const cy0 = height * 0.8 + r() * height * 0.2;
    const speed = 0.3 + r() * 0.5;
    const cx2 = cx + (r() - 0.5) * 200;
    const t = frame * speed;
    const y = cy0 - t;
    const a = Math.max(0, (1 - (cy0 - y) / (height * 0.7)) * intensity * 0.4);
    const sc = 30 + r() * 60 + (frame * speed) * 0.5;
    return { cx, cy0, cx2, y, a, sc };
  });

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          <defs>
            <filter id="smoke-blur">
              <feGaussianBlur stdDeviation="8" />
            </filter>
          </defs>
          {wisps.map((w, i) => (
            <ellipse
              key={i}
              cx={w.cx}
              cy={w.y % height}
              rx={w.sc}
              ry={w.sc * 0.5}
              fill={`rgba(200,200,200,${w.a})`}
              filter="url(#smoke-blur)"
            />
          ))}
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 7. NoiseOverlay
// ---------------------------------------------------------------------------
export const NoiseOverlay: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();

  if (intensity <= 0) return <>{children}</>;

  // Use per-frame seed for animated grain
  const noiseSeed = (seed * 999983 + frame * 2654435761) & 0xffffffff;
  const opacity = intensity * 0.15;

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none', opacity, mixBlendMode: 'overlay' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          <filter id={`noise-${noiseSeed}`}>
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.85"
              numOctaves={4}
              seed={noiseSeed & 0xffff}
              stitchTiles="stitch"
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter={`url(#noise-${noiseSeed})`} />
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 8. GridOverlay
// ---------------------------------------------------------------------------
export const GridOverlay: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  if (intensity <= 0) return <>{children}</>;

  // seed affects grid size for variety
  const rng = mulberry32(seed);
  const spacing = 40 + Math.round(rng() * 40);
  const opacity = intensity * 0.12;

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none', opacity }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          <defs>
            <pattern id={`grid-${seed}`} width={spacing} height={spacing} patternUnits="userSpaceOnUse">
              <path
                d={`M ${spacing} 0 L 0 0 0 ${spacing}`}
                fill="none"
                stroke="rgba(255,255,255,0.8)"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill={`url(#grid-${seed})`} />
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 9. ScanSweep
// ---------------------------------------------------------------------------
export const ScanSweep: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  // Sweep period: 3 seconds
  const period = fps * 3;
  const progress = (frame % period) / period;
  const yPct = progress * 100;
  const alpha = intensity * 0.5;

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          <defs>
            <linearGradient id={`sweep-grad-${seed}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(0,200,255,0)" />
              <stop offset="30%" stopColor={`rgba(0,200,255,${alpha})`} />
              <stop offset="50%" stopColor={`rgba(0,200,255,${alpha * 0.3})`} />
              <stop offset="100%" stopColor="rgba(0,200,255,0)" />
            </linearGradient>
          </defs>
          <rect
            x="0"
            y={`${yPct - 10}%`}
            width="100%"
            height="20%"
            fill={`url(#sweep-grad-${seed})`}
          />
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 10. SpotlightFollow
// ---------------------------------------------------------------------------
export const SpotlightFollow: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  // The spotlight follows a slow Lissajous path seeded by seed
  const rng = mulberry32(seed);
  const phaseX = rng() * Math.PI * 2;
  const phaseY = rng() * Math.PI * 2;
  const t = (frame / fps) * 0.5;
  const cx = width * 0.5 + Math.sin(t + phaseX) * width * 0.2;
  const cy = height * 0.5 + Math.cos(t * 0.7 + phaseY) * height * 0.15;
  const r = Math.min(width, height) * 0.4;

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          <defs>
            <radialGradient
              id={`spotlight-${seed}`}
              cx={cx / width}
              cy={cy / height}
              r={r / Math.min(width, height)}
              gradientUnits="objectBoundingBox"
            >
              <stop offset="0%" stopColor={`rgba(255,240,200,${intensity * 0.15})`} />
              <stop offset="60%" stopColor="rgba(255,240,200,0.02)" />
              <stop offset="100%" stopColor="rgba(0,0,0,0)" />
            </radialGradient>
          </defs>
          <rect width="100%" height="100%" fill={`url(#spotlight-${seed})`} />
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 11. CausticsLight
// ---------------------------------------------------------------------------
export const CausticsLight: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  const count = Math.round(6 * intensity);
  const t = frame / fps;
  const blobs = Array.from({ length: count }, (_, i) => {
    const r = mulberry32(seed * 41 + i * 104729);
    const cx = r() * width;
    const cy = r() * height;
    const speed = 0.3 + r() * 0.4;
    const phase = r() * Math.PI * 2;
    const rx = 60 + r() * 120;
    const ry = 40 + r() * 80;
    const rot = (t * speed * 30 + phase * 57) % 360;
    return { cx, cy, rx, ry, rot };
  });

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'screen' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          <defs>
            <filter id={`caustics-blur-${seed}`}>
              <feGaussianBlur stdDeviation="15" />
            </filter>
          </defs>
          {blobs.map((b, i) => (
            <ellipse
              key={i}
              cx={b.cx + Math.sin(t * 0.7 + i) * 30}
              cy={b.cy + Math.cos(t * 0.5 + i) * 20}
              rx={b.rx}
              ry={b.ry}
              fill={`rgba(100,180,255,${intensity * 0.07})`}
              transform={`rotate(${b.rot} ${b.cx} ${b.cy})`}
              filter={`url(#caustics-blur-${seed})`}
            />
          ))}
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------------------------------------------------------------------------
// 12. BokehLights
// ---------------------------------------------------------------------------
export const BokehLights: React.FC<EffectProps> = ({
  children,
  intensity = 1,
  seed = 42,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  if (intensity <= 0) return <>{children}</>;

  const COLORS = ['#ff9ef6', '#9ecbff', '#fffb9e', '#9effcb', '#ff9e9e'];
  const count = Math.round(20 * intensity);
  const t = frame / fps;

  const circles = Array.from({ length: count }, (_, i) => {
    const r = mulberry32(seed * 53 + i * 196613);
    const x = r() * width;
    const y = r() * height;
    const radius = 20 + r() * 80 * intensity;
    const speed = 0.2 + r() * 0.3;
    const phase = r() * Math.PI * 2;
    const dy = Math.sin(t * speed + phase) * 15;
    const alpha = (0.04 + r() * 0.08) * intensity;
    const color = COLORS[Math.floor(r() * COLORS.length)];
    return { x, y: y + dy, radius, alpha, color };
  });

  return (
    <>
      {children}
      <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'screen' }}>
        <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
          <defs>
            <filter id={`bokeh-blur-${seed}`}>
              <feGaussianBlur stdDeviation="12" />
            </filter>
          </defs>
          {circles.map((c, i) => (
            <circle
              key={i}
              cx={c.x}
              cy={c.y}
              r={c.radius}
              fill={c.color}
              opacity={c.alpha}
              filter={`url(#bokeh-blur-${seed})`}
            />
          ))}
        </svg>
      </AbsoluteFill>
    </>
  );
};
