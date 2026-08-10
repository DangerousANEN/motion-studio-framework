import React from 'react';
import { BaseSceneProps } from '../VideoSpec.schema';
import { PRESETS } from '../registry/presets';

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
  // Sized with explicit width/height, NOT `inset: 0` alone.
  //
  // The shader-backed transitions (ripple, crosswarp, filmBurn, bookFlip, ...)
  // rasterise the scene through Remotion's HtmlInCanvas: the subtree is placed
  // inside a `<canvas layoutSubtree>` and captured with captureElementImage().
  // That canvas subtree does NOT establish the containing block a normal
  // absolutely-positioned child resolves `inset` against, so `inset: 0` alone
  // resolved to a zero-sized box and the capture came back empty -- a fully
  // black frame, with no error thrown and the render reporting success.
  //
  // The DOM transitions (fade, slide, iris, ...) composite in normal DOM where
  // `inset: 0` does resolve, which is why only the shader group broke and made
  // the bug look preset-specific.
  //
  // Measured, frame 20 of the same two-scene spec (identical apart from the
  // transition name):
  //     inset: 0 alone          -> YMAX 29  (blank)
  //     inset: 0 + width/height -> YMAX 220 (renders)
  //
  // `isolation: 'isolate'` is a separate fix: it gives each scene its own
  // stacking context so a preset's internal zIndex (cards use 5) cannot paint
  // over the incoming scene for the whole overlap.
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
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
  // Resolved by name from the registry rather than a hand-written switch.
  // A switch meant every new preset touched this file, which does not scale to
  // 100+ scenes and makes concurrent authoring a merge conflict generator.
  const entry = PRESETS[props.preset as string];

  if (!entry) {
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

  const Component = entry.component;
  return <Component {...props} />;
};
