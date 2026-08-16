import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { getSafeArea } from '../lib/safeArea';
import { resolveMotion } from '../lib/motion';
import { useStyle } from '../theme/StyleContext';
import { Backdrop } from '../theme/Backdrop';

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

/**
 * MSF Studio universal preset pack.
 *
 * The components deliberately read only structured, manifest-documented props.
 * They use the existing safe-area, style and motion systems so a new scene does
 * not become an isolated theme or timing implementation.
 */

type StepItem = { label: string; detail?: string; description?: string } | string;
type StepListProps = BaseSceneProps & { steps?: StepItem[]; title?: string };

/** Numbered procedure/checklist for explainers and onboarding videos. */
export const StepList: React.FC<BaseSceneProps> = (props) => {
  const { steps, title } = props as StepListProps;
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'reveal');
  const items = (Array.isArray(steps) && steps.length > 0 ? steps : [
    { label: 'Определите задачу', description: 'Сформулируйте ожидаемый результат' },
    { label: 'Выберите инструмент', description: 'Оставьте только подходящие варианты' },
    { label: 'Проверьте результат', description: 'Зафиксируйте следующий шаг' },
  ]).slice(0, 5).map((item) => typeof item === 'string'
    ? { label: item, description: undefined }
    : { label: item.label, description: item.description ?? item.detail });
  const rowHeight = Math.min(Math.round(safe.height / Math.max(items.length + 1.45, 4)), Math.round(height * 0.17));

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}>
        <div style={{ color: accent, fontFamily: fonts.display, fontSize: Math.round(height * 0.021), fontWeight: 800, letterSpacing: Math.round(width * 0.004), textTransform: 'uppercase', opacity: animate(frame, 0, 1) }}>
          {title || 'План действий'}
        </div>
        <div style={{ marginTop: Math.round(height * 0.035), display: 'flex', flexDirection: 'column', gap: Math.round(rowHeight * 0.15) }}>
          {items.map((item, index) => {
            const progress = clamp01(animate(frame - index * Math.round(fps * 0.16), 0, 1));
            return (
              <div key={`${item.label}-${index}`} style={{ minHeight: rowHeight, display: 'flex', alignItems: 'center', gap: Math.round(width * 0.032), opacity: progress, transform: `translateX(${Math.round((1 - progress) * width * 0.10)}px)` }}>
                <div style={{ width: Math.round(rowHeight * 0.68), height: Math.round(rowHeight * 0.68), borderRadius: '50%', backgroundColor: accent, color: theme.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(rowHeight * 0.28), flexShrink: 0, boxShadow: `0 0 ${Math.round(rowHeight * 0.18)}px ${accent}55` }}>
                  {index + 1}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ color: theme.text, fontFamily: fonts.display, fontSize: Math.round(height * 0.030), fontWeight: 800, lineHeight: 1.15, overflowWrap: 'break-word' }}>{item.label}</div>
                  {item.description && <div style={{ color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * 0.020), marginTop: Math.round(height * 0.006), lineHeight: 1.25, overflowWrap: 'break-word' }}>{item.description}</div>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

type ComparisonSide = { title?: string; text?: string; label?: string; color?: string };
type BeforeAfterProps = BaseSceneProps & { before?: ComparisonSide; after?: ComparisonSide; title?: string };

/** Clear before/after transformation without invented metrics or names. */
export const BeforeAfter: React.FC<BaseSceneProps> = (props) => {
  const { before, after, title } = props as BeforeAfterProps;
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'reveal');
  const left = before ?? { label: 'До', title: 'Ручной процесс', text: 'Много повторяющихся действий' };
  const right = after ?? { label: 'После', title: 'Автоматизированный поток', text: 'Быстрый и прозрачный результат' };
  const leftProgress = clamp01(animate(frame, 0, 1));
  const rightProgress = clamp01(animate(frame - Math.round(fps * 0.22), 0, 1));
  const cardGap = Math.round(width * 0.028);
  const cardWidth = Math.floor((safe.width - cardGap) / 2);

  const card = (side: ComparisonSide, progress: number, isAfter: boolean) => (
    <div style={{ width: cardWidth, minHeight: Math.round(safe.height * 0.46), background: isAfter ? `${accent}1C` : `${theme.surface}DD`, border: `2px solid ${isAfter ? accent : `${theme.muted}66`}`, borderRadius: Math.round(width * 0.028), padding: Math.round(width * 0.040), boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', opacity: progress, transform: `translateY(${Math.round((1 - progress) * height * (isAfter ? 0.08 : -0.08))}px)` }}>
      <div style={{ color: isAfter ? accent : theme.muted, fontFamily: fonts.display, fontWeight: 800, fontSize: Math.round(height * 0.020), letterSpacing: Math.round(width * 0.003), textTransform: 'uppercase' }}>{side.label || (isAfter ? 'После' : 'До')}</div>
      <div>
        <div style={{ color: theme.text, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * 0.036), lineHeight: 1.05, overflowWrap: 'break-word' }}>{side.title || ''}</div>
        <div style={{ color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * 0.021), lineHeight: 1.35, marginTop: Math.round(height * 0.018), overflowWrap: 'break-word' }}>{side.text || ''}</div>
      </div>
      <div style={{ width: '100%', height: Math.round(height * 0.008), borderRadius: 999, backgroundColor: isAfter ? accent : theme.muted, opacity: isAfter ? 1 : 0.55 }} />
    </div>
  );

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}>
        <div style={{ color: theme.text, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * 0.040), lineHeight: 1.05, opacity: animate(frame, 0, 1) }}>{title || 'Трансформация'}</div>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: cardGap }}>
          {card(left, leftProgress, false)}
          {card(right, rightProgress, true)}
        </div>
      </div>
    </div>
  );
};

