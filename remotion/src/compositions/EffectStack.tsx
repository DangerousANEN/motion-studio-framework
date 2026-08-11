import React from 'react';
import { EFFECTS } from '../registry/effects';
import { VISUAL_EFFECTS } from '../registry/effects_visual';
import { SCENE_EFFECTS } from '../registry/effects_scene';

/**
 * Wraps a scene in its declared effects.
 *
 * The three effect packs are looked up in order and merged into one namespace,
 * so a spec just names an effect without caring which family it came from.
 * Unknown names are skipped rather than thrown: a spec that mentions an effect
 * this build does not have should render the scene, not an error card. The
 * skipped name is logged so it still surfaces during a render.
 *
 * Effects are applied so that the FIRST entry ends up outermost. That makes a
 * spec read top-down the way it composes: a camera move listed before a grade
 * contains the graded content, not the other way round.
 */
export interface SceneEffectRef {
  name: string;
  intensity?: number;
  seed?: number;
}

type AnyEffectComponent = React.ComponentType<{
  children: React.ReactNode;
  intensity?: number;
  seed?: number;
}>;

const lookup = (name: string): AnyEffectComponent | null => {
  const entry =
    (EFFECTS as Record<string, { component: AnyEffectComponent }>)[name] ??
    (VISUAL_EFFECTS as Record<string, { component: AnyEffectComponent }>)[name] ??
    (SCENE_EFFECTS as Record<string, { component: AnyEffectComponent }>)[name];
  return entry ? entry.component : null;
};

export const EffectStack: React.FC<{
  effects?: SceneEffectRef[];
  children: React.ReactNode;
}> = ({ effects, children }) => {
  if (!effects || effects.length === 0) return <>{children}</>;

  // reduceRight so effects[0] is the outermost wrapper.
  return effects.reduceRight<React.ReactElement>((inner, spec) => {
    const Component = lookup(spec.name);
    if (!Component) {
      // eslint-disable-next-line no-console
      console.warn(`[EffectStack] unknown effect "${spec.name}" — skipped`);
      return inner;
    }
    return (
      <Component intensity={spec.intensity ?? 1} seed={spec.seed}>
        {inner}
      </Component>
    );
  }, <>{children}</> as React.ReactElement);
};
