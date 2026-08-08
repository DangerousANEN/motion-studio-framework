import { z } from 'zod';

export const PresetTypeSchema = z.enum([
  'HeroKinetic',
  'StatCounter',
  'GridGridFloor',
  'SwipePanels',
  'TypewriterSub',
]);

export type PresetType = z.infer<typeof PresetTypeSchema>;

export const BaseSceneSchema = z.object({
  id: z.string().default('scene-1'),
  durationInFrames: z.number().int().positive().default(90),
  preset: PresetTypeSchema.default('HeroKinetic'),
  title: z.string().optional(),
  subtitle: z.string().optional(),
  text: z.string().optional(),
  accentColor: z.string().optional(),
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
});

export const VideoSpecSchema = z.object({
  width: z.number().int().default(1080),
  height: z.number().int().default(1920),
  fps: z.number().int().default(30),
  durationInFrames: z.number().int().default(300),
  brandColors: z
    .object({
      bg: z.string().default('#0E0F11'),
      surface: z.string().default('#16181C'),
      gold: z.string().default('#E6C475'),
      neon: z.string().default('#00FF88'),
    })
    .default({
      bg: '#0E0F11',
      surface: '#16181C',
      gold: '#E6C475',
      neon: '#00FF88',
    }),
  audioUrl: z.string().optional(),
  scenes: z.array(BaseSceneSchema).default([
    {
      id: 'scene-1',
      durationInFrames: 90,
      preset: 'HeroKinetic',
      title: 'MOTION STUDIO',
      subtitle: 'Next-Gen Remotion Engine',
    },
    {
      id: 'scene-2',
      durationInFrames: 90,
      preset: 'StatCounter',
      statValue: 100,
      statSuffix: '%',
      statLabel: 'AUTOMATED MOTION',
    },
    {
      id: 'scene-3',
      durationInFrames: 90,
      preset: 'GridGridFloor',
      title: 'NEO-BRUTALISM',
      subtitle: '3D Wireframe Perspective',
    },
    {
      id: 'scene-4',
      durationInFrames: 90,
      preset: 'SwipePanels',
      title: 'FEATURES',
      cards: [
        { title: 'Zero-Shot TTS', description: 'Qwen3 1.7B Voice Cloning', tag: 'AI' },
        { title: 'Spring Motion', description: 'Overshoot typography', tag: 'UX' },
        { title: 'Remotion React', description: 'Pixel-perfect 60 FPS', tag: 'DEV' },
      ],
    },
    {
      id: 'scene-5',
      durationInFrames: 90,
      preset: 'TypewriterSub',
      text: 'Ищете лучшие оупен сорс решения в области ИИ? Канал LLM Hubs ваш главный источник.',
    },
  ]),
});

export type BaseSceneProps = z.infer<typeof BaseSceneSchema>;
export type VideoSpec = z.infer<typeof VideoSpecSchema>;
