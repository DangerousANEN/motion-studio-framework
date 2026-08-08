import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';

/**
 * CompareSplit — old vs new / before vs after.
 * Two panels slide in from opposite sides; a VS badge pops between them.
 * Data: `title` (header), `cards` = [{title, description, color, tag}].
 */
export const CompareSplit: React.FC<BaseSceneProps> = ({
  title,
  text,
  cards,
  accentColor = BRAND.cyan,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const header = title || text || '⚠ NO TITLE IN SPEC';
  const left = cards && cards[0];
  const right = cards && cards[1];

  const headerSpring = spring({ frame, fps, config: { damping: 14, stiffness: 100 } });
  const leftSpring = spring({ frame: frame - 10, fps, config: { damping: 16, stiffness: 90 } });
  const rightSpring = spring({ frame: frame - 16, fps, config: { damping: 16, stiffness: 90 } });

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
        position: 'relative',
        overflow: 'hidden',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        gap: '36px',
      }}
    >
      <div
        style={{
          opacity: headerSpring,
          transform: `translateY(${interpolate(headerSpring, [0, 1], [-30, 0])}px)`,
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: '54px', fontWeight: 900, color: BRAND.text, margin: 0, letterSpacing: '2px', textTransform: 'uppercase' }}>
          {header}
        </h2>
        <div style={{ width: '140px', height: '5px', backgroundColor: accentColor, margin: '14px auto 0', borderRadius: '3px' }} />
      </div>

      <div style={{ display: 'flex', alignItems: 'stretch', gap: '28px', width: '100%', maxWidth: '960px' }}>
        {left && (
          <div
            style={{
              flex: 1,
              opacity: leftSpring,
              transform: `translateX(${interpolate(leftSpring, [0, 1], [-120, 0])}px)`,
              backgroundColor: BRAND.surface,
              borderRadius: '18px',
              padding: '28px 24px',
              border: `2px solid ${(left.color || '#FF4D5E')}`,
              boxShadow: `8px 8px 0 rgba(0,0,0,0.45)`,
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            {left.tag && (
              <span style={{ alignSelf: 'flex-start', fontSize: '16px', fontWeight: 800, letterSpacing: '2px', color: left.color || '#FF4D5E', border: `1px solid ${left.color || '#FF4D5E'}`, borderRadius: '4px', padding: '4px 12px' }}>
                {left.tag}
              </span>
            )}
            <h3 style={{ fontSize: '34px', fontWeight: 900, color: BRAND.text, margin: 0 }}>{left.title}</h3>
            {left.description && <p style={{ fontSize: '20px', color: BRAND.muted, margin: 0, lineHeight: 1.35 }}>{left.description}</p>}
          </div>
        )}

        <div
          style={{
            alignSelf: 'center',
            opacity: interpolate(frame, [24, 34], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
            transform: `scale(${interpolate(frame, [24, 34], [0.4, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })})`,
            backgroundColor: accentColor,
            color: BRAND.bg,
            fontSize: '26px',
            fontWeight: 900,
            padding: '12px 18px',
            borderRadius: '50%',
            boxShadow: `0 0 24px ${accentColor}80`,
            whiteSpace: 'nowrap',
          }}
        >
          VS
        </div>

        {right && (
          <div
            style={{
              flex: 1,
              opacity: rightSpring,
              transform: `translateX(${interpolate(rightSpring, [0, 1], [120, 0])}px)`,
              backgroundColor: BRAND.surface,
              borderRadius: '18px',
              padding: '28px 24px',
              border: `2px solid ${(right.color || accentColor)}`,
              boxShadow: `8px 8px 0 rgba(0,0,0,0.45)`,
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            {right.tag && (
              <span style={{ alignSelf: 'flex-start', fontSize: '16px', fontWeight: 800, letterSpacing: '2px', color: right.color || accentColor, border: `1px solid ${right.color || accentColor}`, borderRadius: '4px', padding: '4px 12px' }}>
                {right.tag}
              </span>
            )}
            <h3 style={{ fontSize: '34px', fontWeight: 900, color: BRAND.text, margin: 0 }}>{right.title}</h3>
            {right.description && <p style={{ fontSize: '20px', color: BRAND.muted, margin: 0, lineHeight: 1.35 }}>{right.description}</p>}
          </div>
        )}
      </div>
    </div>
  );
};
