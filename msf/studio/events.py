"""Append-only structured run events for MSF Studio v2.

JSONL is intentionally used for the local-first release: it is inspectable,
portable and works without a database.  The EventStore interface can later be
backed by PostgreSQL without changing application contracts.
"""
from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any, Iterable, Optional

from .contracts import EventLevel, RunEvent


class EventStore:
    """File-backed event store scoped to one Studio run directory."""

    def __init__(self, run_dir: Path, run_id: str) -> None:
        self.run_dir = Path(run_dir)
        self.run_id = run_id
        self.path = self.run_dir / "events.jsonl"
        self._lock = Lock()
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def _next_sequence(self) -> int:
        if not self.path.exists():
            return 1
        last = 0
        try:
            with self.path.open("r", encoding="utf-8") as source:
                for line in source:
                    if not line.strip():
                        continue
                    try:
                        last = max(last, int(json.loads(line).get("sequence", 0)))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
        except OSError:
            return 1
        return last + 1

    def append(
        self,
        event_type: str,
        *,
        node: Optional[str] = None,
        level: EventLevel = EventLevel.INFO,
        message: str = "",
        payload: Optional[dict[str, Any]] = None,
    ) -> RunEvent:
        """Persist and return a monotonically ordered event."""
        with self._lock:
            event = RunEvent(
                run_id=self.run_id,
                sequence=self._next_sequence(),
                type=event_type,
                node=node,
                level=level,
                message=message,
                payload=payload or {},
            )
            with self.path.open("a", encoding="utf-8") as destination:
                destination.write(event.model_dump_json() + "\n")
            return event

    def read_after(self, sequence: int = 0, limit: int = 500) -> list[RunEvent]:
        """Return ordered events after a sequence cursor with a safe limit."""
        if limit < 1:
            return []
        events: list[RunEvent] = []
        if not self.path.exists():
            return events
        with self.path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                try:
                    event = RunEvent.model_validate_json(line)
                except ValueError:
                    continue
                if event.sequence > sequence:
                    events.append(event)
                if len(events) >= limit:
                    break
        return events

    def __iter__(self) -> Iterable[RunEvent]:
        return iter(self.read_after())
