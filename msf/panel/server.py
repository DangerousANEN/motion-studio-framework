"""MSF Control Panel — HTTP API over the pipeline's real registries.

WHY A PANEL EXISTS
------------------
Everything this serves was already in the repo and invisible. The library holds
38 scene presets, 96 effects, 12 transitions, 38 SFX and 12 music beds, and the
only way to know that was to read TypeScript. Which is how the pipeline shipped
for weeks using five presets and a voice nobody chose: nothing showed what was
available or what was actually being used.

So the panel is deliberately a VIEW OVER THE SOURCE, not a second catalogue:
every list comes from msf.registry (which parses the same TS the renderer
imports), msf.audio.sfx/music (the same dicts the mixer renders from) and
assets/voices/voices.json (the same file resolve_voice reads). There is no
duplicated inventory to drift. If the panel shows it, the renderer can render it.

WHAT IT DOES NOT DO
-------------------
No authentication. It binds 127.0.0.1 by default and MUST NOT be exposed: the
preview endpoints run node and ffmpeg subprocesses, and /api/graph/run starts a
full render. Binding this to 0.0.0.0 hands anyone on the network a code-execution
surface. `--host` is accepted for local debugging only and warns loudly.

RUN
---
    python -m msf.panel.server            # http://127.0.0.1:8765
    python -m msf.panel.server --port 9000
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

REPO = Path(__file__).resolve().parents[2]
REMOTION = REPO / "remotion"
PANEL_DIR = Path(__file__).resolve().parent
STATIC_DIR = PANEL_DIR / "static"

# Preview artefacts. Kept out of output/ so a cleanup of renders cannot delete
# the cache and vice versa.
CACHE = REPO / "output" / "_panel_cache"
CACHE.mkdir(parents=True, exist_ok=True)

log = logging.getLogger("msf.panel")

app = FastAPI(title="MSF Control Panel", version="1.0")

# Same-origin in normal use; permissive only for localhost dev tooling.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- catalogue

@app.get("/api/scenes")
def api_scenes() -> Dict[str, Any]:
    """Every scene preset, with the flags that decide whether agents can use it.

    `rotation_safe` and `rotation_used` are DIFFERENT and the distinction is the
    whole point of this view: a preset can be safe for rotation yet still be
    excluded because it renders invented content (ScoreHud's PLAYER 1 / 9750).
    Showing only one flag is what let eight usable presets sit unnoticed.
    """
    from msf import registry
    from msf.graph import video_graph

    used = set(video_graph._TEXT_SAFE_PRESETS)
    blocked = set(getattr(video_graph, "_ROTATION_BLOCKLIST", frozenset()))

    items = []
    for info in sorted(registry.load_registry().values(), key=lambda p: p.name):
        items.append({
            "name": info.name,
            "category": info.category,
            "summary": info.summary,
            "fields": list(info.fields),
            "data_driven": info.data_driven,
            "three": info.three,
            "pack": info.pack,
            "rotation_safe": info.rotation_safe,
            "rotation_used": info.name in used,
            "rotation_blocked": info.name in blocked,
        })
    return {
        "total": len(items),
        "rotation_used": sorted(used),
        "categories": registry.by_category(),
        "items": items,
    }


@app.get("/api/effects")
def api_effects() -> Dict[str, Any]:
    """Effects and transitions, kept apart because they are not interchangeable.

    A transition name in a scene's `effects` list is skipped with a console
    warning — EffectStack only resolves the three effect registries.
    """
    from msf import registry

    return {
        "effects": [
            {
                "name": e.name,
                "family": e.family,
                "summary": e.summary,
                "stochastic": e.stochastic,
                "pack": e.pack,
            }
            for e in sorted(registry.load_effects().values(), key=lambda x: x.name)
        ],
        "by_family": registry.effects_by_family(),
        "transitions": registry.transition_names(),
    }


@app.get("/api/voices")
def api_voices() -> Dict[str, Any]:
    """The voice registry, with the cloning mode each entry will ACTUALLY get.

    `mode` is the field that matters. A reference without a transcript silently
    degrades to x-vector (timbre copied, prosody flat), which is the difference
    between a natural read and the robotic one. describe_reference() reports it
    rather than leaving it to be discovered by ear.
    """
    from msf.skills_bridge.qwen3_tts import DEFAULT_VOICE, describe_reference, load_voices

    voices = []
    for key, entry in sorted(load_voices().items()):
        if key.startswith("_"):
            continue
        try:
            info = describe_reference(key)
        except Exception as exc:  # a broken entry must be visible, not fatal
            voices.append({"key": key, "error": str(exc), "usable": False})
            continue
        voices.append({
            "key": key,
            "ref_audio": info.get("ref_audio"),
            "exists": info.get("exists"),
            "duration_sec": info.get("duration_sec"),
            "sample_rate": info.get("sample_rate"),
            "has_ref_text": info.get("has_ref_text"),
            "mode": info.get("mode"),
            "icl": bool(info.get("has_ref_text")),
            "lang": entry.get("lang"),
            "notes": entry.get("notes"),
            "ref_text": entry.get("ref_text"),
            "is_default": key == DEFAULT_VOICE,
            "usable": bool(info.get("exists")),
        })

    from msf.config import MSFConfig

    cfg = MSFConfig()
    return {
        "default": DEFAULT_VOICE,
        "configured": cfg.tts.speaker,
        "configured_is_valid": any(v["key"] == cfg.tts.speaker for v in voices),
        "items": voices,
    }


@app.get("/api/audio")
def api_audio() -> Dict[str, Any]:
    """SFX and music beds, read from the same registries the mixer renders from."""
    from msf.audio import music as music_mod
    from msf.audio import sfx as sfx_mod

    sfx_items = [
        {
            "name": s.name,
            "family": s.family,
            "max_ms": s.max_ms,
            "summary": s.summary,
            "loop": s.loop,
            "peak_db": s.peak_db,
        }
        for s in sorted(sfx_mod.SFX_REGISTRY.values(), key=lambda x: (x.family, x.name))
    ]
    # BedSpec carries bpm/key/character/use — not `summary`. Reading a field that
    # does not exist would silently render every bed with an empty description.
    beds = [
        {
            "name": b.name,
            "bpm": b.bpm,
            "key": b.key,
            "character": b.character,
            "use": b.use,
            "peak_db": b.peak_db,
        }
        for b in sorted(music_mod.MUSIC_REGISTRY.values(), key=lambda x: x.name)
    ]
    return {"sfx": sfx_items, "music": beds}


@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    """One place to see whether the moving parts are actually reachable.

    Every check reports what was verified. A panel that says "OK" without probing
    is worse than no panel — the whole reason the pipeline shipped with a broken
    voice reference is that nothing checked the file existed.
    """
    from msf import registry
    from msf.config import MSFConfig
    from msf.skills_bridge.qwen3_tts import DEFAULT_VOICE, describe_reference

    cfg = MSFConfig()
    checks: List[Dict[str, Any]] = []

    presets = registry.load_registry()
    checks.append({
        "name": "scene registry",
        "ok": len(presets) > 20,
        "detail": f"{len(presets)} presets parsed from remotion/src/registry",
    })

    effects = registry.load_effects()
    checks.append({
        "name": "effect registry",
        "ok": len(effects) > 50,
        "detail": f"{len(effects)} effects, {len(registry.transition_names())} transitions",
    })

    try:
        info = describe_reference(None)
        checks.append({
            "name": f"default voice ({DEFAULT_VOICE})",
            "ok": bool(info.get("exists")) and bool(info.get("has_ref_text")),
            "detail": f"{info.get('mode')} — {Path(str(info.get('ref_audio'))).name}",
        })
    except Exception as exc:
        checks.append({"name": "default voice", "ok": False, "detail": str(exc)})

    checks.append({
        "name": "configured speaker",
        "ok": True,
        "detail": f"tts.speaker={cfg.tts.speaker}",
    })

    checks.append({
        "name": "node + remotion",
        "ok": bool(shutil.which("node")) and (REMOTION / "node_modules").is_dir(),
        "detail": f"node={shutil.which('node') or 'MISSING'}; "
                  f"node_modules={'present' if (REMOTION / 'node_modules').is_dir() else 'MISSING'}",
    })

    checks.append({
        "name": "ffmpeg",
        "ok": bool(shutil.which("ffmpeg")),
        "detail": shutil.which("ffmpeg") or "MISSING — audio mastering will fail",
    })

    # LDR is fail-closed by design: report it, do not run a query here.
    from msf.skills_bridge import deep_research as dr

    checks.append({
        "name": "LDR work dir",
        "ok": dr.LDR_WORK.is_dir(),
        "detail": f"{dr.LDR_WORK} ({'exists' if dr.LDR_WORK.is_dir() else 'MISSING'})",
    })
    checks.append({
        "name": "LDR python",
        "ok": Path(dr.LDR_PYTHON).is_file(),
        "detail": f"{dr.LDR_PYTHON} ({'exists' if Path(dr.LDR_PYTHON).is_file() else 'MISSING'})",
    })

    return {
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "llm": {"base_url": cfg.llm.base_url, "model": cfg.llm.model},
        "render": {"fps": cfg.render.fps, "width": cfg.render.width, "height": cfg.render.height},
    }


# ---------------------------------------------------------------- previews
#
# Every preview renders through the SAME code path the pipeline uses — the panel
# must not have its own renderer, or "it looked fine in the panel" stops meaning
# anything. Scene stills go through remotion/scripts/stress.mjs (the existing
# harness), audio goes through msf.audio.sfx/music, voice through
# synthesize_voice_clone.


class ScenePreviewRequest(BaseModel):
    preset: str
    props: Dict[str, Any] = Field(default_factory=dict)
    frame_pct: float = Field(0.9, ge=0.0, le=1.0)
    duration_frames: int = Field(180, ge=30, le=1800)
    style: str = "pop"


@app.post("/api/preview/scene")
def api_preview_scene(req: ScenePreviewRequest) -> Dict[str, Any]:
    """Render one still of a preset and return a URL to the PNG.

    Validates through msf.spec.validate_spec FIRST. Without that, a preset given
    the wrong row shape renders the red whole-video ERROR card and the panel would
    happily display it as a preview of a working scene.
    """
    from msf import registry
    from msf.spec import validate_spec

    if req.preset not in registry.load_registry():
        raise HTTPException(404, f"unknown preset {req.preset!r}")

    scene: Dict[str, Any] = {
        "id": "preview",
        "durationInFrames": req.duration_frames,
        "preset": req.preset,
        **req.props,
    }
    spec = {
        "width": 1080, "height": 1920, "fps": 60,
        "durationInFrames": req.duration_frames,
        "style": req.style, "scenes": [scene],
    }
    warnings: List[str] = []
    try:
        validate_spec(spec)
    except ValueError as exc:
        # A real validation failure is the useful answer, not a red card.
        raise HTTPException(422, str(exc)) from exc

    token = uuid.uuid4().hex[:12]
    out_dir = CACHE / "scenes"
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = REMOTION / f".panel_{token}.json"
    # stress.mjs takes an absolute FRAME (`c.frame`), not a percentage, and its
    # outDir is resolved relative to the remotion root. Passing `frame_pct`
    # through would be silently ignored and every preview would render the
    # script's own 90% default.
    frame = max(0, min(req.duration_frames - 1, round(req.duration_frames * req.frame_pct)))
    cases.write_text(
        json.dumps(
            [{"name": token, "frame": frame, "style": req.style, "scene": scene}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rel_out = "../output/_panel_cache/scenes"
    node = shutil.which("node")
    if not node:
        cases.unlink(missing_ok=True)
        raise HTTPException(503, "node not found — cannot render scene previews")
    try:
        proc = subprocess.run(
            [node, "scripts/stress.mjs", str(cases.name), rel_out],
            cwd=REMOTION, capture_output=True, text=True, timeout=420,
        )
        png = out_dir / f"{token}.png"
        if proc.returncode != 0 or not png.is_file():
            raise HTTPException(
                500,
                "render failed: " + ((proc.stdout or "") + (proc.stderr or ""))[-600:],
            )
    finally:
        cases.unlink(missing_ok=True)

    return {
        "url": f"/preview/scenes/{token}.png",
        "preset": req.preset,
        "frame": frame,
        "frame_pct": req.frame_pct,
        "warnings": warnings,
    }


class VoicePreviewRequest(BaseModel):
    voice: Optional[str] = None
    text: str = Field(
        "Открытые модели догнали закрытые по длине контекста и по цене.",
        min_length=1, max_length=400,
    )


@app.post("/api/preview/voice")
def api_preview_voice(req: VoicePreviewRequest) -> Dict[str, Any]:
    """Synthesize a line so a voice can be HEARD before a 3-minute render uses it.

    This is the check that was missing: the pipeline ran for weeks on a fallback
    female voice because nothing ever played a sample.
    """
    from msf.skills_bridge.qwen3_tts import describe_reference, synthesize_voice_clone

    try:
        info = describe_reference(req.voice)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    if not info.get("exists"):
        raise HTTPException(422, f"reference audio missing: {info.get('ref_audio')}")

    out_dir = CACHE / "voice"
    out_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex[:12]
    dst = out_dir / f"{token}.wav"
    started = time.time()
    try:
        _, duration = synthesize_voice_clone(
            text=req.text, voice=req.voice, output_path=str(dst)
        )
    except Exception as exc:
        raise HTTPException(500, f"synthesis failed: {exc}") from exc

    return {
        "url": f"/preview/voice/{token}.wav",
        "voice": req.voice or "(registry default)",
        "mode": info.get("mode"),
        "icl": bool(info.get("has_ref_text")),
        "duration_sec": round(duration, 2),
        "synth_sec": round(time.time() - started, 1),
    }


@app.get("/api/preview/sfx/{name}")
def api_preview_sfx(name: str) -> Dict[str, Any]:
    """Render one SFX to a wav. Same synth the mixer uses, so it sounds identical."""
    from msf.audio import sfx as sfx_mod

    if name not in sfx_mod.SFX_REGISTRY:
        raise HTTPException(404, f"unknown sfx {name!r}")
    out_dir = CACHE / "sfx"
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{name}.wav"
    if not dst.is_file():
        wav = sfx_mod.render(name)
        _write_wav(dst, wav, sfx_mod.SR)
    return {"url": f"/preview/sfx/{name}.wav", "name": name}


@app.get("/api/preview/music/{name}")
def api_preview_music(name: str, seconds: float = 8.0) -> Dict[str, Any]:
    """Render a short excerpt of a music bed.

    Uses loop_bed(), the same function node_soundtrack uses to fill a timeline.
    render_bed() alone would produce the bed's natural length (often a couple of
    bars) and its decaying tail, which is not what a viewer hears under a video.
    """
    from msf.audio import music as music_mod

    if name not in music_mod.MUSIC_REGISTRY:
        raise HTTPException(404, f"unknown bed {name!r}")
    seconds = max(2.0, min(30.0, seconds))
    out_dir = CACHE / "music"
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{name}_{int(seconds)}s.wav"
    if not dst.is_file():
        wav = music_mod.loop_bed(name, seconds)
        _write_wav(dst, wav, music_mod.SR)
    return {"url": f"/preview/music/{dst.name}", "name": name, "seconds": seconds}


def _write_wav(path: Path, wav, sr: int) -> None:
    """Write float32 mono to 16-bit PCM."""
    import wave as wave_mod

    import numpy as np

    a = np.asarray(wav, dtype="float32")
    if a.ndim > 1:
        a = a.mean(axis=1)
    peak = float(abs(a).max()) if a.size else 0.0
    if peak > 1.0:
        a = a / peak
    pcm = (a * 32767).astype("int16")
    with wave_mod.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


@app.get("/preview/{kind}/{filename}")
def serve_preview(kind: str, filename: str) -> FileResponse:
    """Serve a cached preview artefact.

    Both components are validated against a whitelist and checked to resolve
    INSIDE the cache: `kind`/`filename` come from the network, and a naive join
    would let `../../..` read any file the process can reach.
    """
    if kind not in ("scenes", "voice", "sfx", "music"):
        raise HTTPException(404, "unknown preview kind")
    candidate = (CACHE / kind / filename).resolve()
    root = (CACHE / kind).resolve()
    if root not in candidate.parents or not candidate.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(candidate)


# ---------------------------------------------------------------- LDR / graph


@app.get("/api/ldr")
def api_ldr() -> Dict[str, Any]:
    """LDR wiring, reported without running a query.

    LDR is fail-closed: node_deep_research raises rather than inventing facts. So
    the useful thing to show is whether it COULD run, and the last raw result.
    """
    from msf.skills_bridge import deep_research as dr

    last = dr.LDR_WORK / "ldr_last_raw.json"
    info: Dict[str, Any] = {
        "work_dir": str(dr.LDR_WORK),
        "work_dir_exists": dr.LDR_WORK.is_dir(),
        "python": str(dr.LDR_PYTHON),
        "python_exists": Path(dr.LDR_PYTHON).is_file(),
        "runner": dr.LDR_RUNNER,
        "runner_exists": (dr.LDR_WORK / dr.LDR_RUNNER).is_file(),
        "searxng_url": dr.SEARXNG_URL,
        "last_result_at": None,
        "last_result_preview": None,
    }
    if last.is_file():
        info["last_result_at"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(last.stat().st_mtime)
        )
        try:
            info["last_result_preview"] = json.loads(last.read_text(encoding="utf-8"))
        except Exception as exc:
            info["last_result_preview"] = {"parse_error": str(exc)}
    try:
        dr.check_searxng()
        info["searxng_ok"] = True
        info["searxng_detail"] = "reachable"
    except Exception as exc:
        info["searxng_ok"] = False
        info["searxng_detail"] = str(exc)[:200]
    return info


@dataclass
class Run:
    """One pipeline run, tracked so the panel can show progress instead of a spinner."""

    run_id: str
    topic: str
    started: float
    status: str = "running"
    node: Optional[str] = None
    log: List[str] = field(default_factory=list)
    error: Optional[str] = None
    output_path: Optional[str] = None
    proc: Optional[subprocess.Popen] = None
    reader: Optional[threading.Thread] = None
    lock: threading.Lock = field(default_factory=threading.Lock)


RUNS: Dict[str, Run] = {}


def _start_reader(r: Run) -> None:
    """Drain the child's stdout on a thread.

    NOT in the request handler. `proc.stdout.readline()` on a blocking pipe waits
    until a line arrives, so polling from /api/runs would hang the HTTP request for
    as long as the child is quiet — and during a Remotion render that is minutes.
    The panel would look frozen at exactly the moment it is most needed.
    """

    def pump() -> None:
        assert r.proc is not None and r.proc.stdout is not None
        for raw in r.proc.stdout:
            line = raw.rstrip()
            with r.lock:
                r.log.append(line)
                # The runner prints `[<node>] done` per node, `OUTPUT: <path>` on
                # success and `ERROR: ...` on failure — see msf/panel/run_job.py.
                if line.startswith("[") and "]" in line:
                    name = line[1:line.index("]")]
                    if name in _node_names() or name == "start":
                        r.node = name
                elif line.startswith("OUTPUT: "):
                    r.output_path = line[len("OUTPUT: "):].strip()
                elif line.startswith("ERROR: "):
                    r.error = line[len("ERROR: "):].strip()
        rc = r.proc.wait()
        with r.lock:
            if r.status == "running":
                r.status = "done" if rc == 0 else "failed"
            if rc != 0 and not r.error:
                r.error = f"exit code {rc}; last log: " + " | ".join(r.log[-3:])

    r.reader = threading.Thread(target=pump, daemon=True, name=f"run-{r.run_id}")
    r.reader.start()


def _snapshot(r: Run) -> Dict[str, Any]:
    with r.lock:
        return {
            "run_id": r.run_id,
            "topic": r.topic,
            "status": r.status,
            "node": r.node,
            "started": time.strftime("%H:%M:%S", time.localtime(r.started)),
            "elapsed_sec": round(time.time() - r.started, 1),
            "error": r.error,
            "output_path": r.output_path,
            "log_lines": len(r.log),
        }


@app.get("/api/runs")
def api_runs() -> Dict[str, Any]:
    """Every run this server started, newest first."""
    return {"runs": [_snapshot(r) for r in sorted(RUNS.values(), key=lambda x: -x.started)]}


@app.get("/api/runs/{run_id}")
def api_run_detail(run_id: str, tail: int = 200) -> Dict[str, Any]:
    r = RUNS.get(run_id)
    if not r:
        raise HTTPException(404, "unknown run")
    out = _snapshot(r)
    with r.lock:
        out["log"] = r.log[-max(1, min(tail, 2000)):]
    return out


# Graph node names, in execution order, so the UI can show a real progress trail
# rather than a spinner.
#
# DERIVED, NOT LISTED. A hardcoded list drifted immediately: the graph registers
# "build_spec" -> node_build_remotion_spec and "render" -> node_remotion_render,
# so a `hasattr(video_graph, "node_build_spec")` check reported both as MISSING
# while they were present and working. Reading the add_node() calls gives the
# registered names AND their order from the one place that defines them.
#
# The builder is `build_msf_graph`. Guessing `build_video_graph` from the module
# name returned an empty node list and flagged all ten node functions as unwired —
# a "helpful" try/except turned a typo into a plausible-looking wrong answer, so
# the candidates are explicit and an empty result is reported as an error.
_GRAPH_BUILDERS = ("build_msf_graph", "build_video_graph")


def _graph_nodes() -> List[Dict[str, str]]:
    import inspect
    import re as _re

    from msf.graph import video_graph

    for builder_name in _GRAPH_BUILDERS:
        builder = getattr(video_graph, builder_name, None)
        if builder is None:
            continue
        try:
            src = inspect.getsource(builder)
        except (OSError, TypeError):
            continue
        nodes = [
            {"name": m.group(1), "fn": m.group(2)}
            for m in _re.finditer(
                r'add_node\(\s*"([^"]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)', src
            )
        ]
        if nodes:
            return nodes
    return []


@app.get("/api/graph")
def api_graph() -> Dict[str, Any]:
    """The pipeline's shape, read from the graph builder rather than duplicated."""
    from msf.graph import video_graph

    nodes = _graph_nodes()
    if not nodes:
        # Do not pretend the pipeline has no nodes.
        raise HTTPException(
            500,
            "could not read the graph: none of "
            f"{_GRAPH_BUILDERS} yielded add_node() calls in msf/graph/video_graph.py",
        )
    wired = {n["fn"] for n in nodes}
    orphans = [
        name for name in dir(video_graph)
        if name.startswith("node_") and name not in wired
    ]
    return {
        "nodes": [n["name"] for n in nodes],
        "node_functions": nodes,
        "unwired_functions": sorted(orphans),
        "rotation_presets": video_graph._TEXT_SAFE_PRESETS,
        "data_driven_count": len(video_graph._DATA_DRIVEN_PRESETS),
        "allowed_presets": len(video_graph.ALLOWED_PRESETS),
    }


