/**
 * Component registry — the single place a scene preset is declared.
 *
 * WHY THIS EXISTS
 * ---------------
 * Adding a preset used to mean editing four files that had to agree:
 *   1. an import in SceneDispatcher.tsx
 *   2. a `case` in its switch
 *   3. the Zod enum in VideoSpec.schema.ts
 *   4. the SAFE_PRESETS / DATA_DRIVEN_PRESETS arrays
 * Miss one and the failure is silent-ish: the spec validates but renders the
 * UNKNOWN PRESET card, or the preset renders but rotation never picks it. That
 * is survivable for 13 presets and hopeless for 100+, especially with several
 * authors touching the same switch statement at once.
 *
 * Here a preset is declared ONCE, next to nothing else, and everything else is
 * derived: the dispatcher looks components up by name, the schema builds its
 * enum from the keys, and the docs generator reads the same metadata.
 *
 * CONTRACT
 * --------
 * Every entry must supply:
 *   component  the React component, taking BaseSceneProps
 *   category   what kind of scene it is, for docs and for rotation buckets
 *   summary    one line, shown in `msf scenes list` and the generated docs
 *   fields     which spec fields it actually reads -- used by the CLI to
 *              scaffold a valid scene and by the validator to warn about
 *              fields that will be ignored
 *   dataDriven true when the preset is meaningless without its data (a chart
 *              with no numbers), so rotation must not substitute it blindly
 *
 * Keep `fields` honest. It is the machine-readable answer to "what can I pass
 * to this preset", and a wrong entry sends an agent down a dead end.
 */
import React from 'react';
import { BaseSceneProps } from '../VideoSpec.schema';

export type PresetCategory =
  | 'typography'
  | 'data'
  | 'diagram'
  | 'code'
  | 'ui-mock'
  | 'device'
  | 'three'
  | 'narrative'
  | 'transition-aid';

export interface PresetDefinition {
  component: React.FC<BaseSceneProps>;
  category: PresetCategory;
  summary: string;
  /** Spec fields this preset reads. Anything else passed to it is ignored. */
  fields: string[];
  /** Requires structured data; rotation must not swap it in arbitrarily. */
  dataDriven?: boolean;
  /** Needs a WebGL canvas — heavier to render, useful for budgeting. */
  three?: boolean;
}

export type PresetRegistry = Record<string, PresetDefinition>;

/**
 * Merge helper so preset packs can live in their own files and be combined
 * without one pack silently overwriting another's name.
 */
export const mergeRegistries = (...packs: PresetRegistry[]): PresetRegistry => {
  const out: PresetRegistry = {};
  for (const pack of packs) {
    for (const [name, def] of Object.entries(pack)) {
      if (out[name]) {
        throw new Error(
          `Duplicate preset name "${name}". Two packs declare it; rename one — ` +
            'the dispatcher resolves by name and would silently pick the last.'
        );
      }
      out[name] = def;
    }
  }
  return out;
};
