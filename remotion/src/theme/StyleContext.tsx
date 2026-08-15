/**
 * Theme-adaptive visual language for MSF Studio.
 *
 * A style kit is the editorial starting point. A StyleConfig is the safe,
 * structured override layer that lets an operator choose a neon colour,
 * background, card surface, glow and motion without forking a preset.
 */
import React, { createContext, useContext, useMemo } from 'react';
import type { Theme } from '../presets/brand';
import type { FontKit } from './fonts';
import { getFontKit } from './fonts';
import type { BackdropKind, EffectProfile, MotionCharacter, StyleKit } from './styleKits';
import { getStyleKit, getStyleTheme, DEFAULT_STYLE_KIT } from './styleKits';

export type PaletteOverrides = Partial<Pick<Theme,
  'bg' | 'surface' | 'gold' | 'neon' | 'cyan' | 'text' | 'muted' |
  'darkBorder' | 'shadowColor' | 'accentCyan' | 'accentGreen' | 'accentWarm'
>>;

/**
 * Public style controls. All values are optional and merge over the selected
 * style family. This contract intentionally excludes arbitrary CSS so an agent
 * cannot produce unreadable or non-deterministic renderer state.
 */
export interface StyleConfig {
  palette?: PaletteOverrides;
  fonts?: string;
  backdrop?: BackdropKind;
  surface?: StyleKit['surface'];
  transition?: string;
  motion?: Partial<MotionCharacter>;
  effects?: Partial<EffectProfile>;
}

/** Merge a scene config over a video config, preserving nested token groups. */
export const mergeStyleConfig = (
  base?: StyleConfig,
  override?: StyleConfig,
): StyleConfig | undefined => {
  if (!base && !override) return undefined;
  return {
    ...base,
    ...override,
    palette: { ...base?.palette, ...override?.palette },
    motion: { ...base?.motion, ...override?.motion },
    effects: { ...base?.effects, ...override?.effects },
  };
};

/** Everything a preset needs to look like it belongs to the active style. */
export interface ResolvedStyle {
  /** The resolved kit — backdrop/surface/transition may include config overrides. */
  kit: StyleKit;
  /** Final colour palette after config and per-scene accent resolution. */
  theme: Theme;
  fonts: FontKit;
  /** Per-scene accent wins over palette.neon and kit defaults. */
  accent: string;
  motion: StyleKit['motion'];
  surface: StyleKit['surface'];
  /** Preserved to let a nested scene merge cleanly over an ambient configuration. */
  config?: StyleConfig;
}

const resolve = (
  styleName?: string,
  accentColor?: string,
  config?: StyleConfig,
): ResolvedStyle => {
  const baseKit = getStyleKit(styleName);
  const baseTheme = getStyleTheme(baseKit);
  const configuredTheme: Theme = { ...baseTheme, ...config?.palette };
  const accent = accentColor || configuredTheme.neon;
  const theme: Theme = {
    ...configuredTheme,
    // Legacy presets read `theme.neon` / `accentGreen`; retain a consistent
    // visible accent even if their implementation predates StyleContext.
    neon: accent,
    accentGreen: accent,
  };
  const kit: StyleKit = {
    ...baseKit,
    fonts: config?.fonts ?? baseKit.fonts,
    backdrop: config?.backdrop ?? baseKit.backdrop,
    surface: config?.surface ?? baseKit.surface,
    transition: config?.transition ?? baseKit.transition,
    motion: { ...baseKit.motion, ...config?.motion },
    effects: { ...baseKit.effects, ...config?.effects },
  };
  return {
    kit,
    theme,
    fonts: getFontKit(kit.fonts),
    accent,
    motion: kit.motion,
    surface: kit.surface,
    config,
  };
};

const StyleContext = createContext<ResolvedStyle>(resolve(DEFAULT_STYLE_KIT));

export interface StyleProviderProps {
  /** Named visual family, for example `llm_hubs_neon`, `terminal` or `glass`. */
  style?: string;
  /** Direct scene accent override for quick authoring. */
  accentColor?: string;
  /** Safe, structured customisation of the selected style family. */
  config?: StyleConfig;
  children: React.ReactNode;
}

export const StyleProvider: React.FC<StyleProviderProps> = ({
  style,
  accentColor,
  config,
  children,
}) => {
  const value = useMemo(
    () => resolve(style, accentColor, config),
    [style, accentColor, config],
  );
  return <StyleContext.Provider value={value}>{children}</StyleContext.Provider>;
};

/** Read the active style. Safe outside a provider for isolated still probes. */
export const useStyle = (): ResolvedStyle => useContext(StyleContext);

/** Resolve a scene override over the ambient video style and its custom tokens. */
export const useSceneStyle = (
  sceneStyle?: string,
  sceneAccent?: string,
  sceneConfig?: StyleConfig,
): ResolvedStyle => {
  const ambient = useStyle();
  return useMemo(() => {
    if (!sceneStyle && !sceneAccent && !sceneConfig) return ambient;
    return resolve(
      sceneStyle ?? ambient.kit.name,
      sceneAccent ?? ambient.accent,
      mergeStyleConfig(ambient.config, sceneConfig),
    );
  }, [ambient, sceneStyle, sceneAccent, sceneConfig]);
};
