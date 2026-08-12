/**
 * Minimal `remotion` stub for the model-icon probe in tests/test_model_icons.py.
 *
 * The real staticFile() needs a bundler/browser context. The probe only asks
 * which slug the rules pick, so mirroring the public/ URL shape is enough.
 */
export const staticFile = (p: string): string => `/${p.replace(/^\/+/, '')}`;
