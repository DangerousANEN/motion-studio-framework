/**
 * Scaffolded preset pack — entries added by tools/msf_add.py.
 *
 * Hand-written packs live beside this one; keeping generated entries
 * separate means the generator never has to parse someone else's file.
 */
import { PresetRegistry } from './types';
import { SignalLaunchHero } from '../presets/SignalLaunchHero';

export const GENERATED_PRESETS: PresetRegistry = {
  SignalLaunchHero: {
    component: SignalLaunchHero,
    category: 'narrative',
    summary: 'Короткий cinematic reveal: новая модель появляется, а цена и результат читаются за один взгляд.',
    fields: ['title', 'subtitle', 'provider', 'metric', 'mediaUrl'],
  },
};
