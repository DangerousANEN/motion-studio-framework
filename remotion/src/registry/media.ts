/**
 * Media / device / chart preset pack.
 *
 * A pack rather than entries in core.ts or ui_mock.ts: these presets are written
 * and extended independently, and mergeRegistries() rejects a name that collides
 * with another pack instead of silently overwriting it.
 *
 * WHAT IS IN HERE AND WHY IT WAS MISSING
 * --------------------------------------
 * The library could describe data and render typography, but it had no way to
 * put REAL material on screen — a photo, a clip, a screen capture, a voice note
 * — and no device to frame it in. A video about a product that never shows the
 * product is the "все сцены одинаковые" complaint in a different form.
 */
import {
  ImageShowcase,
  ScreenRecord,
  VideoEmbed,
  VoiceMemo,
} from '../presets/media';
import { MusicPlayer, PhoneMockup, VinylRecord } from '../presets/device';
import { Bars3D, RingStats } from '../presets/charts';
import { PresetRegistry } from './types';

export const MEDIA_PRESETS: PresetRegistry = {
  ImageShowcase: {
    component: ImageShowcase,
    category: 'media',
    summary: 'Stills with a slow Ken Burns drift; multiple images share the scene.',
    fields: ['images', 'src', 'title', 'subtitle', 'fit', 'kenBurns'],
    dataDriven: true,
  },
  VideoEmbed: {
    component: VideoEmbed,
    category: 'media',
    summary: 'External footage framed in the scene with a progress bar.',
    fields: ['src', 'title', 'subtitle', 'fit', 'startFrom', 'showControls', 'muted'],
    dataDriven: true,
  },
  ScreenRecord: {
    component: ScreenRecord,
    category: 'media',
    summary: 'Screen capture in browser/OS window chrome with a REC indicator.',
    fields: ['src', 'images', 'title', 'subtitle', 'appName', 'urlBar', 'showRec', 'chrome', 'fit'],
    dataDriven: true,
  },
  VoiceMemo: {
    component: VoiceMemo,
    category: 'media',
    summary: 'Voice message bubble with a playing waveform and transcript.',
    fields: ['title', 'subtitle', 'duration', 'waveformSeed', 'transcript'],
  },
  PhoneMockup: {
    component: PhoneMockup,
    category: 'device',
    summary: 'Phone body hosting ANY other preset on its screen (innerPreset).',
    fields: ['innerPreset', 'innerProps', 'title', 'subtitle', 'device', 'tilt'],
    dataDriven: true,
  },
  MusicPlayer: {
    component: MusicPlayer,
    category: 'media',
    summary: 'Now-playing card: cover art, scrubber, equaliser bars.',
    fields: ['trackTitle', 'artist', 'cover', 'duration', 'title', 'subtitle'],
  },
  VinylRecord: {
    component: VinylRecord,
    category: 'media',
    summary: 'Spinning record with a tonearm dropping into the groove.',
    fields: ['trackTitle', 'artist', 'cover', 'rpm', 'spin', 'title', 'subtitle'],
  },
  RingStats: {
    component: RingStats,
    category: 'data',
    summary: 'Up to six independent progress rings, each on its own 0..max scale.',
    fields: ['segments', 'valueSuffix', 'ringMax', 'title', 'subtitle'],
    dataDriven: true,
  },
  Bars3D: {
    component: Bars3D,
    category: 'data',
    summary: 'Extruded 3D bars rising out of a ground plane with shaded faces.',
    fields: ['segments', 'valueSuffix', 'barDepth', 'title', 'subtitle'],
    dataDriven: true,
  },
};
