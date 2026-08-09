import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { calculateStagger, resolveMotion } from '../lib/motion';
import { getSafeArea, safeAreaPadding } from '../lib/safeArea';
import { fitOneLine } from '../theme/layout';

const PANEL_FONT = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

// Shown only when the spec supplies no cards — deliberately looks broken so the
// spec bug surfaces instead of masquerading as real content.
const MISSING_CARDS = [
  { title: '⚠ NO CARDS IN SPEC', description: 'scene.cards was empty', tag: 'BUG', color: '#FF0033' },
];

/**
 * Vertical list of animated cards with alternating slide-in transitions.
 *
 * Safe area & motion fixes:
 *  - Replaced fixed padding ('60px 40px') with safeAreaPadding. On 1080x1920 vertical video,
 *    the bottom 380px action strip covers UI controls; flat padding allowed panel 3 and 4 of 4
 *    to render inside the bottom 380px safe area inset.
 *  - Changed container layout from flex: 1 to position: absolute; inset: 0 to prevent zero-height
 *    collapse inside shader-backed transition OffscreenCanvas wrappers.
 *  - Replaced character-length ladder (len > 40 ? 40px : 50px) with fitOneLine to accurately calculate
 *    font sizing for wide/Cyrillic characters.
 *  - Replaced raw spring() calls with resolveMotion(motion, fps, 'reveal') for title entrance and
 *    resolveMotion(motion, fps, 'transform') with calculateStagger() for panel slides.
 */
export const SwipePanels: React.FC<BaseSceneProps> = ({
  title,
  text,
  cards,
  accentColor = BRAND.gold,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const displayTitle = title || text || '⚠ NO TITLE IN SPEC';
  const displayCards = cards && cards.length > 0 ? cards : MISSING_CARDS;

  const safe = getSafeArea(width, height, safeArea);
  const maxTitleWidth = Math.min(safe.width, 920);
  const maxCardsWidth = Math.min(safe.width, 880);

  const animateReveal = resolveMotion(motion, fps, 'reveal');
  const animateTransform = resolveMotion(motion, fps, 'transform');

  const titleProgress = animateReveal(frame, 0, 1);
  const titleOpacity = interpolate(titleProgress, [0, 1], [0, 1]);
  const titleTranslateY = interpolate(titleProgress, [0, 1], [-40, 0]);

  const titleFontSize = fitOneLine({
    text: displayTitle,
    maxWidth: maxTitleWidth,
    fontFamily: PANEL_FONT,
    fontWeight: 900,
    letterSpacing: '2px',
    textTransform: 'uppercase',
    maxFontSize: 64,
    minFontSize: 32,
  });

  const visibleCards = displayCards.slice(0, 4);
  const cardDelays = calculateStagger(visibleCards.length, 12);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        ...safeAreaPadding(width, height, safeArea),
        overflow: 'hidden',
        fontFamily: PANEL_FONT,
      }}
    >
      {/* Title */}
      <div
        style={{
          opacity: titleOpacity,
          transform: `translateY(${titleTranslateY}px)`,
          marginBottom: '32px',
          textAlign: 'center',
          maxWidth: maxTitleWidth,
          overflowWrap: 'break-word',
          wordBreak: 'break-word',
        }}
      >
        <h2
          style={{
            fontSize: `${titleFontSize}px`,
            fontWeight: 900,
            color: BRAND.text,
            margin: 0,
            letterSpacing: '2px',
            textTransform: 'uppercase',
            overflowWrap: 'break-word',
            wordBreak: 'break-word',
          }}
        >
          {displayTitle}
        </h2>
        <div
          style={{
            width: '120px',
            height: '4px',
            backgroundColor: accentColor,
            margin: '12px auto 0 auto',
            borderRadius: '2px',
          }}
        />
      </div>

      {/* Cards List with staggered entrance */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          width: '100%',
          maxWidth: maxCardsWidth,
          boxSizing: 'border-box',
        }}
      >
        {visibleCards.map((card, idx) => {
          const cardDelay = 10 + cardDelays[idx];
          const cardProgress = animateTransform(frame - cardDelay, 0, 1);

          // Alternate left and right entrance
          const slideDirection = idx % 2 === 0 ? -150 : 150;
          const translateX = interpolate(cardProgress, [0, 1], [slideDirection, 0]);
          const opacity = interpolate(cardProgress, [0, 1], [0, 1]);
          const scale = interpolate(cardProgress, [0, 1], [0.9, 1]);

          const cardAccent = card.color || accentColor;

          return (
            <div
              key={idx}
              style={{
                opacity,
                transform: `translateX(${translateX}px) scale(${scale})`,
                backgroundColor: BRAND.surface,
                borderRadius: '16px',
                padding: '24px 32px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderLeft: `8px solid ${cardAccent}`,
                border: `2px solid #000000`,
                boxShadow: `6px 6px 0px ${BRAND.shadowColor}`,
                overflowWrap: 'break-word',
                wordBreak: 'break-word',
                gap: '16px',
              }}
            >
              <div style={{ flex: 1, minWidth: 0, overflowWrap: 'break-word', wordBreak: 'break-word' }}>
                <h3
                  style={{
                    fontSize: '32px',
                    fontWeight: 800,
                    color: BRAND.text,
                    margin: 0,
                    overflowWrap: 'break-word',
                    wordBreak: 'break-word',
                  }}
                >
                  {card.title}
                </h3>
                {card.description && (
                  <p
                    style={{
                      fontSize: '22px',
                      color: BRAND.muted,
                      margin: '8px 0 0 0',
                      overflowWrap: 'break-word',
                      wordBreak: 'break-word',
                    }}
                  >
                    {card.description}
                  </p>
                )}
              </div>

              {card.tag && (
                <span
                  style={{
                    backgroundColor: `${cardAccent}25`,
                    color: cardAccent,
                    border: `1px solid ${cardAccent}`,
                    padding: '8px 18px',
                    borderRadius: '4px',
                    fontSize: '18px',
                    fontWeight: 800,
                    letterSpacing: '1px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {card.tag}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
