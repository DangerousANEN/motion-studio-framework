import React from 'react';
import { Composition, getInputProps } from 'remotion';
import { MainComposition } from './compositions/Main';
import { BaseSceneSchema, VideoSpec, VideoSpecSchema } from './VideoSpec.schema';

import { GridGridFloor } from './presets/GridGridFloor';
import { HeroKinetic } from './presets/HeroKinetic';
import { StatCounter } from './presets/StatCounter';
import { SwipePanels } from './presets/SwipePanels';
import { TypewriterSub } from './presets/TypewriterSub';

export const RemotionRoot: React.FC = () => {
  const inputProps = getInputProps() as Partial<VideoSpec>;
  const parsedSpec = VideoSpecSchema.parse(inputProps);

  const totalDuration = parsedSpec.scenes.reduce(
    (acc, scene) => acc + scene.durationInFrames,
    0
  );

  return (
    <>
      {/* Main Full Video Composition (Series of Scenes) */}
      <Composition
        id="Main"
        component={MainComposition}
        durationInFrames={totalDuration || parsedSpec.durationInFrames}
        fps={parsedSpec.fps}
        width={parsedSpec.width}
        height={parsedSpec.height}
        defaultProps={parsedSpec}
      />

      {/* Standalone Preset Compositions for individual testing */}
      <Composition
        id="HeroKinetic"
        component={HeroKinetic}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
        schema={BaseSceneSchema}
        defaultProps={{
          id: 'hero-1',
          durationInFrames: 90,
          preset: 'HeroKinetic',
          title: 'MOTION STUDIO',
          subtitle: 'KINETIC TYPOGRAPHY',
        }}
      />

      <Composition
        id="StatCounter"
        component={StatCounter}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
        schema={BaseSceneSchema}
        defaultProps={{
          id: 'stat-1',
          durationInFrames: 90,
          preset: 'StatCounter',
          statValue: 100,
          statSuffix: '%',
          statLabel: 'AUTOMATED MOTION',
        }}
      />

      <Composition
        id="GridGridFloor"
        component={GridGridFloor}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
        schema={BaseSceneSchema}
        defaultProps={{
          id: 'grid-1',
          durationInFrames: 90,
          preset: 'GridGridFloor',
          title: 'NEO-BRUTALISM',
          subtitle: '3D Wireframe Perspective',
        }}
      />

      <Composition
        id="SwipePanels"
        component={SwipePanels}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
        schema={BaseSceneSchema}
        defaultProps={{
          id: 'swipe-1',
          durationInFrames: 90,
          preset: 'SwipePanels',
          title: 'FEATURES',
          cards: [
            { title: 'Zero-Shot TTS', description: 'Qwen3 1.7B Voice Cloning', tag: 'AI' },
            { title: 'Spring Motion', description: 'Overshoot typography', tag: 'UX' },
            { title: 'Remotion React', description: 'Pixel-perfect 60 FPS', tag: 'DEV' },
          ],
        }}
      />

      <Composition
        id="TypewriterSub"
        component={TypewriterSub}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
        schema={BaseSceneSchema}
        defaultProps={{
          id: 'typewriter-1',
          durationInFrames: 90,
          preset: 'TypewriterSub',
          text: 'Ищете лучшие оупен сорс решения в области ИИ? Канал LLM Hubs ваш главный источник.',
        }}
      />
    </>
  );
};
