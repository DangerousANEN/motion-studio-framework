import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea, safeAreaPadding } from '../lib/safeArea';
import { fitOneLine } from '../theme/layout';

export { BRAND };

/**
 * One source of truth for the hero font stack: `fitOneLine` measures with the
 * same family the container renders with, otherwise the fitted size is wrong.
 */
const HERO_FONT = '"Impact", "Arial Black", system-ui, sans-serif';

/**
 * Kinetic hero card with an optional badge and subtitle.
 *
 * Three defects fixed while moving this onto the shared layers:
 *  - `padding: '60px'` ignored the asymmetric platform strips, so the subtitle
 *    landed under the Shorts action column
 *  - `width: '90%'` (972px at 1080) exceeded the 920px safe box, and the card's
 *    tilt pushed its corners further out still
 *  - `fontSize` was picked from `title.length`, which is not a width: 30 wide
 *    uppercase glyphs overflow where 30 narrow ones fit. Now measured.
 */
export const HeroKinetic: React.FC<BaseSceneProps> = ({
  title,
  text,
  subtitle,
  badge,
  accentColor = BRAND.gold,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const displayTitle = title || text || '⚠ NO TITLE IN SPEC';
  const safe = getSafeArea(width, height, safeArea);

  // `reveal` drives the card entrance, `transform` the delayed subtitle.
  // Separate channels let a spec retime one without touching the other.
  const animateReveal = resolveMotion(motion, fps, 'reveal');
  const animateSub = resolveMotion(motion, fps, 'transform');

  const springSnap = animateReveal(frame, 0, 1);
  // The subtitle trails the card by 8 frames.
  const subSpring = animateSub(frame - 8, 0, 1);

  const scale = interpolate(springSnap, [0, 1], [0.4, 1]);
  const rotation = interpolate(springSnap, [0, 1], [-6, -2]); // Signature pop-brutalist tilt
  const shadowOffset = interpolate(springSnap, [0, 1], [0, 14]);

  const subOffsetY = interpolate(subSpring, [0, 1], [40, 0]);
  const subOpacity = interpolate(subSpring, [0, 1], [0, 1]);

  // The card is tilted, so its rotated bounding box is wider than its layout
  // box. Reserve that overhang instead of letting a corner cross the inset.
  const tiltRad = (Math.abs(rotation) * Math.PI) / 180;
  const cardWidth = Math.min(safe.width * Math.cos(tiltRad) - 24, 920);

  // Measure the title rather than guessing from character count.
  const fontSize = fitOneLine({
    text: displayTitle,
    maxWidth: cardWidth - 96, // minus horizontal card padding
    fontFamily: HERO_FONT,
    fontWeight: 900,
    letterSpacing: '-1px',
    textTransform: 'uppercase',
    maxFontSize: 88,
    minFontSize: 40,
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        // Platform-aware insets, not a symmetric 60px. The bottom strip on
        // Shorts/Reels is ~380px; a flat padding put the subtitle under the
        // action column.
        ...safeAreaPadding(width, height, safeArea),
        position: 'relative',
        overflow: 'hidden',
        fontFamily: HERO_FONT,
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
            // Pinned to the top of the SAFE box, not the raw canvas. At 120px
            // the badge sat inside the platform's 280px top strip.
            top: safe.top,
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
            maxWidth: cardWidth,
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
          width: cardWidth,
          maxWidth: '100%',
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
            maxWidth: cardWidth,
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
