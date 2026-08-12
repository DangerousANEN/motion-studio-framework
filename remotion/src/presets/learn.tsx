import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea } from '../lib/safeArea';
import { resolveMotion } from '../lib/motion';
import { useStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';
import { fitWrapped, measure } from '../theme/layout';

/**
 * Learn preset pack — educational and explanatory scenes.
 *
 * Four presets for structured knowledge delivery:
 *   - QuizCard      — interactive question with reveal mechanics
 *   - ProgressPath  — roadmap/checklist with animated connector line
 *   - DefinitionCard — term + definition with accent bar and optional example
 *   - TimelineReveal — chronology axis with per-event reveals
 *
 * CONVENTIONS
 * -----------
 * - All sizes are proportional to width/height (never absolute px).
 * - All durations derived from durationInFrames (never hardcoded frames).
 * - Randomness via mulberry32 (seeded) — never Math.random().
 * - Semantic colour constants for correct/incorrect states (only exception
 *   to the "no hardcoded colours" rule, per spec).
 * - BaseSceneSchema has .passthrough() — extra props arrive at runtime.
 */

// ---------------------------------------------------------------------------
// Semantic state colours (sole exception to the no-hardcode rule)
// ---------------------------------------------------------------------------
/** Correct-answer green — semantic, not decorative. */
const CORRECT_GREEN = '#22C55E';
/** Wrong-answer red — semantic, not decorative. */
const WRONG_RED = '#EF4444';

// ---------------------------------------------------------------------------
// Seeded PRNG — mulberry32 (same impl as camera.tsx)
// ---------------------------------------------------------------------------
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------------------
// clamp01 helper
// ---------------------------------------------------------------------------
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/* ======================================================================
   1. QuizCard
   ======================================================================
   question   — the question text (may be multi-line)
   options[]  — answer strings, typically 4
   correctIndex — which index (0-based) is the right answer
   revealAtProgress — fraction 0..1 of the scene at which answer is revealed
   ====================================================================== */

type QuizProps = BaseSceneProps & {
  question?: string;
  options?: string[];
  correctIndex?: number;
  revealAtProgress?: number;
};

/**
 * QuizCard — animated question + multiple-choice options.
 *
 * Phase 1 (0 → revealAt): options stagger in from the right, one by one.
 * Phase 2 (revealAt → end): correct option turns green (+✓), others dim,
 *          a chosen wrong option (index 0 if not correctIndex) gets a ✗.
 *
 * Reads: question, options[], correctIndex, revealAtProgress.
 */
export const QuizCard: React.FC<BaseSceneProps> = (props) => {
  const { question, options, correctIndex = 0, revealAtProgress = 0.55 } =
    props as QuizProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'reveal');

  // Defaults
  const q = question ?? 'Что является ключевым принципом ООП?';
  const opts: string[] = Array.isArray(options) && options.length >= 2
    ? options
    : ['Инкапсуляция', 'Компиляция', 'Линкование', 'Рендеринг'];

  // Reveal threshold in frames
  const revealFrame = Math.round(revealAtProgress * durationInFrames);
  const revealed = frame >= revealFrame;

  // Wrong-answer index to mark with ✗: first non-correct index
  const wrongIdx = opts.findIndex((_, i) => i !== correctIndex);

  // Layout — vertical stack inside safe area
  const titleFontSize = Math.round(
    Math.min(height * 0.038, (safe.width / Math.max(q.length, 1)) * 2.2)
  );
  const cardH = Math.round(safe.height * 0.1);
  const cardGap = Math.round(safe.height * 0.025);
  const optFontSize = Math.round(height * 0.028);
  const radius = Math.round(height * 0.016);
  const badgeSize = Math.round(height * 0.038);

  // Question fade-in
  const qOpacity = animate(frame, 0, 1);
  const qY = interpolate(frame, [0, Math.round(fps * 0.5)], [24, 0], { extrapolateRight: 'clamp' });

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
          gap: Math.round(safe.height * 0.04),
          boxSizing: 'border-box',
        }}
      >
        {/* Question */}
        <div
          style={{
            opacity: qOpacity,
            transform: `translateY(${qY}px)`,
          }}
        >
          {/* "?" badge */}
          <div
            style={{
              width: badgeSize,
              height: badgeSize,
              borderRadius: '50%',
              backgroundColor: accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: fonts.display,
              fontSize: Math.round(badgeSize * 0.55),
              fontWeight: 900,
              color: theme.bg,
              marginBottom: Math.round(height * 0.018),
            }}
          >
            ?
          </div>
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: titleFontSize,
              fontWeight: 800,
              color: theme.text,
              lineHeight: 1.25,
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
            }}
          >
            {q}
          </div>
        </div>

        {/* Options */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: cardGap,
          }}
        >
          {opts.slice(0, 6).map((opt, i) => {
            // Stagger: each option starts 6 frames after the previous
            const staggerDelay = 8 + i * 8;
            const entryProgress = clamp01(animate(frame - staggerDelay, 0, 1));
            const slideX = (1 - entryProgress) * 80;

            // State after reveal
            const isCorrect = i === correctIndex;
            const isWrong = revealed && !isCorrect && i === wrongIdx;

            let bgColor = theme.surface;
            let borderColor = `${theme.muted}44`;
            let textColor = theme.text;
            let cardOpacity = entryProgress;

            if (revealed) {
              if (isCorrect) {
                bgColor = `${CORRECT_GREEN}22`;
                borderColor = CORRECT_GREEN;
                textColor = CORRECT_GREEN;
              } else if (isWrong) {
                bgColor = `${WRONG_RED}18`;
                borderColor = WRONG_RED;
                textColor = WRONG_RED;
                cardOpacity = entryProgress * 0.85;
              } else {
                cardOpacity = entryProgress * 0.45;
                borderColor = `${theme.muted}22`;
              }
            }

            // Label A / B / C / D
            const label = String.fromCharCode(65 + i);

            return (
              <div
                key={i}
                style={{
                  height: cardH,
                  display: 'flex',
                  alignItems: 'center',
                  gap: Math.round(safe.width * 0.035),
                  backgroundColor: bgColor,
                  border: `2px solid ${borderColor}`,
                  borderRadius: radius,
                  paddingLeft: Math.round(safe.width * 0.04),
                  paddingRight: Math.round(safe.width * 0.04),
                  opacity: cardOpacity,
                  transform: `translateX(${slideX}px)`,
                  boxSizing: 'border-box',
                  transition: 'border-color 0.1s',
                }}
              >
                {/* Letter badge */}
                <div
                  style={{
                    minWidth: Math.round(height * 0.038),
                    height: Math.round(height * 0.038),
                    borderRadius: '50%',
                    border: `2px solid ${borderColor}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: fonts.display,
                    fontSize: Math.round(height * 0.022),
                    fontWeight: 700,
                    color: textColor,
                    flexShrink: 0,
                  }}
                >
                  {label}
                </div>
                {/* Option text */}
                <span
                  style={{
                    fontFamily: fonts.body,
                    fontSize: optFontSize,
                    fontWeight: 600,
                    color: textColor,
                    flex: 1,
                    overflowWrap: 'break-word',
                    wordBreak: 'break-word',
                    lineHeight: 1.3,
                  }}
                >
                  {opt}
                </span>
                {/* Status icon after reveal */}
                {revealed && (isCorrect || isWrong) && (
                  <div
                    style={{
                      fontFamily: fonts.display,
                      fontSize: Math.round(height * 0.032),
                      color: isCorrect ? CORRECT_GREEN : WRONG_RED,
                      flexShrink: 0,
                    }}
                  >
                    {isCorrect ? '✓' : '✗'}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

/* ======================================================================
   2. ProgressPath
   ======================================================================
   steps[]    — [{label, description?} | string]
   currentStep — 0-based index of the active step
   title      — headline above the path
   orientation — 'vertical' | 'horizontal'
   ====================================================================== */

type StepItem = { label: string; description?: string } | string;

type ProgressPathProps = BaseSceneProps & {
  steps?: StepItem[];
  currentStep?: number;
  orientation?: 'vertical' | 'horizontal';
};

/**
 * ProgressPath — animated roadmap with a drawing connector line.
 *
 * The line is drawn progressively via clipPath/scaleY (vertical) or scaleX
 * (horizontal). Past steps receive a ✓ badge; the current step pulses;
 * future steps appear dimmed.
 *
 * Reads: steps[], currentStep, title, orientation.
 */
export const ProgressPath: React.FC<BaseSceneProps> = (props) => {
  const {
    steps,
    currentStep = 1,
    orientation = 'vertical',
    title,
  } = props as ProgressPathProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'reveal');

  // Normalize steps
  const rawSteps: StepItem[] = Array.isArray(steps) && steps.length >= 2
    ? steps
    : [
        { label: 'Начало', description: 'Стартовая точка' },
        { label: 'Изучение', description: 'Основные концепции' },
        { label: 'Практика', description: 'Реальные проекты' },
        { label: 'Мастерство', description: 'Финальная цель' },
      ];

  const normalized = rawSteps.map((s) =>
    typeof s === 'string' ? { label: s, description: undefined } : s
  );
  const count = normalized.length;
  const cur = Math.max(0, Math.min(currentStep, count - 1));

  const isVertical = orientation !== 'horizontal';

  // Overall entry animation: how much of the scene has elapsed (0..1)
  const sceneProgress = clamp01(frame / durationInFrames);

  // Line draw progress: runs over the first 60% of the scene, based on
  // currentStep fraction. We animate from 0 to the correct fraction.
  const targetLineFraction = count > 1 ? cur / (count - 1) : 1;
  const lineDrawProgress = clamp01(animate(frame, 0, targetLineFraction));

  // Pulse for current step: sine wave anchored to frame count
  const pulseT = (Math.sin((frame / fps) * Math.PI * 2) + 1) / 2;
  const pulseScale = 1 + pulseT * 0.12;
  const pulseOpacity = 0.7 + pulseT * 0.3;

  // Title fade-in
  const titleOpacity = animate(frame, 0, 1);

  // Layout
  const dotR = Math.round(Math.min(width, height) * 0.026);
  const dotDiameter = dotR * 2;
  const lineThickness = Math.round(Math.min(width, height) * 0.006);

  const titleFontSize = Math.round(height * 0.034);
  const labelFontSize = Math.round(height * 0.026);
  const descFontSize = Math.round(height * 0.019);

  // Render
  if (isVertical) {
    // --- VERTICAL layout ---
    //
    // STEP SPACING IS SOLVED FROM THE REAL COLUMN HEIGHT.
    //
    // It used to be `safe.height * (title ? 0.82 : 0.92) / (count - 1)`, and the
    // 0.82 was doing two incompatible jobs: standing in for the title block and
    // reserving room for the last step's own height. It did neither. The title
    // lives ABOVE the path area, so its height was subtracted from nothing —
    // the last dot landed at titleBlock + totalH, and its label extended past
    // that. Measured with 5 steps and a title: content ran to y=1656, which is
    // 116px inside the 380px bottom band that platform reserves for the caption
    // and the action rail. Nothing was clipped, so no probe complained; the last
    // step would simply have sat under TikTok's UI.
    //
    // Now the title block is measured, the last row's height is reserved, and the
    // steps are distributed across what genuinely remains.
    const gapX = Math.round(safe.width * 0.045);
    const labelColW = safe.width - dotDiameter - gapX;

    // ROW HEIGHT MUST BE MEASURED FROM THE WRAPPED LINES, NOT DIVIDED WIDTHS.
    //
    // A `ceil(width / colW)` estimate is wrong in both directions and this
    // preset hit both. CSS breaks on word boundaries, so a string 1.05 columns
    // wide takes 2 lines while the estimate says 2 only if it exceeds 1.0 —
    // and, worse, a string 1.9 columns wide can take 3 lines once the last word
    // will not fit. `fitWrapped` returns the library's real line breakdown at a
    // FIXED size (maxFontSize == minFontSize pins it), so the count matches what
    // the browser will actually do.
    const wrapLines = (
      text: string,
      fontSize: number,
      colW: number,
      family: string,
      weight: number
    ) => {
      if (!text) return 0;
      return fitWrapped({
        text,
        maxWidth: colW,
        fontFamily: family,
        fontWeight: weight,
        maxLines: 6,
        maxFontSize: fontSize,
        minFontSize: fontSize,
      }).lines.length;
    };

    const rowHeights = normalized.map((s, i) => {
      // The current step renders at weight 800, the rest at 600.
      const labelH =
        wrapLines(s.label, labelFontSize, labelColW, fonts.display, i === cur ? 800 : 600) *
        labelFontSize *
        1.25;
      const descH = s.description
        ? wrapLines(s.description, descFontSize, labelColW, fonts.body, 400) *
            descFontSize *
            1.3 +
          Math.round(height * 0.005)
        : 0;
      return Math.max(dotDiameter, Math.ceil(labelH + descH));
    });
    const lastRowH = rowHeights[rowHeights.length - 1];

    const titleBlockH = title
      ? wrapLines(title, titleFontSize, safe.width, fonts.display, 800) * titleFontSize * 1.2 +
        Math.round(height * 0.032)
      : 0;

    // A step row is `position: absolute; top: stepSpacing * i`, so its box grows
    // DOWNWARD from that y — `alignItems: 'center'` only centres the dot against
    // the label inside the row, it does not centre the row on the dot. I assumed
    // otherwise and reserved lastRowH/2, which put content 36px deeper into the
    // reserved band than reserving nothing would have.
    //
    // So the last row's FULL height must come out of the span, plus a few px for
    // the difference between the assumed 1.25 line box and what the font actually
    // renders (measured 8px on a two-line Cyrillic label).
    const slack = Math.round(height * 0.008);
    const span = Math.max(0, safe.height - titleBlockH - lastRowH - slack);
    const stepSpacing = count > 1 ? span / (count - 1) : span / 2;

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
            boxSizing: 'border-box',
          }}
        >
          {/* Title */}
          {title && (
            <div
              style={{
                fontFamily: fonts.display,
                fontSize: titleFontSize,
                fontWeight: 800,
                color: theme.text,
                opacity: titleOpacity,
                marginBottom: Math.round(height * 0.032),
                overflowWrap: 'break-word',
              }}
            >
              {title}
            </div>
          )}

          {/* Path area */}
          <div
            style={{
              position: 'relative',
              flex: 1,
            }}
          >
            {/* Connector line — background track */}
            <div
              style={{
                position: 'absolute',
                left: dotR - Math.round(lineThickness / 2),
                top: dotR,
                width: lineThickness,
                height: stepSpacing * (count - 1),
                backgroundColor: `${theme.muted}33`,
                borderRadius: lineThickness,
              }}
            />
            {/* Connector line — animated fill */}
            <div
              style={{
                position: 'absolute',
                left: dotR - Math.round(lineThickness / 2),
                top: dotR,
                width: lineThickness,
                height: stepSpacing * (count - 1) * lineDrawProgress,
                backgroundColor: accent,
                borderRadius: lineThickness,
              }}
            />

            {/* Steps */}
            {normalized.map((step, i) => {
              // Per-step entrance: staggered
              const delay = i * 6;
              const stepEntry = clamp01(animate(frame - delay, 0, 1));

              const isDone = i < cur;
              const isCurrent = i === cur;

              let dotBg = `${theme.muted}33`;
              let dotBorder = `${theme.muted}55`;
              let labelColor = theme.muted;
              if (isDone) {
                dotBg = accent;
                dotBorder = accent;
                labelColor = theme.text;
              } else if (isCurrent) {
                dotBg = accent;
                dotBorder = accent;
                labelColor = theme.text;
              }

              const dotScale = isCurrent ? pulseScale : 1;
              const dotOp = isCurrent ? pulseOpacity : stepEntry;

              return (
                <div
                  key={i}
                  style={{
                    position: 'absolute',
                    top: Math.round(stepSpacing * i),
                    left: 0,
                    right: 0,
                    display: 'flex',
                    // TOP-aligned, not centre-aligned. With `center`, the dot is
                    // centred in a row whose height depends on how many lines its
                    // label wrapped to — so a 2-line description pushed its own
                    // dot further down and the dot-to-dot gaps came out uneven
                    // (measured 237 / 261 / 285 px on one 4-step path) even though
                    // stepSpacing was constant. Top-aligning pins every dot to
                    // stepSpacing * i + dotR regardless of text height.
                    alignItems: 'flex-start',
                    gap: gapX,
                    opacity: stepEntry,
                  }}
                >
                  {/* Dot */}
                  <div
                    style={{
                      width: dotDiameter,
                      height: dotDiameter,
                      borderRadius: '50%',
                      backgroundColor: dotBg,
                      border: `2px solid ${dotBorder}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      transform: `scale(${dotScale})`,
                      opacity: dotOp,
                      zIndex: 2,
                    }}
                  >
                    {isDone && (
                      <span
                        style={{
                          fontFamily: fonts.display,
                          fontSize: Math.round(dotR * 0.9),
                          fontWeight: 900,
                          color: theme.bg,
                        }}
                      >
                        ✓
                      </span>
                    )}
                    {isCurrent && (
                      <div
                        style={{
                          width: Math.round(dotR * 0.55),
                          height: Math.round(dotR * 0.55),
                          borderRadius: '50%',
                          backgroundColor: theme.bg,
                        }}
                      />
                    )}
                  </div>

                  {/* Label + description.
                      The row is top-aligned so dots stay evenly spaced, so the
                      first label line is nudged to sit centred against the dot
                      rather than at the dot's very top. */}
                  <div
                    style={{
                      flex: 1,
                      paddingTop: Math.max(
                        0,
                        Math.round((dotDiameter - labelFontSize * 1.2) / 2)
                      ),
                    }}
                  >
                    <div
                      style={{
                        fontFamily: fonts.display,
                        fontSize: labelFontSize,
                        fontWeight: isCurrent ? 800 : 600,
                        color: labelColor,
                        overflowWrap: 'break-word',
                      }}
                    >
                      {step.label}
                    </div>
                    {step.description && (
                      <div
                        style={{
                          fontFamily: fonts.body,
                          fontSize: descFontSize,
                          color: theme.muted,
                          marginTop: Math.round(height * 0.005),
                          overflowWrap: 'break-word',
                        }}
                      >
                        {step.description}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // --- HORIZONTAL layout ---
  const totalW = safe.width * 0.92;
  const stepSpacingH = count > 1 ? totalW / (count - 1) : totalW / 2;
  const startX = (safe.width - totalW) / 2;
  const lineY = dotR + (title ? Math.round(titleFontSize * 1.6 + height * 0.04) : 0);

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
          boxSizing: 'border-box',
        }}
      >
        {/* Title */}
        {title && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: titleFontSize,
              fontWeight: 800,
              color: theme.text,
              opacity: titleOpacity,
              marginBottom: Math.round(height * 0.04),
              textAlign: 'center',
              overflowWrap: 'break-word',
            }}
          >
            {title}
          </div>
        )}

        {/* Path area */}
        <div
          style={{
            position: 'relative',
            width: safe.width,
            height: Math.round(safe.height * 0.45),
          }}
        >
          {/* Background track */}
          <div
            style={{
              position: 'absolute',
              left: startX + dotR,
              top: lineY - Math.round(lineThickness / 2),
              width: stepSpacingH * (count - 1),
              height: lineThickness,
              backgroundColor: `${theme.muted}33`,
              borderRadius: lineThickness,
            }}
          />
          {/* Animated fill */}
          <div
            style={{
              position: 'absolute',
              left: startX + dotR,
              top: lineY - Math.round(lineThickness / 2),
              width: stepSpacingH * (count - 1) * lineDrawProgress,
              height: lineThickness,
              backgroundColor: accent,
              borderRadius: lineThickness,
            }}
          />

          {/* Steps */}
          {normalized.map((step, i) => {
            const delay = i * 6;
            const stepEntry = clamp01(animate(frame - delay, 0, 1));
            const isDone = i < cur;
            const isCurrent = i === cur;

            let dotBg = `${theme.muted}33`;
            let dotBorder = `${theme.muted}55`;
            let labelColor = theme.muted;
            if (isDone || isCurrent) {
              dotBg = accent;
              dotBorder = accent;
              labelColor = theme.text;
            }

            const dotScale = isCurrent ? pulseScale : 1;
            const dotOp = isCurrent ? pulseOpacity : stepEntry;
            const cx = startX + stepSpacingH * i;

            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: cx,
                  top: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: Math.round(height * 0.012),
                  opacity: stepEntry,
                  width: Math.max(dotDiameter, Math.round(safe.width / count) - 4),
                  transform: `translateX(-${dotR}px)`,
                }}
              >
                {/* Dot */}
                <div
                  style={{
                    width: dotDiameter,
                    height: dotDiameter,
                    borderRadius: '50%',
                    backgroundColor: dotBg,
                    border: `2px solid ${dotBorder}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    transform: `scale(${dotScale})`,
                    opacity: dotOp,
                    zIndex: 2,
                  }}
                >
                  {isDone && (
                    <span
                      style={{
                        fontFamily: fonts.display,
                        fontSize: Math.round(dotR * 0.9),
                        fontWeight: 900,
                        color: theme.bg,
                      }}
                    >
                      ✓
                    </span>
                  )}
                  {isCurrent && (
                    <div
                      style={{
                        width: Math.round(dotR * 0.55),
                        height: Math.round(dotR * 0.55),
                        borderRadius: '50%',
                        backgroundColor: theme.bg,
                      }}
                    />
                  )}
                </div>
                {/* Label */}
                <div
                  style={{
                    fontFamily: fonts.display,
                    fontSize: Math.round(labelFontSize * 0.85),
                    fontWeight: isCurrent ? 800 : 600,
                    color: labelColor,
                    textAlign: 'center',
                    overflowWrap: 'break-word',
                    wordBreak: 'break-word',
                    maxWidth: '100%',
                  }}
                >
                  {step.label}
                </div>
                {step.description && (
                  <div
                    style={{
                      fontFamily: fonts.body,
                      fontSize: Math.round(descFontSize * 0.85),
                      color: theme.muted,
                      textAlign: 'center',
                      overflowWrap: 'break-word',
                      wordBreak: 'break-word',
                      maxWidth: '100%',
                    }}
                  >
                    {step.description}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

/* ======================================================================
   3. DefinitionCard
   ======================================================================
   term       — the term/word to define (large)
   definition — the definition text (revealed word-by-word)
   example    — optional code/usage example in monospace
   source     — optional citation/source
   ====================================================================== */

type DefinitionProps = BaseSceneProps & {
  term?: string;
  definition?: string;
  example?: string;
  source?: string;
};

// How many definition characters to reveal per frame
const CHARS_PER_FRAME = 3;

/**
 * DefinitionCard — term + animated definition reveal.
 *
 * Layout:
 *   left accent bar | term (large) | definition reveals progressively
 *                   | optional usage example in mono | optional source
 *
 * The definition reveal uses a character-count approach: each frame
 * reveals more characters, creating a typewriter effect without per-word
 * splitting. The reveal rate is scaled to cover the full text by 80% of
 * durationInFrames so there is always a "reading" pause at the end.
 *
 * Reads: term, definition, example, source.
 */
export const DefinitionCard: React.FC<BaseSceneProps> = (props) => {
  const { term, definition, example, source } = props as DefinitionProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'reveal');

  const t = term ?? 'Рекурсия';
  const def =
    definition ??
    'Рекурсия — это техника программирования, при которой функция вызывает саму себя для решения подзадачи меньшего размера, пока не будет достигнуто базовое условие.';
  const ex = example ?? 'function factorial(n) {\n  if (n <= 1) return 1;\n  return n * factorial(n - 1);\n}';
  const src = source ?? undefined;

  // Accent bar animation
  const barEntry = animate(frame, 0, 1);
  const barH = safe.height * barEntry;

  // Term slide-in
  const termDelay = Math.round(fps * 0.15);
  const termOpacity = clamp01(animate(frame - termDelay, 0, 1));
  const termY = (1 - termOpacity) * 28;

  // Definition reveal — character by character
  const defDelay = Math.round(fps * 0.4);
  const revealFrames = Math.round(durationInFrames * 0.75) - defDelay;
  const defProgress = clamp01((frame - defDelay) / Math.max(1, revealFrames));
  const revealedChars = Math.round(defProgress * def.length);
  const visibleDef = def.slice(0, revealedChars);

  // Example fade in after definition is mostly visible
  const exDelay = defDelay + revealFrames * 0.85;
  const exOpacity = clamp01(animate(frame - exDelay, 0, 1));

  // Source fade
  const srcDelay = exDelay + Math.round(fps * 0.3);
  const srcOpacity = clamp01(animate(frame - srcDelay, 0, 1));

  // Sizes.
  //
  // The text column is what remains after the accent bar and its gap — sizing
  // against the full safe width overflows by exactly that much.
  const barWidth = Math.round(width * 0.012);
  const barGap = Math.round(width * 0.04);
  const textW = safe.width - barWidth - barGap;

  // TERM: MEASURED, not a character-count ladder.
  //
  // This was `min(height*0.065, (safe.width*0.88 / t.length) * 1.5 + 8)`, the
  // exact ladder theme/layout.ts exists to replace. For "Квантизация" it picked
  // 118px, and 11 Cyrillic glyphs at weight 900 need ~1090px — so the term ran
  // to x=1079 and lost its last letter off the frame edge, rendering
  // "Квантизаци". Cyrillic is wider per character than the Latin the ladder was
  // tuned on, which is precisely the case a proxy cannot see.
  //
  // Two lines are allowed: a long compound term ("Дистилляция знаний") would
  // otherwise shrink to nothing to stay on one.
  const termFit = fitWrapped({
    text: t,
    maxWidth: textW,
    maxHeight: Math.round(safe.height * 0.22),
    fontFamily: fonts.display,
    fontWeight: 900,
    maxLines: 2,
    lineHeight: 1.1,
    maxFontSize: Math.round(height * 0.065),
    minFontSize: Math.round(height * 0.03),
  });
  const termFontSize = termFit.fontSize;

  // Underline spans the term's REAL width, capped at the column. The old
  // `t.length * fontSize * 0.55` guess drifted with the script and stopped
  // halfway under the word.
  const termLineW = Math.min(
    textW,
    Math.ceil(
      Math.max(
        ...(termFit.lines.length ? termFit.lines : [t]).map(
          (line) =>
            measure({
              text: line,
              fontFamily: fonts.display,
              fontSize: termFontSize,
              fontWeight: 900,
              letterSpacing: '-0.02em',
            }).width
        )
      )
    )
  );

  const defFontSize = Math.round(height * 0.026);

  // EXAMPLE: sized so its widest line fits the box.
  //
  // `whiteSpace: 'pre'` is required — the default example is real multi-line
  // code and collapsing its newlines would scramble it — but 'pre' also
  // suppresses wrapping, so `wordBreak: 'break-all'` next to it was dead code.
  // A one-line prose example ("Llama-4-Scout-109B в Q4 влезает в одну RTX 4090")
  // therefore pushed straight through the box border and off the canvas, cut
  // after "RT". Measuring the longest line keeps 'pre' and still fits.
  const exPad = Math.round(height * 0.018);
  const exInnerW = textW - exPad * 2;
  const exLines = ex ? ex.split('\n') : [];
  const exBase = Math.round(height * 0.021);
  const exWidest = exLines.length
    ? Math.max(
        ...exLines.map(
          (line) =>
            measure({ text: line || ' ', fontFamily: fonts.mono, fontSize: exBase }).width
        )
      )
    : 1;
  const exFontSize = Math.max(
    Math.round(height * 0.012),
    Math.min(exBase, Math.floor((exBase * exInnerW) / Math.max(1, exWidest)))
  );

  const srcFontSize = Math.round(height * 0.018);

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
          flexDirection: 'row',
          alignItems: 'flex-start',
          boxSizing: 'border-box',
        }}
      >
        {/* Left accent bar */}
        <div
          style={{
            width: barWidth,
            height: barH,
            backgroundColor: accent,
            borderRadius: Math.round(barWidth / 2),
            flexShrink: 0,
            alignSelf: 'flex-start',
            marginTop: Math.round(safe.height * 0.12),
          }}
        />

        {/* Content */}
        <div
          style={{
            flex: 1,
            paddingLeft: barGap,
            marginTop: Math.round(safe.height * 0.12),
            display: 'flex',
            flexDirection: 'column',
            gap: Math.round(height * 0.03),
          }}
        >
          {/* Term */}
          <div
            style={{
              opacity: termOpacity,
              transform: `translateY(${termY}px)`,
            }}
          >
            <div
              style={{
                fontFamily: fonts.display,
                fontSize: termFontSize,
                fontWeight: 900,
                color: theme.text,
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
                overflowWrap: 'break-word',
                wordBreak: 'break-word',
              }}
            >
              {t}
            </div>
            {/* Underline accent — spans the term's measured width. */}
            <div
              style={{
                width: termLineW,
                height: Math.round(height * 0.005),
                backgroundColor: accent,
                borderRadius: 4,
                marginTop: Math.round(height * 0.008),
                opacity: termOpacity,
              }}
            />
          </div>

          {/* Definition */}
          <div
            style={{
              fontFamily: fonts.body,
              fontSize: defFontSize,
              fontWeight: 400,
              color: theme.text,
              lineHeight: 1.6,
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
              minHeight: Math.round(defFontSize * 1.6 * 3), // reserve 3 lines
            }}
          >
            {visibleDef}
            {/* Blinking cursor during reveal */}
            {revealedChars < def.length && (
              <span
                style={{
                  display: 'inline-block',
                  width: Math.round(defFontSize * 0.5),
                  height: Math.round(defFontSize * 0.85),
                  backgroundColor: accent,
                  marginLeft: 2,
                  verticalAlign: 'text-bottom',
                  opacity: Math.round(frame / 3) % 2 === 0 ? 1 : 0.1,
                }}
              />
            )}
          </div>

          {/* Example */}
          {ex && (
            <div
              style={{
                opacity: exOpacity,
                transform: `translateY(${(1 - exOpacity) * 16}px)`,
                backgroundColor: `${theme.surface}cc`,
                border: `1.5px solid ${accent}44`,
                borderRadius: Math.round(height * 0.012),
                padding: exPad,
              }}
            >
              <div
                style={{
                  fontFamily: fonts.mono,
                  fontSize: exFontSize,
                  color: accent,
                  lineHeight: 1.65,
                  whiteSpace: 'pre',
                  overflowX: 'hidden',
                  overflowWrap: 'break-word',
                  wordBreak: 'break-all',
                }}
              >
                {ex}
              </div>
            </div>
          )}

          {/* Source */}
          {src && (
            <div
              style={{
                opacity: srcOpacity,
                fontFamily: fonts.body,
                fontSize: srcFontSize,
                color: theme.muted,
                fontStyle: 'italic',
                overflowWrap: 'break-word',
              }}
            >
              — {src}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ======================================================================
   4. TimelineReveal
   ======================================================================
   events[]   — [{date, label, description?}]
   title      — headline
   ====================================================================== */

type TimelineEvent = {
  date: string;
  label: string;
  description?: string;
};

type TimelineProps = BaseSceneProps & {
  events?: TimelineEvent[];
  title?: string;
};

/**
 * TimelineReveal — animated chronology axis.
 *
 * Dots appear sequentially on a vertical axis. For each dot:
 *   1. The dot pops in (scale 0→1).
 *   2. A horizontal connector line draws left→right.
 *   3. The date and label fade in.
 * The last event that has appeared is the "active" one — its label is
 * highlighted with the accent colour.
 *
 * Reads: events[], title.
 */
export const TimelineReveal: React.FC<BaseSceneProps> = (props) => {
  const { events, title } = props as TimelineProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'reveal');

  // Defaults
  const evts: TimelineEvent[] = Array.isArray(events) && events.length >= 2
    ? events
    : [
        { date: '2020', label: 'Начало пути', description: 'Первые шаги в программировании' },
        { date: '2021', label: 'Первый проект', description: 'Запуск собственного приложения' },
        { date: '2022', label: 'Команда', description: 'Работа в технологическом стартапе' },
        { date: '2024', label: 'Масштаб', description: 'Архитектура для миллионов пользователей' },
      ];

  const count = evts.length;

  // Title animation
  const titleOpacity = animate(frame, 0, 1);

  // Each event gets a time window within the scene.
  // Events reveal sequentially: event i starts at i / count * durationInFrames
  const eventWindowFrames = durationInFrames / count;

  // Axis line: central vertical spine
  const axisFontSize = Math.round(height * 0.021);
  const labelFontSize = Math.round(height * 0.026);
  const descFontSize = Math.round(height * 0.019);
  const titleFontSize = Math.round(height * 0.034);
  const dotR = Math.round(height * 0.022);
  const dotDiameter = dotR * 2;
  const connectorLen = Math.round(safe.width * 0.08);
  const lineThickness = Math.round(height * 0.005);

  const contentH = title
    ? safe.height * 0.82
    : safe.height * 0.9;
  const rowH = contentH / Math.max(count, 1);

  // Last revealed event index
  let activeIdx = -1;
  for (let i = 0; i < count; i++) {
    const startFrame = Math.round(i * eventWindowFrames);
    if (frame >= startFrame) activeIdx = i;
  }

  // Axis line draw progress: reaches full height when all events revealed
  const axisDrawProgress = clamp01(
    animate(frame, 0, 1) * ((activeIdx + 1) / count)
  );

  // The axis sits at a fixed X
  const axisX = Math.round(safe.width * 0.24);

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
          boxSizing: 'border-box',
        }}
      >
        {/* Title */}
        {title && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: titleFontSize,
              fontWeight: 800,
              color: theme.text,
              opacity: titleOpacity,
              marginBottom: Math.round(height * 0.03),
              overflowWrap: 'break-word',
            }}
          >
            {title}
          </div>
        )}

        {/* Timeline body */}
        <div
          style={{
            position: 'relative',
            flex: 1,
          }}
        >
          {/* Vertical axis — background */}
          <div
            style={{
              position: 'absolute',
              left: axisX - Math.round(lineThickness / 2),
              top: dotR,
              width: lineThickness,
              height: rowH * count - dotR,
              backgroundColor: `${theme.muted}33`,
              borderRadius: lineThickness,
            }}
          />
          {/* Vertical axis — animated fill */}
          <div
            style={{
              position: 'absolute',
              left: axisX - Math.round(lineThickness / 2),
              top: dotR,
              width: lineThickness,
              height: (rowH * count - dotR) * axisDrawProgress,
              backgroundColor: accent,
              borderRadius: lineThickness,
            }}
          />

          {/* Events */}
          {evts.map((evt, i) => {
            const startFrame = Math.round(i * eventWindowFrames);
            const localFrame = frame - startFrame;
            const isActive = i === activeIdx;
            const isPast = i < activeIdx;
            const appeared = localFrame >= 0;

            if (!appeared) {
              return null;
            }

            // Dot pop-in
            const dotScale = clamp01(animate(localFrame, 0, 1));
            // Connector draw
            const connectorProgress = clamp01(
              interpolate(localFrame, [Math.round(fps * 0.1), Math.round(fps * 0.4)], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              })
            );
            // Text fade
            const textOpacity = clamp01(
              interpolate(localFrame, [Math.round(fps * 0.25), Math.round(fps * 0.55)], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              })
            );

            const dotColor = isActive ? accent : isPast ? `${accent}88` : `${theme.muted}55`;
            const dateColor = isActive ? accent : theme.muted;
            const labelColor = isActive ? theme.text : `${theme.text}99`;
            const top = Math.round(rowH * i);

            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  top,
                  left: 0,
                  right: 0,
                  display: 'flex',
                  alignItems: 'center',
                  height: dotDiameter,
                }}
              >
                {/* Date — left of axis */}
                <div
                  style={{
                    width: axisX - dotR - Math.round(safe.width * 0.03),
                    textAlign: 'right',
                    fontFamily: fonts.display,
                    fontSize: axisFontSize,
                    fontWeight: 700,
                    color: dateColor,
                    opacity: textOpacity,
                    overflowWrap: 'break-word',
                    flexShrink: 0,
                  }}
                >
                  {evt.date}
                </div>

                {/* Dot */}
                <div
                  style={{
                    width: dotDiameter,
                    height: dotDiameter,
                    borderRadius: '50%',
                    backgroundColor: dotColor,
                    border: `2px solid ${isActive ? accent : `${theme.muted}44`}`,
                    transform: `scale(${dotScale})`,
                    flexShrink: 0,
                    zIndex: 2,
                    marginLeft: Math.round(safe.width * 0.03) - dotR,
                  }}
                />

                {/* Connector line */}
                <div
                  style={{
                    width: connectorLen * connectorProgress,
                    height: lineThickness,
                    backgroundColor: isActive ? accent : `${theme.muted}66`,
                    borderRadius: lineThickness,
                    flexShrink: 0,
                    marginLeft: Math.round(safe.width * 0.008),
                  }}
                />

                {/* Label + description */}
                <div
                  style={{
                    marginLeft: Math.round(safe.width * 0.02),
                    opacity: textOpacity,
                    flex: 1,
                  }}
                >
                  <div
                    style={{
                      fontFamily: fonts.display,
                      fontSize: labelFontSize,
                      fontWeight: isActive ? 800 : 600,
                      color: labelColor,
                      overflowWrap: 'break-word',
                      wordBreak: 'break-word',
                      lineHeight: 1.2,
                    }}
                  >
                    {evt.label}
                  </div>
                  {evt.description && isActive && (
                    <div
                      style={{
                        fontFamily: fonts.body,
                        fontSize: descFontSize,
                        color: theme.muted,
                        marginTop: Math.round(height * 0.006),
                        overflowWrap: 'break-word',
                        wordBreak: 'break-word',
                        lineHeight: 1.35,
                      }}
                    >
                      {evt.description}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
