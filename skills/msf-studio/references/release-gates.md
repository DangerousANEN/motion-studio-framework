# Release quality gates

A new or modified asset remains `draft` until every relevant gate passes.

| Asset | Required gates |
|---|---|
| Scene | Manifest, Zod fields, registry entry, Python wire contract where applicable, demo props, TypeScript check, schema validation, preview/still review. |
| Effect | Registry entry, intensity `0` no-op, deterministic behavior or seeded randomness, TypeScript check, visual preview. |
| Music/SFX | Registration, deterministic render, source/license metadata, loudness/loop audit, recipe smoke test. |
| Voice | Consent, source owner, clean copy, corrected transcript, audition, quality report, human approval. |

For incompatible scene props, publish `scene@next` with migration notes. Preserve old versions for historical VideoSpec reproducibility. Never edit a stable scene in place to change its contract.
