"""Canonical local-first run service for the LangGraph + Remotion pipeline."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from threading import Lock
from typing import Optional

from .contracts import (
    ArtifactRef,
    EventLevel,
    RunRequest,
    RunSnapshot,
    RunStatus,
    new_id,
    utc_now,
)
from .events import EventStore


_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_ROOT = _REPO / "output" / "studio"
_PATCHABLE_REQUEST_FIELDS = {
    "topic", "preset", "style", "style_config", "voice", "research", "music", "sfx", "agent_level",
    "media_assets", "pinned_sources",
}
_SUPPORTED_OPERATOR_NODES = {"deep_research", "script_split"}
_MAX_OPERATOR_INSTRUCTION_CHARS = 480


class RunNotFoundError(KeyError):
    """Raised when an opaque Studio run ID cannot be resolved."""


class RunStateError(RuntimeError):
    """Raised when an invalid run lifecycle transition is requested."""


class StudioRunService:
    """File-backed run service with a future database/queue compatible API.

    A v2 run owns a private directory and starts a dedicated child process.  The
    child process is deliberate: loading the TTS CUDA model or a Node renderer
    must not take down the panel/application API on OOM or renderer failure.
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root or _DEFAULT_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)
        self._processes: dict[str, subprocess.Popen[str]] = {}
        self._lock = Lock()

    def _run_dir(self, run_id: str) -> Path:
        if not run_id.startswith("run_") or any(ch not in "0123456789abcdefrun_" for ch in run_id):
            raise RunNotFoundError("invalid run id")
        return self.root / run_id

    def _snapshot_path(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "snapshot.json"

    def _request_path(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "request.json"

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        temporary.replace(path)

    def _sync_index(self, snapshot: RunSnapshot, request: RunRequest | None = None) -> None:
        """Mirror a safe run summary into SQLite; run files remain canonical."""
        from .run_index import RunIndex

        current = request
        if current is None:
            request_path = self._request_path(snapshot.run_id)
            if not request_path.is_file():
                return
            current = RunRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
        RunIndex(self.root).upsert(snapshot, current)

    def _store_snapshot(self, snapshot: RunSnapshot) -> None:
        path = self._snapshot_path(snapshot.run_id)
        self._write_json(path, snapshot.model_dump(mode="json"))
        self._sync_index(snapshot)

    def get_snapshot(self, run_id: str) -> RunSnapshot:
        path = self._snapshot_path(run_id)
        if not path.is_file():
            raise RunNotFoundError(run_id)
        return RunSnapshot.model_validate_json(path.read_text(encoding="utf-8"))

    def _update_snapshot(self, snapshot: RunSnapshot, **changes: object) -> RunSnapshot:
        updated = snapshot.model_copy(update=changes)
        self._store_snapshot(updated)
        return updated

    def get_request(self, run_id: str) -> RunRequest:
        """Return the immutable request snapshot currently attached to a local run."""
        path = self._request_path(run_id)
        if not path.is_file():
            raise RunNotFoundError(run_id)
        return RunRequest.model_validate_json(path.read_text(encoding="utf-8"))

    def patch_draft(
        self,
        run_id: str,
        *,
        request_patch: dict[str, object] | None = None,
        operator_overrides: dict[str, str] | None = None,
    ) -> tuple[RunSnapshot, RunRequest]:
        """Apply a bounded editorial patch before approval, never after worker start."""
        snapshot = self.get_snapshot(run_id)
        if snapshot.status != RunStatus.DRAFT:
            raise RunStateError("only a draft run can be edited; cancel and create a revised draft after approval")
        patch = request_patch or {}
        unknown = set(patch) - _PATCHABLE_REQUEST_FIELDS
        if unknown:
            raise ValueError(f"unsupported draft patch fields: {', '.join(sorted(unknown))}")
        current = self.get_request(run_id)
        payload = current.model_dump(mode="json")
        payload.update(patch)
        merged_overrides = dict(current.operator_overrides)
        for node, instruction in (operator_overrides or {}).items():
            if node not in _SUPPORTED_OPERATOR_NODES:
                raise ValueError(f"operator instruction is not supported for node {node!r}")
            clean = str(instruction).strip()
            if not clean:
                merged_overrides.pop(node, None)
                continue
            if len(clean) > _MAX_OPERATOR_INSTRUCTION_CHARS:
                raise ValueError(f"operator instruction for {node!r} exceeds {_MAX_OPERATOR_INSTRUCTION_CHARS} characters")
            merged_overrides[node] = clean
        payload["operator_overrides"] = merged_overrides
        updated_request = RunRequest.model_validate(payload)
        self._write_json(self._request_path(run_id), updated_request.model_dump(mode="json"))
        self._sync_index(snapshot, updated_request)
        EventStore(self._run_dir(run_id), run_id).append(
            "run.draft_updated",
            message="Operator updated draft inputs before approval",
            payload={"fields": sorted(patch), "instruction_nodes": sorted(merged_overrides)},
        )
        return snapshot, updated_request

    def create_run(self, request: RunRequest) -> RunSnapshot:
        """Create an immutable request + draft run without consuming GPU work."""
        run_id = new_id("run")
        run_dir = self._run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=False)
        snapshot = RunSnapshot(
            run_id=run_id,
            request_id=request.request_id,
            project_id=request.project_id,
            status=RunStatus.DRAFT,
        )
        self._write_json(self._request_path(run_id), request.model_dump(mode="json"))
        self._store_snapshot(snapshot)
        EventStore(run_dir, run_id).append(
            "run.created",
            message="Studio run draft created",
            payload={"request_id": request.request_id, "project_id": request.project_id},
        )
        return snapshot

    def validate(self, run_id: str, valid: bool, diagnostics_count: int = 0) -> RunSnapshot:
        snapshot = self.get_snapshot(run_id)
        if snapshot.status not in {RunStatus.DRAFT, RunStatus.VALIDATED}:
            raise RunStateError(f"cannot validate run in state {snapshot.status.value}")
        events = EventStore(self._run_dir(run_id), run_id)
        if not valid:
            events.append(
                "validation.failed",
                level=EventLevel.ERROR,
                message="Storyboard validation failed",
                payload={"diagnostics_count": diagnostics_count},
            )
            return snapshot
        updated = self._update_snapshot(snapshot, status=RunStatus.VALIDATED)
        events.append(
            "validation.completed",
            message="Storyboard validation passed",
            payload={"diagnostics_count": diagnostics_count},
        )
        return updated

    def queue(self, run_id: str) -> RunSnapshot:
        snapshot = self.get_snapshot(run_id)
        if snapshot.status != RunStatus.VALIDATED:
            raise RunStateError("only validated runs can be queued")
        updated = self._update_snapshot(snapshot, status=RunStatus.QUEUED)
        EventStore(self._run_dir(run_id), run_id).append("run.queued", message="Run queued for worker")
        return updated

    def start(self, run_id: str) -> RunSnapshot:
        """Start the canonical worker process after explicit application approval."""
        with self._lock:
            snapshot = self.get_snapshot(run_id)
            if snapshot.status != RunStatus.QUEUED:
                raise RunStateError("only queued runs can start")
            request = RunRequest.model_validate_json(self._request_path(run_id).read_text(encoding="utf-8"))
            if not request.approved:
                raise RunStateError("render requires explicit approval")
            run_dir = self._run_dir(run_id)
            updated = self._update_snapshot(snapshot, status=RunStatus.RUNNING, started_at=utc_now())
            EventStore(run_dir, run_id).append("run.started", message="Worker process started")
            process = subprocess.Popen(
                [sys.executable, "-m", "msf.studio.worker_job", str(run_dir)],
                cwd=_REPO,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            self._processes[run_id] = process
            return updated

    def cancel(self, run_id: str) -> RunSnapshot:
        with self._lock:
            snapshot = self.get_snapshot(run_id)
            if snapshot.status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
                return snapshot
            process = self._processes.get(run_id)
            if process and process.poll() is None:
                process.terminate()
            updated = self._update_snapshot(snapshot, status=RunStatus.CANCELLED, completed_at=utc_now())
            EventStore(self._run_dir(run_id), run_id).append("run.cancelled", level=EventLevel.WARNING, message="Run cancelled")
            return updated

    def add_artifact(self, run_id: str, path: Path, kind: str, mime_type: str) -> ArtifactRef:
        """Register a file inside the run directory without exposing host paths."""
        snapshot = self.get_snapshot(run_id)
        run_dir = self._run_dir(run_id).resolve()
        resolved = Path(path).resolve()
        if run_dir not in resolved.parents and resolved != run_dir:
            raise ValueError("artifact must live inside its run directory")
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
        artifact = ArtifactRef(
            kind=kind,
            name=resolved.name,
            mime_type=mime_type,
            relative_uri=resolved.relative_to(run_dir).as_posix(),
            size_bytes=resolved.stat().st_size,
            sha256=digest,
        )
        artifacts = [*snapshot.artifacts, artifact]
        self._update_snapshot(snapshot, artifacts=artifacts)
        EventStore(run_dir, run_id).append(
            "artifact.created",
            message=f"Artifact registered: {artifact.name}",
            payload=artifact.model_dump(mode="json"),
        )
        return artifact

    def list_runs(self, limit: int = 80, status: str | None = None) -> list[dict[str, object]]:
        """Return a persistent searchable archive, backfilling legacy run folders once."""
        from .run_index import RunIndex

        index = RunIndex(self.root)
        for run_dir in self.root.glob("run_*"):
            if not run_dir.is_dir():
                continue
            snapshot_path, request_path = run_dir / "snapshot.json", run_dir / "request.json"
            if not snapshot_path.is_file() or not request_path.is_file():
                continue
            try:
                snapshot = RunSnapshot.model_validate_json(snapshot_path.read_text(encoding="utf-8"))
                request = RunRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
                index.upsert(snapshot, request)
            except (ValueError, OSError):
                # A half-written interrupted legacy run should not hide all valid history.
                continue
        return index.list(limit=limit, status=status)

    def events(self, run_id: str, after_sequence: int = 0, limit: int = 500):
        self.get_snapshot(run_id)
        return EventStore(self._run_dir(run_id), run_id).read_after(after_sequence, limit)
