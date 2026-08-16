import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';

const FONT = '"Inter", "SF Pro Display", -apple-system, sans-serif';

/**
 * SignalLaunchHero — Короткий cinematic reveal: новая модель появляется, а цена и результат читаются за один взгляд.
 *
 * Reads: title, subtitle, provider, metric, mediaUrl
 */
export const SignalLaunchHero: React.FC<BaseSceneProps> = ({
  title,
  subtitle,
  accentColor = BRAND.accentGreen,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);

  // Motion goes through resolveMotion so intensity presets and per-scene
  // overrides both work. Never interpolate on raw frame numbers here.
  const reveal = resolveMotion(motion, fps, 'reveal')(frame, 0, 1);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: BRAND.bg,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: safe.top,
          left: safe.left,
          width: safe.width,
          height: safe.height,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 24,
          opacity: reveal,
          transform: `translateY(${(1 - reveal) * 30}px)`,
        }}
      >
        {/* TODO: replace with the real scene body. */}
        {title && (
          <h1
            style={{
              margin: 0,
              fontFamily: FONT,
              fontSize: Math.round(height * 0.045),
              fontWeight: 900,
              color: BRAND.text,
              textAlign: 'center',
            }}
          >
            {title}
          </h1>
        )}
        {subtitle && (
          <p
            style={{
              margin: 0,
              fontFamily: FONT,
              fontSize: Math.round(height * 0.022),
              color: accentColor,
              textAlign: 'center',
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
};
