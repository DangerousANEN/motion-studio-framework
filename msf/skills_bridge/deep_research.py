"""Bridge to Local Deep Research (LDR) — fail-closed fact gathering.

WHY A SUBPROCESS AND NOT AN IMPORT
----------------------------------
LDR lives in its own venv (`~/ldr_venv`) with heavy, conflicting deps, and it
MUST be invoked with cwd=`~/ldr_work`: a legacy `C:\\Users\\ANEN\\local_deep_research.py`
shadows the installed package and turns `from local_deep_research import api`
into an ImportError. Importing it into this process is not an option.

WHY FAIL-CLOSED
---------------
This is the whole point of the module. LDR degrades SILENTLY in a specific,
dangerous way: when SearXNG's JSON API is unreachable it finds nothing, and the
LLM then answers the research question **from its own memory**. The output looks
like a polished, confident, cited-looking report and is worth nothing — a
measured run produced 9 122 characters of prose with `sources=0`. A video built
on that ships invented 2026 model names and invented benchmark numbers as fact.

So every path that cannot prove it did real research raises:
  * SearXNG not answering JSON            -> RuntimeError
  * ldr_run.py exited non-zero            -> RuntimeError
  * result json missing or stale          -> RuntimeError
  * sources == 0                          -> RuntimeError
  * summary empty                         -> RuntimeError

STALENESS IS A REAL FAILURE MODE, NOT A THEORETICAL ONE
-------------------------------------------------------
`ldr_run.py` overwrites `ldr_last_raw.json` on success. If a run crashes, the
PREVIOUS run's file is still sitting there with `sources=60` — so a naive reader
would sail through the fail-closed gate holding somebody else's research. Both
the mtime (newer than process start) and the echoed query are checked.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

HOME = Path(os.path.expanduser("~"))

# These are host facts, not preferences: LDR is installed in this venv and only
# runs correctly from this directory. Overridable for tests and other machines.
LDR_WORK = Path(os.environ.get("MSF_LDR_WORK", HOME / "ldr_work"))
LDR_PYTHON = Path(
    os.environ.get("MSF_LDR_PYTHON", HOME / "ldr_venv" / "Scripts" / "python.exe")
)
LDR_RUNNER = "ldr_run.py"
RAW_JSON = "ldr_last_raw.json"

# Port 8888, not 8080: 8080 is taken by devin-sandbox on this host.
SEARXNG_URL = os.environ.get("MSF_SEARXNG_URL", "http://localhost:8888")


class ResearchUnavailable(RuntimeError):
    """Research could not be PROVEN to have happened. Never a warning."""


@dataclass
class ResearchFacts:
    """A research result that carries its own evidence.

    `sources` is not decoration — it is what makes the fail-closed check
    meaningful, and callers are expected to surface it.
    """

    query: str
    summary: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_sec: float = 0.0
    iterations: int = 0
    detailed: bool = False

    @property
    def source_count(self) -> int:
        return len(self.sources)

    def urls(self, limit: int = 25) -> List[str]:
        out = []
        for s in self.sources[:limit]:
            if isinstance(s, dict):
                url = s.get("link") or s.get("url") or s.get("id")
                if url:
                    out.append(str(url))
            elif s:
                out.append(str(s))
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "summary": self.summary,
            "source_count": self.source_count,
            "urls": self.urls(),
            "elapsed_sec": self.elapsed_sec,
            "iterations": self.iterations,
            "detailed": self.detailed,
        }


def check_searxng(url: str = SEARXNG_URL, timeout: float = 10.0) -> None:
    """Raise unless SearXNG answers the JSON API.

    Checking `/` is not enough: it returns 200 while `?format=json` returns 403
    when the JSON format is not enabled in settings.yml. That 403 is exactly the
    silent-degradation path this module exists to prevent, so the probe must hit
    the JSON endpoint specifically.
    """
    probe = f"{url.rstrip('/')}/search?q=msf+probe&format=json"
    try:
        with urllib.request.urlopen(probe, timeout=timeout) as resp:
            if resp.status != 200:
                raise ResearchUnavailable(
                    f"SearXNG JSON API returned HTTP {resp.status} at {probe}. "
                    "Without it LDR finds nothing and the model answers from memory."
                )
            body = resp.read(2048)
    except urllib.error.HTTPError as exc:
        hint = ""
        if exc.code == 403:
            hint = (
                " The JSON format is disabled. Fix:\n"
                "  docker exec ldr-searxng sh -c 'printf \"\\nsearch:\\n  formats:\\n"
                "    - html\\n    - json\\n\" >> /etc/searxng/settings.yml'\n"
                "  docker restart ldr-searxng"
            )
        raise ResearchUnavailable(
            f"SearXNG JSON API returned HTTP {exc.code} at {probe}.{hint}"
        ) from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise ResearchUnavailable(
            f"SearXNG unreachable at {url} ({exc}). "
            "Start it with: docker start ldr-searxng"
        ) from exc

    if not body.lstrip().startswith(b"{"):
        raise ResearchUnavailable(
            f"SearXNG at {probe} answered 200 but not JSON — the JSON format is "
            "probably disabled in settings.yml."
        )


def _preflight() -> None:
    if not LDR_PYTHON.exists():
        raise ResearchUnavailable(
            f"LDR interpreter missing: {LDR_PYTHON}. "
            "Create it with: python -m venv ~/ldr_venv && "
            "~/ldr_venv/Scripts/python.exe -m pip install local-deep-research"
        )
    runner = LDR_WORK / LDR_RUNNER
    if not runner.exists():
        raise ResearchUnavailable(f"LDR runner missing: {runner}")


def research(
    query: str,
    *,
    detailed: bool = False,
    iters: int = 2,
    qpi: int = 3,
    results: int = 8,
    engine: str = "searxng",
    model: Optional[str] = None,
    timeout: float = 1800.0,
    min_sources: int = 1,
) -> ResearchFacts:
    """Run LDR and return facts, or raise. Never returns unverified output.

    `min_sources` defaults to 1 because the only number that matters is "not
    zero" — zero means the model answered from memory. Raise it for topics where
    a single blog post is not enough evidence.
    """
    if not query or not query.strip():
        raise ValueError("empty research query")

    _preflight()
    check_searxng()

    raw_path = LDR_WORK / RAW_JSON
    # Recorded BEFORE launching so a crashed run cannot pass off the previous
    # run's json as its own.
    started = time.time()
    stale_mtime = raw_path.stat().st_mtime if raw_path.exists() else 0.0

    cmd = [
        str(LDR_PYTHON),
        LDR_RUNNER,
        query,
        "--iters",
        str(iters),
        "--qpi",
        str(qpi),
        "--results",
        str(results),
        "--engine",
        engine,
    ]
    if detailed:
        cmd.append("--detailed")
    if model:
        cmd += ["--model", model]

    print(f"[research] {'detailed' if detailed else 'quick'} engine={engine} "
          f"iters={iters} qpi={qpi} results={results}")
    print(f"[research] query: {query[:160]}{'...' if len(query) > 160 else ''}")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(LDR_WORK),  # MANDATORY: see the module docstring on shadowing.
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ResearchUnavailable(
            f"LDR exceeded {timeout:.0f}s. Lower --iters/--qpi, or raise the timeout."
        ) from exc

    elapsed = round(time.time() - started, 1)

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-800:]
        raise ResearchUnavailable(
            f"LDR exited {proc.returncode} after {elapsed}s.\n{tail}"
        )

    if not raw_path.exists():
        raise ResearchUnavailable(f"LDR wrote no {RAW_JSON} in {LDR_WORK}")

    if raw_path.stat().st_mtime <= stale_mtime:
        raise ResearchUnavailable(
            f"{RAW_JSON} was not rewritten by this run (mtime unchanged). "
            "Refusing to report a previous run's research as this one's."
        )

    try:
        data = json.loads(raw_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchUnavailable(f"cannot read {raw_path}: {exc}") from exc

    echoed = (data.get("query") or "").strip()
    if echoed and echoed != query.strip():
        raise ResearchUnavailable(
            "the result file answers a DIFFERENT query — concurrent LDR runs "
            f"share {RAW_JSON}.\n  asked:  {query[:100]}\n  found:  {echoed[:100]}"
        )

    summary = (data.get("summary") or data.get("report") or "").strip()
    sources = data.get("sources") or data.get("all_links_of_system") or []

    if len(sources) < min_sources:
        raise ResearchUnavailable(
            f"LDR returned {len(sources)} sources (need >= {min_sources}) but "
            f"{len(summary)} characters of summary. That is the model answering "
            "from memory, not research — refusing to build a video on it. "
            "Check: SearXNG JSON enabled, and detailed_research() given a "
            "settings_snapshot rather than loose kwargs."
        )

    if not summary:
        raise ResearchUnavailable(
            f"LDR found {len(sources)} sources but produced an empty summary."
        )

    facts = ResearchFacts(
        query=query,
        summary=summary,
        sources=list(sources),
        elapsed_sec=elapsed,
        iterations=int(data.get("iterations") or iters),
        detailed=detailed,
    )
    print(f"[research] OK {elapsed}s | {len(summary)} chars | "
          f"{facts.source_count} sources")
    return facts
