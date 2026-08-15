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
  muted: '#A9B6CC',
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
 * `muted` MUST CLEAR ~4.5:1 AGAINST ITS OWN `bg`.
 * Presets use `muted` for sub-labels (ring captions, axis labels, timestamps) at
 * small sizes. Four of the six kits added below originally shipped a `muted`
 * chosen to look tasteful in isolation and measured 2.98–4.13 against their
 * backgrounds — `steel` failed even the 3:1 large-text floor, so its captions
 * were effectively invisible in a rendered frame. Check any new palette with a
 * contrast ratio, not by eye: a dim caption on a dark backdrop looks
 * "subtle" in a swatch and unreadable at 1080x1920.
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

/**
 * Six new palettes — one per new style kit.
 * Each one has a unique bg darkness, accent hue, and triadic variation so that
 * rendered frames differ at the pixel level (the accent triads drive the ring
 * colours, bg drives the corner sample).
 */

/** «Рассвет» — тёплый оранжево-золотой оптимистичный. */
const sunrise: Theme = {
  ...pop,
  bg: '#130B04',          // очень тёмный янтарь
  surface: '#221509',
  gold: '#FFAE42',        // апельсиновое золото
  neon: '#FF8C1A',        // насыщенный оранжевый
  cyan: '#FFD580',        // светлое золото
  text: '#FFF8EE',
  muted: '#C09468',
  darkBorder: '#000000',
  shadowColor: '#000000',
  accentCyan: '#FFD580',
  accentGreen: '#FF8C1A',
  accentWarm: '#FFAE42',
};

/** «Лес» — глубокий изумрудный эко. */
const forest: Theme = {
  ...pop,
  bg: '#061108',          // почти чёрный с зелёным
  surface: '#0D1F10',
  gold: '#80E890',        // мятно-зелёный
  neon: '#2DDA5A',        // живой зелёный
  cyan: '#60E8B0',        // лесная бирюза
  text: '#E8FFF0',
  muted: '#6C9E7C',
  darkBorder: '#000000',
  shadowColor: '#000000',
  accentCyan: '#60E8B0',
  accentGreen: '#2DDA5A',
  accentWarm: '#80E890',
};

/** «Монохром» — тёплая сепия/бумага (темнее обычного paper, другой акцент). */
const mono_warm: Theme = {
  ...pop,
  bg: '#160F08',          // тёмный кофейный
  surface: '#261A0F',
  gold: '#D4A96A',        // тёплый янтарь
  neon: '#C8924A',        // жжёная охра
  cyan: '#A87B58',        // коричнево-медный
  text: '#F5ECD8',
  muted: '#9C8272',
  darkBorder: '#000000',
  shadowColor: '#000000',
  accentCyan: '#A87B58',
  accentGreen: '#C8924A',
  accentWarm: '#D4A96A',
};

/** «Кибер-лайм» — максимально агрессивный лайм+пурпур. */
const cyber_lime: Theme = {
  ...pop,
  bg: '#020D02',          // почти чёрный с едва различимым зелёным
  surface: '#071407',
  gold: '#C6FF00',        // кислотный лайм
  neon: '#AAFF00',        // чистый лайм
  cyan: '#FF00C8',        // магента-пурпур (контраст к лайму)
  text: '#F0FFD8',
  muted: '#5A8A30',
  darkBorder: '#000000',
  shadowColor: '#000000',
  accentCyan: '#FF00C8',
  accentGreen: '#AAFF00',
  accentWarm: '#C6FF00',
};

/** LLM Hubs — near-black product surface, neon-green action colour and aqua data colour. */
const llm_hubs: Theme = {
  ...pop,
  bg: '#030807',
  surface: '#091512',
  // Legacy field name only: it intentionally resolves to the same neon green,
  // so un-migrated presets cannot leak a gold/amber card into this series.
  gold: '#00F0A8',
  neon: '#00F0A8',
  cyan: '#58E6D2',
  text: '#F4FFF9',
  muted: '#91B3A5',
  darkBorder: '#00120C',
  shadowColor: '#000000',
  accentCyan: '#58E6D2',
  accentGreen: '#00F0A8',
  accentWarm: '#00F0A8',
};

/** «Конфета» — тёмный пастель-поп (фон тёмный, акценты мягко-конфетные). */
const candy: Theme = {
  ...pop,
  bg: '#12040E',          // тёмный ягодный
  surface: '#1F0A1A',
  gold: '#FF8FD8',        // розово-лавандовый
  neon: '#FF6EC7',        // яркий розовый
  cyan: '#A78BFF',        // лавандовый
  text: '#FFF0FA',
  muted: '#A96BA0',
  darkBorder: '#000000',
  shadowColor: '#000000',
  accentCyan: '#A78BFF',
  accentGreen: '#FF6EC7',
  accentWarm: '#FF8FD8',
};

