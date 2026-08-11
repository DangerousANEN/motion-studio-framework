import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';

/**
 * CryptoWallet — a wallet card: masked address, balance counting up, token rows.
 *
 * Reads: address, balance, currency, tokens[]{symbol,name,amount,usd,change}, title
 *
 * The address is always masked mid-string. A wallet mockup is exactly the kind
 * of asset that gets screenshotted and reused, and a full address on screen is
 * an invitation to paste a real one in later.
 */

const FONT = '"Inter", "SF Pro Display", -apple-system, sans-serif';
const MONO = 'ui-monospace, "SF Mono", Menlo, monospace';

const W = {
  bg: '#0B0E14',
  card: '#151A24',
  cardTop: '#1D2431',
  text: '#FFFFFF',
  muted: '#7A8598',
  up: '#00D18F',
  down: '#FF5C5C',
};

interface Token {
  symbol: string;
  name?: string;
  amount: number;
  usd?: number;
  change?: number;
  color?: string;
}

/** Keep the ends, hide the middle — never render a full address. */
const maskAddress = (addr: string): string =>
  addr.length <= 14 ? addr : `${addr.slice(0, 6)}···${addr.slice(-4)}`;

const fmt = (n: number, digits = 2): string =>
  n.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });

/**
 * Render the balance with its currency.
 *
 * A one-character symbol prefixes the number the way money is written: `$12,480`.
 * A ticker does not — `USDT12,480` reads as one broken token, which is exactly
 * what shipped when a spec passed `currency: "USDT"`. Anything longer than a
 * single glyph is treated as a ticker and follows the amount with a space.
 */
const formatBalance = (amount: number, currency: string): string => {
  const value = fmt(amount, 0);
  return currency.length <= 1 ? `${currency}${value}` : `${value} ${currency}`;
};

export const CryptoWallet: React.FC<BaseSceneProps> = ({
  title,
  address,
  balance,
  currency = '$',
  tokens,
  accentColor = '#00D18F',
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);

  const list: Token[] = Array.isArray(tokens) && tokens.length
    ? (tokens as Token[])
    : [
        { symbol: 'ETH', name: 'Ethereum', amount: 4.218, usd: 14_842, change: 2.4, color: '#7B8CFF' },
        { symbol: 'USDT', name: 'Tether', amount: 8_400, usd: 8_400, change: 0.0, color: '#26A17B' },
        { symbol: 'SOL', name: 'Solana', amount: 62.5, usd: 9_120, change: -1.8, color: '#B45CFF' },
      ];

  const total = typeof balance === 'number'
    ? balance
    : list.reduce((acc, t) => acc + (t.usd ?? 0), 0);

  const animateValue = resolveMotion(motion ?? { curve: 'easeOut', duration: 50 }, fps, 'value');
  const animateRow = resolveMotion(motion, fps, 'reveal');

  const shown = total * Math.min(1, Math.max(0, animateValue(frame, 0, 1)));
  const cardIn = animateRow(frame, 0, 1);
  const rowStagger = Math.min(12, Math.max(6, (durationInFrames * 0.35) / list.length));

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: W.bg, overflow: 'hidden' }}>
      <div
        style={{
          position: 'absolute',
          top: safe.top,
          left: safe.left,
          width: safe.width,
          height: safe.height,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 22,
          boxSizing: 'border-box',
        }}
      >
        {title && (
          <h2
            style={{
              margin: 0,
              fontFamily: FONT,
              fontSize: Math.round(height * 0.026),
              fontWeight: 800,
              color: W.muted,
              letterSpacing: 1.6,
              textTransform: 'uppercase',
              opacity: cardIn,
            }}
          >
            {title}
          </h2>
        )}

        {/* balance card */}
        <div
          style={{
            background: `linear-gradient(160deg, ${W.cardTop}, ${W.card})`,
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: 22,
            padding: '26px 26px 24px',
            boxShadow: '0 24px 60px rgba(0,0,0,0.5)',
            opacity: cardIn,
            transform: `translateY(${(1 - cardIn) * 26}px)`,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 16,
            }}
          >
            <span style={{ fontFamily: MONO, fontSize: Math.round(height * 0.017), color: W.muted }}>
              {maskAddress(address ?? '0x7a4Fc9E2b81D3aA65e0F19c7C42b8Dd90341Ee12')}
            </span>
            <span
              style={{
                fontFamily: FONT,
                fontSize: Math.round(height * 0.014),
                fontWeight: 700,
                color: accentColor,
                border: `1px solid ${accentColor}`,
                borderRadius: 6,
                padding: '3px 9px',
              }}
            >
              MAINNET
            </span>
          </div>

          <div
            style={{
              fontFamily: FONT,
              fontSize: Math.round(height * 0.055),
              fontWeight: 900,
              color: W.text,
              lineHeight: 1,
              // tnum stops the digits jittering as the counter runs
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {formatBalance(shown, currency)}
          </div>
          <div
            style={{
              fontFamily: FONT,
              fontSize: Math.round(height * 0.016),
              color: W.muted,
              marginTop: 6,
            }}
          >
            Общий баланс
          </div>
        </div>

        {/* token rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {list.map((t, i) => {
            const rowIn = animateRow(frame - 10 - i * rowStagger, 0, 1);
            const up = (t.change ?? 0) >= 0;
            return (
              <div
                key={t.symbol + i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  backgroundColor: W.card,
                  border: '1px solid rgba(255,255,255,0.05)',
                  borderRadius: 14,
                  padding: '13px 16px',
                  opacity: rowIn,
                  transform: `translateX(${(1 - rowIn) * 22}px)`,
                }}
              >
                <div
                  style={{
                    width: Math.round(height * 0.026),
                    height: Math.round(height * 0.026),
                    borderRadius: '50%',
                    backgroundColor: t.color ?? accentColor,
                    flexShrink: 0,
                  }}
                />
                <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
                  <span
                    style={{
                      fontFamily: FONT,
                      fontSize: Math.round(height * 0.019),
                      fontWeight: 700,
                      color: W.text,
                    }}
                  >
                    {t.symbol}
                  </span>
                  {t.name && (
                    <span
                      style={{
                        fontFamily: FONT,
                        fontSize: Math.round(height * 0.014),
                        color: W.muted,
                      }}
                    >
                      {t.name}
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                  <span
                    style={{
                      fontFamily: FONT,
                      fontSize: Math.round(height * 0.019),
                      fontWeight: 700,
                      color: W.text,
                      fontVariantNumeric: 'tabular-nums',
                    }}
                  >
                    {fmt(t.amount * Math.min(1, Math.max(0, animateValue(frame - i * 4, 0, 1))), 2)}
                  </span>
                  {typeof t.change === 'number' && (
                    <span
                      style={{
                        fontFamily: FONT,
                        fontSize: Math.round(height * 0.014),
                        color: up ? W.up : W.down,
                        fontVariantNumeric: 'tabular-nums',
                      }}
                    >
                      {up ? '+' : ''}
                      {t.change.toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
