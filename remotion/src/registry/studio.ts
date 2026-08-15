/**
 * Studio preset pack — reusable business/explainer scenes for MSF Studio v2.
 *
 * Kept separate from core/learn packs to give scene authoring a clean ownership
 * boundary. `mergeRegistries()` rejects duplicate names when this pack is wired
 * into the top-level registry.
 */
import { BeforeAfter, DecisionGrid, MetricTrend, StepList } from '../presets/studio';
import { LlmHubsCTA } from '../presets/llm_hubs';
import { PresetRegistry } from './types';

export const STUDIO_PRESETS: PresetRegistry = {
  LlmHubsCTA: {
    component: LlmHubsCTA,
    category: 'narrative',
    summary: 'Branded LLM Hubs subscription CTA with supplied avatar and fixed @llm_hubs handle.',
    fields: ['title', 'text'],
    dataDriven: false,
  },
  DecisionGrid: {
    component: DecisionGrid,
    category: 'narrative',
    summary: 'Bounded 2–4 option decision matrix for provider, workflow or tool choice.',
    fields: ['cards', 'title'],
    dataDriven: true,
  },
  StepList: {
    component: StepList,
    category: 'diagram',
    summary: 'Numbered procedure or checklist with staggered, readable steps.',
    fields: ['steps', 'title'],
    dataDriven: true,
  },
  BeforeAfter: {
    component: BeforeAfter,
    category: 'narrative',
    summary: 'Side-by-side before/after transformation with structured copy.',
    fields: ['before', 'after', 'title'],
    dataDriven: true,
  },
  MetricTrend: {
    component: MetricTrend,
    category: 'data',
    summary: 'Short labelled trend line for growth, adoption or progress.',
    fields: ['points', 'metricLabel', 'valueSuffix', 'title'],
    dataDriven: true,
  },
};
