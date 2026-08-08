import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';

export const GridGridFloor: React.FC<BaseSceneProps> = ({
  title,
  text,
  subtitle,
  accentColor = BRAND.neon,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const displayTitle = title || text || 'GRID FLOOR 3D';

  // Perspective floor grid animation
  const gridOffset = (frame * 3) % 60;

  // Title spring pop
  const cardSpring = spring({
    frame,
    fps,
    config: {
      damping: 14,
      stiffness: 90,
    },
  });

  const cardTranslateY = interpolate(cardSpring, [0, 1], [100, 0]);
  const cardOpacity = interpolate(cardSpring, [0, 1], [0, 1]);

  const len = displayTitle.length;
  const fontSize = len > 50 ? '48px' : len > 25 ? '60px' : '80px';

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
        perspective: '800px',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* 3D Wireframe Perspective Grid Floor */}
      <div
        style={{
          position: 'absolute',
          bottom: '-30%',
          width: '200%',
          height: '100%',
          transform: 'rotateX(75deg)',
          transformOrigin: '50% 100%',
          backgroundImage: `
            linear-gradient(to right, ${accentColor}30 1px, transparent 1px),
            linear-gradient(to bottom, ${accentColor}30 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          backgroundPosition: `0px ${gridOffset}px`,
          maskImage: 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%)',
          WebkitMaskImage: 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%)',
          pointerEvents: 'none',
        }}
      />

      {/* Floating 3D Neo-Brutalist Card */}
      <div
        style={{
          opacity: cardOpacity,
          transform: `translateY(${cardTranslateY}px) translateZ(50px)`,
          backgroundColor: BRAND.surface,
          border: `4px solid ${accentColor}`,
          borderRadius: '24px',
          padding: '48px 40px',
          textAlign: 'center',
          boxShadow: `12px 12px 0px ${accentColor}`,
          zIndex: 5,
          maxWidth: '900px',
          width: '90%',
          boxSizing: 'border-box',
          overflowWrap: 'break-word',
          wordBreak: 'break-word',
        }}
      >
        <div
          style={{
            display: 'inline-block',
            backgroundColor: accentColor,
            color: BRAND.bg,
            fontWeight: 900,
            fontSize: '20px',
            padding: '6px 18px',
            borderRadius: '6px',
            letterSpacing: '2px',
            textTransform: 'uppercase',
            marginBottom: '20px',
          }}
        >
          MSF 3D SCENE
        </div>

        <h1
          style={{
            fontSize,
            fontWeight: 900,
            color: BRAND.text,
            margin: 0,
            lineHeight: 1.1,
            letterSpacing: '-1px',
            textTransform: 'uppercase',
            overflowWrap: 'break-word',
            wordBreak: 'break-word',
          }}
        >
          {displayTitle}
        </h1>

        {subtitle && (
          <p
            style={{
              fontSize: '30px',
              fontWeight: 600,
              color: BRAND.muted,
              marginTop: '20px',
              marginBottom: 0,
              letterSpacing: '1px',
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
};
