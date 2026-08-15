import React from 'react';
import {
  AbsoluteFill,
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
import { useSceneStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';

const resolveSrc = (src: string) => (src.startsWith('http') || src.startsWith('data:') ? src : staticFile(src));
const clamp = (value: number, low = 0, high = 1) => Math.min(high, Math.max(low, value));

type CursorStep = { x: number; y: number; at?: number; label?: string };

/**
 * ScreenGuide — a real screenshot or recording, framed for tutorials.
 *
 * It supports a deterministic camera path over source material and cursor steps,
 * so the user can supply a recording and the agent can direct attention without
 * baking an arrow into the source file.
 */
export const ScreenGuide: React.FC<BaseSceneProps> = (props) => {
  const {
    src,
    images,
    title,
    subtitle,
    appName,
    urlBar,
    chrome = 'browser',
    fit = 'cover',
    muted = true,
    focusX = 0.5,
    focusY = 0.5,
    focusScale = 1.15,
    panX = 0,
    panY = 0,
    cursorSteps,
    guideText,
    showRec = true,
    accentColor,
  } = props as BaseSceneProps & {
    focusX?: number; focusY?: number; focusScale?: number; panX?: number; panY?: number;
    cursorSteps?: CursorStep[]; guideText?: string;
  };
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent, surface } = useSceneStyle(props.style, accentColor, props.styleConfig);
  const reveal = resolveMotion(props.motion ?? { curve: 'overdamped', duration: 18 }, fps, 'reveal');
  const appear = reveal(frame, 0, 1);
  const still = Array.isArray(images) && images.length ? images[0] : undefined;
  const source = src || still;
  const progress = clamp(frame / Math.max(1, durationInFrames - 1));
  const scale = interpolate(progress, [0, 1], [1.01, Math.max(1, focusScale)], { extrapolateRight: 'clamp' });
  const translateX = (0.5 - clamp(focusX)) * safe.width * (scale - 1) + panX * safe.width * progress;
  const translateY = (0.5 - clamp(focusY)) * safe.height * (scale - 1) + panY * safe.height * progress;
  const steps = Array.isArray(cursorSteps) ? cursorSteps.slice(0, 5) : [];
  const current = steps.reduce<CursorStep | undefined>((latest, step, index) => {
    const at = step.at ?? index / Math.max(1, steps.length);
    return progress >= at ? step : latest;
  }, steps[0]);
  const chromeHeight = Math.round(height * 0.034);

  if (!source) {
    return <AbsoluteFill style={{ background: '#3A0A0A', color: '#FFF', display: 'grid', placeItems: 'center', fontFamily: 'ui-monospace', fontSize: 30 }}>SCREEN GUIDE NEEDS src OR images[0]</AbsoluteFill>;
  }

  return (
    <AbsoluteFill style={{ background: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, display: 'flex', flexDirection: 'column', gap: Math.round(height * 0.018), justifyContent: 'center' }}>
        <div style={{ color: accent, fontFamily: fonts.mono, fontWeight: 800, fontSize: Math.round(height * 0.016), letterSpacing: 2, opacity: appear }}>ИНТЕРАКТИВНЫЙ ГАЙД</div>
        <div style={{ color: theme.text, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * 0.039), lineHeight: 1.05, opacity: appear }}>{title || 'Покажите действие на экране'}</div>
        <div style={{ width: safe.width, height: Math.round(safe.height * 0.61), borderRadius: Math.round(height * 0.018), overflow: 'hidden', background: theme.surface, border: `2px solid ${accent}66`, boxShadow: surface === 'glass' ? `0 24px 80px ${accent}20` : '0 18px 44px rgba(0,0,0,.45)', opacity: appear, transform: `translateY(${(1 - appear) * 20}px)` }}>
          {chrome !== 'none' && <div style={{ height: chromeHeight, display: 'flex', alignItems: 'center', gap: chromeHeight * .24, padding: `0 ${chromeHeight * .4}px`, background: `${theme.surface}EE`, borderBottom: `1px solid ${theme.muted}33` }}>
            {['#FF5F57', '#FEBC2E', '#28C840'].map((color) => <i key={color} style={{ width: chromeHeight * .28, height: chromeHeight * .28, borderRadius: 99, background: color }} />)}
            <div style={{ flex: 1, marginLeft: chromeHeight * .3, padding: `0 ${chromeHeight * .35}px`, lineHeight: `${chromeHeight * .58}px`, borderRadius: 99, color: theme.muted, background: theme.bg, fontFamily: fonts.mono, fontSize: chromeHeight * .34, overflow: 'hidden', whiteSpace: 'nowrap' }}>{urlBar || appName || 'screen-guide'}</div>
            {showRec !== false && <span style={{ color: theme.text, fontFamily: fonts.mono, fontSize: chromeHeight * .33, fontWeight: 800 }}><b style={{ color: '#FF4D5A' }}>●</b> REC</span>}
          </div>}
          <div style={{ height: `calc(100% - ${chrome !== 'none' ? chromeHeight : 0}px)`, position: 'relative', overflow: 'hidden', background: '#050809' }}>
            {src ? <OffthreadVideo src={resolveSrc(src)} muted={muted !== false} style={{ width: '100%', height: '100%', objectFit: fit === 'contain' ? 'contain' : 'cover', transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`, transformOrigin: `${clamp(focusX) * 100}% ${clamp(focusY) * 100}%` }} /> : <Img src={resolveSrc(still as string)} style={{ width: '100%', height: '100%', objectFit: fit === 'contain' ? 'contain' : 'cover', transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`, transformOrigin: `${clamp(focusX) * 100}% ${clamp(focusY) * 100}%` }} />}
            {current && <div style={{ position: 'absolute', left: `${clamp(current.x) * 100}%`, top: `${clamp(current.y) * 100}%`, transform: 'translate(-10%, -8%)', pointerEvents: 'none' }}>
              <div style={{ width: Math.round(height * .033), height: Math.round(height * .044), background: theme.text, clipPath: 'polygon(0 0, 0 100%, 30% 72%, 48% 100%, 64% 91%, 46% 63%, 88% 61%)', filter: `drop-shadow(0 0 8px ${accent})` }} />
              <div style={{ position: 'absolute', left: Math.round(height * .024), top: Math.round(height * .03), width: Math.round(height * .018), height: Math.round(height * .018), borderRadius: 99, background: accent, boxShadow: `0 0 0 ${Math.round(height * .011)}px ${accent}33, 0 0 22px ${accent}` }} />
              {current.label && <div style={{ position: 'absolute', top: Math.round(height * .06), left: Math.round(height * .026), padding: `${Math.round(height * .008)}px ${Math.round(height * .013)}px`, borderRadius: 8, color: theme.bg, background: accent, fontFamily: fonts.body, fontWeight: 800, fontSize: Math.round(height * .016), whiteSpace: 'nowrap' }}>{current.label}</div>}
            </div>}
          </div>
        </div>
        {(guideText || subtitle) && <div style={{ color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * .021), lineHeight: 1.35, opacity: appear }}>{guideText || subtitle}</div>}
      </div>
    </AbsoluteFill>
  );
};

