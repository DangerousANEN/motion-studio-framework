import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';

/**
 * QuoteCard — a pull quote with attribution. Good for research findings,
 * paper abstracts, or a punchy takeaway between denser scenes.
 * Data: `text` (the quote), optional `author`, `role`, `title` (kicker).
 *
 * Sizing comes from the safe-area layer instead of a hardcoded padding pair.
 * The old `padding: 70px 56px` + `maxWidth: 900px` let the card reach 900px of
 * a 920px safe width with its 7px accent border and 20px shadow spilling past
 * that, and put the kicker inside the platform's top overlay zone.
 */

const FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif';

export const QuoteCard: React.FC<BaseSceneProps> = ({
  title,
  text,
  author,
  role,
  accentColor = BRAND.gold,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const vertical = height >= width;
  const safe = getSafeArea(width, height, safeArea);

  const quote = text || '⚠ NO QUOTE IN SPEC';
  const words = quote.split(' ');

  // The card entrance keeps its spring feel by default but is now overridable
  // per scene; the quote mark and word reveal ride their own channels.
  const animateCard = resolveMotion(
    motion ?? { curve: 'spring', spring: { damping: 16, stiffness: 85 } },
    fps,
    'transform'
  );
  const animateMark = resolveMotion(
    motion ?? { curve: 'spring', spring: { damping: 12, stiffness: 140 } },
    fps,
    'transform'
  );
  const animateReveal = resolveMotion(motion, fps, 'reveal');

  const cardProgress = animateCard(frame, 0, 1);
  const markProgress = animateMark(frame - 6, 0, 1);

  // Card must fit inside the safe box *including* its border and shadow, so the
  // shadow spread is subtracted rather than assumed to be free space.
  const SHADOW_SPREAD = 24;
  const cardMaxWidth = Math.min(vertical ? 900 : 1180, safe.width - SHADOW_SPREAD * 2);

  const attributionStart = 12 + words.length * 2.5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        backgroundColor: BRAND.bg,
        overflow: 'hidden',
        fontFamily: FONT,
      }}
    >
      {/* Soft accent glow, centred on the safe box rather than the raw frame. */}
      <div
        style={{
          position: 'absolute',
          left: safe.left + safe.width / 2 - 310,
          top: safe.top + safe.height / 2 - 310,
          width: 620,
          height: 620,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}18 0%, transparent 70%)`,
          opacity: cardProgress,
        }}
      />

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
        {title && (
          <div
            style={{
              fontSize: 20,
              fontWeight: 800,
              letterSpacing: '4px',
              textTransform: 'uppercase',
              color: accentColor,
              marginBottom: 24,
              textAlign: 'center',
              opacity: animateReveal(frame, 0, 1),
            }}
          >
            {title}
          </div>
        )}

        <div
          style={{
            position: 'relative',
            opacity: cardProgress,
            transform: `translateY(${(1 - cardProgress) * 40}px)`,
            backgroundColor: BRAND.surface,
            borderLeft: `7px solid ${accentColor}`,
            borderRadius: '4px 18px 18px 4px',
            padding: vertical ? '46px 42px' : '40px 56px',
            maxWidth: cardMaxWidth,
            boxSizing: 'border-box',
            boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: vertical ? -32 : -40,
              left: 26,
              fontSize: vertical ? 120 : 140,
              lineHeight: 1,
              fontWeight: 900,
              color: accentColor,
              opacity: markProgress * 0.35,
              transform: `scale(${0.5 + markProgress * 0.5})`,
              userSelect: 'none',
            }}
          >
            «
          </div>

          <p
            style={{
              fontSize: vertical ? 40 : 38,
              lineHeight: 1.4,
              fontWeight: 600,
              color: BRAND.text,
              margin: 0,
              fontStyle: 'italic',
            }}
          >
            {words.map((word, i) => {
              const start = 12 + i * 2.5;
              // Words fade from 0.15 rather than 0 so the block's shape is
              // readable from the first frame instead of popping in.
              const wordOpacity = 0.15 + 0.85 * animateReveal(frame - start, 0, 1);
              return (
                <span key={i} style={{ opacity: Math.min(1, wordOpacity) }}>
                  {word}{' '}
                </span>
              );
            })}
          </p>

          {(author || role) && (
            <div
              style={{
                marginTop: 30,
                display: 'flex',
                alignItems: 'baseline',
                gap: 14,
                flexWrap: 'wrap',
                opacity: animateReveal(frame - attributionStart, 0, 1),
              }}
            >
              <div style={{ width: 46, height: 3, backgroundColor: accentColor, borderRadius: 2 }} />
              {author && (
                <span style={{ fontSize: vertical ? 28 : 26, fontWeight: 800, color: BRAND.text }}>
                  {author}
                </span>
              )}
              {role && (
                <span style={{ fontSize: vertical ? 22 : 20, color: BRAND.muted }}>{role}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
