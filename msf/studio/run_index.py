"""SQLite index for the local Studio run archive.

A run directory remains the worker's source of truth because it keeps each run
portable and inspectable. SQLite stores a small searchable projection so the UI
can list years of runs without recursively parsing every events file on each page
load. It contains no prompts, hidden reasoning, credentials or absolute paths.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

_SCHEMA = """
CREATE TABLE IF NOT EXISTS studio_runs (
  run_id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT,
  started_at TEXT,
  completed_at TEXT,
  topic TEXT NOT NULL,
  preset TEXT NOT NULL,
  style TEXT,
  voice TEXT,
  research INTEGER NOT NULL,
  music INTEGER NOT NULL,
  sfx INTEGER NOT NULL,
  agent_level INTEGER NOT NULL,
  artifacts_count INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_studio_runs_created ON studio_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_studio_runs_status_created ON studio_runs(status, created_at DESC);
"""


class RunIndex:
    """Short-lived SQLite connections keep panel and worker process interactions safe."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.path = self.root / "run_index.sqlite3"
        self.root.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def upsert(self, snapshot: Any, request: Any) -> None:
        """Store only the safe list-view projection of a canonical run."""
        row = {
            "run_id": snapshot.run_id,
            "request_id": snapshot.request_id,
            "project_id": snapshot.project_id,
            "status": snapshot.status.value if hasattr(snapshot.status, "value") else str(snapshot.status),
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
            "started_at": snapshot.started_at.isoformat() if snapshot.started_at else None,
            "completed_at": snapshot.completed_at.isoformat() if snapshot.completed_at else None,
            "topic": request.topic,
            "preset": request.preset,
            "style": request.style,
            "voice": request.voice,
            "research": int(bool(request.research)),
            "music": int(bool(request.music)),
            "sfx": int(bool(request.sfx)),
            "agent_level": request.agent_level,
            "artifacts_count": len(snapshot.artifacts),
            "updated_at": (snapshot.completed_at or snapshot.started_at or snapshot.created_at).isoformat(),
        }
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO studio_runs (
                  run_id,request_id,project_id,status,created_at,started_at,completed_at,
                  topic,preset,style,voice,research,music,sfx,agent_level,artifacts_count,updated_at
                ) VALUES (
                  :run_id,:request_id,:project_id,:status,:created_at,:started_at,:completed_at,
                  :topic,:preset,:style,:voice,:research,:music,:sfx,:agent_level,:artifacts_count,:updated_at
                ) ON CONFLICT(run_id) DO UPDATE SET
                  request_id=excluded.request_id, project_id=excluded.project_id, status=excluded.status,
                  created_at=excluded.created_at, started_at=excluded.started_at, completed_at=excluded.completed_at,
                  topic=excluded.topic, preset=excluded.preset, style=excluded.style, voice=excluded.voice,
                  research=excluded.research, music=excluded.music, sfx=excluded.sfx,
                  agent_level=excluded.agent_level, artifacts_count=excluded.artifacts_count, updated_at=excluded.updated_at""",
                row,
            )

    def list(self, *, limit: int = 80, status: str | None = None) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        query = "SELECT * FROM studio_runs"
        params: list[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def run_ids(self) -> set[str]:
        with self._connect() as conn:
            return {str(row[0]) for row in conn.execute("SELECT run_id FROM studio_runs")}


__all__ = ["RunIndex"]
