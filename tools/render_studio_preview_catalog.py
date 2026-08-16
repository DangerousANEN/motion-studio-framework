#!/usr/bin/env python3
"""Materialize all cacheable MSF Studio preview assets through the public panel API.

The Studio UI lazily renders scene thumbnails only when a card becomes visible.  This
one-off batch command warms that exact cache for the complete catalog and generates
an audition file for every usable voice, music bed, and SFX registered by the mixer.
It deliberately calls the same HTTP routes as Studio rather than duplicating
Remotion/TTS/audio implementation details.

Usage from the repository root:
    PYTHONPATH=. python3 tools/render_studio_preview_catalog.py

The command is sequential on purpose.  The resident RenderClient owns one Chromium
renderer; parallel requests would only contend for it and make errors hard to tie to
a specific preset.  A machine-readable report is written inside the ignored panel
cache under output/_panel_cache/batches/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "output" / "_panel_cache"
DEFAULT_BASE_URL = "http://127.0.0.1:8765"
VOICE_AUDITION = (
    "Проверяем голос в Motion Studio. Речь должна быть понятной, спокойной и "
    "естественной: этот фрагмент прозвучит в каталоге перед запуском рендера."
)


def _payload(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{response.request.method} {response.url}: non-JSON {response.status_code}") from exc
    if not response.ok:
        detail = data.get("detail", data) if isinstance(data, dict) else data
        raise RuntimeError(f"{response.request.method} {response.url}: HTTP {response.status_code}: {detail}")
    if not isinstance(data, dict):
        raise RuntimeError(f"{response.request.method} {response.url}: expected object payload")
    return data


def _get(session: requests.Session, base_url: str, route: str) -> dict[str, Any]:
    return _payload(session.get(f"{base_url}{route}", timeout=300))


def _post(session: requests.Session, base_url: str, route: str, body: dict[str, Any]) -> dict[str, Any]:
    return _payload(session.post(f"{base_url}{route}", json=body, timeout=600))


def _all_scenes(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    """Collect the full catalog despite its intentionally capped response size.

    `/api/studio/catalog` has no offset parameter and limits an individual response
    to 100 scenes.  Categories are an existing public catalog dimension, so querying
    each category retains the same production filtering/metadata contract and makes
    incomplete coverage a visible batch error instead of a silent omission.
    """
    offset = 0
    page_size = 100
    target: int | None = None
    by_name: dict[str, dict[str, Any]] = {}
    while target is None or offset < target:
        route = "/api/studio/catalog?" + urlencode({"limit": page_size, "offset": offset})
        page = _get(session, base_url, route)
        page_target = int(page.get("total") or 0)
        if target is None:
            target = page_target
        elif target != page_target:
            raise RuntimeError(f"catalog total changed during batch: {target} -> {page_target}")
        items = list(page.get("items") or [])
        if not items and offset < target:
            raise RuntimeError(f"catalog returned an empty page at offset {offset} before total {target}")
        for item in items:
            if item.get("name"):
                by_name[str(item["name"])] = item
        offset += len(items)
    if len(by_name) != target:
        raise RuntimeError(
            f"catalog coverage incomplete: found {len(by_name)} unique scenes, expected {target}; "
            "refusing to claim full preview coverage"
        )
    return [by_name[name] for name in sorted(by_name)]


def _record(
    report: dict[str, Any], kind: str, name: str, action,
) -> None:
    started = time.monotonic()
    try:
        result = action()
    except Exception as exc:  # report every individual element and continue the batch
        report["failures"].append({"kind": kind, "name": name, "error": str(exc)})
        print(f"FAIL  {kind:<10} {name}: {exc}", flush=True)
        return
    entry = {"name": name, "seconds": round(time.monotonic() - started, 2), **result}
    report["completed"].setdefault(kind, []).append(entry)
    cached = result.get("cached")
    suffix = " (cached)" if cached else ""
    print(f"OK    {kind:<10} {name}{suffix} · {entry['seconds']}s", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--skip-scenes", action="store_true")
    parser.add_argument("--skip-audio", action="store_true")
    parser.add_argument("--skip-voices", action="store_true")
    parser.add_argument("--skip-styles", action="store_true")
    parser.add_argument("--skip-transitions", action="store_true")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    started_at = datetime.now(UTC)
    report: dict[str, Any] = {
        "started_at": started_at.isoformat(),
        "base_url": base_url,
        "completed": {},
        "failures": [],
        "catalog": {},
    }

    with requests.Session() as session:
        # This starts no render; it verifies that the panel and the resident renderer
        # are reachable before a long batch begins.
        _get(session, base_url, "/api/render-server")

        if not args.skip_scenes:
            scenes = _all_scenes(session, base_url)
            report["catalog"]["scenes"] = len(scenes)
            print(f"Scenes: {len(scenes)}", flush=True)
            for number, scene in enumerate(scenes, start=1):
                name = str(scene["name"])
                print(f"[{number:03d}/{len(scenes):03d}] ", end="", flush=True)
                _record(
                    report,
                    "scene_thumbnail",
                    name,
                    lambda name=name: _post(
                        session, base_url, "/api/preview/thumbnail", {"preset": name, "demo_props": True}
                    ),
                )

        if not args.skip_voices:
            voice_catalog = _get(session, base_url, "/api/voices")
            voices = [item for item in voice_catalog.get("items", []) if item.get("usable")]
            report["catalog"]["usable_voices"] = len(voices)
            print(f"Usable voices: {len(voices)}", flush=True)
            for voice in voices:
                name = str(voice["key"])
                _record(
                    report,
                    "voice_audition",
                    name,
                    lambda name=name: _post(
                        session, base_url, "/api/preview/voice", {"voice": name, "text": VOICE_AUDITION}
                    ),
                )

        if not args.skip_audio:
            audio_catalog = _get(session, base_url, "/api/audio")
            music = list(audio_catalog.get("music") or [])
            sfx = list(audio_catalog.get("sfx") or [])
            report["catalog"]["music"] = len(music)
            report["catalog"]["sfx"] = len(sfx)
            print(f"Music beds: {len(music)} · SFX: {len(sfx)}", flush=True)
            for item in music:
                name = str(item["name"])
                _record(
                    report,
                    "music_audition",
                    name,
                    lambda name=name: _get(session, base_url, f"/api/preview/music/{name}?seconds=8"),
                )
            for item in sfx:
                name = str(item["name"])
                _record(
                    report,
                    "sfx_audition",
                    name,
                    lambda name=name: _get(session, base_url, f"/api/preview/sfx/{name}"),
                )

        # A style is shown on its own recommended real scene; a transition is
        # rendered over one shared base pair. Both outputs go through the same
        # cacheable public endpoints that Elements uses in-browser.
        styles = _get(session, base_url, "/api/studio/styles").get("families", [])
        effects = _get(session, base_url, "/api/effects")
        report["catalog"]["style_families"] = len(styles)
        report["catalog"]["transitions"] = len(effects.get("transitions") or [])
        known_scenes = {item.get("name") for item in (_all_scenes(session, base_url) if args.skip_scenes else scenes)}
        if not args.skip_styles:
            for style in styles:
                style_id = str(style.get("id") or "")
                candidates = [str(name) for name in style.get("recommended_scenes", []) if name in known_scenes]
                preset = candidates[0] if candidates else "HeroKinetic"
                _record(
                    report,
                    "style_scene_thumbnail",
                    style_id,
                    lambda style_id=style_id, preset=preset: _post(
                        session, base_url, "/api/preview/thumbnail",
                        {"preset": preset, "style": style_id, "demo_props": True, "scale": 0.22, "frame_pct": 0.78},
                    ),
                )
        if not args.skip_transitions:
            for transition in effects.get("transitions") or []:
                name = str(transition)
                _record(
                    report,
                    "transition_motion_preview",
                    name,
                    lambda name=name: _post(
                        session, base_url, "/api/preview/transition",
                        {"transition": name, "style": "llm_hubs_neon"},
                    ),
                )
        report["finished_at"] = datetime.now(UTC).isoformat()

    batch_dir = CACHE / "batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    output = batch_dir / f"studio_preview_batch_{started_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    completed = sum(len(items) for items in report["completed"].values())
    print(f"\nCompleted={completed} failures={len(report['failures'])} report={output}", flush=True)
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        print(f"Panel transport failure: {exc}", file=sys.stderr)
        raise SystemExit(2)
