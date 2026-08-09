/**
 * PostFX — the "juice" layer.
 *
 * WHY THIS EXISTS
 * ---------------
 * The vision audit of v4 output was explicit about what was missing:
 * "no subtle bloom, no chromatic aberration, no glassmorphism, no gradient
 * mesh reflections, no volumetric lighting" and "flat solid fills".
 *
 * This wraps scene content in a stack of cheap, GPU-friendly overlays that
 * read as expensive: grain, vignette, bloom, RGB split, scanlines. Everything
 * is driven by the active style kit's EffectProfile, so a scene opts in by
 * choosing a style rather than by hand-wiring filters.
 *
 * Deliberately CSS/SVG based, not WebGL: it composites over ANY scene content
 * including the Three.js presets, costs no extra render context, and cannot
 * fail the way a shader can.
 */
import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import type { EffectProfile } from '../theme/styleKits';

/** Animated film grain. Regenerated per frame so it shimmers like real grain. */
const Grain: React.FC<{ opacity: number }> = ({ opacity }) => {
  const frame = useCurrentFrame();
  if (opacity <= 0) return null;
  // Reseed per frame; `random` is deterministic so renders stay reproducible.
  const seed = Math.floor(random(`grain-${frame}`) * 100000);
  return (
    <AbsoluteFill
      style={{
        opacity,
        mixBlendMode: 'overlay',
        pointerEvents: 'none',
      }}
    >
      <svg width="100%" height="100%">
        <filter id={`grain-${seed}`}>
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.85"
            numOctaves={3}
            seed={seed}
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Edge darkening — pulls the eye to the centre. */
const Vignette: React.FC<{ strength: number }> = ({ strength }) => {
  if (strength <= 0) return null;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        background: `radial-gradient(ellipse at center, transparent 42%, rgba(0,0,0,${strength}) 100%)`,
      }}
    />
  );
};

/** Scanlines / CRT overlay. */
const Scanlines: React.FC<{ strength: number }> = ({ strength }) => {
  if (strength <= 0) return null;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        opacity: strength,
        backgroundImage:
          'repeating-linear-gradient(to bottom, rgba(0,0,0,0.6) 0px, rgba(0,0,0,0.6) 1px, transparent 1px, transparent 4px)',
        mixBlendMode: 'multiply',
      }}
    />
  );
};

/**
 * Bloom. Duplicates the content, blurs it, and screens it back over itself.
 * `children` is rendered twice — acceptable for DOM content, and the blurred
 * copy is aria-hidden so it never doubles up for accessibility tooling.
 */
const Bloom: React.FC<{ strength: number; children: React.ReactNode }> = ({
  strength,
  children,
}) => {
  if (strength <= 0) return <>{children}</>;
  return (
    <>
      {children}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          filter: `blur(${18 * strength}px) brightness(1.25)`,
          opacity: Math.min(0.85, strength),
          mixBlendMode: 'screen',
        }}
      >
        {children}
      </AbsoluteFill>
    </>
  );
};

/**
 * Chromatic aberration — offset red/blue copies.
 * `pulse` (0..1) lets a scene spike the effect on an impact frame.
 */
const Chromatic: React.FC<{ strength: number; pulse?: number; children: React.ReactNode }> = ({
  strength,
  pulse = 0,
  children,
}) => {
  const amount = strength * (1 + pulse * 4);
  if (amount <= 0) return <>{children}</>;
  const px = amount * 6;
  return (
    <>
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          transform: `translateX(${-px}px)`,
          filter: 'url(#msf-chroma-r)',
          opacity: 0.5,
          mixBlendMode: 'screen',
        }}
      >
        {children}
      </AbsoluteFill>
      {children}
      <AbsoluteFill
        aria-hidden
        style={{
          pointerEvents: 'none',
          transform: `translateX(${px}px)`,
          filter: 'url(#msf-chroma-b)',
          opacity: 0.5,
          mixBlendMode: 'screen',
        }}
      >
        {children}
      </AbsoluteFill>
    </>
  );
};

/** SVG colour-channel filters used by <Chromatic>. Mounted once. */
const ChromaFilters: React.FC = () => (
  <svg width={0} height={0} style={{ position: 'absolute' }} aria-hidden>
    <filter id="msf-chroma-r">
      <feColorMatrix
        type="matrix"
        values="1 0 0 0 0
                0 0 0 0 0
                0 0 0 0 0
                0 0 0 1 0"
      />
    </filter>
    <filter id="msf-chroma-b">
      <feColorMatrix
        type="matrix"
        values="0 0 0 0 0
                0 0 0 0 0
                0 0 1 0 0
                0 0 0 1 0"
      />
    </filter>
  </svg>
);

export type PostFXProps = {
  effects: EffectProfile;
  /** 0..1 spike for impact moments (beat hits, reveals). */
  pulse?: number;
  children: React.ReactNode;
};

/**
 * Composite wrapper. Order matters: colour-channel work happens on the content,
 * then light is added, then physical-medium artefacts sit on top.
 */
export const PostFX: React.FC<PostFXProps> = ({ effects, pulse = 0, children }) => {
  return (
    <AbsoluteFill>
      <ChromaFilters />
      <Bloom strength={effects.bloom}>
        <Chromatic strength={effects.chromatic} pulse={pulse}>
          {children}
        </Chromatic>
      </Bloom>
      <Scanlines strength={effects.scanlines} />
      <Vignette strength={effects.vignette} />
      <Grain opacity={effects.grain} />
    </AbsoluteFill>
  );
};
