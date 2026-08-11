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

/**
 * Additional palettes so every style kit is visually distinct.
 *
 * WHY THESE EXIST
 * ---------------
 * Eight kits used to share five palettes: `editorial` and `clean` both pointed
 * at `noir`, and `neon` and `retro` both at `sunset`. Measured on an identical
 * RingStats frame rendered through each kit, those two pairs came out with a
 * backdrop distance of 0.0 and the same ring colours — switching style did
 * nothing visible. A "style" that cannot be told apart from another is not a
 * style, so the four collided kits get their own palettes below.
 */
const paper: Theme = {
  ...pop,
  bg: '#0B0B0C',
  surface: '#17181A',
  gold: '#E8E2D4',
  neon: '#F2EDE2',
  cyan: '#C9C3B6',
  text: '#FBF9F5',
  muted: '#8A8578',
  accentCyan: '#C9C3B6',
  accentGreen: '#F2EDE2',
  accentWarm: '#E8E2D4',
};

const vhs: Theme = {
  ...pop,
  bg: '#120A16',
  surface: '#1F1024',
  gold: '#FFD166',
  neon: '#FF5FA2',
  cyan: '#5FE0FF',
  text: '#FFF0F8',
  muted: '#A87FA0',
  accentCyan: '#5FE0FF',
  accentGreen: '#FF5FA2',
  accentWarm: '#FFD166',
};

/** Broadcast red/white urgency — `news` used to share `pop`'s palette. */
const broadcast: Theme = {
  ...pop,
  bg: '#0C0D10',
  surface: '#191B20',
  gold: '#FFC93C',
  neon: '#FF3B30',
  cyan: '#FFFFFF',
  text: '#FFFFFF',
  muted: '#8E949E',
  accentCyan: '#FFFFFF',
  accentGreen: '#FF3B30',
  accentWarm: '#FFC93C',
};

const ink: Theme = {
  ...pop,
  bg: '#07080A',
  surface: '#111317',
  gold: '#FFFFFF',
  neon: '#FFFFFF',
  cyan: '#D6DAE0',
  text: '#FFFFFF',
  muted: '#7A8089',
  accentCyan: '#D6DAE0',
  accentGreen: '#FFFFFF',
  accentWarm: '#FFFFFF',
};

export const THEMES: Record<string, Theme> = {
  pop,
  noir,
  glass,
  blueprint,
  sunset,
  paper,
  vhs,
  ink,
  broadcast,
};

export const getTheme = (name?: string): Theme => THEMES[name || 'pop'] || pop;

export const BRAND = pop;
