/**
 * Learn preset pack — educational and explanatory scenes.
 *
 * Four presets for interactive, data-driven educational content:
 *   QuizCard       — question + multiple choice with reveal animation
 *   ProgressPath   — roadmap/checklist with animated connector line
 *   DefinitionCard — term + typewriter definition reveal
 *   TimelineReveal — chronology axis with sequential event reveal
 *
 * ADDING THIS PACK TO THE REGISTRY
 * ---------------------------------
 * This pack is intentionally NOT imported in src/registry/presets.ts.
 * The parent agent connects packs explicitly. To wire it:
 *
 *   import { LEARN_PRESETS } from './learn';
 *   // add LEARN_PRESETS to the mergeRegistries() call in presets.ts
 *
 * This avoids merge conflicts and keeps pack ownership clear.
 */
import {
  QuizCard,
  ProgressPath,
  DefinitionCard,
  TimelineReveal,
} from '../presets/learn';
import { PresetRegistry } from './types';

export const LEARN_PRESETS: PresetRegistry = {
  QuizCard: {
    component: QuizCard,
    category: 'narrative',
    summary:
      'Quiz question with staggered options; correct answer revealed with green highlight + ✓.',
    fields: ['question', 'options', 'correctIndex', 'revealAtProgress', 'title'],
    dataDriven: true,
  },
  ProgressPath: {
    component: ProgressPath,
    category: 'diagram',
    summary:
      'Roadmap / checklist: steps connected by an animated line, current step pulses.',
    fields: ['steps', 'currentStep', 'title', 'orientation'],
    dataDriven: true,
  },
  DefinitionCard: {
    component: DefinitionCard,
    category: 'typography',
    summary:
      'Term headline + typewriter definition reveal, accent bar, optional mono example.',
    fields: ['term', 'definition', 'example', 'source', 'title'],
    dataDriven: true,
  },
  TimelineReveal: {
    component: TimelineReveal,
    category: 'narrative',
    summary:
      'Chronology axis: events appear sequentially, active event expands with description.',
    fields: ['events', 'title'],
    dataDriven: true,
  },
};
