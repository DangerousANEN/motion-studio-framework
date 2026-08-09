/**
 * Text auto-fit built on @remotion/layout-utils.
 *
 * WHY THIS EXISTS
 * ---------------
 * Presets previously sized type with a length ladder:
 *
 *     const fontSize = len > 60 ? '48px' : len > 30 ? '64px' : '88px';
 *
 * Character count is a bad proxy for rendered width. "МОЩНОСТЬ" and "iiiiiiii"
 * are both 8 characters and occupy wildly different space, and Cyrillic runs
 * wider than Latin at the same count. The ladder therefore both overflowed the
 * 1080px frame and wasted space on short strings.
 *
 * These helpers measure the actual glyphs in the actual loaded font, so the
 * answer is correct for any script. Fonts MUST be loaded first (see
 * theme/fonts.ts) or measurement happens against a fallback face and the
 * result is wrong — that is what `validateFontIsLoaded` guards against.
 */
import { fitText, fitTextOnNLines, measureText } from '@remotion/layout-utils';

/**
 * Largest font size (px) at which `text` fits `maxWidth` on ONE line,
 * clamped to a legible range.
 */
export const fitOneLine = ({
  text,
  maxWidth,
  fontFamily,
  fontWeight = 900,
  letterSpacing,
  textTransform,
  maxFontSize = 130,
  minFontSize = 32,
}: {
  text: string;
  maxWidth: number;
  fontFamily: string;
  fontWeight?: number | string;
  letterSpacing?: string;
  textTransform?: 'uppercase' | 'lowercase' | 'capitalize' | 'none';
  maxFontSize?: number;
  minFontSize?: number;
}): number => {
  if (!text) return minFontSize;
  const { fontSize } = fitText({
    text,
    withinWidth: maxWidth,
    fontFamily,
    fontWeight,
    letterSpacing,
    textTransform,
  });
  return Math.max(minFontSize, Math.min(maxFontSize, fontSize));
};

/**
 * Font size for text allowed to wrap across up to `maxLines`, plus the actual
 * line breakdown the library computed.
 *
 * Uses the library's own `fitTextOnNLines` rather than approximating, then
 * enforces a height budget: a size that fits N lines horizontally can still
 * overflow vertically once line-height is applied.
 */
export const fitWrapped = ({
  text,
  maxWidth,
  maxHeight,
  fontFamily,
  fontWeight = 800,
  maxLines = 4,
  lineHeight = 1.12,
  letterSpacing,
  textTransform,
  maxFontSize = 120,
  minFontSize = 28,
}: {
  text: string;
  maxWidth: number;
  maxHeight?: number;
  fontFamily: string;
  fontWeight?: number | string;
  maxLines?: number;
  lineHeight?: number;
  letterSpacing?: string;
  textTransform?: 'uppercase' | 'lowercase' | 'capitalize' | 'none';
  maxFontSize?: number;
  minFontSize?: number;
}): { fontSize: number; lines: string[] } => {
  if (!text) return { fontSize: minFontSize, lines: [] };

  const fitted = fitTextOnNLines({
    text,
    maxLines,
    maxBoxWidth: maxWidth,
    fontFamily,
    fontWeight,
    letterSpacing,
    textTransform,
    maxFontSize,
  });

  let size = Math.min(maxFontSize, fitted.fontSize);

  // Horizontal fit does not imply vertical fit. Shrink until the wrapped block
  // respects the height budget.
  if (maxHeight && maxHeight > 0) {
    const lineCount = Math.max(1, fitted.lines.length);
    while (size > minFontSize && lineCount * size * lineHeight > maxHeight) {
      size *= 0.94;
    }
  }

  return {
    fontSize: Math.max(minFontSize, Math.min(maxFontSize, size)),
    lines: fitted.lines,
  };
};

/** Rendered dimensions of a string — useful for badges and pill backgrounds. */
export const measure = (opts: {
  text: string;
  fontFamily: string;
  fontSize: number;
  fontWeight?: number | string;
  letterSpacing?: string;
}) => measureText(opts);

/** Safe-area box for a given canvas, so nothing hides under platform UI. */
export const safeBox = (width: number, height: number, margin: number) => ({
  width: width - margin * 2,
  height: height - margin * 2,
  margin,
});