/** Telegram-style voice card with an optional circular video/avatar asset. */
export const TelegramVoiceRound: React.FC<BaseSceneProps> = (props) => {
  const { title, subtitle, contactName, transcript, duration, waveformSeed = 12, avatar, src, accentColor } = props as BaseSceneProps & { avatar?: string };
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useSceneStyle(props.style, accentColor, props.styleConfig);
  const reveal = resolveMotion(props.motion ?? { curve: 'overdamped', duration: 18 }, fps, 'reveal');
  const appear = reveal(frame, 0, 1);
  const total = duration ?? durationInFrames / fps;
  const played = clamp(frame / Math.max(1, durationInFrames - 1));
  const bars = Array.from({ length: 34 }, (_, index) => {
    const base = 0.25 + 0.7 * Math.abs(Math.sin((index + waveformSeed) * .78));
    const active = index / 34 <= played;
    return <i key={index} style={{ width: Math.max(2, safe.width * .008), height: `${base * 100}%`, borderRadius: 99, background: active ? accent : `${theme.muted}55` }} />;
  });
  const portrait = avatar || src;
  return (
    <AbsoluteFill style={{ background: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: Math.round(height * .025) }}>
        <div style={{ color: theme.text, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * .039), opacity: appear }}>{title || 'Голосовое сообщение'}</div>
        <div style={{ background: `${theme.surface}EE`, border: `1.5px solid ${accent}55`, borderRadius: Math.round(height * .026), padding: Math.round(height * .025), display: 'flex', gap: Math.round(width * .03), alignItems: 'center', boxShadow: `0 20px 60px ${accent}18`, opacity: appear, transform: `translateY(${(1 - appear) * 18}px)` }}>
          <div style={{ width: Math.round(height * .15), height: Math.round(height * .15), borderRadius: '50%', overflow: 'hidden', background: `${accent}22`, border: `3px solid ${accent}`, display: 'grid', placeItems: 'center', flexShrink: 0 }}>
            {portrait ? <Img src={resolveSrc(portrait)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <span style={{ color: accent, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * .06) }}>{(contactName || 'TG').slice(0, 1)}</span>}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ color: theme.text, fontFamily: fonts.body, fontWeight: 800, fontSize: Math.round(height * .022) }}>{contactName || 'Telegram'}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: Math.round(width * .015), marginTop: Math.round(height * .014) }}>
              <div style={{ width: Math.round(height * .042), height: Math.round(height * .042), borderRadius: '50%', background: accent, display: 'grid', placeItems: 'center', flexShrink: 0 }}><span style={{ color: theme.bg, fontSize: Math.round(height * .018) }}>▶</span></div>
              <div style={{ height: Math.round(height * .052), flex: 1, display: 'flex', alignItems: 'center', gap: 2 }}>{bars}</div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: Math.round(height * .009), color: theme.muted, fontFamily: fonts.mono, fontSize: Math.round(height * .014) }}><span>0:{String(Math.floor(total * played)).padStart(2, '0')}</span><span>{Math.round(total)} sec</span></div>
          </div>
        </div>
        {(transcript || subtitle) && <div style={{ color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * .022), lineHeight: 1.35, opacity: appear }}>{transcript ? `«${transcript}»` : subtitle}</div>}
      </div>
    </AbsoluteFill>
  );
};

