import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BaseSceneProps } from '../VideoSpec.schema';
import { BRAND } from './brand';
import { calculateStagger, resolveMotion } from '../lib/motion';
import { getSafeArea } from '../lib/safeArea';
import { fitOneLine } from '../theme/layout';

/**
 * Single font stack constant for FlowDiagram.
 * Passed to fitOneLine and rendered elements so measurement matches rendering face.
 */
const FLOW_FONT = 'system-ui, -apple-system, sans-serif';

/**
 * FlowDiagram — a pipeline that draws itself node by node.
 * Connectors grow between nodes, so the viewer sees data moving through stages.
 *
 * Safe area and motion refactor notes:
 *  - Replaced hardcoded `padding: '60px 50px'` with safe area box positioning (`safe.top`, `safe.left`, `safe.width`, `safe.height`).
 *    On vertical 1080x1920, top 280px and bottom 380px platform strips hid header/nodes; container now sits within safe box.
 *  - Derived maximum node width and connector dimensions from `safe.width` & `safe.height` to guarantee full containment.
 *  - Measured node labels with `fitOneLine` to prevent label overflow.
 *  - Replaced raw spring calls with `resolveMotion(motion, fps, 'reveal')` for header and `'transform'` for staggered nodes.
 *  - Utilized `calculateStagger(count, stagger, staggerFrom)` from `lib/motion.ts` for clean node delay sequencing.
 */
export const FlowDiagram: React.FC<BaseSceneProps> = ({
  title,
  text,
  nodes,
  steps,
  accentColor = BRAND.neon,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const vertical = height >= width;

  const items =
    (nodes && nodes.length ? nodes.map((n) => ({ label: n.label, sub: n.sub, color: n.color })) : null) ||
    (steps && steps.length ? steps.map((s) => ({ label: s.label, sub: s.detail, color: undefined })) : null) ||
    [{ label: '⚠ NO NODES IN SPEC', sub: undefined, color: undefined }];

  const header = title || text;
  const safe = getSafeArea(width, height, safeArea);

  // 'reveal' channel for header entrance; 'transform' channel for node pop-in & connector progression.
  const animateReveal = resolveMotion(motion, fps, 'reveal');
  const animateTransform = resolveMotion(motion, fps, 'transform');

  const headerProgress = animateReveal(frame, 0, 1);
  const headerOffsetY = interpolate(headerProgress, [0, 1], [-26, 0]);

  // Motion stagger settings. Default stagger is 14 frames between sequential nodes.
  const staggerFrames = motion?.transform?.stagger ?? motion?.default?.stagger ?? 14;
  const staggerDelays = calculateStagger(items.length, staggerFrames, 'first');

  // Compute layout dimensions relative to safe box.
  // In vertical orientation, calculate node minWidth/maxWidth safely within safe.width.
  const maxNodeWidth = Math.min(safe.width, vertical ? 700 : Math.floor(safe.width / items.length));
  const nodePaddingX = vertical ? 34 : 26;
  const nodeInnerWidth = Math.max(100, maxNodeWidth - nodePaddingX * 2);

  const headerFontSize = header
    ? fitOneLine({
        text: header,
        maxWidth: safe.width,
        fontFamily: FLOW_FONT,
        fontWeight: 900,
        letterSpacing: '2px',
        textTransform: 'uppercase',
        maxFontSize: vertical ? 52 : 44,
        minFontSize: 24,
      })
    : 44;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: BRAND.bg,
        overflow: 'hidden',
        fontFamily: FLOW_FONT,
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: safe.top,
          left: safe.left,
          width: safe.width,
          height: safe.height,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '30px',
          boxSizing: 'border-box',
        }}
      >
        {header && (
          <h2
            style={{
              fontSize: `${headerFontSize}px`,
              fontWeight: 900,
              color: BRAND.text,
              margin: 0,
              textAlign: 'center',
              letterSpacing: '2px',
              textTransform: 'uppercase',
              opacity: headerProgress,
              transform: `translateY(${headerOffsetY}px)`,
              maxWidth: safe.width,
              lineHeight: 1.15,
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
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
            width: safe.width,
            boxSizing: 'border-box',
          }}
        >
          {items.map((item, i) => {
            const startFrame = 12 + staggerDelays[i];
            const nodeProgress = animateTransform(frame - startFrame, 0, 1);
            const scale = interpolate(nodeProgress, [0, 1], [0.75, 1]);

            // Connector line grows during the second half of the node slot window.
            const connectorStart = startFrame + staggerFrames * 0.5;
            const connectorProgress = animateTransform(
              frame - connectorStart,
              0,
              1
            );

            const color = item.color || (i % 2 === 0 ? accentColor : BRAND.cyan);

            const labelFontSize = fitOneLine({
              text: item.label,
              maxWidth: nodeInnerWidth,
              fontFamily: FLOW_FONT,
              fontWeight: 900,
              maxFontSize: vertical ? 34 : 26,
              minFontSize: 18,
            });

            return (
              <React.Fragment key={i}>
                <div
                  style={{
                    opacity: nodeProgress,
                    transform: `scale(${scale})`,
                    backgroundColor: BRAND.surface,
                    border: `2px solid ${color}`,
                    borderRadius: '14px',
                    padding: vertical ? `22px ${nodePaddingX}px` : `20px ${nodePaddingX}px`,
                    width: vertical ? `${Math.min(safe.width, 560)}px` : undefined,
                    minWidth: vertical ? undefined : `${Math.min(210, Math.floor(safe.width / items.length))}px`,
                    maxWidth: `${maxNodeWidth}px`,
                    textAlign: 'center',
                    boxShadow: `0 0 22px ${color}35`,
                    boxSizing: 'border-box',
                    overflowWrap: 'break-word',
                    wordBreak: 'break-word',
                  }}
                >
                  <div
                    style={{
                      fontSize: `${labelFontSize}px`,
                      fontWeight: 900,
                      color: BRAND.text,
                      lineHeight: 1.15,
                    }}
                  >
                    {item.label}
                  </div>
                  {item.sub && (
                    <div
                      style={{
                        fontSize: vertical ? '20px' : '16px',
                        color: BRAND.muted,
                        marginTop: '6px',
                        lineHeight: 1.25,
                      }}
                    >
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
                        transform: vertical ? `scaleY(${connectorProgress})` : `scaleX(${connectorProgress})`,
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
    </div>
  );
};
