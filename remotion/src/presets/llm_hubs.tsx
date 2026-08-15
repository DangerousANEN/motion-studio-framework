import React from 'react';
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import type { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea } from '../lib/safeArea';
import { Backdrop } from '../theme/Backdrop';
import { useStyle } from '../theme/StyleContext';

/** A production CTA with real supplied channel branding and no invented counts. */
export const LlmHubsCTA: React.FC<BaseSceneProps> = (props) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const enter = spring({ frame, fps, config: { damping: 16, stiffness: 140, mass: 0.8 } });
  const glow = interpolate(frame, [0, fps * 0.45, fps * 1.8], [0, 0.42, 0.16], { extrapolateRight: 'clamp' });
  const avatarSize = Math.min(Math.round(safe.width * 0.32), Math.round(height * 0.26));
  const title = props.title || 'Больше практики с LLM';
  const subtitle = props.text || 'Подписывайтесь на канал — новые инструменты, промпты и способы экономить.';

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', background: theme.bg }}>
      <Backdrop />
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(circle at 50% 42%, ${accent}${Math.round(glow * 255).toString(16).padStart(2, '0')} 0%, transparent 48%)` }} />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', boxSizing: 'border-box', opacity: enter, transform: `translateY(${Math.round((1 - enter) * height * 0.05)}px)` }}>
        <div style={{ width: avatarSize, height: avatarSize, borderRadius: '50%', padding: Math.max(5, Math.round(avatarSize * 0.035)), background: `linear-gradient(135deg, ${accent}, #B7A4FF)`, boxShadow: `0 0 ${Math.round(avatarSize * 0.28)}px ${accent}88`, boxSizing: 'border-box' }}>
          <Img src={staticFile('brand/llm-hubs-avatar.jpg')} style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover', display: 'block' }} />
        </div>
        <div style={{ marginTop: Math.round(height * 0.040), color: accent, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * 0.024), letterSpacing: Math.round(width * 0.005), textTransform: 'uppercase' }}>LLM HUBS</div>
        <div style={{ marginTop: Math.round(height * 0.015), color: theme.text, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * 0.046), lineHeight: 1.04, maxWidth: safe.width * 0.95 }}>{title}</div>
        <div style={{ marginTop: Math.round(height * 0.022), color: theme.muted, fontFamily: fonts.body, fontWeight: 600, fontSize: Math.round(height * 0.023), lineHeight: 1.32, maxWidth: safe.width * 0.90 }}>{subtitle}</div>
        <div style={{ marginTop: Math.round(height * 0.042), borderRadius: 999, background: accent, color: theme.bg, fontFamily: fonts.display, fontWeight: 900, padding: `${Math.round(height * 0.016)}px ${Math.round(width * 0.052)}px`, fontSize: Math.round(height * 0.033), boxShadow: `0 ${Math.round(height * 0.010)}px ${Math.round(height * 0.025)}px ${accent}66` }}>@llm_hubs</div>
      </div>
    </div>
  );
};
