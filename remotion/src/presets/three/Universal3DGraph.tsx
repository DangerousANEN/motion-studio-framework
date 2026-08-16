import React from 'react';
import {ThreeCanvas} from '@remotion/three';
import {useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import * as THREE from 'three';
import {AssetMesh, useAssetScene} from './Universal3D';
import {BaseSceneProps} from '../../VideoSpec.schema';

type Vec3 = [number, number, number];
type Primitive = 'box' | 'sphere' | 'torus' | 'cylinder' | 'cone' | 'plane' | 'octahedron' | 'icosahedron' | 'line' | 'asset' | 'group';
type Ease = 'linear' | 'easeInOut' | 'easeOut';
export type Universal3DNode = {
  id: string;
  type: Primitive;
  position?: Vec3;
  rotation?: Vec3;
  scale?: Vec3;
  color?: string;
  emissive?: string;
  opacity?: number;
  metalness?: number;
  roughness?: number;
  wireframe?: boolean;
  args?: number[];
  assetUrl?: string;
  children?: Universal3DNode[];
  motion?: {
    from?: Partial<Pick<Universal3DNode, 'position' | 'rotation' | 'scale'>>;
    to?: Partial<Pick<Universal3DNode, 'position' | 'rotation' | 'scale'>>;
    start?: number;
    end?: number;
    ease?: Ease;
    loop?: 'none' | 'pingpong' | 'repeat';
  };
};
export type Universal3DGraphSpec = {
  version: 1;
  background?: string;
  camera?: {preset?: 'orbit' | 'arc' | 'dolly' | 'figureEight'; position?: Vec3; lookAt?: Vec3; fov?: number};
  lights?: Array<{type: 'ambient' | 'directional' | 'point' | 'spot'; position?: Vec3; color?: string; intensity?: number}>;
  grid?: {enabled?: boolean; size?: number; divisions?: number; color?: string; secondaryColor?: string};
  nodes: Universal3DNode[];
};

const v = (input: unknown, fallback: Vec3 = [0, 0, 0]): Vec3 => Array.isArray(input) && input.length === 3 ? [Number(input[0]) || 0, Number(input[1]) || 0, Number(input[2]) || 0] : fallback;
const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(max, n));
const ease = (t: number, mode: Ease = 'easeInOut') => mode === 'linear' ? t : mode === 'easeOut' ? 1 - Math.pow(1 - t, 3) : t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const lerpVec = (a: Vec3, b: Vec3, t: number): Vec3 => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];

function motionValue(node: Universal3DNode, frame: number, duration: number, key: 'position' | 'rotation' | 'scale', fallback: Vec3): Vec3 {
  const m = node.motion;
  if (!m || !m.from?.[key] || !m.to?.[key]) return v(node[key], fallback);
  const start = Number(m.start ?? 0); const end = Math.max(start + 1, Number(m.end ?? duration));
  let t = clamp((frame - start) / (end - start), 0, 1);
  if (m.loop === 'repeat') t = ((frame - start) / (end - start)) % 1;
  if (m.loop === 'pingpong') { const raw = ((frame - start) / (end - start)) % 2; t = raw > 1 ? 2 - raw : raw; }
  return lerpVec(v(m.from[key], fallback), v(m.to[key], fallback), ease(t, m.ease));
}

const Material: React.FC<{node: Universal3DNode}> = ({node}) => <meshStandardMaterial color={node.color || '#7c8cff'} emissive={node.emissive || '#000000'} emissiveIntensity={node.emissive ? .35 : 0} metalness={clamp(Number(node.metalness ?? .2), 0, 1)} roughness={clamp(Number(node.roughness ?? .45), .04, 1)} transparent={Number(node.opacity ?? 1) < 1} opacity={clamp(Number(node.opacity ?? 1), 0, 1)} wireframe={Boolean(node.wireframe)} />;

