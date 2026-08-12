import React from 'react';
import { Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea } from '../lib/safeArea';
import { resolveMotion } from '../lib/motion';
import { useStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';

/**
 * Device and audio-player presets.
 *
 * PhoneMockup is the structurally interesting one: it renders ANOTHER scene
 * inside a phone body. That is the "модель телефона в котором будет другая
 * сцена на выбор" from the brief.
 *
 * WHY THE NESTED SCENE IS RESOLVED THROUGH A LAZY REGISTRY LOOKUP
 * --------------------------------------------------------------
 * PhoneMockup lives in the preset registry, and the scene it hosts also comes
 * from that registry — so importing the registry at module scope would be a
 * cycle (registry -> device.tsx -> registry). The import is therefore done
 * inside the component body via a function that reads the already-initialised
 * module. This is also why `innerPreset` is validated at render time rather
 * than by the schema: the schema cannot reference the registry either.
 *
 * A nested preset that does not exist renders a readable error INSIDE the phone
 * screen instead of throwing — a thrown error kills the whole render, and one
 * bad nested name should not lose a 20-scene video.
 *
 * RECURSION GUARD
 * ---------------
 * A PhoneMockup whose `innerPreset` is PhoneMockup would recurse until the
 * stack blows. `depth` is threaded through and capped.
 */

const resolveSrc = (s: string): string =>
  s.startsWith('http') || s.startsWith('data:') ? s : staticFile(s);

/* ----------------------------------------------------------- PhoneMockup */

/** Nested-scene resolution, deferred to render time to avoid an import cycle. */
const useNestedPreset = (name?: string): React.FC<BaseSceneProps> | undefined => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires, global-require
  const registry = require('../registry/presets') as {
    PRESETS: Record<string, { component: React.FC<BaseSceneProps> }>;
  };
  if (!name) return undefined;
  return registry.PRESETS[name]?.component;
};

