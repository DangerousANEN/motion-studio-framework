import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';

/**
 * TgChat — a Telegram thread with bubbles arriving one after another, and
 * optionally a composed message being typed and sent on camera.
 *
 * Reads: messages[]{from,text,time,read,out}, contactName, contactStatus, title,
 *        compose, typing, showCursor, showInputBar, sendAtProgress, tgTheme,
 *        datePill
 *
 * WHY THE COMPOSE SEQUENCE EXISTS
 * -------------------------------
 * A thread whose bubbles merely fade in reads as a screenshot with an
 * animation slapped on. The moment that makes a chat mockup feel real is
 * watching the message get *written*: characters appearing in the input field,
 * a cursor travelling to the send button, the button being pressed, and the
 * bubble launching into the thread. That is the sequence this preset performs
 * when `compose` is set.
 *
 * EVERYTHING IS OPT-OUT
 * ---------------------
 * `compose` absent            -> no input bar, no cursor: the old behaviour,
 *                                so existing specs render exactly as before.
 * `showInputBar: false`       -> keeps the typing but hides the whole bar.
 * `showCursor: false`         -> types and sends without the mouse pointer,
 *                                which is what you want for a "phone" look
 *                                where a finger, not a cursor, would tap.
 * `typing: false`             -> the text is already in the field; only the
 *                                click and send are animated.
 *
 * TIMELINE
 * --------
 * The composed message owns the tail of the scene. `sendAtProgress` (0..1,
 * default 0.72) is the moment the send button is pressed; typing fills the
 * span before it, and the sent bubble flies into the thread after it. Anchoring
 * to scene progress rather than absolute frames means the same spec works at
 * any scene length instead of the send landing off the end of a short scene.
 *
 * FIDELITY TO THE REAL CLIENT
 * ---------------------------
 * Reviewed side by side against an Android screenshot; every difference below
 * was a reason the mockup read as "not Telegram", in rough order of how loudly
 * it announced itself:
 *
 *   1. FONT. This preset set no `fontFamily`, so it inherited the composition's
 *      serif display face. Telegram is a system sans (Roboto/SF/Inter) — nothing
 *      else makes a chat look this wrong this fast. Now pinned explicitly.
 *   2. LIGHT THEME. The reference is the light theme on a doodled sky-blue
 *      wallpaper; this preset only had the dark one. `tgTheme` picks, and light
 *      is the default because that is what a screenshot-in-a-video usually is.
 *   3. TAILS AND GROUPING. Every bubble had a tail. The real client draws a nib
 *      only on the LAST bubble of a same-sender run and squares the inner
 *      corners of the rest, which is what makes a burst of messages read as one
 *      block. Grouping also collapses the vertical gap within a run (2px) versus
 *      between runs (10px).
 *   4. INLINE META. Time and ticks sit on the SAME line as short text, indented
 *      into the text flow by a reserved inline spacer — not on their own line
 *      under it. Getting this wrong makes every bubble one line too tall.
 *   5. HEADER CHROME. Back arrow, call handset and the 3-dot menu were missing,
 *      and the avatar was a flat gradient disc with no initial in it.
 *   6. DATE PILL. A centred translucent capsule above the first message.
 *
 * GEOMETRY NOTE
 * -------------
 * Bubble radius is 18px with 6px on grouped inner corners, the input bar is 6%
 * of frame height, and the send/record button is a filled circle to the right of
 * the field — all measured off the reference.
 */

