"""Smoke checks for MSF Studio evidence-first research and script planning."""
from datetime import datetime, timedelta, timezone

from msf.studio.contracts import EvidenceClaim, EvidenceSource, ResearchPack
from msf.studio.research import ResearchQualityError, validate_research_pack
from msf.studio.script_planner import ScriptQualityError, plan_from_claims, validate_script_plan
from msf.studio.research_workflow import storyboard_from_script
from msf.studio.storyboard import StoryboardValidator


if __name__ == "__main__":
    source_a = EvidenceSource(
        source_id="src_official", url="https://example.ai/pricing", title="Official pricing", publisher="Example AI",
        source_type="primary", excerpt="Official page confirms a free tier and documents the current request limits in detail.",
        retrieved_at=datetime.now(timezone.utc),
    )
    source_b = EvidenceSource(
        source_id="src_docs", url="https://docs.example.ai/models", title="Model docs", publisher="Example AI Docs",
        source_type="official_docs", excerpt="Official documentation lists supported models and API options for developers and end users.",
        retrieved_at=datetime.now(timezone.utc),
    )
    claim = EvidenceClaim(
        claim_id="claim_free", statement="Платформа публикует бесплатный тариф и документацию по его текущим ограничениям.",
        source_ids=[source_a.source_id, source_b.source_id], confidence="high",
    )
    pack = ResearchPack(topic="Тест evidence-first", sources=[source_a, source_b], claims=[claim])
    assert validate_research_pack(pack) == []

    # A release article cannot be treated as current merely because it was
    # retrieved today: it needs a recent release date and published primary evidence.
    release_sources = [
        source_a.model_copy(update={"published_at": datetime.now(timezone.utc)}),
        source_b.model_copy(update={"published_at": datetime.now(timezone.utc)}),
    ]
    release_pack = pack.model_copy(update={
        "research_id": "research_release_fresh",
        "release_topic": True,
        "release_date": datetime.now(timezone.utc),
        "sources": release_sources,
    })
    assert validate_research_pack(release_pack) == []
    stale_release = release_pack.model_copy(update={"release_date": datetime.now(timezone.utc) - timedelta(days=22)})
    try:
        validate_research_pack(stale_release)
    except ResearchQualityError:
        pass
    else:
        raise AssertionError("stale release topic was accepted")
    plan = plan_from_claims(title="Тест", research=pack, hook="Вот как проверить бесплатный доступ без догадок.", cta_handle="@llm_hubs")
    assert validate_script_plan(plan, pack) == []
    storyboard = storyboard_from_script(plan, pack)
    assert StoryboardValidator().validate(storyboard, pack).valid
    broken = plan.model_copy(update={"lines": [plan.lines[0], plan.lines[1].model_copy(update={"evidence_claim_ids": []})]})
    try:
        validate_script_plan(broken, pack)
    except ScriptQualityError:
        pass
    else:
        raise AssertionError("unsupported factual line was accepted")
    print(f"claims={len(pack.claims)}")
    print(f"script_lines={len(plan.lines)}")
    print(f"storyboard_scenes={len(storyboard.scenes)}")