export const PhoneMockup: React.FC<BaseSceneProps> = (props) => {
  const {
    innerPreset,
    innerProps,
    title,
    subtitle,
    device = 'phone',
    tilt,
    depth = 0,
    motion,
    safeArea = 'platform',
    accentColor,
  } = props;

  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const { theme, fonts, accent: styleAccent, motion: character } = useStyle();
  const accent = accentColor || styleAccent;
  const animate = resolveMotion(motion, fps, 'reveal');
  const appear = animate(frame, 0, 1);

  const Nested = useNestedPreset(innerPreset as string | undefined);

  // Phone body sized to the safe box, leaving room for a caption.
  const availH = Math.round(safe.height * (title || subtitle ? 0.78 : 0.94));

  // THE SCREEN MUST MATCH THE CANVAS ASPECT, NOT A REAL PHONE'S.
  // A nested scene lays out against the FULL canvas (useVideoConfig is the
  // composition's, not this wrapper's), so it can only be placed by uniform
  // scale. Uniform scale into a screen of a different aspect leaves slack on one
  // axis, and every way of spending that slack is a visible defect:
  //   * scale by height  -> overflows the sides, silently eating the first and
  //     last character of every line (measured 80px/side: "Разбери код" -> "Разбери к")
  //   * scale by width, centre -> letterbox above AND below the content
  //   * scale by width, bottom-anchor -> one big dead band at the top; on a chat
  //     that read as 26% of the screen being empty black above the header, when
  //     a real Telegram header is pinned to the top edge.
  // Hardcoding 19.5:9 here was the root cause: 9:16 content can never fill it.
  // Deriving the screen from the canvas aspect makes the fit exact, so there is
  // no slack to misplace. The body is then whatever that screen plus bezel needs.
  //
  // Closed form: with bezel = BEZEL_RATIO * bodyW and A = height / width,
  //   bodyH = screenW * A + 2 * bezel = bodyW * ((1 - 2*BEZEL_RATIO) * A + 2*BEZEL_RATIO)
  const BEZEL_RATIO = 0.022;
  const A = height / width;
  const bodyToWidth = (1 - 2 * BEZEL_RATIO) * A + 2 * BEZEL_RATIO;
  let bodyW = Math.min(safe.width, Math.floor(availH / bodyToWidth));
  let bezel = Math.max(6, Math.round(bodyW * BEZEL_RATIO));
  let screenW = bodyW - bezel * 2;
  let screenH = Math.round(screenW * A);
  let bodyH = screenH + bezel * 2;
  // The max(6, ...) floor on bezel can push a very small phone over budget.
  if (bodyH > availH) {
    const shrink = availH / bodyH;
    bodyW = Math.floor(bodyW * shrink);
    bezel = Math.max(6, Math.round(bodyW * BEZEL_RATIO));
    screenW = bodyW - bezel * 2;
    screenH = Math.round(screenW * A);
    bodyH = screenH + bezel * 2;
  }
  const radius = Math.round(bodyW * 0.115);

  // A gentle idle rotation makes the slab feel like an object rather than a
  // rectangle. `tilt: 0` opts out for a flat, editorial framing.
  const idleTilt = typeof tilt === 'number' ? tilt : character.tilt || -2;
  const wobble = Math.sin(frame / 90) * 1.1;

  const inner = Nested ? (
    // The nested scene believes it owns a full canvas, so it is rendered at
    // canvas size and scaled into the screen. Rendering it at screen size
    // instead would make every internal `height * 0.03` font microscopic — the
    // scene would be laid out for a 300px-tall viewport.
    //
    // The screen is derived from the canvas aspect above, so `screenW / width`
    // and `screenH / height` are the same ratio: the fit is exact on both axes.
    // There is no slack left to letterbox or to overflow, which is what used to
    // either clip the first/last character of every line (scale-by-height) or
    // leave a dead band above the chat header (scale-by-width, bottom-anchored).
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width,
        height,
        transform: `scale(${screenW / width})`,
        transformOrigin: 'top left',
      }}
    >
      <Nested
        {...({
          ...(typeof innerProps === 'object' && innerProps ? innerProps : {}),
          preset: innerPreset,
          id: `${props.id}-inner`,
          durationInFrames: props.durationInFrames,
          // Inside a phone the platform safe area is wrong: the phone screen IS
          // the frame, so the nested scene uses tight insets.
          safeArea: 'loose',
          accentColor: accent,
          depth: (depth as number) + 1,
        } as unknown as BaseSceneProps)}
      />
    </div>
  ) : (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#2A0B0B',
        color: '#FFF',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: 24,
        fontFamily: 'ui-monospace, monospace',
        fontSize: Math.round(screenW * 0.055),
        lineHeight: 1.3,
      }}
    >
      {innerPreset
        ? `⚠ UNKNOWN innerPreset\n"${innerPreset}"`
        : '⚠ NO innerPreset IN SPEC'}
    </div>
  );

  // Depth cap: a phone inside a phone inside a phone is a bug, not a feature.
  const tooDeep = (depth as number) >= 2;

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
          gap: Math.round(height * 0.024),
          boxSizing: 'border-box',
        }}
      >
        <div
          style={{
            width: bodyW,
            height: bodyH,
            borderRadius: radius,
            backgroundColor: '#08090B',
            border: `${bezel * 0.5}px solid #1C1F26`,
            boxSizing: 'border-box',
            padding: bezel,
            position: 'relative',
            opacity: appear,
            transform: `perspective(1800px) rotateY(${idleTilt + wobble}deg) rotateX(${
              (1 - appear) * 8
            }deg) translateY(${(1 - appear) * 40}px) scale(${0.94 + appear * 0.06})`,
            boxShadow: `0 40px 90px rgba(0,0,0,0.6), 0 0 0 1px ${accent}22`,
          }}
        >
          {/* screen */}
          <div
            style={{
              width: screenW,
              height: screenH,
              borderRadius: radius * 0.82,
              overflow: 'hidden',
              position: 'relative',
              backgroundColor: '#000',
            }}
          >
            {tooDeep ? (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  fontFamily: 'ui-monospace, monospace',
                  fontSize: Math.round(screenW * 0.05),
                  textAlign: 'center',
                  padding: 20,
                }}
              >
                ⚠ nesting depth limit
              </div>
            ) : (
              inner
            )}

            {/* screen glare — one soft diagonal band, the thing that reads as glass */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background:
                  'linear-gradient(118deg, rgba(255,255,255,0.13) 0%, rgba(255,255,255,0) 34%, rgba(255,255,255,0) 68%, rgba(255,255,255,0.05) 100%)',
                pointerEvents: 'none',
              }}
            />
          </div>

          {/* dynamic-island style cutout */}
          {device !== 'tablet' && (
            <div
              style={{
                position: 'absolute',
                top: bezel * 1.6,
                left: '50%',
                transform: 'translateX(-50%)',
                width: bodyW * 0.26,
                height: bodyW * 0.075,
                borderRadius: 999,
                backgroundColor: '#000',
                zIndex: 5,
              }}
            />
          )}
        </div>

        {(title || subtitle) && (
          <div style={{ textAlign: 'center', opacity: appear }}>
            {title && (
              <div
                style={{
                  fontFamily: fonts.display,
                  fontSize: Math.round(height * 0.031),
                  fontWeight: 800,
                  color: theme.text,
                }}
              >
                {title}
              </div>
            )}
            {subtitle && (
              <div
                style={{
                  fontFamily: fonts.body,
                  fontSize: Math.round(height * 0.019),
                  color: accent,
                  marginTop: 6,
                  fontWeight: 600,
                }}
              >
                {subtitle}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

/* ----------------------------------------------------------- MusicPlayer */

/**
 * MusicPlayer — a now-playing card with cover art, a scrubber and equaliser bars.
 *
 * Reads: trackTitle/title, artist/subtitle, cover, duration, bars
 */
export const MusicPlayer: React.FC<BaseSceneProps> = ({
  title,
  trackTitle,
  subtitle,
  artist,
  cover,
  duration,
  motion,
  safeArea = 'platform',
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const { theme, fonts, accent: styleAccent, surface } = useStyle();
  const accent = accentColor || styleAccent;
  const animate = resolveMotion(motion, fps, 'reveal');
  const appear = animate(frame, 0, 1);

  const name = (trackTitle as string) || title || 'Untitled';
  const by = (artist as string) || subtitle || '';
  const played = Math.max(0, Math.min(1, frame / durationInFrames));
  const totalSec = typeof duration === 'number' ? duration : durationInFrames / fps;
  const mmss = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

  const artSize = Math.min(safe.width * 0.82, safe.height * 0.46);
  const eqBars = 28;

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
          gap: Math.round(height * 0.024),
          boxSizing: 'border-box',
        }}
      >
        {/* cover art */}
        <div
          style={{
            width: artSize,
            height: artSize,
            borderRadius: Math.round(artSize * 0.06),
            overflow: 'hidden',
            backgroundColor: theme.surface,
            opacity: appear,
            transform: `translateY(${(1 - appear) * 30}px) scale(${0.94 + appear * 0.06})`,
            boxShadow:
              surface === 'brutal'
                ? `16px 16px 0 rgba(0,0,0,0.85)`
                : `0 30px 70px rgba(0,0,0,0.55)`,
            border: surface === 'brutal' ? '4px solid #000' : `1.5px solid ${accent}33`,
            position: 'relative',
            flexShrink: 0,
          }}
        >
          {cover ? (
            <Img src={resolveSrc(cover as string)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            // No cover: a generated gradient disc rather than an empty square.
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background: `radial-gradient(circle at 32% 28%, ${accent}, ${theme.surface} 68%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width={artSize * 0.3} height={artSize * 0.3} viewBox="0 0 24 24" opacity={0.85}>
                <path
                  d="M9 18V6l10-2v12M9 18a3 3 0 11-6 0 3 3 0 016 0zm10-2a3 3 0 11-6 0 3 3 0 016 0z"
                  fill="none"
                  stroke="#0B0D10"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                />
              </svg>
            </div>
          )}
        </div>

        {/* track identity */}
        <div style={{ textAlign: 'center', opacity: appear, width: '100%' }}>
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: Math.round(height * 0.032),
              fontWeight: 800,
              color: theme.text,
              lineHeight: 1.15,
            }}
          >
            {name}
          </div>
          {by && (
            <div
              style={{
                fontFamily: fonts.body,
                fontSize: Math.round(height * 0.02),
                color: accent,
                marginTop: 6,
                fontWeight: 600,
              }}
            >
              {by}
            </div>
          )}
        </div>

        {/* equaliser — seeded-free: pure sine per bar, so it is frame-deterministic */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: Math.max(2, Math.round(safe.width * 0.006)),
            height: Math.round(height * 0.05),
            opacity: appear,
          }}
        >
          {Array.from({ length: eqBars }).map((_, i) => {
            const phase = frame / 6 + i * 0.7;
            const h = 0.25 + (Math.sin(phase) * 0.5 + 0.5) * 0.75;
            return (
              <div
                key={i}
                style={{
                  width: Math.round(safe.width * 0.018),
                  height: `${h * 100}%`,
                  borderRadius: 3,
                  backgroundColor: i / eqBars <= played ? accent : `${theme.muted}44`,
                }}
              />
            );
          })}
        </div>

        {/* scrubber */}
        <div style={{ width: '100%', opacity: appear }}>
          <div
            style={{
              height: Math.round(height * 0.005),
              borderRadius: 999,
              backgroundColor: `${theme.muted}44`,
              position: 'relative',
            }}
          >
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                bottom: 0,
                width: `${played * 100}%`,
                borderRadius: 999,
                backgroundColor: accent,
              }}
            />
            <div
              style={{
                position: 'absolute',
                left: `${played * 100}%`,
                top: '50%',
                width: Math.round(height * 0.014),
                height: Math.round(height * 0.014),
                borderRadius: '50%',
                backgroundColor: accent,
                transform: 'translate(-50%, -50%)',
                boxShadow: `0 0 0 ${Math.round(height * 0.005)}px ${accent}33`,
              }}
            />
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: 8,
              fontFamily: fonts.mono,
              fontSize: Math.round(height * 0.015),
              color: theme.muted,
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            <span>{mmss(totalSec * played)}</span>
            <span>{mmss(totalSec)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ----------------------------------------------------------- VinylRecord */

/**
 * VinylRecord — a spinning record with a tonearm.
 *
 * Reads: trackTitle/title, artist/subtitle, cover, rpm, spin
 *
 * The rotation is computed from the frame, never accumulated, so any frame can
 * be rendered independently — Remotion renders out of order.
 */
export const VinylRecord: React.FC<BaseSceneProps> = ({
  title,
  trackTitle,
  subtitle,
  artist,
  cover,
  rpm = 33,
  spin = true,
  motion,
  safeArea = 'platform',
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const { theme, fonts, accent: styleAccent } = useStyle();
  const accent = accentColor || styleAccent;
  const animate = resolveMotion(motion, fps, 'reveal');
  const appear = animate(frame, 0, 1);

  const name = (trackTitle as string) || title || '';
  const by = (artist as string) || subtitle || '';

  const size = Math.min(safe.width * 0.94, safe.height * 0.6);
  // Real rpm: at 33⅓ rpm a revolution takes 1.8s.
  const revsPerSecond = (typeof rpm === 'number' ? rpm : 33) / 60;
  const angle = spin === false ? 0 : (frame / fps) * revsPerSecond * 360;

  // Grooves: concentric rings, drawn once and rotated as a group.
  const grooves = React.useMemo(
    () => Array.from({ length: 22 }).map((_, i) => 0.995 - i * 0.0295),
    []
  );

  const labelR = size * 0.17;

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
        <div
          style={{
            width: size,
            height: size,
            position: 'relative',
            opacity: appear,
            transform: `scale(${0.9 + appear * 0.1})`,
            flexShrink: 0,
          }}
        >
          {/* the disc */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '50%',
              background: 'radial-gradient(circle at 50% 50%, #14161A 0%, #0A0B0D 62%, #05060700 100%)',
              boxShadow: '0 30px 80px rgba(0,0,0,0.6)',
              transform: `rotate(${angle}deg)`,
            }}
          >
            <svg viewBox="0 0 100 100" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
              {grooves.map((r, i) => (
                <circle
                  key={i}
                  cx="50"
                  cy="50"
                  r={r * 49}
                  fill="none"
                  stroke={i % 4 === 0 ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.035)'}
                  strokeWidth={0.25}
                />
              ))}
              {/* one bright sheen wedge so the rotation is visible even on a still */}
              <path
                d="M50 50 L50 1 A49 49 0 0 1 84 15 Z"
                fill="rgba(255,255,255,0.045)"
              />
            </svg>

            {/* centre label */}
            <div
              style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                width: labelR * 2,
                height: labelR * 2,
                marginLeft: -labelR,
                marginTop: -labelR,
                borderRadius: '50%',
                overflow: 'hidden',
                background: cover ? undefined : `radial-gradient(circle at 36% 30%, ${accent}, #10121500 78%)`,
                backgroundColor: cover ? undefined : theme.surface,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {cover && (
                <Img src={resolveSrc(cover as string)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              )}
              {/* spindle hole */}
              <div
                style={{
                  position: 'absolute',
                  width: labelR * 0.14,
                  height: labelR * 0.14,
                  borderRadius: '50%',
                  backgroundColor: theme.bg,
                }}
              />
            </div>
          </div>

          {/* tonearm — drops onto the record as the scene opens */}
          <div
            style={{
              position: 'absolute',
              right: -size * 0.06,
              top: size * 0.06,
              width: size * 0.52,
              height: size * 0.06,
              transformOrigin: '92% 50%',
              transform: `rotate(${interpolate(appear, [0, 1], [-26, 14])}deg)`,
            }}
          >
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '50%',
                width: '100%',
                height: Math.max(3, size * 0.011),
                marginTop: -(size * 0.011) / 2,
                borderRadius: 999,
                background: 'linear-gradient(90deg, #C9CDD6, #7E848F)',
                boxShadow: '0 3px 10px rgba(0,0,0,0.5)',
              }}
            />
            {/* pivot */}
            <div
              style={{
                position: 'absolute',
                right: -size * 0.022,
                top: '50%',
                width: size * 0.062,
                height: size * 0.062,
                marginTop: -(size * 0.062) / 2,
                borderRadius: '50%',
                background: 'linear-gradient(140deg, #2A2E36, #14161A)',
                border: '2px solid #3A404A',
              }}
            />
            {/* headshell */}
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: '50%',
                width: size * 0.055,
                height: size * 0.028,
                marginTop: -(size * 0.028) / 2,
                borderRadius: 3,
                backgroundColor: accent,
              }}
            />
          </div>
        </div>

        {(name || by) && (
          <div style={{ textAlign: 'center', opacity: appear }}>
            {name && (
              <div
                style={{
                  fontFamily: fonts.display,
                  fontSize: Math.round(height * 0.032),
                  fontWeight: 800,
                  color: theme.text,
                  letterSpacing: -0.5,
                }}
              >
                {name}
              </div>
            )}
            {by && (
              <div
                style={{
                  fontFamily: fonts.body,
                  fontSize: Math.round(height * 0.02),
                  color: accent,
                  marginTop: 8,
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                }}
              >
                {by}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
