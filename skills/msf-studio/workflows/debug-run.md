# Debug run workflow

1. Fetch run snapshot, validation result, events, trace spans and artifacts.
2. Find the earliest blocking condition: an ERROR validation diagnostic, failed node/span or missing artifact.
3. Classify the failure: catalog/schema, data shape, dependency/environment, research/provider, TTS, audio, Remotion/ffmpeg or QA.
4. Apply the narrowest safe repair. Revalidate before retrying.
5. Retry from the first safe checkpoint rather than launching the whole costly run when possible.
6. Report node, error class, repaired change, remaining risk and artifact status.

Do not infer hidden model thoughts from telemetry. Do not expose raw prompts, secrets or private media through debug output.
