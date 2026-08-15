# Modify scene workflow

1. Fetch the current manifest and identify the exact backwards-compatible or breaking change.
2. For visual-only compatible changes, create a draft patch and preserve the public prop schema.
3. For changed/removed props, create `@next`, write migration instructions and keep the old version renderable.
4. Update fixtures for minimum, typical, dense and malformed inputs.
5. Run the complete scene quality gate and compare preview frames against the prior behavior where relevant.
6. Submit the draft change set for release review; never silently overwrite a stable version.
