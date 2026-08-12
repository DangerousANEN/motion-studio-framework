/**
 * Transition layer for MSF.
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * Main.tsx used a plain <Series>, which produces hard cuts between every scene.
 * @remotion/transitions provides the crossfades/wipes, but wiring it in has one
 * non-obvious trap that this module exists to contain:
 *
 *   A <TransitionSeries> is SHORTER than the sum of its scene durations.
 *   Each <TransitionSeries.Transition> overlaps the outgoing and incoming
 *   scene, so the timeline loses `timing` frames per transition.
 *
 * MSF renders one continuous voice-over track over the whole video. If the
 * video timeline shrinks but the audio does not, every scene after the first
 * transition drifts out of sync with the narration -- and the tail of the
 * voice-over gets cut off entirely. So the composition duration MUST be
 * computed with the overlap subtracted, using exactly the same numbers the
 * renderer uses. `getTransitionPlan()` is that single source of truth: Root.tsx
 * uses it for durationInFrames, Main.tsx uses it to lay out the series.
 *
 * Verified against @remotion/transitions 4.0.507: 18 presentations ship in
 * dist/presentations (the plan's "20" was wrong). Presentations that are
 * WebGL shaders also export a plain React implementation under the unsuffixed
 * name (e.g. `dissolve` alongside `dissolveShader`); we deliberately use the
 * non-shader variants because headless Chrome in CI has no reliable GPU and
 * the shader path can fall back to a black frame.
 */
