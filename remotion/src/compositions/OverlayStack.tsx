import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { useStyle } from '../theme/StyleContext';

/**
 * Scene overlays — HUD elements that sit ON TOP of a scene's content.
 *
 * WHY THESE ARE NOT EFFECTS
 * -------------------------
 * The obvious home for "add a timer / a notification / a money popup" is the
 * effects registry, and that was the first attempt. It does not work: the
 * effect contract is
 *
 *     { children, intensity?, seed? }
 *
 * and EffectStack passes exactly those three. There is no channel for the
 * timer's duration, the notification's text, or the amount of money credited,
 * and widening the effect contract would change the signature of all 96
 * existing effects.
 *
 * So overlays are their own scene-level layer: `scene.overlays[]`, each entry
 * carrying its own props, rendered above the scene by Main. They compose with
 * ANY preset — that is the point. A screen recording with a countdown, a chat
 * with a payment toast, a chart with a notification.
 *
 * TIMING
 * ------
 * Each overlay accepts `at` (0..1 scene progress) for when it appears and
 * `hold` (seconds) for how long it stays. Progress-relative rather than
 * absolute frames so the same overlay works in a 3s and a 30s scene.
 */

export interface OverlaySpec {
  type: string;
  /** 0..1 — when in the scene it appears. Default 0.1. */
  at?: number;
  /** Seconds on screen. Default: to the end of the scene. */
  hold?: number;
  /** Corner placement. Default varies per overlay type. */
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center' | 'top' | 'bottom';
  // timer
  seconds?: number;
  countUp?: boolean;
  label?: string;
  // notification
  appName?: string;
  title?: string;
  text?: string;
  icon?: string;
  // money
  amount?: number;
  currency?: string;
  sender?: string;
}

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/** Resolves a corner into absolute offsets. */
const anchor = (
  position: OverlaySpec['position'],
  inset: number,
  fallback: OverlaySpec['position']
): React.CSSProperties => {
  const p = position ?? fallback;
  switch (p) {
    case 'top-left':
      return { top: inset, left: inset };
    case 'top-right':
      return { top: inset, right: inset };
    case 'bottom-left':
      return { bottom: inset, left: inset };
    case 'bottom-right':
      return { bottom: inset, right: inset };
    case 'top':
      return { top: inset, left: inset, right: inset };
    case 'bottom':
      return { bottom: inset, left: inset, right: inset };
    case 'center':
    default:
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
  }
};

/**
 * Shared appear/disappear envelope.
 * Returns 0 when the overlay should not be mounted at all.
 */
