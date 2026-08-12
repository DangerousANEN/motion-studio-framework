import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea } from '../lib/safeArea';
import { resolveMotion } from '../lib/motion';
import { useStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';
import { fitWrapped } from '../theme/layout';

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
  // Cell must leave room for the label slot below the ring, or a 6-ring layout
  // overflows the safe box vertically once labels are reserved.
  const cell = Math.min(
    (safe.width - gap * (perRow - 1)) / perRow,
    ((safe.height * (title ? 0.66 : 0.86) - gap * (rows - 1)) / rows) * 0.8
  );
  const stroke = Math.max(8, Math.round(cell * 0.085));
  const r = (cell - stroke) / 2;
  const circumference = 2 * Math.PI * r;

  // FIXED-HEIGHT LABEL SLOT, same reason as Bars3D.
  // The wrap container centres its items, so a two-line label made its column
  // taller and shoved that ring UP relative to its neighbours — three rings on
  // three different centre lines. "Qwen3.6-235B-A22B" wraps while
  // "GLM-5.2-Air" does not, so mixed model names always broke the row.
  // Reserving two lines for every label keeps every ring on one axis.
  const labelFont = Math.round(cell * 0.1);
  const labelSlotH = Math.round(labelFont * 1.15 * 2);

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
                {/* Label slot: fixed height so a wrapping name cannot lift its
                    ring off the shared centre line. Font is MEASURED — a long
                    model name at a flat cell*0.1 overflowed the cell width. */}
                <div
                  style={{
                    height: labelSlotH,
                    width: cell,
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'center',
                  }}
                >
                  {s.label && (
                    <span
                      style={{
                        fontFamily: fonts.body,
                        fontSize: fitWrapped({
                          text: s.label,
                          maxWidth: cell * 0.98,
                          maxHeight: labelSlotH,
                          fontFamily: fonts.body,
                          fontWeight: 600,
                          maxLines: 2,
                          maxFontSize: labelFont,
                          minFontSize: Math.round(height * 0.011),
                        }).fontSize,
                        color: theme.muted,
                        textAlign: 'center',
                        fontWeight: 600,
                        lineHeight: 1.15,
                      }}
                    >
                      {s.label}
                    </span>
                  )}
                </div>
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
  // A column is WIDER than its bar: the isometric block extends `depth` to the
  // right. Budget the column first, then derive the bar, or the extrusion pushes
  // neighbours together and the last column overflows the safe box (seen as
  // "labels crammed on one line, shifted left, bars touching").
  const DEPTH_RATIO = 0.34;
  const colW = Math.max(
    32,
    Math.min((safe.width - gap * (shown.length - 1)) / shown.length, safe.width * 0.2)
  );
  const barW = Math.round(colW / (1 + DEPTH_RATIO));
  const depth = typeof barDepth === 'number' ? barDepth : Math.round(barW * DEPTH_RATIO);
  // Every column reserves the same label slot so one-line and two-line labels
  // cannot shift their bars off the shared baseline. Two lines plus leading.
  const labelSlotH = Math.round(barW * 0.19 * 2 * 1.15);
  // The tallest bar must leave room for: the isometric cap it lifts (depth*0.52),
  // the value text above it, the ground shadow and the label slot below. Without
  // this the block grew past the plot box and the value collided with the title.
  const valueH = Math.round(barW * 0.3 * 1.2);
  const chromeH = valueH + labelSlotH + Math.round(barW * 0.25) + Math.round(depth * 0.52);
  const barMaxH = Math.max(40, plotH - chromeH);

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
            const h = Math.max(2, barMaxH * target * grow);
            const color = s.color || colors[i % colors.length];
            const displayed = Math.round((s.value ?? 0) * grow);

            // ISOMETRIC EXTRUSION VIA clip-path, NOT CSS 3D ROTATION.
            // The faces used to be three divs rotated -90deg/90deg inside a
            // parent at rotateX(6deg), under a `perspective` on the flex row with
            // perspectiveOrigin 50% 78%. Two things went wrong:
            //   * a face rotated -90deg against a parent tilted only 6deg ends up
            //     ~84deg to the camera, i.e. nearly edge-on, so the top face
            //     rendered as a 1-2px sliver instead of a cap;
            //   * the bars stand ABOVE the perspective origin, so the camera sees
            //     the UNDERSIDE of that cap — a backface — which is why what
            //     survived looked like a detached triangular shard at the
            //     top-right corner rather than part of the block.
            // Vision check on the render: "top face missing / detached shard" on
            // all three bars. Perspective-free isometric polygons cannot fail
            // that way: dx/dy are fixed pixel offsets, so the cap is always a
            // real parallelogram and the block always reads as solid.
            const dx = depth;
            const dy = Math.round(depth * 0.52);
            const blockW = barW + dx;
            const blockH = h + dy;
            // Front face occupies y = dy..dy+h; the cap rises to y = 0 at x = dx.
            const front = `polygon(0px ${dy}px, ${barW}px ${dy}px, ${barW}px ${blockH}px, 0px ${blockH}px)`;
            const cap = `polygon(0px ${dy}px, ${dx}px 0px, ${blockW}px 0px, ${barW}px ${dy}px)`;
            const side = `polygon(${barW}px ${dy}px, ${blockW}px 0px, ${blockW}px ${h}px, ${barW}px ${blockH}px)`;

            return (
              <div
                key={i}
                style={{
                  width: colW,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: Math.round(barW * 0.14),
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

                {/* the extruded bar: front face + cap + right side, all clipped
                    out of one box so they cannot drift apart */}
                <div style={{ position: 'relative', width: blockW, height: blockH }}>
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      clipPath: cap,
                      background: shade(color, 1.3),
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      clipPath: side,
                      background: `linear-gradient(180deg, ${shade(color, 0.62)}, ${shade(color, 0.4)})`,
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      clipPath: front,
                      background: `linear-gradient(180deg, ${color}, ${shade(color, 0.72)})`,
                      filter: `drop-shadow(0 0 ${Math.round(barW * 0.3)}px ${color}44)`,
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

                {/* FIXED-HEIGHT LABEL SLOT.
                    The row is aligned flex-end, so the column's BOTTOM edge is
                    what lines up — not the bar's. A one-line label ("GLM-5.2")
                    made its column shorter than a two-line one ("Qwen3.6-27B"),
                    pushing that bar visibly below the others' baseline (caught in
                    review as "the gold bar sits lower"). Reserving the same slot
                    for every label puts all bars back on one line.
                    Size is measured, not assumed: model names are long and a
                    fixed barW*0.19 clipped them under `overflow: hidden`. */}
                <div
                  style={{
                    height: labelSlotH,
                    width: colW,
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'center',
                  }}
                >
                  {s.label && (
                    <span
                      style={{
                        fontFamily: fonts.body,
                        fontSize: fitWrapped({
                          text: s.label,
                          maxWidth: colW * 0.96,
                          maxHeight: labelSlotH,
                          fontFamily: fonts.body,
                          fontWeight: 600,
                          maxLines: 2,
                          maxFontSize: Math.round(barW * 0.19),
                          minFontSize: Math.round(height * 0.011),
                        }).fontSize,
                        color: theme.muted,
                        fontWeight: 600,
                        textAlign: 'center',
                        lineHeight: 1.15,
                      }}
                    >
                      {s.label}
                    </span>
                  )}
                </div>
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
