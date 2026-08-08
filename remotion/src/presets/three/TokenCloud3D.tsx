import React, { useMemo, useRef } from 'react';
import { ThreeCanvas } from '@remotion/three';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { BaseSceneProps } from '../../VideoSpec.schema';
import { BRAND } from '../brand';

/**
 * TokenCloud3D — an embedding space made literal: tokens as points in 3D,
 * clustering into semantic groups while the camera orbits.
 *
 * Frame-driven only. `useFrame` is never used for animation state, because
 * Remotion renders discontinuously (frame 0, 5, 200...) and any accumulated
 * delta would desync across the render workers.
 */

const CLUSTER_COLORS = [BRAND.accentCyan, BRAND.accentGreen, BRAND.gold];

const PointCloud: React.FC<{ frame: number; durationInFrames: number; count: number }> = ({
  frame,
  durationInFrames,
  count,
}) => {
  const geomRef = useRef<THREE.BufferGeometry>(null);

  // Deterministic pseudo-random: same layout on every render worker.
  const { scattered, clustered, colors } = useMemo(() => {
    let seed = 1337;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    };

    const scattered = new Float32Array(count * 3);
    const clustered = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    const centers = [
      [-2.2, 0.9, 0.0],
      [2.2, -0.4, -0.8],
      [0.1, -1.9, 0.9],
    ];

    for (let i = 0; i < count; i++) {
      // Start: uniform noise in a wide box — an untrained, meaningless space.
      scattered[i * 3] = (rand() - 0.5) * 9;
      scattered[i * 3 + 1] = (rand() - 0.5) * 9;
      scattered[i * 3 + 2] = (rand() - 0.5) * 9;

      // End: tight gaussian blobs — learned structure.
      const c = i % centers.length;
      const spread = 0.62;
      clustered[i * 3] = centers[c][0] + (rand() - 0.5) * spread;
      clustered[i * 3 + 1] = centers[c][1] + (rand() - 0.5) * spread;
      clustered[i * 3 + 2] = centers[c][2] + (rand() - 0.5) * spread;

      const col = new THREE.Color(CLUSTER_COLORS[c]);
      colors[i * 3] = col.r;
      colors[i * 3 + 1] = col.g;
      colors[i * 3 + 2] = col.b;
    }
    return { scattered, clustered, colors };
  }, [count]);

  // Ease scatter -> clusters over the middle 70% of the scene.
  const t = interpolate(frame, [durationInFrames * 0.1, durationInFrames * 0.8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const eased = t * t * (3 - 2 * t);

  const positions = useMemo(() => {
    const out = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i++) {
      out[i] = scattered[i] + (clustered[i] - scattered[i]) * eased;
    }
    return out;
  }, [count, scattered, clustered, eased]);

  useFrame(() => {
    if (geomRef.current) {
      geomRef.current.attributes.position.needsUpdate = true;
    }
  });

  return (
    <points>
      <bufferGeometry ref={geomRef}>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.085}
        vertexColors
        transparent
        opacity={0.95}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
};

const OrbitCamera: React.FC<{ frame: number; durationInFrames: number }> = ({
  frame,
  durationInFrames,
}) => {
  const progress = durationInFrames > 0 ? frame / durationInFrames : 0;
  const angle = progress * Math.PI * 0.75 - Math.PI * 0.2;
  const radius = interpolate(progress, [0, 1], [11, 7.6]);

  useFrame(({ camera }) => {
    camera.position.set(
      Math.sin(angle) * radius,
      interpolate(progress, [0, 1], [2.6, 0.7]),
      Math.cos(angle) * radius,
    );
    camera.lookAt(0, 0, 0);
  });
  return null;
};

export const TokenCloud3D: React.FC<BaseSceneProps> = ({
  title,
  subtitle,
  accentColor = BRAND.accentCyan,
  pointCount = 900,
}) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const vertical = height >= width;

  return (
    <div style={{ flex: 1, backgroundColor: BRAND.bg, position: 'relative', overflow: 'hidden' }}>
      <ThreeCanvas
        width={width}
        height={height}
        style={{ position: 'absolute', inset: 0 }}
        camera={{ fov: 50, position: [0, 2.6, 11] }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={[BRAND.bg]} />
        <ambientLight intensity={0.7} />
        <pointLight position={[6, 6, 6]} intensity={1.1} color={accentColor} />
        <OrbitCamera frame={frame} durationInFrames={durationInFrames} />
        <PointCloud frame={frame} durationInFrames={durationInFrames} count={pointCount} />
      </ThreeCanvas>

      {/* Text overlay sits above the canvas in normal DOM */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: vertical ? 'flex-end' : 'center',
          alignItems: vertical ? 'center' : 'flex-start',
          padding: vertical ? '0 56px 190px' : '0 0 0 96px',
          pointerEvents: 'none',
          fontFamily: 'system-ui, -apple-system, sans-serif',
        }}
      >
        <h1
          style={{
            fontSize: vertical ? '68px' : '76px',
            fontWeight: 900,
            color: BRAND.text,
            margin: 0,
            lineHeight: 1.05,
            textAlign: vertical ? 'center' : 'left',
            letterSpacing: '-2px',
            textShadow: `0 6px 40px ${BRAND.bg}, 0 0 90px ${BRAND.bg}`,
            opacity: interpolate(frame, [6, 26], [0, 1], { extrapolateRight: 'clamp' }),
            transform: `translateY(${interpolate(frame, [6, 30], [26, 0], {
              extrapolateRight: 'clamp',
            })}px)`,
            maxWidth: vertical ? '100%' : '52%',
          }}
        >
          {title || '⚠ NO TITLE IN SPEC'}
        </h1>
        {subtitle && (
          <p
            style={{
              fontSize: vertical ? '31px' : '33px',
              color: BRAND.muted,
              marginTop: '20px',
              textAlign: vertical ? 'center' : 'left',
              maxWidth: vertical ? '86%' : '46%',
              lineHeight: 1.35,
              textShadow: `0 3px 26px ${BRAND.bg}`,
              opacity: interpolate(frame, [22, 44], [0, 1], { extrapolateRight: 'clamp' }),
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
};
