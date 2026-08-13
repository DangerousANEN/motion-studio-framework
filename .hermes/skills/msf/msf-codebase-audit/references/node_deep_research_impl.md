# node_deep_research — Full Implementation Reference

Source: audit session 2026-08-12, derived from ldr_run.py + video_graph.py full reads.

## Constants (add after line 31 in video_graph.py)

```python
LDR_VENV_PYTHON = r"C:\Users\ANEN\ldr_venv\Scripts\python.exe"
LDR_SCRIPT      = r"C:\Users\ANEN\ldr_work\ldr_run.py"
LDR_WORKDIR     = r"C:\Users\ANEN\ldr_work"
```

## Helper functions (add before node_deep_research)

```python
def _build_ldr_query(state: VideoState) -> str:
    """Auto-generate LDR query from state fields."""
    explicit = state.get("ldr_query")
    if explicit:
        return explicit
    topic = state.get("ldr_topic")
    if topic:
        return topic
    text = state.get("text", "")
    return text[:120].strip() or "state of the art LLM models 2026"


def _format_ldr_context(summary: str, sources: List[str]) -> str:
    """Format LDR result into a context block for downstream nodes."""
    ctx = "## Актуальные данные (LDR Research)\n\n" + summary.strip() + "\n"
    if sources:
        ctx += "\n### Источники:\n"
        for i, s in enumerate(sources[:10], 1):
            ctx += f"{i}. {s}\n"
    return ctx
```

## node_deep_research (insert after node_voice_synthesis ~line 377)

```python
def node_deep_research(state: VideoState) -> VideoState:
    """Optional LDR research node.

    Active ONLY when state["ldr_enabled"] is True.
    Runs ldr_run.py via subprocess in ldr_venv (dependency isolation).

    PITFALL: cwd=LDR_WORKDIR is mandatory. C:/Users/ANEN contains
    local_deep_research.py which shadows the installed package -> ImportError.

    CACHE: Pass ldr_cache_path to reuse ldr_last_raw.json without re-running.
    LDR failure is non-fatal: warning logged, ldr_context="", pipeline continues.
    """
    if not state.get("ldr_enabled"):
        return state  # pass-through, no side effects

    # Reuse cache if available
    cache_path = state.get("ldr_cache_path")
    if cache_path and Path(cache_path).is_file():
        try:
            cached = json.loads(Path(cache_path).read_text(encoding="utf-8"))
            summary = cached.get("summary") or cached.get("report") or ""
            src_list = cached.get("sources") or cached.get("all_links_of_system") or []
            if summary:
                sources = [
                    (s.get("link") or s.get("url") or str(s))
                    for s in src_list[:15]
                    if isinstance(s, (dict, str))
                ]
                state["ldr_summary"] = summary
                state["ldr_sources"] = sources
                state["ldr_context"] = _format_ldr_context(summary, sources)
                print(f"[deep_research] loaded from cache {cache_path}")
                return state
        except Exception as exc:
            print(f"[deep_research] cache error: {exc} — re-running LDR")

    query = _build_ldr_query(state)
    model = state.get("ldr_model", "antigravity/claude-sonnet-4-6")
    iters = state.get("ldr_iters", 2)
    qpi = state.get("ldr_qpi", 3)
    detailed = state.get("ldr_detailed", False)
    out_md = str(Path(LDR_WORKDIR) / "ldr_msf_context.md")

    cmd = [
        LDR_VENV_PYTHON, LDR_SCRIPT, query,
        "--model", model, "--iters", str(iters), "--qpi", str(qpi), "--out", out_md,
    ]
    if detailed:
        cmd.append("--detailed")

    print(f"[deep_research] query={query[:80]!r} model={model} iters={iters} qpi={qpi}")
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, errors="replace",
        cwd=LDR_WORKDIR,
        timeout=600,  # 10 min max; SearXNG can be slow
    )

    if result.returncode != 0:
        print(f"[deep_research] WARNING: LDR failed (exit {result.returncode}). "
              f"Stderr: {result.stderr[:500]}")
        state["ldr_context"] = ""
        return state

    raw_path = Path(LDR_WORKDIR) / "ldr_last_raw.json"
    summary = ""
    sources: List[str] = []
    if raw_path.is_file():
        try:
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            summary = raw.get("summary") or raw.get("report") or ""
            src_list = raw.get("sources") or raw.get("all_links_of_system") or []
            sources = [
                (s.get("link") or s.get("url") or str(s))
                for s in src_list[:15]
                if isinstance(s, (dict, str))
            ]
        except Exception as exc:
            print(f"[deep_research] JSON parse error: {exc}")

    state["ldr_summary"] = summary
    state["ldr_sources"] = sources
    state["ldr_context"] = _format_ldr_context(summary, sources)
    state["ldr_cache_path"] = str(raw_path)
    print(f"[deep_research] done: summary={len(summary)} chars sources={len(sources)}")
    return state
```

## VideoState fields to add (TypedDict, after existing fields ~line 135)

```python
    # === LDR Deep Research ===
    ldr_enabled: Optional[bool]
    ldr_query: Optional[str]
    ldr_topic: Optional[str]
    ldr_detailed: Optional[bool]
    ldr_iters: Optional[int]
    ldr_qpi: Optional[int]
    ldr_model: Optional[str]
    ldr_summary: Optional[str]
    ldr_sources: Optional[List[str]]
    ldr_context: Optional[str]
    ldr_cache_path: Optional[str]
```

## build_msf_graph() changes

```python
# Add node registration:
workflow.add_node("deep_research", node_deep_research)

# Change first edge:
# BEFORE: workflow.set_entry_point("gate_check"); workflow.add_edge("gate_check", "script_split")
# AFTER:
workflow.set_entry_point("gate_check")
workflow.add_edge("gate_check", "deep_research")
workflow.add_edge("deep_research", "script_split")
```

## Example invocation with LDR enabled

```python
import sys
sys.path.insert(0, r"C:\Users\ANEN\motion-studio-framework")
from msf.graph.video_graph import build_msf_graph

result = build_msf_graph().invoke({
    "text": "Открытые модели в 2026 году.",
    "agent_level": 1,
    "ldr_enabled": True,
    "ldr_query": "best open weight LLMs August 2026 Gemma Qwen DeepSeek consumer GPU",
    "ldr_iters": 2,
    "ldr_qpi": 3,
    "output_path": r"C:\Users\ANEN\motion-studio-framework\output\with_research.mp4",
    "storyboard": [...],
})
print("LDR context:", result.get("ldr_context", "")[:200])
print("MP4:", result["final_mp4"])
```
