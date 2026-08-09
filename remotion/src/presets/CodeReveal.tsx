import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';
import { fitOneLine } from '../theme/layout';

const CODE_FONT = 'Consolas, "Courier New", monospace';

/**
 * CodeReveal — terminal window that types code line by line.
 * Data: `code` (newline separated), optional `title`, `language`.
 */
export const CodeReveal: React.FC<BaseSceneProps> = ({
  title,
  code,
  language,
  accentColor = BRAND.neon,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const vertical = height >= width;

  const source = code || '⚠ NO CODE IN SPEC';
  const lines = source.split('\n');

  const animateReveal = resolveMotion(motion, fps, 'reveal');
  const windowProgress = animateReveal(frame, 0, 1);
  const perLine = 9;

  const safe = getSafeArea(width, height, safeArea);

  // Window geometry, derived from the safe box rather than a magic constant.
  const windowWidth = Math.min(safe.width, vertical ? 940 : 1280);
  const codePadX = 26;
  const gutterWidth = 34;
  const gutterGap = 16;
  // Width actually available to the code text itself.
  const textWidth = windowWidth - codePadX * 2 - gutterWidth - gutterGap;

  // The longest line decides the type size for the whole block: sizing each
  // line independently would make the font jump between rows. A fixed 26px was
  // overflowing the window on lines like `"voice": "syenduk"`, and the flex row
  // then clipped it because a text span defaults to min-width:auto.
  const longest = lines.reduce((a, b) => (b.length > a.length ? b : a), '');
  const fontSize = fitOneLine({
    text: longest,
    maxWidth: textWidth,
    fontFamily: CODE_FONT,
    fontWeight: 400,
    maxFontSize: vertical ? 26 : 22,
    minFontSize: 13,
  });

  // Very small syntax highlighting: enough to read as code, no parser needed.
  const colorFor = (line: string): string => {
    const t = line.trim();
    if (t.startsWith('#') || t.startsWith('//')) return BRAND.muted;
    if (/^(def|class|import|from|return|async|await|function|const|let|var)\b/.test(t)) return accentColor;
    if (/^[A-Za-zА-Яа-я_][\w]*\s*=/.test(t)) return BRAND.cyan;
    return BRAND.text;
  };

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
        gap: '26px',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        overflow: 'hidden',
      }}
    >
      {title && (
        <h2
          style={{
            fontSize: vertical ? '46px' : '38px',
            fontWeight: 900,
            color: BRAND.text,
            margin: 0,
            textTransform: 'uppercase',
            letterSpacing: '2px',
            textAlign: 'center',
            opacity: interpolate(frame, [0, 12], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          {title}
        </h2>
      )}

      <div
        style={{
          opacity: windowProgress,
          transform: `scale(${interpolate(windowProgress, [0, 1], [0.92, 1])})`,
          width: `${windowWidth}px`,
          maxWidth: '100%',
          backgroundColor: '#0A0B0D',
          border: `2px solid ${accentColor}55`,
          borderRadius: '14px',
          overflow: 'hidden',
          boxShadow: `0 24px 60px rgba(0,0,0,0.6), 0 0 30px ${accentColor}22`,
        }}
      >
        {/* Title bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '9px',
            padding: '14px 18px',
            backgroundColor: '#15171B',
            borderBottom: '1px solid #23262C',
          }}
        >
          <span style={{ width: 13, height: 13, borderRadius: '50%', backgroundColor: '#FF5F57' }} />
          <span style={{ width: 13, height: 13, borderRadius: '50%', backgroundColor: '#FEBC2E' }} />
          <span style={{ width: 13, height: 13, borderRadius: '50%', backgroundColor: '#28C840' }} />
          {language && (
            <span style={{ marginLeft: 'auto', fontSize: '16px', color: BRAND.muted, letterSpacing: '1px' }}>
              {language}
            </span>
          )}
        </div>

        <div style={{ padding: `22px ${codePadX}px`, fontFamily: CODE_FONT }}>
          {lines.map((line, i) => {
            const start = 10 + i * perLine;
            const reveal = interpolate(frame, [start, start + perLine], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const shown = Math.round(line.length * reveal);
            const isTyping = reveal > 0 && reveal < 1;

            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  gap: `${gutterGap}px`,
                  fontSize: `${fontSize}px`,
                  lineHeight: 1.55,
                  opacity: reveal > 0 ? 1 : 0.12,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                <span style={{ color: '#3A3F47', minWidth: `${gutterWidth}px`, flexShrink: 0, textAlign: 'right', userSelect: 'none' }}>
                  {i + 1}
                </span>
                {/* minWidth:0 is required: a flex child defaults to min-width:auto,
                    so a long line refuses to shrink and gets clipped by the
                    window's overflow:hidden instead of wrapping. */}
                <span style={{ color: colorFor(line), minWidth: 0, flex: 1 }}>
                  {line.slice(0, shown)}
                  {isTyping && (
                    <span style={{ color: accentColor, opacity: Math.floor(frame / 8) % 2 ? 1 : 0.15 }}>▌</span>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
