import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';

/**
 * QuoteCard — a pull quote with attribution. Good for research findings,
 * paper abstracts, or a punchy takeaway between denser scenes.
 * Data: `text` (the quote), optional `author`, `role`, `title` (kicker).
 */
export const QuoteCard: React.FC<BaseSceneProps> = ({
  title,
  text,
  author,
  role,
  accentColor = BRAND.gold,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const vertical = height >= width;

  const quote = text || '⚠ NO QUOTE IN SPEC';
  const cardSpring = spring({ frame, fps, config: { damping: 16, stiffness: 85 } });
  const markSpring = spring({ frame: frame - 6, fps, config: { damping: 12, stiffness: 140 } });

  const words = quote.split(' ');

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: vertical ? '70px 56px' : '60px 120px',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* Soft accent glow behind the card */}
      <div
        style={{
          position: 'absolute',
          width: '620px',
          height: '620px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}18 0%, transparent 70%)`,
          opacity: cardSpring,
        }}
      />

      {title && (
        <div
          style={{
            fontSize: '20px',
            fontWeight: 800,
            letterSpacing: '4px',
            textTransform: 'uppercase',
            color: accentColor,
            marginBottom: '24px',
            opacity: interpolate(frame, [0, 14], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          {title}
        </div>
      )}

      <div
        style={{
          position: 'relative',
          opacity: cardSpring,
          transform: `translateY(${interpolate(cardSpring, [0, 1], [40, 0])}px)`,
          backgroundColor: BRAND.surface,
          borderLeft: `7px solid ${accentColor}`,
          borderRadius: '4px 18px 18px 4px',
          padding: vertical ? '46px 42px' : '40px 56px',
          maxWidth: vertical ? '900px' : '1180px',
          boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: vertical ? '-32px' : '-40px',
            left: '26px',
            fontSize: vertical ? '120px' : '140px',
            lineHeight: 1,
            fontWeight: 900,
            color: accentColor,
            opacity: markSpring * 0.35,
            transform: `scale(${interpolate(markSpring, [0, 1], [0.5, 1])})`,
            userSelect: 'none',
          }}
        >
          «
        </div>

        <p
          style={{
            fontSize: vertical ? '40px' : '38px',
            lineHeight: 1.4,
            fontWeight: 600,
            color: BRAND.text,
            margin: 0,
            fontStyle: 'italic',
          }}
        >
          {words.map((word, i) => {
            const start = 12 + i * 2.5;
            const wordOpacity = interpolate(frame, [start, start + 8], [0.15, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <span key={i} style={{ opacity: wordOpacity }}>
                {word}{' '}
              </span>
            );
          })}
        </p>

        {(author || role) && (
          <div
            style={{
              marginTop: '30px',
              display: 'flex',
              alignItems: 'baseline',
              gap: '14px',
              opacity: interpolate(frame, [12 + words.length * 2.5, 12 + words.length * 2.5 + 14], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
            }}
          >
            <div style={{ width: '46px', height: '3px', backgroundColor: accentColor, borderRadius: '2px' }} />
            {author && (
              <span style={{ fontSize: vertical ? '28px' : '26px', fontWeight: 800, color: BRAND.text }}>
                {author}
              </span>
            )}
            {role && (
              <span style={{ fontSize: vertical ? '22px' : '20px', color: BRAND.muted }}>{role}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
