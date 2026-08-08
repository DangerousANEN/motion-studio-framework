import React from 'react';
import { ThreeCanvas } from '@remotion/three';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { useFrame } from '@react-three/fiber';
import { BaseSceneProps } from '../../VideoSpec.schema';
import { BRAND } from '../brand';

/**
 * LayerStack3D — transformer blocks as stacked slabs, rising one by one while a
 * signal pulse travels upward through them. Built for "how it works" beats where
 * depth is the whole point.
 *
 * Data: `layers` (labels, bottom -> top). Falls back to a visible marker.
 */

const Slab: React.FC<{
  index: number;
  total: number;
  label: string;
  frame: number;
  fps: number;
  accentColor: string;
}> = ({ index, total, label, frame, fps, accentColor }) => {
  const delay = 8 + index * 5;
  const rise = spring({
    frame: frame - delay,
    fps,
    config: { damping: 15, stiffness: 90 },
  });

  const y = (index - (total - 1) / 2) * 0.92;
  const settledY = interpolate(rise, [0, 1], [y - 3.2, y]);

  // Pulse sweeps bottom -> top after the stack has assembled.
  const pulseStart = 12 + total * 5;
  const pulsePos = interpolate(frame, [pulseStart, pulseStart + total * 7], [0, total], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const heat = Math.max(0, 1 - Math.abs(pulsePos - index) * 1.35);

  return (
    <group position={[0, settledY, 0]} scale={rise}>
      <mesh>
        <boxGeometry args={[4.4, 0.52, 2.5]} />
        <meshStandardMaterial
          color={BRAND.surface}
          emissive={accentColor}
          emissiveIntensity={0.06 + heat * 0.85}
          metalness={0.35}
          roughness={0.55}
        />
      </mesh>
      {/* Slightly larger translucent shell reads as an edge glow without
          needing EdgesGeometry, which cannot be built declaratively here. */}
      <mesh scale={[1.012, 1.06, 1.012]}>
        <boxGeometry args={[4.4, 0.52, 2.5]} />
        <meshBasicMaterial
          color={accentColor}
          transparent
          opacity={0.06 + heat * 0.3}
          wireframe
        />
      </mesh>
    </group>
  );
};

const OrbitRig: React.FC<{ frame: number; durationInFrames: number }> = ({
  frame,
  durationInFrames,
}) => {
  const p = durationInFrames > 0 ? frame / durationInFrames : 0;
  const angle = -0.5 + p * 1.15;
  const radius = interpolate(p, [0, 1], [10.5, 8.2]);

  useFrame(({ camera }) => {
    camera.position.set(Math.sin(angle) * radius, 1.6 + p * 1.2, Math.cos(angle) * radius);
    camera.lookAt(0, 0, 0);
  });
  return null;
};

export const LayerStack3D: React.FC<BaseSceneProps> = ({
  title,
  subtitle,
  layers,
  accentColor = BRAND.accentGreen,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const vertical = height >= width;

  const labels = layers && layers.length > 0 ? layers : ['⚠ NO LAYERS IN SPEC'];

  return (
    <div style={{ flex: 1, backgroundColor: BRAND.bg, position: 'relative', overflow: 'hidden' }}>
      <ThreeCanvas
        width={width}
        height={height}
        style={{ position: 'absolute', inset: 0 }}
        camera={{ fov: 46, position: [0, 1.6, 10.5] }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={[BRAND.bg]} />
        <ambientLight intensity={0.55} />
        <directionalLight position={[5, 9, 6]} intensity={1.15} />
        <pointLight position={[-6, -3, 4]} intensity={0.7} color={accentColor} />
        <OrbitRig frame={frame} durationInFrames={durationInFrames} />
        {labels.map((label, i) => (
          <Slab
            key={i}
            index={i}
            total={labels.length}
            label={label}
            frame={frame}
            fps={fps}
            accentColor={accentColor}
          />
        ))}
      </ThreeCanvas>

      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
          alignItems: vertical ? 'center' : 'flex-start',
          padding: vertical ? '110px 56px 0' : '80px 0 0 96px',
          pointerEvents: 'none',
          fontFamily: 'system-ui, -apple-system, sans-serif',
        }}
      >
        <h1
          style={{
            fontSize: vertical ? '60px' : '68px',
            fontWeight: 900,
            color: BRAND.text,
            margin: 0,
            letterSpacing: '-1.5px',
            textAlign: vertical ? 'center' : 'left',
            textShadow: `0 5px 34px ${BRAND.bg}`,
            opacity: interpolate(frame, [4, 24], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          {title || '⚠ NO TITLE IN SPEC'}
        </h1>
        {subtitle && (
          <p
            style={{
              fontSize: vertical ? '29px' : '31px',
              color: BRAND.muted,
              marginTop: '16px',
              textAlign: vertical ? 'center' : 'left',
              maxWidth: vertical ? '84%' : '44%',
              lineHeight: 1.35,
              textShadow: `0 3px 22px ${BRAND.bg}`,
              opacity: interpolate(frame, [18, 40], [0, 1], { extrapolateRight: 'clamp' }),
            }}
          >
            {subtitle}
          </p>
        )}
      </div>

      {/* Layer labels as a DOM list — crisper than 3D text at 1080p */}
      <div
        style={{
          position: 'absolute',
          right: vertical ? '40px' : '110px',
          top: '50%',
          transform: 'translateY(-50%)',
          display: 'flex',
          flexDirection: 'column-reverse',
          gap: '10px',
          pointerEvents: 'none',
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
        }}
      >
        {labels.map((label, i) => (
          <div
            key={i}
            style={{
              fontSize: vertical ? '21px' : '22px',
              color: BRAND.text,
              backgroundColor: 'rgba(22,24,28,0.82)',
              border: `1px solid ${accentColor}55`,
              borderRadius: '7px',
              padding: '7px 13px',
              opacity: interpolate(frame, [10 + i * 5, 24 + i * 5], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
            }}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
  );
};