type TrendPoint = { label: string; value: number; note?: string };
type MetricTrendProps = BaseSceneProps & { points?: TrendPoint[]; metricLabel?: string; valueSuffix?: string; title?: string };

/** A labelled trend line for growth, adoption or other time-series proof. */
export const MetricTrend: React.FC<BaseSceneProps> = (props) => {
  const { points, metricLabel, valueSuffix = '', title } = props as MetricTrendProps;
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  const animate = resolveMotion(props.motion ?? props.intensity, fps, 'value');
  const data = (Array.isArray(points) && points.length >= 2 ? points : [
    { label: 'Старт', value: 18 }, { label: 'Неделя 2', value: 42 }, { label: 'Неделя 4', value: 76 },
  ]).slice(0, 6);
  const maxValue = Math.max(...data.map((point) => point.value), 1);
  const minValue = Math.min(...data.map((point) => point.value), 0);
  const span = Math.max(maxValue - minValue, 1);
  const chartTop = Math.round(safe.top + safe.height * 0.23);
  const chartHeight = Math.round(safe.height * 0.47);
  const chartWidth = safe.width;
  const progress = clamp01(animate(frame, 0, 1));
  const path = data.map((point, index) => {
    const x = data.length === 1 ? chartWidth / 2 : (chartWidth * index) / (data.length - 1);
    const y = chartHeight - ((point.value - minValue) / span) * chartHeight;
    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, boxSizing: 'border-box' }}>
        <div style={{ color: accent, fontFamily: fonts.display, fontWeight: 800, fontSize: Math.round(height * 0.020), letterSpacing: Math.round(width * 0.003), textTransform: 'uppercase' }}>{metricLabel || 'Динамика показателя'}</div>
        <div style={{ color: theme.text, fontFamily: fonts.display, fontWeight: 900, fontSize: Math.round(height * 0.038), marginTop: Math.round(height * 0.010), lineHeight: 1.08 }}>{title || 'Рост по ключевым этапам'}</div>
        <div style={{ position: 'absolute', top: chartTop - safe.top, left: 0, width: chartWidth, height: chartHeight }}>
          <svg width={chartWidth} height={chartHeight} viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{ overflow: 'visible' }}>
            {[0.25, 0.5, 0.75].map((fraction) => <line key={fraction} x1={0} x2={chartWidth} y1={chartHeight * fraction} y2={chartHeight * fraction} stroke={`${theme.muted}33`} strokeWidth={2} />)}
            <path d={path} fill="none" stroke={accent} strokeWidth={Math.round(width * 0.008)} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - progress} />
            {data.map((point, index) => {
              const x = data.length === 1 ? chartWidth / 2 : (chartWidth * index) / (data.length - 1);
              const y = chartHeight - ((point.value - minValue) / span) * chartHeight;
              const dotProgress = clamp01(animate(frame - index * Math.round(fps * 0.10), 0, 1));
              return <circle key={`${point.label}-${index}`} cx={x} cy={y} r={Math.round(width * 0.014) * dotProgress} fill={accent} stroke={theme.bg} strokeWidth={Math.round(width * 0.006)} />;
            })}
          </svg>
          {data.map((point, index) => {
            const x = data.length === 1 ? chartWidth / 2 : (chartWidth * index) / (data.length - 1);
            const y = chartHeight - ((point.value - minValue) / span) * chartHeight;
            const reveal = clamp01(animate(frame - index * Math.round(fps * 0.10), 0, 1));
            return <div key={`${point.label}-${index}`} style={{ position: 'absolute', left: x, top: y, transform: 'translate(-50%, -135%)', opacity: reveal, textAlign: 'center', pointerEvents: 'none' }}>
              <div style={{ color: theme.text, fontFamily: fonts.display, fontSize: Math.round(height * 0.024), fontWeight: 900 }}>{Math.round(point.value * progress)}{valueSuffix}</div>
              <div style={{ color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * 0.016), marginTop: 4, whiteSpace: 'nowrap' }}>{point.label}</div>
            </div>;
          })}
        </div>
      </div>
    </div>
  );
};


