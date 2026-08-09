/**
 * MSF Motion Layer — unified interpolation contract for all scenes.
 *
 * PROBLEM
 * -------
 * Each preset previously hardcoded its own easing and duration:
 *   - StatCounter: spring(frame, fps, {damping: 14, stiffness: 90})
 *   - CodeReveal: interpolate(frame, [0, 30], [0, 1], {easing: Easing.out(Easing.ease)})
 *   - TokenCloud3D: raw linear
 *
 * This scattered three problems:
 *   1. No single place to change project-wide motion feel
 *   2. Weak agents couldn't control interpolation without breaking it
 *   3. Smart agents had to repeat curve definitions in every scene
 *
 * SOLUTION
 * --------
 * One `MotionConfig` object per scene channel. Presets consume it via
 * `resolveMotion()`, which returns a ready-to-use interpolation function.
 *
 * Channels: camera, value, reveal, transform, opacity — each can have its own
 * curve. Example: camera moves with slow easeInOut, counter ticks with spring.
 *
 * USAGE IN PRESETS
 * -----------------
 *   import { resolveMotion, type MotionConfig } from '../lib/motion';
 *
 *   type Props = {
 *     motion?: MotionConfig;
 *     // ... rest
 *   };
 *
 *   export const MyPreset: React.FC<Props> = ({motion, ...}) => {
 *     const animate = resolveMotion(motion, useVideoConfig().fps);
 *     const progress = animate(useCurrentFrame(), 0, durationInFrames);
 *     // ...
 *   };
 *
 * USAGE IN SPECS
 * --------------
 * Python side:
 *   scene.motion = {
 *     "curve": "spring",
 *     "spring": {"damping": 12, "stiffness": 100},
 *     "duration": 48
 *   }
 *
 * Weak agents use intensity presets:
 *   scene.intensity = "calm"  →  MOTION_PRESETS["calm"]
 *
 * Smart agents pass full MotionConfig with per-channel overrides:
 *   scene.motion = {"camera": {...}, "value": {...}}
 */

import {
  Easing,
  interpolate,
  measureSpring,
  spring,
  type SpringConfig,
} from 'remotion';

/** Curve identifier — named or custom cubic bezier. */
export type Curve =
  | 'linear'
  | 'ease'
  | 'easeIn'
  | 'easeOut'
  | 'easeInOut'
  | 'spring'
  | 'bounce'
  | 'anticipate'
  | 'overdamped'
  | [number, number, number, number]; // cubic bezier control points

/** Spring parameters — only used when curve='spring'. */
export interface SpringParams {
  damping?: number;
  stiffness?: number;
  mass?: number;
  overshootClamping?: boolean;
}

/** Stagger mode — how to offset sibling elements. */
export type StaggerFrom =
  | 'first'
  | 'last'
  | 'center'
  | 'edges'
  | 'random';

/** Loop mode. */
export type LoopMode = 'none' | 'pingpong' | 'repeat';

/** Core motion config — applies to any animatable property. */
export interface MotionConfig {
  curve?: Curve;
  spring?: SpringParams;
  duration?: number; // frames
  delay?: number; // frames
  stagger?: number; // frames between siblings
  staggerFrom?: StaggerFrom;
  loop?: LoopMode;
}

/** Per-channel motion overrides. */
export interface ChanneledMotion {
  camera?: MotionConfig;
  value?: MotionConfig;
  reveal?: MotionConfig;
  transform?: MotionConfig;
  opacity?: MotionConfig;
  default?: MotionConfig; // fallback for channels without explicit config
}

/** Intensity presets — simple knob for weak agents. */
export const MOTION_PRESETS: Record<string, MotionConfig> = {
  calm: {
    curve: 'easeInOut',
    duration: 60,
  },
  normal: {
    curve: 'easeOut',
    duration: 36,
  },
  punchy: {
    curve: 'spring',
    spring: { damping: 10, stiffness: 120 },
    duration: 24,
  },
  extreme: {
    curve: 'bounce',
    duration: 18,
  },
};

