import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';

const DEFAULT_CARDS = [
  { title: 'Fast Rendering', description: '60 FPS Motion Graphics', tag: 'SPEED', color: BRAND.gold },
  { title: 'Zero-Shot TTS', description: 'Qwen3 Voice Cloning', tag: 'AUDIO', color: BRAND.neon },
  { title: 'Remotion React', description: 'Programmatic Video Spec', tag: 'CODE', color: '#61DAFB' },
];

export const SwipePanels: React.FC<BaseSceneProps> = ({
  title,
  text,
  cards,
  accentColor = BRAND.gold,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const displayTitle = title || text || 'KEY CAPABILITIES';
  const displayCards = cards && cards.length > 0 ? cards : DEFAULT_CARDS;

  const titleSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });

  const titleLen = displayTitle.length;
  const titleFontSize = titleLen > 40 ? '40px' : titleLen > 20 ? '50px' : '64px';

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
      }}
    >
      {/* Title */}
      <div
        style={{
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(titleSpring, [0, 1], [-40, 0])}px)`,
          marginBottom: '40px',
          textAlign: 'center',
          maxWidth: '920px',
          overflowWrap: 'break-word',
          wordBreak: 'break-word',
        }}
      >
        <h2
          style={{
            fontSize: titleFontSize,
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

      {/* Cards List with staggered spring entrance */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          width: '100%',
          maxWidth: '880px',
          boxSizing: 'border-box',
        }}
      >
        {displayCards.slice(0, 4).map((card, idx) => {
          const cardDelay = 10 + idx * 12;
          const cardSpring = spring({
            frame: frame - cardDelay,
            fps,
            config: { damping: 14, stiffness: 100 },
          });

          // Alternate left and right entrance
          const slideDirection = idx % 2 === 0 ? -150 : 150;
          const translateX = interpolate(cardSpring, [0, 1], [slideDirection, 0]);
          const opacity = interpolate(cardSpring, [0, 1], [0, 1]);
          const scale = interpolate(cardSpring, [0, 1], [0.9, 1]);

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
