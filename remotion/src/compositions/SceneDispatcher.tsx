import React from 'react';
import { BaseSceneProps } from '../VideoSpec.schema';
import { CodeReveal } from '../presets/CodeReveal';
import { CompareSplit } from '../presets/CompareSplit';
import { FlowDiagram } from '../presets/FlowDiagram';
import { GridGridFloor } from '../presets/GridGridFloor';
import { HeroKinetic } from '../presets/HeroKinetic';
import { QuoteCard } from '../presets/QuoteCard';
import { StatCounter } from '../presets/StatCounter';
import { SwipePanels } from '../presets/SwipePanels';
import { TypewriterSub } from '../presets/TypewriterSub';
import { LayerStack3D } from '../presets/three/LayerStack3D';
import { TokenCloud3D } from '../presets/three/TokenCloud3D';

/**
 * Maps spec preset names to components. An unknown preset renders a loud error
 * card rather than silently falling back, so a typo in the spec fails Vision QA
 * instead of shipping the wrong template.
 *
 * SCENE ISOLATION -- do not remove the wrapper below.
 * Several presets put `zIndex: 5` on their foreground cards to sit above their
 * own background layer. A z-index only competes inside a stacking context, and
 * the transition wrappers do not create one, so those cards used to be promoted
 * into the *composition* stacking context. The practical effect: during a
 * crossfade the OUTGOING scene's card painted on top of the fully-opaque
 * incoming scene for the whole overlap, so the picture appeared to hard-cut at
 * the end of the transition instead of blending. Measured on a 24-frame fade:
 * 80-87% of the total colour change happened in the single frame 59->60.
 *
 * `isolation: 'isolate'` forces a stacking context per scene, keeping each
 * preset's z-indices local so the transition's opacity/transform actually
 * composites the two layers. Verified: the same fade then moves its largest
 * single-frame delta down to ~16% of range and spreads the change across the
 * overlap.
 */
export const SceneDispatcher: React.FC<BaseSceneProps> = (props) => {
  // Absolutely filled rather than `flex: 1`: a flex child only gets height when
  // its parent is a flex container, and TransitionSeries.Sequence is not one.
  // With `flex: 1` this wrapper collapsed to zero height and every preset that
  // sizes itself from the parent (StatCounter, CodeReveal, QuoteCard) rendered a
  // blank frame -- presets built on AbsoluteFill kept working, which is what made
  // it look preset-specific. Inset-0 makes the wrapper independent of the parent's
  // layout mode.
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        isolation: 'isolate',
      }}
    >
      <ScenePreset {...props} />
    </div>
  );
};

const ScenePreset: React.FC<BaseSceneProps> = (props) => {
  switch (props.preset) {
    case 'HeroKinetic':
      return <HeroKinetic {...props} />;
    case 'StatCounter':
      return <StatCounter {...props} />;
    case 'GridGridFloor':
      return <GridGridFloor {...props} />;
    case 'SwipePanels':
      return <SwipePanels {...props} />;
    case 'TypewriterSub':
      return <TypewriterSub {...props} />;
    case 'CompareSplit':
      return <CompareSplit {...props} />;
    case 'FlowDiagram':
      return <FlowDiagram {...props} />;
    case 'CodeReveal':
      return <CodeReveal {...props} />;
    case 'QuoteCard':
      return <QuoteCard {...props} />;
    case 'TokenCloud3D':
      return <TokenCloud3D {...props} />;
    case 'LayerStack3D':
      return <LayerStack3D {...props} />;
    default:
      return (
        <div
          style={{
            flex: 1,
            backgroundColor: '#3A0A0A',
            color: '#FFFFFF',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            fontSize: '38px',
            padding: '60px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '80px', marginBottom: '20px' }}>⚠</div>
          UNKNOWN PRESET
          <div style={{ fontSize: '30px', color: '#FFB4B4', marginTop: '14px' }}>
            {String(props.preset)}
          </div>
        </div>
      );
  }
};
