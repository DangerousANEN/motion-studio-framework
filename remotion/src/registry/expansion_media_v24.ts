import {AppScreenGallery, BeforeAfterLens, DeepZoomStory, DocumentMarginNotes, ImageEvidenceCompare, LayeredWindowStack, PhotoConstellation, ThreePhoto360Drift, VideoChapterRail, VoiceNotePullQuote} from '../presets/expansion_media_choreography';
import {PresetRegistry} from './types';

export const EXPANSION_MEDIA_V24_PRESETS: PresetRegistry = {
  ThreePhoto360Drift: {component: ThreePhoto360Drift, category: 'media', summary: 'Slow 360-degree interpolated camera drift across three arbitrarily arranged photos.', fields: ['images', 'positions', 'cameraPath', 'captions', 'title'], dataDriven: true},
  PhotoConstellation: {component: PhotoConstellation, category: 'media', summary: 'Depth-aware constellation of four to nine media frames.', fields: ['images', 'layoutSeed', 'focusOrder', 'captions', 'title'], dataDriven: true},
  DeepZoomStory: {component: DeepZoomStory, category: 'media', summary: 'Full-frame image story with deliberate zoom stops.', fields: ['image', 'stops', 'caption', 'title'], dataDriven: true},
  BeforeAfterLens: {component: BeforeAfterLens, category: 'media', summary: 'Before/after split lens with a typed central claim.', fields: ['beforeUrl', 'afterUrl', 'labelBefore', 'labelAfter', 'claim', 'title'], dataDriven: true},
  VideoChapterRail: {component: VideoChapterRail, category: 'media', summary: 'Primary video surface with chapter navigation rail.', fields: ['videoUrl', 'chapters', 'channel', 'title'], dataDriven: true},
  VoiceNotePullQuote: {component: VoiceNotePullQuote, category: 'media', summary: 'Voice note waveform and transcript pull quote.', fields: ['speaker', 'avatar', 'audioUrl', 'quote', 'duration', 'waveformSeed'], dataDriven: true},
  DocumentMarginNotes: {component: DocumentMarginNotes, category: 'media', summary: 'Document or screenshot with source-aware marginal notes.', fields: ['documentUrl', 'notes', 'source', 'date', 'title'], dataDriven: true},
  AppScreenGallery: {component: AppScreenGallery, category: 'device', summary: 'Slow interpolated gallery of application screens in selectable device framing.', fields: ['screens', 'device', 'captions', 'title'], dataDriven: true},
  LayeredWindowStack: {component: LayeredWindowStack, category: 'ui-mock', summary: 'Reordering layered browser, chat, table and media windows.', fields: ['windows', 'focusOrder', 'labels', 'title'], dataDriven: true},
  ImageEvidenceCompare: {component: ImageEvidenceCompare, category: 'media', summary: 'Two screenshot evidence comparison with source/date ribbons.', fields: ['leftImage', 'rightImage', 'leftMeta', 'rightMeta', 'difference', 'title'], dataDriven: true},
};
