import {AgentRunConsole, BrowserDecisionTable, ChangelogTerminal, CommunityFAQ, PromptABLab, QuoteRepost, ReactionPulse, TelegramChannelPost, TelegramFeedScroll, TelegramForwardChain} from '../presets/expansion_community';
import {PresetRegistry} from './types';

export const EXPANSION_COMMUNITY_V24_PRESETS: PresetRegistry = {
  TelegramChannelPost: {component: TelegramChannelPost, category: 'ui-mock', summary: 'Configurable Telegram-style channel post with channel identity, media and CTA.', fields: ['channel', 'handle', 'avatar', 'postText', 'mediaUrl', 'reactions', 'views', 'time', 'cta'], dataDriven: true},
  TelegramFeedScroll: {component: TelegramFeedScroll, category: 'ui-mock', summary: 'Controlled channel feed with a deliberately focused post.', fields: ['channel', 'posts', 'focusPostId', 'scrollDirection', 'title'], dataDriven: true},
  TelegramForwardChain: {component: TelegramForwardChain, category: 'ui-mock', summary: 'Origin-to-forward chain for transparent distribution stories.', fields: ['origin', 'forwards', 'title'], dataDriven: true},
  ReactionPulse: {component: ReactionPulse, category: 'ui-mock', summary: 'Supplied reactions, comment count and reach displayed without invented growth.', fields: ['reactions', 'comments', 'views', 'period', 'title'], dataDriven: true},
  QuoteRepost: {component: QuoteRepost, category: 'ui-mock', summary: 'Original social claim and reusable quoted commentary.', fields: ['original', 'commentary', 'author', 'source', 'title'], dataDriven: true},
  CommunityFAQ: {component: CommunityFAQ, category: 'ui-mock', summary: 'Question, answer and resource stack for community education.', fields: ['questions', 'answers', 'links', 'title'], dataDriven: true},
  ChangelogTerminal: {component: ChangelogTerminal, category: 'code', summary: 'High-legibility product update and changelog terminal.', fields: ['product', 'version', 'date', 'changes'], dataDriven: true},
  PromptABLab: {component: PromptABLab, category: 'ui-mock', summary: 'A/B prompt comparison with supplied outputs and rubric.', fields: ['promptA', 'promptB', 'resultA', 'resultB', 'rubric', 'title'], dataDriven: true},
  AgentRunConsole: {component: AgentRunConsole, category: 'ui-mock', summary: 'Non-sensitive agent workflow progress console.', fields: ['steps', 'status', 'duration', 'artifacts', 'title'], dataDriven: true},
  BrowserDecisionTable: {component: BrowserDecisionTable, category: 'ui-mock', summary: 'Browser-framed decision table with inspected cell.', fields: ['url', 'columns', 'rows', 'selectedCell', 'caption', 'title'], dataDriven: true},
};
