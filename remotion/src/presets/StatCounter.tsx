import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';

export const StatCounter: React.FC<BaseSceneProps> = ({
  statValue = 100,
  statPrefix = '',
  statSuffix = '%',
  statLabel,
  title,
  text,
  badge,
  accentColor = BRAND.neon,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const label = statLabel || title || text || '⚠ NO STAT LABEL IN SPEC';

  const countSpring = spring({
    frame,
    fps,
    config: {
      damping: 18,
      stiffness: 80,
    },
  });

  // Keep fractional precision when the target value is fractional (e.g. 6.8 GB),
  // otherwise Math.round would display "6 GB" and misreport the stat.
  const decimals = Number.isInteger(statValue)
    ? 0
    : Math.min(2, (String(statValue).split('.')[1] ?? '').length);
  const rawValue = interpolate(countSpring, [0, 1], [0, statValue]);
  const currentValue = decimals === 0
    ? Math.round(rawValue)
    : Number(rawValue.toFixed(decimals));
  const scale = interpolate(countSpring, [0, 1], [0.8, 1]);
  const opacity = interpolate(frame, [0, 10], [0, 1], { extrapolateLeft: 'clamp' });

  const ringProgress = interpolate(countSpring, [0, 1], [0, 280]);

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 40px',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Background radial glow */}
      <div
        style={{
          position: 'absolute',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}20 0%, transparent 70%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Main Counter Card Container */}
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          backgroundColor: BRAND.surface,
          border: `2px solid ${accentColor}40`,
          borderRadius: '32px',
          padding: '60px 60px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          boxShadow: `0 20px 50px rgba(0,0,0,0.5), 0 0 30px ${accentColor}20`,
          position: 'relative',
          maxWidth: '900px',
          width: '90%',
          boxSizing: 'border-box',
          overflowWrap: 'break-word',
          wordBreak: 'break-word',
        }}
      >
        {/* Optional corner accent — opt-in via spec, never a hardcoded label */}
        {badge && (
          <div
            style={{
              position: 'absolute',
              top: 20,
              right: 25,
              fontSize: '18px',
              color: accentColor,
              fontWeight: 800,
              letterSpacing: '2px',
            }}
          >
            {badge}
          </div>
        )}

        {/* Counter Number Display */}
        <div
          style={{
            fontSize: '130px',
            fontWeight: 900,
            color: BRAND.text,
            letterSpacing: '-4px',
            lineHeight: 1,
            display: 'flex',
            alignItems: 'baseline',
            textShadow: `0 0 40px ${accentColor}60`,
          }}
        >
          {statPrefix && (
            <span style={{ fontSize: '80px', color: accentColor, marginRight: '8px' }}>
              {statPrefix}
            </span>
          )}
          <span>{currentValue}</span>
          {statSuffix && (
            <span style={{ fontSize: '80px', color: accentColor, marginLeft: '8px' }}>
              {statSuffix}
            </span>
          )}
        </div>

        {/* Dynamic Progress Bar */}
        <div
          style={{
            width: '280px',
            height: '8px',
            backgroundColor: '#2A2D34',
            borderRadius: '4px',
            marginTop: '30px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${ringProgress}px`,
              height: '100%',
              backgroundColor: accentColor,
              borderRadius: '4px',
              boxShadow: `0 0 12px ${accentColor}`,
            }}
          />
        </div>

        {/* Label */}
        {label && (
          <div
            style={{
              marginTop: '25px',
              fontSize: '28px',
              fontWeight: 700,
              color: BRAND.muted,
              letterSpacing: '2px',
              textTransform: 'uppercase',
              textAlign: 'center',
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
            }}
          >
            {label}
          </div>
        )}
      </div>
    </div>
  );
};
