# Add audio pack workflow

1. Classify the asset as procedural music, procedural SFX or external licensed media.
2. Create a manifest with source/license, mood/semantic tags, loudness, loop behavior and maximum gain.
3. For procedural audio, register a deterministic function and expose it through the existing registry.
4. Map each scene event to a semantic role such as `intro_hit`, `data_tick`, `message`, `transition` or `success_chime`.
5. Run registration, duration/loudness/loop checks and recipe smoke test.
6. Publish only an immutable pack version after review.

Do not attach arbitrary SFX to every visual change. Preserve speech intelligibility and use sparse cue density.