const useEnvelope = (spec: OverlaySpec) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const start = Math.round(durationInFrames * clamp01(spec.at ?? 0.1));
  const holdFrames = spec.hold ? Math.round(spec.hold * fps) : durationInFrames - start;
  const end = Math.min(durationInFrames, start + holdFrames);
  const inFrames = Math.min(14, Math.max(6, Math.round(fps * 0.22)));

  if (frame < start || frame > end) return { visible: false, t: 0, local: 0 };

  const rise = interpolate(frame, [start, start + inFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fall = interpolate(frame, [end - inFrames, end], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return { visible: true, t: Math.min(rise, fall), local: frame - start };
};

/* ---------------------------------------------------------- TimerOverlay */

/**
 * A countdown (or count-up) pill with a progress ring.
 * Default counts DOWN from `seconds`, because that is the urgency device.
 */
const TimerOverlay: React.FC<{ spec: OverlaySpec }> = ({ spec }) => {
  const { height, fps } = useVideoConfig();
  const { theme, fonts, accent } = useStyle();
  const { visible, t, local } = useEnvelope(spec);
  if (!visible) return null;

  const total = typeof spec.seconds === 'number' ? spec.seconds : 10;
  const elapsed = local / fps;
  const remaining = Math.max(0, total - elapsed);
  const value = spec.countUp ? Math.min(total, elapsed) : remaining;
  const progress = clamp01(spec.countUp ? elapsed / total : remaining / total);

  const size = Math.round(height * 0.09);
  const stroke = Math.max(5, Math.round(size * 0.09));
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  // Runs red in the last 3 seconds of a countdown.
  const urgent = !spec.countUp && remaining <= 3;
  const color = urgent ? '#FF4D4D' : accent;
  const pulse = urgent ? 1 + Math.sin(local / 2.2) * 0.04 : 1;

  const mmss =
    total >= 60
      ? `${Math.floor(value / 60)}:${String(Math.floor(value % 60)).padStart(2, '0')}`
      : String(Math.ceil(value));

  return (
    <div
      style={{
        position: 'absolute',
        ...anchor(spec.position, Math.round(height * 0.022), 'top-right'),
        display: 'flex',
        alignItems: 'center',
        gap: Math.round(size * 0.18),
        opacity: t,
        transform: `${
          spec.position === 'center' ? 'translate(-50%, -50%) ' : ''
        }scale(${(0.9 + t * 0.1) * pulse})`,
        zIndex: 60,
      }}
    >
      <div style={{ width: size, height: size, position: 'relative' }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="rgba(0,0,0,0.55)" />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={`${theme.muted}44`}
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={circ * (1 - progress)}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: fonts.display,
            fontSize: Math.round(size * (total >= 60 ? 0.26 : 0.36)),
            fontWeight: 900,
            color: '#FFFFFF',
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {mmss}
        </div>
      </div>
      {spec.label && (
        <div
          style={{
            fontFamily: fonts.body,
            fontSize: Math.round(height * 0.017),
            fontWeight: 700,
            color: '#FFFFFF',
            backgroundColor: 'rgba(0,0,0,0.55)',
            padding: `${Math.round(height * 0.006)}px ${Math.round(height * 0.012)}px`,
            borderRadius: 999,
          }}
        >
          {spec.label}
        </div>
      )}
    </div>
  );
};

/* --------------------------------------------------- NotificationOverlay */

/** An iOS/Android-style banner sliding in from the top. */
const NotificationOverlay: React.FC<{ spec: OverlaySpec }> = ({ spec }) => {
  const { width, height } = useVideoConfig();
  const { theme, fonts, accent } = useStyle();
  const { visible, t } = useEnvelope(spec);
  if (!visible) return null;

  const cardW = Math.round(width * 0.84);
  const pad = Math.round(height * 0.014);
  const iconSize = Math.round(height * 0.042);

  return (
    <div
      style={{
        position: 'absolute',
        top: Math.round(height * 0.03),
        left: '50%',
        width: cardW,
        marginLeft: -cardW / 2,
        // Slides down from above the frame and settles — the banner motion.
        transform: `translateY(${(1 - t) * -Math.round(height * 0.06)}px)`,
        opacity: t,
        backgroundColor: 'rgba(28,30,36,0.94)',
        backdropFilter: 'blur(18px)',
        WebkitBackdropFilter: 'blur(18px)',
        borderRadius: Math.round(height * 0.016),
        border: '1px solid rgba(255,255,255,0.13)',
        boxShadow: '0 18px 50px rgba(0,0,0,0.55)',
        padding: pad,
        display: 'flex',
        alignItems: 'center',
        gap: pad,
        boxSizing: 'border-box',
        zIndex: 60,
      }}
    >
      <div
        style={{
          width: iconSize,
          height: iconSize,
          borderRadius: Math.round(iconSize * 0.26),
          background: `linear-gradient(140deg, ${accent}, ${theme.cyan})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          fontSize: iconSize * 0.55,
        }}
      >
        {spec.icon ?? '🔔'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            gap: 8,
          }}
        >
          <span
            style={{
              fontFamily: fonts.body,
              fontSize: Math.round(height * 0.0155),
              fontWeight: 800,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 0.6,
            }}
          >
            {spec.appName ?? 'Уведомление'}
          </span>
          <span
            style={{
              fontFamily: fonts.body,
              fontSize: Math.round(height * 0.013),
              color: 'rgba(255,255,255,0.5)',
              flexShrink: 0,
            }}
          >
            сейчас
          </span>
        </div>
        {spec.title && (
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: Math.round(height * 0.019),
              fontWeight: 700,
              color: '#FFFFFF',
              marginTop: 3,
              lineHeight: 1.2,
            }}
          >
            {spec.title}
          </div>
        )}
        {spec.text && (
          <div
            style={{
              fontFamily: fonts.body,
              fontSize: Math.round(height * 0.0165),
              color: 'rgba(255,255,255,0.78)',
              marginTop: 2,
              lineHeight: 1.3,
              overflow: 'hidden',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {spec.text}
          </div>
        )}
      </div>
    </div>
  );
};

/* ---------------------------------------------------------- MoneyOverlay */

/**
 * A "money credited" toast: amount counting up, green, with a rising ghost.
 * The single most-requested overlay shape in monetisation content.
 */
const MoneyOverlay: React.FC<{ spec: OverlaySpec }> = ({ spec }) => {
  const { height, fps } = useVideoConfig();
  const { fonts } = useStyle();
  const { visible, t, local } = useEnvelope(spec);
  if (!visible) return null;

  const amount = typeof spec.amount === 'number' ? spec.amount : 1000;
  const currency = spec.currency ?? '₽';
  // Counts up over ~0.6s then holds; a credited amount that keeps ticking for
  // the whole scene reads as a stock price, not a payment.
  const countProgress = clamp01(local / (fps * 0.6));
  const shown = Math.round(amount * countProgress);
  const GREEN = '#2BD97C';

  const fmt = (n: number) => n.toLocaleString('ru-RU');

  return (
    <div
      style={{
        position: 'absolute',
        ...anchor(spec.position, Math.round(height * 0.024), 'top-right'),
        opacity: t,
        transform: `${spec.position === 'center' ? 'translate(-50%, -50%) ' : ''}translateY(${
          (1 - t) * Math.round(height * 0.02)
        }px)`,
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        gap: Math.round(height * 0.012),
        backgroundColor: 'rgba(10,26,18,0.92)',
        border: `1.5px solid ${GREEN}66`,
        borderRadius: 999,
        padding: `${Math.round(height * 0.01)}px ${Math.round(height * 0.02)}px`,
        boxShadow: `0 12px 36px rgba(0,0,0,0.5), 0 0 ${Math.round(
          height * 0.02
        )}px ${GREEN}22`,
      }}
    >
      <div
        style={{
          width: Math.round(height * 0.032),
          height: Math.round(height * 0.032),
          borderRadius: '50%',
          backgroundColor: GREEN,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <svg width={Math.round(height * 0.018)} height={Math.round(height * 0.018)} viewBox="0 0 24 24">
          <path
            d="M12 19V5M12 5l-6 6M12 5l6 6"
            stroke="#06210F"
            strokeWidth="2.6"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            transform="rotate(180 12 12)"
          />
        </svg>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span
          style={{
            fontFamily: fonts.display,
            fontSize: Math.round(height * 0.026),
            fontWeight: 900,
            color: GREEN,
            fontVariantNumeric: 'tabular-nums',
            lineHeight: 1.1,
          }}
        >
          +{fmt(shown)} {currency}
        </span>
        {(spec.sender || spec.label) && (
          <span
            style={{
              fontFamily: fonts.body,
              fontSize: Math.round(height * 0.014),
              color: 'rgba(255,255,255,0.66)',
            }}
          >
            {spec.sender ?? spec.label}
          </span>
        )}
      </div>
    </div>
  );
};

/* ---------------------------------------------------------------- router */

const OVERLAY_TYPES: Record<string, React.FC<{ spec: OverlaySpec }>> = {
  timer: TimerOverlay,
  notification: NotificationOverlay,
  money: MoneyOverlay,
};

export const OVERLAY_NAMES = Object.keys(OVERLAY_TYPES);

/**
 * Renders a scene's overlay stack. Unknown types are skipped with a warning
 * rather than thrown: one bad overlay name must not lose the whole render.
 */
export const OverlayStack: React.FC<{ overlays?: OverlaySpec[] }> = ({ overlays }) => {
  if (!overlays || overlays.length === 0) return null;
  return (
    <>
      {overlays.map((spec, i) => {
        const Component = OVERLAY_TYPES[spec.type];
        if (!Component) {
          // eslint-disable-next-line no-console
          console.warn(
            `[OverlayStack] unknown overlay "${spec.type}" — skipped. Known: ${OVERLAY_NAMES.join(', ')}`
          );
          return null;
        }
        return <Component key={`${spec.type}-${i}`} spec={spec} />;
      })}
    </>
  );
};
