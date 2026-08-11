import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea } from '../lib/safeArea';
import { resolveMotion } from '../lib/motion';
import { useStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';

/**
 * Extra data presets: radial gauges and 3D bars.
 *
 * These cover the two shapes DonutFill and StatCounter cannot express:
 *   - several independent percentages at once (DonutFill shows shares of ONE
 *     whole, so three 80% rings are impossible there)
 *   - a magnitude comparison across categories, with depth
 *
 * WHY THE RINGS ARE SVG AND THE BARS ARE CSS 3D
 * ---------------------------------------------
 * A stroked SVG arc is the only reliable way to get a rounded-cap progress ring
 * whose sweep is exactly proportional to a number — a CSS conic-gradient cannot
 * round its ends. The bars, conversely, need real perspective and per-face
 * shading, which CSS transforms give for free and SVG would require faking.
 */

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/** Palette for series data, derived from the active theme. */
const seriesColors = (theme: {
  neon: string;
  cyan: string;
  gold: string;
  accentCyan: string;
}): string[] => [theme.neon, theme.cyan, theme.gold, theme.accentCyan, '#FF4D9D', '#8B7CFF'];

/* -------------------------------------------------------------- RingStats */

/**
 * RingStats — up to six independent progress rings that sweep to their value.
 *
 * Reads: segments[]{label,value,color}, valueSuffix, title, subtitle, ringMax
 *
 * Unlike DonutFill, each ring is its OWN 0..100 scale. `ringMax` overrides the
 * top of that scale (e.g. 60 fps target, 200% growth).
 */
export const RingStats: React.FC<BaseSceneProps> = ({
  segments,
  title,
  subtitle,
  valueSuffix = '%',
  ringMax = 100,
  motion,
  safeArea = 'platform',
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const { theme, fonts, accent: styleAccent } = useStyle();
  const accent = accentColor || styleAccent;
  const animate = resolveMotion(motion, fps, 'value');

  const items = (Array.isArray(segments) && segments.length
    ? segments
    : [
        { label: 'Скорость', value: 92 },
        { label: 'Точность', value: 78 },
        { label: 'Стоимость', value: 41 },
      ]) as { label?: string; value?: number; color?: string }[];

  const shown = items.slice(0, 6);
  const colors = seriesColors(theme);
  const max = typeof ringMax === 'number' && ringMax > 0 ? ringMax : 100;

  // Layout: 3 per row max, so 1-3 items sit in one row and 4-6 in two.
  const perRow = shown.length <= 3 ? shown.length : Math.ceil(shown.length / 2);
  const rows = Math.ceil(shown.length / perRow);
  const gap = Math.round(safe.width * 0.05);
  const cell = Math.min(
    (safe.width - gap * (perRow - 1)) / perRow,
    (safe.height * (title ? 0.66 : 0.86) - gap * (rows - 1)) / rows
  );
  const stroke = Math.max(8, Math.round(cell * 0.085));
  const r = (cell - stroke) / 2;
  const circumference = 2 * Math.PI * r;

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
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
          gap: Math.round(height * 0.03),
          boxSizing: 'border-box',
        }}
      >
        {title && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: Math.round(height * 0.033),
              fontWeight: 800,
              color: theme.text,
              textAlign: 'center',
              opacity: animate(frame, 0, 1),
            }}
          >
            {title}
          </div>
        )}

        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap,
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {shown.map((s, i) => {
            const target = clamp01((s.value ?? 0) / max);
            // Staggered so the rings fill in sequence, not in unison.
            const p = animate(frame - i * 7, 0, 1) * target;
            const color = s.color || colors[i % colors.length];
            const displayed = Math.round(p * max);
            return (
              <div
                key={i}
                style={{
                  width: cell,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: Math.round(cell * 0.06),
                }}
              >
                <div style={{ width: cell, height: cell, position: 'relative' }}>
                  <svg width={cell} height={cell} style={{ transform: 'rotate(-90deg)' }}>
                    <circle
                      cx={cell / 2}
                      cy={cell / 2}
                      r={r}
                      fill="none"
                      stroke={`${theme.muted}33`}
                      strokeWidth={stroke}
                    />
                    <circle
                      cx={cell / 2}
                      cy={cell / 2}
                      r={r}
                      fill="none"
                      stroke={color}
                      strokeWidth={stroke}
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                      // Dash offset is the sweep: exactly proportional to value.
                      strokeDashoffset={circumference * (1 - p)}
                      style={{ filter: `drop-shadow(0 0 ${stroke * 0.5}px ${color}66)` }}
                    />
                  </svg>
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <span
                      style={{
                        fontFamily: fonts.display,
                        fontSize: Math.round(cell * 0.23),
                        fontWeight: 900,
                        color: theme.text,
                        fontVariantNumeric: 'tabular-nums',
                        lineHeight: 1,
                      }}
                    >
                      {displayed}
                      <span style={{ fontSize: Math.round(cell * 0.11), color: theme.muted }}>
                        {valueSuffix}
                      </span>
                    </span>
                  </div>
                </div>
                {s.label && (
                  <span
                    style={{
                      fontFamily: fonts.body,
                      fontSize: Math.round(cell * 0.1),
                      color: theme.muted,
                      textAlign: 'center',
                      fontWeight: 600,
                    }}
                  >
                    {s.label}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {subtitle && (
          <div
            style={{
              fontFamily: fonts.body,
              fontSize: Math.round(height * 0.019),
              color: accent,
              fontWeight: 600,
              textAlign: 'center',
            }}
          >
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
};

/* ----------------------------------------------------------------- Bars3D */

/**
 * Bars3D — extruded bars rising out of a ground plane.
 *
 * Reads: segments[]{label,value,color}, valueSuffix, title, subtitle, barDepth
 *
 * The perspective is a single shared CSS `perspective` on the container with
 * each bar built from three faces (front, top, side). That is cheap, exact, and
 * — unlike a WebGL scene — needs no canvas, so it composites correctly inside
 * the shader transitions that rasterise the DOM.
 */
export const Bars3D: React.FC<BaseSceneProps> = ({
  segments,
  title,
  subtitle,
  valueSuffix = '',
  barDepth,
  motion,
  safeArea = 'platform',
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const { theme, fonts, accent: styleAccent } = useStyle();
  const accent = accentColor || styleAccent;
  const animate = resolveMotion(motion, fps, 'value');

  const items = (Array.isArray(segments) && segments.length
    ? segments
    : [
        { label: 'Янв', value: 32 },
        { label: 'Фев', value: 48 },
        { label: 'Мар', value: 61 },
        { label: 'Апр', value: 87 },
      ]) as { label?: string; value?: number; color?: string }[];

  const shown = items.slice(0, 8);
  const colors = seriesColors(theme);
  const maxValue = Math.max(...shown.map((s) => s.value ?? 0), 1);

  const plotH = Math.round(safe.height * (title ? 0.6 : 0.74));
  const gap = Math.round(safe.width * 0.03);
  const barW = Math.max(
    24,
    Math.min((safe.width - gap * (shown.length - 1)) / shown.length, safe.width * 0.17)
  );
  const depth = typeof barDepth === 'number' ? barDepth : Math.round(barW * 0.34);

  /** Shade a hex colour by a factor for the top/side faces. */
  const shade = (hex: string, f: number): string => {
    const m = hex.replace('#', '');
    const full = m.length === 3 ? m.split('').map((c) => c + c).join('') : m;
    const n = parseInt(full, 16);
    if (Number.isNaN(n) || full.length !== 6) return hex;
    const cl = (v: number) => Math.max(0, Math.min(255, Math.round(v)));
    return `rgb(${cl(((n >> 16) & 255) * f)}, ${cl(((n >> 8) & 255) * f)}, ${cl((n & 255) * f)})`;
  };

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div
        style={{
          position: 'absolute',
          top: safe.top,
          left: safe.left,
          width: safe.width,
          height: safe.height,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: Math.round(height * 0.03),
          boxSizing: 'border-box',
        }}
      >
        {title && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: Math.round(height * 0.033),
              fontWeight: 800,
              color: theme.text,
              opacity: animate(frame, 0, 1),
            }}
          >
            {title}
          </div>
        )}

        <div
          style={{
            height: plotH,
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'center',
            gap,
            perspective: Math.round(height * 1.1),
            perspectiveOrigin: '50% 78%',
          }}
        >
          {shown.map((s, i) => {
            const target = (s.value ?? 0) / maxValue;
            const grow = animate(frame - i * 6, 0, 1);
            const h = Math.max(2, plotH * 0.84 * target * grow);
            const color = s.color || colors[i % colors.length];
            const displayed = Math.round((s.value ?? 0) * grow);

            return (
              <div
                key={i}
                style={{
                  width: barW,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: Math.round(barW * 0.14),
                  transformStyle: 'preserve-3d',
                }}
              >
                <span
                  style={{
                    fontFamily: fonts.display,
                    fontSize: Math.round(barW * 0.3),
                    fontWeight: 800,
                    color: theme.text,
                    fontVariantNumeric: 'tabular-nums',
                    opacity: grow,
                  }}
                >
                  {displayed}
                  {valueSuffix}
                </span>

                {/* the extruded bar: front face + top face + right side */}
                <div
                  style={{
                    position: 'relative',
                    width: barW,
                    height: h,
                    transformStyle: 'preserve-3d',
                    transform: 'rotateX(6deg) rotateY(-16deg)',
                  }}
                >
                  {/* front */}
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: `linear-gradient(180deg, ${color}, ${shade(color, 0.72)})`,
                      borderRadius: `${barW * 0.06}px ${barW * 0.06}px 0 0`,
                      boxShadow: `0 0 ${barW * 0.5}px ${color}33`,
                    }}
                  />
                  {/* top */}
                  <div
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      width: barW,
                      height: depth,
                      background: shade(color, 1.28),
                      transformOrigin: 'top',
                      transform: `rotateX(-90deg)`,
                      borderRadius: 2,
                    }}
                  />
                  {/* right side */}
                  <div
                    style={{
                      position: 'absolute',
                      right: 0,
                      top: 0,
                      width: depth,
                      height: h,
                      background: shade(color, 0.5),
                      transformOrigin: 'right',
                      transform: `rotateY(90deg)`,
                    }}
                  />
                </div>

                {/* ground shadow anchors the bar to the plane */}
                <div
                  style={{
                    width: barW * 1.05,
                    height: Math.round(barW * 0.1),
                    borderRadius: '50%',
                    background: `radial-gradient(ellipse, rgba(0,0,0,0.55), transparent 72%)`,
                    marginTop: -Math.round(barW * 0.05),
                  }}
                />

                {s.label && (
                  <span
                    style={{
                      fontFamily: fonts.body,
                      fontSize: Math.round(barW * 0.19),
                      color: theme.muted,
                      fontWeight: 600,
                      textAlign: 'center',
                    }}
                  >
                    {s.label}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {subtitle && (
          <div
            style={{
              fontFamily: fonts.body,
              fontSize: Math.round(height * 0.019),
              color: accent,
              fontWeight: 600,
            }}
          >
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
};
