import React, { useMemo, useRef } from 'react';
import { ThreeCanvas } from '@remotion/three';
import {
  useCurrentFrame,
  useVideoConfig,
  staticFile,
  interpolate,
  delayRender,
  continueRender,
} from 'remotion';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { BaseSceneProps } from '../../VideoSpec.schema';
import { BRAND } from '../brand';
import { resolveMotion } from '../../lib/motion';
import { getSafeArea } from '../../lib/safeArea';
import { fitOneLine, fitWrapped } from '../../theme/layout';

const ORBIT_FONT = '"Inter", "SF Pro Display", -apple-system, sans-serif';

/**
 * Load a .glb and return it once it is fully parsed, or null while pending.
 *
 * WHY NOT useGLTF + <Suspense>
 * ----------------------------
 * ThreeCanvas runs r3f with frameloop="demand": it rasterises ONCE per Remotion
 * frame and then stops. useGLTF suspends, Remotion's delayRender for the canvas
 * resolves on that first empty draw, and the model — which arrives ~170ms later
 * — lands in the scene graph after the only draw that will ever happen. Result:
 * a frame that reports success, has correct geometry in memory, and shows
 * nothing. Measured: fetch completed at +168ms, "R3F render frame" cleared at
 * +94ms; centre of frame 0.0% ink, 0 colours.
 *
 * So the model is loaded OUTSIDE the canvas, the render is held with
 * delayRender until the geometry exists, and the canvas is not mounted at all
 * until then. Its single on-demand draw therefore already contains the mesh.
 * Verified with the same probe: 75.8% ink, 570 distinct colours.
 */
const useGlbScene = (url: string): THREE.Group | null => {
  const [handle] = React.useState(() => delayRender(`ModelOrbit3D: loading ${url}`));
  const [scene, setScene] = React.useState<THREE.Group | null>(null);

  React.useEffect(() => {
    let alive = true;
    import('three/examples/jsm/loaders/GLTFLoader.js')
      .then(({ GLTFLoader }) => {
        new GLTFLoader().load(
          url,
          (gltf) => {
            if (!alive) return;
            setScene(gltf.scene);
            continueRender(handle);
          },
          undefined,
          (err) => {
            // Never leave the render hanging: a missing model must fail loudly
            // in QA (empty subject) rather than time out after 30s.
            // eslint-disable-next-line no-console
            console.error(`[ModelOrbit3D] failed to load ${url}:`, err);
            continueRender(handle);
          }
        );
      })
      .catch(() => continueRender(handle));
    return () => {
      alive = false;
    };
  }, [url, handle]);

  return scene;
};

interface ModelViewerProps {
  scene: THREE.Group;
  frame: number;
  durationInFrames: number;
  accentColor: string;
  material?: 'original' | 'clay' | 'glass' | 'wireframe' | 'xray';
  autoFrame?: boolean;
  modelScale?: number;
  spinModel?: boolean;
}

/**
 * GLTF Model with auto-framing, material override, and optional rotation.
 */
