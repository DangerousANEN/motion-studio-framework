/**
 * Brand palette + named themes.
 *
 * BRAND stays exported as the default (pop) palette so existing presets keep
 * working unchanged. Presets that support theming should call `getTheme(name)`
 * and read colors from the returned object.
 */

export type Theme = {
  bg: string;
  surface: string;
  gold: string;
  neon: string;
  cyan: string;
  text: string;
  muted: string;
  darkBorder: string;
  shadowColor: string;
  /** Aliases used by the 3D presets. */
  accentCyan: string;
  accentGreen: string;
  accentWarm: string;
};

const pop: Theme = {
  bg: '#0E0F11',
  surface: '#16181C',
  gold: '#E6C475',
  neon: '#00FF88',
  cyan: '#00D4FF',
  text: '#FFFFFF',
  muted: '#8B92A0',
  darkBorder: '#000000',
  shadowColor: '#000000',
  accentCyan: '#00D4FF',
  accentGreen: '#00FF88',
  accentWarm: '#E6C475',
};

const noir: Theme = {
  ...pop,
  bg: '#08090A',
  surface: '#121316',
  gold: '#D8D8D8',
  neon: '#FFFFFF',
  cyan: '#B8BCC4',
  muted: '#6E747E',
  accentCyan: '#B8BCC4',
  accentGreen: '#FFFFFF',
  accentWarm: '#D8D8D8',
};

const glass: Theme = {
  ...pop,
  bg: '#0B1220',
  surface: 'rgba(255,255,255,0.06)',
  gold: '#FFD79A',
  neon: '#7CF7C6',
  cyan: '#7CC5FF',
  muted: '#93A2BC',
  accentCyan: '#7CC5FF',
  accentGreen: '#7CF7C6',
  accentWarm: '#FFD79A',
};

const blueprint: Theme = {
  ...pop,
  bg: '#061018',
  surface: '#0C1B26',
  gold: '#7FE3FF',
  neon: '#39D0FF',
  cyan: '#39D0FF',
  text: '#DFF6FF',
  muted: '#5E8CA3',
  accentCyan: '#39D0FF',
  accentGreen: '#7FE3FF',
  accentWarm: '#9EF0FF',
};

const sunset: Theme = {
  ...pop,
  bg: '#140A14',
  surface: '#221024',
  gold: '#FFC46B',
  neon: '#FF7A6B',
  cyan: '#FF9ECF',
  text: '#FFF3EC',
  muted: '#B98CA0',
  accentCyan: '#FF9ECF',
  accentGreen: '#FFC46B',
  accentWarm: '#FF7A6B',
};

export const THEMES: Record<string, Theme> = { pop, noir, glass, blueprint, sunset };

export const getTheme = (name?: string): Theme => THEMES[name || 'pop'] || pop;

export const BRAND = pop;
