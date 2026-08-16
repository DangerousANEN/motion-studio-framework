import {AssetOrbit3D, DataCube, DeviceConveyor3D, ExplodedProductView, GlobeSignalMap, IsometricWorkflowCity, LogoSculpture3D, MilestoneCorridor3D, ParticleDataField, WorkflowFlyThrough3D} from '../presets/expansion_three';
import {PresetRegistry} from './types';
import {Universal3DGraph} from '../presets/three/Universal3DGraph';

export const EXPANSION_THREE_V24_PRESETS: PresetRegistry = {
  Universal3DGraph: {component: Universal3DGraph, category: 'three', summary: 'Declarative 3D scene graph with primitives, groups, assets, camera, lights and timeline motion.', fields: ['graph', 'title'], dataDriven: true, three: true},
  AssetOrbit3D: {component: AssetOrbit3D, category: 'three', summary: 'Slow licensed-asset orbit with deterministic procedural fallback.', fields: ['assetUrl', 'assetLicense', 'assetAttribution', 'cameraPreset', 'materialMode', 'fallbackShape', 'title'], dataDriven: true, three: true},
  ExplodedProductView: {component: ExplodedProductView, category: 'three', summary: 'Asset breakdown into supplied semantic layers.', fields: ['assetUrl', 'assetLicense', 'parts', 'explodeDistance', 'cameraPreset', 'title'], dataDriven: true, three: true},
  WorkflowFlyThrough3D: {component: WorkflowFlyThrough3D, category: 'three', summary: '3D camera flight through labeled workflow stations.', fields: ['workflowNodes', 'assetUrl', 'cameraPreset', 'title'], dataDriven: true, three: true},
  DataCube: {component: DataCube, category: 'three', summary: 'Three-axis data cube with highlighted dimension.', fields: ['x', 'y', 'z', 'labels', 'highlight', 'title'], dataDriven: true, three: true},
  LogoSculpture3D: {component: LogoSculpture3D, category: 'three', summary: 'Three-dimensional logo/material transition scene.', fields: ['svgUrl', 'assetUrl', 'materialMode', 'cameraPreset', 'tagline', 'title'], dataDriven: true, three: true},
  DeviceConveyor3D: {component: DeviceConveyor3D, category: 'three', summary: 'Device fleet moving around a 3D core.', fields: ['screens', 'devices', 'cameraPreset', 'title'], dataDriven: true, three: true},
  ParticleDataField: {component: ParticleDataField, category: 'three', summary: 'Deterministic particle data grouping and focus field.', fields: ['groups', 'values', 'focusGroup', 'caption', 'title'], dataDriven: true, three: true},
  IsometricWorkflowCity: {component: IsometricWorkflowCity, category: 'three', summary: 'Isometric workflow environment with active path.', fields: ['zones', 'activePath', 'labels', 'title'], dataDriven: true, three: true},
  GlobeSignalMap: {component: GlobeSignalMap, category: 'three', summary: 'Supplied location and route signal map, never implicit live data.', fields: ['locations', 'routes', 'metric', 'source', 'title'], dataDriven: true, three: true},
  MilestoneCorridor3D: {component: MilestoneCorridor3D, category: 'three', summary: 'Depth corridor of sourced dated milestones.', fields: ['milestones', 'cameraPreset', 'source', 'title'], dataDriven: true, three: true},
};
