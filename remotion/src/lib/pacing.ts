/**
 * Reveal pacing: when things finish appearing, expressed in seconds of dwell.
 *
 * WHY THIS EXISTS
 * ---------------
 * Presets schedule their reveals as fractions of durationInFrames:
 *
 *     const revealFrames = Math.round(durationInFrames * 0.75) - delay;
 *
 * That looks safe and is not. A fraction gives the viewer a fraction of the
 * scene to read the result, so the reading time scales with the scene instead of
 * with the text. Measured on DefinitionCard at 180 frames: the definition
 * finished typing at 2.68s of a 3.0s scene, leaving 0.30s before the cut — and
 * at 10s it would leave 1.0s, still a tenth of the scene to read the payload.
 * The number that matters is ABSOLUTE: how many seconds is this on screen,
 * settled, before the cut.
 *
 * `settleBy` inverts the question — it returns the latest frame by which a
 * reveal must be finished for a given dwell, and presets schedule backwards from
 * there. `paceSequence` does the same for a chain of reveals.
 *
 * WHEN A SCENE IS TOO SHORT
 * -------------------------
 * These helpers cannot create time. If the scene is shorter than the dwell it
 * asks for, they collapse the reveal to frame 0 (everything visible immediately,
 * maximum reading time) rather than silently shortening the dwell. Fix the
 * scene's duration in the spec — the pipeline sizes it from the narration, so a
 * scene too short to read is a script problem, not a layout one.
 */

/** A settled element should be readable for at least this long. */
export const MIN_DWELL_SEC = 1.0;

/**
 * How long a reveal animation itself takes to finish after it starts.
 *
 * `settleBy` has to subtract this as well as the dwell. Scheduling a reveal to
 * START at `duration - dwell` gives it `dwell` minus its own animation time —
 * measured on DefinitionCard, asking for 1.0s of dwell produced 0.77s, and the
 * missing 0.23s was exactly the spring settling. The springs in lib/motion.ts
 * land within ~0.25s at 60fps for the reveal character.
 */
export const REVEAL_TAIL_SEC = 0.25;

/** Russian prose on a phone, characters per second, deliberately generous. */
export const READ_CHARS_PER_SEC = 12;

/**
 * Latest frame at which a reveal may START and still leave `dwellSec` of settled
 * screen time, accounting for the animation's own duration.
 *
 * Returns 0 when the scene cannot afford the dwell — render it immediately.
 */
export const settleBy = (
  durationInFrames: number,
  fps: number,
  dwellSec: number = MIN_DWELL_SEC
): number => Math.max(0, Math.round(durationInFrames - (dwellSec + REVEAL_TAIL_SEC) * fps));

/**
 * Seconds needed to read `text`, floored at MIN_DWELL_SEC.
 *
 * Use for the element carrying the scene's payload — the definition, the quote,
 * the answer — not for a badge or a date.
 */
export const readingSec = (text: string): number =>
  Math.max(MIN_DWELL_SEC, (text?.length ?? 0) / READ_CHARS_PER_SEC);

/**
 * Start/end frames for a chain of reveals that must ALL be settled by
 * `settleFrame`, given relative weights.
 *
 * weights are proportional durations, not frames: [3, 1, 1] spends three times
 * as long on the first reveal as on each of the others. The chain is laid out
 * from `startFrame` to `settleFrame`; if that window is non-positive every step
 * gets [0, 0] and the content is simply visible from the first frame.
 */
export const paceSequence = (
  startFrame: number,
  settleFrame: number,
  weights: number[]
): { start: number; end: number; frames: number }[] => {
  const window = settleFrame - startFrame;
  const total = weights.reduce((a, b) => a + Math.max(0, b), 0);
  if (window <= 0 || total <= 0) {
    return weights.map(() => ({ start: 0, end: 0, frames: 0 }));
  }
  const out: { start: number; end: number; frames: number }[] = [];
  let cursor = startFrame;
  weights.forEach((w, i) => {
    const frames =
      i === weights.length - 1
        ? settleFrame - cursor // absorb rounding so the last step lands exactly
        : Math.round((Math.max(0, w) / total) * window);
    out.push({ start: Math.round(cursor), end: Math.round(cursor + frames), frames });
    cursor += frames;
  });
  return out;
};
