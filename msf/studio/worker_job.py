"""Child-process worker for a single approved MSF Studio run."""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

from .contracts import EventLevel, RunRequest, RunStatus, utc_now
from .events import EventStore
from .runs import StudioRunService
from .tracing import TraceStore


def _update_status(service: StudioRunService, run_id: str, **changes: object) -> None:
    snapshot = service.get_snapshot(run_id)
    service._update_snapshot(snapshot, **changes)  # internal worker-only transition


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return 2
    run_dir = Path(argv[1]).resolve()
    run_id = run_dir.name
    service = StudioRunService(run_dir.parent)
    events = EventStore(run_dir, run_id)
    traces = TraceStore(run_dir, run_id)
    try:
        request = RunRequest.model_validate_json((run_dir / "request.json").read_text(encoding="utf-8"))
        from msf.graph.video_graph import build_msf_graph

        graph_state = {
            "text": request.text or request.topic,
            "preset": request.preset,
            "voice": request.voice,
            "agent_level": request.agent_level,
            "output_path": str(run_dir / "final.mp4"),
            "music": request.music,
            "sfx": request.sfx,
            "research": request.research,
        }
        if request.research:
            graph_state["research_query"] = request.topic
        graph = build_msf_graph()
        final: dict = {}
        with traces.span("run.execute", attributes={"provider": "langgraph", "model": "configured"}):
            for update in graph.stream(graph_state):
                for node, payload in update.items():
                    with traces.span(f"node.{node}", attributes={"node": node}):
                        events.append("node.completed", node=node, message=f"{node} completed")
                        if isinstance(payload, dict):
                            final.update(payload)
                            if payload.get("error"):
                                events.append(
                                    "node.failed",
                                    node=node,
                                    level=EventLevel.ERROR,
                                    message=str(payload["error"]),
                                )
        mp4 = final.get("final_mp4") or final.get("raw_mp4")
        if mp4 and Path(mp4).is_file():
            target = run_dir / "final.mp4"
            source = Path(mp4).resolve()
            if source != target.resolve():
                target.write_bytes(source.read_bytes())
            service.add_artifact(run_id, target, "video", "video/mp4")
            snapshot = service.get_snapshot(run_id)
            artifact_id = snapshot.artifacts[-1].artifact_id
            _update_status(
                service,
                run_id,
                status=RunStatus.COMPLETED,
                completed_at=utc_now(),
                output_artifact_id=artifact_id,
            )
            events.append("run.completed", message="Render and QA completed")
            return 0
        raise RuntimeError("pipeline completed without an MP4 artifact")
    except Exception as exc:  # boundary: all failures must be visible in event stream
        failure_span = traces.start("run.failed", attributes={"status_code": 1})
        traces.finish(failure_span, error=f"{type(exc).__name__}: {exc}")
        events.append(
            "run.failed",
            level=EventLevel.ERROR,
            message=str(exc),
            payload={"exception": type(exc).__name__, "traceback": traceback.format_exc(limit=12)},
        )
        try:
            _update_status(service, run_id, status=RunStatus.FAILED, completed_at=utc_now(), error=str(exc))
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