/** Project-wide default — soft easeInOut, medium duration. */
const DEFAULT_MOTION: MotionConfig = {
  curve: 'easeInOut',
  duration: 24,
};

/**
 * Resolve a named curve to a Remotion Easing function.
 * Custom bezier curves are passed as-is to interpolate({ easing }).
 */
function curveToEasing(curve: Curve): ((t: number) => number) | undefined {
  if (Array.isArray(curve)) {
    // Custom cubic bezier — interpolate accepts it directly
    return undefined; // will be handled in resolveMotion via easing option
  }
  switch (curve) {
    case 'linear':
      return Easing.linear;
    case 'ease':
      return Easing.ease;
    case 'easeIn':
      return Easing.in(Easing.ease);
    case 'easeOut':
      return Easing.out(Easing.ease);
    case 'easeInOut':
      return Easing.inOut(Easing.ease);
    case 'bounce':
      return Easing.bounce;
    case 'anticipate':
      return (t: number) => {
        const c = 0.6;
        return t < 0.5
          ? 2 * t * t * ((c + 1) * 2 * t - c)
          : 1 + 2 * (t - 1) * (t - 1) * ((c + 1) * 2 * (t - 1) + c);
      };
    case 'overdamped':
      return (t: number) => 1 - Math.exp(-6 * t) * (1 + 6 * t);
    case 'spring':
      // Spring is handled separately via spring() function
      return undefined;
    default:
      return Easing.inOut(Easing.ease);
  }
}

/**
 * Resolve MotionConfig into a function that interpolates [from, to] over time.
 *
 * Returns (currentFrame, from, to) => value.
 *
 * @param config - MotionConfig or intensity preset name
 * @param fps - Video FPS (required for spring calculations)
 * @param channel - Optional channel override for multi-channel scenes
 */
export function resolveMotion(
  config: MotionConfig | ChanneledMotion | string | undefined,
  fps: number,
  channel?: keyof Omit<ChanneledMotion, 'default'>
): (currentFrame: number, from: number, to: number) => number {
  // Resolve config
  let resolved: MotionConfig;

  if (typeof config === 'string') {
    // Intensity preset
    resolved = MOTION_PRESETS[config] || DEFAULT_MOTION;
  } else if (!config) {
    resolved = DEFAULT_MOTION;
  } else if (
    'camera' in config ||
    'value' in config ||
    'reveal' in config ||
    'transform' in config ||
    'opacity' in config
  ) {
    // Channeled motion — pick the requested channel or default
    const channeled = config as ChanneledMotion;
    if (channel && channeled[channel]) {
      resolved = channeled[channel]!;
    } else {
      resolved = channeled.default || DEFAULT_MOTION;
    }
  } else {
    resolved = config as MotionConfig;
  }

  const {
    curve = 'easeInOut',
    spring: springParams,
    duration = 24,
    delay = 0,
    loop = 'none',
  } = resolved;

  // Build interpolation function
  return (currentFrame: number, from: number, to: number): number => {
    let frame = currentFrame - delay;

    // Handle loop modes
    if (loop === 'repeat' && frame >= duration) {
      frame = frame % duration;
    } else if (loop === 'pingpong' && frame >= duration) {
      const cycle = Math.floor(frame / duration);
      frame = cycle % 2 === 0 ? frame % duration : duration - (frame % duration);
    } else if (frame >= duration) {
      return to;
    }

    if (frame < 0) return from;

    // Spring curve — use Remotion's spring()
    if (curve === 'spring') {
      const clampOvershoot = springParams?.overshootClamping ?? false;
      const config: SpringConfig = {
        damping: springParams?.damping ?? 14,
        stiffness: springParams?.stiffness ?? 90,
        mass: springParams?.mass ?? 1,
        overshootClamping: clampOvershoot,
      };
      const progress = spring({
        frame,
        fps,
        config,
      });
      // A spring's overshoot is the whole point of using one: an under-damped
      // spring returns progress > 1 mid-flight. Clamping the interpolate output
      // would flatten that back to `to` and destroy the bounce, so extrapolation
      // is left open unless the caller explicitly asked for overshootClamping.
      return interpolate(progress, [0, 1], [from, to], {
        extrapolateLeft: 'clamp',
        extrapolateRight: clampOvershoot ? 'clamp' : 'extend',
      });
    }

    // Standard easing curves
    const easingFn = curveToEasing(curve);

    // `anticipate` deliberately leaves the [0,1] band (it dips below 0 to wind
    // up, then overshoots past 1), so clamping the right edge would neuter it.
    //
    // `bounce` is NOT in this list, despite the name: Remotion's Easing.bounce
    // settles from below — measured range over [0,1] is 0.0 -> 0.9999, dipping
    // back down mid-flight (0.91 -> 0.77 -> 1.0) like a ball hitting the floor.
    // It is non-monotonic but never exceeds the target, so clamping is correct.
    const overshootingCurve = curve === 'anticipate';

    const options: Parameters<typeof interpolate>[3] = {
      extrapolateLeft: 'clamp',
      extrapolateRight: overshootingCurve ? 'extend' : 'clamp',
    };

    if (Array.isArray(curve)) {
      // Custom bezier: y-control points outside [0,1] mean the author wants
      // overshoot (e.g. [.34,1.56,.64,1] — the classic "back out" curve).
      const wantsOvershoot = curve[1] > 1 || curve[3] > 1 || curve[1] < 0 || curve[3] < 0;
      options.easing = Easing.bezier(...curve);
      options.extrapolateRight = wantsOvershoot ? 'extend' : 'clamp';
    } else if (easingFn) {
      options.easing = easingFn;
    }

    return interpolate(frame, [0, duration], [from, to], options);
  };
}

