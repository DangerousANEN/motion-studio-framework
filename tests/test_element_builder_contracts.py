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
