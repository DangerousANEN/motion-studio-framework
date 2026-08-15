import React from 'react';
import {staticFile, useVideoConfig} from 'remotion';
import {BaseSceneProps} from '../VideoSpec.schema';
import {getSafeArea} from '../lib/safeArea';
import {Backdrop} from '../theme/Backdrop';
import {useStyle} from '../theme/StyleContext';

/** Shared safe frame for the 50-scene expansion.
 *
 * Every pack owns its visual composition, but all of them use this shell so a
 * long Cyrillic label can never make a row wider than the platform-safe canvas.
 */
export const SceneFrame: React.FC<{
  props: BaseSceneProps;
  children: React.ReactNode;
  align?: 'center' | 'start';
}> = ({props, children, align = 'center'}) => {
  const {width, height} = useVideoConfig();
  const safe = getSafeArea(width, height, props.safeArea ?? 'platform');
  const {theme} = useStyle();
  return <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: theme.bg}}>
    <Backdrop />
    <div style={{position: 'absolute', top: safe.top, left: safe.left, width: safe.width, height: safe.height, boxSizing: 'border-box', minWidth: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: align}}>{children}</div>
  </div>;
};

/** Safe flex row: the important minWidth:0 rule prevents the rightmost card from
 * being pushed outside the frame by a long word. */
export const SafeRow: React.FC<{children: React.ReactNode; gap?: number; style?: React.CSSProperties}> = ({children, gap = 16, style}) => (
  <div style={{display: 'flex', width: '100%', minWidth: 0, overflow: 'hidden', gap, ...style}}>{children}</div>
);

/** One flexible child that may shrink below its content width. */
export const SafeFlex: React.FC<{children?: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <div style={{flex: 1, minWidth: 0, overflow: 'hidden', boxSizing: 'border-box', ...style}}>{children}</div>
);

export const asText = (value: unknown, fallback = ''): string => typeof value === 'string' ? value : fallback;
export const asNumber = (value: unknown, fallback = 0): number => typeof value === 'number' && Number.isFinite(value) ? value : fallback;
export const asRows = (value: unknown): Record<string, unknown>[] => Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => !!item && typeof item === 'object') : [];
export const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

/** Remote assets remain remote; relative assets are served through Remotion. */
export const resolveMedia = (value: unknown): string => {
  const url = asText(value);
  if (!url) return '';
  return /^(https?:|data:|blob:)/i.test(url) ? url : staticFile(url);
};

export const isVideoMedia = (url: string) => /\.(mp4|webm|mov)(?:[?#].*)?$/i.test(url);

export const sceneHeadingStyle = (height: number, fonts: {display: string}, color: string): React.CSSProperties => ({
  fontFamily: fonts.display,
  color,
  fontWeight: 900,
  fontSize: Math.round(height * .041),
  lineHeight: 1.03,
  maxWidth: '100%',
  overflowWrap: 'anywhere',
});
