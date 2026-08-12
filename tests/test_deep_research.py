"""Fail-closed contract for the deep-research bridge.

THE FAILURE THIS GUARDS AGAINST
-------------------------------
LDR degrades silently: with SearXNG's JSON API unreachable it finds nothing and
the LLM answers from memory, producing a confident, polished, cited-LOOKING
report. A measured run produced 9 122 characters with sources=0. A video built on
that ships invented model names and invented benchmark numbers as fact.

So `sources == 0` must RAISE, never warn — and every one of these tests exists
because there is a way to accidentally sail past that check.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from msf.skills_bridge import deep_research as dr
from msf.skills_bridge.deep_research import ResearchFacts, ResearchUnavailable


@pytest.fixture()
def fake_ldr(tmp_path, monkeypatch):
    """A fake LDR install: a runner, an interpreter, and a writable work dir.

    Returns a helper that sets what the "run" will produce.
    """
    work = tmp_path / "ldr_work"
    work.mkdir()
    (work / dr.LDR_RUNNER).write_text("# fake runner", encoding="utf-8")
    py = tmp_path / "python.exe"
    py.write_text("# fake interpreter", encoding="utf-8")

    monkeypatch.setattr(dr, "LDR_WORK", work)
    monkeypatch.setattr(dr, "LDR_PYTHON", py)
    # SearXNG is probed separately; these tests are about the result contract.
    monkeypatch.setattr(dr, "check_searxng", lambda *a, **k: None)

    class Result:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def configure(payload=None, returncode=0, write=True, stderr=""):
        def fake_run(cmd, **kwargs):
            # The cwd is not cosmetic: running from ~ makes a legacy
            # local_deep_research.py shadow the package and ImportError.
            assert Path(kwargs["cwd"]) == work
            if write and payload is not None:
                time.sleep(0.01)  # ensure a newer mtime than the pre-run stamp
                (work / dr.RAW_JSON).write_text(
                    json.dumps(payload, ensure_ascii=False), encoding="utf-8"
                )
            return Result(returncode, stderr=stderr)

        monkeypatch.setattr(dr.subprocess, "run", fake_run)

    configure.work = work  # type: ignore[attr-defined]
    return configure


def _payload(query="q", sources=3, summary="реальные факты"):
    return {
        "query": query,
        "summary": summary,
        "iterations": 2,
        "sources": [
            {"title": f"t{i}", "link": f"https://example.com/{i}"} for i in range(sources)
        ],
    }


def test_zero_sources_raises_even_with_a_long_summary(fake_ldr):
    """The exact silent-degradation case: lots of prose, no research."""
    fake_ldr(_payload(sources=0, summary="x" * 9000))
    with pytest.raises(ResearchUnavailable, match="0 sources"):
        dr.research("q")


def test_sources_present_returns_facts(fake_ldr):
    fake_ldr(_payload(sources=8))
    facts = dr.research("q")
    assert facts.source_count == 8
    assert facts.summary == "реальные факты"
    assert facts.urls(2) == ["https://example.com/0", "https://example.com/1"]


def test_min_sources_can_be_raised(fake_ldr):
    fake_ldr(_payload(sources=2))
    with pytest.raises(ResearchUnavailable, match="need >= 5"):
        dr.research("q", min_sources=5)


def test_empty_summary_with_sources_raises(fake_ldr):
    fake_ldr(_payload(sources=5, summary="   "))
    with pytest.raises(ResearchUnavailable, match="empty summary"):
        dr.research("q")


def test_nonzero_exit_raises_and_reports_stderr(fake_ldr):
    fake_ldr(_payload(), returncode=1, stderr="ImportError: cannot import name 'api'")
    with pytest.raises(ResearchUnavailable, match="exited 1"):
        dr.research("q")


def test_stale_result_file_is_refused(fake_ldr):
    """A crashed run must not pass off the PREVIOUS run's json as its own.

    ldr_run.py overwrites ldr_last_raw.json only on success, so after a crash a
    file with sources=60 is still sitting there — and a naive reader sails
    straight through the fail-closed gate holding somebody else's research.
    """
    work = Path(fake_ldr.work)
    (work / dr.RAW_JSON).write_text(json.dumps(_payload(sources=60)), encoding="utf-8")
    # Now "run" without rewriting the file.
    fake_ldr(_payload(), write=False)
    with pytest.raises(ResearchUnavailable, match="not rewritten"):
        dr.research("q")


def test_result_for_a_different_query_is_refused(fake_ldr):
    """Concurrent runs share one result file; answering the wrong question is a lie."""
    fake_ldr(_payload(query="какой-то другой вопрос", sources=9))
    with pytest.raises(ResearchUnavailable, match="DIFFERENT query"):
        dr.research("мой вопрос")


def test_missing_result_file_raises(fake_ldr):
    fake_ldr(None, write=False)
    with pytest.raises(ResearchUnavailable, match="no ldr_last_raw.json"):
        dr.research("q")


def test_missing_interpreter_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(dr, "LDR_PYTHON", tmp_path / "nope.exe")
    monkeypatch.setattr(dr, "check_searxng", lambda *a, **k: None)
    with pytest.raises(ResearchUnavailable, match="interpreter missing"):
        dr.research("q")


def test_missing_runner_raises(tmp_path, monkeypatch):
    py = tmp_path / "python.exe"
    py.write_text("x", encoding="utf-8")
    empty = tmp_path / "work"
    empty.mkdir()
    monkeypatch.setattr(dr, "LDR_PYTHON", py)
    monkeypatch.setattr(dr, "LDR_WORK", empty)
    monkeypatch.setattr(dr, "check_searxng", lambda *a, **k: None)
    with pytest.raises(ResearchUnavailable, match="runner missing"):
        dr.research("q")


def test_empty_query_is_rejected():
    with pytest.raises(ValueError, match="empty research query"):
        dr.research("   ")


def test_searxng_unreachable_raises_with_a_fix_hint():
    """A closed port must fail loudly — this is the whole silent-failure path."""
    with pytest.raises(ResearchUnavailable, match="unreachable"):
        dr.check_searxng("http://localhost:9", timeout=2)


def test_facts_to_dict_carries_the_evidence():
    facts = ResearchFacts(
        query="q",
        summary="s",
        sources=[{"link": "https://a.example"}, {"url": "https://b.example"}],
        elapsed_sec=12.3,
    )
    d = facts.to_dict()
    assert d["source_count"] == 2
    assert d["urls"] == ["https://a.example", "https://b.example"]


# ----------------------------------------------------------------- graph wiring


def test_research_node_is_a_noop_unless_requested(monkeypatch):
    """Opt-in: an unrelated render must not suddenly require SearXNG."""
    from msf.graph import video_graph as vg

    def explode(*a, **k):  # pragma: no cover - must never run
        raise AssertionError("research ran without being requested")

    monkeypatch.setattr(dr, "research", explode)
    state = {"text": "привет"}
    assert vg.node_deep_research(dict(state)) == state


def test_research_node_keeps_a_supplied_storyboard(monkeypatch):
    """A hand-authored storyboard wins; research attaches as verification."""
    from msf.graph import video_graph as vg

    facts = ResearchFacts(
        query="q", summary="итог", sources=[{"link": "https://a.example"}]
    )
    monkeypatch.setattr(
        "msf.skills_bridge.deep_research.research", lambda *a, **k: facts
    )

    board = [{"text": "сцена один", "preset": "HeroKinetic"}]
    out = vg.node_deep_research(
        {"research": True, "research_query": "q", "storyboard": board}
    )
    assert out["storyboard"] == board
    assert out["research_sources"] == ["https://a.example"]
    assert "text" not in out  # narration untouched


def test_research_node_propagates_the_failure(monkeypatch):
    """The node must NOT catch ResearchUnavailable — fail-closed means fail."""
    from msf.graph import video_graph as vg

    def boom(*a, **k):
        raise ResearchUnavailable("sources=0")

    monkeypatch.setattr("msf.skills_bridge.deep_research.research", boom)
    with pytest.raises(ResearchUnavailable):
        vg.node_deep_research({"research": True, "research_query": "q"})


def test_research_node_writes_a_script_from_the_facts(monkeypatch):
    from msf.graph import video_graph as vg

    facts = ResearchFacts(
        query="q", summary="Модель X набрала 77 баллов.",
        sources=[{"link": "https://a.example"}],
    )
    monkeypatch.setattr(
        "msf.skills_bridge.deep_research.research", lambda *a, **k: facts
    )
    monkeypatch.setattr(
        "msf.agents.llm_client.LLMClient.chat",
        lambda self, *a, **k: "Первая строка.\n- Вторая строка.\n\nТретья строка.",
    )
    out = vg.node_deep_research({"research": True, "research_query": "q"})
    # Bullets and blank lines stripped, joined into narration for the splitter.
    assert out["text"] == "Первая строка. Вторая строка. Третья строка."
    assert out["research_facts"]["source_count"] == 1


def test_graph_runs_research_before_the_script_split():
    """Research can REPLACE `text`, so it must precede the split."""
    from msf.graph.video_graph import build_msf_graph

    graph = build_msf_graph()
    nodes = set(graph.get_graph().nodes)
    assert "deep_research" in nodes
    edges = {(e.source, e.target) for e in graph.get_graph().edges}
    assert ("gate_check", "deep_research") in edges
    assert ("deep_research", "script_split") in edges
