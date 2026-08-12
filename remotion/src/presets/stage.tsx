import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea } from '../lib/safeArea';
import { resolveMotion } from '../lib/motion';
import { useStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';
import { fitOneLine } from '../theme/layout';

/**
 * Stage preset pack — music, gaming, and show scenes.
 *
 * Four live-performance / esports / broadcast presets that share one theme:
 *   something is happening RIGHT NOW and the viewer has to feel it.
 *
 *   LyricLines   — karaoke-style lyric fill; active line highlighted + scaled,
 *                  words fill left-to-right inside the active line.
 *   ScoreHud     — gaming HUD: rolling score, health bar, combo multiplier,
 *                  round timer.
 *   CountdownHero — big 3-2-1-GO: number flies in and out, a ring pulse
 *                   radiates, on the final beat a flash and custom word.
 *   VersusSplit  — split-screen matchup with diagonal divider, VS impact text,
 *                  and sides sliding in from their respective edges.
 *
 * CONVENTIONS (project-wide)
 * --------------------------
 * • Sigs: `export const X: React.FC<BaseSceneProps>` — dispatcher resolves
 *   by name, no default export needed.
 * • Extra data read via local type + `props as T`, because BaseSceneSchema
 *   has .passthrough() so the fields arrive at runtime but are not in the
 *   TypeScript type. Parent will add them to the schema later.
 * • No hardcoded colours except semantic health-bar constants (named below).
 * • All random values seeded with mulberry32. Math.random() is banned:
 *   Remotion renders frames out of order in parallel workers.
 * • All sizes proportional to height/width; no literal pixel values.
 */

/* ─── Shared utilities ──────────────────────────────────────────────────── */

/** Deterministic PRNG — identical to Backdrop.tsx, copied to avoid a dep. */
const mulberry32 = (seed: number) => {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const clamp01 = (v: number) => clamp(v, 0, 1);

/* ─── Semantic colour constants (health bar only) ────────────────────────
 *
 * Project rule: hardcoded colours are forbidden EXCEPT for semantic
 * meanings that the theme cannot express (green = alive, red = danger).
 * These are named constants so the intent is obvious.
 */
/** Full health — universally understood as "good". */
const HEALTH_FULL_COLOR = '#22C55E'; // semantic green
/** Low health — universally understood as "danger". */
const HEALTH_LOW_COLOR = '#EF4444'; // semantic red
/** Health threshold below which the bar turns red. */
const HEALTH_DANGER_THRESHOLD = 0.25;

/* ══════════════════════════════════════════════════════════════════════════
 *  1. LyricLines — karaoke lyric display
 * ══════════════════════════════════════════════════════════════════════════ */

/**
 * LyricLines — karaoke-style lyric scene.
 *
 * Reads: lines[] (string | {text: string, startAt?: number}), title, artist
 *
 * Behaviour per spec:
 *  • Active line is accent-coloured and slightly enlarged.
 *  • Words inside the active line are filled left-to-right (karaoke fill):
 *    each word brightens as time passes through its slot within the line.
 *  • Past lines are dimmed and translated upward.
 *  • Future lines are neutral.
 *
 * Timing: each line occupies an equal slice of `durationInFrames`.
 * If a line supplies `startAt` (0..1 fraction of total duration) it overrides
 * the automatic equal-slice boundary.
 */

type LyricsLine = { text: string; startAt?: number };

type LyricLinesProps = BaseSceneProps & {
  lines?: (LyricsLine | string)[];
  title?: string;
  artist?: string;
};

export const LyricLines: React.FC<BaseSceneProps> = (props) => {
  const { lines, title, artist } = props as LyricLinesProps;
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'opacity');

  // Normalise lines to {text, startAt} objects.
  const rawLines = Array.isArray(lines) && lines.length > 0
    ? lines
    : ['Здесь будет текст', 'Вашей любимой', 'Песни'];

  const normLines: LyricsLine[] = rawLines.map((l, i) => {
    if (typeof l === 'string') {
      return { text: l, startAt: i / rawLines.length };
    }
    return { text: l.text, startAt: l.startAt ?? i / rawLines.length };
  });

  // Determine which line is active based on progress 0..1.
  const progress = frame / durationInFrames; // 0..1 through the whole scene

  // Find the active line index: the last line whose startAt <= progress.
  let activeIdx = normLines.length - 1;
  for (let i = 0; i < normLines.length; i++) {
    const nextStart = normLines[i + 1]?.startAt ?? 1;
    if (progress < nextStart) {
      activeIdx = i;
      break;
    }
  }

  // Progress within the active line (0..1).
  const lineStart = normLines[activeIdx].startAt ?? activeIdx / normLines.length;
  const lineEnd = normLines[activeIdx + 1]?.startAt ?? 1;
  const lineWidth = Math.max(lineEnd - lineStart, 0.01);
  const lineProgress = clamp01((progress - lineStart) / lineWidth);

  // Layout sizes — proportional to canvas height.
  const lineFontBase = Math.round(height * 0.048);
  const activeFontSize = Math.round(lineFontBase * 1.18);
  const artistFontSize = Math.round(height * 0.025);
  const titleFontSize = Math.round(height * 0.022);

  // Entrance opacity for the whole block.
  const blockOpacity = animate(frame, 0, 1);

  // How far past lines slide up (a share of one line height).
  const lineH = activeFontSize * 1.8;

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
          opacity: blockOpacity,
          gap: Math.round(height * 0.01),
          boxSizing: 'border-box',
          overflow: 'hidden',
        }}
      >
        {/* Song metadata at the top */}
        {(title || artist) && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              marginBottom: Math.round(height * 0.025),
            }}
          >
            {title && (
              <div
                style={{
                  fontFamily: fonts.display,
                  fontSize: titleFontSize,
                  fontWeight: 800,
                  color: accent,
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                  textAlign: 'center',
                }}
              >
                {title}
              </div>
            )}
            {artist && (
              <div
                style={{
                  fontFamily: fonts.body,
                  fontSize: artistFontSize,
                  color: theme.muted,
                  fontWeight: 500,
                  textAlign: 'center',
                  marginTop: Math.round(height * 0.006),
                }}
              >
                {artist}
              </div>
            )}
          </div>
        )}

        {/* Lyric lines */}
        {/*
          CLIPPED SCROLL WINDOW — do not remove `overflow: hidden`.
          Past lines translate up by `-lineH * 1.1 * n` with no bound. In a flex
          column that transform is not clipped by the parent's layout box, so by
          the third line the text had travelled far enough to paint over the
          title/artist header — two strings rendered on top of each other. A
          fixed-height window with hidden overflow makes the lines scroll behind
          their own edge instead of over the header.
        */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: Math.round(height * 0.012),
            width: '100%',
            height: lineH * 3.2,
            overflow: 'hidden',
            justifyContent: 'center',
          }}
        >
          {normLines.map((line, i) => {
            const isPast = i < activeIdx;
            const isActive = i === activeIdx;
            const isFuture = i > activeIdx;

            // Past lines slide up and fade.
            const pastShift = isPast ? -lineH * 1.1 * (activeIdx - i) : 0;
            const opacity = isPast ? 0.28 : isFuture ? 0.45 : 1;
            const fontSize = isActive ? activeFontSize : lineFontBase;

            // Karaoke word-fill for the active line.
            const words = line.text.split(' ');
            const nWords = words.length;

            return (
              <div
                key={i}
                style={{
                  transform: `translateY(${pastShift}px)`,
                  opacity,
                  transition: 'none',
                  fontSize,
                  fontFamily: fonts.display,
                  fontWeight: isActive ? 800 : 500,
                  textAlign: 'center',
                  width: safe.width,
                  overflowWrap: 'break-word',
                  lineHeight: 1.35,
                  display: 'flex',
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                  gap: `0 ${Math.round(fontSize * 0.28)}px`,
                }}
              >
                {isActive
                  ? // Word-by-word fill for active line.
                    words.map((word, wi) => {
                      // Each word occupies an equal fraction of lineProgress.
                      const wordStart = wi / nWords;
                      const wordEnd = (wi + 1) / nWords;
                      // A word is "filled" when lineProgress has passed its midpoint.
                      // For a smoother look, fill fades over the word's own slot.
                      const wordFill = clamp01((lineProgress - wordStart) / Math.max(wordEnd - wordStart, 0.01));
                      const wordColor = wordFill > 0.5 ? accent : theme.muted;
                      const wordOpacity = 0.45 + wordFill * 0.55;
                      return (
                        <span
                          key={wi}
                          style={{
                            color: wordColor,
                            opacity: wordOpacity,
                            fontWeight: 800,
                            // Slight scale-up as a word becomes active.
                            transform: `scale(${1 + wordFill * 0.06})`,
                            display: 'inline-block',
                            transformOrigin: 'center bottom',
                          }}
                        >
                          {word}
                        </span>
                      );
                    })
                  : // Past / future lines — plain text.
                    line.text}
              </div>
            );
          })}
        </div>

        {/* Progress pip row: one pip per line */}
        <div
          style={{
            display: 'flex',
            gap: Math.round(height * 0.008),
            marginTop: Math.round(height * 0.03),
          }}
        >
          {normLines.map((_, i) => (
            <div
              key={i}
              style={{
                width: i === activeIdx ? Math.round(height * 0.028) : Math.round(height * 0.01),
                height: Math.round(height * 0.01),
                borderRadius: Math.round(height * 0.005),
                background: i === activeIdx ? accent : theme.muted,
                opacity: i < activeIdx ? 0.4 : 1,
                transition: 'none',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

/* ══════════════════════════════════════════════════════════════════════════
 *  2. ScoreHud — gaming HUD overlay
 * ══════════════════════════════════════════════════════════════════════════ */

/**
 * ScoreHud — gaming heads-up display.
 *
 * Reads: score, health (0..100), combo, timeLeft, playerName
 *
 * • Score rolls up from 0 to `score` across the scene.
 * • Health bar shrinks left-to-right; colour shifts green → red at 25%.
 * • Combo multiplier pulses (scale bounce) whenever it's a value > 1.
 * • Round timer counts down from `timeLeft` to 0.
 */

type ScoreHudProps = BaseSceneProps & {
  score?: number;
  health?: number;
  combo?: number;
  timeLeft?: number;
  playerName?: string;
};

export const ScoreHud: React.FC<BaseSceneProps> = (props) => {
  const { score = 9750, health = 100, combo = 3, timeLeft = 60, playerName = 'PLAYER 1' } =
    props as ScoreHudProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'value');

  const sceneProgress = clamp01(frame / durationInFrames);

  // Score rolls from 0 → score over the scene.
  const displayScore = Math.round(animate(frame, 0, score));

  // Health 0..100 → 0..1 (health bar fill).
  const healthFraction = clamp01(health / 100);
  // Health bar colour: green at full, red when low.
  const isDangerous = healthFraction <= HEALTH_DANGER_THRESHOLD;
  const healthColor = isDangerous ? HEALTH_LOW_COLOR : HEALTH_FULL_COLOR;
  // Bar shrinks as scene progresses (simulates taking damage to final health).
  const animatedHealth = clamp01(animate(frame, 1, healthFraction));

  // Combo pulse: when combo > 1 a sinusoidal scale pulse runs at 2 Hz.
  const comboPulse =
    combo > 1
      ? 1 + 0.12 * Math.sin((frame / fps) * 2 * Math.PI * 2)
      : 1;

  // Timer counts from timeLeft down toward 0 across durationInFrames.
  const displayTime = Math.max(0, Math.round(timeLeft * (1 - sceneProgress)));

  // Layout sizes.
  const scoreFontSize = Math.round(height * 0.088);
  const labelFontSize = Math.round(height * 0.022);
  const comboFontSize = Math.round(height * 0.064);
  const timerFontSize = Math.round(height * 0.048);
  const barH = Math.round(height * 0.022);
  const barW = safe.width;

  const blockOpacity = animate(frame, 0, 1);

  // Seeded sparks for combo > 1 (deterministic particles).
  const rng = mulberry32(combo * 31 + frame);
  const sparkCount = combo > 1 ? 6 : 0;
  const sparks = Array.from({ length: sparkCount }, (_, si) => ({
    x: rng() * 100,
    y: rng() * 40 + 30,
    r: rng() * 4 + 2,
    opacity: rng() * 0.7 + 0.2,
  }));

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
          justifyContent: 'space-between',
          opacity: blockOpacity,
          boxSizing: 'border-box',
          paddingTop: Math.round(height * 0.02),
          paddingBottom: Math.round(height * 0.02),
        }}
      >
        {/* Top row: player name + timer */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              fontFamily: fonts.mono,
              fontSize: labelFontSize,
              color: theme.muted,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
            }}
          >
            {playerName}
          </div>
          {/* Round timer */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-end',
              gap: Math.round(height * 0.004),
            }}
          >
            <div
              style={{
                fontFamily: fonts.mono,
                fontSize: labelFontSize * 0.85,
                color: theme.muted,
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              РАУНД
            </div>
            <div
              style={{
                fontFamily: fonts.mono,
                fontSize: timerFontSize,
                fontWeight: 900,
                fontVariantNumeric: 'tabular-nums',
                color: displayTime <= 10 ? HEALTH_LOW_COLOR : theme.text,
              }}
            >
              {String(displayTime).padStart(2, '0')}
            </div>
          </div>
        </div>

        {/* Central score */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: Math.round(height * 0.008),
          }}
        >
          <div
            style={{
              fontFamily: fonts.mono,
              fontSize: labelFontSize,
              color: theme.muted,
              fontWeight: 600,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
            }}
          >
            СЧЁТ
          </div>
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: scoreFontSize,
              fontWeight: 900,
              color: accent,
              fontVariantNumeric: 'tabular-nums',
              textShadow: `0 0 ${Math.round(scoreFontSize * 0.5)}px ${accent}66`,
              letterSpacing: '-0.02em',
            }}
          >
            {displayScore.toLocaleString('ru-RU')}
          </div>
        </div>

        {/* Health bar */}
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: Math.round(height * 0.008) }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontFamily: fonts.mono,
              fontSize: labelFontSize * 0.85,
              color: theme.muted,
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
            }}
          >
            <span>ЗДОРОВЬЕ</span>
            <span style={{ color: healthColor }}>{Math.round(animatedHealth * 100)}%</span>
          </div>
          {/* Track */}
          <div
            style={{
              width: barW,
              height: barH,
              backgroundColor: `${theme.surface}cc`,
              borderRadius: barH / 2,
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            {/* Fill */}
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                width: `${animatedHealth * 100}%`,
                height: '100%',
                background: `linear-gradient(90deg, ${healthColor}cc, ${healthColor})`,
                borderRadius: barH / 2,
                boxShadow: `0 0 ${barH}px ${healthColor}88`,
                transition: 'none',
              }}
            />
          </div>
        </div>

        {/* Combo multiplier */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative',
          }}
        >
          {/* Deterministic sparkles behind combo when active */}
          {sparks.map((sp, si) => (
            <div
              key={si}
              style={{
                position: 'absolute',
                left: `${sp.x}%`,
                top: `${sp.y}%`,
                width: Math.round(sp.r),
                height: Math.round(sp.r),
                borderRadius: '50%',
                background: accent,
                opacity: sp.opacity,
                pointerEvents: 'none',
              }}
            />
          ))}
          <div
            style={{
              fontFamily: fonts.mono,
              fontSize: labelFontSize * 0.85,
              color: theme.muted,
              fontWeight: 600,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
            }}
          >
            КОМБО
          </div>
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: comboFontSize,
              fontWeight: 900,
              color: combo > 1 ? accent : theme.muted,
              transform: `scale(${comboPulse})`,
              textShadow: combo > 1 ? `0 0 ${Math.round(comboFontSize * 0.4)}px ${accent}99` : 'none',
              letterSpacing: '-0.01em',
              lineHeight: 1,
            }}
          >
            ×{combo}
          </div>
        </div>
      </div>
    </div>
  );
};

