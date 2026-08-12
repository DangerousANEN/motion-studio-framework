/**
 * Colour maths for opaque compositing.
 *
 * WHY THIS EXISTS
 * ---------------
 * Presets express subtle fills as an alpha suffix on a theme hex:
 *
 *     backgroundColor: `${theme.muted}33`
 *
 * That is correct only when nothing sits behind the element. When something
 * does — a connector line, a card edge, a backdrop grid — the alpha lets it
 * show through, and the result is a visible seam that no layout probe detects
 * because every box is exactly where it should be.
 *
 * The concrete bug: ProgressPath draws its connector track first, then the step
 * dots on top. Pending dots were filled `${theme.muted}33`, so the track
 * remained visible as a faint vertical stripe crossing the inside of every
 * pending circle.
 *
 * `blend` resolves the same visual tone against a known backdrop and returns an
 * OPAQUE hex, so the fill covers what is behind it. Use it wherever a fill is
 * decorative-but-must-be-solid; keep the alpha suffix when see-through is the
 * actual intent (glass surfaces, overlay scrims).
 */

/** Parse #rgb / #rrggbb (with or without a trailing alpha pair) to [r,g,b]. */
const parseHex = (hex: string): [number, number, number] => {
  let h = hex.trim().replace(/^#/, '');
  if (h.length === 3 || h.length === 4) {
    h = h
      .slice(0, 3)
      .split('')
      .map((c) => c + c)
      .join('');
  }
  // A 8-digit value carries its own alpha; the caller's `amount` wins, so the
  // trailing pair is dropped rather than multiplied in.
  if (h.length >= 6) h = h.slice(0, 6);
  const n = parseInt(h, 16);
  if (Number.isNaN(n)) return [0, 0, 0];
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};

const toHex = (r: number, g: number, b: number) =>
  '#' +
  [r, g, b]
    .map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0'))
    .join('');

/**
 * `fg` composited over `bg` at `amount` (0..1), returned as an opaque hex.
 *
 * blend('#8B92A0', '#0E0F11', 0.2) is what `#8B92A033` looks like on the pop
 * background — but solid, so it hides whatever is underneath.
 */
export const blend = (fg: string, bg: string, amount: number): string => {
  const a = Math.max(0, Math.min(1, amount));
  const [r1, g1, b1] = parseHex(fg);
  const [r2, g2, b2] = parseHex(bg);
  return toHex(r1 * a + r2 * (1 - a), g1 * a + g2 * (1 - a), b1 * a + b2 * (1 - a));
};

/** Relative luminance (WCAG), 0..1. */
export const luminance = (hex: string): number => {
  const [r, g, b] = parseHex(hex).map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

/** WCAG contrast ratio between two colours, 1..21. */
export const contrastRatio = (a: string, b: string): number => {
  const la = luminance(a);
  const lb = luminance(b);
  const hi = Math.max(la, lb);
  const lo = Math.min(la, lb);
  return (hi + 0.05) / (lo + 0.05);
};
