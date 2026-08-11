import React from 'react';
import {
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea } from '../lib/safeArea';
import { resolveMotion } from '../lib/motion';
import { useStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';

/**
 * Media presets — the scenes that put real footage and stills on screen.
 *
 * WHY THESE ARE A SEPARATE PACK
 * -----------------------------
 * Every existing preset draws itself from data. These four instead *host*
 * external assets: a photo, a video, a screen recording, a voice note. They
 * share the frame/mask/label plumbing below, so they live in one file.
 *
 * ASSET RESOLUTION
 * ----------------
 * `src` may be a URL (http…) or a path relative to `remotion/public/`. Anything
 * not starting with http is passed through `staticFile()`. A missing asset is
 * the one failure mode that matters here, so each preset renders a loud, legible
 * placeholder instead of an empty box: a blank frame passes automated QA and is
 * only caught by a human watching the video.
 *
 * WHY OffthreadVideo AND NOT <Video>
 * ----------------------------------
 * `<OffthreadVideo>` extracts frames with ffmpeg during a render instead of
 * driving an HTML5 video element. Seeking a <video> during a parallel render is
 * the classic source of duplicated/black frames, because the element's
 * currentTime does not always settle before the frame is captured.
 */

const resolveSrc = (src: string): string =>
  src.startsWith('http') || src.startsWith('data:') ? src : staticFile(src);

/** Loud, readable stand-in for a missing asset. */
const MissingAsset: React.FC<{ what: string; field: string; theme: { bg: string } }> = ({
  what,
  field,
  theme,
}) => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      backgroundColor: '#3A0A0A',
      color: '#FFFFFF',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 18,
      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
      textAlign: 'center',
      padding: 70,
    }}
  >
    <div style={{ fontSize: 46, fontWeight: 800 }}>⚠ NO {what} IN SPEC</div>
    <div style={{ fontSize: 30, opacity: 0.85 }}>set `{field}` on this scene</div>
  </div>
);

/* ------------------------------------------------------------------ frames */

/**
 * The rounded "device-ish" plate every media preset sits on. Carries the style
 * kit's surface treatment so a photo in the `glass` kit gets a frosted frame
 * and the same photo in `pop` gets a hard brutalist shadow.
 */