/** Palette per Telegram theme, sampled from the reference screenshots. */
const THEMES = {
  light: {
    bg: '#D3ECFA',
    doodle: 'rgba(120, 178, 220, 0.22)',
    bubbleIn: '#FFFFFF',
    // Telegram's outgoing bubble is BLUE with white text, not the pale green of
    // WhatsApp — sampled off the reference screenshot as #3996EC. Using green
    // here made the mockup read as the wrong app entirely, which review caught
    // as the single most obvious difference.
    bubbleOut: '#3996EC',
    textIn: '#000000',
    textOut: '#FFFFFF',
    metaIn: 'rgba(0,0,0,0.35)',
    metaOut: 'rgba(255,255,255,0.78)',
    header: '#FFFFFF',
    headerText: '#1D242D',
    headerMeta: '#82919E',
    bar: '#FFFFFF',
    barIcon: '#8794A1',
    placeholder: '#9CA9B4',
    accent: '#3390EC',
    tick: 'rgba(255,255,255,0.92)',
    pill: 'rgba(125, 160, 190, 0.55)',
    pillText: '#FFFFFF',
    shadow: '0 1px 2px rgba(16,35,47,0.12)',
  },
  dark: {
    bg: '#0E1621',
    doodle: 'rgba(255, 255, 255, 0.035)',
    bubbleIn: '#182533',
    bubbleOut: '#2B5278',
    textIn: '#FFFFFF',
    textOut: '#FFFFFF',
    metaIn: '#6D7F8F',
    metaOut: 'rgba(255,255,255,0.62)',
    header: '#17212B',
    headerText: '#FFFFFF',
    headerMeta: '#7D8E9C',
    bar: '#17212B',
    barIcon: '#707E8B',
    placeholder: '#6D7F8F',
    accent: '#5288C1',
    tick: '#5FD3F3',
    pill: 'rgba(24, 37, 51, 0.72)',
    pillText: 'rgba(255,255,255,0.86)',
    shadow: '0 1px 3px rgba(0,0,0,0.35)',
  },
} as const;

/**
 * Telegram renders in the platform UI font. Inheriting the composition's serif
 * display face was the single most obvious tell that this was not a real client.
 */
const TG_FONT =
  '"Inter", "Segoe UI", Roboto, "Helvetica Neue", "SF Pro Text", Arial, sans-serif';

interface ChatMessage {
  from?: string;
  text?: string;
  /** Original in-render Telegram-style sticker, constrained by VideoSpec schema. */
  sticker?: 'brain' | 'rocket' | 'spark' | 'thumbsUp';
  time?: string;
  read?: boolean;
  out?: boolean;
}

/** Rough width estimate so a bubble can size itself without a DOM measure. */
const estimateWidth = (text: string, fontSize: number): number =>
  Math.min(text.length * fontSize * 0.54, 10_000);

/**
 * Sent/read ticks. The real glyph is two overlapping checks offset by ~4px with
 * the second clipped by the first, not two independent strokes at a distance.
 */
const Tick: React.FC<{ read: boolean; color: string; size?: number }> = ({
  read,
  color,
  size = 16,
}) => (
  <svg
    width={size}
    height={(size * 11) / 16}
    viewBox="0 0 16 11"
    style={{ marginLeft: 3, display: 'block' }}
  >
    <path
      d={read ? 'M0.8 5.9L3.9 9L9.7 2.2' : 'M2.4 5.9L5.5 9L11.3 2.2'}
      stroke={color}
      strokeWidth={1.7}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {read && (
      <path
        d="M6.4 9L12.2 2.2"
        stroke={color}
        strokeWidth={1.7}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    )}
  </svg>
);

/**
 * The bubble nib. Telegram's is a curved flick off the bottom corner, not a
 * triangle — a straight-edged triangle is instantly recognisable as a fake.
 *
 * GEOMETRY: the svg is placed so its LEFT edge sits on the bubble's right edge
 * (`right: -size`) and its bottom aligns with the bubble's bottom. The path fills
 * from the top-left corner (which meets the bubble's straightened corner) out to
 * the flick. An earlier version used `right: -size*0.52` with a path drawn in the
 * left half of the viewBox, which put the visible ink back INSIDE the bubble and
 * rendered no tail at all — pixel-checked: the bubble's right edge was a plain
 * rounded corner, max x identical on every row.
 */
