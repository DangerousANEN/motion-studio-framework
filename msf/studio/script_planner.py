"""Script quality gates and deterministic evidence-aware planning helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .contracts import ResearchPack, ScriptLine, ScriptPlan
from .research import ResearchQualityError, allowed_claims


class ScriptQualityError(ValueError):
    """Raised when a script could create unsupported or unreadable claims."""


FACTUAL_KINDS = {"fact", "interpretation", "instruction"}


@dataclass(frozen=True)
class StoryAngle:
    """A viewer question and its intentionally narrow evidence/payoff route."""

    claim_ids: tuple[str, ...]
    takeaway: str
    takeaway_claim_ids: tuple[str, ...]
    cta_asset: str
    cta_text: str
    # Optional short paraphrases for proof beats. Their claim IDs remain the
    # source of truth, while the wording can be made understandable on screen.
    factual_narrations: tuple[str, ...] = ()




@dataclass(frozen=True)
class ScriptPolicy:
    max_words_per_line: int = 34
    require_cta_when_handle_provided: bool = True
    require_hook: bool = True
    max_lines: int = 12


def words(text: str) -> int:
    return len([token for token in text.split() if token])


def validate_script_plan(
    plan: ScriptPlan,
    research: Optional[ResearchPack],
    policy: ScriptPolicy = ScriptPolicy(),
) -> list[str]:
    """Fail closed for unsupported factual narration; return only soft warnings."""
    if len(plan.lines) > policy.max_lines:
        raise ScriptQualityError(f"script has more than {policy.max_lines} lines")
    if policy.require_hook and not any(line.kind == "hook" for line in plan.lines):
        raise ScriptQualityError("script needs a hook")
    if policy.require_cta_when_handle_provided and plan.cta_handle and not any(line.kind == "cta" for line in plan.lines):
        raise ScriptQualityError("script with cta_handle needs a CTA line")

    claims = allowed_claims(research) if research else {}
    warnings: list[str] = []
    for index, line in enumerate(plan.lines):
        if words(line.narration) > policy.max_words_per_line:
            warnings.append(f"line {index + 1} is dense; split it for voice and readability")
        if line.kind in FACTUAL_KINDS:
            if research is None:
                raise ScriptQualityError(f"{line.kind} line {index + 1} requires a research pack")
            if not line.evidence_claim_ids:
                raise ScriptQualityError(f"{line.kind} line {index + 1} has no evidence claim")
            missing = set(line.evidence_claim_ids) - set(claims)
            if missing:
                raise ScriptQualityError(f"line {index + 1} references unknown claims: {sorted(missing)}")
        elif line.evidence_claim_ids:
            warnings.append(f"non-factual line {index + 1} has citations that are not needed")
        if line.kind == "cta" and plan.cta_handle and plan.cta_handle not in line.narration:
            raise ScriptQualityError("CTA must include the configured channel handle")
    return warnings


def plan_from_angle(
    *,
    title: str,
    research: ResearchPack,
    hook: str,
    angle: StoryAngle,
    cta_handle: str,
    intents: Optional[Iterable[str]] = None,
) -> ScriptPlan:
    """Build a short narrative around one question instead of dumping every claim.

    An angle is valid only when each factual takeaway is explicitly linked to a
    selected research claim. The audience gets two proof beats at most, one
    practical implication and a concrete asset promised by the CTA.
    """
    claims = allowed_claims(research)
    selected = [claims[claim_id] for claim_id in angle.claim_ids]
    if not selected or len(selected) > 2:
        raise ScriptQualityError("a short-video angle requires one or two evidence claims")
    missing_takeaway = set(angle.takeaway_claim_ids) - set(angle.claim_ids)
    if missing_takeaway:
        raise ScriptQualityError("takeaway must be supported by selected angle claims")
    if not angle.cta_asset.strip() or not angle.cta_text.strip():
        raise ScriptQualityError("angle needs a concrete Telegram asset and CTA text")
    if angle.factual_narrations and len(angle.factual_narrations) != len(selected):
        raise ScriptQualityError("evidence paraphrases must match selected evidence claims")
    intent_list = list(intents or ("hook", "evidence", "proof", "takeaway", "cta"))
    lines = [ScriptLine(kind="hook", narration=hook, scene_intent=intent_list[0])]
    for index, claim in enumerate(selected):
        narration = angle.factual_narrations[index] if angle.factual_narrations else claim.statement
        lines.append(ScriptLine(
            kind="fact", narration=narration, on_screen_text=narration[:150],
            evidence_claim_ids=[claim.claim_id], scene_intent=intent_list[min(index + 1, len(intent_list) - 1)],
        ))
    lines.append(ScriptLine(
        kind="instruction", narration=angle.takeaway, evidence_claim_ids=list(angle.takeaway_claim_ids),
        scene_intent=intent_list[min(3, len(intent_list) - 1)],
    ))
    cta_narration = angle.cta_text if cta_handle.lower() in angle.cta_text.lower() else f"{angle.cta_text} {cta_handle}."
    lines.append(ScriptLine(
        kind="cta", narration=cta_narration, scene_intent=intent_list[-1],
    ))
    plan = ScriptPlan(research_id=research.research_id, title=title, lines=lines, cta_handle=cta_handle)
    validate_script_plan(plan, research)
    return plan


def plan_from_claims(
    *,
    title: str,
    research: ResearchPack,
    hook: str,
    cta_handle: Optional[str] = None,
    cta_text: Optional[str] = None,
    intents: Optional[Iterable[str]] = None,
) -> ScriptPlan:
    """Create a conservative draft where every generated factual line is cited.

    The helper does not invent connective claims. It presents the evidence claim
    text itself and leaves nuanced framing to a later validated curated edit.
    """
    claims = allowed_claims(research)
    intent_list = list(intents or ("explainer", "evidence", "metric", "cta"))
    lines = [ScriptLine(kind="hook", narration=hook, scene_intent=intent_list[0])]
    for index, claim in enumerate(claims.values()):
        kind = "instruction" if claim.claim_type == "recommendation" else claim.claim_type
        lines.append(
            ScriptLine(
                kind=kind,  # type: ignore[arg-type]
                narration=claim.statement,
                on_screen_text=claim.statement[:150],
                evidence_claim_ids=[claim.claim_id],
                scene_intent=intent_list[min(index + 1, len(intent_list) - 1)],
            )
        )
    if cta_handle:
        lines.append(
            ScriptLine(
                kind="cta",
                narration=cta_text or f"Подписывайтесь на {cta_handle}: там больше практичных разборов LLM.",
                scene_intent="cta",
            )
        )
    plan = ScriptPlan(research_id=research.research_id, title=title, lines=lines, cta_handle=cta_handle)
    validate_script_plan(plan, research)
    return plan
