import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';
import { useSceneStyle } from '../theme/StyleContext';

/**
 * AiChatStream — provider-branded assistant conversation.
 *
 * A prior generic, almost empty dark chat had no provider identity and streamed
 * a long line character-by-character, which made the whole bubble reflow while
 * it was being read. This version treats a chat as an editorial product card:
 * stable copy, provider avatar, one visible effort decision and a real composer.
 */
const FONT = '"Inter", "SF Pro Display", -apple-system, system-ui, sans-serif';
const DEEPSEEK_BLUE = '#5F7CFF';

type Msg = { from?: string; text?: string; out?: boolean };

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

export const AiChatStream: React.FC<BaseSceneProps> = ({
  title,
  messages,
  response,
  accentColor,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);
  const isDeepSeek = /deepseek/i.test(title ?? '');
  // Series defaults apply a green accent at Scene level. A named provider chat
  // must preserve its blue identity rather than inherit the generic series tint.
  const providerAccent = isDeepSeek ? DEEPSEEK_BLUE : (accentColor ?? DEEPSEEK_BLUE);
  const { theme } = useSceneStyle(undefined, providerAccent);
  const appear = resolveMotion(motion, fps, 'reveal');
  const history = Array.isArray(messages) && messages.length
    ? (messages as Msg[])
    : [{ text: 'Как выбрать effort для задачи?', out: true }];
  const prompt = history.find((item) => item.text)?.text || 'Как выбрать effort для задачи?';
  const answer = response || 'Выбирайте low для простых задач. High или max — только когда нужен глубокий разбор и tools.';

  const shellIn = clamp01(appear(frame, 0, 1));
  const promptIn = clamp01(appear(frame - 7, 0, 1));
  const answerIn = clamp01(appear(frame - 16, 0, 1));
  const chipsIn = clamp01(appear(frame - 25, 0, 1));
  const composerIn = clamp01(appear(frame - 32, 0, 1));
  const cardWidth = Math.min(safe.width * 0.94, 850);
  const offsetY = interpolate(shellIn, [0, 1], [38, 0]);
  const titleText = isDeepSeek ? 'DeepSeek V4 Pro' : (title || 'AI Assistant');
  const subtitle = isDeepSeek ? 'Expert Mode · reasoning controls' : 'Assistant workspace';
  const userFont = Math.round(height * 0.020);
  const answerFont = Math.round(height * 0.022);

  return (
    <div style={{ position: 'absolute', inset: 0, background: theme.bg, overflow: 'hidden', fontFamily: FONT }}>
      <div style={{ position: 'absolute', width: width * 1.1, height: width * 1.1, borderRadius: '50%', left: -width * 0.25, top: safe.top - width * 0.18, background: `radial-gradient(circle, ${providerAccent}2C 0%, transparent 67%)`, filter: 'blur(8px)' }} />
      <div style={{ position: 'absolute', inset: 0, opacity: 0.48, backgroundImage: `linear-gradient(${theme.muted}12 1px, transparent 1px),linear-gradient(90deg, ${theme.muted}12 1px, transparent 1px)`, backgroundSize: `${Math.round(width * 0.09)}px ${Math.round(width * 0.09)}px` }} />

      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: cardWidth, minHeight: Math.round(safe.height * 0.66), boxSizing: 'border-box', borderRadius: Math.round(width * 0.042), overflow: 'hidden', opacity: shellIn, transform: `translateY(${offsetY}px)`, background: `linear-gradient(145deg, ${theme.surface}FA, ${theme.bg}F4)`, border: `1.5px solid ${providerAccent}88`, boxShadow: `0 26px 64px ${theme.shadowColor}A8, 0 0 44px ${providerAccent}22`, display: 'flex', flexDirection: 'column' }}>
          <div style={{ height: Math.round(height * 0.092), padding: `0 ${Math.round(width * 0.038)}px`, display: 'flex', alignItems: 'center', gap: Math.round(width * 0.024), borderBottom: `1px solid ${providerAccent}38`, background: `${theme.bg}8A` }}>
            <div style={{ width: Math.round(height * 0.052), height: Math.round(height * 0.052), borderRadius: Math.round(height * 0.017), background: `linear-gradient(145deg, ${providerAccent}, #9CB0FF)`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#FFFFFF', fontWeight: 900, fontSize: Math.round(height * 0.020), letterSpacing: '-0.08em', boxShadow: `0 0 18px ${providerAccent}88`, flexShrink: 0 }}>DS</div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ color: theme.text, fontSize: Math.round(height * 0.022), lineHeight: 1.05, fontWeight: 850, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{titleText}</div>
              <div style={{ color: providerAccent, fontSize: Math.round(height * 0.014), marginTop: 4, fontWeight: 750, letterSpacing: '0.05em', textTransform: 'uppercase' }}>{subtitle}</div>
            </div>
            <div style={{ border: `1px solid ${providerAccent}77`, color: providerAccent, borderRadius: 999, padding: '5px 9px', fontSize: Math.round(height * 0.013), letterSpacing: '0.05em', fontWeight: 800 }}>ONLINE</div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: Math.round(height * 0.018), padding: `${Math.round(height * 0.030)}px ${Math.round(width * 0.038)}px`, flex: 1, boxSizing: 'border-box', justifyContent: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', opacity: promptIn, transform: `translateY(${Math.round((1 - promptIn) * height * 0.018)}px)` }}>
              <div style={{ maxWidth: '78%', background: `${providerAccent}24`, border: `1px solid ${providerAccent}66`, borderRadius: '18px 18px 5px 18px', padding: `${Math.round(height * 0.014)}px ${Math.round(width * 0.027)}px`, color: theme.text, fontSize: userFont, fontWeight: 650, lineHeight: 1.3 }}>{prompt}</div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: Math.round(width * 0.018), opacity: answerIn, transform: `translateY(${Math.round((1 - answerIn) * height * 0.018)}px)` }}>
              <div style={{ width: Math.round(height * 0.034), height: Math.round(height * 0.034), borderRadius: '50%', background: providerAccent, color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: Math.round(height * 0.013), fontWeight: 900, flexShrink: 0, marginTop: 4 }}>DS</div>
              <div style={{ flex: 1, background: `${theme.bg}C8`, border: `1px solid ${theme.muted}38`, borderRadius: '18px 18px 18px 5px', padding: `${Math.round(height * 0.017)}px ${Math.round(width * 0.027)}px` }}>
                <div style={{ color: theme.text, fontSize: answerFont, fontWeight: 680, lineHeight: 1.3, overflowWrap: 'normal', wordBreak: 'normal' }}>{answer}</div>
                <div style={{ display: 'flex', gap: 8, marginTop: Math.round(height * 0.020), opacity: chipsIn, flexWrap: 'wrap' }}>
                  {['LOW', 'HIGH', 'MAX'].map((effort) => {
                    const active = effort === 'HIGH';
                    return <span key={effort} style={{ borderRadius: 999, padding: '5px 10px', border: `1px solid ${active ? providerAccent : `${theme.muted}55`}`, color: active ? providerAccent : theme.muted, background: active ? `${providerAccent}1C` : 'transparent', fontSize: Math.round(height * 0.014), fontWeight: 850, letterSpacing: '0.08em' }}>{effort}</span>;
                  })}
                </div>
              </div>
            </div>
          </div>

          <div style={{ padding: `${Math.round(height * 0.018)}px ${Math.round(width * 0.038)}px ${Math.round(height * 0.026)}px`, borderTop: `1px solid ${theme.muted}28`, opacity: composerIn }}>
            <div style={{ minHeight: Math.round(height * 0.055), borderRadius: 999, border: `1px solid ${theme.muted}55`, background: `${theme.bg}B8`, display: 'flex', alignItems: 'center', paddingLeft: Math.round(width * 0.024), gap: 10 }}>
              <span style={{ color: theme.muted, fontSize: Math.round(height * 0.017), flex: 1 }}>Спросить про reasoning…</span>
              <div style={{ width: Math.round(height * 0.045), height: Math.round(height * 0.045), borderRadius: '50%', marginRight: 5, background: providerAccent, color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: Math.round(height * 0.022), boxShadow: `0 0 13px ${providerAccent}88` }}>↑</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