/**
 * Calculate the actual duration a spring takes to settle within threshold.
 * Useful for dynamic scene length based on motion config.
 */
export function measureSpringDuration(
  config: MotionConfig | undefined,
  fps: number,
  threshold = 0.005
): number {
  if (!config || config.curve !== 'spring') {
    return config?.duration ?? DEFAULT_MOTION.duration ?? 24;
  }

  const springConfig: Partial<SpringConfig> = {
    damping: config.spring?.damping ?? 14,
    stiffness: config.spring?.stiffness ?? 90,
    mass: config.spring?.mass ?? 1,
  };

  // measureSpring returns a frame count directly, not an object.
  return measureSpring({
    fps,
    config: springConfig,
    threshold,
  });
}

/**
 * Generate stagger delays for a list of items.
 *
 * @param count - Number of items
 * @param stagger - Delay between items (frames)
 * @param from - Stagger origin
 * @returns Array of delay values (frames)
 */
export function calculateStagger(
  count: number,
  stagger: number,
  from: StaggerFrom = 'first'
): number[] {
  const delays: number[] = [];

  switch (from) {
    case 'first':
      for (let i = 0; i < count; i++) {
        delays.push(i * stagger);
      }
      break;
    case 'last':
      for (let i = 0; i < count; i++) {
        delays.push((count - 1 - i) * stagger);
      }
      break;
    case 'center':
      const center = Math.floor(count / 2);
      for (let i = 0; i < count; i++) {
        delays.push(Math.abs(i - center) * stagger);
      }
      break;
    case 'edges':
      for (let i = 0; i < count; i++) {
        const distFromEdge = Math.min(i, count - 1 - i);
        delays.push((Math.floor(count / 2) - distFromEdge) * stagger);
      }
      break;
    case 'random':
      const randomOrder = Array.from({ length: count }, (_, i) => i)
        .sort(() => Math.random() - 0.5);
      for (let i = 0; i < count; i++) {
        delays.push(randomOrder.indexOf(i) * stagger);
      }
      break;
    default:
      // Default to 'first'
      for (let i = 0; i < count; i++) {
        delays.push(i * stagger);
      }
  }

  return delays;
}