import { linearTiming, springTiming, type TransitionPresentation, type TransitionTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { slide } from '@remotion/transitions/slide';
import { wipe } from '@remotion/transitions/wipe';
import { flip } from '@remotion/transitions/flip';
import { clockWipe } from '@remotion/transitions/clock-wipe';
import { iris } from '@remotion/transitions/iris';
import { pushCut } from '@remotion/transitions/push-cut';
import { none } from '@remotion/transitions/none';
import { ripple } from '@remotion/transitions/ripple';
import { crosswarp } from '@remotion/transitions/crosswarp';
import { crossZoom } from '@remotion/transitions/cross-zoom';
import { swap } from '@remotion/transitions/swap';
import { linearBlur } from '@remotion/transitions/linear-blur';
import { zoomInOut } from '@remotion/transitions/zoom-in-out';
import { dreamyZoom } from '@remotion/transitions/dreamy-zoom';
import { filmBurn } from '@remotion/transitions/film-burn';
import { zoomBlur } from '@remotion/transitions/zoom-blur';
import { bookFlip } from '@remotion/transitions/book-flip';

/** Every transition name accepted in a VideoSpec. Keep in sync with VideoSpec.schema.ts. */
export const TRANSITION_NAMES = [
  'none',
  'fade',
  'slide',
  'wipe',
  'flip',
  'clockWipe',
  'iris',
  'pushCut',
  'ripple',
  'crosswarp',
  'crossZoom',
  'swap',
  'linearBlur',
  'zoomInOut',
  'dreamyZoom',
  'filmBurn',
  'zoomBlur',
  'bookFlip',
] as const;

export type TransitionName = (typeof TRANSITION_NAMES)[number];

export type TransitionDirection = 'from-left' | 'from-right' | 'from-top' | 'from-bottom';

export type TransitionConfig = {
  type: TransitionName;
  /** Overlap length in frames. Also the amount of timeline the transition consumes. */
  durationInFrames?: number;
  direction?: TransitionDirection;
  /** 'spring' feels organic on motion, 'linear' is predictable for wipes. */
  timing?: 'spring' | 'linear';
};

/** Default overlap: 18 frames = 300ms at 60fps. Long enough to read, short enough to keep pace. */
export const DEFAULT_TRANSITION_FRAMES = 18;

type BuildArgs = {
  config: TransitionConfig;
  width: number;
  height: number;
};

/**
 * Each presentation is generic over its own props type, and those types are
 * mutually incompatible (IrisProps requires width/height, CrosswarpProps is
 * Record<string, never>). TransitionSeries.Transition only needs to *hold* the
 * presentation and hand it back its own props, so an `any` parameter here is
 * the intended escape hatch rather than a lost type check -- the props are
 * validated at each construction site below.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type AnyPresentation = TransitionPresentation<any>;

/**
 * Resolve a spec transition name into a real TransitionPresentation.
 * `iris` and `clockWipe` require explicit width/height, which is why this is a
 * function of the composition size rather than a static lookup table.
 *
 * Note the shader-backed presentations (dissolve, ripple, crosswarp, ...) take a
 * required props object -- passing no argument is a compile error, so each call
 * passes at least `{}`.
 */
export const buildPresentation = ({ config, width, height }: BuildArgs): AnyPresentation => {
  const direction = config.direction ?? 'from-right';

  switch (config.type) {
    case 'none':
      return none();
    case 'fade':
      // `shouldFadeOutExitingScene` is NOT optional decoration — without it
      // there is no cross-fade at all, only a fade-IN of the incoming scene on
      // top of a fully opaque outgoing one. Upstream:
      //     opacity: isEntering ? progress
      //            : passedProps.shouldFadeOutExitingScene ? 1 - progress : 1
      // The default leaves the exiting scene at opacity 1 for the whole overlap
      // and then unmounts it, so the cut lands on the last frame of the window.
      // With both sides animating, the overlap actually blends.
      return fade({ shouldFadeOutExitingScene: true });
    // 'dissolve' is deliberately absent — do not re-add it.
    //
    // It is not a cross-fade and it never blends the two scenes. The shader
    // derives a per-pixel burn threshold from the OUTGOING scene's luminance:
    //     burn = 0.5 + 0.5 * luma(outgoing);  show = burn - progress;
    //     if (show < 0.001) return incoming;   // hard per-pixel swap
    // Pixels flip one by one in luminance order. Our scenes are large areas of
    // near-uniform luma, so nearly every pixel crosses the threshold on the
    // same frame and the result is a cut.
    //
    // Measured on two HeroKinetic scenes (worst single-frame share of the whole
    // luma range; a cross-fade spreads this over the full overlap):
    //     24-frame overlap -> 99.0% in one frame
    //     48-frame overlap -> 99.0% in one frame (window shrank to 2 frames)
    //     48-frame, textured GridGridFloor -> 91.9%
    // Frame-by-frame inspection confirms scene A holds fully opaque, then B
    // appears fully opaque on the next frame. Lengthening the overlap makes it
    // worse, not better, so this cannot be tuned away with parameters.
    //
    // Use 'fade' for a real blend, or 'filmBurn' when the fiery burn-through
    // look is actually wanted (it owns that effect and reads intentionally).
    case 'slide':
      return slide({ direction });
    case 'wipe':
      return wipe({ direction });
    case 'flip':
      return flip({ direction });
    case 'pushCut':
      // pushCut has no `direction`; it is a scale/flash cut. Keep defaults.
      return pushCut();
    case 'clockWipe':
      return clockWipe({ width, height });
    case 'iris':
      return iris({ width, height });
    case 'ripple':
      return ripple({});
    case 'crosswarp':
      return crosswarp({});
    case 'crossZoom':
      return crossZoom({});
    case 'swap':
      return swap({});
    case 'linearBlur':
      return linearBlur({});
    case 'zoomInOut':
      return zoomInOut({});
    case 'dreamyZoom':
      return dreamyZoom({});
    case 'filmBurn':
      return filmBurn({});
    case 'zoomBlur':
      return zoomBlur({});
    case 'bookFlip':
      return bookFlip({});
    default: {
      // Exhaustiveness guard: adding a name to TRANSITION_NAMES without handling
      // it here becomes a compile error instead of a silent runtime fallback.
      const never: never = config.type;
      throw new Error(`Unhandled transition: ${String(never)}`);
    }
  }
};

export const buildTiming = (config: TransitionConfig): TransitionTiming => {
  const durationInFrames = config.durationInFrames ?? DEFAULT_TRANSITION_FRAMES;
  if (config.timing === 'linear') {
    return linearTiming({ durationInFrames });
  }
  return springTiming({ durationInFrames, config: { damping: 200 } });
};

export type PlannedTransition = {
  /** Index of the scene this transition runs *before*. Always >= 1. */
  beforeSceneIndex: number;
  config: TransitionConfig;
  durationInFrames: number;
};

export type TransitionPlan = {
  /** Composition length with transition overlap already subtracted. */
  totalDurationInFrames: number;
  /** Sum of all transition overlaps. */
  overlapFrames: number;
  transitions: PlannedTransition[];
};

type PlanScene = {
  durationInFrames: number;
  transition?: TransitionConfig | null;
};

/**
 * Compute the real composition length and the transition list.
 *
 * A transition declared on scene N runs between scene N-1 and scene N. A
 * transition on scene 0 is meaningless (nothing to transition from) and is
 * ignored rather than throwing, so a spec author reordering scenes does not
 * get a hard failure.
 *
 * Guard: a transition cannot be longer than either adjacent scene, or Remotion
 * throws at render time. We clamp instead, because a slightly shorter wipe is
 * always better than a failed render.
 */
export const getTransitionPlan = (scenes: PlanScene[]): TransitionPlan => {
  const transitions: PlannedTransition[] = [];
  let overlapFrames = 0;

  const sumScenes = scenes.reduce((acc, scene) => acc + scene.durationInFrames, 0);

  for (let i = 1; i < scenes.length; i += 1) {
    const config = scenes[i].transition;
    if (!config || config.type === 'none') {
      continue;
    }

    const requested = config.durationInFrames ?? DEFAULT_TRANSITION_FRAMES;
    // Leave at least 1 frame of each neighbouring scene visible outside the overlap.
    const maxAllowed = Math.max(
      0,
      Math.min(scenes[i - 1].durationInFrames, scenes[i].durationInFrames) - 1
    );
    const durationInFrames = Math.min(requested, maxAllowed);

    if (durationInFrames <= 0) {
      continue;
    }

    transitions.push({ beforeSceneIndex: i, config, durationInFrames });
    overlapFrames += durationInFrames;
  }

  return {
    totalDurationInFrames: Math.max(1, sumScenes - overlapFrames),
    overlapFrames,
    transitions,
  };
};
