# MSF Video Pipeline Readiness

## Executive assessment

MSF Studio is ready as a **controlled local video production workspace**, but it is not yet a fully unattended production conveyor. The renderer, run lifecycle, Resources, Element Builder, audio normalization, voice workflow, overlay category, style catalog and pipeline graph are implemented. The remaining dependency for a complete unattended scenario-to-video run is a healthy configured research LLM runtime and a final end-to-end render verification on the target machine.

## What was tested

| Area | Result |
|---|---|
| Research-to-script contracts | Passed deterministic workflow suite. Evidence claims, source linkage, Russian copy policy, comparison modes and storyboard validation are covered. |
| Studio API | Passed targeted panel/API tests. Existing research-to-script endpoint remains contract-compatible. |
| Settings persistence | Passed real GET/PATCH/GET cycle for archetype, provider, query/source limits, duration, FPS, audio levels, subtitles and comparison controls. |
| Settings UI | Verified in browser. New controls load, remain in the local dashboard and do not overlap at the tested viewport. |
| Scenario Lab UI | Verified topic input, controls, request state and loading state. Added a 90-second client timeout so long research calls no longer leave the panel in an indefinite state. |
| Element Builder regressions | Passed existing Element Builder contract tests together with resources and panel tests. |
| Syntax | Python compilation and JavaScript syntax check passed. |

## Scenario test limitation

A real external research-to-script call was attempted for the topic **«Как экономнее пользоваться современными LLM без дорогой подписки»**. Public source collection started successfully, but the configured OpenAI-compatible proxy returned an explicit `Insufficient credits` response before the structured evidence-claims step. The adapter now surfaces proxy-level errors directly and avoids reporting them as an ambiguous empty JSON response. The deterministic pipeline tests pass; a real generated scenario requires the LLM runtime to be available.

## New operator controls

The Settings page now includes defaults for voice, style, agent freedom, research enablement, music, SFX, subtitles, content archetype, audience, CTA handle and asset, search provider, query/source limits, community proof, comparison mode and models, visual evidence mode, observed-comparison requirement, target duration, FPS, music level and SFX level.

A **Scenario Lab** was added below Settings. It runs the existing `research-to-script` API separately from rendering and displays source/claim counts, title, hook, takeaway, CTA, storyboard scene count and warnings. This creates a safe editorial checkpoint before a storyboard is transferred into a render draft.

## Remaining production work

The next recommended step is to configure a stable research LLM provider, run the Scenario Lab successfully, save the returned storyboard, prepare a draft, approve it explicitly, render the complete MP4 and inspect the final audio/video QA artifacts. For unattended operation, Scenario Lab should later be promoted to a persisted background job with resumable milestones rather than a synchronous request.
