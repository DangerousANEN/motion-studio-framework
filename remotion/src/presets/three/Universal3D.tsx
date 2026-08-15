import React from 'react';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import {continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import * as THREE from 'three';

export type CameraPreset = 'orbit' | 'arc' | 'dolly' | 'figureEight';
export type MaterialMode = 'original' | 'clay' | 'glass' | 'wireframe';
export type FallbackShape = 'orb' | 'cube' | 'ring' | 'chip' | 'nodes';

const resolveAsset = (value?: string) => !value ? '' : /^(https?:|data:)/i.test(value) ? value : staticFile(value);

/** Holds a Remotion render until GLB geometry is genuinely available. */
const useAssetScene = (assetUrl?: string): THREE.Group | null => {
  const url = resolveAsset(assetUrl);
  const [handle] = React.useState(() => delayRender(`Universal3D asset: ${url || 'fallback'}`));
  const [scene, setScene] = React.useState<THREE.Group | null>(null);
  React.useEffect(() => {
    if (!url) { continueRender(handle); return; }
    let alive = true;
    import('three/examples/jsm/loaders/GLTFLoader.js').then(({GLTFLoader}) => {
      new GLTFLoader().load(url, (gltf) => { if (alive) setScene(gltf.scene); continueRender(handle); }, undefined, () => continueRender(handle));
    }).catch(() => continueRender(handle));
    return () => { alive = false; };
  }, [url, handle]);
  return scene;
};

const CameraRig: React.FC<{preset: CameraPreset; progress: number}> = ({preset, progress}) => {
  const camera = useThree((state) => state.camera);
  let angle = -0.65 + progress * Math.PI * 1.5; let radius = 5.5; let y = 1.1;
  if (preset === 'arc') { angle = -.65 + progress * Math.PI; radius = 5.2; }
  if (preset === 'dolly') { angle = -.45; radius = 7.2 - progress * 3.0; }
  if (preset === 'figureEight') { angle = progress * Math.PI * 2; radius = 5.5 + Math.cos(angle) * .5; y = 1.1 + Math.sin(angle * 2) * .7; }
  camera.position.set(Math.sin(angle) * radius, y, Math.cos(angle) * radius);
  camera.lookAt(0, 0, 0); camera.updateProjectionMatrix();
  return null;
};

const AssetMesh: React.FC<{scene: THREE.Group; material: MaterialMode; accent: string}> = ({scene, material, accent}) => {
  const object = React.useMemo(() => {
    const clone = scene.clone(true); const box = new THREE.Box3().setFromObject(clone); const size = new THREE.Vector3(); const center = new THREE.Vector3(); box.getSize(size); box.getCenter(center); const max = Math.max(size.x, size.y, size.z, .001); const scale = 3.4 / max; clone.scale.setScalar(scale); clone.position.set(-center.x * scale, -center.y * scale, -center.z * scale);
    if (material !== 'original') clone.traverse((node) => { if ((node as THREE.Mesh).isMesh) { const mesh = node as THREE.Mesh; if (material === 'clay') mesh.material = new THREE.MeshStandardMaterial({color: 0xdddddd, roughness: .82, metalness: .08}); if (material === 'wireframe') mesh.material = new THREE.MeshBasicMaterial({color: accent, wireframe: true}); if (material === 'glass') mesh.material = new THREE.MeshPhysicalMaterial({color: accent, metalness: .7, roughness: .12, transmission: .5, transparent: true, opacity: .68}); } });
    return clone;
  }, [scene, material, accent]);
  return <primitive object={object}/>;
};

const Fallback: React.FC<{shape: FallbackShape; accent: string; frame: number}> = ({shape, accent, frame}) => {
  const spin = frame * .015;
  if (shape === 'ring') return <group rotation={[.35, spin, 0]}><mesh><torusGeometry args={[1.55,.24,24,96]}/><meshStandardMaterial color={accent} metalness={.8} roughness={.2}/></mesh><mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[.9,.1,16,72]}/><meshStandardMaterial color="#ffffff" metalness={.6}/></mesh></group>;
  if (shape === 'cube' || shape === 'chip') return <group rotation={[spin*.55,spin,0]}><mesh><boxGeometry args={shape==='chip'?[2.7,.45,2.0]:[2.5,2.5,2.5]}/><meshStandardMaterial color={accent} metalness={.72} roughness={.24}/></mesh>{shape==='chip'&&Array.from({length:10},(_,i)=><mesh key={i} position={[((i%5)-2)*.58,-.45,Math.floor(i/5)*1.8-.9]}><boxGeometry args={[.14,.5,.5]}/><meshStandardMaterial color="#ffffff"/></mesh>)}</group>;
  if (shape === 'nodes') return <group rotation={[0,spin*.25,0]}>{Array.from({length:16},(_,i)=>{const a=i*Math.PI*2/16;return <mesh key={i} position={[Math.cos(a)*(1.2+(i%3)*.3),Math.sin(a*2)*.6,Math.sin(a)*(1.2+(i%3)*.3)]}><sphereGeometry args={[.13+(i%4)*.025,16,16]}/><meshStandardMaterial color={i%3===0?accent:'#ffffff'} emissive={i%3===0?accent:'#000000'} emissiveIntensity={.3}/></mesh>;})}</group>;
  return <mesh rotation={[spin*.3,spin,0]}><icosahedronGeometry args={[1.75,3]}/><meshStandardMaterial color={accent} metalness={.65} roughness={.22} emissive={accent} emissiveIntensity={.1}/></mesh>;
};

/** Shared native 3D frame. It is safe when external geometry is absent: fallback
 * geometry remains visible and the render is never blocked beyond loader failure. */
export const Universal3DViewport: React.FC<{assetUrl?: string; cameraPreset?: CameraPreset; materialMode?: MaterialMode; fallbackShape?: FallbackShape; accent: string; background?: string; style?: React.CSSProperties}> = ({assetUrl, cameraPreset='orbit', materialMode='original', fallbackShape='orb', accent, background='#000000', style}) => {
  const frame = useCurrentFrame(); const {width, height, durationInFrames} = useVideoConfig(); const scene = useAssetScene(assetUrl); const progress = Math.max(0, Math.min(1, frame / Math.max(1, durationInFrames - 1)));
  return <ThreeCanvas width={width} height={height} camera={{fov:42,position:[0,1.1,5.5]}} gl={{antialias:true,alpha:true}} style={{position:'absolute',inset:0,width:'100%',height:'100%',...style}}><color attach="background" args={[background]}/><ambientLight intensity={.45}/><directionalLight position={[5,7,5]} intensity={1.5}/><directionalLight position={[-5,2,-4]} intensity={.9} color={accent}/><pointLight position={[0,-3,4]} intensity={.45} color="#ffffff"/><CameraRig preset={cameraPreset} progress={progress}/>{scene?<AssetMesh scene={scene} material={materialMode} accent={accent}/>:<Fallback shape={fallbackShape} accent={accent} frame={frame}/>}<gridHelper args={[16,16,accent,'#20263A']} position={[0,-2,0]}/></ThreeCanvas>;
};
