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
 *        compose, typing, showCursor, showInputBar, sendAtProgress
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
 * GEOMETRY NOTE
 * -------------
 * Bubble corner radii, the input bar height and the tail placement follow the
 * reference screenshot: tails on the bottom-outer corner, 6% of frame height
 * for the bar, attachment + record button on the right of the field.
 */

const TG = {
  bg: '#0E1621',
  bubbleIn: '#182533',
  bubbleOut: '#2B5278',
  text: '#FFFFFF',
  meta: '#6D7F8F',
  bar: '#17212B',
  field: '#242F3D',
  accent: '#5288C1',
  tick: '#5FD3F3',
};

interface ChatMessage {
  from?: string;
  text?: string;
  time?: string;
  read?: boolean;
  out?: boolean;
}

/** Rough width estimate so a bubble can size itself without a DOM measure. */
const estimateWidth = (text: string, fontSize: number): number =>
  Math.min(text.length * fontSize * 0.54, 10_000);

const Tick: React.FC<{ read: boolean; color: string; size?: number }> = ({
  read,
  color,
  size = 16,
}) => (
  <svg width={size} height={(size * 11) / 16} viewBox="0 0 16 11" style={{ marginLeft: 4 }}>
    <path
      d="M1 5.5L4.5 9L11 2"
      stroke={color}
      strokeWidth={1.6}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {read && (
      <path
        d="M6 9L12.5 2"
        stroke={color}
        strokeWidth={1.6}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    )}
  </svg>
);

/**
 * Mouse pointer, drawn rather than imported so it needs no asset and scales
 * with the frame. The shadow is what sells it as sitting *above* the UI.
 */
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

