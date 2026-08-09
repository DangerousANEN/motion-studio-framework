/**
 * Platform-aware safe areas for vertical video.
 *
 * WHY THIS EXISTS
 * ---------------
 * Three disagreeing sources of truth were found in the codebase:
 *
 *   1. `VideoSpec.schema.ts`  -> safeMargin: 120, symmetric on all sides
 *   2. `msf/libraries/typography_library.py` -> top 140 / bottom 240 / sides 56,
 *      and it is never imported by the Remotion render path at all
 *   3. Every preset hardcodes its own container padding: '60px 40px',
 *      '60px 50px', '60px' — none of them reference safeMargin
 *
 * None of these protect the bottom strip. On Shorts/Reels/TikTok the bottom
 * ~380px carries the handle, caption, and the like/share/comment column, and
 * the top ~280px carries the search bar and status bar. A caption placed at
 * y=1800 with `safeMargin: 120` is legal by the schema and completely hidden
 * in the app.
 *
 * The old `safeBox(width, height, margin)` in theme/layout.ts could not express
 * this because it took a single symmetric margin. Vertical video is inherently
 * asymmetric: the bottom needs roughly 3x the top.
 *
 * MEASUREMENTS
 * ------------
 * `platform` values are sized for 1080x1920 and scale proportionally for other
 * canvas sizes. They are deliberately conservative: content inside the platform
 * box is readable on every major vertical surface without per-platform tuning.
 *
 * USAGE
 * -----
 *   const safe = getSafeArea(width, height, 'platform');
 *
 *   <div style={{
 *     position: 'absolute',
 *     top: safe.top, left: safe.left,
 *     width: safe.width, height: safe.height,
 *   }}>
 *
 * or as padding on a full-bleed container:
 *
 *   <div style={{...safeAreaPadding(width, height, 'platform')}}>
 */

/** Named safe-area profiles. */
export type SafeAreaMode = 'platform' | 'loose' | 'none' | 'custom';

/** Explicit per-side insets, in pixels. */
export interface SafeInsets {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

/** A resolved safe area: insets plus the usable content box. */
export interface SafeArea extends SafeInsets {
  /** Usable content width (canvas width minus horizontal insets). */
  width: number;
  /** Usable content height (canvas height minus vertical insets). */
  height: number;
  /** Center of the usable box, useful for 3D camera targets. */
  centerX: number;
  centerY: number;
}

/**
 * Reference insets at 1080x1920.
 *
 * platform: keeps content clear of the search/status bar at the top and the
 *   handle + caption + action column at the bottom.
 * loose: for content that is decorative or intentionally full-bleed, but should
 *   still avoid the extreme edges.
 * none: no insets — full bleed. Use for backgrounds and 3D scenes that are
 *   meant to run edge to edge.
 */
const REFERENCE_HEIGHT = 1920;
const REFERENCE_WIDTH = 1080;

const PROFILES: Record<Exclude<SafeAreaMode, 'custom'>, SafeInsets> = {
  platform: { top: 280, bottom: 380, left: 80, right: 80 },
  loose: { top: 140, bottom: 180, left: 60, right: 60 },
  none: { top: 0, bottom: 0, left: 0, right: 0 },
};

/**
 * Resolve a safe area for a canvas.
 *
 * Insets scale with the canvas so a 720x1280 render gets proportionally the
 * same protection as 1080x1920. Horizontal insets scale on width, vertical on
 * height — scaling both on one axis would distort on square/landscape formats.
 *
 * @param width - Canvas width in px
 * @param height - Canvas height in px
 * @param mode - Named profile, or 'custom' when supplying `custom`
 * @param custom - Explicit insets, required when mode is 'custom'
 */
export function getSafeArea(
  width: number,
  height: number,
  mode: SafeAreaMode = 'platform',
  custom?: Partial<SafeInsets>
): SafeArea {
  let insets: SafeInsets;

  if (mode === 'custom') {
    insets = {
      top: custom?.top ?? 0,
      bottom: custom?.bottom ?? 0,
      left: custom?.left ?? 0,
      right: custom?.right ?? 0,
    };
  } else {
    const ref = PROFILES[mode];
    const vScale = height / REFERENCE_HEIGHT;
    const hScale = width / REFERENCE_WIDTH;
    insets = {
      top: Math.round(ref.top * vScale),
      bottom: Math.round(ref.bottom * vScale),
      left: Math.round(ref.left * hScale),
      right: Math.round(ref.right * hScale),
    };
  }

  // A pathological canvas (or an over-eager custom inset) must not produce a
  // negative box — clamp to zero and let the caller see a degenerate area
  // rather than NaN-propagating layout.
  const usableWidth = Math.max(0, width - insets.left - insets.right);
  const usableHeight = Math.max(0, height - insets.top - insets.bottom);

  return {
    ...insets,
    width: usableWidth,
    height: usableHeight,
    centerX: insets.left + usableWidth / 2,
    centerY: insets.top + usableHeight / 2,
  };
}

/**
 * Safe area expressed as CSS padding, for full-bleed flex containers.
 * Backgrounds still cover the whole frame; only content is inset.
 */
export function safeAreaPadding(
  width: number,
  height: number,
  mode: SafeAreaMode = 'platform',
  custom?: Partial<SafeInsets>
): {
  paddingTop: number;
  paddingBottom: number;
  paddingLeft: number;
  paddingRight: number;
} {
  const safe = getSafeArea(width, height, mode, custom);
  return {
    paddingTop: safe.top,
    paddingBottom: safe.bottom,
    paddingLeft: safe.left,
    paddingRight: safe.right,
  };
}

/**
 * Absolute-position style for the safe content box.
 * Use when a preset needs to place a box rather than pad a container.
 */
export function safeAreaBox(
  width: number,
  height: number,
  mode: SafeAreaMode = 'platform',
  custom?: Partial<SafeInsets>
): {
  position: 'absolute';
  top: number;
  left: number;
  width: number;
  height: number;
} {
  const safe = getSafeArea(width, height, mode, custom);
  return {
    position: 'absolute',
    top: safe.top,
    left: safe.left,
    width: safe.width,
    height: safe.height,
  };
}

/**
 * True when a box would intrude into platform UI.
 * Intended for QA/audit passes over a rendered spec, not for runtime layout.
 */
export function violatesSafeArea(
  box: { top: number; left: number; width: number; height: number },
  canvasWidth: number,
  canvasHeight: number,
  mode: SafeAreaMode = 'platform'
): { violates: boolean; reasons: string[] } {
  const safe = getSafeArea(canvasWidth, canvasHeight, mode);
  const reasons: string[] = [];

  if (box.top < safe.top) {
    reasons.push(`top ${box.top} is above safe top ${safe.top}`);
  }
  if (box.top + box.height > canvasHeight - safe.bottom) {
    reasons.push(
      `bottom ${box.top + box.height} is below safe bottom ${canvasHeight - safe.bottom}`
    );
  }
  if (box.left < safe.left) {
    reasons.push(`left ${box.left} is outside safe left ${safe.left}`);
  }
  if (box.left + box.width > canvasWidth - safe.right) {
    reasons.push(
      `right ${box.left + box.width} is outside safe right ${canvasWidth - safe.right}`
    );
  }

  return { violates: reasons.length > 0, reasons };
}
