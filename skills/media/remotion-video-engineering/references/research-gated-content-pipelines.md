# Wiring a research step into an automated pipeline (fail-closed)

Applies when a video/content pipeline is *required* to run fresh research before it
generates a script, so stale facts cannot reach the output. Written after adding a
Local Deep Research (LDR) stage to the MSF video graph. Companion skill:
`local-deep-research` (user-owned — read it for the runner itself; the notes below are
the pipeline-integration half).

---

## 1. Exit code is not a research check

The LDR runner ends with:

```python
return 0 if summary else 1
```

So a run that found **zero sources** and answered purely from model memory exits **0**.
A node that gates on `returncode != 0` passes hallucinated facts downstream — precisely
the failure the research stage was added to prevent.

Gate on the **source count read from the result JSON** (§3), not from stdout:

```python
sources = data.get("sources") or data.get("all_links_of_system") or []
if len(sources) < min_sources:
    raise ResearchUnavailable(
        f"{len(sources)} sources but {len(summary)} chars of summary — "
        "that is the model answering from memory, not research"
    )
```

Regexing `sources=(\d+)` out of the banner line works but is the weaker option: it
depends on the runner's print formatting, and the JSON file has to be read anyway to get
the summary and the URLs. Parse stdout only if you deliberately want to avoid touching
the file.

`min_sources` defaults to **1**, because the only number that matters is "not zero".
Raise it per-topic when one blog post is not enough evidence.

## 1a. The two guards the file-reading approach *requires*

Reading `ldr_last_raw.json` is right, but the file is shared mutable state and both
failure modes are live, not theoretical.

**Stale file.** The runner overwrites the JSON *only on success*. After a crash the
previous run's file is still sitting there with `sources=60`, so a naive reader sails
straight through the fail-closed gate holding somebody else's research. Stamp the mtime
**before** launching and compare after:

```python
stale_mtime = raw.stat().st_mtime if raw.exists() else 0.0
...  # subprocess.run(...)
if raw.stat().st_mtime <= stale_mtime:
    raise ResearchUnavailable("result file was not rewritten by this run")
```

**Wrong query.** Concurrent runs share that one file. The dump echoes the query it
answered — compare it to the one you asked:

```python
echoed = (data.get("query") or "").strip()
if echoed and echoed != query.strip():
    raise ResearchUnavailable("the result file answers a DIFFERENT query")
```

Both guards are cheap and both are unreachable by any test that only mocks the happy
path — write them as explicit negative tests (§9).

## 1b. Probe the search backend's JSON endpoint, not its root

The whole silent-degradation path starts at the search backend, so check it *before*
spending minutes on a run. `GET /` returns **200** while `GET /search?q=x&format=json`
returns **403** when the JSON format is disabled — checking the root proves nothing.

```python
probe = f"{url.rstrip('/')}/search?q=probe&format=json"   # NOT just url
```

Put the fix in the exception text for the 403 case specifically, so the next reader does
not have to rediscover it. Also reject a 200 whose body does not start with `{` — that is
the same misconfiguration answering with HTML.

## 1c. Make the gate opt-in, and let it be a true no-op

`if not (state.get("research") or state.get("research_query")): return state` as the first
two lines. Otherwise adding a research stage makes every unrelated render newly dependent
on a search container being up — which is how a mandatory gate gets deleted by the next
person debugging an unrelated failure.

Opt-in is *not* the same as fail-open: once enabled there is no degraded path.

## 2. Fail closed, not open

The default shape a code-generating subagent reaches for is:

```python
except Exception as exc:
    state["research_context"] = ""      # and continue
    print(f"[research] skipped: {exc}")
```

That converts a hard requirement into a silent no-op the moment the search backend is
down. Two independently-dispatched subagents produced exactly this, with **zero**
`raise` statements in a 553-line plan. If the user asked for mandatory research, the
node must raise.

## 3. Read machine output from disk, not stdout

stdout is human-formatted: banner lines, `====` rules, summary body, numbered
`SOURCES:` list. There is **no JSON mode**. `json.loads(result.stdout)` cannot work.

- machine-readable dump: `ldr_last_raw.json`, written to the **current working
  directory** every run (so a fixed `cwd` is doubly required — the other reason is
  module shadowing)
- human/markdown: optional `--out FILE` → `# query`, summary, `## Источники`

## 4. Verify the CLI contract by reading the runner

| | |
|---|---|
| query | **positional** — `ldr_run.py "question"`; there is no `--query` |
| format | no `--format` flag exists |
| depth | `--detailed`, `--iters N`, `--qpi N`, `--results N` |
| output | `--out FILE` (markdown) + `ldr_last_raw.json` in cwd |

**Subagents invent flags for local runners.** Two separate code-writing children emitted
`ldr_run.py --query "..." --format json` followed by `json.loads(stdout)`. Both die on
the first argparse call. When delegating an integration against a local script, either
hand the child the verified flag table or read the script yourself before accepting the
code. A plan that looks detailed and cites real file paths can still be built on invented
interfaces.