const Tail: React.FC<{ out: boolean; color: string; size: number }> = ({ out, color, size }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 12 12"
    style={{
      position: 'absolute',
      bottom: 0,
      [out ? 'right' : 'left']: -size + 0.5,
      transform: out ? undefined : 'scaleX(-1)',
      display: 'block',
    }}
  >
    {/* Straight left edge glued to the bubble; concave sweep back to the point. */}
    <path d="M0 0V12H8.4C4.2 11 1.6 7.4 0.6 2.4Z" fill={color} />
  </svg>
);

/**
 * Mouse pointer, drawn rather than imported so it needs no asset and scales
 * with the frame. The shadow is what sells it as sitting *above* the UI.
 */
const STICKER_GLYPHS = {
  brain: '🧠',
  rocket: '🚀',
  spark: '✨',
  thumbsUp: '👍',
} as const;

/**
 * A light, original Telegram-style sticker reaction. Motion is limited to the
 * first 12 frames after arrival, then becomes perfectly static for readability.
 */
const ChatSticker: React.FC<{
  kind: keyof typeof STICKER_GLYPHS;
  progress: number;
  height: number;
  out: boolean;
}> = ({ kind, progress, height, out }) => {
  const enter = Math.max(0, Math.min(1, progress));
  const scale = 0.76 + enter * 0.24;
  const rotation = (1 - enter) * (out ? 8 : -8);
  const size = Math.round(height * 0.072);
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.32),
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: Math.round(size * 0.7),
        lineHeight: 1,
        transform: `scale(${scale}) rotate(${rotation}deg)`,
        background: out
          ? 'linear-gradient(135deg, rgba(57,150,236,0.22), rgba(57,150,236,0.04))'
          : 'linear-gradient(135deg, rgba(255,255,255,0.88), rgba(255,255,255,0.48))',
        border: out ? '1px solid rgba(57,150,236,0.32)' : '1px solid rgba(31,69,99,0.10)',
        boxShadow: '0 5px 14px rgba(24,56,84,0.17)',
      }}
      aria-label={`${kind} sticker`}
    >
      {STICKER_GLYPHS[kind]}
    </div>
  );
};

const Cursor: React.FC<{ x: number; y: number; size: number; pressed: boolean }> = ({
  x,
  y,
  size,
  pressed,
}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      width: size,
      height: size,
      transform: `scale(${pressed ? 0.86 : 1})`,
      transformOrigin: '20% 20%',
      pointerEvents: 'none',
      zIndex: 40,
      filter: 'drop-shadow(0 3px 6px rgba(0,0,0,0.55))',
    }}
  >
    <svg viewBox="0 0 24 24" width={size} height={size}>
      <path d="M5 2.5L18.5 12.2L12.4 13.1L15.6 20.2L12.9 21.4L9.7 14.2L5 18.4Z" fill="#FFFFFF" />
      <path
        d="M5 2.5L18.5 12.2L12.4 13.1L15.6 20.2L12.9 21.4L9.7 14.2L5 18.4Z"
        fill="none"
        stroke="rgba(0,0,0,0.55)"
        strokeWidth={1.1}
        strokeLinejoin="round"
      />
    </svg>
  </div>
);

/**
 * The doodle wallpaper. Telegram's light theme is never flat — a plain fill is
 * a tell. The real one is line-art doodles (cats, planes, cups); these are
 * simplified vector glyphs tiled in a repeating group, which reads correctly at
 * the size a phone screen occupies in a 9:16 frame. Polka dots did not: review
 * flagged them as "simple polka-dot pattern, not Telegram's vector line-art".
 */
