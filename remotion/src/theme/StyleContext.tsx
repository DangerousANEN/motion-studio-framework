/**
 * The style layer, wired.
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * `styleKits.ts` has shipped eight complete looks — palette + fonts + motion
 * character + backdrop + post-FX intent — since it was written, and NOTHING
 * imported `getStyleKit`. Verified with a repo-wide grep: the only reference to
 * the module was `PostFX.tsx` importing the `EffectProfile` *type*. So the
 * kits were dead configuration: setting `style: "retro"` on a spec changed
 * nothing, because no component ever asked which style was active.
 *
 * Meanwhile every preset hardcoded its own colours (`TG.bg = '#17212B'`,
 * `BRAND.neon`, literal `'#00FF88'`), which is why "styles should recolour the
 * scenes" was impossible: there was no channel to recolour *through*.
 *
 * This adds that channel. `<StyleProvider>` resolves a kit once at the top of
 * the composition and publishes it; presets call `useStyle()` and read
 * `theme`/`fonts`/`motion`/`surface` from there.
 *
 * WHY CONTEXT AND NOT PROPS
 * -------------------------
 * A prop would have to be threaded through TransitionSeries, EffectStack and
 * the dispatcher into 17+ presets, and every new preset would have to remember
 * to forward it. Context makes the style ambient: a preset that wants it asks,
 * one that does not is unaffected. It also survives the HtmlInCanvas
 * rasterisation the shader transitions use, because the provider sits above
 * the captured subtree.
 *
 * WHY THE DEFAULT IS THE POP KIT AND NOT `undefined`
 * --------------------------------------------------
 * `useStyle()` outside a provider returns the default kit rather than throwing.
 * Presets are rendered directly in tests and in `remotion still` probes without
 * the full Main composition; making the hook throw would turn every such probe
 * into a crash, and making it return undefined would push a null-check into
 * every call site. A sane default keeps both paths working.
 *
 * PER-SCENE OVERRIDE
 * ------------------
 * A scene may set its own `style`, which wins over the spec-level one. That is
 * how a single video mixes an `editorial` explainer section with one `neon`
 * announcement beat, which is exactly the "different styles" the brief asks
 * for. `accentColor` still overrides the kit's accent on top of that, because
 * the accent is the one colour authors reach for most often.
 */
import React, { createContext, useContext, useMemo } from 'react';
import type { Theme } from '../presets/brand';
import type { FontKit } from './fonts';
import { getFontKit } from './fonts';
import type { StyleKit } from './styleKits';
import { getStyleKit, getStyleTheme, DEFAULT_STYLE_KIT } from './styleKits';

/** Everything a preset needs to look like it belongs to the active style. */
export interface ResolvedStyle {
  /** The kit itself — read `backdrop`, `surface`, `transition` from here. */
  kit: StyleKit;
  /** Colour palette the kit points at, with any accent override applied. */
  theme: Theme;
  /** Font families for display / body / mono text. */
  fonts: FontKit;
  /**
   * The single accent colour. Resolution order:
   *   scene.accentColor  ->  kit's theme.neon
   * A preset should use this for its one highlight colour rather than reaching
   * for `theme.neon` directly, so a per-scene override actually takes effect.
   */
  accent: string;
  /** Convenience: the kit's motion character. */
  motion: StyleKit['motion'];
  /** Convenience: card/border treatment. */
  surface: StyleKit['surface'];
}

const resolve = (styleName?: string, accentColor?: string): ResolvedStyle => {
  const kit = getStyleKit(styleName);
  const base = getStyleTheme(kit);
  const accent = accentColor || base.neon;

  // The accent is folded into the palette so a preset reading `theme.neon`
  // (as all the existing ones do) honours a per-scene override without every
  // preset being rewritten first. This is what makes the wiring incremental.
  const theme: Theme = accentColor
    ? { ...base, neon: accentColor, accentGreen: accentColor }
    : base;

  return {
    kit,
    theme,
    fonts: getFontKit(kit.fonts),
    accent,
    motion: kit.motion,
    surface: kit.surface,
  };
};

const StyleContext = createContext<ResolvedStyle>(resolve(DEFAULT_STYLE_KIT));

export interface StyleProviderProps {
  /** Style kit name. Unknown names fall back to the default, never throw. */
  style?: string;
  /** Overrides the kit's accent colour for everything below this provider. */
  accentColor?: string;
  children: React.ReactNode;
}

export const StyleProvider: React.FC<StyleProviderProps> = ({
  style,
  accentColor,
  children,
}) => {
  // Memoised on the two inputs: the resolved object is passed as context value,
  // and a fresh object every frame would re-render every consumer on every
  // frame for no reason. At 60fps x 17 presets that is not free.
  const value = useMemo(() => resolve(style, accentColor), [style, accentColor]);
  return <StyleContext.Provider value={value}>{children}</StyleContext.Provider>;
};

/**
 * Read the active style. Safe outside a provider — returns the default kit.
 *
 * @example
 *   const { theme, fonts, accent } = useStyle();
 *   <div style={{ background: theme.surface, fontFamily: fonts.display }} />
 */
export const useStyle = (): ResolvedStyle => useContext(StyleContext);

/**
 * Per-scene style resolution, for use inside a preset.
 *
 * A preset receives `style` and `accentColor` as props; this folds them over
 * the ambient style so the scene-level value wins. Presets should prefer this
 * over bare `useStyle()` when they accept those props.
 */
export const useSceneStyle = (
  sceneStyle?: string,
  sceneAccent?: string
): ResolvedStyle => {
  const ambient = useStyle();
  return useMemo(() => {
    if (!sceneStyle && !sceneAccent) return ambient;
    // Scene style wins; when only an accent is given, keep the ambient kit.
    return resolve(sceneStyle ?? ambient.kit.name, sceneAccent ?? ambient.accent);
  }, [ambient, sceneStyle, sceneAccent]);
};
