/**
 * Scene backdrops — the layer behind every preset's content.
 *
 * WHY
 * ---
 * Every preset currently paints its own flat `backgroundColor` and stops there.
 * That is the "flat solid fills / muddy dark mode" note from the vision audit,
 * and it is also why all scenes read as the same scene: identical empty
 * background, different text on top.
 *
 * `StyleKit.backdrop` has named six treatments since styleKits.ts was written
 * but nothing rendered them. This is that renderer.
 *
 * DETERMINISM
 * -----------
 * Anything random here is seeded (mulberry32) and derived from the frame, never
 * from `Math.random()`. Remotion renders frames out of order and in parallel
 * workers; an unseeded random would produce a different backdrop per frame and
 * flicker violently. Every generator below takes an explicit seed.
 *
 * COST
 * ----
 * These are CSS gradients and SVG, not WebGL. A backdrop must not cost more
 * than the content in front of it — `mesh` in particular is four radial
 * gradients on a slow drift, not a shader.
 */
import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import type { BackdropKind } from './styleKits';
import type { Theme } from '../presets/brand';
import { useStyle } from './StyleContext';

/** Deterministic PRNG — same seed, same sequence, on every worker. */
const mulberry32 = (seed: number) => {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

const hexToRgba = (hex: string, alpha: number): string => {
  const m = hex.replace('#', '');
  const full = m.length === 3 ? m.split('').map((c) => c + c).join('') : m;
  const n = parseInt(full, 16);
  if (Number.isNaN(n) || full.length !== 6) return `rgba(255,255,255,${alpha})`;
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
};

interface BackdropProps {
  /** Overrides the active style kit's backdrop. */
  kind?: BackdropKind;
  /** Overrides the palette. Defaults to the active style's theme. */
  theme?: Theme;
  /** Scales visual strength, 0..1. Lets a busy scene calm its own background. */
  opacity?: number;
  seed?: number;
}

/**
 * Technical isometric grid — the Pop-Laboratory signature.
 * Two layered line sets with a perspective fade toward the top.
 */
const GridBackdrop: React.FC<{ theme: Theme; strength: number }> = ({ theme, strength }) => {
  const line = hexToRgba(theme.neon, 0.09 * strength);
  const fine = hexToRgba(theme.muted, 0.07 * strength);
  return (
    <>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `linear-gradient(${line} 1px, transparent 1px), linear-gradient(90deg, ${line} 1px, transparent 1px)`,
          backgroundSize: '120px 120px',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `linear-gradient(${fine} 1px, transparent 1px), linear-gradient(90deg, ${fine} 1px, transparent 1px)`,
          backgroundSize: '24px 24px',
          // Fades the fine grid out toward the top so the frame has depth
          // instead of reading as graph paper.
          maskImage: 'linear-gradient(to top, black 30%, transparent 85%)',
          WebkitMaskImage: 'linear-gradient(to top, black 30%, transparent 85%)',
        }}
      />
    </>
  );
};

/**
 * Animated gradient mesh — the "expensive" modern look.
 * Four radial blobs orbiting on slow, mutually-prime periods so the pattern
 * never visibly repeats within a short.
 */
const MeshBackdrop: React.FC<{ theme: Theme; strength: number; frame: number; fps: number }> = ({
  theme,
  strength,
  frame,
  fps,
}) => {
  const t = frame / fps;
  const blobs = [
    { c: theme.neon, x: 30 + Math.sin(t * 0.21) * 14, y: 26 + Math.cos(t * 0.17) * 12, r: 52 },
    { c: theme.cyan, x: 72 + Math.cos(t * 0.13) * 13, y: 34 + Math.sin(t * 0.19) * 15, r: 46 },
    { c: theme.gold, x: 46 + Math.sin(t * 0.11) * 16, y: 74 + Math.cos(t * 0.23) * 11, r: 44 },
    { c: theme.accentCyan, x: 80 + Math.sin(t * 0.29) * 10, y: 82 + Math.cos(t * 0.15) * 9, r: 38 },
  ];
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: blobs
          .map((b) => `radial-gradient(circle at ${b.x}% ${b.y}%, ${hexToRgba(b.c, 0.34 * strength)} 0%, transparent ${b.r}%)`)
          .join(', '),
        filter: 'blur(4px)',
      }}
    />
  );
};

