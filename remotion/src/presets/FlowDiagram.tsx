import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';

/**
 * FlowDiagram — a pipeline that draws itself node by node.
 * Connectors grow between nodes, so the viewer sees data moving through stages.
 * Data: `title`, plus `nodes` = [{label, sub, color}] (or `steps` = [{label, detail}]).
 * Lays out vertically on portrait, horizontally on landscape.
 */
export const FlowDiagram: React.FC<BaseSceneProps> = ({
  title,
  text,
  nodes,
  steps,
  accentColor = BRAND.neon,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const vertical = height >= width;

  const items =
    (nodes && nodes.length ? nodes.map((n) => ({ label: n.label, sub: n.sub, color: n.color })) : null) ||
    (steps && steps.length ? steps.map((s) => ({ label: s.label, sub: s.detail, color: undefined })) : null) ||
    [{ label: '⚠ NO NODES IN SPEC', sub: undefined, color: undefined }];

  const header = title || text;
  const headerSpring = spring({ frame, fps, config: { damping: 14, stiffness: 110 } });

  // Each node gets a slot; the connector fills during the second half of the slot.
  const slot = 14;

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 50px',
        gap: '30px',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        overflow: 'hidden',
      }}
    >
      {header && (
        <h2
          style={{
            fontSize: vertical ? '52px' : '44px',
            fontWeight: 900,
            color: BRAND.text,
            margin: 0,
            textAlign: 'center',
            letterSpacing: '2px',
            textTransform: 'uppercase',
            opacity: headerSpring,
            transform: `translateY(${interpolate(headerSpring, [0, 1], [-26, 0])}px)`,
          }}
        >
          {header}
        </h2>
      )}

      <div
        style={{
          display: 'flex',
          flexDirection: vertical ? 'column' : 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 0,
        }}
      >
        {items.map((item, i) => {
          const appear = spring({
            frame: frame - 12 - i * slot,
            fps,
            config: { damping: 15, stiffness: 120 },
          });
          const connector = interpolate(
            frame,
            [12 + i * slot + slot * 0.5, 12 + (i + 1) * slot],
            [0, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
          );
          const color = item.color || (i % 2 === 0 ? accentColor : BRAND.cyan);

          return (
            <React.Fragment key={i}>
              <div
                style={{
                  opacity: appear,
                  transform: `scale(${interpolate(appear, [0, 1], [0.75, 1])})`,
                  backgroundColor: BRAND.surface,
                  border: `2px solid ${color}`,
                  borderRadius: '14px',
                  padding: vertical ? '22px 34px' : '20px 26px',
                  minWidth: vertical ? '520px' : '210px',
                  textAlign: 'center',
                  boxShadow: `0 0 22px ${color}35`,
                }}
              >
                <div style={{ fontSize: vertical ? '34px' : '26px', fontWeight: 900, color: BRAND.text }}>
                  {item.label}
                </div>
                {item.sub && (
                  <div style={{ fontSize: vertical ? '20px' : '16px', color: BRAND.muted, marginTop: '6px' }}>
                    {item.sub}
                  </div>
                )}
              </div>

              {i < items.length - 1 && (
                <div
                  style={{
                    width: vertical ? '5px' : '58px',
                    height: vertical ? '46px' : '5px',
                    backgroundColor: '#23262C',
                    position: 'relative',
                    borderRadius: '3px',
                    overflow: 'hidden',
                    flexShrink: 0,
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      backgroundColor: accentColor,
                      transformOrigin: vertical ? 'top center' : 'left center',
                      transform: vertical ? `scaleY(${connector})` : `scaleX(${connector})`,
                      boxShadow: `0 0 12px ${accentColor}`,
                    }}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
