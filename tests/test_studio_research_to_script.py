from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

import pytest

from msf.studio.contracts import EvidenceSource, PinnedResearchSource, ResearchToScriptRequest
from msf.studio.research_to_script import (
    ResearchToScriptError,
    ResearchToScriptWorkflow,
    SearchHit,
    _deduplicate_hits,
    _is_safe_public_url,
    _official_domain_for_topic,
    _official_seed_hits_for_topic,
    _rank_hit_for_topic,
    _queries_for,
    _route_topic,
)


class FakeSearch:
    def search(self, query: str, *, limit: int) -> list[SearchHit]:
        return [
            SearchHit("Официальный анонс", "https://example-ai.test/announce", "Первый источник"),
            SearchHit("Независимая проверка", "https://reporting.test/check", "Второй источник"),
            SearchHit("Дубликат", "https://example-ai.test/announce#details", "Дубликат"),
        ][:limit]


class FakeExtractor:
    def extract(self, hit: SearchHit) -> EvidenceSource | None:
        rows = {
            "https://example-ai.test/announce": EvidenceSource(
                url=hit.url,
                title=hit.title,
                publisher="example-ai.test",
                source_type="primary",
                published_at=datetime.now(timezone.utc),
                excerpt="Официальный источник описывает проверенную возможность продукта и условия доступа.",
            ),
            "https://reporting.test/check": EvidenceSource(
                url=hit.url,
                title=hit.title,
                publisher="reporting.test",
                source_type="reputable_reporting",
                excerpt="Независимая проверка подтверждает результат на практической задаче без неподтверждённых цифр.",
            ),
        }
        return rows.get(hit.url)


