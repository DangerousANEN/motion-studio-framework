/**
 * UI mockup preset pack — messaging, AI chat, crypto and banking interfaces.
 *
 * A pack rather than entries in core.ts: these are written and extended
 * independently of the original presets, and mergeRegistries() will reject a
 * name that collides with another pack instead of silently overwriting it.
 */
import { AiChatStream } from '../presets/AiChatStream';
import { BankCard } from '../presets/BankCard';
import { CryptoWallet } from '../presets/CryptoWallet';
import { TgChat } from '../presets/TgChat';
import { PresetRegistry } from './types';

export const UI_MOCK_PRESETS: PresetRegistry = {
  TgChat: {
    component: TgChat,
    category: 'ui-mock',
    summary: 'Telegram thread with bubbles arriving in sequence and read ticks.',
    fields: ['messages', 'title'],
    dataDriven: true,
  },
  AiChatStream: {
    component: AiChatStream,
    category: 'ui-mock',
    summary: 'LLM chat with the reply streaming token by token behind a cursor.',
    fields: ['messages', 'response', 'title'],
    dataDriven: true,
  },
  CryptoWallet: {
    component: CryptoWallet,
    category: 'ui-mock',
    summary: 'Wallet card with a masked address, counting balance and token rows.',
    fields: ['address', 'balance', 'currency', 'tokens', 'title'],
    dataDriven: true,
  },
  BankCard: {
    component: BankCard,
    category: 'device',
    summary: 'Payment card tilting into view; only the last four digits shown.',
    fields: ['last4', 'holder', 'expiry', 'brand', 'title', 'subtitle'],
  },
};