/** A recognisable long-form video card, hosting a real clip or a poster image. */
export const YouTubeCard: React.FC<BaseSceneProps> = (props) => {
  const { src, images, title, subtitle, channelName, handle, startFrom = 0, muted = true, showControls = true, accentColor } = props;
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent, surface } = useSceneStyle(props.style, accentColor, props.styleConfig);
  const reveal = resolveMotion(props.motion ?? { curve: 'overdamped', duration: 18 }, fps, 'reveal');
  const appear = reveal(frame, 0, 1);
  const still = Array.isArray(images) && images.length ? images[0] : undefined;
  const source = src || still;
  if (!source) return <AbsoluteFill style={{ background: '#3A0A0A', color: '#FFF', display: 'grid', placeItems: 'center', fontFamily: 'ui-monospace', fontSize: 30 }}>VIDEO CARD NEEDS src OR images[0]</AbsoluteFill>;
  return (
    <AbsoluteFill style={{ background: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: Math.round(height * .02) }}>
        <div style={{ color: accent, fontFamily: fonts.mono, fontWeight: 800, fontSize: Math.round(height * .016), letterSpacing: 2, opacity: appear }}>VIDEO INSERT</div>
        <div style={{ overflow: 'hidden', borderRadius: Math.round(height * .02), background: theme.surface, border: `1.5px solid ${accent}55`, boxShadow: surface === 'glass' ? `0 25px 90px ${accent}20` : '0 18px 44px rgba(0,0,0,.45)', opacity: appear, transform: `scale(${.97 + .03 * appear})` }}>
          <div style={{ height: Math.round(safe.width * .55), background: '#000', position: 'relative' }}>
            {src ? <OffthreadVideo src={resolveSrc(src)} startFrom={startFrom} muted={muted !== false} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <Img src={resolveSrc(still as string)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />}
            <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', width: Math.round(height * .075), height: Math.round(height * .075), display: 'grid', placeItems: 'center', borderRadius: 99, background: `${theme.bg}CC`, border: `2px solid ${accent}`, color: accent, fontSize: Math.round(height * .03) }}>▶</div>
            {showControls !== false && <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, padding: Math.round(height * .015), background: 'linear-gradient(transparent, rgba(0,0,0,.82))' }}><div style={{ height: 3, borderRadius: 99, background: `${theme.muted}88` }}><div style={{ width: `${Math.min(96, 10 + frame / fps * 7)}%`, height: '100%', background: accent, borderRadius: 99 }} /></div></div>}
          </div>
          <div style={{ padding: Math.round(height * .022) }}>
            <div style={{ color: theme.text, fontFamily: fonts.display, fontWeight: 800, fontSize: Math.round(height * .027), lineHeight: 1.12 }}>{title || 'Вставьте реальное видео или запись экрана'}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginTop: Math.round(height * .014), color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * .018) }}><span>{channelName || 'Channel'}</span><span>{handle || 'video'}</span></div>
          </div>
        </div>
        {subtitle && <div style={{ color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * .021), lineHeight: 1.35, opacity: appear }}>{subtitle}</div>}
      </div>
    </AbsoluteFill>
  );
};

