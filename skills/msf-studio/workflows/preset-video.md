# Preset video workflow

1. Normalize the brief into topic, audience, language, platform, duration, factuality and brand constraints.
2. Query the catalog with topic/intents. Reject draft/deprecated results.
3. Fetch manifests for candidates. Select only schemas that match available data.
4. Build a `StoryboardDraft`; use `AudioPolicy(mode="suggest")` unless the user names approved assets.
5. Validate. Fix errors before preview; warnings need a documented decision.
6. Create preview and inspect readable copy, safe area, title/data alignment, effect restraint and audio cue relevance.
7. Request final-render approval at the policy boundary. Do not bypass it.
8. Return run status, artifacts, validation and user-visible QA summary.

Fallback order for missing structured data: select a text/narrative stable scene → request real data → defer the claim. Never manufacture numbers, quotations or chat messages.
