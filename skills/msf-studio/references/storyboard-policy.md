# Storyboard policy

Create scene blocks from manifests, not prose. Every block must have a preset, only declared props, a readable duration and an audio policy.

1. Keep one visual claim per scene. Split dense text before reducing font size.
2. For a data-driven preset, provide all manifest-required data. Do not rely on component fallback data in production.
3. Respect `readability.duration_short`; increase duration or reduce text.
4. Respect platform safe area. Never position important text at screen edges.
5. Choose at most one high-salience effect per scene. Use `FocusPulse` for non-moving emphasis on dense data/comparison scenes.
6. Resolve audio by semantic role. Use a quiet bed under voice, keep SFX sparse, and do not manually stack conflicting scene and root music.
7. Validate after every meaningful draft change and preview before a final render.

A valid storyboard is a precondition for render, not evidence that the rendered result is visually approved.
