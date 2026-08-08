import { z } from 'zod';

export const PresetTypeSchema = z.enum([
  'HeroKinetic',
  'StatCounter',
  'GridGridFloor',
  'SwipePanels',
  'TypewriterSub',
]);

export type PresetType = z.infer<typeof PresetTypeSchema>;

export const SAFE_PRESETS: PresetType[] = [
  'HeroKinetic',
  'StatCounter',
  'GridGridFloor',
  'SwipePanels',
  'TypewriterSub',
];

export const BaseSceneSchema = z.object({
  id: z.string().default('scene-1'),
  durationInFrames: z.number().int().positive(),
  preset: PresetTypeSchema.default('HeroKinetic'),
  title: z.string().optional(),
  subtitle: z.string().optional(),
  text: z.string().optional(),
  bodyText: z.string().optional(),
  accentColor: z.string().optional(),
  badge: z.string().optional(),
  // Preset specific optional fields
  statValue: z.number().optional(),
  statPrefix: z.string().optional(),
  statSuffix: z.string().optional(),
  statLabel: z.string().optional(),
  cards: z
    .array(
      z.object({
        title: z.string(),
        description: z.string().optional(),
        tag: z.string().optional(),
        color: z.string().optional(),
      })
    )
    .optional(),
  audioUrl: z.string().optional(),
}).passthrough();

export const VideoSpecSchema = z.object({
  width: z.number().int().default(1080),
  height: z.number().int().default(1920),
  fps: z.number().int().default(60),
  durationInFrames: z.number().int().optional(),
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