const ModelMesh: React.FC<ModelViewerProps> = ({
  scene,
  frame,
  durationInFrames,
  accentColor,
  material = 'original',
  autoFrame = true,
  modelScale = 1.0,
  spinModel = false,
}) => {
  const modelRef = useRef<THREE.Group>(null);

  // Deep clone scene so multiple instances or frame re-evaluations do not clash.
  const cloned = useMemo(() => {
    const root = scene.clone(true);


    if (material !== 'original') {
      root.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          if (material === 'clay') {
            mesh.material = new THREE.MeshStandardMaterial({
              color: 0xdedede,
              roughness: 0.85,
              metalness: 0.1,
            });
          } else if (material === 'wireframe') {
            mesh.material = new THREE.MeshBasicMaterial({
              color: accentColor,
              wireframe: true,
            });
          } else if (material === 'glass') {
            mesh.material = new THREE.MeshPhysicalMaterial({
              color: accentColor,
              transparent: true,
              opacity: 0.55,
              roughness: 0.15,
              metalness: 0.8,
              transmission: 0.6,
            });
          } else if (material === 'xray') {
            mesh.material = new THREE.MeshBasicMaterial({
              color: accentColor,
              wireframe: true,
              transparent: true,
              opacity: 0.35,
            });
          }
        }
      });
    }

    if (autoFrame) {
      // Normalise ANY model to the same on-screen size: a 0.1m prop and a 10m
      // vehicle must both fill the frame, so scale by the largest dimension.
      const box = new THREE.Box3().setFromObject(root);
      const size = new THREE.Vector3();
      const centre = new THREE.Vector3();
      box.getSize(size);
      box.getCenter(centre);
      const maxDim = Math.max(size.x, size.y, size.z);
      if (maxDim > 0.0001) {
        const scale = (3.6 / maxDim) * modelScale;
        root.scale.set(scale, scale, scale);
        // Recentre on the origin AFTER scaling. Many GLBs are authored with
        // their pivot at a corner or at the feet; orbiting an off-centre pivot
        // swings the subject in and out of frame. Done explicitly rather than
        // with drei's <Center> so the offset is applied to the same object the
        // camera rig targets.
        root.position.set(-centre.x * scale, -centre.y * scale, -centre.z * scale);
      }
    } else if (modelScale !== 1.0) {
      root.scale.multiplyScalar(modelScale);
    }

    return root;
  }, [scene, material, autoFrame, modelScale, accentColor]);

  // Spin model if requested
  const modelAngle = spinModel
    ? (frame / Math.max(durationInFrames, 1)) * Math.PI * 2
    : 0;

  return (
    <group ref={modelRef} rotation={[0, modelAngle, 0]}>
      <primitive object={cloned} />
    </group>
  );
};

/**
 * Camera Orbit Rig driven deterministically by Remotion frame & motion layer.
 */
const CameraRig: React.FC<{
  frame: number;
  durationInFrames: number;
  orbit: 'full360' | 'arc' | 'figureEight' | 'dolly';
  orbitDegrees: number;
  startAngle: number;
  elevation: number;
  motionProgress: number;
}> = ({
  durationInFrames,
  orbit,
  orbitDegrees,
  startAngle,
  elevation,
  motionProgress,
}) => {
  const p = motionProgress;
  const radStart = (startAngle * Math.PI) / 180;
  const sweepRad = (orbitDegrees * Math.PI) / 180;

  let angle = radStart + p * sweepRad;
  let radius = 6.2;
  let camY = elevation;

  if (orbit === 'arc') {
    angle = radStart + p * ((orbitDegrees || 90) * Math.PI) / 180;
    radius = 5.8;
  } else if (orbit === 'figureEight') {
    angle = radStart + p * Math.PI * 2;
    camY = elevation + Math.sin(angle * 2) * 0.8;
    radius = 6.0 + Math.cos(angle) * 0.6;
  } else if (orbit === 'dolly') {
    angle = radStart;
    radius = interpolate(p, [0, 1], [8.0, 4.2]);
  }

  // Camera is positioned during render, not in useFrame. ThreeCanvas runs
  // frameloop="demand": it draws once per Remotion frame, and a useFrame
  // callback is not guaranteed to land before that draw -- the same ordering
  // that made a late-loading GLB render as an empty canvas. Deriving the
  // transform from `frame` here keeps every worker deterministic.
  const camera = useThree((s) => s.camera);
  const x = Math.sin(angle) * radius;
  const z = Math.cos(angle) * radius;
  camera.position.set(x, camY, z);
  camera.lookAt(0, 0, 0);
  camera.updateProjectionMatrix();

  return null;
};

/**
 * Hotspot pins in 3D space with pulse animation
 */
