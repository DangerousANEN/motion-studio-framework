"""Create five @llm_hubs drafts through the native MSF research-to-script pipeline.

This runner deliberately does not name, rank or assign presets. Each invocation
uses the catalog-based selector and persists its draft before the next topic, so
cross-video recent-scene avoidance has observable project history.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from msf.studio.contracts import ResearchToScriptRequest
from msf.studio.research_to_script import ResearchToScriptError, ResearchToScriptWorkflow
from msf.studio.storyboard import StoryboardStore

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "projects" / "llm_hubs" / "generated" / "pipeline-diverse-2026-08-16"
PROJECT_ID = "llm_hubs_pipeline_diverse_2026_08_16"

TOPICS = [
    {
        "slug": "01_gemini37_flash_practical_test",
        "topic": "Gemini 3.7 Flash: где быстрая модель может заменить дорогой Claude в реальном рабочем workflow",
        "archetype": "comparison",
        "cta_asset": "чек-лист сравнения качества, скорости и цены на одном рабочем prompt",
    },
    {
        "slug": "02_deepseek_v4pro_own_prompt",
        "topic": "DeepSeek V4 Pro 0813: как честно проверить новую модель на своём рабочем prompt до миграции",
        "archetype": "how_to",
        "cta_asset": "таблица для фиксации качества, latency, цены и ошибок модели",
    },
    {
        "slug": "03_grok46_long_agent",
        "topic": "Grok 4.6: чем long-running agent отличается от обычного LLM-чата и где растёт стоимость",
        "archetype": "explainer",
        "cta_asset": "шпаргалка по контексту, tool calls и контролю расходов агента",
    },
    {
        "slug": "04_openharness_agent_control",
        "topic": "OpenHarness GitHub: как skills, memory и permissions меняют поведение AI-агента",
        "archetype": "case_study",
        "cta_asset": "короткий чек-лист безопасных permissions и dry run для agent workflow",
    },
    {
        "slug": "05_opencode_provider_control",
        "topic": "OpenCode GitHub: как использовать coding agent с разными LLM и не потерять контроль над diff",
        "archetype": "how_to",
        "cta_asset": "чек-лист review, тестов и выбора провайдера для coding agent",
    },
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    store = StoryboardStore()
    workflow = ResearchToScriptWorkflow()
    artifacts: list[dict[str, object]] = []

    for position, item in enumerate(TOPICS, start=1):
        request = ResearchToScriptRequest(
            topic=item["topic"],
            audience="широкая русскоязычная аудитория: LLM, агенты, практическая экономия и контроль качества",
            cta_handle="@llm_hubs",
            cta_asset=item["cta_asset"],
            content_archetype=item["archetype"],
            style_family="llm_hubs_neon",
            provider="duckduckgo",
            max_queries=4,
            max_sources=8,
            community_proof_mode="discover",
            community_platforms=["youtube", "x", "reddit"],
            max_community_leads=3,
            project_id=PROJECT_ID,
            scene_diversity="high",
            avoid_recent_scenes=True,
            recent_scene_window=4,
            motion_safety="calm",
        )
        try:
            result = workflow.run(request)
            stored = store.create(result.storyboard)
            payload = result.model_dump(mode="json")
            payload["stored_storyboard"] = stored.model_dump(mode="json")
            path = OUT / f"{position:02d}_{item['slug']}.research-to-script.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            artifacts.append({
                "position": position,
                "slug": item["slug"],
                "ok": True,
                "path": str(path.relative_to(ROOT)),
                "storyboard_id": stored.draft_id,
                "presets": [scene.preset for scene in stored.scenes],
                "selection_summary": stored.selection_summary,
            })
        except ResearchToScriptError as exc:
            artifacts.append({"position": position, "slug": item["slug"], "ok": False, "error": str(exc)})

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runner": "native_msf_research_to_script_with_storyboard_history",
        "project_id": PROJECT_ID,
        "scene_policy": {"diversity": "high", "avoid_recent_scenes": True, "recent_scene_window": 4},
        "items": artifacts,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "successes": sum(item["ok"] for item in artifacts), "failures": sum(not item["ok"] for item in artifacts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