@lru_cache(maxsize=1)
def _node_names() -> tuple:
    return tuple(n["name"] for n in _graph_nodes())


class VoiceAddRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=48)
    ref_audio: str = Field(..., description="Path to a wav on this machine")
    ref_text: str = Field(
        ..., min_length=10,
        description="VERBATIM transcript of ref_audio. Required — without it ICL is off.",
    )
    lang: str = "ru"
    notes: str = ""


@app.post("/api/voices")
def api_add_voice(req: VoiceAddRequest) -> Dict[str, Any]:
    """Register a new cloning reference in assets/voices/voices.json.

    The transcript is MANDATORY, not optional. resolve_voice() returns ref_text=None
    for an entry without one, which flips the model to x_vector_only_mode: timbre
    copied, prosody flat. That failure is inaudible until you hear the render, so
    the API refuses to create an entry that would silently degrade.

    The wav is copied into assets/voices/refs/ and the registry stores a
    repo-relative path, so the project stays portable — an absolute path into a
    cache directory is exactly what broke voice synthesis before.
    """
    import re as _re

    import soundfile as sf

    from msf.skills_bridge import qwen3_tts

    if not _re.fullmatch(r"[A-Za-z0-9_-]+", req.key):
        raise HTTPException(422, "key must be [A-Za-z0-9_-]+")
    if req.key.startswith("_"):
        raise HTTPException(422, "keys starting with _ are reserved for metadata")

    src = Path(req.ref_audio).expanduser()
    if not src.is_file():
        raise HTTPException(404, f"reference audio not found: {src}")

    try:
        meta = sf.info(str(src))
    except Exception as exc:
        raise HTTPException(422, f"not a readable audio file: {exc}") from exc
    # Qwen3-TTS clones from a few seconds of speech. Too short and the timbre is
    # unstable; report it rather than let the user discover it in a render.
    if meta.duration < 4.0:
        raise HTTPException(
            422,
            f"reference is {meta.duration:.1f}s — too short for stable cloning "
            "(use at least 4s, ideally 8-20s of clean speech)",
        )

    voices_path = REPO / "assets" / "voices" / "voices.json"
    registry_data: Dict[str, Any] = {}
    if voices_path.is_file():
        registry_data = json.loads(voices_path.read_text(encoding="utf-8"))
    if req.key in registry_data:
        raise HTTPException(409, f"voice {req.key!r} already exists")

    refs_dir = REPO / "assets" / "voices" / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)
    dst = refs_dir / f"{req.key}_{int(meta.samplerate / 1000)}k{src.suffix}"
    if dst.resolve() != src.resolve():
        shutil.copy2(src, dst)

    registry_data[req.key] = {
        "ref_audio": str(dst.relative_to(REPO)).replace("\\", "/"),
        "ref_text": req.ref_text.strip(),
        "lang": req.lang,
        "notes": req.notes or f"added via panel ({meta.duration:.1f}s, {meta.samplerate}Hz)",
    }
    voices_path.write_text(
        json.dumps(registry_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # load_voices() memoises in a module global; a stale cache would make the new
    # voice invisible until restart.
    qwen3_tts._VOICES_CACHE = None

    info = qwen3_tts.describe_reference(req.key)
    return {
        "key": req.key,
        "ref_audio": registry_data[req.key]["ref_audio"],
        "duration_sec": round(meta.duration, 2),
        "sample_rate": meta.samplerate,
        "mode": info.get("mode"),
        "icl": bool(info.get("has_ref_text")),
    }


@app.delete("/api/voices/{key}")
def api_delete_voice(key: str) -> Dict[str, Any]:
    """Remove a voice from the registry. The wav file is left on disk."""
    from msf.skills_bridge import qwen3_tts

    if key == qwen3_tts.DEFAULT_VOICE:
        raise HTTPException(
            409,
            f"{key!r} is DEFAULT_VOICE — deleting it would make resolve_voice(None) "
            "fall through to a reference with no transcript, disabling ICL.",
        )
    voices_path = REPO / "assets" / "voices" / "voices.json"
    data = json.loads(voices_path.read_text(encoding="utf-8")) if voices_path.is_file() else {}
    if key not in data:
        raise HTTPException(404, f"unknown voice {key!r}")
    data.pop(key)
    voices_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    qwen3_tts._VOICES_CACHE = None
    return {"removed": key}


class RunRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=400)
    text: Optional[str] = None
    preset: str = "HeroKinetic"
    voice: Optional[str] = None
    scenes: int = Field(4, ge=1, le=20)
    agent_level: int = Field(3, ge=1, le=5)
    research: bool = False


@app.post("/api/graph/run")
def api_graph_run(req: RunRequest) -> Dict[str, Any]:
    """Start a pipeline run as a subprocess and return its id.

    A SUBPROCESS, not a thread: the graph loads a 1.7B TTS model onto CUDA and
    shells out to Remotion and ffmpeg. In-process it would block the event loop
    for minutes and a crash would take the panel down with it.
    """
    from msf import registry

    if req.preset not in registry.load_registry():
        raise HTTPException(404, f"unknown preset {req.preset!r}")
    if req.voice:
        from msf.skills_bridge.qwen3_tts import load_voices

        if req.voice not in load_voices():
            raise HTTPException(404, f"unknown voice {req.voice!r}")

    run_id = uuid.uuid4().hex[:12]
    payload = {
        "topic": req.topic,
        "text": req.text,
        "preset": req.preset,
        "voice": req.voice,
        "scenes": req.scenes,
        "agent_level": req.agent_level,
        "research": req.research,
        "run_id": run_id,
    }
    job = CACHE / "runs"
    job.mkdir(parents=True, exist_ok=True)
    job_file = job / f"{run_id}.json"
    job_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    runner = PANEL_DIR / "run_job.py"
    proc = subprocess.Popen(
        [sys.executable, str(runner), str(job_file)],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    RUNS[run_id] = Run(run_id=run_id, topic=req.topic, started=time.time(), proc=proc)
    _start_reader(RUNS[run_id])
    return {"run_id": run_id, "status": "running"}


@app.post("/api/runs/{run_id}/kill")
def api_kill_run(run_id: str) -> Dict[str, Any]:
    r = RUNS.get(run_id)
    if not r:
        raise HTTPException(404, "unknown run")
    if r.proc and r.proc.poll() is None:
        r.proc.terminate()
        with r.lock:
            r.status = "killed"
    return {"run_id": run_id, "status": r.status}


# ---------------------------------------------------------------- static UI


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html = STATIC_DIR / "index.html"
    if not html.is_file():
        raise HTTPException(500, f"UI missing: {html}")
    return HTMLResponse(html.read_text(encoding="utf-8"))


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="MSF control panel")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    if args.host not in ("127.0.0.1", "localhost"):
        log.warning(
            "Binding %s exposes unauthenticated endpoints that run node/ffmpeg "
            "subprocesses and start renders. Do not do this on a shared network.",
            args.host,
        )

    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
