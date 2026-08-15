import {BenchmarkArena, BenchmarkHeatmap, CapabilityRadar, ClaimEvidenceChain, ContextWindowLadder, CostQualityScatter, EvidenceConflictBoard, ExperimentProtocol, LeaderboardRace, ReleaseDelta, TokenFlowSankey, TrueCostCalculator} from '../presets/expansion_research';
import {PresetRegistry} from './types';

export const EXPANSION_RESEARCH_V24_PRESETS: PresetRegistry = {
  BenchmarkArena: {component: BenchmarkArena, category: 'data', summary: 'Head-to-head model benchmark arena with value-preserving score bars.', fields: ['models', 'benchmark', 'source', 'title'], dataDriven: true},
  BenchmarkHeatmap: {component: BenchmarkHeatmap, category: 'data', summary: 'Models × benchmarks heatmap matrix for structured evidence.', fields: ['rows', 'columns', 'source', 'title'], dataDriven: true},
  LeaderboardRace: {component: LeaderboardRace, category: 'data', summary: 'Transparent before/after ranking movement without invented deltas.', fields: ['rankBefore', 'rankAfter', 'metric', 'asOf', 'title'], dataDriven: true},
  CostQualityScatter: {component: CostQualityScatter, category: 'data', summary: 'Cost versus quality scatter plot with supplied data points.', fields: ['scatterPoints', 'xLabel', 'yLabel', 'source', 'title'], dataDriven: true},
  CapabilityRadar: {component: CapabilityRadar, category: 'data', summary: 'Multi-axis capability comparison radar.', fields: ['axes', 'series', 'source', 'title'], dataDriven: true},
  ContextWindowLadder: {component: ContextWindowLadder, category: 'data', summary: 'Context-capacity ladder with practical captions.', fields: ['items', 'unit', 'asOf', 'title'], dataDriven: true},
  TrueCostCalculator: {component: TrueCostCalculator, category: 'data', summary: 'Workload cost decomposition for input, output, cache and retries.', fields: ['lineItems', 'total', 'currency', 'method', 'title'], dataDriven: true},
  TokenFlowSankey: {component: TokenFlowSankey, category: 'diagram', summary: 'Token flow rows and value-preserving link story.', fields: ['flowNodes', 'links', 'unit', 'source', 'title'], dataDriven: true},
  ClaimEvidenceChain: {component: ClaimEvidenceChain, category: 'narrative', summary: 'Claim-to-evidence chain with caveat and source discipline.', fields: ['claim', 'evidence', 'caveat', 'title'], dataDriven: true},
  EvidenceConflictBoard: {component: EvidenceConflictBoard, category: 'narrative', summary: 'Two-source disagreement board for transparent uncertainty.', fields: ['claim', 'sourceA', 'sourceB', 'difference', 'title'], dataDriven: true},
  ExperimentProtocol: {component: ExperimentProtocol, category: 'diagram', summary: 'Reproducible test recipe: inputs, settings, metric and threshold.', fields: ['steps', 'metric', 'threshold', 'title'], dataDriven: true},
  ReleaseDelta: {component: ReleaseDelta, category: 'narrative', summary: 'Dated version-to-version release delta.', fields: ['previous', 'current', 'deltas', 'sources', 'title'], dataDriven: true},
};