class FakeLLM:
    def __init__(self, *, unknown_url: bool = False, bad_proof: str | None = None, comparison_mode: str = "observed") -> None:
        self.unknown_url = unknown_url
        self.bad_proof = bad_proof
        self.comparison_mode = comparison_mode

    def complete(self, task: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if task == "evidence_claims":
            source_urls = [row["url"] for row in payload["sources"]]
            if self.unknown_url:
                source_urls = ["https://unknown.test/not-in-research"]
            return {
                "summary": "Два источника объясняют, что изменилось и как проверить вывод на своей задаче.",
                "claims": [
                    {
                        "statement": "Официальный источник описывает новую возможность продукта.",
                        "source_urls": [source_urls[0]],
                        "confidence": "high",
                        "claim_type": "fact",
                    },
                    {
                        "statement": "Независимая проверка советует сравнить результат на своей задаче.",
                        "source_urls": [source_urls[-1]],
                        "confidence": "medium",
                        "claim_type": "recommendation",
                    },
                ],
            }
        if task == "comparison_proof":
            models = list(payload.get("requested_models") or ["Модель А", "Модель Б"])
            if self.comparison_mode == "proposed":
                return {
                    "mode": "proposed", "visual_mode": "code_test", "task": "Исправить одну ошибку в тестовом проекте",
                    "prompt_summary": "Один prompt, один файл и одинаковый лимит времени.", "models": models,
                    "conditions": ["Одинаковый prompt", "Одинаковый тестовый проект"],
                    "criterion": "Сколько ручных правок осталось после запуска тестов.", "outcome": "inconclusive",
                    "strength": "Нужно проверить результат на одинаковой задаче.", "weakness": "Источники не показывают два готовых результата.",
                    "evidence_claim_ids": [], "asset_urls": [],
                    "disclosure": "Один тест не доказывает, что модель лучше вообще.",
                }
            return {
                "mode": "observed", "visual_mode": "code_test", "task": "Исправить одну ошибку в тестовом проекте",
                "prompt_summary": "Один prompt, один файл и одинаковый лимит времени.", "models": models,
                "conditions": ["Одинаковый prompt", "Одинаковый тестовый проект"],
                "criterion": "Проходят ли тесты без ручных правок.", "outcome": "left_wins",
                "strength": "Первая модель решила конкретную задачу без дополнительной правки.", "weakness": "Вторая модель потребовала ручной проверки результата.",
                "evidence_claim_ids": [payload["claims"][0]["claim_id"]], "asset_urls": [payload["source_urls"][0]],
                "disclosure": "Один пример не доказывает, что модель лучше на всех задачах.",
            }
        return {
            "title": "Что реально изменилось",
            "hook": "Это стоит проверить самому",
            "factual_narrations": [self.bad_proof or "Новая возможность уже описана в официальном источнике."],
            "takeaway": "Сначала сравните результат на своей задаче, а потом принимайте решение.",
            "cta_text": "Готовый чек-лист и ссылки уже лежат в канале",
        }


def _workflow(*, unknown_url: bool = False, bad_proof: str | None = None, comparison_mode: str = "observed") -> ResearchToScriptWorkflow:
    return ResearchToScriptWorkflow(search_provider=FakeSearch(), extractor=FakeExtractor(), llm=FakeLLM(unknown_url=unknown_url, bad_proof=bad_proof, comparison_mode=comparison_mode))


def test_research_to_script_builds_evidence_linked_unique_storyboard() -> None:
    result = _workflow().run(ResearchToScriptRequest(
        topic="как проверить новую возможность модели",
        cta_asset="чек-лист проверки и ссылки на источники",
        style_family="llm_hubs_neon",
        max_queries=2,
        max_sources=2,
    ))

    assert result.script.language == "ru"
    assert result.script.lines[0].kind == "hook"
    assert result.script.lines[-1].kind == "cta"
    factual = [line for line in result.script.lines if line.kind in {"fact", "instruction"}]
    assert factual and all(line.evidence_claim_ids for line in factual)
    assert len({scene.preset for scene in result.storyboard.scenes}) == len(result.storyboard.scenes)
    assert {scene.style_kit for scene in result.storyboard.scenes} == {"llm_hubs_neon"}
    assert [item.phase for item in result.milestones] == [
        "topic_routed", "query_plan_created", "sources_collected", "pages_extracted", "claims_validated", "script_composed", "storyboard_validated",
    ]
    assert result.topic_plan is not None
    assert result.topic_plan.archetype == "how_to"


def test_required_pinned_source_is_extracted_before_open_web_candidates() -> None:
    result = _workflow().run(ResearchToScriptRequest(
        topic="как проверить новую возможность модели",
        pinned_sources=[PinnedResearchSource(
            url="https://example-ai.test/announce",
            mode="required",
            reason="Официальный анонс нужен как первичный источник",
        )],
        max_queries=2,
        max_sources=2,
    ))
    assert any(source.url == "https://example-ai.test/announce" for source in result.research.sources)
    assert "pinned_sources_processed" in [item.phase for item in result.milestones]


def test_missing_required_pinned_source_fails_closed() -> None:
    with pytest.raises(ResearchToScriptError, match="required pinned source could not be extracted"):
        _workflow().run(ResearchToScriptRequest(
            topic="как проверить новую возможность модели",
            pinned_sources=[PinnedResearchSource(
                url="https://missing.test/required",
                mode="required",
                reason="Нужно проверить обязательную ссылку",
            )],
            max_queries=2,
            max_sources=2,
        ))


def test_observed_comparison_proof_creates_task_first_storyboard() -> None:
    result = _workflow().run(ResearchToScriptRequest(
        topic="сравнение двух моделей на коде", comparison_mode="observed",
        comparison_models=["Модель А", "Модель Б"], visual_evidence_mode="code_test",
        require_observed_comparison=True, max_queries=2, max_sources=2,
    ))
    assert len(result.comparison_proofs) == 1
    proof = result.comparison_proofs[0]
    assert proof.mode == "observed" and proof.outcome == "left_wins"
    assert proof.asset_urls == ["https://example-ai.test/announce"]
    assert [line.scene_intent for line in result.script.lines] == [
        "comparison_hook", "comparison_setup", "comparison_result", "comparison_caveat", "cta",
    ]
    assert all(line.evidence_claim_ids for line in result.script.lines[1:4])
    assert len({scene.preset for scene in result.storyboard.scenes}) == len(result.storyboard.scenes)


def test_observed_comparison_fails_when_only_proposed_proof_exists() -> None:
    with pytest.raises(ResearchToScriptError, match="requires an observed comparison"):
        _workflow(comparison_mode="proposed").run(ResearchToScriptRequest(
            topic="сравнение двух моделей на коде", comparison_mode="observed",
            comparison_models=["Модель А", "Модель Б"], require_observed_comparison=True,
            max_queries=2, max_sources=2,
        ))


def test_research_to_script_drops_claims_without_extracted_citations() -> None:
    with pytest.raises(ResearchToScriptError, match="no claims linked to extracted research"):
        _workflow(unknown_url=True).run(ResearchToScriptRequest(topic="проверяемая тема", max_queries=2, max_sources=2))


def test_russian_quality_gate_rejects_cjk_or_dense_proof_beats() -> None:
    with pytest.raises(ResearchToScriptError, match="non-Russian CJK"):
        _workflow(bad_proof="Проверьте это 参数").run(ResearchToScriptRequest(topic="проверяемая тема", max_queries=2, max_sources=2))
    too_long = " ".join(["проверка"] * 25)
    with pytest.raises(ResearchToScriptError, match="overlong proof beat"):
        _workflow(bad_proof=too_long).run(ResearchToScriptRequest(topic="проверяемая тема", max_queries=2, max_sources=2))


def test_provider_query_plan_keeps_official_and_topic_specific_routes() -> None:
    plan = _route_topic(ResearchToScriptRequest(topic="как проверить ограничения OpenAI API"))
    queries = _queries_for("как проверить ограничения OpenAI API", 3, plan)
    assert queries[0].startswith("site:developers.openai.com")
    assert "практическая инструкция" in queries[1]
    assert "типичные ошибки" in queries[2]
    seed = _official_seed_hits_for_topic("ограничения OpenAI API")[0]
    irrelevant = SearchHit("Responses API reference", "https://developers.openai.com/api/reference/resources/responses")
    assert _rank_hit_for_topic(seed, "ограничения OpenAI API") > _rank_hit_for_topic(irrelevant, "ограничения OpenAI API")


def test_known_provider_topics_require_an_official_extracted_source() -> None:
    assert _official_domain_for_topic("ограничения OpenAI API") == "developers.openai.com"
    assert _official_seed_hits_for_topic("ограничения OpenAI API")[0].url == "https://developers.openai.com/api/docs/guides/rate-limits"
    with pytest.raises(ResearchToScriptError, match="official source"):
        _workflow().run(ResearchToScriptRequest(topic="ограничения OpenAI API", max_queries=2, max_sources=2))


def test_public_url_guard_and_deduplication_are_fail_closed() -> None:
    assert _is_safe_public_url("https://example.com/article")
    assert not _is_safe_public_url("file:///etc/passwd")
    assert not _is_safe_public_url("http://127.0.0.1:8765/private")
    assert not _is_safe_public_url("http://localhost:8765/private")
    deduplicated = _deduplicate_hits([
        SearchHit("One", "https://example.com/article#part"),
        SearchHit("Two", "https://example.com/article"),
        SearchHit("Unsafe", "http://127.0.0.1:8765/private"),
    ])
    assert [hit.url for hit in deduplicated] == ["https://example.com/article"]


def test_claude_provider_topics_use_current_official_platform_host() -> None:
    assert _official_domain_for_topic("Claude Sonnet 5 сравнение") == "platform.claude.com"
    seed = _official_seed_hits_for_topic("Claude Sonnet 5 сравнение")[0]
    assert seed.url == "https://platform.claude.com/docs/en/about-claude/models/overview"


@pytest.mark.parametrize(("topic", "expected"), [
    ("как настроить локальную базу знаний для команды", "how_to"),
    ("почему ошибка агента удалила нужные файлы", "incident"),
    ("миф: бесплатная модель всегда обходится дешевле", "myth_fact"),
    ("кейс: команда сократила ручную проверку документов", "case_study"),
    ("что меняется на рынке ИИ-инструментов для дизайнеров", "trend"),
])
def test_topic_router_supports_non_release_archetypes(topic: str, expected: str) -> None:
    assert _route_topic(ResearchToScriptRequest(topic=topic)).archetype == expected


def test_community_hit_becomes_review_only_lead() -> None:
    from msf.studio.research_to_script import _community_lead_from_hit

    lead = _community_lead_from_hit(SearchHit(
        "Gemini vs Sonnet — same prompt UI test",
        "https://www.youtube.com/watch?v=demo",
        "same prompt, both outputs, score and conditions shown",
    ))
    assert lead is not None
    assert lead.platform == "youtube"
    assert lead.editorial_status == "needs_review"
    assert lead.allowed_use == "attributed_recreation_only"
    assert set(lead.evidence_completeness) == {"task_visible", "both_outputs_visible", "conditions_visible", "criterion_visible"}


class CommunitySearch(FakeSearch):
    def search(self, query: str, *, limit: int) -> list[SearchHit]:
        if "site:youtube.com" in query:
            return [SearchHit(
                "Same prompt UI test: Gemini vs Sonnet",
                "https://www.youtube.com/watch?v=community-demo",
                "same prompt, both outputs, identical settings and score shown",
            )]
        return super().search(query, limit=limit)


def test_community_discovery_returns_lead_not_factual_source() -> None:
    workflow = ResearchToScriptWorkflow(search_provider=CommunitySearch(), extractor=FakeExtractor(), llm=FakeLLM())
    result = workflow.run(ResearchToScriptRequest(
        topic="как сравнить две модели на одной задаче",
        max_queries=2,
        max_sources=2,
        community_proof_mode="discover",
        community_platforms=["youtube"],
        max_community_leads=1,
    ))
    assert len(result.community_leads) == 1
    assert result.community_leads[0].editorial_status == "needs_review"
    assert result.community_leads[0].platform == "youtube"
    assert all("youtube" not in source.url for source in result.research.sources)
    assert "community_proof_discovered" in [item.phase for item in result.milestones]
