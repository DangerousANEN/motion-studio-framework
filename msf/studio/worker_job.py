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


_NODE_ACTIVITY = {
    "gate_check": ("Проверяем входные ограничения", "Проверяем tier, topic и обязательные параметры."),
    "deep_research": ("Исследуем тему", "Собираем и проверяем публичные источники."),
    "script_split": ("Собираем сценарий", "Строим hook, смысл, доказательство и CTA."),
    "voice_synthesis": ("Готовим озвучку", "Синтезируем голос для готовых сцен."),
    "soundtrack": ("Сводим звук", "Подбираем музыку, SFX и ducking."),
    "build_spec": ("Собираем видеоспеку", "Проверяем сцены, стиль и renderer contract."),
    "render": ("Рендерим композицию", "Remotion рендерит цельный ролик; per-scene прогресс доступен только при явном отчёте renderer."),
    "master_audio": ("Мастерим аудио", "Нормализуем и финализируем звуковую дорожку."),
    "qa": ("Проводим QA", "Проверяем длительность, кадры, звук и итоговый файл."),
    "repair": ("Исправляем QA-ошибку", "Применяем разрешённый repair path перед повторным рендером."),
}


def _activity_for(node: str, task_input: object) -> dict[str, object]:
    label, detail = _NODE_ACTIVITY.get(node, (node, "Выполняется узел графа."))
    scene_count = 0
    if isinstance(task_input, dict):
        scenes = task_input.get("scenes") or (task_input.get("spec_dict") or {}).get("scenes", [])
        if isinstance(scenes, list):
            scene_count = len(scenes)
    payload: dict[str, object] = {"activity": label, "detail": detail}
    if scene_count:
        payload["scene_count"] = scene_count
    return payload


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
            "operator_overrides": request.operator_overrides,
        }
        if request.research:
            graph_state["research_query"] = request.topic
        graph = build_msf_graph()
        final: dict = {}
        task_spans: dict[str, object] = {}
        with traces.span("run.execute", attributes={"provider": "langgraph", "model": "configured"}):
            # `tasks` emits an event when LangGraph starts a node and another when
            # it completes. This is operational telemetry, not model reasoning.
            for task in graph.stream(graph_state, stream_mode="tasks"):
                node = str(task.get("name") or "unknown")
                task_id = str(task.get("id") or node)
                if "input" in task:
                    activity = _activity_for(node, task.get("input"))
                    _update_status(service, run_id, current_node=node)
                    events.append("node.started", node=node, message=str(activity["activity"]), payload=activity)
                    task_spans[task_id] = traces.start(f"node.{node}", attributes={"node": node})
                    continue
                span = task_spans.pop(task_id, None)
                error = task.get("error")
                if span is not None:
                    traces.finish(span, error=str(error) if error else None)
                if error:
                    events.append("node.failed", node=node, level=EventLevel.ERROR, message=str(error))
                    raise RuntimeError(str(error))
                result = task.get("result")
                events.append("node.completed", node=node, message=f"{node} completed")
                if isinstance(result, dict):
                    final.update(result)
                    if result.get("error"):
                        events.append(
                            "node.failed",
                            node=node,
                            level=EventLevel.ERROR,
                            message=str(result["error"]),
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
                current_node=None,
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
            _update_status(service, run_id, status=RunStatus.FAILED, completed_at=utc_now(), error=str(exc), current_node=None)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
