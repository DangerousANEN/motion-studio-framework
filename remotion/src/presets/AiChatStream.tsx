import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';
import { settleBy } from '../lib/pacing';

/**
 * AiChatStream — an LLM chat with the response streaming token by token.
 *
 * Reads: messages[]{from,text,time,out}, title, response
 *
 * The assistant reply types out at a tokens-per-frame pace derived from the
 * scene length, not a fixed delay: a fixed rate either overruns a short scene
 * or crawls through a long one. The cursor blinks on a deterministic square
 * wave (frame % 24), so it is stable across out-of-order renders.
 */

const FONT = '"Inter", "SF Pro Display", -apple-system, sans-serif';

const AI = {
  bg: '#0E1117',
  user: '#232A37',
  ai: '#151B26',
  text: '#E8EAED',
  muted: '#7C8698',
  accent: '#7B8CFF',
  border: 'rgba(255,255,255,0.06)',
};

interface Msg {
  from?: string;
  text?: string;
  out?: boolean;
}

const estimateChars = (text: string): number => text.length;

export const AiChatStream: React.FC<BaseSceneProps> = ({
  title,
  messages,
  response,
  accentColor = AI.accent,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);

  const history: Msg[] = Array.isArray(messages) && messages.length
    ? (messages as Msg[])
    : [{ from: 'me', text: 'Объясни KV-кэш простыми словами', out: true }];
  const reply = response ?? 'KV-кэш — это память, куда модель складывает уже прочитанные токены, чтобы не перечитывать весь контекст заново на каждом шаге генерации.';

  const appear = resolveMotion(motion, fps, 'reveal');
  const headerIn = appear(frame, 0, 1);

  // Stream the reply across most of the scene, starting after the history lands.
  //
  // `streamDur` was `durationInFrames - startAt - 4`, i.e. the stream finished 4
  // frames before the cut — 0.07s of dwell on the answer that IS the scene. At
  // 90% of a 180-frame scene the reply still read "...проседает после" with the
  // sentence unfinished, which looks like a truncation bug rather than a stream.
  // The typing cursor is the only thing distinguishing the two, and it blinks off
  // half the time.
  //
  // Now the last character lands at settleBy(), so the completed answer plus its
  // token footer are readable for MIN_DWELL_SEC.
  const startAt = Math.min(durationInFrames * 0.28, 30);
  const streamDur = Math.max(1, settleBy(durationInFrames, fps) - startAt);
  const total = estimateChars(reply);
  const shown = Math.max(0, Math.min(total, Math.round(((frame - startAt) / streamDur) * total)));
  const cursorOn = frame % 24 < 14;

  const userFont = Math.round(height * 0.019);
  const replyFont = Math.round(height * 0.02);

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: AI.bg, overflow: 'hidden' }}>
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
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '6px 2px 16px',
            borderBottom: `1px solid ${AI.border}`,
          }}
        >
          <div
            style={{
              width: Math.round(height * 0.026),
              height: Math.round(height * 0.026),
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${accentColor}, #B26BFF)`,
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontFamily: FONT,
              fontSize: Math.round(height * 0.018),
              fontWeight: 700,
              color: AI.text,
              opacity: headerIn,
            }}
          >
            {title || 'Нейросеть'}
          </span>
          <span
            style={{
              fontFamily: FONT,
              fontSize: Math.round(height * 0.013),
              color: accentColor,
              border: `1px solid ${accentColor}55`,
              borderRadius: 6,
              padding: '2px 8px',
              opacity: headerIn,
            }}
          >
            GPT
          </span>
        </div>

        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            gap: 12,
            paddingBottom: 6,
          }}
        >
          {history.map((m, i) => {
            const hIn = appear(frame - 8 - i * 8, 0, 1);
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  opacity: hIn,
                  transform: `translateY(${(1 - hIn) * 10}px)`,
                }}
              >
                <div
                  style={{
                    maxWidth: safe.width * 0.8,
                    backgroundColor: AI.user,
                    border: `1px solid ${AI.border}`,
                    borderRadius: 14,
                    borderBottomRightRadius: 4,
                    padding: '10px 14px',
                    fontFamily: FONT,
                    fontSize: userFont,
                    lineHeight: 1.35,
                    color: AI.text,
                  }}
                >
                  {m.text}
                </div>
              </div>
            );
          })}

          {/* streaming assistant reply */}
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
              style={{
                maxWidth: safe.width * 0.88,
                backgroundColor: AI.ai,
                border: `1px solid ${AI.border}`,
                borderRadius: 14,
                borderBottomLeftRadius: 4,
                padding: '12px 14px',
                fontFamily: FONT,
                fontSize: replyFont,
                lineHeight: 1.42,
                color: AI.text,
                opacity: appear(frame - 20, 0, 1),
              }}
            >
              {shown > 0 && reply.slice(0, shown)}
              {/* cursor is drawn with a span, so its width does not reflow text */}
              <span
                style={{
                  display: 'inline-block',
                  width: 3,
                  height: replyFont * 1.05,
                  marginLeft: 3,
                  verticalAlign: 'text-bottom',
                  backgroundColor: accentColor,
                  opacity: cursorOn && shown < total ? 1 : 0,
                }}
              />
              {shown >= total && (
                <div
                  style={{
                    marginTop: 8,
                    fontFamily: FONT,
                    fontSize: Math.round(height * 0.014),
                    color: AI.muted,
                  }}
                >
                  ✓ {total} токенов · 0.4 с
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
