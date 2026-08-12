import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea, type SafeAreaMode } from '../lib/safeArea';
import { resolveMotion } from '../lib/motion';
import { useStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';
import { fitOneLine, fitWrapped, measure } from '../theme/layout';
import { resolveModelIcon } from '../lib/modelIcons';

/**
 * Social proof and engagement presets.
 *
 * Four presets that bring social media mechanics on screen:
 *   PostCard     — a social media post card with animated metric counters
 *   CommentWall  — a streaming comment stack with stagger animation
 *   SubscribeCTA — a subscribe button with cursor, click, and bell animation
 *   Leaderboard  — a ranked list with proportional bars and stagger reveal
 *
 * WHY LOCAL TYPES AND NOT THE SCHEMA
 * -----------------------------------
 * VideoSpec.schema.ts uses BaseSceneSchema.passthrough() so extra fields flow
 * through at runtime. We declare local extended types and cast `props` at each
 * component boundary. This keeps our fields isolated until the parent agent
 * promotes them to the official schema.
 *
 * ALL SIZES PROPORTIONAL
 * ----------------------
 * Every dimension is derived from `width` or `height` — no absolute px values.
 * This keeps the presets resolution-agnostic across 1080x1920 and other canvases.
 *
 * SEEDED RANDOM
 * -------------
 * Any stochastic element uses mulberry32(seed), never Math.random().
 * Remotion renders frames out-of-order — Math.random() would flicker.
 */

// ---------------------------------------------------------------------------
// Seeded PRNG — copy of mulberry32 from fx/effects/camera.tsx
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
// Shared helpers
// ---------------------------------------------------------------------------

/** Gradient avatar circle with the first letter of a name. */
const AvatarCircle: React.FC<{
  name: string;
  size: number;
  seed?: number;
  fontSize?: number;
}> = ({ name, size, seed = 42, fontSize }) => {
  const rand = mulberry32(seed);
  const h1 = Math.floor(rand() * 360);
  const h2 = (h1 + 40 + Math.floor(rand() * 60)) % 360;
  const letter = (name || '?').charAt(0).toUpperCase();
  const fs = fontSize ?? Math.round(size * 0.42);
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: `linear-gradient(135deg, hsl(${h1},80%,55%), hsl(${h2},85%,45%))`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        boxShadow: `0 0 ${Math.round(size * 0.18)}px hsl(${h1},80%,55%)55`,
      }}
    >
      <span
        style={{
          fontFamily: 'sans-serif',
          fontSize: fs,
          fontWeight: 800,
          color: '#fff',
          lineHeight: 1,
          userSelect: 'none',
        }}
      >
        {letter}
      </span>
    </div>
  );
};

/** Format a large number compactly: 12345 → "12.3K" */
function fmtNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

/* ============================================================ PostCard */

/**
 * PostCard — social media post card.
 *
 * Reads: author, handle, text, likes, reposts, comments (number), avatar, verified.
 *
 * The metric row (likes / reposts / comments) uses a slot-machine counter:
 * numbers scroll upward from 0 to their target value, clipped to the cell height.
 */
type PostCardProps = BaseSceneProps & {
  author?: string;
  handle?: string;
  text?: string;
  likes?: number;
  reposts?: number;
  comments?: number;
  avatar?: string;
  verified?: boolean;
};

const CheckBadge: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="11" fill={color} />
    <polyline
      points="7,12 11,16 17,8"
      stroke="#fff"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/** A slot-machine digit counter that scrolls upward from 0 to `value`. */
