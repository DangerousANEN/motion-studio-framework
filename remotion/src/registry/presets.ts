/**
 * The scene-preset registry — assembled from packs.
 *
 * WHAT CHANGED AND WHY
 * --------------------
 * This file used to BE the registry: one object holding every preset. That works
 * until presets are written in parallel. Nine authors adding entries to one
 * object touch the same lines, and the merge that follows is where a preset
 * quietly disappears — the file still compiles, so nothing complains until a
 * spec asks for a name that is no longer there and gets the UNKNOWN PRESET card.
 *
 * So the object is now assembled from packs. Each pack is a separate module with
 * a single owner, and mergeRegistries() throws on a duplicate name across packs.
 * A collision becomes an import-time error naming both packs, instead of a
 * silent last-writer-wins.
 *
 * ADDING A PACK
 * -------------
 *   1. create registry/<pack>.ts exporting `Record<string, PresetDefinition>`
 *   2. import it below and add it to the mergeRegistries() call
 * Nothing else changes: the dispatcher resolves components by name, the Zod
 * enum builds from PRESET_NAMES, rotation reads the dataDriven flag, and the
 * docs generator reads the same metadata.
 *
 * The exports below are unchanged from the single-object version, so every
 * existing consumer keeps working.
 */
import { PresetRegistry, mergeRegistries } from './types';
import { CORE_PRESETS, COMMON_FIELDS } from './core';
import { UI_MOCK_PRESETS } from './ui_mock';
import { MEDIA_PRESETS } from './media';

export { COMMON_FIELDS };

export const PRESETS: PresetRegistry = mergeRegistries(
  CORE_PRESETS,
  UI_MOCK_PRESETS,
  MEDIA_PRESETS
);

/** All preset names, sorted — the source for the Zod enum. */
export const PRESET_NAMES = Object.keys(PRESETS).sort();

/** Presets safe for automatic rotation (not data-dependent). */
export const ROTATION_SAFE = PRESET_NAMES.filter((n) => !PRESETS[n].dataDriven);

/** Presets that must not be substituted by rotation. */
export const DATA_DRIVEN = PRESET_NAMES.filter((n) => PRESETS[n].dataDriven);

export const byCategory = (category: string): string[] =>
  PRESET_NAMES.filter((n) => PRESETS[n].category === category);
