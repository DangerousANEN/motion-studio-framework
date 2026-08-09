import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';
import { fitOneLine, fitWrapped } from '../theme/layout';

/**
 * Single font stack constant for CompareSplit.
 * Passed to fitOneLine/fitWrapped and rendered elements so measurement matches rendering face.
 */
const COMPARE_FONT = 'system-ui, -apple-system, sans-serif';

/**
 * CompareSplit — Old vs New / Before vs After side-by-side card comparison.
 *
 * Safe area and motion refactor notes:
 *  - Replaced hardcoded `padding: '60px 40px'` with safe area box positioning (`safe.top`, `safe.height`).
 *    At 1080x1920, flat 60px padding put header inside the top 280px platform bar and cards into bottom 380px platform UI.
 *  - Derived two-column card widths directly from `safe.width` (920px) minus VS badge & gap reserves (104px total),
 *    yielding 408px per card. At 1080 width, fixed 960px container crossed the 80px side insets.
 *  - Measured header and card titles via `fitOneLine` and descriptions via `fitWrapped` to eliminate text overflow.
 *  - Replaced hardcoded raw springs with `resolveMotion(motion, fps, 'reveal')` for header and `'transform'` for cards/badge.
 */
export const CompareSplit: React.FC<BaseSceneProps> = ({
  title,
  text,
  cards,
  accentColor = BRAND.cyan,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const header = title || text || '⚠ NO TITLE IN SPEC';
  const left = cards && cards[0];
  const right = cards && cards[1];

  const safe = getSafeArea(width, height, safeArea);

  // 'reveal' channel drives header entrance; 'transform' handles card & badge motion.
  const animateReveal = resolveMotion(motion, fps, 'reveal');
  const animateTransform = resolveMotion(motion, fps, 'transform');

  const headerProgress = animateReveal(frame, 0, 1);
  const leftProgress = animateTransform(frame - 10, 0, 1);
  const rightProgress = animateTransform(frame - 16, 0, 1);
  const vsProgress = animateTransform(frame - 24, 0, 1);

  const headerOffsetY = interpolate(headerProgress, [0, 1], [-30, 0]);
  const leftOffsetX = interpolate(leftProgress, [0, 1], [-120, 0]);
  const rightOffsetX = interpolate(rightProgress, [0, 1], [120, 0]);
  const vsScale = interpolate(vsProgress, [0, 1], [0.4, 1]);
  const vsOpacity = Math.min(1, Math.max(0, vsProgress));

  // Layout calculations: derive card width from safe box.
  // safe.width is 920px at 1080 canvas width (1080 - 80 - 80).
  // VS badge takes ~64px width + 40px total gap space (20px each side).
  const vsWidth = 64;
  const gap = 20;
  const totalGapAndVS = vsWidth + gap * 2;
  const cardWidth = Math.floor((safe.width - totalGapAndVS) / 2);
  const cardPaddingX = 24;
  const cardInnerWidth = Math.max(100, cardWidth - cardPaddingX * 2);

  const headerFontSize = fitOneLine({
    text: header,
    maxWidth: safe.width,
    fontFamily: COMPARE_FONT,
    fontWeight: 900,
    letterSpacing: '2px',
    textTransform: 'uppercase',
    maxFontSize: 54,
    minFontSize: 28,
  });

  const leftTitleSize = left?.title
    ? fitOneLine({
        text: left.title,
        maxWidth: cardInnerWidth,
        fontFamily: COMPARE_FONT,
        fontWeight: 900,
        maxFontSize: 34,
        minFontSize: 20,
      })
    : 34;

  const rightTitleSize = right?.title
    ? fitOneLine({
        text: right.title,
        maxWidth: cardInnerWidth,
        fontFamily: COMPARE_FONT,
        fontWeight: 900,
        maxFontSize: 34,
        minFontSize: 20,
      })
    : 34;

  const leftDescBlock = left?.description
    ? fitWrapped({
        text: left.description,
        maxWidth: cardInnerWidth,
        maxHeight: 180,
        fontFamily: COMPARE_FONT,
        fontWeight: 400,
        maxLines: 4,
        lineHeight: 1.35,
        maxFontSize: 20,
        minFontSize: 14,
      })
    : null;

  const rightDescBlock = right?.description
    ? fitWrapped({
        text: right.description,
        maxWidth: cardInnerWidth,
        maxHeight: 180,
        fontFamily: COMPARE_FONT,
        fontWeight: 400,
        maxLines: 4,
        lineHeight: 1.35,
        maxFontSize: 20,
        minFontSize: 14,
      })
    : null;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: BRAND.bg,
        overflow: 'hidden',
        fontFamily: COMPARE_FONT,
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
          gap: '36px',
          boxSizing: 'border-box',
        }}
      >
        <div
          style={{
            opacity: headerProgress,
            transform: `translateY(${headerOffsetY}px)`,
            textAlign: 'center',
            maxWidth: safe.width,
          }}
        >
          <h2
            style={{
              fontSize: `${headerFontSize}px`,
              fontWeight: 900,
              color: BRAND.text,
              margin: 0,
              letterSpacing: '2px',
              textTransform: 'uppercase',
              lineHeight: 1.1,
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
            }}
          >
            {header}
          </h2>
          <div
            style={{
              width: '140px',
              height: '5px',
              backgroundColor: accentColor,
              margin: '14px auto 0',
              borderRadius: '3px',
            }}
          />
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'stretch',
            justifyContent: 'center',
            gap: `${gap}px`,
            width: safe.width,
            boxSizing: 'border-box',
          }}
        >
          {left && (
            <div
              style={{
                width: `${cardWidth}px`,
                boxSizing: 'border-box',
                opacity: leftProgress,
                transform: `translateX(${leftOffsetX}px)`,
                backgroundColor: BRAND.surface,
                borderRadius: '18px',
                padding: `28px ${cardPaddingX}px`,
                border: `2px solid ${left.color || '#FF4D5E'}`,
                boxShadow: '8px 8px 0 rgba(0,0,0,0.45)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                overflowWrap: 'break-word',
                wordBreak: 'break-word',
              }}
            >
              {left.tag && (
                <span
                  style={{
                    alignSelf: 'flex-start',
                    fontSize: '16px',
                    fontWeight: 800,
                    letterSpacing: '2px',
                    color: left.color || '#FF4D5E',
                    border: `1px solid ${left.color || '#FF4D5E'}`,
                    borderRadius: '4px',
                    padding: '4px 12px',
                  }}
                >
                  {left.tag}
                </span>
              )}
              <h3
                style={{
                  fontSize: `${leftTitleSize}px`,
                  fontWeight: 900,
                  color: BRAND.text,
                  margin: 0,
                  lineHeight: 1.15,
                }}
              >
                {left.title}
              </h3>
              {leftDescBlock && (
                <p
                  style={{
                    fontSize: `${leftDescBlock.fontSize}px`,
                    color: BRAND.muted,
                    margin: 0,
                    lineHeight: 1.35,
                  }}
                >
                  {left.description}
                </p>
              )}
            </div>
          )}

          <div
            style={{
              alignSelf: 'center',
              width: `${vsWidth}px`,
              textAlign: 'center',
              boxSizing: 'border-box',
              opacity: vsOpacity,
              transform: `scale(${vsScale})`,
              backgroundColor: accentColor,
              color: BRAND.bg,
              fontSize: '26px',
              fontWeight: 900,
              padding: '12px 0',
              borderRadius: '50%',
              boxShadow: `0 0 24px ${accentColor}80`,
              whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
          >
            VS
          </div>

          {right && (
            <div
              style={{
                width: `${cardWidth}px`,
                boxSizing: 'border-box',
                opacity: rightProgress,
                transform: `translateX(${rightOffsetX}px)`,
                backgroundColor: BRAND.surface,
                borderRadius: '18px',
                padding: `28px ${cardPaddingX}px`,
                border: `2px solid ${right.color || accentColor}`,
                boxShadow: '8px 8px 0 rgba(0,0,0,0.45)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                overflowWrap: 'break-word',
                wordBreak: 'break-word',
              }}
            >
              {right.tag && (
                <span
                  style={{
                    alignSelf: 'flex-start',
                    fontSize: '16px',
                    fontWeight: 800,
                    letterSpacing: '2px',
                    color: right.color || accentColor,
                    border: `1px solid ${right.color || accentColor}`,
                    borderRadius: '4px',
                    padding: '4px 12px',
                  }}
                >
                  {right.tag}
                </span>
              )}
              <h3
                style={{
                  fontSize: `${rightTitleSize}px`,
                  fontWeight: 900,
                  color: BRAND.text,
                  margin: 0,
                  lineHeight: 1.15,
                }}
              >
                {right.title}
              </h3>
              {rightDescBlock && (
                <p
                  style={{
                    fontSize: `${rightDescBlock.fontSize}px`,
                    color: BRAND.muted,
                    margin: 0,
                    lineHeight: 1.35,
                  }}
                >
                  {right.description}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
