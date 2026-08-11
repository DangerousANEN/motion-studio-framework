/**
 * Social proof and engagement preset pack.
 *
 * These four presets handle the social-signal use cases the library had no
 * answer for: showing a post getting reactions, a live comment stream,
 * a channel subscribe moment, and a ranked leaderboard.
 *
 * They live in their own pack so their independent development does not touch
 * core.ts, ui_mock.ts, or media.ts. mergeRegistries() will error loudly if a
 * name ever collides with another pack.
 */
import {
  PostCard,
  CommentWall,
  SubscribeCTA,
  Leaderboard,
} from '../presets/social';
import { PresetRegistry } from './types';

export const SOCIAL_PRESETS: PresetRegistry = {
  PostCard: {
    component: PostCard,
    category: 'ui-mock',
    summary: 'Social post card: avatar, name, text, animated metric counters (likes/reposts/comments), verified badge.',
    fields: ['author', 'handle', 'text', 'likes', 'reposts', 'comments', 'avatar', 'verified'],
    dataDriven: true,
  },
  CommentWall: {
    component: CommentWall,
    category: 'ui-mock',
    summary: 'Live comment stream: comments arrive bottom-to-top with stagger, older ones drift up and fade.',
    fields: ['comments', 'title'],
    dataDriven: true,
  },
  SubscribeCTA: {
    component: SubscribeCTA,
    category: 'ui-mock',
    summary: 'Subscribe CTA: cursor moves to button, clicks, button switches to Subscribed, bell rings.',
    fields: ['channelName', 'subscribers', 'buttonText', 'subscribedText', 'avatar'],
  },
  Leaderboard: {
    component: Leaderboard,
    category: 'data',
    summary: 'Ranked rows with proportional bars; rows enter with stagger, leader is accent-highlighted.',
    fields: ['rows', 'title', 'valueSuffix'],
    dataDriven: true,
  },
};
