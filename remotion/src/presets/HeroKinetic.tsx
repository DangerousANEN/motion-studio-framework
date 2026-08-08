import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';

export const BRAND = {
  bg: '#0E0F11',
  surface: '#181A20',
  gold: '#E6C475',
  neon: '#00FF88',
  cyan: '#00D4FF',
  text: '#FFFFFF',
  darkBorder: '#000000',
  shadowColor: '#000000',
};

export const HeroKinetic: React.FC<BaseSceneProps> = ({
  title = 'HERO KINETIC',
  subtitle = 'DYNAMIC POP TYPOGRAPHY',
  accentColor = BRAND.gold,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

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

      {/* Decorative Geometric Neo-Brutalist Badge */}
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
        }}
      >
        ★ LLM HUBS • SOTA TECH ★
      </div>

      {/* Main Kinetic Pop-Laboratory Card */}
      <div
        style={{
          transform: `scale(${scale}) rotate(${rotation}deg)`,
          backgroundColor: accentColor,
          padding: '36px 54px',
          borderRadius: '8px',
          border: '6px solid #000000',
          boxShadow: `${shadowOffset}px ${shadowOffset}px 0px ${BRAND.shadowColor}`,
          textAlign: 'center',
          maxWidth: '960px',
          zIndex: 5,
        }}
      >
        <h1
          style={{
            fontSize: '92px',
            fontWeight: 900,
            color: '#000000',
            letterSpacing: '-1px',
            margin: 0,
            lineHeight: 1.0,
            textTransform: 'uppercase',
          }}
        >
          {title}
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
            zIndex: 5,
          }}
        >
          <p
            style={{
              fontSize: '34px',
              fontWeight: 800,
              color: BRAND.text,
              letterSpacing: '2px',
              textTransform: 'uppercase',
              margin: 0,
            }}
          >
            {subtitle}
          </p>
        </div>
      )}
    </div>
  );
};
