import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';

export { BRAND };

export const HeroKinetic: React.FC<BaseSceneProps> = ({
  title,
  text,
  subtitle,
  badge,
  accentColor = BRAND.gold,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const displayTitle = title || text || '⚠ NO TITLE IN SPEC';

  const len = displayTitle.length;
  const fontSize = len > 60 ? '48px' : len > 30 ? '64px' : '88px';

  // Snappy Neo-Brutalist spring physics (stiff, quick snap)
  const springSnap = spring({
    frame,
    fps,
    config: {
      damping: 10,
      stiffness: 180,
      mass: 0.6,
    },
  });

  const scale = interpolate(springSnap, [0, 1], [0.4, 1]);
  const rotation = interpolate(springSnap, [0, 1], [-6, -2]); // Signature pop-brutalist tilt
  const shadowOffset = interpolate(springSnap, [0, 1], [0, 14]);

  // Subtitle delayed entry
  const subSpring = spring({
    frame: frame - 8,
    fps,
    config: {
      damping: 12,
      stiffness: 140,
    },
  });

  const subOffsetY = interpolate(subSpring, [0, 1], [40, 0]);
  const subOpacity = interpolate(subSpring, [0, 1], [0, 1]);

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: '"Impact", "Arial Black", system-ui, sans-serif',
      }}
    >
      {/* Neo-Brutalist Isometric Background Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.05) 2px, transparent 2px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 2px, transparent 2px)
          `,
          backgroundSize: '60px 60px',
          opacity: 0.6,
        }}
      />

      {/* Decorative Geometric Neo-Brutalist Badge (Optional) */}
      {badge && (
        <div
          style={{
            position: 'absolute',
            top: '120px',
            backgroundColor: BRAND.neon,
            color: '#000000',
            padding: '12px 28px',
            borderRadius: '4px',
            border: '4px solid #000000',
            boxShadow: '6px 6px 0px #000000',
            fontSize: '28px',
            fontWeight: 900,
            textTransform: 'uppercase',
            letterSpacing: '2px',
            transform: 'rotate(3deg)',
            maxWidth: '900px',
            textAlign: 'center',
            overflowWrap: 'break-word',
            wordBreak: 'break-word',
          }}
        >
          {badge}
        </div>
      )}

      {/* Main Kinetic Pop-Laboratory Card */}
      <div
        style={{
          transform: `scale(${scale}) rotate(${rotation}deg)`,
          backgroundColor: accentColor,
          padding: '36px 48px',
          borderRadius: '8px',
          border: '6px solid #000000',
          boxShadow: `${shadowOffset}px ${shadowOffset}px 0px ${BRAND.shadowColor}`,
          textAlign: 'center',
          maxWidth: '920px',
          width: '90%',
          boxSizing: 'border-box',
          overflowWrap: 'break-word',
          wordBreak: 'break-word',
          zIndex: 5,
        }}
      >
        <h1
          style={{
            fontSize,
            fontWeight: 900,
            color: '#000000',
            letterSpacing: '-1px',
            margin: 0,
            lineHeight: 1.1,
            textTransform: 'uppercase',
            overflowWrap: 'break-word',
            wordBreak: 'break-word',
          }}
        >
          {displayTitle}
        </h1>
      </div>

      {/* Subtitle Neo-Brutalist Tag */}
      {subtitle && (
        <div
          style={{
            marginTop: '40px',
            transform: `translateY(${subOffsetY}px)`,
            opacity: subOpacity,
            backgroundColor: BRAND.surface,
            border: '4px solid #000000',
            boxShadow: '8px 8px 0px #000000',
            padding: '20px 36px',
            borderRadius: '6px',
            maxWidth: '900px',
            boxSizing: 'border-box',
            overflowWrap: 'break-word',
            wordBreak: 'break-word',
            zIndex: 5,
          }}
        >
          <p
            style={{
              fontSize: '32px',
              fontWeight: 800,
              color: BRAND.text,
              letterSpacing: '1px',
              textTransform: 'uppercase',
              margin: 0,
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
            }}
          >
            {subtitle}
          </p>
        </div>
      )}
    </div>
  );
};
