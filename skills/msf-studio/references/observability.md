# Observability and debug

Use `RunEvent` for ordered lifecycle changes and `TraceSpan` for operational timing. A trace is not a reasoning log.

Display or persist only:

- run ID, status, node name, tool/provider name, duration, retry attempt;
- validation diagnostics and their scene index;
- artifact ID, kind and relative URI;
- bounded error type/message and redacted technical stack trace.

Never persist/display model hidden reasoning, prompt internals, authentication tokens, full reference-audio content, raw private uploads or absolute filesystem paths.

Debug sequence:

1. Read the first ERROR validation diagnostic; correct its field/schema mismatch.
2. Otherwise locate first `node.failed`/failed span.
3. Inspect artifacts created before the failure and the minimal error boundary.
4. Apply the narrowest repair, revalidate and retry from a safe checkpoint.
5. Do not restart a costly render if the validation or asset error remains unresolved.
