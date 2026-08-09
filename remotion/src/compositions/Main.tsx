import React from 'react';
import { Audio, staticFile } from 'remotion';
import { TransitionSeries } from '@remotion/transitions';
import { VideoSpec } from '../VideoSpec.schema';
import { SceneDispatcher } from './SceneDispatcher';
import { buildPresentation, buildTiming, getTransitionPlan } from '../lib/transitions';

/**
 * Scene timeline.
 *
 * Uses <TransitionSeries> rather than <Series> so scenes cross-fade instead of
 * hard-cutting. The composition length is computed by the same getTransitionPlan()
 * that lays out this series (see Root.tsx) -- transitions consume timeline, so
 * the two must agree or the voice-over drifts out of sync with the picture.
 */
export const MainComposition: React.FC<VideoSpec> = ({ scenes, audioUrl, width, height }) => {
  const plan = getTransitionPlan(scenes);

  // Index the plan by the scene it precedes for O(1) lookup while mapping.
  const transitionBefore = new Map(
    plan.transitions.map((t) => [t.beforeSceneIndex, t])
  );

  const resolveSrc = (src: string) => (src.startsWith('http') ? src : staticFile(src));

  return (
    <div style={{ flex: 1, backgroundColor: '#0E0F11', display: 'flex' }}>
      {audioUrl && <Audio src={resolveSrc(audioUrl)} />}
      <TransitionSeries>
        {scenes.flatMap((scene, index) => {
          const planned = transitionBefore.get(index);

          const sequence = (
            <TransitionSeries.Sequence
              key={scene.id}
              durationInFrames={scene.durationInFrames}
            >
              {scene.audioUrl && <Audio src={resolveSrc(scene.audioUrl)} />}
              <SceneDispatcher {...scene} />
            </TransitionSeries.Sequence>
          );

          if (!planned) {
            return [sequence];
          }

          return [
            <TransitionSeries.Transition
              key={`${scene.id}-transition`}
              presentation={buildPresentation({
                config: planned.config,
                width,
                height,
              })}
              timing={buildTiming({
                ...planned.config,
                durationInFrames: planned.durationInFrames,
              })}
            />,
            sequence,
          ];
        })}
      </TransitionSeries>
    </div>
  );
};
