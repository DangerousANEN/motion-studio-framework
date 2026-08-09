import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea, safeAreaPadding } from '../lib/safeArea';
import { fitWrapped } from '../theme/layout';

/**
 * Shared font family for measuring and rendering to ensure font size accuracy.
 */
const TYPEWRITER_FONT = 'system-ui, -apple-system, sans-serif';

/**
 * TypewriterSub preset: frame-driven word-by-word kinetic text reveal.
 *
 * Refactored onto shared safe area + motion layers:
 *  - Fixed padding replaced with `safeAreaPadding` to protect top search/status bars
 *    and bottom Shorts/Reels caption & action overlay columns.
 *  - Raw spring animations replaced with `resolveMotion(motion, fps, 'reveal')`.
 *  - Arbitrary character-count font ladder replaced with `fitWrapped` measuring
 *    the FULL final text string once, keeping font size constant during reveal.
 */
export const TypewriterSub: React.FC<BaseSceneProps> = ({
  text,
  title,
  bodyText,
  subtitle,
  badge,
  durationInFrames,
  accentColor = BRAND.gold,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const config = useVideoConfig();
  const { fps, width, height } = config;
  const totalFrames = durationInFrames || config.durationInFrames || 90;

  // Safe area box calculations for platform UI avoidance
  const safe = getSafeArea(width, height, safeArea);
  const containerWidth = Math.min(safe.width, 960);

  // Motion resolver for reveal channel
  const animateReveal = resolveMotion(motion, fps, 'reveal');

  // No silent demo fallback: missing text in spec is a bug that should be visible.
  const rawText = text || title || bodyText || subtitle || '⚠ NO TEXT IN SPEC';
  const words = rawText.split(/\s+/).filter(Boolean);
  const wordCount = words.length;

  const framesPerWord = wordCount > 0 ? Math.max(1, totalFrames / wordCount) : 5;

  // Active word index based on current frame
  const activeWordIdx = Math.min(
    wordCount - 1,
    Math.floor(frame / framesPerWord)
  );

  // Measure the FULL text once (not the currently revealed words), so that font size
  // remains strictly stable as words appear frame by frame (same principle as StatCounter).
  const fitted = fitWrapped({
    text: rawText,
    maxWidth: containerWidth,
    maxHeight: Math.min(safe.height * 0.7, 1200),
    fontFamily: TYPEWRITER_FONT,
    fontWeight: 700,
    lineHeight: 1.3,
    maxFontSize: 56,
    minFontSize: 24,
  });
  const fontSize = `${fitted.fontSize}px`;

  const badgeText = badge || (title || text || bodyText ? subtitle : undefined);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        ...safeAreaPadding(width, height, safeArea),
        overflow: 'hidden',
        fontFamily: TYPEWRITER_FONT,
        boxSizing: 'border-box',
      }}
    >
      {/* Background glow, pinned to safe area center */}
      <div
        style={{
          position: 'absolute',
          left: safe.centerX - 350,
          top: safe.centerY - 350,
          width: 700,
          height: 700,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}18 0%, transparent 70%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Optional badge */}
      {badgeText && (
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
          {badgeText}
        </div>
      )}

      {/* Word Cloud Kinetic Display */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignContent: 'center',
          gap: '14px 20px',
          maxWidth: `${containerWidth}px`,
          maxHeight: `${Math.round(safe.height * 0.85)}px`,
          overflow: 'hidden',
          lineHeight: 1.3,
          zIndex: 5,
          boxSizing: 'border-box',
        }}
      >
        {words.map((word, idx) => {
          const wordProgress = animateReveal(frame - idx * framesPerWord, 0, 1);
          const isRevealed = idx <= activeWordIdx;
          const isCurrent = idx === activeWordIdx;

          const scale = isCurrent
            ? interpolate(wordProgress, [0, 1], [0.6, 1.15])
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
