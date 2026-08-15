"""Smoke check for Studio v2 event and trace persistence."""
from pathlib import Path
from tempfile import TemporaryDirectory

from msf.studio.events import EventStore
from msf.studio.tracing import TraceStore


if __name__ == "__main__":
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        events = EventStore(root, "run_demo")
        created = events.append("run.created", message="created")
        completed = events.append("node.completed", node="build_spec", message="done")
        assert [event.sequence for event in events.read_after()] == [created.sequence, completed.sequence]

        traces = TraceStore(root, "run_demo", trace_id="trace_demo")
        with traces.span("node.build_spec", attributes={"node": "build_spec", "prompt": "must not persist"}):
            pass
        spans = traces.read()
        assert len(spans) == 2
        assert spans[0].attributes == {"node": "build_spec"}
        assert spans[-1].status == "ok"
        print(f"events={len(events.read_after())}")
        print(f"spans={len(spans)}")
