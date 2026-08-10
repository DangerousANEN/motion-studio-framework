import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';

/**
 * TgChat — a Telegram thread with bubbles arriving one after another.
 *
 * Reads: messages[]{from,text,time,read}, title
 *
 * The messages arrive on a stagger rather than all at once: a chat that appears
 * fully formed reads as a screenshot, and the whole point of animating it is to
 * show the exchange happening. Each bubble also measures its own width from its
 * text so a long message wraps instead of overflowing the safe box — Russian
 * strings run ~1.4x their English equivalents and were the usual cause.
 */

const FONT = '"Inter", "SF Pro Display", -apple-system, sans-serif';

const TG = {
  bg: '#17212B',
  bubbleIn: '#182533',
  bubbleOut: '#2B5278',
  text: '#FFFFFF',
  meta: '#6D7F8F',
  header: '#17212B',
  accent: '#5288C1',
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

const Tick: React.FC<{ read: boolean; color: string }> = ({ read, color }) => (
  <svg width={16} height={11} viewBox="0 0 16 11" style={{ marginLeft: 4 }}>
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

export const TgChat: React.FC<BaseSceneProps> = ({
  title,
  messages,
  accentColor = TG.accent,
  motion,
  safeArea = 'platform',
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
        { from: 'me', text: 'Впритык, но работает', time: '14:04', out: true, read: true },
      ];

  const animate = resolveMotion(motion, fps, 'reveal');

  const bubbleFont = Math.round(height * 0.021);
  const metaFont = Math.round(height * 0.013);
  const maxBubble = safe.width * 0.74;
  // Stagger sized to the scene: a fixed per-message delay either runs off the
  // end of a short scene or leaves a long one half empty.
  const stagger = Math.min(18, Math.max(8, (durationInFrames * 0.55) / list.length));

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: TG.bg,
        overflow: 'hidden',
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
                fontFamily: FONT,
                fontSize: Math.round(height * 0.019),
                fontWeight: 700,
                color: TG.text,
              }}
            >
              {title || 'Аня'}
            </span>
            <span style={{ fontFamily: FONT, fontSize: metaFont, color: TG.meta }}>
              в сети
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
            paddingBottom: 8,
          }}
        >
          {list.map((m, i) => {
            const appear = animate(frame - i * stagger, 0, 1);
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
                  // Bubbles rise into place from the side they belong to.
                  transform: `translate(${(1 - appear) * (out ? 26 : -26)}px, ${
                    (1 - appear) * 12
                  }px)`,
                }}
              >
                <div
                  style={{
                    maxWidth: maxBubble,
                    minWidth: wide ? maxBubble * 0.5 : undefined,
                    backgroundColor: out ? TG.bubbleOut : TG.bubbleIn,
                    color: TG.text,
                    borderRadius: 14,
                    borderBottomRightRadius: out ? 4 : 14,
                    borderBottomLeftRadius: out ? 14 : 4,
                    padding: '10px 13px 8px',
                    fontFamily: FONT,
                    fontSize: bubbleFont,
                    lineHeight: 1.32,
                    boxSizing: 'border-box',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.28)',
                  }}
                >
                  {!out && m.from && (
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
                    {out && <Tick read={Boolean(m.read)} color="#6FD05C" />}
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