/** A high-contrast still-image insert with a controlled crop and explanatory caption. */
export const ImageSpotlight: React.FC<BaseSceneProps> = (props) => {
  const { src, images, title, subtitle, fit = 'cover', kenBurns = true, accentColor } = props;
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent, surface } = useSceneStyle(props.style, accentColor, props.styleConfig);
  const source = src || (Array.isArray(images) && images[0]);
  const reveal = resolveMotion(props.motion ?? { curve: 'overdamped', duration: 18 }, fps, 'reveal');
  const appear = reveal(frame, 0, 1);
  if (!source) return <AbsoluteFill style={{ background: '#3A0A0A', color: '#FFF', display: 'grid', placeItems: 'center', fontFamily: 'ui-monospace', fontSize: 30 }}>IMAGE SPOTLIGHT NEEDS src OR images[0]</AbsoluteFill>;
  const imageScale = kenBurns === false ? 1 : interpolate(frame, [0, 240], [1.02, 1.09], { extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, display: 'grid', gridTemplateRows: '1fr auto', gap: Math.round(height * .023) }}>
        <div style={{ position: 'relative', overflow: 'hidden', borderRadius: Math.round(height * .025), background: theme.surface, border: `2px solid ${accent}55`, boxShadow: surface === 'glass' ? `0 28px 90px ${accent}24` : '0 20px 48px rgba(0,0,0,.5)', opacity: appear }}>
          <Img src={resolveSrc(source as string)} style={{ width: '100%', height: '100%', objectFit: fit === 'contain' ? 'contain' : 'cover', transform: `scale(${imageScale})` }} />
          <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(180deg, transparent 42%, ${theme.bg}EE 100%)` }} />
          <div style={{ position: 'absolute', left: Math.round(width * .045), right: Math.round(width * .045), bottom: Math.round(height * .035) }}>
            <div style={{ color: accent, fontFamily: fonts.mono, fontWeight: 800, fontSize: Math.round(height * .015), letterSpacing: 2 }}>MEDIA SPOTLIGHT</div>
            <div style={{ color: theme.text, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * .038), lineHeight: 1.07, marginTop: 8 }}>{title || 'Изображение как сюжетная сцена'}</div>
          </div>
        </div>
        {subtitle && <div style={{ color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * .021), lineHeight: 1.35, opacity: appear }}>{subtitle}</div>}
      </div>
    </AbsoluteFill>
  );
};