## 5. Carry confidence grades through to the output

A good research report flags its own weak numbers (`⚠ single source`,
`vendor-reported`, `contradicts [12]`). Those flags get laundered into clean-looking
facts the moment someone copies values into a template. Keep a confidence field beside
every value:

```python
{"value": 77.2, "metric": "SWE-bench Verified", "confidence": "confirmed"}   # 2+ sources agree
{"value": 99.2, "metric": "AIME 2026",          "confidence": "vendor"}      # never ship as fact
```

Only `confirmed` reaches user-facing output. Expect real gaps too: a landscape report can
be rich on benchmark scores and contain **no** throughput or licence data at all — any
downstream claim about those is invented unless a second pass fills them.

## 6. Cache by query hash

A multi-minute research run per render makes the pipeline unusable. Store
`<sha1(query)>.md` with a TTL and reuse it; only bypass on an explicit refresh flag.

## 7. Where the node goes

Insert between the gate/validation node and the script-splitting node — the research step
can **replace** `text`, so it has to run before the text is cut into scenes.

Note that a mechanical text splitter cannot *use* a research report — it only chops
sentences. So the node needs an LLM step of its own (`report → narration`), and that step
is a fresh hallucination surface *inside* the pipeline. Make the grounding rule blunt in
the prompt; a soft instruction invites exactly what the research stage exists to prevent:

```
1. Все факты, цифры, названия и версии бери ТОЛЬКО из исследования ниже.
   Ничего не добавляй по памяти. Если чего-то нет в тексте — не упоминай.
```

**A caller-supplied storyboard wins.** If `state["storyboard"]` exists, keep it and attach
the sources as verification material rather than rewriting it — someone hand-authored those
scenes and a research pass is not a mandate to discard them.

## 8. Report the pipeline's own claim honestly

The summary you hand the user is about a *gate*, so it has to be verifiable both ways.
Prove the success path with real numbers and prove the refusal path by breaking it:

```
real run, iters=1 qpi=1 results=4   103 s, 2371 chars, 8 sources, real URLs
                                    narration generated with correct dates/params
backend pointed at a dead port      pipeline STOPPED with ResearchUnavailable
                                    (not "warned and continued")
```

A fail-closed gate that has never been observed failing closed is an untested claim. One
env-var override (`MSF_SEARXNG_URL=http://localhost:9`) is the entire experiment — do it.

## 9. Test the refusal paths, not the happy path

The happy path is the one case that cannot regress unnoticed. Every guard above needs a
negative test, and the fixture that makes them cheap is a fake install: a temp dir with a
dummy runner file, a dummy interpreter, `check_searxng` patched to a no-op, and
`subprocess.run` patched to write whatever payload the test wants.

Worth having as distinct tests, because each one is a different way to sail past the gate:

- zero sources **with a 9 000-character summary** (the actual observed failure)
- `min_sources` raised above what the run returned
- sources present but summary empty
- runner exit != 0
- result file missing
- result file **not rewritten** (stale-mtime guard)
- result file answering a **different query**
- search backend unreachable
- the node is a **no-op** when research was not requested
- the node **does not catch** the exception (fail-closed means the graph stops)
- a supplied storyboard survives untouched

Also assert the wiring itself, since an unwired node passes all of the above:

```python
edges = {(e.source, e.target) for e in build_graph().get_graph().edges}
assert ("gate_check", "deep_research") in edges
assert ("deep_research", "script_split") in edges
```

## 10. Layout fixtures are not content — and a ranking needs its criterion

Two related ways fabricated data reaches a deliverable even with the gate in place.

**Hand-made fixtures leak.** Stress-testing a preset's geometry needs long realistic
strings, so you write a spec by hand — a 2026 open-source leaderboard, say. That spec
never touches the research node. The preset then renders it *beautifully*: sorts by
value, awards 🥇, right-aligns the percentages. The user reviewing the screenshot reads
the **claim**, not the fixture, and here correctly objected that Claude Opus is not an
open-source model and that Kimi K3 led at the time. Label fixture output as a geometry
probe when you show it, and never promote a layout fixture into a shipped scene.

**A ranked list is a claim about a metric, so the metric must be on screen.** "Best
open-source model" has no single answer: raw capability and capability-per-watt produce
different first places, and so do licence-restricted vs fully permissive scopings. A
leaderboard with no stated criterion is not merely vague — it is incorrect for most
readings of it. Require the research node to return the metric name alongside the rows
and render it (`subtitle: "SWE-bench Verified, открытые веса"`), the same way §5 requires
a confidence grade to survive into the output. This is the factual twin of the layout rule
in `chart-and-widget-visual-design.md` §1g: drawing a medal makes ordering a correctness
claim, and naming the metric is what makes that claim checkable.
