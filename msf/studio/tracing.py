"""Operational tracing for Studio runs.

This module records *observable work* (nodes, tool invocations, timings and
errors).  It must never accept or persist chain-of-thought, hidden model
messages, tokens, credentials, or raw user files.  The dashboard uses these
spans to explain where a job stopped without pretending to expose private model
reasoning.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Iterator, Optional

from .contracts import TraceSpan, new_id, utc_now


SAFE_ATTRIBUTE_KEYS = {
    "node",
    "tool",
    "model",
    "scene_count",
    "artifact_kind",
    "attempt",
    "duration_ms",
    "status_code",
    "provider",
}


def redact_attributes(attributes: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Keep a small operational allowlist; never store free-form prompt/thought data."""
    if not attributes:
        return {}
    return {key: value for key, value in attributes.items() if key in SAFE_ATTRIBUTE_KEYS}


class TraceStore:
    """Append-only JSONL trace span store, colocated with a Studio run."""

    def __init__(self, run_dir: Path, run_id: str, trace_id: Optional[str] = None) -> None:
        self.run_dir = Path(run_dir)
        self.run_id = run_id
        self.trace_id = trace_id or new_id("trace")
        self.path = self.run_dir / "trace.jsonl"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _append(self, span: TraceSpan) -> TraceSpan:
        with self._lock:
            with self.path.open("a", encoding="utf-8") as destination:
                destination.write(span.model_dump_json() + "\n")
        return span

    def start(self, name: str, *, parent_span_id: Optional[str] = None, attributes: Optional[dict[str, Any]] = None) -> TraceSpan:
        return self._append(
            TraceSpan(
                trace_id=self.trace_id,
                span_id=new_id("span"),
                parent_span_id=parent_span_id,
                run_id=self.run_id,
                name=name,
                attributes=redact_attributes(attributes),
            )
        )

    def finish(self, span: TraceSpan, *, error: Optional[str] = None, attributes: Optional[dict[str, Any]] = None) -> TraceSpan:
        finished = span.model_copy(
            update={
                "status": "error" if error else "ok",
                "ended_at": utc_now(),
                "error": error,
                "attributes": {**span.attributes, **redact_attributes(attributes)},
            }
        )
        return self._append(finished)

    @contextmanager
    def span(self, name: str, *, parent_span_id: Optional[str] = None, attributes: Optional[dict[str, Any]] = None) -> Iterator[TraceSpan]:
        started = self.start(name, parent_span_id=parent_span_id, attributes=attributes)
        try:
            yield started
        except Exception as exc:
            self.finish(started, error=f"{type(exc).__name__}: {exc}")
            raise
        else:
            self.finish(started)

    def read(self, limit: int = 500) -> list[TraceSpan]:
        if limit < 1 or not self.path.exists():
            return []
        spans: list[TraceSpan] = []
        with self.path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                try:
                    spans.append(TraceSpan.model_validate_json(line))
                except ValueError:
                    continue
        return spans[-limit:]
