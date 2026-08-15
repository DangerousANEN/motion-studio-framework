import {
  CaseStudyBoard,
  CountdownRing,
  FeatureSpotlight,
  HookStack,
  KineticPhrase,
  MythFact,
  ProblemSolution,
  QuoteEvidence,
  SourceStack,
  StatsBand,
} from '../presets/expansion_narrative';
import {PresetRegistry} from './types';

export const EXPANSION_NARRATIVE_PRESETS: PresetRegistry = {
  HookStack: {component: HookStack, category: 'typography', summary: 'High-retention multi-level hook with urgency and proof pill.', fields: ['headline', 'subhead', 'proof', 'urgency', 'title', 'text'], dataDriven: false},
  KineticPhrase: {component: KineticPhrase, category: 'typography', summary: 'Static-reading phrase anchor between story beats.', fields: ['phrase', 'highlight', 'caption', 'title', 'text'], dataDriven: false},
  ProblemSolution: {component: ProblemSolution, category: 'narrative', summary: 'Directed problem-to-solution contrast with structured copy.', fields: ['problem', 'solution', 'title'], dataDriven: true},
  FeatureSpotlight: {component: FeatureSpotlight, category: 'narrative', summary: 'Single feature, benefit and sequence indicator for product reveals.', fields: ['feature', 'benefit', 'index', 'title'], dataDriven: true},
  CaseStudyBoard: {component: CaseStudyBoard, category: 'narrative', summary: 'Context, action and result board without invented metrics.', fields: ['context', 'action', 'result', 'label', 'title'], dataDriven: true},
  MythFact: {component: MythFact, category: 'narrative', summary: 'Myth-versus-fact education split.', fields: ['myth', 'fact', 'title'], dataDriven: true},
  QuoteEvidence: {component: QuoteEvidence, category: 'narrative', summary: 'Evidence quote with explicit source attribution.', fields: ['quote', 'source', 'role', 'title', 'text'], dataDriven: true},
  StatsBand: {component: StatsBand, category: 'data', summary: 'Two-to-four compact stat blocks with optional footnote.', fields: ['stats', 'title', 'footnote'], dataDriven: true},
  SourceStack: {component: SourceStack, category: 'narrative', summary: 'Verified primary-source stack for evidence-first explainers.', fields: ['sources', 'title', 'status'], dataDriven: true},
  CountdownRing: {component: CountdownRing, category: 'data', summary: 'Ring display for release dates, windows or conditions.', fields: ['value', 'label', 'caption', 'progress', 'title', 'text'], dataDriven: true},
};
