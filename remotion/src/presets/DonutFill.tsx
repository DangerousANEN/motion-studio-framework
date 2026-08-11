import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';
import { fitOneLine } from '../theme/layout';

/**
 * Segmented donut/pie whose arcs grow from zero to their share.
 *
 * The percent counters and the arcs are driven by the SAME progress value, not
 * by two independent animations. Running them separately lets the number read
 * "80%" while the arc is drawn at 74% — a few frames of visible disagreement
 * that is obvious once you look for it.
 *
 * Arcs are stroked circles with `strokeDasharray`, not filled `<path>` wedges:
 * a dash offset animates cleanly and needs no arc-flag trigonometry, and the
 * rounded `strokeLinecap` that the design calls for comes for free. `pie` is
 * the same geometry with the stroke width set to the full radius.
 */

const FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif';

/** Fraction of the circle each shape sweeps. halfDonut is a 180° gauge. */
const SWEEP: Record<string, number> = {
  donut: 1,
  pie: 1,
  ring: 1,
  halfDonut: 0.5,
};

export const DonutFill: React.FC<BaseSceneProps> = ({
  segments,
  shape = 'donut',
  thickness,
  // Default: one continuous sweep from 12 o'clock. Segments blooming from
  // their own start points read as unrelated animations, not one chart.
  fillMode = 'fromOrigin',
  centerContent = 'total',
  labelPlacement = 'legend',
  percentCounters = true,
  gapAngle = 2,
  highlightSegment,
  valueSuffix = '%',
  title,
  accentColor = BRAND.neon,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);

  // Spec default for this preset: easeOut over 60 frames. A spring would
  // overshoot, and an arc cannot render >100% without wrapping onto itself.
  const animateValue = resolveMotion(motion ?? { curve: 'easeOut', duration: 60 }, fps, 'value');
  const animateReveal = resolveMotion(motion, fps, 'reveal');

  const data = segments && segments.length > 0
    ? segments.slice(0, 6)
    : [
        { label: 'NO SEGMENTS', value: 100, color: accentColor },
      ];

  const total = data.reduce((acc, s) => acc + Math.max(0, s.value), 0) || 1;

  // accentColor leads the palette, so any brand colour EQUAL to it has to be
  // dropped or two segments render in the same paint. BRAND.accentGreen is
  // '#00FF88' and so is BRAND.neon, which is the accentColor default — so a
  // 3-segment donut painted segments 1 and 3 identically (measured #00F780
  // over 220deg and again over 45deg on the 62/24/14 chart). Those two are
  // adjacent across the ring's closing boundary, which also made the 2deg
  // separator between them read as a hole punched inside one segment rather
  // than as a divider between two.
  const PALETTE = ((): string[] => {
    const candidates = [
      accentColor,
      BRAND.accentCyan,
      BRAND.accentGreen,
      BRAND.gold,
      '#FF6B9D',
      '#A78BFA',
      '#FFB86B',
    ];
    const seen = new Set<string>();
    const unique: string[] = [];
    for (const colour of candidates) {
      const key = colour.trim().toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      unique.push(colour);
    }
    return unique;
  })();

  // Geometry is derived from the safe box: at 1080x1920 the platform profile
  // leaves 920x1260, and the ring must not grow into the caption strip.
  const legendRows = labelPlacement === 'legend' ? data.length : 0;
  const legendHeight = legendRows * 54 + (legendRows ? 24 : 0);
  const titleHeight = title ? 96 : 0;
  const available = Math.min(safe.width, safe.height - legendHeight - titleHeight);
  const size = Math.max(240, available);
  const stroke = thickness ?? (shape === 'pie' ? size / 2 : Math.round(size * 0.13));
  // Stroke straddles the path, so the radius must leave half of it inside.
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const sweep = SWEEP[shape] ?? 1;

  // A round linecap adds a half-disc of radius `stroke/2` to BOTH ends of every
  // arc. At size 920 that is stroke 120 over radius 400 = 8.6deg of overhang per
  // end, which is larger than the 2deg gap the spec asks for: measured on a
  // 62/24/14 donut the arcs swallowed the gaps entirely (sum 359.9deg of 360)
  // and the smallest segment rendered 18.8% instead of 14%. So the cap has to be
  // paid for out of the dash length, and it only exists when a gap exists.
  const useRoundCap = gapAngle > 0;
  const capDegrees = useRoundCap ? (stroke / 2 / radius) * (180 / Math.PI) : 0;
  const capFraction = (capDegrees / 360) * 2; // both ends
  const gapFraction = (gapAngle / 360) * sweep;
  const usableFraction = Math.max(0, sweep - gapFraction * data.length);

  const revealProgress = animateReveal(frame, 0, 1);

  // How much of the ring is drawn overall, 0..1. In 'fromOrigin' every segment
  // is laid end-to-end from the 12 o'clock start and the ring is revealed as ONE
  // continuous sweep, so the arcs appear to grow out of a single point instead
  // of each blooming from its own position. Any other mode animates each arc in
  // place, which reads as several unrelated things happening at once.
  const ringProgress = fillMode === 'fromOrigin' ? animateValue(frame, 0, 1) : 1;

  let cursor = 0;
  const arcs = data.map((segment, i) => {
    const share = Math.max(0, segment.value) / total;
    const fraction = share * usableFraction;

    // sequential/clockSweep hand each segment its own slice of the timeline;
    // simultaneous gives every segment the full window.
    let progress: number;
    if (fillMode === 'fromOrigin') {
      // One shared sweep: this segment fills only once the sweep has travelled
      // past its start, and finishes when the sweep passes its end. Segment i
      // therefore visibly emerges from where segment i-1 ended -- a single
      // growing arc, not three simultaneous ones.
      const startFrac = cursor;
      const endFrac = cursor + fraction;
      const swept = ringProgress * sweep;
      progress =
        endFrac <= startFrac
          ? 0
          : Math.min(1, Math.max(0, (swept - startFrac) / (endFrac - startFrac)));
    } else if (fillMode === 'simultaneous') {
      progress = animateValue(frame, 0, 1);
    } else {
      const per = 60 / data.length;
      progress = animateValue(frame - i * per, 0, 1);
    }
    const clamped = Math.min(1, Math.max(0, progress));

    const start = cursor;
    cursor += fraction + gapFraction;

    // Shorten the stroked path by the cap overhang and push its start inward by
    // half of it, so the *painted* arc — caps included — occupies exactly
    // `fraction`. Segments too small to host their own caps collapse to a dot
    // rather than rendering wider than their share.
    const paintable = Math.max(0, fraction - capFraction);

    // A round cap paints a half-disc even when the dash length is 0, which left
    // a visible dot parked at every segment's start position before its turn
    // came. In 'fromOrigin' that betrayed the illusion of one growing arc: all
    // three anchors were on screen from frame 0. Suppress the stroke entirely
    // until this segment actually starts filling.
    const hasInk = clamped > 0.0001;

    return {
      ...segment,
      color: segment.color || PALETTE[i % PALETTE.length],
      share,
      // The SAME clamped progress feeds the arc length and the counter below.
      progress: clamped,
      hasInk,
      dash: paintable * clamped * circumference,
      offset: (start + capFraction / 2) * circumference,
      displayValue: segment.value * clamped,
    };
  });

  // halfDonut starts at 180° (west) so it reads as a gauge; full shapes start
  // at 12 o'clock.
  const rotation = shape === 'halfDonut' ? 180 : -90;

  const leader = arcs.reduce((a, b) => (b.share > a.share ? b : a), arcs[0]);
  const animatedTotal = arcs.reduce((acc, a) => acc + a.displayValue, 0);

  const centerText =
    centerContent === 'total'
      ? `${Math.round(animatedTotal)}${valueSuffix}`
      : centerContent === 'leader'
        ? `${Math.round(leader.displayValue)}${valueSuffix}`
        : centerContent === 'label'
          ? leader.label
          : '';

  // The centre label must fit the donut hole, not the whole frame.
  const holeWidth = (radius - stroke / 2) * 2 * 0.82;
  const centerSize = centerText
    ? fitOneLine({
        text: centerText,
        maxWidth: Math.max(80, holeWidth),
        fontFamily: FONT,
        fontWeight: 900,
        letterSpacing: '-2px',
        maxFontSize: 128,
        minFontSize: 32,
      })
    : 0;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        backgroundColor: BRAND.bg,
        overflow: 'hidden',
        fontFamily: FONT,
      }}
    >
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
          gap: 24,
        }}
      >
        {title && (
          <h2
            style={{
              margin: 0,
              fontSize: 44,
              fontWeight: 800,
              color: BRAND.text,
              textAlign: 'center',
              letterSpacing: '-1px',
              opacity: revealProgress,
            }}
          >
            {title}
          </h2>
        )}

        <div style={{ position: 'relative', width: size, height: shape === 'halfDonut' ? size / 2 + stroke : size }}>
          <svg
            width={size}
            height={shape === 'halfDonut' ? size / 2 + stroke : size}
            viewBox={`0 0 ${size} ${shape === 'halfDonut' ? size / 2 + stroke : size}`}
            style={{ display: 'block', overflow: 'visible' }}
          >
            <g transform={`rotate(${rotation} ${size / 2} ${size / 2})`}>
              {/* Track: shows the shape before the arcs arrive. */}
              <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={BRAND.surface}
                strokeWidth={stroke}
                strokeDasharray={`${sweep * circumference} ${circumference}`}
              />
              {arcs.map((arc, i) => (
                <circle
                  key={arc.label + i}
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="none"
                  stroke={arc.color}
                  strokeWidth={highlightSegment === i ? stroke * 1.18 : stroke}
                  strokeLinecap={useRoundCap ? 'round' : 'butt'}
                  // Dash pattern: [visible arc, rest of circle]. Offset walks
                  // the start point around; negative because the dash array
                  // advances clockwise under the -90deg rotation.
                  strokeDasharray={`${arc.dash} ${circumference}`}
                  strokeDashoffset={-arc.offset}
                  // A zero-length dash with a round cap still paints a dot.
                  // Hidden until this segment's turn in the sweep arrives.
                  opacity={arc.hasInk ? 1 : 0}
                />
              ))}
            </g>
          </svg>

          {centerText && shape !== 'pie' && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: shape === 'halfDonut' ? 'flex-end' : 'center',
                pointerEvents: 'none',
              }}
            >
              <div
                style={{
                  fontSize: centerSize,
                  fontWeight: 900,
                  color: BRAND.text,
                  letterSpacing: '-2px',
                  lineHeight: 1,
                }}
              >
                {centerText}
              </div>
            </div>
          )}
        </div>

        {labelPlacement === 'legend' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, width: '100%' }}>
            {arcs.map((arc, i) => (
              <div
                key={arc.label + i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  opacity: revealProgress,
                }}
              >
                <span
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: 6,
                    backgroundColor: arc.color,
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontSize: 30,
                    fontWeight: 700,
                    color: BRAND.text,
                    flex: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {arc.label}
                </span>
                {percentCounters && (
                  <span style={{ fontSize: 30, fontWeight: 900, color: arc.color }}>
                    {/* Same `progress` that set this arc's dash length. */}
                    {Math.round(arc.displayValue)}
                    {valueSuffix}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