const Wallpaper: React.FC<{ color: string; tile: number }> = ({ color, tile }) => {
  const s = 100; // glyph space; the whole group is scaled by `tile`
  const stroke = {
    fill: 'none',
    stroke: color,
    strokeWidth: 2.4,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  };
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
      <svg
        width="100%"
        height="100%"
        style={{ position: 'absolute', inset: 0 }}
        aria-hidden
      >
        <defs>
          <pattern id="tgdoodle" width={tile} height={tile} patternUnits="userSpaceOnUse">
            <g transform={`scale(${tile / s})`}>
              {/* paper plane */}
              <path d="M8 22L34 12L24 34L21 26Z" {...stroke} />
              {/* cup */}
              <path d="M58 12H76V22a9 9 0 01-9 9 9 9 0 01-9-9Z" {...stroke} />
              <path d="M76 15h4a4 4 0 010 8h-4" {...stroke} />
              {/* cat face */}
              <circle cx="22" cy="66" r="10" {...stroke} />
              <path d="M14 58l2-6 5 4M30 58l-2-6-5 4" {...stroke} />
              <circle cx="19" cy="65" r="1.4" fill={color} />
              <circle cx="25" cy="65" r="1.4" fill={color} />
              {/* heart */}
              <path
                d="M70 78c-6-4-10-7-10-11a5 5 0 019-3 5 5 0 019 3c0 4-4 7-10 11Z"
                {...stroke}
              />
              {/* stars */}
              <path d="M46 44l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" {...stroke} />
              <circle cx="88" cy="52" r="2.4" fill={color} />
              <circle cx="6" cy="42" r="1.8" fill={color} />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#tgdoodle)" />
      </svg>
    </div>
  );
};

