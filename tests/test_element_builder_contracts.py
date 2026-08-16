from __future__ import annotations

import json
from pathlib import Path

import pytest

from msf.panel import server
from msf.studio import style_catalog


def test_builder_overlay_contract_is_renderer_safe() -> None:
    request = server.BuilderOverlayRequest(
        name="telegram-update",
        overlay_type="notification",
        label="Важное обновление",
        style_id="llm_hubs_neon",
    )

    overlay = server._builder_overlay_spec(request)

    assert overlay["type"] == "notification"
    assert overlay["appName"] == "Telegram"
    assert overlay["title"] == "Важное обновление"
    assert 0 <= overlay["at"] <= 1


def test_builder_overlay_rejects_unknown_runtime_type() -> None:
    request = server.BuilderOverlayRequest(
        name="unknown-overlay",
        overlay_type="invalid",
        label="Не должно пройти",
        style_id="llm_hubs_neon",
    )

    with pytest.raises(Exception) as exc_info:
        server._builder_overlay_spec(request)

    assert "unknown overlay type" in str(exc_info.value)


def test_style_draft_is_discoverable_but_marked_draft(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    drafts = tmp_path / "style_drafts.json"
    drafts.write_text(
        json.dumps(
            {
                "signal_orchid": {
                    "id": "signal_orchid",
                    "label": "Signal Orchid",
                    "base_style": "llm_hubs_neon",
                    "summary": "Test style draft with safe violet action token.",
                    "recommended_scenes": ["HeroKinetic"],
                    "safe_config": {"palette": {"neon": "#B48CFF"}},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(style_catalog, "_STYLE_DRAFTS_PATH", drafts)

    payload = style_catalog.style_catalog_payload()
    draft = next(item for item in payload["families"] if item["id"] == "signal_orchid")

    assert draft["draft"] is True
    assert draft["base_style"] == "llm_hubs_neon"
    assert draft["defaults"]["palette"]["neon"] == "#B48CFF"


def test_transition_scaffold_writes_code_and_recipe_in_isolated_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server, "_TRANSITION_SCAFFOLD_DIR", tmp_path / "generated")
    monkeypatch.setattr(server, "_TRANSITION_RECIPES", tmp_path / "transition_recipes.json")
    request = server.BuilderTransitionRecipeRequest(
        name="product-reveal",
        base_transition="fade",
        style_id="llm_hubs_neon",
        summary="Short readable transition between two production scenes.",
    )

    result = server.api_builder_transition_scaffold(request)

    generated = tmp_path / "generated" / "product_reveal.ts"
    assert generated.is_file()
    assert "product_revealRecipe" in generated.read_text(encoding="utf-8")
    assert result["recipe"]["component_path"].endswith("product_reveal.ts")
    stored = json.loads((tmp_path / "transition_recipes.json").read_text(encoding="utf-8"))
    assert stored["product-reveal"]["base_transition"] == "fade"


def _universal_graph() -> dict:
    return {
        "version": 1,
        "background": "#0b1020",
        "nodes": [
            {"id": "core", "type": "icosahedron", "position": [0, 0, 0]},
            {"id": "group", "type": "group", "children": [
                {"id": "ring", "type": "torus", "rotation": [1, 0, 0]},
            ]},
        ],
    }


def test_universal_3d_graph_accepts_nested_declarative_nodes() -> None:
    clean = server._validate_universal_3d_graph(_universal_graph())
    assert clean["version"] == 1
    assert len(clean["nodes"]) == 2


def test_universal_3d_graph_rejects_duplicate_ids() -> None:
    graph = _universal_graph()
    graph["nodes"].append({"id": "core", "type": "sphere"})
    with pytest.raises(Exception, match="unique"):
        server._validate_universal_3d_graph(graph)


def test_universal_3d_graph_rejects_unknown_primitive() -> None:
    graph = _universal_graph()
    graph["nodes"][0]["type"] = "arbitrary_js"
    with pytest.raises(Exception, match="unsupported"):
        server._validate_universal_3d_graph(graph)


def test_universal_3d_graph_registers_recipe_in_isolated_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    recipes = tmp_path / "universal_3d_recipes.json"
    monkeypatch.setattr(server, "_UNIVERSAL_3D_RECIPES", recipes)
    request = server.Universal3DGraphRequest(
        name="OrbitSignalField",
        summary="Declarative 3D signal field for a video scene.",
        style_id="llm_hubs_neon",
        graph=_universal_graph(),
    )
    result = server.api_builder_3d_register(request)
    assert result["status"] == "registered_recipe"
    stored = json.loads(recipes.read_text(encoding="utf-8"))
    assert stored["OrbitSignalField"]["kind"] == "universal_3d_graph"
    assert stored["OrbitSignalField"]["graph"]["nodes"][1]["children"][0]["type"] == "torus"
