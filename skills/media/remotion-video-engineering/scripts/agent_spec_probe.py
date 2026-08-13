#!/usr/bin/env python
"""Measure where LLM agents break when authoring a JSON spec against a schema.

Purpose: decide guardrails from evidence instead of intuition. Run the same
tasks against the same models with two different briefs (v1 = current docs,
v2 = docs + explicit type rules) and compare clean-spec counts. If better docs
close the gap, do NOT remove capability from the agent.

Adapt SCHEMA_VALIDATOR, BRIEF_V1/V2, TASKS and semantic_checks() to your project.

Usage:
    python agent_spec_probe.py --models m1,m2 --brief v1
    python agent_spec_probe.py --models m1,m2 --brief v2

Then diff the two summaries.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import urllib.request

# --- project wiring -------------------------------------------------------
GATEWAY = "http://localhost:20128/v1/chat/completions"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# A validator that exits non-zero on an invalid spec and prints field paths.
SCHEMA_VALIDATOR = ["node", "validate_spec.mjs"]
VALIDATOR_CWD = PROJECT_ROOT / "remotion"
OUT_DIR = PROJECT_ROOT / "audit" / "probe_results"

MODELS = ["antigravity/gemini-3.6-flash-medium", "antigravity/gemini-3.6-flash-high"]

# --- the two briefs under test -------------------------------------------
BRIEF_V1 = """You author a VideoSpec JSON for a motion-graphics renderer.
(Insert the project's CURRENT instructions verbatim — this is the control.)
Return ONLY the JSON object, no prose, no markdown fence.
"""

# Same text plus explicit wrong/right pairs for the types agents get wrong.
# Abstract prose underperforms a visible contrast — show both forms.
BRIEF_V2 = BRIEF_V1 + """
TYPES THAT ARE EASY TO GET WRONG — read before writing:

1. statValue is a NUMBER, never a string. Units go in statSuffix.
   WRONG: "statValue": "6.8 GB"
   RIGHT: "statValue": 6.8, "statSuffix": " GB"

2. steps and nodes are arrays of OBJECTS, never arrays of strings.
   WRONG: "steps": ["A", "B"]
   RIGHT: "steps": [{"label": "A", "detail": "..."}]

3. cards is an array of OBJECTS with a required "title".
   WRONG: "cards": [{"label": "Before", "value": "10h"}]
   RIGHT: "cards": [{"title": "10h", "description": "manual", "tag": "BEFORE"}]

4. durationInFrames counts FRAMES, not seconds. At 60fps, 3 seconds = 180.
"""

TASKS = [
    {"name": "stat_scene",
     "prompt": "Show '7B model now fits in 6.8 GB of VRAM' as an animated counter. 3s at 60fps.",
     "expect_preset": "StatCounter"},
    {"name": "compare_scene",
     "prompt": "Compare 'needed a $5000 server' vs 'a laptop is enough' side by side. 4s at 60fps.",
     "expect_preset": "CompareSplit"},
    {"name": "flow_scene",
     "prompt": "Show 'text -> tokens -> vectors -> attention layers' as a pipeline. 4s at 60fps.",
     "expect_preset": "FlowDiagram"},
    {"name": "multi_scene",
     "prompt": "Three sentences, one scene each, each with a preset that fits its meaning. 3s per scene.",
     "expect_preset": None},
]


def call_model(model: str, prompt: str, brief: str, timeout: int = 180) -> str:
    """Call the gateway. Handles SSE, which some gateways return unconditionally."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": brief},
                     {"role": "user", "content": prompt}],
        "temperature": 0.3, "max_tokens": 3000,
    }).encode()
    req = urllib.request.Request(GATEWAY, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = resp.read().decode("utf-8", errors="replace")

    if not payload.lstrip().startswith("data:"):
        return json.loads(payload)["choices"][0]["message"]["content"] or ""

    parts: List[str] = []
    for line in payload.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if not chunk or chunk == "[DONE]":
            continue
        try:
            obj = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        for choice in obj.get("choices", []):
            piece = (choice.get("delta") or {}).get("content")
            if piece:
                parts.append(piece)
    return "".join(parts)


def extract_json(raw: str):
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    note = None
    if fenced:
        text, note = fenced.group(1).strip(), "wrapped_in_fence"
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None, "no_json_object"
    try:
        return json.loads(text[start:end + 1]), note
    except json.JSONDecodeError as exc:
        return None, f"json_decode_error: {exc.msg}"


def schema_validate(spec: Dict[str, Any]) -> tuple[bool, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUT_DIR / "_tmp_spec.json"
    tmp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    proc = subprocess.run(SCHEMA_VALIDATOR + [str(tmp)], capture_output=True,
                          text=True, cwd=str(VALIDATOR_CWD), timeout=120)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def semantic_checks(spec: Dict[str, Any], task: Dict[str, Any]) -> List[str]:
    """Errors a schema cannot express: right shape, wrong meaning."""
    issues: List[str] = []
    scenes = spec.get("scenes") or []
    if not scenes:
        return ["no_scenes"]

    needs = {"StatCounter": ["statValue"], "CompareSplit": ["cards"],
             "SwipePanels": ["cards"], "FlowDiagram": ["nodes", "steps"],
             "CodeReveal": ["code"], "LayerStack3D": ["layers"]}
    for i, sc in enumerate(scenes):
        preset = sc.get("preset")
        required = needs.get(preset)
        if required and not any(sc.get(k) for k in required):
            issues.append(f"scene{i}:{preset}_missing_data")
        if not sc.get("durationInFrames"):
            issues.append(f"scene{i}:missing_duration")
        if preset == "StatCounter" and isinstance(sc.get("statValue"), str):
            issues.append(f"scene{i}:statValue_is_string")

    exp = task.get("expect_preset")
    if exp and scenes[0].get("preset") != exp:
        issues.append(f"preset_mismatch(got={scenes[0].get('preset')},fit={exp})")
    if task["name"] == "multi_scene" and len({s.get("preset") for s in scenes}) == 1:
        issues.append("all_scenes_same_preset")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--brief", choices=["v1", "v2"], default="v1")
    args = ap.parse_args()

    brief = BRIEF_V1 if args.brief == "v1" else BRIEF_V2
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []

    for model in models:
        for task in TASKS:
            rec: Dict[str, Any] = {"model": model, "task": task["name"]}
            t0 = time.time()
            try:
                raw = call_model(model, task["prompt"], brief)
            except Exception as exc:  # noqa: BLE001 — report, keep sweeping
                rec.update(status="call_failed", error=str(exc)[:300])
                results.append(rec)
                print(f"[{model}/{task['name']}] CALL FAILED: {str(exc)[:120]}", flush=True)
                continue
            rec["latency_s"] = round(time.time() - t0, 1)

            spec, note = extract_json(raw)
            rec["parse_note"] = note
            if spec is None:
                rec["status"] = "parse_failed"
                results.append(rec)
                print(f"[{model}/{task['name']}] PARSE FAILED: {note}", flush=True)
                continue

            ok, detail = schema_validate(spec)
            rec["schema_ok"] = ok
            if not ok:
                rec["schema_error"] = detail[:600]
            rec["semantic_issues"] = semantic_checks(spec, task)
            rec["status"] = "ok" if (ok and not rec["semantic_issues"]) else "flawed"
            rec["spec"] = spec
            results.append(rec)
            print(f"[{'OK  ' if rec['status'] == 'ok' else 'FLAW'}] "
                  f"{model}/{task['name']} schema={ok} issues={rec['semantic_issues']}",
                  flush=True)

    out = OUT_DIR / f"probe_report_{args.brief}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out}\n\n=== SUMMARY (brief={args.brief}) ===")
    for model in models:
        rows = [r for r in results if r["model"] == model]
        print(f"{model}: {sum(1 for r in rows if r.get('status') == 'ok')}/{len(rows)} clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
