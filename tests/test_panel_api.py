"""Panel API tests: the panel must never show a catalogue the renderer disagrees with.

WHY THIS EXISTS
---------------
The panel's whole purpose is to stop the pipeline from silently using a fraction of
its library. If the panel itself reports numbers from a second, drifting source, it
becomes the problem it was built to solve. So every catalogue endpoint is asserted
against the registry modules, not against a hardcoded expected count.

Bugs this caught while it was being written:
  * /api/audio read `bed.summary` — BedSpec has no such field, so every music bed
    would have rendered with an empty description.
  * /api/graph guessed the builder name `build_video_graph`; the real one is
    `build_msf_graph`, so it reported ZERO nodes and flagged all ten node
    functions as "unwired".
  * /api/preview/scene passed `frame_pct` to stress.mjs, which reads `frame` —
    the parameter was silently ignored.

Preview endpoints that render (scene stills, TTS) are exercised in a separate
opt-in test: one costs ~15s of node, the other ~45s of GPU.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from msf import registry
from msf.panel.server import app

client = TestClient(app)


# --------------------------------------------------------------------- scenes

def test_scenes_match_the_registry_exactly() -> None:
    d = client.get("/api/scenes").json()
    assert d["total"] == len(registry.load_registry())
    assert {i["name"] for i in d["items"]} == set(registry.preset_names())


def test_scene_flags_are_not_invented() -> None:
    d = client.get("/api/scenes").json()
    reg = registry.load_registry()
    for item in d["items"]:
        info = reg[item["name"]]
        assert item["data_driven"] == info.data_driven
        assert item["category"] == info.category
        assert set(item["fields"]) == set(info.fields)


def test_rotation_used_is_what_the_graph_actually_rotates() -> None:
    """The panel must show the graph's real rotation list, not `rotation_safe`.

    Those differ by design — ScoreHud is safe but excluded because it renders
    invented content — and conflating them is what hid the problem originally.
    """
    from msf.graph import video_graph

    d = client.get("/api/scenes").json()
    assert set(d["rotation_used"]) == set(video_graph._TEXT_SAFE_PRESETS)
    used = {i["name"] for i in d["items"] if i["rotation_used"]}
    assert used == set(video_graph._TEXT_SAFE_PRESETS)


def test_blocked_presets_are_marked_and_excluded() -> None:
    d = client.get("/api/scenes").json()
    blocked = {i["name"] for i in d["items"] if i["rotation_blocked"]}
    assert "ScoreHud" in blocked and "BankCard" in blocked
    assert not (blocked & set(d["rotation_used"])), "a blocked preset is in rotation"


def test_scene_rotation_list_is_not_the_old_five() -> None:
    d = client.get("/api/scenes").json()
    assert len(d["rotation_used"]) > 5


# -------------------------------------------------------------------- effects

def test_effects_match_the_registry_and_exclude_transitions() -> None:
    d = client.get("/api/effects").json()
    assert {e["name"] for e in d["effects"]} == set(registry.load_effects())
    assert d["transitions"] == registry.transition_names()
    assert not (set(d["transitions"]) & {e["name"] for e in d["effects"]})


def test_no_effect_has_an_unknown_family() -> None:
    d = client.get("/api/effects").json()
    assert [e["name"] for e in d["effects"] if e["family"] == "unknown"] == []


# --------------------------------------------------------------------- voices

def test_voices_report_the_cloning_mode_each_will_get() -> None:
    """`icl` is the field that matters: False means flat prosody, silently."""
    d = client.get("/api/voices").json()
    assert d["items"], "voice registry is empty"
    for v in d["items"]:
        assert "mode" in v and v["mode"]
        assert v["icl"] == bool(v["has_ref_text"])


def test_configured_speaker_validity_is_reported() -> None:
    d = client.get("/api/voices").json()
    keys = {v["key"] for v in d["items"]}
    assert d["configured_is_valid"] == (d["configured"] in keys)
    assert d["configured_is_valid"], (
        f"config tts.speaker={d['configured']!r} is not in the registry — synthesis "
        "would fall back to a different (female) voice"
    )


def test_default_voice_is_flagged_exactly_once() -> None:
    d = client.get("/api/voices").json()
    assert sum(1 for v in d["items"] if v["is_default"]) == 1


# ---------------------------------------------------------------------- audio

def test_audio_lists_every_registered_sfx_and_bed_with_real_metadata() -> None:
    from msf.audio import music as music_mod
    from msf.audio import sfx as sfx_mod

    d = client.get("/api/audio").json()
    assert {s["name"] for s in d["sfx"]} == set(sfx_mod.SFX_REGISTRY)
    assert {b["name"] for b in d["music"]} == set(music_mod.MUSIC_REGISTRY)
    # BedSpec has no `summary`; the fields below are the ones that exist.
    for b in d["music"]:
        assert b["character"], f"{b['name']}: empty character"
        assert b["use"], f"{b['name']}: empty use"
        assert b["bpm"] > 0
    for s in d["sfx"]:
        assert s["summary"], f"{s['name']}: empty summary"


def test_sfx_and_music_previews_produce_real_audio() -> None:
    """Cheap to render (pure numpy), so always checked."""
    import wave

    from msf.panel.server import CACHE

    r = client.get("/api/preview/sfx/click_soft")
    assert r.status_code == 200, r.text
    path = CACHE / "sfx" / "click_soft.wav"
    assert path.is_file()
    with wave.open(str(path)) as wf:
        assert wf.getnframes() > 0

    r = client.get("/api/preview/music/minimal_pulse?seconds=3")
    assert r.status_code == 200, r.text


def test_unknown_audio_names_are_404_not_500() -> None:
    assert client.get("/api/preview/sfx/does_not_exist").status_code == 404
    assert client.get("/api/preview/music/does_not_exist").status_code == 404


# ---------------------------------------------------------------------- graph

def test_graph_reports_the_real_node_names_in_order() -> None:
    d = client.get("/api/graph").json()
    assert d["nodes"][:3] == ["gate_check", "deep_research", "script_split"]
    assert "build_spec" in d["nodes"] and "render" in d["nodes"]
    assert d["unwired_functions"] == [], (
        f"node functions not wired into the graph: {d['unwired_functions']}"
    )


def test_graph_endpoint_fails_loudly_if_it_cannot_read_the_builder(monkeypatch) -> None:
    """An empty node list must be a 500, not a cheerful empty pipeline."""
    import msf.panel.server as srv

    monkeypatch.setattr(srv, "_GRAPH_BUILDERS", ("no_such_builder",))
    assert client.get("/api/graph").status_code == 500


# --------------------------------------------------------------------- status

def test_status_checks_report_real_probes() -> None:
    d = client.get("/api/status").json()
    names = {c["name"] for c in d["checks"]}
    assert "scene registry" in names
    assert "effect registry" in names
    assert any(n.startswith("default voice") for n in names)
    assert "ffmpeg" in names
    for c in d["checks"]:
        assert c["detail"], f"{c['name']} reports no detail — an unverified 'OK'"


# -------------------------------------------------------------------- preview

def test_scene_preview_rejects_an_unknown_preset() -> None:
    r = client.post("/api/preview/scene", json={"preset": "NotAPreset"})
    assert r.status_code == 404


def test_scene_preview_rejects_a_spec_that_would_render_an_error_card() -> None:
    """Wrong row shape red-cards the WHOLE video, so the panel must not render it."""
    r = client.post(
        "/api/preview/scene",
        json={"preset": "CryptoWallet", "props": {"balance": 1, "tokens": [{"symbol": "ETH"}]}},
    )
    assert r.status_code == 422
    assert "amount" in r.text


def test_preview_path_traversal_is_blocked() -> None:
    """`kind` and `filename` come from the network."""
    for bad in ("../../../../Windows/win.ini", "..%2f..%2fsecrets"):
        assert client.get(f"/preview/scenes/{bad}").status_code in (400, 404)
    assert client.get("/preview/etc/passwd").status_code == 404


# ----------------------------------------------------------------------- runs

def test_runs_is_empty_and_valid_before_anything_starts() -> None:
    d = client.get("/api/runs").json()
    assert isinstance(d["runs"], list)


def test_unknown_run_is_404() -> None:
    assert client.get("/api/runs/deadbeef").status_code == 404


def test_run_request_validates_preset_and_voice() -> None:
    assert client.post("/api/graph/run", json={"topic": "тест", "preset": "Nope"}).status_code == 404
    assert client.post(
        "/api/graph/run", json={"topic": "тест", "preset": "HeroKinetic", "voice": "nope"}
    ).status_code == 404


def test_voice_add_requires_a_transcript() -> None:
    """No transcript means x-vector mode — the silent quality regression."""
    r = client.post("/api/voices", json={"key": "tmp_test", "ref_audio": "x.wav"})
    assert r.status_code == 422  # missing required ref_text


def test_voice_add_rejects_a_missing_file() -> None:
    r = client.post(
        "/api/voices",
        json={
            "key": "tmp_test",
            "ref_audio": "C:/definitely/not/here.wav",
            "ref_text": "какой-то достаточно длинный транскрипт",
        },
    )
    assert r.status_code == 404


def test_default_voice_cannot_be_deleted() -> None:
    from msf.skills_bridge.qwen3_tts import DEFAULT_VOICE

    assert client.delete(f"/api/voices/{DEFAULT_VOICE}").status_code == 409


# ------------------------------------------------------------------------- UI

def test_ui_is_served_and_references_the_script() -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "/static/app.js" in r.text


@pytest.mark.skipif(os.environ.get("MSF_SLOW_TESTS") != "1", reason="renders with node (~20s)")
def test_scene_preview_actually_renders_a_png() -> None:
    r = client.post(
        "/api/preview/scene",
        json={"preset": "HeroKinetic", "props": {"title": "ТЕСТ"}, "frame_pct": 0.9},
    )
    assert r.status_code == 200, r.text
    served = client.get(r.json()["url"])
    assert served.status_code == 200
    assert served.content[:8] == b"\x89PNG\r\n\x1a\n"
