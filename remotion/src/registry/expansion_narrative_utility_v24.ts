import {BrandOutroMosaic, CalendarLaunchWindow, ColdOpenContradiction, CounterfactualSplit, DecisionTree, MemoryTimeline, ProofBackedCTA, TradeoffSliders} from '../presets/expansion_narrative_utility';
import {PresetRegistry} from './types';

export const EXPANSION_NARRATIVE_UTILITY_V24_PRESETS: PresetRegistry = {
  ColdOpenContradiction: {component: ColdOpenContradiction, category: 'narrative', summary: 'First-second contradiction that resolves into the real question.', fields: ['claimA', 'claimB', 'realQuestion', 'proofLabel', 'title'], dataDriven: true},
  CounterfactualSplit: {component: CounterfactualSplit, category: 'narrative', summary: 'Choice A versus choice B outcome split.', fields: ['choiceA', 'choiceB', 'outcomesA', 'outcomesB', 'title'], dataDriven: true},
  MemoryTimeline: {component: MemoryTimeline, category: 'narrative', summary: 'Then-now-next fragment timeline.', fields: ['past', 'present', 'next', 'dates', 'title'], dataDriven: true},
  DecisionTree: {component: DecisionTree, category: 'diagram', summary: 'Constrained data-defined decision path.', fields: ['decisionNodes', 'chosenPath', 'title'], dataDriven: true},
  TradeoffSliders: {component: TradeoffSliders, category: 'data', summary: 'Price, latency, quality, privacy or control trade-off sliders.', fields: ['dimensions', 'takeaway', 'title'], dataDriven: true},
  CalendarLaunchWindow: {component: CalendarLaunchWindow, category: 'narrative', summary: 'Dated release, embargo or deadline window.', fields: ['date', 'window', 'timezone', 'whatChanges', 'source', 'title'], dataDriven: true},
  ProofBackedCTA: {component: ProofBackedCTA, category: 'narrative', summary: 'Source, benefit and meaningful next action CTA.', fields: ['proof', 'benefit', 'action', 'channel', 'url', 'title'], dataDriven: true},
  BrandOutroMosaic: {component: BrandOutroMosaic, category: 'media', summary: 'Product-evidence-community brand outro mosaic.', fields: ['media', 'brandName', 'handle', 'cta', 'logoUrl', 'title'], dataDriven: true},
};
