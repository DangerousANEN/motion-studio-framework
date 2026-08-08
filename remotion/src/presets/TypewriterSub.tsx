import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './HeroKinetic';

export const TypewriterSub: React.FC<BaseSceneProps> = ({
  text = 'Ищете лучшие оупен сорс решения в области ИИ? Канал LLM Hubs ваш главный источник.',
  accentColor = BRAND.gold,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(' ').filter(Boolean);
  const framesPerWord = 5;

  // Active word index based on frames
  const activeWordIdx = Math.min(
    words.length - 1,
    Math.floor(frame / framesPerWord)
  );

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '80px',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Glow pulse */}
      <div
        style={{
          position: 'absolute',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}18 0%, transparent 70%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Subtitle Badge */}
      <div
        style={{
          backgroundColor: BRAND.surface,
          border: `1px solid ${accentColor}40`,
          padding: '8px 24px',
          borderRadius: '30px',
          color: accentColor,
          fontSize: '18px',
          fontWeight: 800,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '40px',
        }}
      >
        SUBTITLES / VOICEOVER
      </div>

      {/* Word Cloud Kinetic Display */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignContent: 'center',
          gap: '16px 24px',
          maxWidth: '920px',
          lineHeight: 1.3,
        }}
      >
        {words.map((word, idx) => {
          const isRevealed = idx <= activeWordIdx;
          const isCurrent = idx === activeWordIdx;

          // Word pop spring animation
          const wordSpring = spring({
            frame: frame - idx * framesPerWord,
            fps,
            config: { damping: 12, stiffness: 120 },
          });

          const scale = isCurrent
            ? interpolate(wordSpring, [0, 1], [0.5, 1.25])
            : isRevealed
            ? 1
            : 0.8;

          const opacity = isRevealed ? 1 : 0.15;
          const color = isCurrent
            ? accentColor
            : isRevealed
            ? BRAND.text
            : BRAND.muted;

          return (
            <span
              key={idx}
              style={{
                fontSize: '52px',
                fontWeight: isCurrent ? 900 : 700,
                color,
                opacity,
                transform: `scale(${scale})`,
                display: 'inline-block',
                transition: 'color 0.1s ease',
                textShadow: isCurrent ? `0 0 20px ${accentColor}80` : 'none',
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
