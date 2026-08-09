import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';
import { fitOneLine, fitWrapped } from '../theme/layout';

/**
 * Single source of truth for GridGridFloor font stack.
 * `fitOneLine` and `fitWrapped` must measure with the exact same font family
 * applied to the rendered elements, otherwise calculated font sizes will overflow.
 */
const GRID_FONT = 'system-ui, -apple-system, sans-serif';

/**
 * 3D Neo-Brutalist Grid Floor scene with a floating pop card.
 *
 * Defect fixes & safe area integration:
 *  - `padding: '60px 40px'` put card content into the 380px bottom platform strip on Shorts/Reels.
 *  - `flex: 1` container collapsed to 0 height under shader transitions (e.g. dissolve/filmBurn).
 *  - Hardcoded `spring({ damping: 14, stiffness: 90 })` bypassed the unified motion layer.
 *  - Character count ladder (`len > 50 ? ...`) gave inaccurate font sizes for wide/narrow glyphs.
 *  - `maxWidth: '900px'` and `width: '90%'` ignored safeArea boundaries on small canvas sizes.
 */
export const GridGridFloor: React.FC<BaseSceneProps> = ({
  title,
  text,
  subtitle,
  badge,
  accentColor = BRAND.neon,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const displayTitle = title || text || '⚠ NO TITLE IN SPEC';
  const safe = getSafeArea(width, height, safeArea);

  // Perspective floor grid animation
  const gridOffset = (frame * 3) % 60;

  // Motion resolved via the shared layer so specs can override curve/duration per channel
  const animateReveal = resolveMotion(motion, fps, 'reveal');
  const cardProgress = animateReveal(frame, 0, 1);

  const cardTranslateY = interpolate(cardProgress, [0, 1], [100, 0]);
  const cardOpacity = Math.min(1, Math.max(0, cardProgress));

  // Geometry derived from safe box bounds instead of a hardcoded 900px / 90%
  const cardWidth = Math.min(safe.width, 900);
  const cardPadX = Math.round(cardWidth * 0.06);
  const innerWidth = cardWidth - cardPadX * 2;

  // Title font size measured dynamically with GRID_FONT font stack
  const titleFontSize = fitOneLine({
    text: displayTitle,
    maxWidth: innerWidth,
    fontFamily: GRID_FONT,
    fontWeight: 900,
    letterSpacing: '-1px',
    textTransform: 'uppercase',
    maxFontSize: 80,
    minFontSize: 32,
  });

  // Subtitle measured with fitWrapped to fit safe bounds and line budget
  const subBlock = subtitle
    ? fitWrapped({
        text: subtitle,
        maxWidth: innerWidth,
        maxHeight: Math.max(80, safe.height * 0.2),
        fontFamily: GRID_FONT,
        fontWeight: 600,
        maxLines: 3,
        lineHeight: 1.2,
        letterSpacing: '1px',
        maxFontSize: 30,
        minFontSize: 18,
      })
    : null;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        backgroundColor: BRAND.bg,
        overflow: 'hidden',
        perspective: '800px',
        fontFamily: GRID_FONT,
      }}
    >
      {/* 3D Wireframe Perspective Grid Floor (Full Bleed Background) */}
      <div
        style={{
          position: 'absolute',
          bottom: '-30%',
          width: '200%',
          left: '-50%',
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

      {/* Safe Area Container positioning floating card clear of platform UI */}
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
        }}
      >
        {/* Floating 3D Neo-Brutalist Card */}
        <div
          style={{
            opacity: cardOpacity,
            transform: `translateY(${cardTranslateY}px) translateZ(50px)`,
            backgroundColor: BRAND.surface,
            border: `4px solid ${accentColor}`,
            borderRadius: '24px',
            padding: `${Math.round(cardPadX * 0.9)}px ${cardPadX}px`,
            textAlign: 'center',
            boxShadow: `12px 12px 0px ${accentColor}`,
            zIndex: 5,
            width: cardWidth,
            maxWidth: '100%',
            boxSizing: 'border-box',
            overflowWrap: 'break-word',
            wordBreak: 'break-word',
          }}
        >
          {badge && (
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
              {badge}
            </div>
          )}

          <h1
            style={{
              fontSize: `${titleFontSize}px`,
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

          {subtitle && subBlock && (
            <p
              style={{
                fontSize: `${subBlock.fontSize}px`,
                fontWeight: 600,
                color: BRAND.muted,
                marginTop: '20px',
                marginBottom: 0,
                letterSpacing: '1px',
                lineHeight: 1.2,
                overflowWrap: 'break-word',
                wordBreak: 'break-word',
              }}
            >
              {subtitle}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