export const TgChat: React.FC<BaseSceneProps> = ({
  title,
  contactName,
  contactStatus,
  messages,
  accentColor = TG.accent,
  motion,
  safeArea = 'platform',
  compose,
  typing = true,
  showCursor = true,
  showInputBar = true,
  sendAtProgress = 0.72,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);

  const list: ChatMessage[] = Array.isArray(messages) && messages.length
    ? (messages as ChatMessage[])
    : [
        { from: 'Аня', text: 'Привет! Видел новую модель?', time: '14:02' },
        { from: 'me', text: 'Ага, уже запустил локально', time: '14:03', out: true, read: true },
        { from: 'Аня', text: 'И как? Влезает в 12 гигов?', time: '14:03' },
      ];

  const animate = resolveMotion(motion, fps, 'reveal');

  const bubbleFont = Math.round(height * 0.021);
  const metaFont = Math.round(height * 0.013);
  const maxBubble = safe.width * 0.74;

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
  const thread: ChatMessage[] = sent
    ? [...list, { text: composeText, out: true, read: false, time: '' }]
    : list;

  // Stagger sized to the scene: a fixed per-message delay either runs off the
  // end of a short scene or leaves a long one half empty. When composing, the
  // pre-existing messages must all be on screen before typing starts.
  const staggerBudget = hasCompose ? typeStart : durationInFrames * 0.55;
  const stagger = Math.min(18, Math.max(6, staggerBudget / Math.max(1, list.length)));

  const barHeight = Math.round(height * 0.062);
  const barTop = safe.top + safe.height - barHeight;
  // Send button centre — the cursor's destination and the press target.
  const sendSize = Math.round(barHeight * 0.62);
  const sendCx = safe.left + safe.width - sendSize / 2 - Math.round(barHeight * 0.16);
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

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: TG.bg, overflow: 'hidden' }}>
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
        {/* chat header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '10px 4px 18px',
            borderBottom: '1px solid rgba(255,255,255,0.07)',
          }}
        >
          <div
            style={{
              width: Math.round(height * 0.028),
              height: Math.round(height * 0.028),
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${accentColor}, #8FB8E0)`,
              flexShrink: 0,
            }}
          />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span
              style={{
                fontSize: Math.round(height * 0.019),
                fontWeight: 700,
                color: TG.text,
              }}
            >
              {contactName || title || 'Аня'}
            </span>
            <span style={{ fontSize: metaFont, color: TG.meta }}>
              {/* While the user types, Telegram shows "печатает…" in the header —
                  the detail that makes the mockup read as live. */}
              {isTyping ? 'печатает…' : (contactStatus ?? 'в сети')}
            </span>
          </div>
        </div>

        {/* bubbles, bottom-aligned like a real thread */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            gap: 10,
            paddingBottom: hasCompose && showInputBar ? barHeight + 14 : 8,
          }}
        >
          {thread.map((m, i) => {
            const isComposed = sent && i === thread.length - 1;
            // The composed bubble has its own launch animation starting at the
            // press; the rest keep the stagger.
            const appear = isComposed
              ? animate(frame - sendFrame, 0, 1)
              : animate(frame - i * stagger, 0, 1);
            const out = Boolean(m.out);
            const text = m.text ?? '';
            const wide = estimateWidth(text, bubbleFont) > maxBubble * 0.8;

            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: out ? 'flex-end' : 'flex-start',
                  opacity: appear,
                  // Bubbles rise into place from the side they belong to; the
                  // composed one launches upward out of the input field.
                  transform: isComposed
                    ? `translateY(${(1 - appear) * 46}px) scale(${0.9 + appear * 0.1})`
                    : `translate(${(1 - appear) * (out ? 26 : -26)}px, ${(1 - appear) * 12}px)`,
                }}
              >
                <div
                  style={{
                    maxWidth: maxBubble,
                    minWidth: wide ? maxBubble * 0.5 : undefined,
                    backgroundColor: out ? TG.bubbleOut : TG.bubbleIn,
                    color: TG.text,
                    borderRadius: 16,
                    borderBottomRightRadius: out ? 5 : 16,
                    borderBottomLeftRadius: out ? 16 : 5,
                    padding: '10px 13px 8px',
                    fontSize: bubbleFont,
                    lineHeight: 1.32,
                    boxSizing: 'border-box',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.28)',
                  }}
                >
                  {!out && m.from && m.from !== 'me' && (
                    <div
                      style={{
                        fontSize: metaFont,
                        fontWeight: 700,
                        color: accentColor,
                        marginBottom: 3,
                      }}
                    >
                      {m.from}
                    </div>
                  )}
                  <span>{text}</span>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      gap: 2,
                      marginTop: 4,
                      fontSize: metaFont,
                      color: out ? 'rgba(255,255,255,0.62)' : TG.meta,
                    }}
                  >
                    {m.time ?? ''}
                    {out && <Tick read={Boolean(m.read)} color={TG.tick} size={metaFont * 1.1} />}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ------------------------------------------------------- input bar */}
      {hasCompose && showInputBar && (
        <div
          style={{
            position: 'absolute',
            left: safe.left,
            top: barTop,
            width: safe.width,
            height: barHeight,
            backgroundColor: TG.bar,
            borderRadius: barHeight * 0.44,
            display: 'flex',
            alignItems: 'center',
            gap: Math.round(barHeight * 0.2),
            padding: `0 ${Math.round(barHeight * 0.16)}px`,
            boxSizing: 'border-box',
            zIndex: 20,
            boxShadow: '0 -6px 22px rgba(0,0,0,0.35)',
          }}
        >
          {/* emoji button */}
          <svg width={barHeight * 0.42} height={barHeight * 0.42} viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="9.2" fill="none" stroke={TG.meta} strokeWidth="1.7" />
            <circle cx="9" cy="10" r="1.25" fill={TG.meta} />
            <circle cx="15" cy="10" r="1.25" fill={TG.meta} />
            <path d="M8.2 14.2C9.3 15.6 10.6 16.2 12 16.2C13.4 16.2 14.7 15.6 15.8 14.2"
              fill="none" stroke={TG.meta} strokeWidth="1.7" strokeLinecap="round" />
          </svg>

          {/* the field: typed text, or the placeholder before typing starts */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              fontSize: Math.round(barHeight * 0.34),
              color: typedChars > 0 ? TG.text : TG.meta,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              minWidth: 0,
            }}
          >
            <span
              style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                // Sent: the field empties, exactly as the real client does.
                opacity: sent ? 0 : 1,
              }}
            >
              {typedChars > 0 ? typedText : 'Сообщение'}
            </span>
            {/* caret — blinks on a 30-frame cycle while the field has focus */}
            {!sent && typedChars > 0 && (
              <span
                style={{
                  display: 'inline-block',
                  width: 2,
                  height: Math.round(barHeight * 0.4),
                  marginLeft: 2,
                  backgroundColor: accentColor,
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
              stroke={TG.meta}
              strokeWidth="1.7"
              strokeLinecap="round"
            />
          </svg>

          {/* send button — the click target */}
          <div
            style={{
              width: sendSize,
              height: sendSize,
              borderRadius: '50%',
              backgroundColor: accentColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              // Press feedback: dips and brightens under the cursor.
              transform: `scale(${pressed ? 0.88 : 1})`,
              boxShadow: pressed
                ? `0 0 0 ${Math.round(sendSize * 0.18)}px ${accentColor}33`
                : '0 2px 8px rgba(0,0,0,0.4)',
            }}
          >
            <svg width={sendSize * 0.52} height={sendSize * 0.52} viewBox="0 0 24 24">
              <path d="M3.2 11.4L20 4.2L13.2 20.6L11 13.6Z" fill="#FFFFFF" />
            </svg>
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
