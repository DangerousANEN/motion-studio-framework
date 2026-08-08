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
 */
export const SceneDispatcher: React.FC<BaseSceneProps> = (props) => {
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