/** Organic drifting noise field via SVG turbulence. */
const NoiseBackdrop: React.FC<{ theme: Theme; strength: number; frame: number; seed: number }> = ({
  theme,
  strength,
  frame,
  seed,
}) => {
  // Frequency crawls very slowly so the field breathes without boiling.
  const freq = 0.008 + Math.sin(frame / 220) * 0.0022;
  const id = `noiseBackdrop${seed}`;
  return (
    <>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse at 50% 40%, ${hexToRgba(theme.neon, 0.14 * strength)} 0%, transparent 62%)`,
        }}
      />
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.5 * strength }}>
        <filter id={id}>
          <feTurbulence
            type="fractalNoise"
            baseFrequency={freq}
            numOctaves={3}
            seed={seed}
            result="n"
          />
          <feColorMatrix in="n" type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#${id})`} opacity={0.5} />
      </svg>
    </>
  );
};

/** Dot matrix — quieter than the grid, good behind dense text. */
const DotsBackdrop: React.FC<{ theme: Theme; strength: number }> = ({ theme, strength }) => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      backgroundImage: `radial-gradient(${hexToRgba(theme.muted, 0.3 * strength)} 1.6px, transparent 1.7px)`,
      backgroundSize: '34px 34px',
      maskImage: 'radial-gradient(ellipse at 50% 45%, black 25%, transparent 78%)',
      WebkitMaskImage: 'radial-gradient(ellipse at 50% 45%, black 25%, transparent 78%)',
    }}
  />
);

/** Retro CRT scan lines with a slow rolling bright band. */
const ScanlinesBackdrop: React.FC<{ theme: Theme; strength: number; frame: number; height: number }> = ({
  theme,
  strength,
  frame,
  height,
}) => {
  const roll = ((frame * 1.6) % (height + 400)) - 200;
  return (
    <>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `repeating-linear-gradient(to bottom, ${hexToRgba(theme.muted, 0.16 * strength)} 0px, ${hexToRgba(theme.muted, 0.16 * strength)} 1px, transparent 1px, transparent 4px)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: roll,
          height: 180,
          background: `linear-gradient(to bottom, transparent, ${hexToRgba(theme.neon, 0.07 * strength)}, transparent)`,
        }}
      />
    </>
  );
};

/**
 * Flat wash. Not literally nothing: a soft off-centre vignette-lift keeps the
 * frame from looking like a dead grey rectangle while staying maximally
 * readable behind dense information.
 */
const PlainBackdrop: React.FC<{ theme: Theme; strength: number }> = ({ theme, strength }) => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      background: `radial-gradient(ellipse at 50% 32%, ${hexToRgba(theme.surface, 0.9 * strength)} 0%, transparent 70%)`,
    }}
  />
);

/**
 * Renders the active style's backdrop.
 *
 * Absolutely positioned and `pointerEvents: none`; a preset drops it as its
 * first child and paints content on top:
 *
 *   <div style={{ position:'absolute', inset:0, background: theme.bg }}>
 *     <Backdrop />
 *     ...content...
 *   </div>
 */
export const Backdrop: React.FC<BackdropProps> = ({
  kind,
  theme: themeOverride,
  opacity = 1,
  seed = 7,
}) => {
  const style = useStyle();
  const theme = themeOverride ?? style.theme;
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const resolved: BackdropKind = kind ?? style.kit.backdrop;
  const strength = Math.max(0, Math.min(1, opacity));

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {resolved === 'grid' && <GridBackdrop theme={theme} strength={strength} />}
      {resolved === 'mesh' && <MeshBackdrop theme={theme} strength={strength} frame={frame} fps={fps} />}
      {resolved === 'noise' && <NoiseBackdrop theme={theme} strength={strength} frame={frame} seed={seed} />}
      {resolved === 'dots' && <DotsBackdrop theme={theme} strength={strength} />}
      {resolved === 'scanlines' && (
        <ScanlinesBackdrop theme={theme} strength={strength} frame={frame} height={height} />
      )}
      {resolved === 'plain' && <PlainBackdrop theme={theme} strength={strength} />}
    </div>
  );
};

/** Exported for tests and probes that need to enumerate every treatment. */
export const BACKDROP_KINDS: BackdropKind[] = [
  'grid',
  'mesh',
  'noise',
  'dots',
  'scanlines',
  'plain',
];

export { mulberry32, hexToRgba };