const SlotCounter: React.FC<{
  value: number;
  progress: number;
  fontSize: number;
  color: string;
  fontFamily: string;
}> = ({ value, progress, fontSize, color, fontFamily }) => {
  const displayed = Math.floor(value * progress);
  const text = fmtNum(displayed);
  // Scroll: translateY from +fontSize → 0 as progress 0→1.
  //
  // THE TRAVEL MUST BE SMALLER THAN THE SLACK IN THE WINDOW.
  // Travelling a full `fontSize` inside a `fontSize * 1.3` window bottom-aligned
  // meant the glyphs were pushed below their own clip for most of the animation
  // and the metrics row rendered as half-cut numbers. A third of the font size
  // reads as the same mechanical roll and always stays inside the window.
  const ty = interpolate(progress, [0, 1], [fontSize * 0.34, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        height: fontSize * 1.45,
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <span
        style={{
          fontFamily,
          fontSize,
          fontWeight: 700,
          color,
          lineHeight: 1,
          transform: `translateY(${ty}px)`,
          display: 'inline-block',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {text}
      </span>
    </div>
  );
};

const HeartIcon: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
  </svg>
);

const RetweetIcon: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="17 1 21 5 17 9" />
    <path d="M3 11V9a4 4 0 0 1 4-4h14" />
    <polyline points="7 23 3 19 7 15" />
    <path d="M21 13v2a4 4 0 0 1-4 4H3" />
  </svg>
);

const CommentIcon: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

export const PostCard: React.FC<BaseSceneProps> = (props) => {
  const {
    author = 'Alex Rivera',
    handle = '@alexrivera',
    text = 'Just shipped something that changes everything. Stay tuned. 🚀',
    likes = 24800,
    reposts = 3200,
    comments: commentsCount = 1480,
    verified = true,
  } = props as PostCardProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, (props.safeArea as SafeAreaMode | undefined) ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion, fps, 'reveal');

  // Card reveal: slide up + fade in
  const totalDur = durationInFrames;
  const cardProgress = animate(frame, 0, 1);

  // Metric counters start after the card appears (25% of scene)
  const metricStart = Math.round(totalDur * 0.25);
  const metricDur = Math.round(totalDur * 0.55);
  const metricProgress = interpolate(frame, [metricStart, metricStart + metricDur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const cardW = Math.min(safe.width * 0.92, Math.round(height * 0.48));
  const pd = Math.round(cardW * 0.07);
  const avatarSz = Math.round(cardW * 0.14);
  const fTitle = Math.round(height * 0.022);
  const fHandle = Math.round(height * 0.018);
  const fText = Math.round(height * 0.022);
  const fMetric = Math.round(height * 0.02);
  const iconSz = Math.round(fMetric * 1.1);
  const badgeSz = Math.round(fTitle * 0.95);

  const cardOpacity = interpolate(cardProgress, [0, 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardTy = interpolate(cardProgress, [0, 1], [Math.round(height * 0.06), 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const metrics = [
    { icon: <HeartIcon size={iconSz} color={accent} />, value: likes as number, label: 'likes' },
    { icon: <RetweetIcon size={iconSz} color={theme.cyan ?? accent} />, value: reposts as number, label: 'reposts' },
    { icon: <CommentIcon size={iconSz} color={theme.muted} />, value: commentsCount as number, label: 'comments' },
  ];

  // Seed for avatar gradient is based on author name char codes
  const authorStr = String(author);
  const avatarSeed = authorStr.split('').reduce((a, c) => a + c.charCodeAt(0), 0);

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
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Card container */}
        <div
          style={{
            width: cardW,
            background: theme.surface ?? `${theme.bg}cc`,
            borderRadius: Math.round(cardW * 0.06),
            padding: pd,
            boxShadow: `0 ${Math.round(height * 0.015)}px ${Math.round(height * 0.04)}px rgba(0,0,0,0.45)`,
            opacity: cardOpacity,
            transform: `translateY(${cardTy}px)`,
            boxSizing: 'border-box',
          }}
        >
          {/* Header row: avatar + name/handle + verified */}
          <div style={{ display: 'flex', alignItems: 'center', gap: Math.round(pd * 0.6), marginBottom: Math.round(pd * 0.8) }}>
            <AvatarCircle name={authorStr} size={avatarSz} seed={avatarSeed} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: Math.round(badgeSz * 0.4) }}>
                <span
                  style={{
                    fontFamily: fonts.display,
                    fontSize: fTitle,
                    fontWeight: 800,
                    color: theme.text,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {author}
                </span>
                {verified && <CheckBadge size={badgeSz} color={accent} />}
              </div>
              <span
                style={{
                  fontFamily: fonts.body,
                  fontSize: fHandle,
                  color: theme.muted,
                  fontWeight: 500,
                }}
              >
                {handle}
              </span>
            </div>
          </div>

          {/* Post text */}
          <p
            style={{
              fontFamily: fonts.body,
              fontSize: fText,
              color: theme.text,
              lineHeight: 1.55,
              margin: 0,
              marginBottom: Math.round(pd * 0.9),
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
            }}
          >
            {text}
          </p>

          {/* Divider */}
          <div
            style={{
              height: 1,
              background: `${theme.muted}44`,
              marginBottom: Math.round(pd * 0.6),
            }}
          />

          {/* Metric row */}
          <div style={{ display: 'flex', gap: Math.round(cardW * 0.08) }}>
            {metrics.map((m, i) => {
              // Stagger each metric by 8 frames
              const staggeredProgress = interpolate(
                metricProgress,
                [i * 0.12, Math.min(1, i * 0.12 + 0.88)],
                [0, 1],
                { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
              );
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: Math.round(iconSz * 0.35) }}>
                  {m.icon}
                  <SlotCounter
                    value={m.value}
                    progress={staggeredProgress}
                    fontSize={fMetric}
                    color={theme.text}
                    fontFamily={fonts.display}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

/* =========================================================== CommentWall */

/**
 * CommentWall — a live comment stream that stacks bottom-to-top.
 *
 * Reads: comments[] ({author, text, likes?}), title.
 *
 * Comments slide in one by one with stagger. When there are more comments
 * than can fit in the safe area, older ones drift upward and fade out.
 */
type CommentItem = {
  author: string;
  text: string;
  likes?: number;
};

type CommentWallProps = BaseSceneProps & {
  title?: string;
  comments?: CommentItem[];
};

const DEFAULT_COMMENTS: CommentItem[] = [
  { author: 'Maria K', text: 'This is absolutely incredible! 🔥', likes: 142 },
  { author: 'Dev_John', text: 'Been waiting for this moment!', likes: 87 },
  { author: 'Sophie_ML', text: 'Game changer right here 🚀', likes: 201 },
  { author: 'Alexei_D', text: 'How did you even build this?', likes: 55 },
  { author: 'TechTina', text: 'Sharing this everywhere immediately', likes: 319 },
  { author: 'Ryan_Code', text: 'The animation quality is top tier', likes: 76 },
];

export const CommentWall: React.FC<BaseSceneProps> = (props) => {
  const {
    title = 'Live Comments',
    comments: rawComments,
  } = props as CommentWallProps;

  const items: CommentItem[] = Array.isArray(rawComments) && rawComments.length > 0
    ? (rawComments as CommentItem[])
    : DEFAULT_COMMENTS;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, (props.safeArea as SafeAreaMode | undefined) ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion, fps, 'reveal');

  // How wide is a comment card
  const cardW = Math.min(safe.width, Math.round(height * 0.5));
  const pd = Math.round(cardW * 0.055);
  const avatarSz = Math.round(height * 0.048);
  const fAuthor = Math.round(height * 0.019);
  const fText = Math.round(height * 0.021);
  const fLikes = Math.round(height * 0.017);
  const cardBaseH = avatarSz + pd * 2 + Math.round(fText * 1.6) + Math.round(pd * 0.3);
  const gap = Math.round(height * 0.018);

  // How many cards fit in the viewport
  const maxVisible = Math.floor((safe.height - Math.round(height * 0.08)) / (cardBaseH + gap));
  const staggerFrames = Math.max(6, Math.round(durationInFrames / Math.max(items.length, 1)));

  // Title entrance
  const titleY = animate(frame, -Math.round(height * 0.04), 0);
  const titleOp = animate(frame, 0, 1);

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
          overflow: 'hidden',
        }}
      >
        {/* Title */}
        {title && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: Math.round(height * 0.031),
              fontWeight: 800,
              color: theme.text,
              textAlign: 'center',
              marginBottom: Math.round(height * 0.035),
              transform: `translateY(${titleY}px)`,
              opacity: titleOp,
              flexShrink: 0,
            }}
          >
            {title}
          </div>
        )}

        {/* Comment stack — comments arrive bottom-to-top */}
        <div
          style={{
            flex: 1,
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            gap,
            overflow: 'hidden',
          }}
        >
          {items.map((item, i) => {
            const arriveFrame = i * staggerFrames;
            // Progress 0→1 as card slides in
            const entryProgress = interpolate(frame, [arriveFrame, arriveFrame + Math.round(staggerFrames * 0.6)], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });

            // How many cards have arrived so far
            const arrivedCount = Math.min(
              items.length,
              Math.floor((frame + staggerFrames * 0.5) / staggerFrames) + 1
            );
            // Position from the bottom
            const positionFromBottom = arrivedCount - 1 - i;

            // If this card would be buried beyond maxVisible, start fading out
            const overflowDepth = Math.max(0, positionFromBottom - (maxVisible - 1));
            const fadeOut = interpolate(overflowDepth, [0, 1.5], [1, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const driftUp = overflowDepth * (cardBaseH + gap) * 0.5;

            if (entryProgress <= 0) return null;

            const seed = item.author.split('').reduce((a, c) => a + c.charCodeAt(0), 0);

            return (
              <div
                key={i}
                style={{
                  width: cardW,
                  alignSelf: 'center',
                  background: theme.surface ?? `${theme.bg}bb`,
                  borderRadius: Math.round(cardW * 0.045),
                  padding: pd,
                  boxSizing: 'border-box',
                  opacity: entryProgress * fadeOut,
                  transform: `translateY(${interpolate(entryProgress, [0, 1], [Math.round(height * 0.07), 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) - driftUp}px)`,
                  flexShrink: 0,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: Math.round(pd * 0.65) }}>
                  <AvatarCircle name={item.author} size={avatarSz} seed={seed} fontSize={Math.round(avatarSz * 0.40)} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: Math.round(fAuthor * 0.3) }}>
                      <span
                        style={{
                          fontFamily: fonts.display,
                          fontSize: fAuthor,
                          fontWeight: 700,
                          color: accent,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          maxWidth: '70%',
                        }}
                      >
                        {item.author}
                      </span>
                      {item.likes != null && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: Math.round(fLikes * 0.3) }}>
                          <HeartIcon size={Math.round(fLikes * 1.1)} color={accent} />
                          <span style={{ fontFamily: fonts.display, fontSize: fLikes, color: theme.muted, fontWeight: 600 }}>
                            {fmtNum(item.likes)}
                          </span>
                        </div>
                      )}
                    </div>
                    <p
                      style={{
                        fontFamily: fonts.body,
                        fontSize: fText,
                        color: theme.text,
                        margin: 0,
                        lineHeight: 1.45,
                        overflowWrap: 'break-word',
                        wordBreak: 'break-word',
                      }}
                    >
                      {item.text}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

/* ======================================================== SubscribeCTA */

/**
 * SubscribeCTA — subscribe button with cursor animation and bell ring.
 *
 * Reads: channelName, subscribers, buttonText, subscribedText, avatar.
 *
 * Timeline:
 *   0-25%   channel card fades in
 *   25-55%  cursor moves toward the button
 *   55-65%  cursor clicks, button depresses
 *   65-75%  button transitions to "Subscribed" state, subscriber count +1
 *   75-100% bell rings (oscillates), subscriber count increments
 */
type SubscribeCTAProps = BaseSceneProps & {
  channelName?: string;
  subscribers?: number;
  buttonText?: string;
  subscribedText?: string;
  avatar?: string;
};

// Bell icon — swings on its pivot at the top
const BellIcon: React.FC<{ size: number; color: string; swing: number }> = ({ size, color, swing }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={color}
    style={{ transform: `rotate(${swing}deg)`, transformOrigin: '50% 0%', display: 'block' }}
  >
    <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" />
  </svg>
);

export const SubscribeCTA: React.FC<BaseSceneProps> = (props) => {
  const {
    channelName = 'TechChannel',
    subscribers = 142000,
    buttonText = 'Subscribe',
    subscribedText = 'Subscribed',
  } = props as SubscribeCTAProps;

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, (props.safeArea as SafeAreaMode | undefined) ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion, fps, 'reveal');

  const D = durationInFrames;
  // Scene phases (in frames)
  const phaseCard    = Math.round(D * 0.25); // card appears
  const phaseCursor  = Math.round(D * 0.55); // cursor done moving
  const phaseClick   = Math.round(D * 0.65); // click moment
  const phaseSubbed  = Math.round(D * 0.72); // subscribed state shows
  const phaseBell    = Math.round(D * 0.75); // bell starts ringing

  // Card appearance
  const cardOpacity = interpolate(frame, [0, phaseCard * 0.7], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardTy = interpolate(frame, [0, phaseCard * 0.7], [Math.round(height * 0.08), 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Button scale for press feedback
  const btnScale = frame >= phaseClick && frame < phaseSubbed
    ? interpolate(frame, [phaseClick, phaseClick + Math.round(fps * 0.08)], [1, 0.92], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : frame >= phaseSubbed
    ? interpolate(frame, [phaseSubbed, phaseSubbed + Math.round(fps * 0.12)], [0.92, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  // Subscribed state transition
  const isSubscribed = frame >= phaseSubbed;
  const subbedProgress = interpolate(frame, [phaseSubbed, phaseSubbed + Math.round(fps * 0.18)], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subscriber count: shows +1 after subscribe
  const countBase = subscribers as number;
  const displayCount = isSubscribed ? countBase + 1 : countBase;

  // Bell swing: oscillating rotation after bell phase
  const bellFrameLocal = Math.max(0, frame - phaseBell);
  const bellSwing = isSubscribed
    ? Math.sin(bellFrameLocal * 0.35) * interpolate(bellFrameLocal, [0, Math.round(fps * 0.8)], [22, 6], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;
  const bellOpacity = interpolate(frame, [phaseSubbed, phaseSubbed + Math.round(fps * 0.15)], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // === CURSOR ===
  // Channel area center in safe coordinates — cursor travels from off-screen to button
  const cardW = Math.min(safe.width * 0.82, Math.round(height * 0.42));
  const btnW = Math.round(cardW * 0.52);
  const btnH = Math.round(height * 0.062);
  const cursorSize = Math.round(height * 0.038);

  // Cursor path: starts bottom-right of card, moves to button center
  const cursorStartX = safe.left + safe.width * 0.85;
  const cursorStartY = safe.top + safe.height * 0.75;
  const cursorEndX = safe.left + safe.width / 2 + btnW * 0.18; // slightly right of center
  const cursorEndY = safe.centerY + Math.round(height * 0.125);

  const cursorProgress = interpolate(frame, [phaseCard, phaseCursor], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cursorX = interpolate(cursorProgress, [0, 1], [cursorStartX, cursorEndX]);
  const cursorY = interpolate(cursorProgress, [0, 1], [cursorStartY, cursorEndY]);
  const cursorOpacity = interpolate(frame, [phaseCard * 0.5, phaseCard], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // Cursor click squish
  const cursorScaleY = frame >= phaseClick && frame < phaseBell
    ? interpolate(frame, [phaseClick, phaseClick + Math.round(fps * 0.07)], [1, 0.82], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  const channelStr = String(channelName);
  const avatarSeed = channelStr.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  const avatarSz = Math.round(height * 0.09);
  const fChannelName = Math.round(height * 0.028);
  const fSubs = Math.round(height * 0.02);
  const fBtn = Math.round(height * 0.023);
  const pd = Math.round(cardW * 0.07);
  const bellSz = Math.round(btnH * 0.62);

  // Button color transition: accent → green
  const btnBg = isSubscribed
    ? `rgba(30,215,96,${subbedProgress})`
    : accent;
  const btnBgBlend = isSubscribed ? `linear-gradient(135deg, rgba(30,215,96,${subbedProgress}), ${accent})` : accent;

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
        }}
      >
        {/* Channel card */}
        <div
          style={{
            width: cardW,
            background: theme.surface ?? `${theme.bg}bb`,
            borderRadius: Math.round(cardW * 0.07),
            padding: pd,
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: Math.round(height * 0.022),
            opacity: cardOpacity,
            transform: `translateY(${cardTy}px)`,
            boxShadow: `0 ${Math.round(height * 0.012)}px ${Math.round(height * 0.04)}px rgba(0,0,0,0.5)`,
          }}
        >
          {/* Avatar */}
          <AvatarCircle name={channelStr} size={avatarSz} seed={avatarSeed} />

          {/* Channel name */}
          <span
            style={{
              fontFamily: fonts.display,
              fontSize: fChannelName,
              fontWeight: 800,
              color: theme.text,
              textAlign: 'center',
            }}
          >
            {channelName}
          </span>

          {/* Subscriber count */}
          <span
            style={{
              fontFamily: fonts.body,
              fontSize: fSubs,
              color: theme.muted,
              fontWeight: 600,
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {fmtNum(displayCount)} subscribers
          </span>

          {/* Subscribe button */}
          <div
            style={{
              width: btnW,
              height: btnH,
              borderRadius: Math.round(btnH * 0.5),
              background: isSubscribed ? btnBgBlend : accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: Math.round(btnH * 0.22),
              cursor: 'pointer',
              transform: `scale(${btnScale})`,
              boxShadow: `0 0 ${Math.round(btnH * 0.5)}px ${accent}66`,
              transition: 'background 0.3s',
            }}
          >
            {isSubscribed && (
              <div style={{ opacity: bellOpacity }}>
                <BellIcon size={bellSz} color="#fff" swing={bellSwing} />
              </div>
            )}
            <span
              style={{
                fontFamily: fonts.display,
                fontSize: fBtn,
                fontWeight: 800,
                color: '#fff',
                letterSpacing: '0.02em',
              }}
            >
              {isSubscribed ? subscribedText : buttonText}
            </span>
          </div>
        </div>
      </div>

      {/* Cursor — rendered above the card */}
      <div
        style={{
          position: 'absolute',
          left: cursorX,
          top: cursorY,
          width: cursorSize,
          height: cursorSize,
          opacity: cursorOpacity,
          transform: `scaleY(${cursorScaleY})`,
          transformOrigin: 'top left',
          pointerEvents: 'none',
        }}
      >
        <svg width={cursorSize} height={cursorSize} viewBox="0 0 24 24">
          <path
            d="M4 2l16 10.5-7.5 1.5L9 22z"
            fill="white"
            stroke="rgba(0,0,0,0.6)"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  );
};

/**
 * Brand logo for a model name, falling back to the gradient letter avatar.
 *
 * WHY THE LOGO SITS ON A NEUTRAL DISC
 * -----------------------------------
 * Brand marks come in every shape and weight: Qwen is a dense purple glyph,
 * OpenAI is a thin white monoline, Mistral is a wide flat block. Dropped
 * straight onto the dark backdrop they read as different sizes and the row
 * looks ragged. A common disc gives every logo the same silhouette and the same
 * optical weight, and `padding` keeps the mark off the disc edge so a wide logo
 * cannot look bigger than a compact one.
 */
const BrandAvatar: React.FC<{
  name: string;
  size: number;
  seed?: number;
  fontSize?: number;
}> = ({ name, size, seed = 42, fontSize }) => {
  const icon = resolveModelIcon(name);
  if (!icon) {
    // Not a recognised model: the letter avatar is a better answer than a
    // generic "AI" glyph, which would make an unknown model look identified.
    return <AvatarCircle name={name} size={size} seed={seed} fontSize={fontSize} />;
  }
  const pad = Math.round(size * 0.18);
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: 'rgba(255,255,255,0.10)',
        border: '1px solid rgba(255,255,255,0.16)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        boxSizing: 'border-box',
        padding: pad,
      }}
    >
      <img
        src={icon.src}
        alt={name}
        style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
      />
    </div>
  );
};

/* ========================================================== Leaderboard */

/**
 * Leaderboard — ranked list with proportional bars and stagger reveal.
 *
 * Reads: rows[] ({name, value, avatar?}), title, valueSuffix.
 *
 * Each row flies in with stagger (left to right slide). The leader row at
 * position 0 gets the accent colour highlight and a larger bar.
 */
type LeaderboardRow = {
  name?: string;
  /**
   * Alias for `name`. EVERY other data preset in the library keys its items on
   * `label` (segments[].label in RingStats, Bars3D, DonutFill), so a caller —
   * human or pipeline — naturally writes `label` here too. It used to be
   * ignored, and the failure was silent and bizarre rather than loud: the row
   * rendered with NO text at all, and `AvatarCircle` got the string "undefined"
   * so every avatar showed the letter "U". The chart looked like an unfinished
   * template instead of like bad input.
   */
  label?: string;
  value: number;
  avatar?: string;
};

type LeaderboardProps = BaseSceneProps & {
  title?: string;
  rows?: LeaderboardRow[];
  valueSuffix?: string;
  /**
   * Rank by value (default). The medals make this a correctness issue, not a
   * preference: 🥇 is painted on row 0, so trusting caller order let a row
   * scoring 81 sit fifth wearing no medal while a 77 took gold. Set false only
   * when the given order IS the ranking (e.g. alphabetical or chronological).
   */
  sortRows?: boolean;
};

const DEFAULT_ROWS: LeaderboardRow[] = [
  { name: 'Aria Chen', value: 9840 },
  { name: 'Marcus Webb', value: 8120 },
  { name: 'Lena Vogt', value: 6950 },
  { name: 'Sam Park', value: 5300 },
  { name: 'Javi Morales', value: 4100 },
];

const MEDAL_COLORS = ['#FFD700', '#C0C0C0', '#CD7F32'];

export const Leaderboard: React.FC<BaseSceneProps> = (props) => {
  const {
    title = 'Leaderboard',
    rows: rawRows,
    valueSuffix = 'pts',
    sortRows = true,
  } = props as LeaderboardProps;

  const supplied: LeaderboardRow[] = Array.isArray(rawRows) && rawRows.length > 0
    ? (rawRows as LeaderboardRow[])
    : DEFAULT_ROWS;

  // Normalise `label` onto `name` and rank by value. Both fixes exist because a
  // leaderboard that paints 🥇 on row 0 is ASSERTING a ranking, so silently
  // trusting caller order is a factual error on screen, not a layout nit.
  const rows: LeaderboardRow[] = React.useMemo(() => {
    const named = supplied.map((r) => ({
      ...r,
      name: r.name ?? r.label ?? '',
      value: typeof r.value === 'number' ? r.value : 0,
    }));
    return sortRows ? [...named].sort((a, b) => b.value - a.value) : named;
  }, [supplied, sortRows]);

  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, (props.safeArea as SafeAreaMode | undefined) ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion, fps, 'reveal');

  const maxVal = rows.reduce((m, r) => Math.max(m, r.value), 0) || 1;

  const tableW = Math.min(safe.width, Math.round(height * 0.52));
  const rowH = Math.round(Math.min((safe.height - Math.round(height * 0.12)) / rows.length, height * 0.115));
  const fRank = Math.round(height * 0.022);
  const fVal = Math.round(height * 0.020);

  // LAYOUT: rank | logo | [ name over bar ] | value
  //
  // The name and the bar used to sit SIDE BY SIDE, and four attempts at dividing
  // that space all failed because the space is not there to divide. Measured, at
  // 5 rows in a 920px table:
  //
  //   chrome  = padL 27 + padR 62 + rank 62 + logo 91 + gaps 76 = 318
  //   content = 602, of which the value needs 102
  //
  // leaving 500px for a bar that needs ~250 to read as a measurement AND an
  // 18-character model name ("Llama-4-Scout-109B") that needs ~310 at its
  // smallest legible size. 560 into 500 does not go, so every side-by-side split
  // shipped a visible defect:
  //   1. flat font + ellipsis -> "Llama-4-Scout-1...", dropping the parameter
  //      count that is the reason the name is on screen.
  //   2. two-line wrap        -> nothing lost, but "GLM-5.2-Air" wrapped while
  //      row 5 did not, so the rows sat on inconsistent baselines.
  //   3. fitOneLine, bar gets -> fitOneLine CLAMPS at minFontSize instead of
  //      the rest             promising a fit, so text overran the column and
  //                             `overflow: hidden` sheared it mid-glyph: all four
  //                             long names ended at exactly x=541, showing
  //                             "Claude-Opus-4." with the 6 gone. Worse than an
  //                             ellipsis, which at least admits it truncated.
  //   4. name gets what it    -> no shear, but the bar collapsed from 301px to
  //      needs, bar the rest     190px, undoing the widening it was asked for.
  //
  // STACKING them ends the fight: the row is 206px tall and was using ~40 of it.
  // Name and bar each get the FULL 500px column, so the bar is wider than it has
  // ever been and the name renders at ~35px instead of ~18px.
  // padR was rowH*0.30 while the value column still overflowed and ate part of
  // it; measured air was 38px. With the overflow gone the full padding plus
  // `measure()`'s slack over the real glyph box came to 79px — two digits' worth
  // of empty space, now the opposite defect. 0.15 lands at ~48px measured.
  const padL = Math.round(rowH * 0.13);
  const padR = Math.round(rowH * 0.15);
  const gap = Math.round(rowH * 0.09);
  const rankW = Math.round(rowH * 0.30);
  const avatarSz = Math.round(rowH * 0.44);
  const chrome = padL + padR + gap * 3 + rankW + avatarSz;
  const content = Math.max(Math.round(tableW * 0.4), tableW - chrome);

  // The value column is MEASURED, not a percentage guess.
  // A flat 17% share came to 102px while "77 %" renders 98px wide — technically
  // enough, but any longer string ("9 840 pts") overflowed, and since every child
  // is flexShrink: 0 the overflow pushed the row right and ATE padR: measured
  // 25px of air where padR asks for 62.
  const longestValue = rows.reduce((acc, r) => {
    const s = `${r.value.toLocaleString()}${valueSuffix ? ` ${valueSuffix}` : ''}`;
    return s.length > acc.length ? s : acc;
  }, '');
  const longestName = rows.reduce(
    (acc, r) => (String(r.name ?? '').length > acc.length ? String(r.name ?? '') : acc),
    ''
  );
  const valueW = Math.ceil(
    measure({
      text: longestValue || '100 %',
      fontFamily: fonts.display,
      fontSize: fVal,
      fontWeight: 700,
    }).width
  ) + 2;

  // Name and bar share this, stacked.
  const colW = content - valueW - gap;
  const barMaxW = colW;

  // Font is DERIVED FROM A MEASUREMENT, not clamped by one. fitOneLine returns
  // minFontSize when nothing fits, which is how the shear above happened; scaling
  // a measured width guarantees the text fits the column it is given.
  const probeSize = Math.round(height * 0.02);
  const probeW = measure({
    text: longestName || 'Aria Chen',
    fontFamily: fonts.display,
    fontSize: probeSize,
    fontWeight: 800,
  }).width;
  const fName = Math.max(
    Math.round(height * 0.013),
    Math.min(Math.round(height * 0.023), Math.floor((probeSize * colW * 0.98) / probeW))
  );
  const staggerFrames = Math.max(5, Math.round(durationInFrames / (rows.length + 2)));

  // Title
  const titleOp = animate(frame, 0, 1);
  const titleY = animate(frame, -Math.round(height * 0.04), 0);

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
          gap: Math.round(height * 0.03),
        }}
      >
        {/* Title */}
        {title && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: Math.round(height * 0.033),
              fontWeight: 800,
              color: theme.text,
              textAlign: 'center',
              opacity: titleOp,
              transform: `translateY(${titleY}px)`,
              flexShrink: 0,
            }}
          >
            {title}
          </div>
        )}

        {/* Rows */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: Math.round(rowH * 0.12),
            width: tableW,
          }}
        >
          {rows.map((row, i) => {
            const arriveFrame = i * staggerFrames;
            const rowProgress = interpolate(frame, [arriveFrame, arriveFrame + Math.round(staggerFrames * 1.2)], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const barProgress = interpolate(frame, [arriveFrame + Math.round(staggerFrames * 0.5), arriveFrame + Math.round(staggerFrames * 2)], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });

            const isLeader = i === 0;
            const rowAccent = isLeader ? accent : theme.muted;
            const barFill = isLeader ? accent : (theme.cyan ?? accent);
            const rowBg = isLeader
              ? `${accent}18`
              : `${theme.surface ?? theme.bg}88`;
            const barW = Math.round(barMaxW * (row.value / maxVal) * barProgress);

            const nameStr = String(row.name);
            const seed = nameStr.split('').reduce((a, c) => a + c.charCodeAt(0), 0) + i * 100;
            const medal = i < 3 ? MEDAL_COLORS[i] : null;

            const rowSlideX = interpolate(rowProgress, [0, 1], [-Math.round(width * 0.15), 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });

            return (
              <div
                key={i}
                style={{
                  height: rowH,
                  background: rowBg,
                  borderRadius: Math.round(rowH * 0.28),
                  display: 'flex',
                  alignItems: 'center',
                  padding: `0 ${padR}px 0 ${padL}px`,
                  gap,
                  boxSizing: 'border-box',
                  opacity: rowProgress,
                  transform: `translateX(${rowSlideX}px)`,
                  border: isLeader ? `1.5px solid ${accent}55` : 'none',
                  flexShrink: 0,
                }}
              >
                {/* Rank badge */}
                <div
                  style={{
                    width: rankW,
                    textAlign: 'center',
                    flexShrink: 0,
                  }}
                >
                  {medal ? (
                    <span style={{ fontSize: Math.round(fRank * 1.2), lineHeight: 1 }}>{['🥇', '🥈', '🥉'][i]}</span>
                  ) : (
                    <span
                      style={{
                        fontFamily: fonts.mono,
                        fontSize: fRank,
                        fontWeight: 700,
                        color: theme.muted,
                      }}
                    >
                      {i + 1}
                    </span>
                  )}
                </div>

                {/* Brand logo when the label names a known model, letter avatar otherwise. */}
                <BrandAvatar name={nameStr} size={avatarSz} seed={seed} fontSize={Math.round(avatarSz * 0.40)} />

                {/* NAME STACKED OVER BAR — both get the full column.
                    Side by side, neither fit: see the layout comment above. */}
                <div
                  style={{
                    width: colW,
                    flexShrink: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    gap: Math.round(rowH * 0.07),
                  }}
                >
                  <span
                    style={{
                      fontFamily: fonts.display,
                      fontSize: fName,
                      fontWeight: isLeader ? 800 : 600,
                      color: theme.text,
                      whiteSpace: 'nowrap',
                      lineHeight: 1.1,
                    }}
                  >
                    {row.name}
                  </span>
                  <div
                    style={{
                      width: barMaxW,
                      height: Math.round(rowH * 0.15),
                      borderRadius: Math.round(rowH * 0.075),
                      background: `${barFill}22`,
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: barW,
                        height: '100%',
                        background: barFill,
                        borderRadius: Math.round(rowH * 0.075),
                        boxShadow: `0 0 ${Math.round(rowH * 0.12)}px ${barFill}88`,
                      }}
                    />
                  </div>
                </div>

                {/* Value — width MEASURED from the longest string so it cannot
                    overflow and eat the row's right padding. */}
                <span
                  style={{
                    fontFamily: fonts.display,
                    fontSize: fVal,
                    fontWeight: 700,
                    color: rowAccent,
                    width: valueW,
                    flexShrink: 0,
                    textAlign: 'right',
                    whiteSpace: 'nowrap',
                    fontVariantNumeric: 'tabular-nums',
                  }}
                >
                  {row.value.toLocaleString()}{valueSuffix ? ` ${valueSuffix}` : ''}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
