import React from 'react';
import { Audio, staticFile } from 'remotion';
import { TransitionSeries } from '@remotion/transitions';
import { VideoSpec } from '../VideoSpec.schema';
import { SceneDispatcher } from './SceneDispatcher';
import { EffectStack } from './EffectStack';
import { OverlayStack } from './OverlayStack';
import { PostFX } from '../fx/PostFX';
import { StyleProvider, mergeStyleConfig, useStyle } from '../theme/StyleContext';
import { buildPresentation, buildTiming, getTransitionPlan } from '../lib/transitions';

/** Scene content is graded; HUD overlays intentionally remain outside the grade. */
const StyledScene: React.FC<{ scene: VideoSpec['scenes'][number] }> = ({ scene }) => {
  const { kit } = useStyle();
  return (
    <>
      <PostFX effects={kit.effects}>
        <EffectStack effects={scene.effects}>
          <SceneDispatcher {...scene} />
        </EffectStack>
      </PostFX>
      <OverlayStack overlays={scene.overlays} />
    </>
  );
};

/** The visual canvas reads the resolved family palette rather than a hardcoded bg. */
const StyledTimeline: React.FC<VideoSpec> = ({
  scenes,
  audioUrl,
  width,
  height,
  style,
  styleConfig,
}) => {
  const { theme } = useStyle();
  const plan = getTransitionPlan(scenes);
  const transitionBefore = new Map(plan.transitions.map((item) => [item.beforeSceneIndex, item]));
  const resolveSrc = (src: string) => (src.startsWith('http') ? src : staticFile(src));

  return (
    <div style={{ flex: 1, backgroundColor: theme.bg, display: 'flex' }}>
      {audioUrl && <Audio src={resolveSrc(audioUrl)} />}
      <TransitionSeries>
        {scenes.flatMap((scene, index) => {
          const planned = transitionBefore.get(index);
          const sequence = (
            <TransitionSeries.Sequence key={scene.id} durationInFrames={scene.durationInFrames}>
              {scene.audioUrl && <Audio src={resolveSrc(scene.audioUrl)} />}
              <StyleProvider
                style={scene.style ?? style}
                accentColor={scene.accentColor}
                config={mergeStyleConfig(styleConfig, scene.styleConfig)}
              >
                <StyledScene scene={scene} />
              </StyleProvider>
            </TransitionSeries.Sequence>
          );
          if (!planned) return [sequence];
          return [
            <TransitionSeries.Transition
              key={`${scene.id}-transition`}
              presentation={buildPresentation({ config: planned.config, width, height })}
              timing={buildTiming({ ...planned.config, durationInFrames: planned.durationInFrames })}
            />,
            sequence,
          ];
        })}
      </TransitionSeries>
    </div>
  );
};

/** Main Remotion composition: named style family plus optional safe token overrides. */
export const MainComposition: React.FC<VideoSpec> = (props) => (
  <StyleProvider style={props.style} config={props.styleConfig}>
    <StyledTimeline {...props} />
  </StyleProvider>
);