type DecisionOption = { title: string; description?: string; tag?: string; value?: string };
type DecisionGridProps = BaseSceneProps & { cards?: DecisionOption[]; title?: string };

/** A bounded choice matrix for tools, providers and workflow recommendations. */
export const DecisionGrid: React.FC<BaseSceneProps> = (props) => {
  const { cards, title } = props as DecisionGridProps;
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const { theme, fonts, accent } = useStyle();
  // Decision cards are reading surfaces. Do not inherit the scene's scale-capable
  // motion preset: a card may enter once, then its typography must be pixel-stable.
  const cardRevealFrames = Math.max(18, Math.round(fps * 0.58));
  const options = (Array.isArray(cards) && cards.length > 0 ? cards : [
    { tag: 'ЛОКАЛЬНО', title: 'Ollama', description: 'Когда важны приватность и контроль' },
    { tag: 'API', title: 'Free tier', description: 'Когда нужен быстрый эксперимент' },
    { tag: 'МАСШТАБ', title: 'Batch', description: 'Когда задача не требует ответа сейчас' },
  ]).slice(0, 4);
  const gap = Math.round(width * 0.026);
  const columns = options.length <= 2 ? options.length : 2;
  const cardWidth = Math.floor((safe.width - gap * (columns - 1)) / columns);
  const cardHeight = Math.min(Math.round(safe.height * (options.length <= 2 ? 0.46 : 0.31)), Math.round(height * 0.28));

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: theme.bg, overflow: 'hidden' }}>
      <Backdrop />
      <div style={{ position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, boxSizing: 'border-box' }}>
        <div style={{ color: theme.text, fontFamily: fonts.display, fontSize: Math.round(height * 0.040), fontWeight: 900, lineHeight: 1.06, maxWidth: safe.width }}>{title || 'Выберите подходящий режим'}</div>
        <div style={{ marginTop: Math.round(height * 0.05), display: 'flex', flexWrap: 'wrap', gap, alignContent: 'center' }}>
          {options.map((option, index) => {
            const delay = index * Math.round(fps * 0.16);
            // An explicit monotonic entrance prevents scale-up/scale-down pulses
            // even when a parent scene receives an aggressive motion setting.
            const progress = clamp01((frame - delay) / cardRevealFrames);
            const highlight = index === 0;
            return (
              <div key={`${option.title}-${index}`} style={{ width: cardWidth, height: cardHeight, borderRadius: Math.round(width * 0.026), border: `2px solid ${highlight ? accent : `${theme.muted}66`}`, background: highlight ? `${accent}16` : `${theme.surface}DD`, padding: Math.round(width * 0.032), boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', opacity: progress, transform: `translate3d(0, ${Math.round((1 - progress) * height * 0.024)}px, 0)`, willChange: progress < 1 ? 'transform, opacity' : 'auto' }}>
                <div style={{ color: highlight ? accent : theme.muted, fontFamily: fonts.display, fontSize: Math.round(height * 0.017), fontWeight: 900, letterSpacing: Math.round(width * 0.002), textTransform: 'uppercase' }}>{option.tag || `Вариант ${index + 1}`}</div>
                <div>
                  <div style={{ color: theme.text, fontFamily: fonts.display, fontSize: Math.round(height * 0.032), fontWeight: 900, lineHeight: 1.05, overflowWrap: 'break-word' }}>{option.title}</div>
                  {option.value && <div style={{ color: accent, fontFamily: fonts.display, fontSize: Math.round(height * 0.028), fontWeight: 900, marginTop: Math.round(height * 0.012) }}>{option.value}</div>}
                  {option.description && <div style={{ color: theme.muted, fontFamily: fonts.body, fontSize: Math.round(height * 0.018), lineHeight: 1.25, marginTop: Math.round(height * 0.015), overflowWrap: 'break-word' }}>{option.description}</div>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