const MediaPlate: React.FC<{
  radius: number;
  children: React.ReactNode;
  surface: string;
  accent: string;
  style?: React.CSSProperties;
}> = ({ radius, children, surface, accent, style }) => {
  const shadow =
    surface === 'brutal'
      ? `14px 14px 0 rgba(0,0,0,0.85)`
      : surface === 'glass'
        ? `0 24px 70px rgba(0,0,0,0.55)`
        : `0 16px 44px rgba(0,0,0,0.5)`;
  const border =
    surface === 'brutal'
      ? `4px solid #000000`
      : surface === 'glass'
        ? `1.5px solid rgba(255,255,255,0.22)`
        : `2px solid ${accent}44`;
  return (
    <div
      style={{
        position: 'relative',
        borderRadius: radius,
        overflow: 'hidden',
        boxShadow: shadow,
        border,
        boxSizing: 'border-box',
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/** Caption strip used by the media presets, kept identical across them. */
const Caption: React.FC<{
  title?: string;
  subtitle?: string;
  fonts: { display: string; body: string };
  theme: { text: string; muted: string };
  accent: string;
  height: number;
  appear: number;
}> = ({ title, subtitle, fonts, theme, accent, height, appear }) => {
  if (!title && !subtitle) return null;
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: Math.round(height * 0.008),
        opacity: appear,
        transform: `translateY(${(1 - appear) * 18}px)`,
      }}
    >
      {title && (
        <div
          style={{
            fontFamily: fonts.display,
            fontSize: Math.round(height * 0.031),
            fontWeight: 800,
            color: theme.text,
            lineHeight: 1.12,
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
            fontWeight: 600,
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};

/* ------------------------------------------------------- ImageShowcase */

/**
 * ImageShowcase — one or more stills with a slow Ken Burns drift.
 *
 * Reads: images[] (or src), title, subtitle, fit, kenBurns
 *
 * A static photo held for three seconds is dead air; the slow scale+pan is what
 * keeps a still frame alive in a motion piece. `kenBurns: false` disables it for
 * cases where the image is a diagram whose geometry must not move.
 */
export const ImageShowcase: React.FC<BaseSceneProps> = ({
  images,
  src,
  title,
  subtitle,
  fit = 'cover',
  kenBurns = true,
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

  const list: string[] = Array.isArray(images) && images.length
    ? (images as string[])
    : src
      ? [src as string]
      : [];

  if (!list.length) {
    return <MissingAsset what="IMAGE" field="images or src" theme={theme} />;
  }

  // Each image owns an equal slice of the scene.
  const per = durationInFrames / list.length;
  const index = Math.min(list.length - 1, Math.floor(frame / per));
  const localFrame = frame - index * per;
  const localProgress = Math.max(0, Math.min(1, localFrame / per));

  const appear = animate(localFrame, 0, 1);
  // Alternating drift direction so consecutive stills do not all pan the same
  // way, which reads as a mistake rather than a choice.
  const dir = index % 2 === 0 ? 1 : -1;
  const scale = kenBurns === false ? 1 : interpolate(localProgress, [0, 1], [1.06, 1.16]);
  const shiftX = kenBurns === false ? 0 : interpolate(localProgress, [0, 1], [-14 * dir, 14 * dir]);

  const plateW = safe.width;
  const plateH = Math.round(safe.height * (title || subtitle ? 0.76 : 0.94));

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
          gap: Math.round(height * 0.022),
          boxSizing: 'border-box',
        }}
      >
        <MediaPlate
          radius={Math.round(height * 0.02)}
          surface={surface}
          accent={accent}
          style={{
            width: plateW,
            height: plateH,
            opacity: appear,
            transform: `scale(${0.96 + appear * 0.04})`,
            backgroundColor: theme.surface,
          }}
        >
          <Img
            src={resolveSrc(list[index])}
            style={{
              width: '100%',
              height: '100%',
              objectFit: fit === 'contain' ? 'contain' : 'cover',
              transform: `scale(${scale}) translateX(${shiftX}px)`,
            }}
          />
        </MediaPlate>
        <Caption
          title={title}
          subtitle={subtitle}
          fonts={fonts}
          theme={theme}
          accent={accent}
          height={height}
          appear={appear}
        />
        {list.length > 1 && (
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            {list.map((_, i) => (
              <div
                key={i}
                style={{
                  width: i === index ? Math.round(width * 0.05) : Math.round(width * 0.016),
                  height: Math.round(height * 0.005),
                  borderRadius: 999,
                  backgroundColor: i === index ? accent : `${theme.muted}66`,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/* ---------------------------------------------------------- VideoEmbed */

/**
 * VideoEmbed — external footage framed in the scene, with an optional
 * play-button flourish and progress bar.
 *
 * Reads: src, title, subtitle, fit, startFrom, showControls, muted
 */
export const VideoEmbed: React.FC<BaseSceneProps> = ({
  src,
  title,
  subtitle,
  fit = 'cover',
  startFrom,
  showControls = true,
  muted = true,
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

  if (!src) {
    return <MissingAsset what="VIDEO" field="src" theme={theme} />;
  }

  const plateH = Math.round(safe.height * (title || subtitle ? 0.74 : 0.92));
  const progress = Math.max(0, Math.min(1, frame / durationInFrames));

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
          gap: Math.round(height * 0.022),
          boxSizing: 'border-box',
        }}
      >
        <MediaPlate
          radius={Math.round(height * 0.02)}
          surface={surface}
          accent={accent}
          style={{
            width: safe.width,
            height: plateH,
            opacity: appear,
            transform: `scale(${0.96 + appear * 0.04})`,
            backgroundColor: '#000000',
          }}
        >
          <OffthreadVideo
            src={resolveSrc(src as string)}
            muted={muted !== false}
            startFrom={typeof startFrom === 'number' ? startFrom : undefined}
            style={{
              width: '100%',
              height: '100%',
              objectFit: fit === 'contain' ? 'contain' : 'cover',
            }}
          />
          {showControls !== false && (
            <>
              {/* progress bar hugging the bottom edge of the plate */}
              <div
                style={{
                  position: 'absolute',
                  left: 0,
                  right: 0,
                  bottom: 0,
                  height: Math.round(height * 0.006),
                  backgroundColor: 'rgba(255,255,255,0.18)',
                }}
              >
                <div
                  style={{
                    width: `${progress * 100}%`,
                    height: '100%',
                    backgroundColor: accent,
                  }}
                />
              </div>
              {/* play glyph fades out once the clip is under way */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  opacity: interpolate(frame, [0, fps * 0.7, fps * 1.1], [0.95, 0.95, 0], {
                    extrapolateRight: 'clamp',
                  }),
                }}
              >
                <div
                  style={{
                    width: Math.round(height * 0.075),
                    height: Math.round(height * 0.075),
                    borderRadius: '50%',
                    backgroundColor: 'rgba(0,0,0,0.55)',
                    border: `3px solid rgba(255,255,255,0.9)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <svg width={Math.round(height * 0.03)} height={Math.round(height * 0.03)} viewBox="0 0 24 24">
                    <path d="M8 5.5L18.5 12L8 18.5Z" fill="#FFFFFF" />
                  </svg>
                </div>
              </div>
            </>
          )}
        </MediaPlate>
        <Caption
          title={title}
          subtitle={subtitle}
          fonts={fonts}
          theme={theme}
          accent={accent}
          height={height}
          appear={appear}
        />
      </div>
    </div>
  );
};

/* --------------------------------------------------------- ScreenRecord */

/**
 * ScreenRecord — a screen capture presented as a browser/OS window, with a
 * REC indicator and an optional cursor highlight.
 *
 * Reads: src, images[], title, subtitle, appName, urlBar, showRec, chrome
 *
 * This is the preset for "I recorded my screen, put it in the video". The window
 * chrome is what makes the footage read as a recording rather than as a video
 * that happens to be of a UI — without it, a screen capture of a dark app on a
 * dark background has no visible edge at all.
 *
 * Accepts a video `src` OR a still via `images[0]`, because a screenshot walked
 * through with Ken Burns is often enough and much cheaper than a real capture.
 */
export const ScreenRecord: React.FC<BaseSceneProps> = ({
  src,
  images,
  title,
  subtitle,
  appName,
  urlBar,
  showRec = true,
  chrome = 'browser',
  fit = 'cover',
  muted = true,
  motion,
  safeArea = 'platform',
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const { theme, fonts, accent: styleAccent, surface } = useStyle();
  const accent = accentColor || styleAccent;
  const animate = resolveMotion(motion, fps, 'reveal');
  const appear = animate(frame, 0, 1);

  const still = Array.isArray(images) && images.length ? (images[0] as string) : undefined;
  if (!src && !still) {
    return <MissingAsset what="SCREEN CAPTURE" field="src or images[0]" theme={theme} />;
  }

  const barH = Math.round(height * 0.026);
  const plateH = Math.round(safe.height * (title || subtitle ? 0.7 : 0.88));
  // A recording is landscape; centring it in a vertical frame with the window
  // chrome above keeps the aspect honest instead of cropping it to a square.
  const dot = (c: string) => (
    <div style={{ width: barH * 0.3, height: barH * 0.3, borderRadius: '50%', backgroundColor: c }} />
  );

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
          gap: Math.round(height * 0.02),
          boxSizing: 'border-box',
        }}
      >
        <MediaPlate
          radius={Math.round(height * 0.014)}
          surface={surface}
          accent={accent}
          style={{
            width: safe.width,
            height: plateH,
            opacity: appear,
            transform: `translateY(${(1 - appear) * 24}px) scale(${0.97 + appear * 0.03})`,
            backgroundColor: '#0A0C10',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {chrome !== 'none' && (
            <div
              style={{
                height: barH,
                backgroundColor: '#1B2027',
                display: 'flex',
                alignItems: 'center',
                gap: barH * 0.22,
                padding: `0 ${barH * 0.34}px`,
                flexShrink: 0,
                borderBottom: '1px solid rgba(255,255,255,0.08)',
              }}
            >
              {dot('#FF5F57')}
              {dot('#FEBC2E')}
              {dot('#28C840')}
              {(urlBar || appName) && (
                <div
                  style={{
                    marginLeft: barH * 0.3,
                    flex: 1,
                    height: barH * 0.56,
                    borderRadius: barH * 0.28,
                    backgroundColor: '#0E1319',
                    display: 'flex',
                    alignItems: 'center',
                    padding: `0 ${barH * 0.34}px`,
                    fontFamily: fonts.mono,
                    fontSize: barH * 0.38,
                    color: theme.muted,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                  }}
                >
                  {urlBar || appName}
                </div>
              )}
            </div>
          )}
          <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
            {src ? (
              <OffthreadVideo
                src={resolveSrc(src as string)}
                muted={muted !== false}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: fit === 'contain' ? 'contain' : 'cover',
                }}
              />
            ) : (
              <Img
                src={resolveSrc(still as string)}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: fit === 'contain' ? 'contain' : 'cover',
                  // Slow drift so a screenshot still feels like footage.
                  transform: `scale(${interpolate(frame, [0, 240], [1.02, 1.1], {
                    extrapolateRight: 'clamp',
                  })})`,
                }}
              />
            )}
            {showRec !== false && (
              <div
                style={{
                  position: 'absolute',
                  top: barH * 0.5,
                  right: barH * 0.5,
                  display: 'flex',
                  alignItems: 'center',
                  gap: barH * 0.24,
                  padding: `${barH * 0.16}px ${barH * 0.36}px`,
                  borderRadius: 999,
                  backgroundColor: 'rgba(0,0,0,0.62)',
                  fontFamily: fonts.body,
                  fontSize: barH * 0.42,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  letterSpacing: 1,
                }}
              >
                <div
                  style={{
                    width: barH * 0.32,
                    height: barH * 0.32,
                    borderRadius: '50%',
                    backgroundColor: '#FF3B30',
                    // 1s blink at any fps.
                    opacity: frame % fps < fps * 0.55 ? 1 : 0.25,
                  }}
                />
                REC
              </div>
            )}
          </div>
        </MediaPlate>
        <Caption
          title={title}
          subtitle={subtitle}
          fonts={fonts}
          theme={theme}
          accent={accent}
          height={height}
          appear={appear}
        />
      </div>
    </div>
  );
};

/* ------------------------------------------------------------ VoiceMemo */

/**
 * VoiceMemo — a voice message / dictaphone bubble with a live waveform.
 *
 * Reads: title, subtitle, duration, waveformSeed, transcript, playing
 *
 * The waveform is generated, not sampled from the audio: a preset cannot read
 * the mixed track at render time, and a fake-but-plausible envelope is
 * indistinguishable at this size. It is seeded so it does not jitter per frame.
 */
export const VoiceMemo: React.FC<BaseSceneProps> = ({
  title,
  subtitle,
  duration,
  waveformSeed = 11,
  transcript,
  motion,
  safeArea = 'platform',
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const { theme, fonts, accent: styleAccent } = useStyle();
  const accent = accentColor || styleAccent;
  const animate = resolveMotion(motion, fps, 'reveal');
  const appear = animate(frame, 0, 1);

  const bars = 46;
  // Deterministic envelope: two sines plus a seeded offset per bar. Speech-like
  // (bursts and pauses) rather than uniform noise.
  const heights = React.useMemo(() => {
    const out: number[] = [];
    for (let i = 0; i < bars; i++) {
      const s = Math.sin((i + waveformSeed) * 1.7) * 0.5 + 0.5;
      const t = Math.sin((i + waveformSeed) * 0.41) * 0.5 + 0.5;
      const burst = Math.sin(i * 0.28) > -0.35 ? 1 : 0.32;
      out.push(Math.max(0.16, Math.min(1, (s * 0.62 + t * 0.5) * burst)));
    }
    return out;
  }, [waveformSeed]);

  const played = Math.max(0, Math.min(1, frame / durationInFrames));
  const totalSec = typeof duration === 'number' ? duration : durationInFrames / fps;
  const elapsed = totalSec * played;
  const mmss = (s: number) =>
    `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

  const cardW = safe.width;
  const barGap = Math.max(2, Math.round(cardW * 0.004));
  const barW = (cardW * 0.74 - barGap * (bars - 1)) / bars;

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
          gap: Math.round(height * 0.026),
          boxSizing: 'border-box',
        }}
      >
        {title && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: Math.round(height * 0.034),
              fontWeight: 800,
              color: theme.text,
              opacity: appear,
            }}
          >
            {title}
          </div>
        )}

        <div
          style={{
            backgroundColor: theme.surface,
            borderRadius: Math.round(height * 0.018),
            padding: Math.round(height * 0.022),
            display: 'flex',
            alignItems: 'center',
            gap: Math.round(width * 0.028),
            opacity: appear,
            transform: `translateY(${(1 - appear) * 22}px)`,
            border: `1.5px solid ${accent}33`,
            boxSizing: 'border-box',
          }}
        >
          {/* play button with a soft pulse ring while "playing" */}
          <div
            style={{
              width: Math.round(height * 0.056),
              height: Math.round(height * 0.056),
              borderRadius: '50%',
              backgroundColor: accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              boxShadow: `0 0 0 ${Math.round(
                interpolate(Math.sin(frame / 9), [-1, 1], [3, 11])
              )}px ${accent}22`,
            }}
          >
            <svg width={Math.round(height * 0.022)} height={Math.round(height * 0.022)} viewBox="0 0 24 24">
              <path d="M8 5.5L18.5 12L8 18.5Z" fill="#0B0D10" />
            </svg>
          </div>

          {/* waveform: played bars in accent, remainder muted */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: barGap,
              height: Math.round(height * 0.052),
            }}
          >
            {heights.map((h, i) => {
              const isPlayed = i / bars <= played;
              // The bar at the playhead lifts slightly — the detail that makes
              // the waveform look driven by audio rather than painted.
              const atHead = Math.abs(i / bars - played) < 1.5 / bars;
              const lift = atHead ? 1.18 : 1;
              return (
                <div
                  key={i}
                  style={{
                    width: barW,
                    height: `${Math.min(100, h * 100 * lift)}%`,
                    borderRadius: barW,
                    backgroundColor: isPlayed ? accent : `${theme.muted}55`,
                  }}
                />
              );
            })}
          </div>

          <div
            style={{
              fontFamily: fonts.mono,
              fontSize: Math.round(height * 0.017),
              color: theme.muted,
              flexShrink: 0,
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {mmss(elapsed)}
          </div>
        </div>

        {(transcript || subtitle) && (
          <div
            style={{
              fontFamily: fonts.body,
              fontSize: Math.round(height * 0.021),
              color: transcript ? theme.text : accent,
              lineHeight: 1.4,
              opacity: appear,
            }}
          >
            {transcript ? `«${transcript}»` : subtitle}
          </div>
        )}
      </div>
    </div>
  );
};
