import { z } from 'zod';

/**
 * Wire contract between msf/spec.py and the Remotion renderer.
 *
 * Adding a field here alone is not enough — Scene in msf/spec.py must emit it,
 * and validate_spec() should reject specs that would render a placeholder.
 */

export const PresetTypeSchema = z.enum([
  // 2D typographic / layout
  'HeroKinetic',
  'StatCounter',
  'GridGridFloor',
  'SwipePanels',
  'TypewriterSub',
  'CompareSplit',
  'FlowDiagram',
  'CodeReveal',
  'QuoteCard',
  // 3D (Three.js / React Three Fiber)
  'TokenCloud3D',
  'LayerStack3D',
]);

export type PresetType = z.infer<typeof PresetTypeSchema>;

/** Presets a low-capability agent may use without writing any code. */
export const SAFE_PRESETS: PresetType[] = [
  'HeroKinetic',
  'StatCounter',
  'GridGridFloor',
  'SwipePanels',
  'TypewriterSub',
  'CompareSplit',
  'FlowDiagram',
  'CodeReveal',
  'QuoteCard',
  'TokenCloud3D',
  'LayerStack3D',
];

/** Presets that need structured data and must not be swapped in by rotation. */
export const DATA_DRIVEN_PRESETS: PresetType[] = [
  'StatCounter',
  'SwipePanels',
  'CompareSplit',
  'FlowDiagram',
  'CodeReveal',
  'LayerStack3D',
];

export const VideoFormatSchema = z.enum([
  'vertical',
  'horizontal',
  'square',
  'classic',
  'cinema',
  'custom',
]);

export const ThemeSchema = z.enum(['pop', 'noir', 'glass', 'blueprint', 'sunset']);
export type ThemeName = z.infer<typeof ThemeSchema>;

export const CardSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
  tag: z.string().optional(),
  color: z.string().optional(),
  value: z.string().optional(),
  icon: z.string().optional(),
});

export const NodeSchema = z.object({
  label: z.string(),
  sub: z.string().optional(),
  color: z.string().optional(),
});

export const StepSchema = z.object({
  label: z.string(),
  detail: z.string().optional(),
});

export const BaseSceneSchema = z
  .object({
    id: z.string().default('scene-1'),
    durationInFrames: z.number().int().positive(),
    preset: PresetTypeSchema.default('HeroKinetic'),
    title: z.string().optional(),
    subtitle: z.string().optional(),
    text: z.string().optional(),
    bodyText: z.string().optional(),
    accentColor: z.string().optional(),
    badge: z.string().optional(),
    style: z.string().optional(),
    // StatCounter
    statValue: z.number().optional(),
    statPrefix: z.string().optional(),
    statSuffix: z.string().optional(),
    statLabel: z.string().optional(),
    // SwipePanels / CompareSplit / ListReveal
    cards: z.array(CardSchema).optional(),
    // FlowDiagram
    nodes: z.array(NodeSchema).optional(),
    steps: z.array(StepSchema).optional(),
    // CodeReveal
    code: z.string().optional(),
    language: z.string().optional(),
    // QuoteCard
    author: z.string().optional(),
    role: z.string().optional(),
    // 3D presets
    modelUrl: z.string().optional(),
    modelScale: z.number().optional(),
    orbitSpeed: z.number().optional(),
    audioUrl: z.string().optional(),
    // TokenCloud3D
    pointCount: z.number().int().positive().max(4000).optional(),
    // LayerStack3D
    layers: z.array(z.string()).optional(),
  })
  .passthrough();

export const VideoSpecSchema = z.object({
  width: z.number().int().default(1080),
  height: z.number().int().default(1920),
  fps: z.number().int().default(60),
  durationInFrames: z.number().int().optional(),
  format: VideoFormatSchema.default('vertical'),
  safeMargin: z.number().default(120),
  theme: ThemeSchema.default('pop'),
  brandColors: z
    .object({
      bg: z.string().default('#0E0F11'),
      surface: z.string().default('#16181C'),
      gold: z.string().default('#E6C475'),
      neon: z.string().default('#00FF88'),
      cyan: z.string().default('#00D4FF'),
      text: z.string().default('#FFFFFF'),
      muted: z.string().default('#8B92A0'),
    })
    .default({
      bg: '#0E0F11',
      surface: '#16181C',
      gold: '#E6C475',
      neon: '#00FF88',
      cyan: '#00D4FF',
      text: '#FFFFFF',
      muted: '#8B92A0',
    }),
  audioUrl: z.string().optional(),
  scenes: z.array(BaseSceneSchema).min(1),
});

export type BaseSceneProps = z.infer<typeof BaseSceneSchema>;
export type VideoSpec = z.infer<typeof VideoSpecSchema>;
export type Card = z.infer<typeof CardSchema>;
export type FlowNode = z.infer<typeof NodeSchema>;
export type FlowStep = z.infer<typeof StepSchema>;
