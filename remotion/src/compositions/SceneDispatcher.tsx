import React from 'react';
import { BaseSceneProps } from '../VideoSpec.schema';
import { GridGridFloor } from '../presets/GridGridFloor';
import { HeroKinetic } from '../presets/HeroKinetic';
import { StatCounter } from '../presets/StatCounter';
import { SwipePanels } from '../presets/SwipePanels';
import { TypewriterSub } from '../presets/TypewriterSub';

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
    default:
      return <HeroKinetic {...props} />;
  }
};