const HotspotMarkers: React.FC<{
  hotspots?: { position: [number, number, number]; label: string; description?: string }[];
  accentColor: string;
  frame: number;
}> = ({ hotspots, accentColor, frame }) => {
  if (!hotspots || hotspots.length === 0) return null;

  return (
    <group>
      {hotspots.map((hs, i) => {
        const pulse = Math.sin(frame * 0.15 + i) * 0.15 + 1.0;
        return (
          <group key={i} position={hs.position}>
            {/* Outer ring */}
            <mesh scale={[pulse, pulse, pulse]}>
              <ringGeometry args={[0.12, 0.18, 24]} />
              <meshBasicMaterial color={accentColor} side={THREE.DoubleSide} transparent opacity={0.8} />
            </mesh>
            {/* Inner dot */}
            <mesh>
              <circleGeometry args={[0.08, 24]} />
              <meshBasicMaterial color="#FFFFFF" side={THREE.DoubleSide} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
};

export const ModelOrbit3D: React.FC<BaseSceneProps> = ({
  title,
  subtitle,
  badge,
  accentColor = BRAND.accentGreen,
  modelUrl,
  modelScale = 1.0,
  orbit = 'full360',
  orbitDegrees = 360,
  startAngle = -30,
  elevation = 1.6,
  autoFrame = true,
  spinModel = false,
  lighting = 'studio',
  material = 'original',
  groundShadow = 'soft',
  hotspots,
  motion,
  safeArea = 'platform',
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);

  // Orbit progress, 0..1 across the WHOLE scene.
  //
  // Two things must be right here, and both were wrong before:
  //   1. resolveMotion's (from, to) is the OUTPUT range, not a frame window.
  //      Passing (frame, 0, durationInFrames) returned 0..120 while CameraRig
  //      treats the value as 0..1, multiplying the sweep by up to 120.
  //   2. MotionConfig.duration defaults to 24 frames, and every intensity
  //      preset is shorter than a typical scene (calm 60, normal 36, punchy 24,
  //      extreme 18). Past `duration` the resolver returns `to` verbatim, so the
  //      camera froze partway and every later frame shared one bearing.
  //      Measured before the fix: frames 0 and 60 were byte-identical PNGs.
  //
  // A camera move is not an entrance animation -- it has to last the whole
  // shot -- so the scene length is forced as the duration while the author's
  // curve is respected. An explicit `motion.camera.duration` still wins.
  const cameraMotion = useMemo(() => {
    const channel =
      motion && typeof motion === 'object' && 'camera' in motion
        ? (motion as Record<string, { duration?: number }>).camera
        : undefined;
    return resolveMotion(
      { curve: 'easeInOut', ...(channel ?? {}), duration: channel?.duration ?? durationInFrames },
      fps,
      'camera'
    );
  }, [motion, fps, durationInFrames]);
  const motionProgress = cameraMotion(frame, 0, 1);

  // Header entrance reveal
  const headerMotion = resolveMotion(motion, fps, 'reveal');
  const headerReveal = headerMotion(frame, 0, Math.min(24, durationInFrames));

  // Resolve GLB URL to staticFile if relative or provider reference
  const resolvedUrl = useMemo(() => {
    if (!modelUrl) {
      return staticFile('models/khronos/DamagedHelmet.glb');
    }
    if (modelUrl.startsWith('http://') || modelUrl.startsWith('https://') || modelUrl.startsWith('data:')) {
      return modelUrl;
    }
    if (modelUrl.startsWith('khronos:') || modelUrl.startsWith('quaternius:') || modelUrl.startsWith('kenney:')) {
      const [provider, id] = modelUrl.split(':');
      return staticFile(`models/${provider}/${id}.glb`);
    }
    return staticFile(modelUrl);
  }, [modelUrl]);

  // Loaded OUTSIDE the canvas and BEFORE it mounts -- see useGlbScene.
  const modelScene = useGlbScene(resolvedUrl);

  // Typography auto-fit inside safe area bounds
  const titleFontSize = fitOneLine({
    text: title || '',
    fontFamily: ORBIT_FONT,
    fontWeight: 900,
    maxWidth: safe.width - 40,
    maxFontSize: 64,
    minFontSize: 32,
  });

  const subFit = fitWrapped({
    text: subtitle || '',
    fontFamily: ORBIT_FONT,
    fontWeight: 500,
    maxWidth: safe.width - 40,
    maxHeight: 140,
    maxFontSize: 32,
    minFontSize: 20,
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        backgroundColor: BRAND.bg,
        overflow: 'hidden',
      }}
    >
      {/* 3D Scene Viewport.
          Mounted ONLY once the geometry is parsed: ThreeCanvas draws on demand
          exactly once per frame, so a canvas mounted earlier would rasterise an
          empty scene and never redraw. The text overlay below still renders
          while loading, so a missing model shows as an empty subject with
          intact typography rather than a black frame. */}
      {modelScene ? (
        <ThreeCanvas
        width={width}
        height={height}
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
        camera={{ fov: 44, position: [0, elevation, 6.2] }}
        gl={{ antialias: true, alpha: true }}
      >
        <color attach="background" args={[BRAND.bg]} />

        {/* Dynamic Lighting Setups */}
        {lighting === 'studio' && (
          <>
            <ambientLight intensity={0.65} />
            <directionalLight position={[6, 10, 6]} intensity={1.4} />
            <directionalLight position={[-6, 4, -4]} intensity={0.7} color={accentColor} />
            <pointLight position={[0, -5, 4]} intensity={0.4} />
          </>
        )}
        {lighting === 'rim' && (
          <>
            <ambientLight intensity={0.3} />
            <directionalLight position={[0, 8, -8]} intensity={2.4} color={accentColor} />
            <directionalLight position={[6, 3, 5]} intensity={0.5} />
          </>
        )}
        {lighting === 'dramatic' && (
          <>
            <ambientLight intensity={0.25} />
            <spotLight position={[5, 12, 5]} angle={0.4} penumbra={0.8} intensity={2.8} />
            <pointLight position={[-4, -2, -4]} intensity={0.8} color={accentColor} />
          </>
        )}
        {lighting === 'neon' && (
          <>
            <ambientLight intensity={0.35} />
            <directionalLight position={[6, 6, 4]} intensity={1.5} color={BRAND.accentCyan} />
            <directionalLight position={[-6, -4, 4]} intensity={1.5} color={accentColor} />
          </>
        )}

        {/* Orbit Camera Controller */}
        <CameraRig
          frame={frame}
          durationInFrames={durationInFrames}
          orbit={orbit}
          orbitDegrees={orbitDegrees}
          startAngle={startAngle}
          elevation={elevation}
          motionProgress={motionProgress}
        />

        {/* Geometry is already parsed here -- the canvas never mounts without it. */}
        <ModelMesh
          scene={modelScene}
          frame={frame}
          durationInFrames={durationInFrames}
          accentColor={accentColor}
          material={material}
          autoFrame={autoFrame}
          modelScale={modelScale}
          spinModel={spinModel}
        />
        <HotspotMarkers hotspots={hotspots} accentColor={accentColor} frame={frame} />

        {/* Ground grid / shadow */}
        {groundShadow !== 'off' && (
          <gridHelper
            args={[20, 20, accentColor, '#22262E']}
            position={[0, -2.0, 0]}
          />
        )}
      </ThreeCanvas>
      ) : null}

      {/* Safe Area UI Overlay: Header & Subtitle */}
      <div
        style={{
          position: 'absolute',
          top: safe.top,
          left: safe.left,
          width: safe.width,
          height: safe.height,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          pointerEvents: 'none',
          boxSizing: 'border-box',
          padding: '24px 20px',
        }}
      >
        {/* Top Header Section */}
        <div
          style={{
            opacity: headerReveal,
            transform: `translateY(${(1 - headerReveal) * -20}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-start',
            gap: 12,
          }}
        >
          {badge && (
            <div
              style={{
                backgroundColor: `${accentColor}22`,
                border: `1.5px solid ${accentColor}`,
                color: accentColor,
                padding: '6px 14px',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 700,
                fontFamily: ORBIT_FONT,
                textTransform: 'uppercase',
                letterSpacing: 1.5,
              }}
            >
              {badge}
            </div>
          )}
          {title && (
            <h1
              style={{
                margin: 0,
                fontFamily: ORBIT_FONT,
                fontSize: titleFontSize,
                fontWeight: 900,
                color: BRAND.text,
                lineHeight: 1.1,
                letterSpacing: -0.5,
                textShadow: '0 4px 18px rgba(0,0,0,0.85)',
              }}
            >
              {title}
            </h1>
          )}
        </div>

        {/* Bottom Subtitle / Metadata Section */}
        {subtitle && (
          <div
            style={{
              opacity: headerReveal,
              transform: `translateY(${(1 - headerReveal) * 20}px)`,
              backgroundColor: 'rgba(22, 24, 28, 0.75)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 14,
              padding: '16px 20px',
              maxWidth: Math.min(safe.width, 860),
              alignSelf: 'center',
            }}
          >
            <p
              style={{
                margin: 0,
                fontFamily: ORBIT_FONT,
                fontSize: subFit.fontSize,
                fontWeight: 500,
                color: BRAND.muted,
                lineHeight: 1.35,
                textAlign: 'center',
              }}
            >
              {subtitle}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
