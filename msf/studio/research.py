"""Evidence-first research policy for MSF Studio.

The module deliberately separates retrieval from validation. A caller may use a
web search, a connected research provider or an internal source, but no script
can treat the result as evidence until its source/claim graph passes this
fail-closed validator.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from .contracts import EvidenceClaim, EvidenceSource, ResearchPack


class ResearchQualityError(ValueError):
    """Raised when evidence cannot safely support a factual video script."""


PRIMARY_HOST_HINTS = (
    "openai.com", "anthropic.com", "ai.google", "deepmind.google", "huggingface.co",
    "mistral.ai", "meta.com", "github.com", "arxiv.org", "docs.", "research.",
)


@dataclass(frozen=True)
class ResearchPolicy:
    min_sources: int = 2
    min_high_confidence_claims: int = 1
    max_freshness_days: int = 45
    # A release topic must be truly recent. Retrieval time alone is not enough:
    # an agent can rediscover a months-old announcement today.
    max_release_age_days: int = 21
    require_primary_for_cost_or_availability: bool = True
    require_primary_for_release_topics: bool = True


def host_for(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def is_primaryish(source: EvidenceSource) -> bool:
    host = host_for(source.url)
    return source.source_type in {"primary", "official_docs"} or any(hint in host for hint in PRIMARY_HOST_HINTS)


def _as_aware(timestamp: datetime) -> datetime:
    return timestamp if timestamp.tzinfo is not None else timestamp.replace(tzinfo=timezone.utc)


def source_age_days(source: EvidenceSource, now: datetime | None = None) -> int:
    current = now or datetime.now(timezone.utc)
    # Publication time has editorial meaning; retrieval is merely evidence of
    # when the agent looked at the page. Evergreen sources without publication
    # metadata continue to use retrieval as the best available signal.
    timestamp = source.published_at or source.retrieved_at
    return max(0, int((_as_aware(current) - _as_aware(timestamp)).total_seconds() // 86400))


def release_age_days(pack: ResearchPack, now: datetime | None = None) -> int:
    if pack.release_date is None:
        raise ResearchQualityError("release topic is missing release_date")
    current = now or datetime.now(timezone.utc)
    return max(0, int((_as_aware(current) - _as_aware(pack.release_date)).total_seconds() // 86400))


def validate_research_pack(pack: ResearchPack, policy: ResearchPolicy = ResearchPolicy()) -> list[str]:
    """Return non-blocking warnings or raise for a broken factual evidence graph."""
    if len(pack.sources) < policy.min_sources:
        raise ResearchQualityError(f"research needs at least {policy.min_sources} sources")
    source_ids = {source.source_id for source in pack.sources}
    if len(source_ids) != len(pack.sources):
        raise ResearchQualityError("research contains duplicate source IDs")

    if pack.release_topic:
        age = release_age_days(pack)
        if age > policy.max_release_age_days:
            raise ResearchQualityError(
                f"release topic is {age} days old; maximum is {policy.max_release_age_days} days"
            )
        if policy.require_primary_for_release_topics:
            release_sources = [source for source in pack.sources if source.published_at is not None and is_primaryish(source)]
            if not release_sources:
                raise ResearchQualityError(
                    "release topic needs an official or primary source with published_at"
                )

    warnings: list[str] = []
    high_confidence = 0
    for claim in pack.claims:
        missing = set(claim.source_ids) - source_ids
        if missing:
            raise ResearchQualityError(f"claim {claim.claim_id} references missing sources: {sorted(missing)}")
        if claim.claim_type == "fact" and not claim.source_ids:
            raise ResearchQualityError(f"factual claim {claim.claim_id} has no source")
        if claim.confidence == "high":
            high_confidence += 1
        for source_id in claim.source_ids:
            source = next(item for item in pack.sources if item.source_id == source_id)
            if source_age_days(source) > policy.max_freshness_days:
                warnings.append(f"source {source_id} was retrieved more than {policy.max_freshness_days} days ago")
        cost_or_availability = any(token in claim.statement.lower() for token in ("цена", "стоимость", "бесплат", "free", "price", "availability", "доступ"))
        if policy.require_primary_for_cost_or_availability and cost_or_availability:
            sources = [item for item in pack.sources if item.source_id in claim.source_ids]
            if not any(is_primaryish(item) for item in sources):
                raise ResearchQualityError(
                    f"cost/availability claim {claim.claim_id} needs an official or primary source"
                )
    if high_confidence < policy.min_high_confidence_claims:
        raise ResearchQualityError("research has no high-confidence evidence claim")
    return warnings


def allowed_claims(pack: ResearchPack) -> dict[str, EvidenceClaim]:
    """Return claims only after all evidence guards pass."""
    validate_research_pack(pack)
    return {claim.claim_id: claim for claim in pack.claims}