export const TgChat: React.FC<BaseSceneProps> = ({
  title,
  contactName,
  contactStatus,
  messages,
  accentColor,
  motion,
  safeArea = 'platform',
  compose,
  typing = true,
  showCursor = true,
  showInputBar = true,
  sendAtProgress = 0.72,
  tgTheme = 'light',
  datePill,
  isGroup = false,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const TG = THEMES[tgTheme === 'dark' ? 'dark' : 'light'];
  const accent = accentColor || TG.accent;

  const list: ChatMessage[] = Array.isArray(messages) && messages.length
    ? (messages as ChatMessage[])
    : [
        { from: 'Аня', text: 'Привет! Видел новую модель?', time: '14:02' },
        { from: 'me', text: 'Ага, уже запустил локально', time: '14:03', out: true, read: true },
        { from: 'Аня', text: 'И как? Влезает в 12 гигов?', time: '14:03' },
      ];

  const animate = resolveMotion(motion, fps, 'reveal');

  const bubbleFont = Math.round(height * 0.0198);
  const metaFont = Math.round(height * 0.0126);
  // Wider than the old 0.76: at 0.76 a line the real client fits on one row
  // ("хз, я юзаю, норм вроде всё с ним") wrapped onto two.
  const maxBubble = safe.width * 0.84;

  // ---------------------------------------------------------------- compose
  const composeText = typeof compose === 'string' ? compose : '';
  const hasCompose = composeText.length > 0;

  // Send lands at `sendAtProgress` of the scene; clamped so a very short scene
  // still leaves room for the bubble to land, and a very long one does not sit
  // on an idle input bar for seconds.
  const sendFrame = Math.round(
    durationInFrames * Math.max(0.25, Math.min(0.9, sendAtProgress))
  );
  // The cursor starts travelling shortly before the press.
  const travelFrames = Math.min(26, Math.round(durationInFrames * 0.16));
  const cursorStart = sendFrame - travelFrames;
  const pressFrames = 7;

  // Typing fills everything before the cursor starts moving.
  const typeStart = Math.round(durationInFrames * 0.06);
  const typeEnd = Math.max(typeStart + 1, cursorStart - 4);
  const typedChars = !hasCompose
    ? 0
    : typing === false
      ? composeText.length
      : Math.round(
          interpolate(frame, [typeStart, typeEnd], [0, composeText.length], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })
        );
  const typedText = composeText.slice(0, typedChars);
  const isTyping = hasCompose && typing !== false && frame >= typeStart && frame < typeEnd;

  const sent = hasCompose && frame >= sendFrame;
  const pressed = hasCompose && frame >= sendFrame - 2 && frame < sendFrame + pressFrames;

  // Thread = incoming list, plus the composed message once it has been sent.
  // The composed bubble needs a clock like any other: an empty `time` left the
  // last bubble showing a bare tick, which no real client does. Default to the
  // last message's time so the run stays coherent.
  const composeTime = list.length ? (list[list.length - 1].time ?? '') : '';
  const thread: ChatMessage[] = sent
    ? [...list, { text: composeText, out: true, read: false, time: composeTime }]
    : list;

  // Stagger sized to the scene: a fixed per-message delay either runs off the
  // end of a short scene or leaves a long one half empty. When composing, the
  // pre-existing messages must all be on screen before typing starts.
  const staggerBudget = hasCompose ? typeStart : durationInFrames * 0.55;
  const stagger = Math.min(18, Math.max(6, staggerBudget / Math.max(1, list.length)));

  const barHeight = Math.round(height * 0.062);
  // The bar sits on the SCREEN's bottom edge, not the safe area's. Anchoring it
  // to safe.top + safe.height left a fifth of the frame as bare wallpaper below
  // it — flagged in review, and obviously wrong for a client whose composer is
  // flush above the navigation bar. Nested in a PhoneMockup the safe area is
  // 'loose', so this now lands on the phone's screen edge as intended.
  const barTop = height - barHeight;
  // Send button centre — the cursor's destination and the press target.
  const sendSize = Math.round(barHeight * 0.72);
  const sendCx = width - sendSize / 2 - Math.round(safe.left * 0.7);
  const sendCy = barTop + barHeight / 2;

  const cursorSize = Math.round(height * 0.032);
  // Travels from lower-left of the bar to the send button on an ease-out, so it
  // decelerates into the target the way a real pointer does.
  const travel = interpolate(frame, [cursorStart, sendFrame], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: (t) => 1 - Math.pow(1 - t, 3),
  });
  const cursorX = interpolate(travel, [0, 1], [safe.left + safe.width * 0.34, sendCx - cursorSize * 0.18]);
  const cursorY = interpolate(travel, [0, 1], [barTop + barHeight * 1.15, sendCy - cursorSize * 0.16]);

  const avatarSize = Math.round(height * 0.032);
  const iconSize = Math.round(height * 0.024);
  const initial = (contactName || title || 'Аня').trim().charAt(0).toUpperCase();
  // Full-width action bar height, sized like the real one (icon + padding).
  const headerH = Math.round(height * 0.058);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: TG.bg,
        overflow: 'hidden',
        fontFamily: TG_FONT,
      }}
    >
      <Wallpaper color={TG.doodle} tile={Math.round(width * 0.17)} />

      {/* ------------------------------------------------------- chat header
          EDGE TO EDGE. The real Android action bar spans the full width and is
          flush with the top; rendering it as a floating rounded card inset by the
          safe area was flagged in review as an immediate tell. It sits outside the
          safe-area column for that reason, and the thread below is padded by its
          height so no bubble hides underneath. */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width,
          height: headerH,
          display: 'flex',
          alignItems: 'center',
          gap: Math.round(width * 0.026),
          padding: `0 ${safe.left}px`,
          boxSizing: 'border-box',
          backgroundColor: TG.header,
          boxShadow: TG.shadow,
          zIndex: 10,
        }}
      >
        {/* back arrow */}
        <svg width={iconSize} height={iconSize} viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
          <path
            d="M20 12H4M4 12L10.5 5.5M4 12L10.5 18.5"
            fill="none"
            stroke={TG.headerText}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>

        <div
          style={{
            width: avatarSize,
            height: avatarSize,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${accent}, #8FB8E0)`,
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF',
            fontSize: Math.round(avatarSize * 0.46),
            fontWeight: 600,
          }}
        >
          {initial}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 0, flex: 1, minWidth: 0 }}>
          <span
            style={{
              fontSize: Math.round(height * 0.0185),
              fontWeight: 600,
              color: TG.headerText,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              lineHeight: 1.25,
            }}
          >
            {contactName || title || 'Аня'}
          </span>
          {(contactStatus ?? 'в сети') !== '' && (
            <span
              style={{
                fontSize: metaFont,
                color: isTyping ? accent : TG.headerMeta,
                lineHeight: 1.25,
              }}
            >
              {/* While the user types, Telegram shows "печатает…" in the header —
                  the detail that makes the mockup read as live. */}
              {isTyping ? 'печатает…' : (contactStatus ?? 'в сети')}
            </span>
          )}
        </div>

        {/* call + menu, right-aligned like the real header */}
        <svg width={iconSize} height={iconSize} viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
          <path
            d="M6.6 3.5c.6 0 1.1.4 1.3 1l.8 2.6c.2.6 0 1.2-.5 1.6l-1.2.9a12 12 0 005.4 5.4l.9-1.2c.4-.5 1-.7 1.6-.5l2.6.8c.6.2 1 .7 1 1.3v2.4c0 .9-.8 1.6-1.7 1.5C10.3 19.6 4.4 13.7 3.6 5.2 3.5 4.3 4.2 3.5 5.1 3.5z"
            fill={TG.headerMeta}
          />
        </svg>
        <svg width={iconSize} height={iconSize} viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
          <circle cx="12" cy="5" r="1.9" fill={TG.headerMeta} />
          <circle cx="12" cy="12" r="1.9" fill={TG.headerMeta} />
          <circle cx="12" cy="19" r="1.9" fill={TG.headerMeta} />
        </svg>
      </div>

      <div
        style={{
          position: 'absolute',
          top: Math.max(safe.top, headerH),
          left: safe.left,
          width: safe.width,
          height: safe.height - Math.max(0, headerH - safe.top),
          display: 'flex',
          flexDirection: 'column',
          boxSizing: 'border-box',
        }}
      >
        {/* ------------------------------------------------------------ thread */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            paddingTop: Math.round(height * 0.012),
            // Clear the composer, which is now anchored to the screen bottom
            // rather than to the safe area.
            paddingBottom:
              hasCompose && showInputBar
                ? Math.max(8, safe.top + safe.height - barTop + Math.round(height * 0.008))
                : 8,
          }}
        >
          {datePill && (
            <div
              style={{
                alignSelf: 'center',
                marginBottom: Math.round(height * 0.012),
                padding: `${Math.round(height * 0.004)}px ${Math.round(width * 0.022)}px`,
                borderRadius: 999,
                backgroundColor: TG.pill,
                color: TG.pillText,
                fontSize: metaFont,
                fontWeight: 500,
                opacity: animate(frame, 0, 1),
              }}
            >
              {datePill}
            </div>
          )}

          {thread.map((m, i) => {
            const isComposed = sent && i === thread.length - 1;
            // The composed bubble has its own launch animation starting at the
            // press; the rest keep the stagger.
            const appear = isComposed
              ? animate(frame - sendFrame, 0, 1)
              : animate(frame - i * stagger, 0, 1);
            const out = Boolean(m.out);
            const text = m.text ?? '';
            const isSticker = Boolean(m.sticker);
            const wide = estimateWidth(text, bubbleFont) > maxBubble * 0.8;

            // GROUPING. A run of messages from the same sender is one visual
            // block: only the last bubble gets a tail, the inner corners are
            // squared off, and the gap inside a run is tighter than between
            // runs. Giving every bubble a tail was one of the loudest tells.
            const prev = thread[i - 1];
            const next = thread[i + 1];
            const firstOfRun = !prev || Boolean(prev.out) !== out;
            const lastOfRun = !next || Boolean(next.out) !== out;
            const R = Math.round(height * 0.0095);
            const rSmall = Math.round(R * 0.34);
            const tailSize = Math.round(R * 0.85);

            const radius = out
              ? {
                  borderTopLeftRadius: R,
                  borderBottomLeftRadius: R,
                  borderTopRightRadius: firstOfRun ? R : rSmall,
                  // The tail is glued to this corner, so it must be square —
                  // a rounded corner leaves a visible notch between bubble and nib.
                  borderBottomRightRadius: lastOfRun ? 0 : rSmall,
                }
              : {
                  borderTopRightRadius: R,
                  borderBottomRightRadius: R,
                  borderTopLeftRadius: firstOfRun ? R : rSmall,
                  borderBottomLeftRadius: lastOfRun ? 0 : rSmall,
                };

            const bubbleBg = out ? TG.bubbleOut : TG.bubbleIn;
            const metaColor = out ? TG.metaOut : TG.metaIn;
            // Reserve inline room so the time+ticks can sit on the SAME line as
            // a short message, indented into the text flow, the way the real
            // client lays it out. Without this every bubble is a line too tall.
            const metaW = Math.round(
              (m.time ?? '').length * metaFont * 0.56 + (out ? metaFont * 1.5 : 0) + metaFont * 0.6
            );

            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: out ? 'flex-end' : 'flex-start',
                  marginTop: i === 0 ? 0 : firstOfRun ? Math.round(height * 0.0062) : Math.round(height * 0.0016),
                  opacity: appear,
                  // Bubbles rise into place from the side they belong to; the
                  // composed one launches upward out of the input field.
                  transform: isComposed
                    ? `translateY(${(1 - appear) * 46}px) scale(${0.9 + appear * 0.1})`
                    : `translate(${(1 - appear) * (out ? 26 : -26)}px, ${(1 - appear) * 12}px)`,
                }}
              >
                {isSticker && m.sticker ? (
                  <ChatSticker
                    kind={m.sticker}
                    progress={Math.min(1, Math.max(0, (frame - (isComposed ? sendFrame : i * stagger)) / 12))}
                    height={height}
                    out={out}
                  />
                ) : (
                <div
                  style={{
                    position: 'relative',
                    maxWidth: maxBubble,
                    minWidth: wide ? maxBubble * 0.5 : undefined,
                    backgroundColor: bubbleBg,
                    color: out ? TG.textOut : TG.textIn,
                    ...radius,
                    padding: `${Math.round(height * 0.0042)}px ${Math.round(width * 0.022)}px ${Math.round(height * 0.0042)}px`,
                    fontSize: bubbleFont,
                    lineHeight: 1.31,
                    boxSizing: 'border-box',
                    boxShadow: TG.shadow,
                    // The tail hangs outside the bubble box, so the run must be
                    // inset by the nib's width or it would be clipped by the
                    // thread column.
                    marginRight: out ? tailSize : 0,
                    marginLeft: !out ? tailSize : 0,
                  }}
                >
                  {/* Sender name belongs to GROUP chats only. Real Telegram never
                      labels the other party inside a 1-on-1 thread — their name
                      is already in the header. `isGroup` opts in. */}
                  {!out && isGroup && m.from && m.from !== 'me' && firstOfRun && (
                    <div
                      style={{
                        fontSize: metaFont,
                        fontWeight: 600,
                        color: accent,
                        marginBottom: 2,
                      }}
                    >
                      {m.from}
                    </div>
                  )}
                  <span>
                    {text}
                    {/* inline spacer that keeps the last line clear of the meta */}
                    <span style={{ display: 'inline-block', width: metaW, height: 1 }} />
                  </span>
                  <div
                    style={{
                      position: 'absolute',
                      right: Math.round(width * 0.02),
                      bottom: Math.round(height * 0.005),
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      fontSize: metaFont,
                      color: metaColor,
                      lineHeight: 1,
                    }}
                  >
                    {m.time ?? ''}
                    {out && <Tick read={Boolean(m.read)} color={TG.tick} size={metaFont * 1.15} />}
                  </div>

                  {lastOfRun && <Tail out={out} color={bubbleBg} size={tailSize} />}
                </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* --------------------------------------------------------- input bar
          EDGE TO EDGE, like the header: the real bar is a full-width strip at the
          bottom of the screen, not a floating capsule inset from the sides. */}
      {hasCompose && showInputBar && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: barTop,
            width,
            height: barHeight,
            backgroundColor: TG.bar,
            display: 'flex',
            alignItems: 'center',
            gap: Math.round(barHeight * 0.2),
            padding: `0 ${Math.round(safe.left * 0.7)}px`,
            boxSizing: 'border-box',
            zIndex: 20,
            boxShadow: TG.shadow,
          }}
        >
          {/* emoji button */}
          <svg width={barHeight * 0.42} height={barHeight * 0.42} viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="9.2" fill="none" stroke={TG.barIcon} strokeWidth="1.7" />
            <circle cx="9" cy="10" r="1.25" fill={TG.barIcon} />
            <circle cx="15" cy="10" r="1.25" fill={TG.barIcon} />
            <path d="M8.2 14.2C9.3 15.6 10.6 16.2 12 16.2C13.4 16.2 14.7 15.6 15.8 14.2"
              fill="none" stroke={TG.barIcon} strokeWidth="1.7" strokeLinecap="round" />
          </svg>

          {/* the field: typed text, or the placeholder before typing starts */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              fontSize: Math.round(barHeight * 0.34),
              color: !sent && typedChars > 0 ? TG.headerText : TG.placeholder,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              minWidth: 0,
            }}
          >
            <span
              style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {/* Sent: the field returns to the placeholder, exactly as the real
                  client does. Blanking it entirely (opacity 0) left an empty
                  composer, which no real screenshot ever shows. */}
              {sent || typedChars === 0 ? 'Сообщение' : typedText}
            </span>
            {/* caret — blinks on a 30-frame cycle while the field has focus */}
            {!sent && typedChars > 0 && (
              <span
                style={{
                  display: 'inline-block',
                  width: 2,
                  height: Math.round(barHeight * 0.4),
                  marginLeft: 2,
                  backgroundColor: accent,
                  opacity: frame % 30 < 16 ? 1 : 0,
                }}
              />
            )}
          </div>

          {/* attachment */}
          <svg width={barHeight * 0.42} height={barHeight * 0.42} viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
            <path
              d="M16.5 6.5L8.9 14.1a2.4 2.4 0 003.4 3.4l7.2-7.2a4 4 0 00-5.7-5.7l-7.4 7.4a5.6 5.6 0 007.9 7.9l6.4-6.4"
              fill="none"
              stroke={TG.barIcon}
              strokeWidth="1.7"
              strokeLinecap="round"
            />
          </svg>

          {/* Composer action: microphone while the field is empty, send once
              there is text — the real client swaps them, and showing a send
              button over an empty field is a tell. It stays the click target
              either way, so the cursor still lands on it. */}
          <div
            style={{
              width: sendSize,
              height: sendSize,
              borderRadius: '50%',
              backgroundColor: accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              // Press feedback: dips and brightens under the cursor.
              transform: `scale(${pressed ? 0.88 : 1})`,
              boxShadow: pressed
                ? `0 0 0 ${Math.round(sendSize * 0.18)}px ${accent}33`
                : '0 1px 4px rgba(16,35,47,0.28)',
            }}
          >
            {!sent && typedChars > 0 ? (
              <svg width={sendSize * 0.52} height={sendSize * 0.52} viewBox="0 0 24 24">
                <path d="M3.2 11.4L20 4.2L13.2 20.6L11 13.6Z" fill="#FFFFFF" />
              </svg>
            ) : (
              <svg width={sendSize * 0.5} height={sendSize * 0.5} viewBox="0 0 24 24">
                <rect x="9" y="2.6" width="6" height="11.2" rx="3" fill="#FFFFFF" />
                <path
                  d="M6 11.4a6 6 0 0012 0"
                  fill="none"
                  stroke="#FFFFFF"
                  strokeWidth="1.9"
                  strokeLinecap="round"
                />
                <path d="M12 17.4V21" stroke="#FFFFFF" strokeWidth="1.9" strokeLinecap="round" />
              </svg>
            )}
          </div>
        </div>
      )}

      {/* cursor rides above everything, including the bar */}
      {hasCompose && showCursor && frame >= cursorStart && (
        <Cursor x={cursorX} y={cursorY} size={cursorSize} pressed={pressed} />
      )}
    </div>
  );
};

export default TgChat;