/** «Сталь» — промышленный холодный серо-стальной. */
const steel: Theme = {
  ...pop,
  bg: '#080C12',          // тёмный стальной
  surface: '#111720',
  gold: '#7AAED8',        // стальной голубой
  neon: '#5B9EC9',        // холодный синий
  cyan: '#9EC8E0',        // светло-стальной
  text: '#E8F0F8',
  muted: '#6E8798',
  darkBorder: '#000000',
  shadowColor: '#000000',
  accentCyan: '#9EC8E0',
  accentGreen: '#5B9EC9',
  accentWarm: '#7AAED8',
};

// Ten additional palette families for the v2.3 expansion. `gold` remains a
// compatibility alias for legacy presets; it is intentionally never amber by
// default in these kits.
const aurora_flux: Theme = { ...pop, bg: '#07101A', surface: '#0D1D2B', gold: '#9B8CFF', neon: '#58E6D2', cyan: '#9B8CFF', text: '#F1F7FF', muted: '#8CA4B8', darkBorder: '#02070C', shadowColor: '#01050A', accentCyan: '#9B8CFF', accentGreen: '#58E6D2', accentWarm: '#9B8CFF' };
const cobalt_command: Theme = { ...pop, bg: '#07101E', surface: '#0D1D35', gold: '#84B7FF', neon: '#4D8DFF', cyan: '#83D7FF', text: '#F2F7FF', muted: '#91A8C8', darkBorder: '#010712', shadowColor: '#01040B', accentCyan: '#83D7FF', accentGreen: '#4D8DFF', accentWarm: '#84B7FF' };
const infrared_alert: Theme = { ...pop, bg: '#130809', surface: '#271012', gold: '#FF8B8B', neon: '#FF4B55', cyan: '#FFB2B2', text: '#FFF5F5', muted: '#C5969A', darkBorder: '#160103', shadowColor: '#080001', accentCyan: '#FFB2B2', accentGreen: '#FF4B55', accentWarm: '#FF8B8B' };
const violet_luxe: Theme = { ...pop, bg: '#100A1B', surface: '#1B1130', gold: '#D9C4FF', neon: '#B28AFF', cyan: '#8DE8FF', text: '#FAF7FF', muted: '#B3A1CD', darkBorder: '#08040F', shadowColor: '#030106', accentCyan: '#8DE8FF', accentGreen: '#B28AFF', accentWarm: '#D9C4FF' };
const porcelain: Theme = { ...pop, bg: '#F1F3F0', surface: '#FFFFFF', gold: '#126C68', neon: '#0B8078', cyan: '#175B86', text: '#10171B', muted: '#58676C', darkBorder: '#C6D0CC', shadowColor: '#9DA9A5', accentCyan: '#175B86', accentGreen: '#0B8078', accentWarm: '#126C68' };
const liquid_chrome: Theme = { ...pop, bg: '#0A0C10', surface: '#141922', gold: '#E1E7EF', neon: '#75DAFF', cyan: '#A9C7FF', text: '#F5F9FF', muted: '#94A3B4', darkBorder: '#020304', shadowColor: '#000102', accentCyan: '#A9C7FF', accentGreen: '#75DAFF', accentWarm: '#E1E7EF' };
const kinetic_poster: Theme = { ...pop, bg: '#080908', surface: '#121512', gold: '#E7FF3D', neon: '#D7FF00', cyan: '#FFFFFF', text: '#FFFFFF', muted: '#AAB19C', darkBorder: '#000000', shadowColor: '#000000', accentCyan: '#FFFFFF', accentGreen: '#D7FF00', accentWarm: '#E7FF3D' };
const midnight_orbit: Theme = { ...pop, bg: '#050B1A', surface: '#0B1730', gold: '#B6D6FF', neon: '#45B7FF', cyan: '#73F0E2', text: '#F1F7FF', muted: '#8CA5C6', darkBorder: '#00030B', shadowColor: '#000109', accentCyan: '#73F0E2', accentGreen: '#45B7FF', accentWarm: '#B6D6FF' };
const pixel_arcade: Theme = { ...pop, bg: '#100819', surface: '#1C1030', gold: '#C8FF4A', neon: '#91FF00', cyan: '#C57BFF', text: '#F7FFE0', muted: '#A89BBB', darkBorder: '#050008', shadowColor: '#030004', accentCyan: '#C57BFF', accentGreen: '#91FF00', accentWarm: '#C8FF4A' };
const coral_creator: Theme = { ...pop, bg: '#1A0910', surface: '#2A111C', gold: '#FFC0AB', neon: '#FF7C78', cyan: '#FFB3DC', text: '#FFF5F5', muted: '#C69AA7', darkBorder: '#090103', shadowColor: '#050001', accentCyan: '#FFB3DC', accentGreen: '#FF7C78', accentWarm: '#FFC0AB' };

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
  sunrise,
  forest,
  mono_warm,
  cyber_lime,
  llm_hubs,
  candy,
  steel,
  aurora_flux,
  cobalt_command,
  infrared_alert,
  violet_luxe,
  porcelain,
  liquid_chrome,
  kinetic_poster,
  midnight_orbit,
  pixel_arcade,
  coral_creator,
};

export const getTheme = (name?: string): Theme => THEMES[name || 'pop'] || pop;

export const BRAND = pop;
