import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';

/**
 * BankCard — a payment card with a 3D tilt, revealing number and chip.
 *
 * Reads: title, subtitle, last4, holder, expiry, brand
 *
 * Only `last4` is ever shown. A card mockup is the canonical asset that gets
 * screenshotted and reused, and a "16-digit demo number" on screen is one edit
 * away from a real one. The rest of the number is rendered as bullets so the
 * card still reads as a card.
 *
 * LAYOUT
 * Every row is positioned from a shared band table rather than from individual
 * `top: cardH * 0.52` style constants. Those were tuned independently and
 * silently collided once the type was measured at render size: the number row
 * ran to y=168 on a 236px-tall card while the holder block started at y=153,
 * so the bullets sat on top of the CARD HOLDER caption. The brand mark had the
 * same problem against EXPIRES — both were anchored to the bottom-right corner
 * with no awareness of each other. Bands make the arithmetic checkable: each
 * row declares its own top and height, and they do not overlap by construction.
 */

const FONT = '"Inter", "SF Pro Display", -apple-system, sans-serif';
const MONO = 'ui-monospace, "SF Mono", Menlo, monospace';

const CARD_W = 0.86;

export const BankCard: React.FC<BaseSceneProps> = ({
  title,
  subtitle,
  last4 = '4242',
  holder = 'ALEXEY NIKITIN',
  expiry = '09/29',
  brand = 'VISA',
  accentColor = '#E6C475',
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);

  const cardW = safe.width * CARD_W;
  const cardH = cardW * 0.62; // credit card aspect
  const cx = safe.left + safe.width / 2;
  const cy = safe.top + safe.height / 2;

  // Band table — the single source of truth for vertical layout. Every row is
  // positioned by [top, height] against the card top, and none of them overlap.
  // The number face is derived from the width budget (not a magic size): the
  // fixed cardW*0.012 letter-spacing used to overflow — 19 monospace chars at
  // a 63.7px face plus 9.5px tracking came to ~906px against 664px available,
  // so the card's overflow:hidden cut the last4 clean off. Fitting the row
  // means choosing a face that fits, then tracking as a small fraction of it.
  const numberFace = cardH * 0.10;
  const numberTracking = numberFace * 0.08;
  const holderFont = cardH * 0.09;
  const labelFont = cardH * 0.055;
  const band = {
    number: { top: cardH * 0.44, h: numberFace * 1.2 },
    labels: { top: cardH * 0.68, h: labelFont * 1.2 },
    holder: { top: cardH * 0.76, h: holderFont * 1.2 },
    expires: { top: cardH * 0.76, h: holderFont * 1.2 },
  };

  const appear = resolveMotion(motion ?? { curve: 'spring', spring: { damping: 14, stiffness: 90 } }, fps, 'transform');
  const reveal = appear(frame, 0, 1);

  // 3D tilt from the reveal: settle from a 14° rotation to upright.
  const tilt = (1 - reveal) * 14;

  return (
    <div style={{ position: 'absolute', inset: 0, backgroundColor: '#0D0F14', overflow: 'hidden' }}>
      {title && (
        <h2
          style={{
            position: 'absolute',
            top: safe.top,
            left: safe.left,
            width: safe.width,
            margin: 0,
            textAlign: 'center',
            fontFamily: FONT,
            fontSize: Math.round(height * 0.03),
            fontWeight: 900,
            color: '#FFFFFF',
            opacity: reveal,
          }}
        >
          {title}
        </h2>
      )}

      <div
        style={{
          position: 'absolute',
          // Centred by offsetting half its own size. Setting left/top to the
          // centre point alone anchors the card's top-left corner there, which
          // pushed it 80px past the right edge of the safe box.
          left: cx - cardW / 2,
          top: cy - cardH / 2,
          width: cardW,
          height: cardH,
          perspective: 900,
          opacity: reveal,
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            transform: `rotateX(${tilt}deg) rotateY(${-tilt}deg)`,
            transformStyle: 'preserve-3d',
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: cardH * 0.11,
              background: `linear-gradient(135deg, #1C2333 0%, #121722 55%, #0C1017 100%)`,
              border: '1px solid rgba(255,255,255,0.09)',
              boxShadow: `0 ${cardH * 0.12}px ${cardH * 0.3}px rgba(0,0,0,0.6)`,
              overflow: 'hidden',
            }}
          >
            {/* chip */}
            <div
              style={{
                position: 'absolute',
                top: cardH * 0.22,
                left: cardW * 0.08,
                width: cardW * 0.16,
                height: cardH * 0.2,
                borderRadius: cardH * 0.04,
                background: `linear-gradient(135deg, #E8D48A, #B8912F 60%, #8F6E1C)`,
                boxShadow: 'inset 0 0 8px rgba(0,0,0,0.4)',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  inset: '20% 28%',
                  border: '1.5px solid rgba(80,60,10,0.55)',
                  borderRadius: 3,
                }}
              />
            </div>

            {/* contactless */}
            <div
              style={{
                position: 'absolute',
                top: cardH * 0.24,
                left: cardW * 0.27,
                fontFamily: FONT,
                fontSize: cardH * 0.13,
                color: 'rgba(255,255,255,0.85)',
                transform: 'rotate(90deg)',
              }}
            >
              )))
            </div>

            {/* number: bullets + last4 only */}
            <div
              style={{
                position: 'absolute',
                top: band.number.top,
                left: cardW * 0.08,
                fontFamily: MONO,
                fontSize: numberFace,
                letterSpacing: numberTracking,
                color: '#FFFFFF',
                fontVariantNumeric: 'tabular-nums',
                whiteSpace: 'nowrap',
              }}
            >
              •••• •••• •••• {last4}
            </div>

            {/* bottom row */}
            <div
              style={{
                position: 'absolute',
                top: band.labels.top,
                left: cardW * 0.08,
                right: cardW * 0.08,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-end',
              }}
            >
              <div>
                <div
                  style={{
                    fontFamily: FONT,
                    fontSize: labelFont,
                    color: 'rgba(255,255,255,0.5)',
                    letterSpacing: 1.5,
                    textTransform: 'uppercase',
                  }}
                >
                  Card Holder
                </div>
                <div
                  style={{
                    fontFamily: FONT,
                    fontSize: holderFont,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    letterSpacing: 1.2,
                    marginTop: cardH * 0.02,
                  }}
                >
                  {holder}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div
                  style={{
                    fontFamily: FONT,
                    fontSize: labelFont,
                    color: 'rgba(255,255,255,0.5)',
                    letterSpacing: 1.5,
                    textTransform: 'uppercase',
                  }}
                >
                  Expires
                </div>
                <div
                  style={{
                    fontFamily: MONO,
                    fontSize: holderFont,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    marginTop: cardH * 0.02,
                  }}
                >
                  {expiry}
                </div>
              </div>
            </div>

            {/* brand — top-right, where a real card carries the scheme mark.
                It used to sit bottom-right at cardH*0.1 with a cardH*0.2 face,
                which put it straight through the EXPIRES row underneath. The
                top band holds only the chip, so there is room here and no
                stacking to reason about. */}
            <div
              style={{
                position: 'absolute',
                top: cardH * 0.12,
                right: cardW * 0.08,
                fontFamily: FONT,
                fontSize: cardH * 0.16,
                fontWeight: 900,
                fontStyle: 'italic',
                color: accentColor,
              }}
            >
              {brand}
            </div>
          </div>
        </div>
      </div>

      {subtitle && (
        <p
          style={{
            position: 'absolute',
            // Anchored to the BOTTOM of the safe box, not computed from its top.
            top: safe.top + safe.height - Math.round(height * 0.05),
            left: safe.left,
            width: safe.width,
            margin: 0,
            textAlign: 'center',
            fontFamily: FONT,
            fontSize: Math.round(height * 0.019),
            color: '#7A8598',
            opacity: reveal,
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
};