const PrimitiveMesh: React.FC<{node: Universal3DNode; frame: number; duration: number}> = ({node, frame, duration}) => {
  const position = motionValue(node, frame, duration, 'position', [0, 0, 0]);
  const rotation = motionValue(node, frame, duration, 'rotation', [0, 0, 0]);
  const scale = motionValue(node, frame, duration, 'scale', [1, 1, 1]);
  const common = {position, rotation, scale};
  if (node.type === 'group') return <group {...common}>{(node.children || []).map((child) => <PrimitiveMesh key={child.id} node={child} frame={frame} duration={duration} />)}</group>;
  if (node.type === 'asset' && node.assetUrl) return <AssetNode node={node} common={common} />;
  const args = (node.args || []).map(Number);
  let geometry: React.ReactNode;
  if (node.type === 'sphere') geometry = <sphereGeometry args={[args[0] || 1, args[1] || 32, args[2] || 20]} />;
  else if (node.type === 'torus') geometry = <torusGeometry args={[args[0] || 1, args[1] || .2, args[2] || 20, args[3] || 64]} />;
  else if (node.type === 'cylinder') geometry = <cylinderGeometry args={[args[0] || .7, args[1] || .7, args[2] || 1.4, args[3] || 32]} />;
  else if (node.type === 'cone') geometry = <coneGeometry args={[args[0] || .8, args[1] || 1.6, args[2] || 32]} />;
  else if (node.type === 'plane') geometry = <planeGeometry args={[args[0] || 2, args[1] || 2]} />;
  else if (node.type === 'octahedron') geometry = <octahedronGeometry args={[args[0] || 1, args[1] || 0]} />;
  else if (node.type === 'icosahedron') geometry = <icosahedronGeometry args={[args[0] || 1, args[1] || 1]} />;
  else if (node.type === 'line') geometry = <boxGeometry args={[args[0] || 3, args[1] || .025, args[2] || .025]} />;
  else geometry = <boxGeometry args={[args[0] || 1, args[1] || 1, args[2] || 1]} />;
  return <mesh {...common}><>{geometry}</><Material node={node} /></mesh>;
};

const AssetNode: React.FC<{node: Universal3DNode; common: {position: Vec3; rotation: Vec3; scale: Vec3}}> = ({node, common}) => { const scene = useAssetScene(node.assetUrl); return <group {...common}>{scene ? <AssetMesh scene={scene} material={node.wireframe ? 'wireframe' : 'original'} accent={node.color || '#7c8cff'} /> : <mesh><icosahedronGeometry args={[1.2, 2]} /><Material node={{...node, color: node.color || '#7c8cff'}} /></mesh>}</group>; };

const GraphCanvas: React.FC<{spec: Universal3DGraphSpec; width: number; height: number; frame: number; duration: number}> = ({spec, width, height, frame, duration}) => {
  const camera = spec.camera || {}; const position = camera.position || [0, 1.4, 7] as Vec3;
  return <ThreeCanvas width={width} height={height} camera={{fov: camera.fov || 42, position}} gl={{antialias: true, alpha: true}}><color attach="background" args={[spec.background || '#0b1020']} />{(spec.lights || [{type: 'ambient', intensity: .5}, {type: 'directional', position: [4, 6, 5], intensity: 1.4, color: '#ffffff'}]).map((light, i) => { const p = light.position || [0, 4, 4] as Vec3; const color = light.color || '#ffffff'; if (light.type === 'directional') return <directionalLight key={i} position={p} color={color} intensity={light.intensity ?? 1} />; if (light.type === 'point') return <pointLight key={i} position={p} color={color} intensity={light.intensity ?? 1} />; if (light.type === 'spot') return <spotLight key={i} position={p} color={color} intensity={light.intensity ?? 1} />; return <ambientLight key={i} color={color} intensity={light.intensity ?? .5} />; })}<group>{(spec.nodes || []).slice(0, 128).map((node) => <PrimitiveMesh key={node.id} node={node} frame={frame} duration={duration} />)}</group>{spec.grid?.enabled !== false ? <gridHelper args={[spec.grid?.size || 16, spec.grid?.divisions || 16, spec.grid?.color || '#5665ff', spec.grid?.secondaryColor || '#20263a']} position={[0, -2, 0]} /> : null}</ThreeCanvas>;
};

export const Universal3DGraph: React.FC<BaseSceneProps> = (props) => {
  const p = props as BaseSceneProps & {graph?: Universal3DGraphSpec; title?: string}; const spec: Universal3DGraphSpec = p.graph && typeof p.graph === 'object' ? p.graph : {version: 1, nodes: []};
  const {width, height, durationInFrames} = useVideoConfig(); const frame = useCurrentFrame();
  return <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: spec.background || '#0b1020'}}><GraphCanvas spec={spec} width={width} height={height} frame={frame} duration={durationInFrames} /></div>;
};

export const UNIVERSAL_3D_PRIMITIVES: Primitive[] = ['box', 'sphere', 'torus', 'cylinder', 'cone', 'plane', 'octahedron', 'icosahedron', 'line', 'asset', 'group'];
