"""Native evidence-first research-to-script workflow for MSF Studio.

The module deliberately adopts a small set of concepts from Local Deep Research
(query decomposition, bounded source collection, link de-duplication and
fail-closed citations) without importing its heavy runtime or provider stack.
It is safe to invoke from the Studio CLI, API or MCP server: it produces editable
contracts and never starts a renderer job.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
import json
import os
import re
import socket
from typing import Any, Iterable, Literal, Mapping, Protocol, TypedDict
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup
from langgraph.graph import END, StateGraph
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from msf import registry
from msf.spec import FPS, READ_CHARS_PER_SEC

from .catalog import all_scenes
from .contracts import (
    AudioPolicy,
    CapabilityTier,
    ComparisonProof,
    CommunityProofLead,
    EvidenceClaim,
    EvidenceSource,
    ResearchMilestone,
    ResearchPack,
    ResearchToScriptRequest,
    ResearchToScriptResult,
    ScriptLine,
    ScriptPlan,
    StoryboardDraft,
    StoryboardScene,
    TopicPlan,
)
from .research import ResearchQualityError, is_primaryish, validate_research_pack
from .script_planner import ScriptQualityError, StoryAngle, plan_from_angle
from .storyboard import StoryboardValidator


class ResearchToScriptError(RuntimeError):
    """Raised when a topic cannot become a safe evidence-backed video draft."""


@dataclass(frozen=True)
class SearchHit:
    """Untrusted public search result before page-level evidence extraction."""

    title: str
    url: str
    snippet: str = ""
    publisher: str = ""
    published_at: datetime | None = None


class SearchProvider(Protocol):
    """Bounded public-search interface; implementations return links, not conclusions."""

    def search(self, query: str, *, limit: int) -> list[SearchHit]: ...


class StructuredResearchLLM(Protocol):
    """A narrow structured-output LLM surface, easy to fake in deterministic tests."""

    def complete(self, task: Literal["evidence_claims", "comparison_proof", "script_copy"], payload: Mapping[str, Any]) -> dict[str, Any]: ...


class _StrictPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _ClaimItem(_StrictPayload):
    statement: str = Field(min_length=12, max_length=600)
    source_urls: list[str] = Field(min_length=1, max_length=3)
    confidence: Literal["high", "medium", "low"] = "medium"
    claim_type: Literal["fact", "interpretation", "recommendation"] = "fact"


class _ClaimsPayload(_StrictPayload):
    summary: str = Field(min_length=20, max_length=4000)
    claims: list[_ClaimItem] = Field(min_length=1, max_length=5)


class _ComparisonProofPayload(_StrictPayload):
    mode: Literal["observed", "proposed"]
    visual_mode: Literal["code_test", "ui_build", "game_build", "data_viz", "research_answer", "incident", "safety_failure"]
    task: str = Field(min_length=8, max_length=160)
    prompt_summary: str = Field(min_length=8, max_length=180)
    models: list[str] = Field(min_length=2, max_length=3)
    conditions: list[str] = Field(min_length=2, max_length=6)
    criterion: str = Field(min_length=8, max_length=160)
    outcome: Literal["left_wins", "right_wins", "tie", "inconclusive"]
    strength: str = Field(min_length=8, max_length=160)
    weakness: str = Field(min_length=8, max_length=160)
    evidence_claim_ids: list[str] = Field(default_factory=list, max_length=4)
    asset_urls: list[str] = Field(default_factory=list, max_length=4)
    disclosure: str = Field(min_length=12, max_length=180)


class _ScriptCopyPayload(_StrictPayload):
    title: str = Field(min_length=3, max_length=160)
    hook: str = Field(min_length=3, max_length=80)
    factual_narrations: list[str] = Field(min_length=1, max_length=2)
    takeaway: str = Field(min_length=3, max_length=300)
    cta_text: str = Field(min_length=3, max_length=220)


class OpenAIResearchLLM:
    """Structured OpenAI-compatible writer using the configured Manus-compatible endpoint.

    The model is read from ``MSF_RESEARCH_MODEL``. Production callers can provide a
    different implementation, while tests use a deterministic fake and make no
    network or model calls.
    """

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get("MSF_RESEARCH_MODEL", "gpt-5-mini")
        self.client = OpenAI()

    @staticmethod
    def _schema_for(task: str) -> dict[str, Any]:
        if task == "comparison_proof":
            return {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["observed", "proposed"]},
                    "visual_mode": {"type": "string", "enum": ["code_test", "ui_build", "game_build", "data_viz", "research_answer", "incident", "safety_failure"]},
                    "task": {"type": "string", "minLength": 8, "maxLength": 160},
                    "prompt_summary": {"type": "string", "minLength": 8, "maxLength": 180},
                    "models": {"type": "array", "minItems": 2, "maxItems": 3, "items": {"type": "string"}},
                    "conditions": {"type": "array", "minItems": 2, "maxItems": 6, "items": {"type": "string"}},
                    "criterion": {"type": "string", "minLength": 8, "maxLength": 160},
                    "outcome": {"type": "string", "enum": ["left_wins", "right_wins", "tie", "inconclusive"]},
                    "strength": {"type": "string", "minLength": 8, "maxLength": 160},
                    "weakness": {"type": "string", "minLength": 8, "maxLength": 160},
                    "evidence_claim_ids": {"type": "array", "maxItems": 4, "items": {"type": "string"}},
                    "asset_urls": {"type": "array", "maxItems": 4, "items": {"type": "string"}},
                    "disclosure": {"type": "string", "minLength": 12, "maxLength": 180},
                },
                "required": ["mode", "visual_mode", "task", "prompt_summary", "models", "conditions", "criterion", "outcome", "strength", "weakness", "evidence_claim_ids", "asset_urls", "disclosure"],
                "additionalProperties": False,
            }
        if task == "evidence_claims":
            return {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "minLength": 20, "maxLength": 4000},
                    "claims": {
                        "type": "array", "minItems": 1, "maxItems": 5,
                        "items": {
                            "type": "object",
                            "properties": {
                                "statement": {"type": "string", "minLength": 12, "maxLength": 600},
                                "source_urls": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "string"}},
                                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                                "claim_type": {"type": "string", "enum": ["fact", "interpretation", "recommendation"]},
                            },
                            "required": ["statement", "source_urls", "confidence", "claim_type"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["summary", "claims"],
                "additionalProperties": False,
            }
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 160},
                "hook": {"type": "string", "minLength": 3, "maxLength": 80},
                "factual_narrations": {"type": "array", "minItems": 1, "maxItems": 2, "items": {"type": "string", "minLength": 3, "maxLength": 150}},
                "takeaway": {"type": "string", "minLength": 3, "maxLength": 300},
                "cta_text": {"type": "string", "minLength": 3, "maxLength": 220},
            },
            "required": ["title", "hook", "factual_narrations", "takeaway", "cta_text"],
            "additionalProperties": False,
        }

    def complete(self, task: Literal["evidence_claims", "comparison_proof", "script_copy"], payload: Mapping[str, Any]) -> dict[str, Any]:
        if task == "evidence_claims":
            system = (
                "Ты исследователь для русскоязычных коротких видео. Работай только с переданными "
                "источниками. Не добавляй фактов из памяти. Для каждого утверждения возвращай точные "
                "source_urls только из входного списка. Отделяй факт от рекомендации. Пиши по-русски."
            )
        elif task == "comparison_proof":
            system = (
                "Ты редактор доказательных сравнений LLM для русскоязычных коротких видео. Работай только "
                "с переданными claims и source URLs. Верни observed только если источники описывают одну и ту же "
                "задачу, сопоставимые условия и наблюдаемый результат двух моделей; иначе верни proposed и outcome "
                "inconclusive. Один пример не доказывает, что модель лучше вообще. Не выдумывай запрос, победителя, "
                "скриншоты, метрики или ущерб. Пиши коротким понятным русским языком: task, criterion, strength и weakness — "
                "максимум 18 слов; не используй английские слова, кроме точных названий моделей."
            )
        else:
            system = (
                "Ты редактор русскоязычных вертикальных видео. Пиши простым разговорным языком, "
                "без англицизмов и технического жаргона. Не добавляй фактов, чисел или обещаний, "
                "которых нет во входных утверждениях. Hook должен быть коротким и цепляющим."
            )
        try:
            request_kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": task, "strict": True, "schema": self._schema_for(task)},
                },
            }
            # GPT-5 consumes hidden reasoning tokens before visible JSON. Keep
            # reasoning deliberately small for bounded extraction/copy steps and
            # leave enough visible budget for the strict schema response.
            if self.model.startswith(("gpt-5", "o-series")):
                request_kwargs["max_completion_tokens"] = int(os.environ.get("MSF_RESEARCH_MAX_COMPLETION_TOKENS", "5000"))
                request_kwargs["extra_body"] = {"reasoning": {"effort": os.environ.get("MSF_RESEARCH_REASONING", "minimal")}}
            elif self.model.startswith("gemini-"):
                # Gemini uses max_tokens; max_completion_tokens can yield null
                # content with finish_reason=length on the proxy.
                request_kwargs["max_tokens"] = int(os.environ.get("MSF_RESEARCH_MAX_TOKENS", "5000"))
            else:
                request_kwargs["max_tokens"] = int(os.environ.get("MSF_RESEARCH_MAX_TOKENS", "5000"))
            response = self.client.chat.completions.create(**request_kwargs)
            proxy_details = getattr(response, "details", None)
            proxy_error = getattr(response, "error", None) or getattr(proxy_details, "error", None) or getattr(proxy_details, "message", None)
            if proxy_error:
                raise ResearchToScriptError(f"LLM proxy unavailable: {proxy_error}")
            choice = response.choices[0] if getattr(response, "choices", None) else None
            message = getattr(choice, "message", None)
            content = getattr(message, "content", None)
            if not content:
                finish_reason = getattr(choice, "finish_reason", None)
                usage = getattr(response, "usage", None)
                completion_tokens = getattr(usage, "completion_tokens", None)
                raise ResearchToScriptError(
                    f"LLM returned an empty structured response (finish_reason={finish_reason}, "
                    f"completion_tokens={completion_tokens}, model={self.model})"
                )
            decoded = json.loads(content)
            if not isinstance(decoded, dict):
                raise ResearchToScriptError("LLM structured response is not an object")
            return decoded
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            raise ResearchToScriptError(f"LLM returned invalid structured {task} output: {exc}") from exc
        except Exception as exc:
            raise ResearchToScriptError(f"LLM {task} step failed: {str(exc)[:240]}") from exc


class DuckDuckGoSearchProvider:
    """Public search provider with no provider account or API key requirement."""

    def search(self, query: str, *, limit: int) -> list[SearchHit]:
        try:
            from ddgs import DDGS
        except Exception as exc:
            raise ResearchToScriptError(f"public search client is unavailable: {str(exc)[:240]}") from exc
        raw_results: list[Mapping[str, Any]] = []
        failures: list[str] = []
        # DDGS aggregates several public engines. Query a compact fallback set
        # rather than retrying a transiently broken provider indefinitely.
        for backend in ("auto", "google", "bing", "brave"):
            try:
                candidate = list(DDGS().text(query, max_results=limit, backend=backend))
                if candidate:
                    raw_results = [item for item in candidate if isinstance(item, Mapping)]
                    break
            except Exception as exc:
                failures.append(f"{backend}: {str(exc)[:100]}")
        if not raw_results:
            detail = "; ".join(failures) or "no public results"
            raise ResearchToScriptError(f"public search failed across configured fallbacks: {detail}")
        hits: list[SearchHit] = []
        for item in raw_results:
            if not isinstance(item, Mapping):
                continue
            url = str(item.get("href") or item.get("url") or "").strip()
            title = str(item.get("title") or "").strip()
            if url and title:
                hits.append(SearchHit(title=title, url=url, snippet=str(item.get("body") or "")))
        return hits


class SearxngSearchProvider:
    """Optional public SearXNG-compatible JSON provider with explicit endpoint config."""

    def __init__(self, endpoint: str | None = None, timeout_seconds: float = 15.0) -> None:
        self.endpoint = (endpoint or os.environ.get("MSF_RESEARCH_SEARXNG_URL") or "").rstrip("/")
        self.timeout_seconds = timeout_seconds
        if not self.endpoint:
            raise ResearchToScriptError("SearXNG provider requires MSF_RESEARCH_SEARXNG_URL")

    def search(self, query: str, *, limit: int) -> list[SearchHit]:
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
                response = client.get(f"{self.endpoint}/search", params={"q": query, "format": "json"})
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise ResearchToScriptError(f"SearXNG search failed: {str(exc)[:240]}") from exc
        hits: list[SearchHit] = []
        for item in list(payload.get("results") or [])[:limit]:
            if not isinstance(item, Mapping):
                continue
            url = str(item.get("url") or "").strip()
            title = str(item.get("title") or "").strip()
            if url and title:
                hits.append(SearchHit(title=title, url=url, snippet=str(item.get("content") or "")))
        return hits


_BLOCKED_HOSTS = {"localhost", "localhost.localdomain", "metadata.google.internal"}


def _is_public_host(host: str) -> bool:
    candidate = host.lower().strip().rstrip(".")
    if not candidate or candidate in _BLOCKED_HOSTS or candidate.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(candidate)
        return not (address.is_private or address.is_loopback or address.is_link_local or address.is_multicast or address.is_reserved or address.is_unspecified)
    except ValueError:
        return True


def _is_safe_public_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and _is_public_host(parsed.hostname or "")


def _resolve_public_url(value: str) -> bool:
    """Reject hostnames resolving only to non-public addresses before fetching."""
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    if not _is_safe_public_url(value):
        return False
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except OSError:
        return False
    resolved: list[str] = []
    for item in addresses:
        raw = item[4][0]
        if raw not in resolved:
            resolved.append(raw)
    if not resolved:
        return False
    return all(_is_public_host(item) for item in resolved)


def _normalise_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    return parsed._replace(fragment="").geturl()


def _source_type(url: str) -> Literal["primary", "official_docs", "reputable_reporting", "community", "unknown"]:
    host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
    if host.endswith(("openai.com", "anthropic.com", "ai.google", "deepmind.google", "mistral.ai", "meta.com", "huggingface.co")):
        return "primary"
    if host.startswith("docs.") or host.endswith(("github.com", "arxiv.org")):
        return "official_docs"
    if host.endswith(("reuters.com", "theverge.com", "techcrunch.com", "venturebeat.com", "wired.com")):
        return "reputable_reporting"
    return "unknown"


def _parse_published_at(soup: BeautifulSoup) -> datetime | None:
    candidates: list[str] = []
    for selector, attribute in (
        ('meta[property="article:published_time"]', "content"),
        ('meta[name="date"]', "content"),
        ('meta[name="publish_date"]', "content"),
        ('meta[itemprop="datePublished"]', "content"),
        ("time[datetime]", "datetime"),
    ):
        tag = soup.select_one(selector)
        if tag and tag.get(attribute):
            candidates.append(str(tag[attribute]))
    for value in candidates:
        try:
            normalised = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalised)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


class PublicPageExtractor:
    """Small, safe HTML extractor. It is intentionally not a general crawler."""

    def __init__(self, timeout_seconds: float = 15.0, max_bytes: int = 1_500_000, max_redirects: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes
        self.max_redirects = max_redirects

    def extract(self, hit: SearchHit) -> EvidenceSource | None:
        current_url = _normalise_url(hit.url)
        if not _resolve_public_url(current_url):
            return None
        headers = {"User-Agent": "MSFStudioResearch/1.0 (+https://github.com/DangerousANEN/motion-studio-framework)", "Accept": "text/html,application/xhtml+xml"}
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False, headers=headers) as client:
                for _ in range(self.max_redirects + 1):
                    if not _resolve_public_url(current_url):
                        return None
                    response = client.get(current_url)
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            return None
                        current_url = _normalise_url(urljoin(current_url, location))
                        continue
                    response.raise_for_status()
                    if "html" not in response.headers.get("content-type", "").lower():
                        return None
                    content = response.content[: self.max_bytes]
                    break
                else:
                    return None
        except Exception:
            return None
        soup = BeautifulSoup(content, "html.parser")
        for node in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "aside"]):
            node.decompose()
        paragraphs = [" ".join(node.get_text(" ", strip=True).split()) for node in soup.select("article p, main p, p")]
        excerpt = " ".join(part for part in paragraphs if len(part) >= 35)[:4000]
        if len(excerpt) < 20:
            excerpt = " ".join(hit.snippet.split())[:4000]
        if len(excerpt) < 20:
            return None
        title_node = soup.find("title")
        title = " ".join((title_node.get_text(" ", strip=True) if title_node else hit.title).split())[:300]
        publisher = (urlsplit(current_url).hostname or hit.publisher or "unknown").removeprefix("www.")
        return EvidenceSource(
            url=current_url,
            title=title or hit.title[:300],
            publisher=publisher[:160],
            published_at=_parse_published_at(soup) or hit.published_at,
            source_type=_source_type(current_url),
            excerpt=excerpt,
        )


BANNED_JARGON = (
    "ga",
    "preview",
    "general availability",
    "model card",
    "reasoning",
    "workload",
    "agent run",
    "cache-aware",
    "cache hit",
    "cache miss",
    "pipeline",
    "retry",
)


def _jargon_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in BANNED_JARGON if re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", lowered)]


def _ensure_plain_russian_script(plan: ScriptPlan) -> None:
    all_text = " ".join(line.narration for line in plan.lines)
    hits = _jargon_hits(all_text)
    if hits:
        raise ResearchToScriptError(f"script contains banned technical jargon: {', '.join(hits)}")
    if not re.search(r"[А-Яа-яЁё]", all_text):
        raise ResearchToScriptError("script must be written in Russian")
    if re.search(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", all_text):
        raise ResearchToScriptError("script contains non-Russian CJK text")
    proof_lines = [line for line in plan.lines if line.kind == "fact"]
    dense = [line.kind for line in proof_lines if len(line.narration.split()) > 24 or len(line.narration) > 150]
    if dense:
        raise ResearchToScriptError("script contains an overlong proof beat; split or simplify it")


def _short_copy(text: str, *, max_words: int = 24, max_chars: int = 150) -> str:
    """Shorten proof copy at a word boundary for safe vertical-video reading."""
    words: list[str] = []
    for word in text.split():
        candidate = " ".join([*words, word])
        if len(words) >= max_words or len(candidate) > max_chars:
            break
        words.append(word)
    result = " ".join(words).rstrip(" ,;:-")
    if not result:
        return ""
    return result if result.endswith((".", "!", "?")) else result + "."


def _validate_comparison_proof(proof: ComparisonProof, research: ResearchPack, request: ResearchToScriptRequest) -> None:
    claim_ids = {claim.claim_id for claim in research.claims}
    source_urls = {_normalise_url(source.url) for source in research.sources}
    if not set(proof.evidence_claim_ids) <= claim_ids:
        raise ResearchToScriptError("comparison proof references unknown evidence claims")
    if request.comparison_models and set(request.comparison_models) - set(proof.models):
        raise ResearchToScriptError("comparison proof does not include every requested model")
    if proof.mode == "proposed" and proof.outcome != "inconclusive":
        raise ResearchToScriptError("proposed comparison cannot declare a winner")
    if proof.mode == "observed":
        if not proof.evidence_claim_ids:
            raise ResearchToScriptError("observed comparison requires linked evidence claims")
        if not proof.asset_urls:
            raise ResearchToScriptError("observed comparison requires a reproducible result or source asset URL")
        if not {_normalise_url(url) for url in proof.asset_urls} <= source_urls:
            raise ResearchToScriptError("comparison proof asset URLs must come from extracted research")
    if request.require_observed_comparison and proof.mode != "observed":
        raise ResearchToScriptError("topic requires an observed comparison but no reproducible proof was found")


def _script_with_comparison(script: ScriptPlan, proof: ComparisonProof) -> ScriptPlan:
    """Replace generic middle beats with a task-first side-by-side proof sequence."""
    cta = script.lines[-1]
    hook = script.lines[0]
    evidence = list(proof.evidence_claim_ids)
    if proof.mode == "observed":
        result = _short_copy(proof.strength)
        caveat = _short_copy(f"Но {proof.weakness} {proof.disclosure}")
    else:
        result = _short_copy(f"Победителя пока нет: {proof.strength}")
        caveat = _short_copy(f"Проверяйте так: {proof.criterion}. {proof.disclosure}")
    lines = [
        ScriptLine(kind="hook", narration=hook.narration, scene_intent="comparison_hook"),
        ScriptLine(kind="fact", narration=_short_copy(f"Одна задача для всех: {proof.task}"), evidence_claim_ids=evidence, scene_intent="comparison_setup"),
        ScriptLine(kind="fact", narration=result, evidence_claim_ids=evidence, scene_intent="comparison_result"),
        ScriptLine(kind="interpretation", narration=caveat, evidence_claim_ids=evidence, scene_intent="comparison_caveat"),
        ScriptLine(kind="cta", narration=cta.narration, scene_intent="cta"),
    ]
    return ScriptPlan(research_id=script.research_id, title=script.title, lines=lines, cta_handle=script.cta_handle)


_OFFICIAL_TOPIC_DOMAINS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("openai", "chatgpt", "gpt-"), "developers.openai.com"),
    (("anthropic", "claude", "sonnet", "opus", "haiku"), "platform.claude.com"),
    (("gemini", "deepmind"), "ai.google.dev"),
    (("deepseek",), "api-docs.deepseek.com"),
    (("grok", "xai"), "docs.x.ai"),
    (("mistral",), "docs.mistral.ai"),
)


def _official_domain_for_topic(topic: str) -> str | None:
    lowered = topic.lower()
    for hints, domain in _OFFICIAL_TOPIC_DOMAINS:
        if any(hint in lowered for hint in hints):
            return domain
    return None


def _official_seed_hits_for_topic(topic: str) -> list[SearchHit]:
    """Known current official routes for narrow, high-risk provider documentation topics."""
    lowered = topic.lower()
    if _official_domain_for_topic(topic) == "developers.openai.com" and any(marker in lowered for marker in ("лимит", "огранич", "rate limit")):
        return [SearchHit(
            title="Rate limits | OpenAI API",
            url="https://developers.openai.com/api/docs/guides/rate-limits",
            publisher="developers.openai.com",
        )]
    if _official_domain_for_topic(topic) == "platform.claude.com":
        return [SearchHit(
            title="Models overview | Claude Platform",
            url="https://platform.claude.com/docs/en/about-claude/models/overview",
            publisher="platform.claude.com",
        )]
    return []


_ARCHETYPE_SPECS: dict[str, tuple[list[str], list[str]]] = {
    "release": (["official change", "independent context", "who benefits"], ["hook", "evidence", "proof", "takeaway", "cta"]),
    "comparison": (["same-task method", "independent benchmark", "limits"], ["hook", "evidence", "proof", "takeaway", "cta"]),
    "how_to": (["official instructions", "practical steps", "common limits"], ["hook", "explanation", "instruction", "takeaway", "cta"]),
    "case_study": (["case context", "measured result", "repeatability"], ["hook", "explanation", "proof", "takeaway", "cta"]),
    "cost_saving": (["official pricing", "usage conditions", "total cost"], ["hook", "evidence", "proof", "takeaway", "cta"]),
    "incident": (["primary report", "independent reporting", "safe action"], ["hook", "evidence", "proof", "takeaway", "cta"]),
    "myth_fact": (["claim origin", "primary evidence", "practical correction"], ["hook", "explanation", "proof", "takeaway", "cta"]),
    "explainer": (["definition", "mechanism", "practical consequence"], ["hook", "explanation", "evidence", "takeaway", "cta"]),
    "trend": (["multiple current sources", "counterexamples", "viewer impact"], ["hook", "evidence", "proof", "takeaway", "cta"]),
}


def _route_topic(request: ResearchToScriptRequest) -> TopicPlan:
    lowered = request.topic.lower()
    explicit = request.content_archetype
    if explicit != "auto":
        archetype = explicit
    elif request.comparison_mode != "none" or any(marker in lowered for marker in (" против ", " vs ", "сравнен", "что выбрать")):
        archetype = "comparison"
    elif request.release_topic or any(marker in lowered for marker in ("релиз", "вышел", "выход", "анонс", "обновлен")):
        archetype = "release"
    elif any(marker in lowered for marker in ("миф", "правда ли", "заблужд")):
        archetype = "myth_fact"
    elif any(marker in lowered for marker in ("ошиб", "сбой", "слом", "провал", "вред", "утечк", "инцидент")):
        archetype = "incident"
    elif any(marker in lowered for marker in ("дешев", "бесплат", "цена", "стоимост", "эконом")):
        archetype = "cost_saving"
    elif any(marker in lowered for marker in ("как ", "инструк", "настро", "сделать", "гайд")):
        archetype = "how_to"
    elif any(marker in lowered for marker in ("кейс", "история", "пример", "применен")):
        archetype = "case_study"
    elif any(marker in lowered for marker in ("тренд", "почему все", "рынок", "меняется")):
        archetype = "trend"
    else:
        archetype = "explainer"
    focus, roles = _ARCHETYPE_SPECS[archetype]
    return TopicPlan(archetype=archetype, source_focus=focus, preferred_scene_roles=roles, reason=f"Тема направлена в archetype {archetype} по явному выбору или смысловым маркерам.")


def _queries_for(topic: str, max_queries: int, topic_plan: TopicPlan | None = None) -> list[str]:
    plan = topic_plan or TopicPlan(archetype="explainer", source_focus=_ARCHETYPE_SPECS["explainer"][0], preferred_scene_roles=_ARCHETYPE_SPECS["explainer"][1], reason="Fallback explainer route.")
    official_domain = _official_domain_for_topic(topic)
    primary = f"site:{official_domain} {topic}" if official_domain else f"{topic} официальный источник"
    archetype_queries: dict[str, list[str]] = {
        "release": [primary, f"{topic} независимый разбор", f"{topic} что изменилось ограничения", f"{topic} кому полезно"],
        "comparison": [primary, f"{topic} одинаковая задача benchmark методика", f"{topic} независимое сравнение ограничения", f"{topic} side by side test"],
        "how_to": [primary, f"{topic} практическая инструкция шаги", f"{topic} типичные ошибки ограничения", f"{topic} кейс применения результат"],
        "case_study": [primary, f"{topic} кейс измеримый результат", f"{topic} условия и ограничения кейса", f"{topic} независимый разбор"],
        "cost_saving": [primary, f"{topic} официальный тариф условия", f"{topic} реальная стоимость использование", f"{topic} бесплатный доступ ограничения"],
        "incident": [primary, f"{topic} первичный отчёт причина", f"{topic} независимое расследование", f"{topic} как снизить риск"],
        "myth_fact": [primary, f"{topic} проверка фактов источник", f"{topic} распространённое заблуждение", f"{topic} практическое объяснение"],
        "explainer": [primary, f"{topic} как работает простое объяснение", f"{topic} практическое применение ограничения", f"{topic} независимый пример"],
        "trend": [primary, f"{topic} свежий независимый анализ", f"{topic} контрпример ограничения", f"{topic} влияние на пользователей"],
    }
    return archetype_queries[plan.archetype][:max_queries]


def _topic_terms(topic: str) -> set[str]:
    ignored = {"как", "что", "это", "для", "про", "или", "api", "llm", "модель", "проверить", "новый", "новая", "новые"}
    return {word.lower() for word in re.findall(r"[A-Za-zА-Яа-яЁё0-9-]+", topic) if len(word) >= 4 and word.lower() not in ignored}


def _rank_hit_for_topic(hit: SearchHit, topic: str) -> int:
    text = " ".join((hit.title, hit.url, hit.snippet)).lower()
    terms = _topic_terms(topic)
    score = sum(text.count(term) for term in terms) * 4
    source_type = _source_type(hit.url)
    if source_type == "primary":
        score += 5
    elif source_type == "reputable_reporting":
        score += 3
    if hit.url in {seed.url for seed in _official_seed_hits_for_topic(topic)}:
        score += 100
    return score


def _deduplicate_hits(hits: Iterable[SearchHit]) -> list[SearchHit]:
    seen: set[str] = set()
    output: list[SearchHit] = []
    for item in hits:
        url = _normalise_url(item.url)
        if not _is_safe_public_url(url) or url in seen:
            continue
        seen.add(url)
        output.append(SearchHit(title=item.title, url=url, snippet=item.snippet, publisher=item.publisher, published_at=item.published_at))
    return output


def _style_kit_for(request: ResearchToScriptRequest) -> str:
    names = set(registry.style_kit_names())
    requested = request.style_family
    if requested:
        if requested not in names:
            raise ResearchToScriptError(f"unknown renderer style family {requested!r}")
        return requested
    return "llm_hubs_neon" if "llm_hubs_neon" in names else sorted(names)[0]


def _scene_for_role(role: str, used: set[str]) -> str:
    matches = []
    for manifest in all_scenes(tier=CapabilityTier.PRESET):
        if manifest.name in used or manifest.data_driven:
            continue
        tags = {item.lower() for item in manifest.intent_tags}
        score = 5 if role in tags else 0
        score += 2 if (role == "hook" and ("launch" in tags or "announcement" in tags)) else 0
        score += 2 if (role in {"evidence", "proof"} and ("research" in tags or "evidence" in tags)) else 0
        score += 2 if (role == "cta" and "cta" in tags) else 0
        matches.append((score, manifest.name))
    if not matches:
        raise ResearchToScriptError(f"live scene catalog has no unused safe preset for role {role!r}")
    matches.sort(key=lambda item: (-item[0], item[1].lower()))
    return matches[0][1]


_COMPARISON_SCENE_PREFERENCES: dict[str, tuple[str, ...]] = {
    "comparison_hook": ("ColdOpenContradiction", "KineticPhrase", "HookStack"),
    "comparison_setup": ("PromptABLab", "DecisionTree", "MythFact"),
    "comparison_result": ("EvidenceConflictBoard", "BenchmarkArena", "BeforeAfterLens"),
    "comparison_caveat": ("ClaimEvidenceChain", "EvidenceConflictBoard", "DecisionGrid"),
}
_COMPARISON_DATA_SCENES = {"ColdOpenContradiction", "PromptABLab", "EvidenceConflictBoard", "ClaimEvidenceChain"}


def _comparison_scene_props(preset: str, proof: ComparisonProof) -> dict[str, Any]:
    left, right = proof.models[0], proof.models[1]
    task = _short_copy(proof.task, max_words=16, max_chars=110)
    prompt = _short_copy(proof.prompt_summary, max_words=16, max_chars=110)
    criterion = _short_copy(proof.criterion, max_words=16, max_chars=110)
    strength = _short_copy(proof.strength, max_words=16, max_chars=110)
    weakness = _short_copy(proof.weakness, max_words=16, max_chars=110)
    disclosure = _short_copy(proof.disclosure, max_words=16, max_chars=110)
    if preset == "ColdOpenContradiction":
        return {"title": "ОДИН ЗАПРОС. ДВА РЕЗУЛЬТАТА.", "claimA": left, "claimB": right, "realQuestion": task, "proofLabel": criterion}
    if preset == "PromptABLab":
        return {"title": task, "promptA": f"{left}: {prompt}", "promptB": f"{right}: {prompt}", "resultA": left, "resultB": right, "rubric": criterion}
    if preset == "EvidenceConflictBoard":
        return {"title": "РЕЗУЛЬТАТ СРАВНЕНИЯ", "claim": strength, "sourceA": left, "sourceB": right, "difference": weakness}
    if preset == "ClaimEvidenceChain":
        return {"title": "ГРАНИЦА ВЫВОДА", "claim": strength, "evidence": criterion, "caveat": disclosure}
    return {}


def _scene_for_comparison_intent(intent: str, used: set[str], manifests: Mapping[str, Any]) -> str:
    for name in _COMPARISON_SCENE_PREFERENCES.get(intent, ()):
        manifest = manifests.get(name)
        if manifest is not None and name not in used and (not manifest.data_driven or name in _COMPARISON_DATA_SCENES):
            return name
    role = {"comparison_hook": "hook", "comparison_setup": "evidence", "comparison_result": "proof", "comparison_caveat": "takeaway"}.get(intent, "explanation")
    return _scene_for_role(role, used)


def _storyboard_from_script(
    request: ResearchToScriptRequest,
    research: ResearchPack,
    script: ScriptPlan,
    *,
    comparison_proof: ComparisonProof | None = None,
) -> StoryboardDraft:
    style = _style_kit_for(request)
    used: set[str] = set()
    roles = {"hook": "hook", "fact": "evidence", "interpretation": "proof", "instruction": "takeaway", "cta": "cta"}
    scenes: list[StoryboardScene] = []
    manifests = {item.name: item for item in all_scenes(tier=CapabilityTier.PRESET)}
    for line in script.lines:
        preset = _scene_for_comparison_intent(line.scene_intent, used, manifests) if comparison_proof else _scene_for_role(roles.get(line.kind, "explanation"), used)
        used.add(preset)
        manifest = manifests[preset]
        text = (line.on_screen_text or line.narration).strip()
        title = script.title if line.kind == "hook" else None
        # Match StoryboardValidator exactly: the hook title is visible copy too.
        duration = int(max(1.0, len((title or "") + text) / READ_CHARS_PER_SEC) * FPS)
        scenes.append(StoryboardScene(
            preset=preset,
            title=title,
            text=text,
            props=_comparison_scene_props(preset, comparison_proof) if comparison_proof else {},
            style_kit=style,
            duration_in_frames=duration,
            audio=AudioPolicy(mode="suggest", music_mood="focused" if line.kind in {"fact", "instruction"} else "energetic", sfx_roles=manifest.recommended_audio_roles),
            evidence_claim_ids=list(line.evidence_claim_ids),
        ))
    draft = StoryboardDraft(
        project_id=request.project_id,
        title=script.title,
        language="ru",
        scenes=scenes,
        default_style_kit=style,
        research_id=research.research_id,
        script_id=script.script_id,
        capability_tier=CapabilityTier.PRESET,
    )
    validation = StoryboardValidator(tier=CapabilityTier.PRESET).validate(draft, research=research)
    if not validation.valid:
        messages = "; ".join(item.message for item in validation.diagnostics if item.severity.value == "error")
        raise ResearchToScriptError(f"generated storyboard failed validation: {messages}")
    if len({scene.preset for scene in scenes}) != len(scenes):
        raise ResearchToScriptError("generated storyboard repeats a scene preset")
    if {scene.style_kit for scene in scenes} != {style}:
        raise ResearchToScriptError("generated storyboard must use exactly one style family")
    return draft


_COMMUNITY_HOSTS: dict[str, tuple[str, ...]] = {
    "youtube": ("youtube.com", "youtu.be"),
    "x": ("x.com", "twitter.com"),
    "reddit": ("reddit.com",),
}


def _community_platform(url: str) -> str | None:
    host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
    for platform, hosts in _COMMUNITY_HOSTS.items():
        if any(host == item or host.endswith(f".{item}") for item in hosts):
            return platform
    return None


def _community_lead_from_hit(hit: SearchHit) -> CommunityProofLead | None:
    platform = _community_platform(hit.url)
    if platform is None:
        return None
    text = " ".join((hit.title, hit.snippet)).strip()
    lowered = text.lower()
    completeness: list[str] = []
    if any(marker in lowered for marker in ("prompt", "запрос", "задач", "test")):
        completeness.append("task_visible")
    if any(marker in lowered for marker in ("vs", "против", "сравнен", "side by side")):
        completeness.append("both_outputs_visible")
    if any(marker in lowered for marker in ("одинаков", "same", "настрой", "услов")):
        completeness.append("conditions_visible")
    if any(marker in lowered for marker in ("score", "оцен", "benchmark", "тест", "результат")):
        completeness.append("criterion_visible")
    summary = (hit.snippet or f"Публичный community-пост: {hit.title}").strip()
    return CommunityProofLead(
        platform=platform,
        url=_normalise_url(hit.url),
        title=hit.title.strip()[:240] or platform,
        summary=summary[:500],
        task_summary=hit.snippet[:240] or None,
        evidence_completeness=completeness,
    )


class ResearchToScriptState(TypedDict, total=False):
    request: ResearchToScriptRequest
    topic_plan: TopicPlan
    queries: list[str]
    hits: list[SearchHit]
    sources: list[EvidenceSource]
    research: ResearchPack
    comparison_proofs: list[ComparisonProof]
    community_leads: list[CommunityProofLead]
    script: ScriptPlan
    storyboard: StoryboardDraft
    milestones: list[ResearchMilestone]
    warnings: list[str]


class ResearchToScriptWorkflow:
    """LangGraph orchestration from one topic to a validated local storyboard."""

    def __init__(
        self,
        *,
        search_provider: SearchProvider | None = None,
        extractor: PublicPageExtractor | None = None,
        llm: StructuredResearchLLM | None = None,
    ) -> None:
        self.search_provider = search_provider
        self.extractor = extractor or PublicPageExtractor(
            timeout_seconds=float(os.environ.get("MSF_RESEARCH_TIMEOUT_SECONDS", "15"))
        )
        self.llm = llm or OpenAIResearchLLM()
        self.graph = self._build_graph()

    @staticmethod
    def _event(phase: ResearchMilestone["phase"], message: str, **counts: int) -> ResearchMilestone:  # type: ignore[name-defined]
        return ResearchMilestone(phase=phase, message=message, counts=counts)

    def _provider_for(self, request: ResearchToScriptRequest) -> SearchProvider:
        if self.search_provider is not None:
            return self.search_provider
        if request.provider == "searxng":
            return SearxngSearchProvider(timeout_seconds=self.extractor.timeout_seconds)
        return DuckDuckGoSearchProvider()

    def _route_topic(self, state: ResearchToScriptState) -> ResearchToScriptState:
        plan = _route_topic(state["request"])
        return {"topic_plan": plan, "milestones": [self._event("topic_routed", "Выбран сценарный угол и research focus для темы.", archetype=1)]}

    def _plan_queries(self, state: ResearchToScriptState) -> ResearchToScriptState:
        request = state["request"]
        queries = _queries_for(request.topic, request.max_queries, state["topic_plan"])
        events = list(state.get("milestones", []))
        events.append(self._event("query_plan_created", "Сформирован план проверки темы по выбранному сценарному углу.", queries=len(queries)))
        return {"queries": queries, "milestones": events}

    def _collect_sources(self, state: ResearchToScriptState) -> ResearchToScriptState:
        request = state["request"]
        provider = self._provider_for(request)
        # Pinned URLs are candidate pages, not pre-approved evidence. They travel
        # through the same extractor and claim validator as search results.
        pinned_hits = [
            SearchHit(
                title=f"Pinned source: {item.reason[:120]}",
                url=_normalise_url(item.url),
                snippet=f"operator-pinned {item.mode}: {item.reason}",
                publisher=(urlsplit(item.url).hostname or "operator-pinned"),
            )
            for item in request.pinned_sources
        ]
        gathered: list[SearchHit] = [*pinned_hits, *_official_seed_hits_for_topic(request.topic)]
        per_query = max(2, min(4, request.max_sources))
        for query in state["queries"]:
            gathered.extend(provider.search(query, limit=per_query))
        hits = _deduplicate_hits(gathered)
        pinned_order = {_normalise_url(item.url): index for index, item in enumerate(request.pinned_sources)}
        hits.sort(key=lambda item: (0 if _normalise_url(item.url) in pinned_order else 1, pinned_order.get(_normalise_url(item.url), 999), -_rank_hit_for_topic(item, request.topic), item.url))
        # Never trim a user-required URL out of the candidate list merely because
        # open-web search returned many popular pages.
        hits = hits[: max(request.max_sources * 2, len(pinned_hits))]
        if len(hits) < 2:
            raise ResearchToScriptError("research found fewer than two safe public source candidates")
        events = list(state.get("milestones", []))
        events.append(self._event("sources_collected", "Собраны и очищены кандидаты источников.", candidates=len(hits), pinned=len(pinned_hits)))
        return {"hits": hits, "milestones": events}

    def _discover_community_leads(self, state: ResearchToScriptState) -> ResearchToScriptState:
        request = state["request"]
        if request.community_proof_mode == "off" or request.max_community_leads == 0:
            return {"community_leads": []}
        provider = self._provider_for(request)
        gathered: list[SearchHit] = []
        for platform in request.community_platforms:
            hosts = _COMMUNITY_HOSTS[platform]
            query = f"site:{hosts[0]} {request.topic} same prompt comparison test"
            try:
                gathered.extend(provider.search(query, limit=3))
            except ResearchToScriptError:
                continue
        leads: list[CommunityProofLead] = []
        seen: set[str] = set()
        for hit in _deduplicate_hits(gathered):
            lead = _community_lead_from_hit(hit)
            if lead is None or lead.platform not in request.community_platforms or lead.url in seen:
                continue
            seen.add(lead.url)
            leads.append(lead)
            if len(leads) >= request.max_community_leads:
                break
        events = list(state.get("milestones", []))
        events.append(self._event("community_proof_discovered", "Найдены community comparison leads для ручной редакторской проверки.", leads=len(leads)))
        return {"community_leads": leads, "milestones": events}

    def _fetch_evidence(self, state: ResearchToScriptState) -> ResearchToScriptState:
        request = state["request"]
        sources: list[EvidenceSource] = []
        seen_urls: set[str] = set()
        pinned_by_url = {_normalise_url(item.url): item for item in request.pinned_sources}
        resolved_pinned: set[str] = set()
        processed_context = 0
        for hit in state["hits"]:
            requested_url = _normalise_url(hit.url)
            pinned = pinned_by_url.get(requested_url)
            # Required source candidates stay eligible even after ordinary evidence
            # reaches its budget; they must produce a success or a visible failure.
            if len(sources) >= request.max_sources and not (pinned and pinned.mode == "required"):
                continue
            source = self.extractor.extract(hit)
            if source is None:
                continue
            if source.source_type == "community":
                # Community links are review leads, never factual evidence. A
                # required community URL must therefore fail transparently.
                continue
            if pinned and pinned.mode == "context_only":
                processed_context += 1
                resolved_pinned.add(requested_url)
                continue
            if source.url in seen_urls:
                if pinned:
                    resolved_pinned.add(requested_url)
                continue
            seen_urls.add(source.url)
            sources.append(source)
            if pinned:
                resolved_pinned.add(requested_url)
        missing_required = [item.url for item in request.pinned_sources if item.mode == "required" and _normalise_url(item.url) not in resolved_pinned]
        if missing_required:
            names = ", ".join(urlsplit(url).hostname or url for url in missing_required[:3])
            raise ResearchToScriptError(f"required pinned source could not be extracted as safe factual evidence: {names}")
        if len(sources) < 2:
            raise ResearchToScriptError("research could not extract at least two public source excerpts")
        official_domain = _official_domain_for_topic(request.topic)
        if official_domain and not any((urlsplit(source.url).hostname or "").lower().endswith(official_domain) for source in sources):
            raise ResearchToScriptError(f"research requires an extracted official source from {official_domain} for this provider topic")
        events = list(state.get("milestones", []))
        if request.pinned_sources:
            events.append(self._event("pinned_sources_processed", "Обработаны закреплённые оператором публичные источники.", pinned=len(request.pinned_sources), context_only=processed_context, required=len([item for item in request.pinned_sources if item.mode == "required"])))
        events.append(self._event("pages_extracted", "Извлечены краткие фрагменты публичных страниц.", sources=len(sources)))
        return {"sources": sources, "milestones": events}

    def _build_claims(self, state: ResearchToScriptState) -> ResearchToScriptState:
        request = state["request"]
        sources = state["sources"]
        source_rows = [{"url": item.url, "title": item.title, "publisher": item.publisher, "excerpt": item.excerpt} for item in sources]
        raw = self.llm.complete("evidence_claims", {"topic": request.topic, "sources": source_rows, "maximum_claims": 4})
        # Keep the contract compact without discarding an otherwise evidence-linked
        # claim when the structured model returns more than three citations.
        if isinstance(raw, Mapping) and isinstance(raw.get("claims"), list):
            raw = dict(raw)
            raw["claims"] = [
                {**item, "source_urls": item.get("source_urls", [])[:3]}
                if isinstance(item, Mapping) and isinstance(item.get("source_urls"), list) else item
                for item in raw["claims"]
            ]
        try:
            generated = _ClaimsPayload.model_validate(raw)
        except ValidationError as exc:
            raise ResearchToScriptError(f"claim extraction violates contract: {exc}") from exc
        source_by_url = {_normalise_url(source.url): source for source in sources}
        claims: list[EvidenceClaim] = []
        for item in generated.claims:
            linked = [_normalise_url(url) for url in item.source_urls]
            verified_links = [url for url in linked if url in source_by_url]
            # An LLM may append a plausible but unextracted URL. It cannot become
            # evidence: retain only explicit links from this ResearchPack, or drop
            # the claim when none of its citations were actually retrieved.
            if not verified_links:
                continue
            linked_sources = [source_by_url[url] for url in verified_links]
            if linked_sources and all(source.source_type == "community" for source in linked_sources):
                continue
            needs_primary = any(token in item.statement.lower() for token in ("цена", "стоимость", "бесплат", "free", "price", "availability", "доступ"))
            if needs_primary and not any(is_primaryish(source) for source in linked_sources):
                # Do not promote an unsupported price/availability assertion into
                # a video claim simply because a lower-quality page mentioned it.
                continue
            claims.append(EvidenceClaim(
                statement=item.statement,
                source_ids=[source.source_id for source in linked_sources],
                confidence=item.confidence,
                claim_type=item.claim_type,
            ))
        if not claims:
            raise ResearchToScriptError("claim extraction produced no claims linked to extracted research")
        pack = ResearchPack(topic=request.topic, release_topic=request.release_topic, sources=sources, claims=claims, summary=generated.summary)
        return {"research": pack}

    def _validate_evidence(self, state: ResearchToScriptState) -> ResearchToScriptState:
        research = state["research"]
        try:
            warnings = validate_research_pack(research)
        except ResearchQualityError as exc:
            raise ResearchToScriptError(f"evidence validation failed: {exc}") from exc
        events = list(state.get("milestones", []))
        events.append(self._event("claims_validated", "Утверждения связаны с источниками и прошли evidence gate.", claims=len(research.claims), sources=len(research.sources)))
        return {"warnings": warnings, "milestones": events}

    def _build_comparison_proof(self, state: ResearchToScriptState) -> ResearchToScriptState:
        request = state["request"]
        if request.comparison_mode == "none":
            return {"comparison_proofs": []}
        research = state["research"]
        source_by_id = {source.source_id: source for source in research.sources}
        raw = self.llm.complete("comparison_proof", {
            "topic": request.topic,
            "requested_mode": request.comparison_mode,
            "requested_models": request.comparison_models,
            "requested_visual_mode": request.visual_evidence_mode,
            "claims": [
                {"claim_id": claim.claim_id, "statement": claim.statement, "source_urls": [source_by_id[source_id].url for source_id in claim.source_ids]}
                for claim in research.claims
            ],
            "source_urls": [source.url for source in research.sources],
            "instruction": "Найди один честный side-by-side proof. Если источники не описывают одинаковую задачу и результат двух моделей, верни proposed/inconclusive. Для observed добавь только URL из source_urls и evidence_claim_ids только из claims.",
        })
        try:
            payload = _ComparisonProofPayload.model_validate(raw)
            proof = ComparisonProof.model_validate(payload.model_dump())
        except ValidationError as exc:
            raise ResearchToScriptError(f"comparison proof violates contract: {exc}") from exc
        if request.comparison_mode == "proposed" and proof.mode != "proposed":
            raise ResearchToScriptError("proposed comparison request cannot emit an observed winner")
        _validate_comparison_proof(proof, research, request)
        warnings = list(state.get("warnings", []))
        if request.comparison_mode == "observed" and proof.mode == "proposed":
            warnings.append("Не найден воспроизводимый observed side-by-side proof; подготовлен только план честного теста.")
        events = list(state.get("milestones", []))
        events.append(self._event("comparison_proof_validated", "Собрано доказательное сравнение: задача, условия, результат и оговорка.", proofs=1))
        return {"comparison_proofs": [proof], "warnings": warnings, "milestones": events}

    def _compose_script(self, state: ResearchToScriptState) -> ResearchToScriptState:
        request = state["request"]
        research = state["research"]
        usable = [claim for claim in research.claims if claim.claim_type in {"fact", "interpretation"}]
        selected = usable[:2]
        if not selected:
            raise ResearchToScriptError("research has no factual claims suitable for a short video")
        raw = self.llm.complete("script_copy", {
            "topic": request.topic,
            "audience": request.audience,
            "content_archetype": state["topic_plan"].archetype,
            "content_focus": state["topic_plan"].source_focus,
            "claims": [{"claim_id": item.claim_id, "statement": item.statement} for item in selected],
            "instruction": "Верни по одной короткой понятной перефразировке для каждого утверждения в factual_narrations: максимум 24 слова и 150 символов. Пиши только по-русски, без иероглифов, сокращений и англицизмов без объяснения.",
            "cta_asset": request.cta_asset,
            "cta_handle": request.cta_handle,
        })
        try:
            copy = _ScriptCopyPayload.model_validate(raw)
        except ValidationError as exc:
            raise ResearchToScriptError(f"script copy violates contract: {exc}") from exc
        if not copy.factual_narrations:
            raise ResearchToScriptError("script copy must provide at least one plain-language proof beat")
        if len(copy.factual_narrations) > len(selected):
            raise ResearchToScriptError("script copy returned proof beats without matching evidence claims")
        # A single clean proof is preferable to inventing a second paraphrase.
        # Keep the angle intentionally narrow when the model returns fewer beats.
        selected = selected[:len(copy.factual_narrations)]
        if any(len(item) > 150 or len(item.split()) > 24 for item in copy.factual_narrations):
            raise ResearchToScriptError("script copy contains an overlong proof beat")
        angle = StoryAngle(
            claim_ids=tuple(item.claim_id for item in selected),
            factual_narrations=tuple(copy.factual_narrations),
            takeaway=copy.takeaway,
            takeaway_claim_ids=tuple(item.claim_id for item in selected),
            cta_asset=request.cta_asset,
            cta_text=copy.cta_text,
        )
        try:
            script = plan_from_angle(title=copy.title, research=research, hook=copy.hook, angle=angle, cta_handle=request.cta_handle)
        except ScriptQualityError as exc:
            raise ResearchToScriptError(f"script policy failed: {exc}") from exc
        comparison_proofs = state.get("comparison_proofs", [])
        if comparison_proofs:
            script = _script_with_comparison(script, comparison_proofs[0])
        _ensure_plain_russian_script(script)
        events = list(state.get("milestones", []))
        events.append(self._event("script_composed", "Собран короткий русскоязычный сценарий с конкретным Telegram-материалом.", lines=len(script.lines)))
        return {"script": script, "milestones": events}

    def _compose_storyboard(self, state: ResearchToScriptState) -> ResearchToScriptState:
        proofs = state.get("comparison_proofs", [])
        storyboard = _storyboard_from_script(state["request"], state["research"], state["script"], comparison_proof=proofs[0] if proofs else None)
        events = list(state.get("milestones", []))
        events.append(self._event("storyboard_validated", "Подобраны уникальные сцены из live catalog и единый visual style.", scenes=len(storyboard.scenes)))
        return {"storyboard": storyboard, "milestones": events}

    def _build_graph(self):
        graph = StateGraph(ResearchToScriptState)
        graph.add_node("route_topic", self._route_topic)
        graph.add_node("plan_queries", self._plan_queries)
        graph.add_node("collect_sources", self._collect_sources)
        graph.add_node("discover_community_leads", self._discover_community_leads)
        graph.add_node("fetch_evidence", self._fetch_evidence)
        graph.add_node("build_claims", self._build_claims)
        graph.add_node("validate_evidence", self._validate_evidence)
        graph.add_node("build_comparison_proof", self._build_comparison_proof)
        graph.add_node("compose_script", self._compose_script)
        graph.add_node("compose_storyboard", self._compose_storyboard)
        graph.set_entry_point("route_topic")
        graph.add_edge("route_topic", "plan_queries")
        graph.add_edge("plan_queries", "collect_sources")
        graph.add_edge("collect_sources", "discover_community_leads")
        graph.add_edge("discover_community_leads", "fetch_evidence")
        graph.add_edge("fetch_evidence", "build_claims")
        graph.add_edge("build_claims", "validate_evidence")
        graph.add_edge("validate_evidence", "build_comparison_proof")
        graph.add_edge("build_comparison_proof", "compose_script")
        graph.add_edge("compose_script", "compose_storyboard")
        graph.add_edge("compose_storyboard", END)
        return graph.compile()

    def run(self, request: ResearchToScriptRequest) -> ResearchToScriptResult:
        try:
            state = self.graph.invoke({"request": request})
            return ResearchToScriptResult(
                request=request,
                research=state["research"],
                script=state["script"],
                storyboard=state["storyboard"],
                comparison_proofs=state.get("comparison_proofs", []),
                topic_plan=state.get("topic_plan"),
                community_leads=state.get("community_leads", []),
                milestones=state.get("milestones", []),
                warnings=state.get("warnings", []),
            )
        except ResearchToScriptError:
            raise
        except Exception as exc:
            raise ResearchToScriptError(f"research-to-script workflow failed: {str(exc)[:300]}") from exc


__all__ = [
    "DuckDuckGoSearchProvider",
    "OpenAIResearchLLM",
    "PublicPageExtractor",
    "ResearchToScriptError",
    "ResearchToScriptWorkflow",
    "SearchHit",
    "SearchProvider",
    "SearxngSearchProvider",
    "_official_domain_for_topic",
    "_official_seed_hits_for_topic",
    "_rank_hit_for_topic",
    "_topic_terms",
    "StructuredResearchLLM",
    "_deduplicate_hits",
    "_is_safe_public_url",
]
