"""Run one MSF pipeline job in a fresh process, printing progress the panel parses.

WHY A SEPARATE SCRIPT
---------------------
The panel starts this with subprocess.Popen instead of calling the graph in a
thread. The graph loads a 1.7B TTS model onto CUDA and shells out to Remotion and
ffmpeg; in-process it would block the event loop for minutes, and a CUDA OOM would
take the whole panel down with it. A subprocess also means "kill this run" is a
real operation.

CONTRACT WITH THE PANEL
-----------------------
stdout is the progress channel and is parsed, so the format matters:

    [<node>] <message>      one line as each graph node starts
    OUTPUT: <abs path>      once, on success
    ERROR: <message>        once, on failure

Nothing here invents state. If the graph raises, the traceback is printed and the
exit code is non-zero — the panel reports "failed" rather than a plausible-looking
result, because a video that silently did not render is worse than a visible error.

Usage: python -m msf.panel.run_job <job.json>
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("ERROR: usage: run_job.py <job.json>", flush=True)
        return 2

    job_path = Path(argv[1])
    try:
        job = json.loads(job_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: cannot read job file {job_path}: {exc}", flush=True)
        return 2

    run_id = job.get("run_id", "run")
    out_dir = REPO / "output" / f"panel_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # The graph's state keys are VideoState (msf/graph/video_graph.py). `text` is
    # the narration source; the topic alone is not narration, so when no text is
    # supplied the topic is used as the seed and research (if enabled) replaces it.
    state = {
        "text": job.get("text") or job["topic"],
        "preset": job.get("preset", "HeroKinetic"),
        "voice": job.get("voice"),
        "agent_level": job.get("agent_level", 3),
        "output_path": str(out_dir / f"msf_{run_id}.mp4"),
        "music": True,
        "sfx": True,
        "research": bool(job.get("research")),
    }
    if job.get("research"):
        state["research_query"] = job["topic"]

    print(f"[start] run={run_id} preset={state['preset']} "
          f"voice={state['voice'] or '(registry default)'} research={state['research']}",
          flush=True)

    try:
        from msf.graph.video_graph import build_msf_graph

        graph = build_msf_graph()
    except Exception:
        print("ERROR: could not build the graph", flush=True)
        traceback.print_exc()
        return 1

    try:
        # stream() yields one dict per completed node, which is exactly the
        # progress signal the panel needs — invoke() would return only at the end.
        final: dict = {}
        for update in graph.stream(state):
            for node, payload in update.items():
                print(f"[{node}] done", flush=True)
                if isinstance(payload, dict):
                    final.update(payload)
                    if payload.get("error"):
                        print(f"[{node}] error: {payload['error']}", flush=True)
    except Exception:
        print("ERROR: pipeline raised", flush=True)
        traceback.print_exc()
        return 1

    mp4 = final.get("final_mp4") or final.get("raw_mp4") or state["output_path"]
    if mp4 and Path(mp4).is_file():
        print(f"OUTPUT: {Path(mp4).resolve()}", flush=True)
        return 0

    # Reaching here means the graph completed without producing a file. Say so.
    print(
        f"ERROR: pipeline finished but no video exists at {mp4!r}; "
        f"qa_passed={final.get('qa_passed')} error={final.get('error')!r}",
        flush=True,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
