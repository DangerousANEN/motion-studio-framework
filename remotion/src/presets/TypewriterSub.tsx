import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';

export const TypewriterSub: React.FC<BaseSceneProps> = ({
  text,
  title,
  bodyText,
  subtitle,
  durationInFrames,
  accentColor = BRAND.gold,
}) => {
  const frame = useCurrentFrame();
  const config = useVideoConfig();
  const fps = config.fps;
  const totalFrames = durationInFrames || config.durationInFrames || 90;

  const rawText = text || title || bodyText || 'Ищете лучшие оупен сорс решения в области ИИ? Канал LLM Hubs ваш главный источник.';
  const words = rawText.split(/\s+/).filter(Boolean);

  const wordCount = words.length;
  const framesPerWord = wordCount > 0 ? Math.max(1, totalFrames / wordCount) : 5;

  // Active word index based on frames
  const activeWordIdx = Math.min(
    wordCount - 1,
    Math.floor(frame / framesPerWord)
  );

  // Dynamic font sizing for long texts
  const fontSize = wordCount > 30 ? '32px' : wordCount > 18 ? '40px' : wordCount > 10 ? '48px' : '56px';

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
      {/* Glow pulse */}
      <div
        style={{
          position: 'absolute',
          width: '700px',
          height: '700px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}18 0%, transparent 70%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Subtitle Badge */}
      <div
        style={{
          backgroundColor: BRAND.surface,
          border: `2px solid ${accentColor}`,
          boxShadow: `4px 4px 0px ${BRAND.shadowColor}`,
          padding: '10px 28px',
          borderRadius: '4px',
          color: accentColor,
          fontSize: '20px',
          fontWeight: 800,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '40px',
          zIndex: 5,
        }}
      >
        {subtitle || 'SUBTITLES / VOICEOVER'}
      </div>

      {/* Word Cloud Kinetic Display */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignContent: 'center',
          gap: '14px 20px',
          maxWidth: '960px',
          maxHeight: '1400px',
          overflow: 'hidden',
          lineHeight: 1.3,
          zIndex: 5,
          boxSizing: 'border-box',
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
            ? interpolate(wordSpring, [0, 1], [0.6, 1.15])
            : isRevealed
            ? 1
            : 0.85;

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
                fontSize,
                fontWeight: isCurrent ? 900 : 700,
                color,
                opacity,
                transform: `scale(${scale})`,
                display: 'inline-block',
                overflowWrap: 'break-word',
                wordBreak: 'break-word',
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
