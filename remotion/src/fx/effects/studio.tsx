import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import type { EffectProps } from './camera';

/**
 * FocusPulse — a subtle, deterministic centre emphasis for data and comparison
 * scenes.  Unlike a zoom, it preserves layout geometry and is safe for dense
 * captions. Intensity 0 is a pixel-level no-op, as required by EffectStack.
 */
export const FocusPulse: React.FC<EffectProps> = ({ intensity = 1, children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  if (intensity === 0) return <>{children}</>;

  const midpoint = Math.max(1, Math.round(durationInFrames * 0.50));
  const rise = interpolate(frame, [0, midpoint, durationInFrames], [0, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const opacity = rise * Math.min(1, Math.max(0, intensity)) * 0.16;

  return (
    <AbsoluteFill>
      {children}
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          background: `radial-gradient(ellipse at 50% 50%, rgba(255,255,255,${opacity}) 0%, rgba(255,255,255,0) 64%)`,
          mixBlendMode: 'screen',
        }}
      />
    </AbsoluteFill>
  );
};
