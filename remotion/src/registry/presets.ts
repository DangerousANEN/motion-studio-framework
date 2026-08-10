/**
 * The registry of every scene preset MSF can render.
 *
 * Add a preset by adding ONE entry here. SceneDispatcher, the Zod enum, the
 * rotation buckets and the generated docs all read from this object, so there
 * is no second place to keep in sync.
 *
 * Ordering is by category then name, purely for readability.
 */
import { CodeReveal } from '../presets/CodeReveal';
import { CompareSplit } from '../presets/CompareSplit';
import { DonutFill } from '../presets/DonutFill';
import { FlowDiagram } from '../presets/FlowDiagram';
import { GridGridFloor } from '../presets/GridGridFloor';
import { HeroKinetic } from '../presets/HeroKinetic';
import { QuoteCard } from '../presets/QuoteCard';
import { StatCounter } from '../presets/StatCounter';
import { SwipePanels } from '../presets/SwipePanels';
import { TypewriterSub } from '../presets/TypewriterSub';
import { LayerStack3D } from '../presets/three/LayerStack3D';
import { ModelOrbit3D } from '../presets/three/ModelOrbit3D';
import { TokenCloud3D } from '../presets/three/TokenCloud3D';
import { PresetRegistry } from './types';

/** Fields every preset understands, so entries only list what is extra. */
export const COMMON_FIELDS = [
  'id',
  'durationInFrames',
  'preset',
  'accentColor',
  'motion',
  'intensity',
  'safeArea',
  'transition',
];

export const PRESETS: PresetRegistry = {
  // ---- typography -------------------------------------------------------
  HeroKinetic: {
    component: HeroKinetic,
    category: 'typography',
    summary: 'Big kinetic headline with an optional kicker and badge.',
    fields: ['title', 'subtitle', 'badge'],
  },
  TypewriterSub: {
    component: TypewriterSub,
    category: 'typography',
    summary: 'Long text revealed word by word at a readable pace.',
    fields: ['text', 'title'],
  },
  QuoteCard: {
    component: QuoteCard,
    category: 'narrative',
    summary: 'Pull quote on a card with attribution.',
    fields: ['text', 'author', 'role', 'title'],
  },

  // ---- data -------------------------------------------------------------
  StatCounter: {
    component: StatCounter,
    category: 'data',
    summary: 'One number counting up, with prefix/suffix and a label.',
    fields: ['statValue', 'statPrefix', 'statSuffix', 'statLabel', 'title'],
    dataDriven: true,
  },
  DonutFill: {
    component: DonutFill,
    category: 'data',
    summary: 'Segmented donut/pie whose arcs and counters stay in lockstep.',
    fields: [
      'segments',
      'shape',
      'thickness',
      'fillMode',
      'centerContent',
      'labelPlacement',
      'percentCounters',
      'gapAngle',
      'highlightSegment',
      'valueSuffix',
      'title',
    ],
    dataDriven: true,
  },
  CompareSplit: {
    component: CompareSplit,
    category: 'data',
    summary: 'Two options side by side with a VS badge.',
    fields: ['cards', 'title'],
    dataDriven: true,
  },

  // ---- diagram ----------------------------------------------------------
  FlowDiagram: {
    component: FlowDiagram,
    category: 'diagram',
    summary: 'Connected nodes forming a pipeline or process.',
    fields: ['nodes', 'steps', 'title'],
    dataDriven: true,
  },
  SwipePanels: {
    component: SwipePanels,
    category: 'diagram',
    summary: 'A list of feature panels sliding in one after another.',
    fields: ['cards', 'title'],
    dataDriven: true,
  },
  GridGridFloor: {
    component: GridGridFloor,
    category: 'typography',
    summary: 'Headline over a perspective grid floor.',
    fields: ['title', 'subtitle', 'badge'],
  },

  // ---- code -------------------------------------------------------------
  CodeReveal: {
    component: CodeReveal,
    category: 'code',
    summary: 'Syntax-highlighted code revealed line by line.',
    fields: ['code', 'language', 'title'],
    dataDriven: true,
  },

  // ---- three ------------------------------------------------------------
  ModelOrbit3D: {
    component: ModelOrbit3D,
    category: 'three',
    summary: 'Camera orbit around a real .glb model with studio lighting.',
    fields: [
      'modelUrl',
      'modelScale',
      'orbit',
      'orbitDegrees',
      'startAngle',
      'elevation',
      'autoFrame',
      'spinModel',
      'lighting',
      'env',
      'groundShadow',
      'material',
      'hotspots',
      'title',
      'subtitle',
      'badge',
    ],
    three: true,
  },
  TokenCloud3D: {
    component: TokenCloud3D,
    category: 'three',
    summary: 'Point cloud of tokens clustering into semantic groups.',
    fields: ['pointCount', 'title', 'subtitle'],
    three: true,
  },
  LayerStack3D: {
    component: LayerStack3D,
    category: 'three',
    summary: 'Stacked slabs rising with a signal pulse travelling through.',
    fields: ['layers', 'title', 'subtitle'],
    dataDriven: true,
    three: true,
  },
};

/** All preset names, sorted — the source for the Zod enum. */
export const PRESET_NAMES = Object.keys(PRESETS).sort();

/** Presets safe for automatic rotation (not data-dependent). */
export const ROTATION_SAFE = PRESET_NAMES.filter((n) => !PRESETS[n].dataDriven);

/** Presets that must not be substituted by rotation. */
export const DATA_DRIVEN = PRESET_NAMES.filter((n) => PRESETS[n].dataDriven);

export const byCategory = (category: string): string[] =>
  PRESET_NAMES.filter((n) => PRESETS[n].category === category);
