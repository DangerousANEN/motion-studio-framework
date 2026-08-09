import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';
import { fitOneLine, fitWrapped } from '../theme/layout';

/**
 * Big-number stat with a fill bar and a label.
 *
 * Motion is routed through the shared layer rather than a local spring, so a
 * spec can retime the count without editing this file:
 *
 *   motion: { value: { curve: 'spring', spring: { damping: 12 } },
 *             reveal: { curve: 'easeOut', duration: 20 } }
 *
 * Three defects fixed while wiring this up:
 *  - hardcoded `spring({damping:18, stiffness:80})` ignored spec intent
 *  - `padding: '60px 40px'` put the label inside the platform's bottom UI strip
 *  - `fontSize: '130px'` was fixed, so a value like 1 000 000 overflowed the
 *    card; the number is now measured and fitted
 */
export const StatCounter: React.FC<BaseSceneProps> = ({
  statValue = 100,
  statPrefix = '',
  statSuffix = '%',
  statLabel,
  title,
  text,
  badge,
  accentColor = BRAND.neon,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const label = statLabel || title || text || '';
  const safe = getSafeArea(width, height, safeArea);

  // `value` drives the count-up, `reveal` the card entrance. Separate channels
  // mean the card can settle calmly while the number snaps.
  const animateValue = resolveMotion(motion, fps, 'value');
  const animateReveal = resolveMotion(motion, fps, 'reveal');

  const countProgress = animateValue(frame, 0, 1);
  const revealProgress = animateReveal(frame, 0, 1);

  // Preserve fractional precision when the target is fractional (6.8 GB must
  // not display as "6 GB").
  const decimals = Number.isInteger(statValue)
    ? 0
    : Math.min(2, (String(statValue).split('.')[1] ?? '').length);

  // A spring overshoots past 1 by design; clamp the *displayed* number so the
  // counter never shows a value above its target, while the card scale is still
  // free to overshoot for the bounce.
  const countClamped = Math.min(1, Math.max(0, countProgress));
  const rawValue = countClamped * statValue;
  const currentValue =
    decimals === 0 ? Math.round(rawValue) : Number(rawValue.toFixed(decimals));

  const scale = interpolate(revealProgress, [0, 1], [0.8, 1]);
  const opacity = Math.min(1, Math.max(0, revealProgress));

  // Card geometry derived from the safe box instead of a magic 900px.
  const cardWidth = Math.min(safe.width, 900);
  const cardPadX = Math.round(cardWidth * 0.07);
  const innerWidth = cardWidth - cardPadX * 2;

  // Measure the widest string the counter will ever show (the final value), so
  // the type size does not jump mid-count and does not overflow at the end.
  const finalDisplay =
    decimals === 0 ? String(Math.round(statValue)) : statValue.toFixed(decimals);
  const numberFont = 'system-ui, -apple-system, sans-serif';

  // Prefix/suffix render at ~60% of the number size; budget their width too.
  const affixRatio = 0.6;
  const affixChars = (statPrefix?.length ?? 0) + (statSuffix?.length ?? 0);
  const widthBudget = innerWidth / (1 + affixChars * affixRatio * 0.55);

  const numberSize = fitOneLine({
    text: finalDisplay,
    maxWidth: widthBudget,
    fontFamily: numberFont,
    fontWeight: 900,
    letterSpacing: '-4px',
    maxFontSize: 130,
    minFontSize: 48,
  });

  const labelBlock = label
    ? fitWrapped({
        text: label,
        maxWidth: innerWidth,
        maxHeight: Math.max(80, safe.height * 0.16),
        fontFamily: numberFont,
        fontWeight: 700,
        maxLines: 3,
        lineHeight: 1.25,
        letterSpacing: '2px',
        textTransform: 'uppercase',
        maxFontSize: 28,
        minFontSize: 16,
      })
    : { fontSize: 28, lines: [] as string[] };

  // Fill bar tracks the same progress as the number, expressed as a fraction so
  // it is independent of the bar's pixel width.
  const barWidth = Math.min(innerWidth, 280);
  const fillFraction = countClamped;

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: BRAND.bg,
        position: 'relative',
        overflow: 'hidden',
        fontFamily: numberFont,
      }}
    >
      {/* Background glow is decorative and intentionally full-bleed — it sits
          outside the safe area on purpose. */}
      <div
        style={{
          position: 'absolute',
          left: safe.centerX - 250,
          top: safe.centerY - 250,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}20 0%, transparent 70%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Content is confined to the safe box so the label never lands under the
          platform's caption/action column. */}
      <div
        style={{
          position: 'absolute',
          top: safe.top,
          left: safe.left,
          width: safe.width,
          height: safe.height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            opacity,
            transform: `scale(${scale})`,
            backgroundColor: BRAND.surface,
            border: `2px solid ${accentColor}40`,
            borderRadius: '32px',
            padding: `${Math.round(cardPadX * 0.95)}px ${cardPadX}px`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            boxShadow: `0 20px 50px rgba(0,0,0,0.5), 0 0 30px ${accentColor}20`,
            position: 'relative',
            width: cardWidth,
            boxSizing: 'border-box',
            overflowWrap: 'break-word',
            wordBreak: 'break-word',
          }}
        >
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

          <div
            style={{
              fontSize: `${numberSize}px`,
              fontWeight: 900,
              color: BRAND.text,
              letterSpacing: '-4px',
              lineHeight: 1,
              display: 'flex',
              alignItems: 'baseline',
              justifyContent: 'center',
              textShadow: `0 0 40px ${accentColor}60`,
              maxWidth: '100%',
            }}
          >
            {statPrefix && (
              <span
                style={{
                  fontSize: `${Math.round(numberSize * affixRatio)}px`,
                  color: accentColor,
                  marginRight: '8px',
                }}
              >
                {statPrefix}
              </span>
            )}
            <span>{currentValue}</span>
            {statSuffix && (
              <span
                style={{
                  fontSize: `${Math.round(numberSize * affixRatio)}px`,
                  color: accentColor,
                  marginLeft: '8px',
                }}
              >
                {statSuffix}
              </span>
            )}
          </div>

          <div
            style={{
              width: barWidth,
              height: '8px',
              backgroundColor: '#2A2D34',
              borderRadius: '4px',
              marginTop: '30px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${fillFraction * 100}%`,
                height: '100%',
                backgroundColor: accentColor,
                borderRadius: '4px',
                boxShadow: `0 0 12px ${accentColor}`,
              }}
            />
          </div>

          {label && (
            <div
              style={{
                marginTop: '25px',
                fontSize: `${labelBlock.fontSize}px`,
                fontWeight: 700,
                color: BRAND.muted,
                letterSpacing: '2px',
                textTransform: 'uppercase',
                textAlign: 'center',
                lineHeight: 1.25,
                maxWidth: '100%',
                overflowWrap: 'break-word',
                wordBreak: 'break-word',
              }}
            >
              {label}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
