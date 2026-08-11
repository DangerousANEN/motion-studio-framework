/**
 * Stage preset pack — music, gaming, and live-show scenes.
 *
 * A pack dedicated to the "something is happening RIGHT NOW" category:
 * karaoke lyric fills, esports HUDs, broadcast countdowns, and versus
 * split-screens.  These presets share one quality: they are designed to be
 * on-screen while content is in motion — the viewer is engaged, not reading.
 *
 * WHY A SEPARATE PACK
 * -------------------
 * These presets have no conceptual overlap with the existing categories:
 *   - They are not typography (text is secondary, timing is primary).
 *   - They are not data (no axes, no percentages, no charts).
 *   - They are not narrative (no sequential reveal, no storytelling flow).
 *   - They are not UI-mock (no chrome, no device frame).
 *   - They are not pure media (no asset required; they render with defaults).
 *
 * Grouping them here lets a parent spec pick "stage" presets as a rotation
 * bucket without mixing them with chart presets or typography presets.
 *
 * ADDING A NEW STAGE PRESET
 * -------------------------
 *   1. Export it from presets/stage.tsx.
 *   2. Add its entry below.
 *   3. Parent registers this pack via mergeRegistries in registry/presets.ts.
 */

import { LyricLines, ScoreHud, CountdownHero, VersusSplit } from '../presets/stage';
import { PresetRegistry } from './types';

export const STAGE_PRESETS: PresetRegistry = {
  LyricLines: {
    component: LyricLines,
    category: 'media',
    summary: 'Karaoke lyric display: active line highlighted; words fill left-to-right.',
    fields: ['lines', 'title', 'artist', 'motion', 'intensity', 'safeArea', 'accentColor', 'style'],
    dataDriven: true,
  },

  ScoreHud: {
    component: ScoreHud,
    category: 'ui-mock',
    summary: 'Gaming HUD: rolling score, shrinking health bar, pulsing combo, round timer.',
    fields: ['score', 'health', 'combo', 'timeLeft', 'playerName', 'motion', 'intensity', 'safeArea', 'accentColor', 'style'],
  },

  CountdownHero: {
    component: CountdownHero,
    category: 'narrative',
    summary: 'Broadcast 3-2-1-GO: digit fly-in with ring impulse; final beat flashes finalWord.',
    fields: ['from', 'finalWord', 'subtitle', 'motion', 'intensity', 'safeArea', 'accentColor', 'style'],
  },

  VersusSplit: {
    component: VersusSplit,
    category: 'narrative',
    summary: 'Versus split-screen: diagonal panels slide in, VS impact in the centre.',
    fields: [
      'left',
      'right',
      'vsLabel',
      'motion',
      'intensity',
      'safeArea',
      'accentColor',
      'style',
    ],
    dataDriven: true,
  },
};
