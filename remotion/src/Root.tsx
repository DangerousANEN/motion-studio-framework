import React from 'react';
import { Composition, getInputProps } from 'remotion';
import { MainComposition } from './compositions/Main';
import { getTransitionPlan } from './lib/transitions';
import { VideoSpec, VideoSpecSchema } from './VideoSpec.schema';

import { GridGridFloor } from './presets/GridGridFloor';
import { HeroKinetic } from './presets/HeroKinetic';
import { StatCounter } from './presets/StatCounter';
import { SwipePanels } from './presets/SwipePanels';
import { TypewriterSub } from './presets/TypewriterSub';
import { ProbeBlocking, ProbeBoxOnly, ProbeGated, ProbeSuspense } from './audit/GlbProbe';
import { VisualEffectProbe, VisualEffectProbeBare } from './audit/VisualEffectProbe';
import { EffectProbe, EffectProbeBare } from './audit/EffectProbe';
import {
  OverlayTestComp,
  BareTestComp,
  TransitionTestComp,
  FromSceneOnly,
  ToSceneOnly,
} from './audit/EffectProbeComps';

const ErrorScene: React.FC<{ message: string }> = ({ message }) => (
  <div
    style={{
      flex: 1,
      backgroundColor: '#FF0033',
      color: '#FFFFFF',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
      textAlign: 'center',
      fontFamily: 'monospace',
    }}
  >
    <h1 style={{ fontSize: '72px', margin: '0 0 20px 0', fontWeight: 900 }}>RENDER ERROR</h1>
    <p style={{ fontSize: '36px', margin: 0, fontWeight: 700 }}>{message}</p>
  </div>
);

export const RemotionRoot: React.FC = () => {
  const inputProps = getInputProps() as Partial<VideoSpec>;
  const parsed = VideoSpecSchema.safeParse(inputProps);

  if (!parsed.success) {
    const errorMsg = `ERROR: no scenes supplied or invalid spec: ${parsed.error.message}`;
    return (
      <Composition
        id="Main"
        component={() => <ErrorScene message={errorMsg} />}
        durationInFrames={120}
        fps={60}
        width={1080}
        height={1920}
      />
    );
  }

  const spec = parsed.data;
  // TransitionSeries OVERLAPS scenes, so the timeline is shorter than the sum of
  // scene durations by the total overlap. Summing durations naively left the
  // composition longer than the rendered content and desynced the pre-rendered
  // audio track. computeTransitionPlan() is the single source of truth and is
  // mirrored by compute_total_frames() in msf/spec.py
  // (tests/test_transition_parity.py asserts the two agree).
  const totalDuration = getTransitionPlan(spec.scenes).totalDurationInFrames;

  return (
    <>
      {/* Main Full Video Composition (Series of Scenes) */}
      <Composition
        id="Main"
        component={MainComposition}
        durationInFrames={totalDuration}
        fps={spec.fps}
        width={spec.width}
        height={spec.height}
        defaultProps={spec}
      />

      {/* Standalone Preset Compositions for individual testing */}
      <Composition
        id="HeroKinetic"
        component={HeroKinetic}
        durationInFrames={90}
        fps={spec.fps}
        width={spec.width}
        height={spec.height}
        defaultProps={{
          id: 'test-hero',
          durationInFrames: 90,
          preset: 'HeroKinetic',
          title: 'HERO KINETIC',
          subtitle: 'PRESET TEST',
        }}
      />

      <Composition
        id="StatCounter"
        component={StatCounter}
        durationInFrames={90}
        fps={spec.fps}
        width={spec.width}
        height={spec.height}
        defaultProps={{
          id: 'test-stat',
          durationInFrames: 90,
          preset: 'StatCounter',
          statValue: 100,
          statSuffix: '%',
          statLabel: 'TEST METRIC',
        }}
      />

      <Composition
        id="GridGridFloor"
        component={GridGridFloor}
        durationInFrames={90}
        fps={spec.fps}
        width={spec.width}
        height={spec.height}
        defaultProps={{
          id: 'test-grid',
          durationInFrames: 90,
          preset: 'GridGridFloor',
          title: 'GRID FLOOR',
          subtitle: 'TEST SCENE',
        }}
      />

      <Composition
        id="SwipePanels"
        component={SwipePanels}
        durationInFrames={90}
        fps={spec.fps}
        width={spec.width}
        height={spec.height}
        defaultProps={{
          id: 'test-swipe',
          durationInFrames: 90,
          preset: 'SwipePanels',
          title: 'SWIPE PANELS',
        }}
      />

      <Composition
        id="TypewriterSub"
        component={TypewriterSub}
        durationInFrames={90}
        fps={spec.fps}
        width={spec.width}
        height={spec.height}
        defaultProps={{
          id: 'test-typewriter',
          durationInFrames: 90,
          preset: 'TypewriterSub',
          text: 'Typewriter preset test string.',
        }}
      />
      <Composition
        id="ProbeBoxOnly"
        component={ProbeBoxOnly}
        durationInFrames={30}
        fps={60}
        width={1080}
        height={1920}
      />
      <Composition
        id="ProbeSuspense"
        component={ProbeSuspense}
        durationInFrames={30}
        fps={60}
        width={1080}
        height={1920}
      />
      <Composition
        id="ProbeBlocking"
        component={ProbeBlocking}
        durationInFrames={30}
        fps={60}
        width={1080}
        height={1920}
      />
      <Composition
        id="ProbeGated"
        component={ProbeGated}
        durationInFrames={30}
        fps={60}
        width={1080}
        height={1920}
      />

      {/* ---- Effect / Transition probe compositions ---- */}
      <Composition
        id="OverlayTest"
        component={OverlayTestComp}
        durationInFrames={90}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{ name: 'ParticlesDust', intensity: 1, seed: 42 }}
      />
      <Composition
        id="BareTest"
        component={BareTestComp}
        durationInFrames={90}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{}}
      />
      <Composition
        id="TransitionTest"
        component={TransitionTestComp}
        durationInFrames={90}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{ name: 'CrossFade', progress: 0.5, seed: 42 }}
      />
      <Composition
        id="FromSceneOnly"
        component={FromSceneOnly}
        durationInFrames={90}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{}}
      />
      <Composition
        id="ToSceneOnly"
        component={ToSceneOnly}
        durationInFrames={90}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{}}
      />

      {/* ---- Visual Effect probe compositions (camera / grade / distortion) ---- */}
      <Composition
        id="VisualEffectProbe"
        component={VisualEffectProbe}
        durationInFrames={90}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{ effect: 'Vignette', intensity: 1, seed: 42 }}
      />
      <Composition
        id="VisualEffectProbeBare"
        component={VisualEffectProbeBare}
        durationInFrames={90}
        fps={60}
        width={1080}
        height={1920}
      />
    </>
  );
};
