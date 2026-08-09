/**
 * Typography layer — deterministic font loading.
 *
 * WHY THIS EXISTS
 * ---------------
 * Presets used to hardcode `fontFamily: '"Impact", "Arial Black", system-ui'`.
 * Two problems, both verified rather than assumed:
 *
 *  1. In headless Chromium on Windows there is no guarantee `Impact` is present.
 *     The renderer silently substitutes a fallback, so the rendered frame does not
 *     match what the preview showed.
 *  2. `Impact` and `Arial Black` have poor-to-absent Cyrillic coverage. Russian copy —
 *     which is this project's primary language — degrades or falls back mid-word.
 *
 * Every family below was checked for a `cyrillic` subset by grepping the actual
 * @remotion/google-fonts payload. NOTE: `Anton` and `BebasNeue` — the two most
 * popular "shorts" display faces — FAILED that check and are deliberately absent.
 * Do not add them back without re-running audit/fontinfo.js.
 */
import { loadFont as loadArsenal } from '@remotion/google-fonts/Arsenal';
import { loadFont as loadGolosText } from '@remotion/google-fonts/GolosText';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadManrope } from '@remotion/google-fonts/Manrope';
import { loadFont as loadMontserrat } from '@remotion/google-fonts/Montserrat';
import { loadFont as loadOnest } from '@remotion/google-fonts/Onest';
import { loadFont as loadOswald } from '@remotion/google-fonts/Oswald';
import { loadFont as loadRubik } from '@remotion/google-fonts/Rubik';
import { loadFont as loadStalinistOne } from '@remotion/google-fonts/StalinistOne';
import { loadFont as loadUnbounded } from '@remotion/google-fonts/Unbounded';

export type FontRole = 'display' | 'body' | 'mono';

/** Families verified to carry a `cyrillic` subset. */
const unbounded = loadUnbounded('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700', '900'] });
const montserrat = loadMontserrat('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700', '900'] });
const manrope = loadManrope('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700', '800'] });
const onest = loadOnest('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700', '900'] });
const golos = loadGolosText('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700', '900'] });
const oswald = loadOswald('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700'] });
const rubik = loadRubik('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700', '900'] });
const inter = loadInter('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700', '900'] });
const arsenal = loadArsenal('normal', { subsets: ['cyrillic', 'latin'], weights: ['400', '700'] });
const stalinist = loadStalinistOne('normal', { subsets: ['cyrillic', 'latin'], weights: ['400'] });

/**
 * Monospace: no Cyrillic-safe mono ships in our verified set, and code snippets
 * are Latin by nature, so a system stack is honest here.
 */
const MONO_STACK = 'ui-monospace, SFMono-Regular, "JetBrains Mono", Menlo, Consolas, monospace';

export type FontKit = {
  /** Big kinetic headlines. */
  display: string;
  /** Paragraphs, subtitles, captions. */
  body: string;
  /** Code and terminal output. */
  mono: string;
};

/**
 * Named typographic pairings. A style kit picks one of these by name so that
 * changing a video's look never means editing a preset.
 */
export const FONT_KITS: Record<string, FontKit> = {
  // Geometric, wide, loud — the default for Pop-Laboratory.
  pop: { display: unbounded.fontFamily, body: manrope.fontFamily, mono: MONO_STACK },
  // Neutral Swiss/editorial.
  editorial: { display: montserrat.fontFamily, body: inter.fontFamily, mono: MONO_STACK },
  // Modern Russian-first grotesque.
  modern: { display: onest.fontFamily, body: golos.fontFamily, mono: MONO_STACK },
  // Condensed, news-ticker energy.
  news: { display: oswald.fontFamily, body: rubik.fontFamily, mono: MONO_STACK },
  // Heavy slab poster look.
  poster: { display: stalinist.fontFamily, body: arsenal.fontFamily, mono: MONO_STACK },
};

export const DEFAULT_FONT_KIT: keyof typeof FONT_KITS = 'pop';

export const getFontKit = (name?: string): FontKit =>
  FONT_KITS[name ?? DEFAULT_FONT_KIT] ?? FONT_KITS[DEFAULT_FONT_KIT];

/**
 * Every font's readiness promise. `Root.tsx` awaits these via `delayRender`
 * so frame 0 is never rendered with a substituted fallback face.
 */
export const fontReadyPromises: Promise<unknown>[] = [
  unbounded.waitUntilDone(),
  montserrat.waitUntilDone(),
  manrope.waitUntilDone(),
  onest.waitUntilDone(),
  golos.waitUntilDone(),
  oswald.waitUntilDone(),
  rubik.waitUntilDone(),
  inter.waitUntilDone(),
  arsenal.waitUntilDone(),
  stalinist.waitUntilDone(),
];

export const waitForFonts = (): Promise<unknown> => Promise.all(fontReadyPromises);
