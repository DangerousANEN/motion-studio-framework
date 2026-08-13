# Building a control panel over a generation pipeline

Use when the user asks for a web panel / dashboard to watch, inspect, or drive an existing
render pipeline ("нам надо сделать вебпанельку, чтобы я мог следить за процессом, видеть
какие голоса у нас есть, какие сцены, эффекты…").

Reference implementation: `msf/panel/` in motion-studio-framework — FastAPI + a single
dependency-free `app.js`, `python -m msf.panel.server` on :8765.

## Why the panel is the fix, not a nice-to-have

The request usually follows a run of "why is it only using N presets / the wrong voice".
Both were true because **the library was invisible**: 38 scene presets, 96 effects, 12
transitions, 38 SFX and 16 music beds, discoverable only by reading TypeScript. Nothing
displayed what existed versus what was in use, so a five-item hardcoded rotation and a
fallback voice ran for weeks unnoticed.

Treat the panel as an observability fix for that class of bug. Which dictates its design.

## Rule 1: a VIEW over the source, never a second catalogue

Every list must come from the same module the pipeline itself reads:

| section | source |
|---|---|
| scenes | the registry parser that the pipeline's rotation also uses |
| effects / transitions | same registry module, separate namespaces |
| voices | the voice registry via its own `describe_reference()` |
| SFX / music | the live `*_REGISTRY` dicts the mixer renders from |
| graph | the `add_node()` calls in the graph builder |

A panel with its own inventory becomes the drift problem it was built to expose. Tests
should assert each endpoint **against the registry modules**, not against expected counts —
a count baked into a test is stale on the next pack.

## Rule 2: show the distinction the user was burned by

Do not collapse near-synonyms into one badge. In this pipeline `rotation_safe` (13) and
"actually rotated" (8) differ because four presets render convincing fictional demo data.
The panel marks all three states — `в ротации`, `нужны данные`, `свой демо-контент` — and
that difference is the whole reason the user could not see the problem before.

Same for voices: `ICL` vs `x-vector` is the field that matters, because the degraded mode
is inaudible until a render finishes.

## Rule 3: previews go through the pipeline's own code paths

Scene stills through the existing stress/still harness, voice through the real synth
function, SFX/music through the audio module. If the panel has its own renderer, "it looked
fine in the panel" stops meaning anything.

Run the pipeline's **spec validator first** on any preview. A wrong row shape renders a red
whole-video ERROR card; without validation the panel displays that as a working preview.

Cost, measured: a scene still ≈13–40 s (the renderer rebuilds its bundle per invocation),
one TTS phrase ≈45 s (cold model load on CUDA), SFX and music beds instant (pure numpy).
Say so in the UI — a 40 s button with no explanation reads as broken.

## Rule 4: long jobs are subprocesses, drained by a thread

```python
proc = subprocess.Popen([sys.executable, runner, job_file], stdout=PIPE,
                        stderr=STDOUT, text=True, bufsize=1,
                        env={**os.environ, "PYTHONUNBUFFERED": "1"})
```

- **Subprocess, not a thread**: the job loads a 1.7B model onto CUDA and shells out to
  node and ffmpeg. In-process it blocks the event loop for minutes and an OOM takes the
  panel down. It also makes "kill this run" a real operation.
- **Drain stdout on a reader thread.** `readline()` on a blocking pipe waits for a line, so
  polling from the request handler hangs the HTTP request for the whole quiet stretch of a
  render — the panel looks frozen exactly when it matters. Guard the shared `Run` with a
  lock and have handlers return a snapshot.
- Give the runner a **parsed stdout contract** and document it in both files:
  `[<node>] done` per step, `OUTPUT: <abs path>` once on success, `ERROR: <msg>` on
  failure. Derive the step list from the graph builder, not a literal.
- The runner must **not** report success without checking the artefact exists. "Pipeline
  finished but no video exists at …" is the useful message.

## Rule 5: status checks must probe, not assert

A panel that prints "OK" without probing is worse than none — an unverified green is how
the broken voice reference survived. Each check returns `{name, ok, detail}` and `detail`
carries what was actually inspected (resolved binary path, parsed count, "exists"/"MISSING").
Test that no check has an empty `detail`.

## Rule 6: security, since there is no auth

Bound to 127.0.0.1, and say so in the README and in a `--host` warning. Preview endpoints
run node/ffmpeg, the run endpoint starts a render, and a voice-add endpoint writes files
into the repo — that is a code-execution surface.

File-serving routes take BOTH segments from the network, so whitelist the kind and confirm
the resolved path stays inside the cache directory:

```python
if kind not in ("scenes", "voice", "sfx", "music"):
    raise HTTPException(404, "unknown preview kind")
candidate = (CACHE / kind / filename).resolve()
if (CACHE / kind).resolve() not in candidate.parents or not candidate.is_file():
    raise HTTPException(404, "not found")
```

Assert traversal is blocked in tests (`../../../../Windows/win.ini`, `/preview/etc/passwd`).

## Rule 7: mutations enforce the invariant, not just the schema

The voice-add endpoint requires a transcript (`min_length`), rejects a reference under 4 s,
copies the wav into the repo's asset dir and stores a **repo-relative** path — an absolute
path into a cache dir is what broke voice synthesis in the first place. It also refuses to
delete the default entry. Invalidate any module-level cache the registry loader memoises,
or the new entry stays invisible until restart.

## The bug class this work generates: "plausible wrong answer"

Every panel bug found here succeeded and returned something false — no exception, no empty
result. Assume this shape and check the parsed value, not the status code.

| symptom | cause |
|---|---|
| every music bed described as `""` | read `BedSpec.summary`; the real fields are `character`/`use`/`bpm`/`key`. `getattr(x, "summary", "")` makes an absent field an empty string forever |
| graph shows 0 nodes, all node functions "unwired" | guessed the builder name; a `try/except AttributeError` returning `[]` turned a typo into a tidy wrong answer. Name candidates explicitly and error on empty |
| every scene preview at the same frame | passed `frame_pct` to a script that reads absolute `frame`; unknown keys are ignored |
| literal `null` on the page | `Node.replaceChildren()` **stringifies** `null`. Route top-level mounts through a helper that filters absent nodes |
| duplicate `media media` tag | pack name equals category name; also normalise `ui_mock` vs `ui-mock` before comparing |

## Frontend without a build step

Ship plain `index.html` + `app.js` inside the Python package: it must not need
`npm install` to open. A tiny `el(tag, attrs, ...kids)` helper plus `mount()` is enough for
seven views. `node --check app.js` after every edit — nested `el(...)` calls are easy to
mis-paren and the browser gives you a blank page.

Surface fetch failures as the **server's own error text**, never a generic message: a view
that renders an empty-but-tidy list when the backend is broken repeats the original sin.

## Verification loop that actually caught things

1. `TestClient(app)` over every endpoint — catches shape bugs in seconds.
2. Start the real server in the background, `curl` each route for a status code.
3. Drive it with the browser: click each nav item, then run a DOM probe for
   `innerText.includes('null')`, `.err` elements, and card counts per view.
4. Screenshot each view and read it — the duplicate tag and the literal `null` were only
   visible this way.
5. `browser_console` with no argument at the end: an empty `js_errors` list is part of the
   pass.
