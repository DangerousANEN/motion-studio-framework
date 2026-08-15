import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { useSceneStyle } from '../theme/StyleContext';
import { resolveMotion } from '../lib/motion';
import { getSafeArea, safeAreaPadding } from '../lib/safeArea';
import { fitOneLine, fitWrapped } from '../theme/layout';

/**
 * HeroKinetic — premium editorial hook with a short controlled entrance and a
 * long static reading dwell. It deliberately avoids an all-accent rectangular
 * card: style families provide the colour while the structure remains useful
 * for high-retention openings, product announcements and myth-busting claims.
 */
const HERO_FONT = '"Arial Black", "Inter", system-ui, sans-serif';

export const HeroKinetic: React.FC<BaseSceneProps> = ({
  title,
  text,
  subtitle,
  badge,
  accentColor,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const { theme, accent, surface } = useSceneStyle(undefined, accentColor);
  const safe = getSafeArea(width, height, safeArea);
  const displayTitle = title || text || 'NO TITLE';
  const reveal = resolveMotion(motion ?? 'normal', fps, 'reveal');
  const panelIn = reveal(frame, 0, 1);
  const copyIn = reveal(frame - 8, 0, 1);
  // Use the ACTUAL inner width of the glass card. The old 0.86×safe estimate
  // ignored horizontal card padding; a no-break Cyrillic word could therefore
  // be measured as fitting but still clip in the rendered H1.
  const panelWidth = Math.min(safe.width * 0.9, 820);
  const panelPadX = Math.round(width * 0.05);
  const titleMaxWidth = panelWidth - panelPadX * 2;
  const longestWord = displayTitle.split(/\s+/).reduce((longest, word) => word.length > longest.length ? word : longest, '');
  const titleFit = fitWrapped({
    text: displayTitle,
    maxWidth: titleMaxWidth,
    maxHeight: height * 0.23,
    fontFamily: HERO_FONT,
    fontWeight: 900,
    maxLines: 2,
    lineHeight: 0.96,
    letterSpacing: '-2px',
    textTransform: 'uppercase',
    maxFontSize: Math.round(height * 0.094),
    minFontSize: Math.round(height * 0.048),
  });
  // fitTextOnNLines optimises wrapped lines. This second measurement protects
  // the longest unbreakable token after CSS word breaking is disabled.
  const longestWordSize = fitOneLine({
    text: longestWord,
    maxWidth: titleMaxWidth,
    fontFamily: HERO_FONT,
    fontWeight: 900,
    letterSpacing: '-2px',
    textTransform: 'uppercase',
    maxFontSize: Math.round(height * 0.094),
    minFontSize: Math.round(height * 0.026),
  });
  const titleFontSize = Math.min(titleFit.fontSize, longestWordSize);
  const subFit = subtitle
    ? fitWrapped({
      text: subtitle,
      maxWidth: titleMaxWidth,
      maxHeight: height * 0.13,
      fontFamily: '"Inter", system-ui, sans-serif',
      fontWeight: 700,
      maxLines: 3,
      lineHeight: 1.14,
      maxFontSize: Math.round(height * 0.035),
      minFontSize: Math.round(height * 0.024),
    })
    : null;

  const translateY = interpolate(panelIn, [0, 1], [34, 0]);
  const titleY = interpolate(copyIn, [0, 1], [22, 0]);
  const scanX = interpolate(frame, [0, Math.max(36, Math.round(fps * 1.3))], [-safe.width * 0.4, safe.width * 1.15], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const rimOpacity = interpolate(panelIn, [0, 1], [0, 0.74]);

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: theme.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        ...safeAreaPadding(width, height, safeArea),
        position: 'relative',
        overflow: 'hidden',
        fontFamily: HERO_FONT,
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.62,
          backgroundImage: `
            linear-gradient(${theme.muted}14 1px, transparent 1px),
            linear-gradient(90deg, ${theme.muted}14 1px, transparent 1px)
          `,
          backgroundSize: `${Math.round(width * 0.09)}px ${Math.round(width * 0.09)}px`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: width * 1.05,
          height: width * 1.05,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accent}2C 0%, ${accent}10 27%, transparent 66%)`,
          filter: 'blur(4px)',
          transform: `translateY(${height * -0.03}px) scale(${0.92 + panelIn * 0.08})`,
          opacity: panelIn,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: scanX,
          top: safe.top + safe.height * 0.24,
          height: safe.height * 0.52,
          width: Math.max(10, width * 0.045),
          background: `linear-gradient(90deg, transparent, ${accent}45, transparent)`,
          filter: 'blur(5px)',
          opacity: panelIn * 0.55,
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          width: panelWidth,
          position: 'relative',
          zIndex: 2,
          opacity: panelIn,
          transform: `translateY(${translateY}px)`,
          padding: `${Math.round(height * 0.034)}px ${panelPadX}px ${Math.round(height * 0.04)}px`,
          boxSizing: 'border-box',
          borderRadius: surface === 'glass' ? 34 : 22,
          border: `1.5px solid ${accent}88`,
          background: surface === 'glass'
            ? `linear-gradient(145deg, ${theme.surface}F2, ${theme.bg}DE)`
            : theme.surface,
          boxShadow: `0 0 0 1px ${theme.text}0D inset, 0 22px 58px ${theme.shadowColor}88, 0 0 48px ${accent}25`,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            height: 3,
            width: `${Math.round(55 + panelIn * 45)}%`,
            background: `linear-gradient(90deg, ${accent}, ${theme.cyan}, transparent)`,
            opacity: rimOpacity,
          }}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: Math.round(height * 0.022) }}>
          <div style={{ width: 9, height: 9, borderRadius: '50%', background: accent, boxShadow: `0 0 14px ${accent}` }} />
          <span style={{ fontFamily: '"Inter", system-ui, sans-serif', color: accent, fontSize: Math.round(height * 0.018), fontWeight: 800, letterSpacing: '0.13em', textTransform: 'uppercase' }}>
            {badge || 'НОВЫЙ РАЗБОР'}
          </span>
          <div style={{ flex: 1, height: 1, background: `${theme.muted}44` }} />
          <span style={{ fontFamily: '"Inter", system-ui, sans-serif', color: theme.muted, fontSize: Math.round(height * 0.016), fontWeight: 700 }}>LLM HUBS</span>
        </div>

        <div style={{ overflow: 'visible', maxWidth: titleMaxWidth }}>
          <h1
            style={{
              fontSize: titleFontSize,
              fontWeight: 900,
              color: theme.text,
              letterSpacing: '-0.045em',
              lineHeight: 0.96,
              margin: 0,
              maxWidth: titleMaxWidth,
              textTransform: 'uppercase',
              transform: `translateY(${titleY}px)`,
              opacity: copyIn,
              overflowWrap: 'normal',
              wordBreak: 'keep-all',
              hyphens: 'none',
            }}
          >
            {displayTitle}
          </h1>
        </div>

        <div style={{ width: Math.round(width * 0.13), height: 4, borderRadius: 999, background: accent, boxShadow: `0 0 18px ${accent}`, marginTop: Math.round(height * 0.026), opacity: copyIn }} />
        {subtitle && subFit && (
          <p
            style={{
              fontFamily: '"Inter", system-ui, sans-serif',
              fontSize: subFit.fontSize,
              fontWeight: 700,
              color: theme.muted,
              lineHeight: 1.14,
              margin: `${Math.round(height * 0.022)}px 0 0`,
              maxWidth: titleMaxWidth,
              opacity: copyIn,
              overflowWrap: 'normal',
              wordBreak: 'keep-all',
              hyphens: 'none',
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
};
