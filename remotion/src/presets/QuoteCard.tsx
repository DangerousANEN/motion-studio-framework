import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { useSceneStyle } from '../theme/StyleContext';
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
  accentColor,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const vertical = height >= width;
  const safe = getSafeArea(width, height, safeArea);

  const { theme, accent } = useSceneStyle(undefined, accentColor);
  const quote = text || '⚠ NO QUOTE IN SPEC';
  const words = quote.split(' ');

  // The opening mark is decorative but must not sit on the first line of text.
  // Its clearance is derived from the glyph size rather than hardcoded, so the
  // two stay in step if the size changes.
  const quoteMarkSize = vertical ? 120 : 140;
  const quoteMarkClearance = Math.round(quoteMarkSize * 0.42);

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
        backgroundColor: theme.bg,
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
          background: `radial-gradient(circle, ${accent}18 0%, transparent 70%)`,
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
              color: accent,
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
            backgroundColor: theme.surface,
            borderLeft: `7px solid ${accent}`,
            borderRadius: '4px 18px 18px 4px',
            padding: vertical ? '46px 42px' : '40px 56px',
            maxWidth: cardMaxWidth,
            boxSizing: 'border-box',
            boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
          }}
        >
          {/*
            The mark sits in the padding band above the text, not on top of it.
            Absolute + a matching paddingTop on the paragraph is what keeps the
            glyph and the first line from occupying the same pixels: at 120px
            the glyph's ink is ~0.7em tall, so it needs that much clearance
            reserved below its own top edge.
          */}
          <div
            style={{
              position: 'absolute',
              top: vertical ? -14 : -18,
              left: vertical ? 30 : 34,
              fontSize: quoteMarkSize,
              lineHeight: 1,
              fontWeight: 900,
              color: accent,
              opacity: markProgress * 0.32,
              transform: `scale(${0.5 + markProgress * 0.5})`,
              transformOrigin: 'top left',
              userSelect: 'none',
              pointerEvents: 'none',
            }}
          >
            «
          </div>

          <p
            style={{
              fontSize: vertical ? 40 : 38,
              lineHeight: 1.4,
              fontWeight: 600,
              color: theme.text,
              margin: 0,
              // Clears the quote mark instead of letting the first line collide
              // with it.
              paddingTop: quoteMarkClearance,
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
                opacity: animateReveal(frame - attributionStart, 0, 1),
              }}
            >
              {/* The rule reads as a divider ABOVE the attribution. Inline in a
                  baseline row it looked like an em dash pointing at the name. */}
              <div
                style={{
                  width: 46,
                  height: 3,
                  backgroundColor: accent,
                  borderRadius: 2,
                  marginBottom: 14,
                }}
              />
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: 12,
                  flexWrap: 'wrap',
                }}
              >
                {author && (
                  <span style={{ fontSize: vertical ? 28 : 26, fontWeight: 800, color: theme.text }}>
                    {author}
                  </span>
                )}
                {role && (
                  <span style={{ fontSize: vertical ? 22 : 20, color: theme.muted }}>{role}</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
