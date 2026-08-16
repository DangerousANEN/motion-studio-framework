import {
  BrowserTour,
  CommentThread,
  DeviceShowcase,
  NotificationStack,
  PollResult,
  PromptComposer,
  ProviderChat,
  ScreenMagnifier,
  VideoFrame,
  VoiceWave,
} from '../presets/expansion_social';
import {PresetRegistry} from './types';

export const EXPANSION_SOCIAL_PRESETS: PresetRegistry = {
  PromptComposer: {component: PromptComposer, category: 'ui-mock', summary: 'Prompt input composer with typed presentation and send action.', fields: ['prompt', 'provider', 'sendLabel', 'text'], dataDriven: true},
  ProviderChat: {component: ProviderChat, category: 'ui-mock', summary: 'Provider-branded chat with replaceable avatar, prompt, answer and reasoning chips.', fields: ['provider', 'avatarText', 'avatarUrl', 'prompt', 'answer', 'chips', 'title', 'text'], dataDriven: true},
  NotificationStack: {component: NotificationStack, category: 'ui-mock', summary: 'One-to-three platform-neutral notification overlays.', fields: ['notifications', 'title', 'position'], dataDriven: true},
  CommentThread: {component: CommentThread, category: 'ui-mock', summary: 'Discussion thread for comments, reactions and social proof.', fields: ['comments', 'title', 'platformLabel'], dataDriven: true},
  PollResult: {component: PollResult, category: 'data', summary: 'Poll result bars with labels and percentage values.', fields: ['question', 'options', 'title'], dataDriven: true},
  BrowserTour: {component: BrowserTour, category: 'ui-mock', summary: 'Browser chrome with screenshot slot and numbered walkthrough steps.', fields: ['url', 'title', 'steps', 'screenshotUrl'], dataDriven: true},
  ScreenMagnifier: {component: ScreenMagnifier, category: 'media', summary: 'Focused crop and zoom treatment for a screen recording or screenshot.', fields: ['mediaUrl', 'focus', 'caption', 'zoom', 'title'], dataDriven: true},
  DeviceShowcase: {component: DeviceShowcase, category: 'device', summary: 'Phone, tablet or desktop framing for supplied media.', fields: ['mediaUrl', 'device', 'title', 'caption', 'text'], dataDriven: true},
  VoiceWave: {component: VoiceWave, category: 'media', summary: 'Voice message player with deterministic waveform and transcript cue.', fields: ['speaker', 'duration', 'caption', 'waveformSeed', 'text'], dataDriven: true},
  VideoFrame: {component: VideoFrame, category: 'media', summary: 'Video or reel framing with media slot, channel and chapter marker.', fields: ['mediaUrl', 'title', 'channel', 'duration', 'chapter'], dataDriven: true},
};