/* ══════════════════════════════════════════════════════════════════════════
 *  3. CountdownHero — 3-2-1-GO big countdown
 * ══════════════════════════════════════════════════════════════════════════ */

/**
 * CountdownHero — broadcast-style countdown.
 *
 * Reads: from (number, default 3), finalWord, subtitle
 *
 * Timing: scene duration is divided into (from + 1) equal beats:
 *   beats 0..from-1 → digits from..1
 *   beat  from      → finalWord / subtitle
 *
 * Per-beat animation:
 *   • Digit enters from scale(2) → scale(1) with easeOut, exits scale(0.5).
 *   • A ring expands from the centre and fades (impulse).
 *   • On the final beat: full-screen flash fades, finalWord appears.
 */

type CountdownHeroProps = BaseSceneProps & {
  from?: number;
  finalWord?: string;
  subtitle?: string;
};

export const CountdownHero: React.FC<BaseSceneProps> = (props) => {
  const { from: fromProp = 3, finalWord = 'СТАРТ', subtitle } = props as CountdownHeroProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'opacity');

  // Clamp from to a sensible range.
  const totalBeats = Math.max(1, Math.round(fromProp)) + 1; // digits + 1 final beat
  const beatFrames = durationInFrames / totalBeats;

  // Which beat we're in (0-indexed; last beat = final word).
  const beatIndex = Math.min(Math.floor(frame / beatFrames), totalBeats - 1);
  const beatFrame = frame - beatIndex * beatFrames; // frame within the beat
  const beatProgress = clamp01(beatFrame / beatFrames);

  const isFinal = beatIndex === totalBeats - 1;
  // Digit for this beat: beat 0 → fromProp, beat 1 → fromProp-1, ...
  const digit = isFinal ? null : fromProp - beatIndex;

  // Digit scale: flies in from large → normal → shrinks out.
  //
  // THE EXIT MUST LAND EXACTLY ON THE BEAT BOUNDARY.
  // With `exitStart = 0.55 * beat` and `exitDur = 0.35 * beat` the fade
  // finished at 0.90 of the beat, so the last ~10% of every beat rendered a
  // fully transparent digit — a measured 2.5-frame black gap between "3" and
  // "2" on a 90-frame scene. Deriving exitDur from the remaining time makes the
  // outgoing digit hand over to the next one with no hole.
  const enterDur = Math.round(beatFrames * 0.38);
  const exitStart = Math.round(beatFrames * 0.55);
  const exitDur = Math.max(1, beatFrames - exitStart);

  const enterScale = beatFrame < enterDur
    ? interpolate(beatFrame, [0, enterDur], [2.2, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 1;
  const exitScale = beatFrame > exitStart
    ? interpolate(beatFrame - exitStart, [0, exitDur], [1, 0.45], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 1;
  const digitScale = enterScale * exitScale;

  const digitOpacity = beatFrame < enterDur
    ? interpolate(beatFrame, [0, enterDur * 0.5], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : beatFrame > exitStart
    ? interpolate(beatFrame - exitStart, [0, exitDur], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 1;

  // Ring pulse: expands from 0 → 160% width and fades.
  const ringDur = Math.round(beatFrames * 0.65);
  const ringScale = interpolate(clamp01(beatFrame / ringDur), [0, 1], [0, 3.2], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const ringOpacity = interpolate(clamp01(beatFrame / ringDur), [0, 0.15, 1], [0, 0.7, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Flash on final beat: bright overlay that fades quickly.
  const flashOpacity = isFinal
    ? interpolate(beatFrame, [0, Math.round(fps * 0.15), Math.round(fps * 0.45)], [0.9, 0.5, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  // Final word entrance.
  const finalEnterDur = Math.round(beatFrames * 0.35);
  const finalScale = isFinal
    ? interpolate(beatFrame, [0, finalEnterDur], [0.6, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 1;
  const finalOpacity = isFinal
    ? interpolate(beatFrame, [0, finalEnterDur], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 0;

  // Subtitle entrance follows the final word with a small delay.
  const subEnterDelay = Math.round(finalEnterDur * 0.6);
  const subEnterDur = Math.round(beatFrames * 0.3);
  const subOpacity = isFinal
    ? interpolate(
        beatFrame - subEnterDelay,
        [0, subEnterDur],
        [0, 1],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      )
    : 0;

  // Sizes.
  const numFontSize = Math.round(height * 0.22);
  const labelFontSize = Math.round(height * 0.032);
  // MEASURE THE FINAL WORD, DON'T ASSUME IT FITS.
  // A flat `height * 0.14` (269px at 1920) only fits ~6 wide glyphs across the
  // safe area. "ДОГНАЛИ" (7 caps) rendered 1080px wide in a 1080px frame: the
  // leading Д and trailing И were sliced off by the viewport, so the hero beat
  // of the scene read "ОГНАЛ". Any word longer than ~6 characters hit this, and
  // because the middle of the word still looked correct the frame passed a
  // glance. Measure against the safe width and only ever shrink.
  const finalFontSize = Math.min(
    Math.round(height * 0.14),
    fitOneLine({
      text: finalWord,
      maxWidth: safe.width,
      fontFamily: fonts.display,
      fontWeight: 900,
      maxFontSize: Math.round(height * 0.14),
      minFontSize: Math.round(height * 0.05),
    })
  );
  const ringBase = Math.round(Math.min(width, height) * 0.36);

  // Global entrance for the whole composition.
  const globalOpacity = animate(frame, 0, 1);

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: theme.bg, overflow: 'hidden' }}>
      <Backdrop />

      {/* Flash overlay */}
      {flashOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: accent,
            opacity: flashOpacity,
            pointerEvents: 'none',
          }}
        />
      )}

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
          opacity: globalOpacity,
        }}
      >
        {/* Ring impulse — centred in the safe area */}
        <div
          style={{
            position: 'absolute',
            width: ringBase,
            height: ringBase,
            borderRadius: '50%',
            border: `${Math.round(height * 0.008)}px solid ${accent}`,
            opacity: ringOpacity,
            transform: `scale(${ringScale})`,
            pointerEvents: 'none',
          }}
        />

        {/* Countdown digit or final word */}
        {!isFinal && digit !== null && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: numFontSize,
              fontWeight: 900,
              color: accent,
              lineHeight: 1,
              transform: `scale(${digitScale})`,
              opacity: digitOpacity,
              textShadow: `0 0 ${Math.round(numFontSize * 0.4)}px ${accent}88`,
              fontVariantNumeric: 'tabular-nums',
              userSelect: 'none',
            }}
          >
            {digit}
          </div>
        )}

        {isFinal && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: Math.round(height * 0.016),
              opacity: finalOpacity,
              transform: `scale(${finalScale})`,
            }}
          >
            <div
              style={{
                fontFamily: fonts.display,
                fontSize: finalFontSize,
                fontWeight: 900,
                color: accent,
                lineHeight: 1,
                textShadow: `0 0 ${Math.round(finalFontSize * 0.35)}px ${accent}99`,
                textAlign: 'center',
                overflowWrap: 'break-word',
              }}
            >
              {finalWord}
            </div>
            {subtitle && (
              <div
                style={{
                  fontFamily: fonts.body,
                  fontSize: labelFontSize,
                  color: theme.muted,
                  fontWeight: 600,
                  textAlign: 'center',
                  opacity: subOpacity,
                  overflowWrap: 'break-word',
                }}
              >
                {subtitle}
              </div>
            )}
          </div>
        )}

        {/* Beat count-below hint */}
        {!isFinal && (
          <div
            style={{
              position: 'absolute',
              bottom: Math.round(safe.height * 0.08),
              display: 'flex',
              gap: Math.round(height * 0.012),
            }}
          >
            {Array.from({ length: totalBeats - 1 }, (_, i) => (
              <div
                key={i}
                style={{
                  width: Math.round(height * 0.012),
                  height: Math.round(height * 0.012),
                  borderRadius: '50%',
                  background: i < beatIndex ? theme.muted : i === beatIndex ? accent : `${accent}44`,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/* ══════════════════════════════════════════════════════════════════════════
 *  4. VersusSplit — versus/matchup screen
 * ══════════════════════════════════════════════════════════════════════════ */

/**
 * VersusSplit — split-screen matchup / battle card.
 *
 * Reads:
 *   left  { name, value?, avatar? }   — left competitor
 *   right { name, value?, avatar? }   — right competitor
 *   vsLabel                           — centre text (default "VS")
 *
 * Layout:
 *   • Two diagonal halves of the screen; each half slides in from its edge.
 *   • Left half slides in from the left, right from the right.
 *   • Divider is a diagonal line (CSS clip-path).
 *   • "VS" label flies in from scale(3) with a bounce (impact).
 *   • All content (names, values, avatars) clipped to their safe column.
 *   • Background colours: left = neon tint, right = cyan tint (theme-derived).
 */

type CompetitorSlot = { name?: string; value?: string; avatar?: string };

type VersusSplitProps = BaseSceneProps & {
  left?: CompetitorSlot;
  right?: CompetitorSlot;
  vsLabel?: string;
};

export const VersusSplit: React.FC<BaseSceneProps> = (props) => {
  const {
    left: leftData = { name: 'КОМАНДА А' },
    right: rightData = { name: 'КОМАНДА Б' },
    vsLabel = 'VS',
  } = props as VersusSplitProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'opacity');

  // Each panel slides in from its respective edge.
  const slideDur = Math.round(fps * 0.45);
  const leftSlide = interpolate(frame, [0, slideDur], [-width, 0], {
    easing: (t) => 1 - Math.pow(1 - t, 3), // easeOutCubic
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const rightSlide = interpolate(frame, [0, slideDur], [width, 0], {
    easing: (t) => 1 - Math.pow(1 - t, 3),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // VS impact: large scale shrinks to 1 over a short duration, bounce.
  const vsDelay = Math.round(slideDur * 0.6);
  const vsDur = Math.round(fps * 0.3);
  const vsScale = interpolate(
    clamp01((frame - vsDelay) / vsDur),
    [0, 0.55, 0.8, 1],
    [3.5, 0.85, 1.08, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
  const vsOpacity = interpolate(frame - vsDelay, [0, vsDur * 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Content opacity inside each panel — appears slightly after the slide.
  const contentDelay = Math.round(slideDur * 0.55);
  const contentDur = Math.round(fps * 0.35);
  const contentOpacity = interpolate(frame, [contentDelay, contentDelay + contentDur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Sizes.
  //
  // NAME FONT MUST BE MEASURED AGAINST THE COLUMN, NOT THE SAFE AREA.
  // The first version divided `safe.width * 0.44 * 1.8` by the longest name,
  // which is ~1.8x more room than the column actually has (the column is
  // `safe.width * 0.43`). "Llama4" came out at 111px in a 395px column, wrapped
  // to "Llam/a4", and collided with the VS label. Budget the real column width
  // and assume ~0.62em per glyph for a 900-weight display face.
  const colWidth = safe.width * 0.43;
  const longestName = Math.max(leftData.name?.length ?? 6, rightData.name?.length ?? 6, 4);
  const nameFontSize = Math.round(
    Math.min(height * 0.05, colWidth / (longestName * 0.62))
  );
  const valueFontSize = Math.round(height * 0.038);
  const vsFontSize = Math.round(height * 0.09);
  const avatarSize = Math.round(height * 0.12);

  // VERTICAL OFFSETS KEEP THE COLUMNS OUT OF THE VS LABEL.
  // Both columns used `justifyContent: 'center'` over the full safe height, so
  // their names landed on the exact centre line where the VS impact text sits —
  // three elements stacked in one spot. Pushing the left column above centre
  // and the right below it also reads better with the diagonal clip.
  const columnShift = Math.round(safe.height * 0.17);

  // Left panel occupies the left ~50%, clipped diagonally.
  // Right panel the right ~50%, clipped diagonally.
  // The diagonal offset in px — the clip goes from top-right to bottom-left of centre.
  const diagOffset = Math.round(width * 0.04);

  // Left panel clip: polygon covering left half + diagonal slant to the right.
  const leftClip = `polygon(0 0, calc(50% + ${diagOffset}px) 0, calc(50% - ${diagOffset}px) 100%, 0 100%)`;
  const rightClip = `polygon(calc(50% + ${diagOffset}px) 0, 100% 0, 100% 100%, calc(50% - ${diagOffset}px) 100%)`;

  // Theme-derived tint colours for each half (no hardcode).
  const leftTint = `${theme.neon}1A`; // 10% neon
  const rightTint = `${theme.cyan}1A`; // 10% cyan

  // Avatar placeholder (initials) when no avatar URL is provided.
  const Initials = ({ name, color }: { name?: string; color: string }) => (
    <div
      style={{
        width: avatarSize,
        height: avatarSize,
        borderRadius: '50%',
        background: `${color}33`,
        border: `${Math.round(avatarSize * 0.05)}px solid ${color}66`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: fonts.display,
        fontSize: Math.round(avatarSize * 0.38),
        fontWeight: 900,
        color,
      }}
    >
      {(name ?? '?').charAt(0).toUpperCase()}
    </div>
  );

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: theme.bg, overflow: 'hidden' }}>
      <Backdrop />

      {/* ── Left panel ─────────────────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateX(${leftSlide}px)`,
          clipPath: leftClip,
          background: leftTint,
        }}
      />
      {/* Left content — MUST stay inside safe area */}
      <div
        style={{
          position: 'absolute',
          top: safe.top,
          left: safe.left,
          width: colWidth,
          height: safe.height,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          // Sits above the centre line so the name clears the VS label.
          transform: `translateX(${leftSlide}px) translateY(${-columnShift}px)`,
          opacity: contentOpacity,
          gap: Math.round(height * 0.018),
        }}
      >
        {leftData.avatar ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={leftData.avatar}
            alt={leftData.name ?? ''}
            style={{ width: avatarSize, height: avatarSize, borderRadius: '50%', objectFit: 'cover', border: `${Math.round(avatarSize * 0.05)}px solid ${accent}66` }}
          />
        ) : (
          <Initials name={leftData.name} color={theme.neon} />
        )}
        <div
          style={{
            fontFamily: fonts.display,
            fontSize: nameFontSize,
            fontWeight: 900,
            color: theme.text,
            textAlign: 'center',
            // A competitor name is an identifier, not prose: breaking "Qwen3"
            // into "Qwen"/"3" changes what the viewer reads. Keep it on one
            // line and let the font size (already budgeted from the column
            // width above) do the fitting.
            whiteSpace: 'nowrap',
            maxWidth: '100%',
          }}
        >
          {leftData.name ?? ''}
        </div>
        {leftData.value && (
          <div
            style={{
              fontFamily: fonts.mono,
              fontSize: valueFontSize,
              fontWeight: 700,
              color: theme.neon,
              textAlign: 'center',
            }}
          >
            {leftData.value}
          </div>
        )}
      </div>

      {/* ── Right panel ────────────────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateX(${rightSlide}px)`,
          clipPath: rightClip,
          background: rightTint,
        }}
      />
      {/* Right content */}
      <div
        style={{
          position: 'absolute',
          top: safe.top,
          right: safe.right,
          width: colWidth,
          height: safe.height,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          // Sits below the centre line, mirroring the left column.
          transform: `translateX(${rightSlide}px) translateY(${columnShift}px)`,
          opacity: contentOpacity,
          gap: Math.round(height * 0.018),
        }}
      >
        {rightData.avatar ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={rightData.avatar}
            alt={rightData.name ?? ''}
            style={{ width: avatarSize, height: avatarSize, borderRadius: '50%', objectFit: 'cover', border: `${Math.round(avatarSize * 0.05)}px solid ${theme.cyan}66` }}
          />
        ) : (
          <Initials name={rightData.name} color={theme.cyan} />
        )}
        <div
          style={{
            fontFamily: fonts.display,
            fontSize: nameFontSize,
            fontWeight: 900,
            color: theme.text,
            textAlign: 'center',
            // A competitor name is an identifier, not prose: breaking "Qwen3"
            // into "Qwen"/"3" changes what the viewer reads. Keep it on one
            // line and let the font size (already budgeted from the column
            // width above) do the fitting.
            whiteSpace: 'nowrap',
            maxWidth: '100%',
          }}
        >
          {rightData.name ?? ''}
        </div>
        {rightData.value && (
          <div
            style={{
              fontFamily: fonts.mono,
              fontSize: valueFontSize,
              fontWeight: 700,
              color: theme.cyan,
              textAlign: 'center',
            }}
          >
            {rightData.value}
          </div>
        )}
      </div>

      {/* ── VS label — centre impact ────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width,
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            fontFamily: fonts.display,
            fontSize: vsFontSize,
            fontWeight: 900,
            color: theme.text,
            letterSpacing: '-0.02em',
            textShadow: `0 0 ${Math.round(vsFontSize * 0.6)}px ${accent}bb, 0 ${Math.round(vsFontSize * 0.06)}px ${Math.round(vsFontSize * 0.22)}px rgba(0,0,0,0.7)`,
            transform: `scale(${vsScale})`,
            opacity: vsOpacity,
            userSelect: 'none',
          }}
        >
          {vsLabel ?? 'VS'}
        </div>
      </div>
    </div>
  );
};
