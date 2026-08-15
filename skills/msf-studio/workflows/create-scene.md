# Create scene workflow

1. State the visual job in one sentence and list input data, output hierarchy, target formats and audio roles.
2. Create a `draft` `SceneManifest` and fixture before writing TSX.
3. Add the component in a dedicated preset pack. Use safe-area helpers, style context and duration-relative animation.
4. Add only necessary Zod fields. Add matching Python `Scene` fields and camelCase mapping when the graph emits those props.
5. Add registry entry with honest `fields`, `dataDriven` and summary. Add realistic demo props.
6. Run TypeScript check, schema/preview-props validation and a visual preview/still check.
7. Create an AssetChangeSet with screenshots/clip, tests and migration notes.
8. Keep the result draft until release approval.

Do not source remote media or unlicensed audio. Do not duplicate a scene under a different name if a manifest-compatible existing scene solves the task.
