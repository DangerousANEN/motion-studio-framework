/**
 * SignalWipeDemo — Плавный переход от доказательства к выводу с коротким readable motion window.
 *
 * Element Builder scaffold. This is intentionally not part of the production
 * transition enum until its author wires it into remotion/src/lib/transitions.ts
 * and passes the normal TypeScript/render verification.
 */
export const SignalWipeDemoRecipe = {
  name: 'SignalWipeDemo',
  baseTransition: 'bookFlip',
  style: 'llm_hubs_neon',
} as const;
