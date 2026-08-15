"""Versioned contracts for the MSF Studio v2 application layer.

These models deliberately sit beside the legacy ``msf.contracts`` package.  The
legacy package supports the retired Playwright/HTML pipeline; this module is the
public, schema-first boundary for the LangGraph + Remotion execution path.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


SPEC_VERSION = "2.0"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for persisted Studio records."""
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    """Create opaque stable IDs without exposing filesystem paths to clients."""
    return f"{prefix}_{uuid4().hex}"


class StudioModel(BaseModel):
    """Strict default base model for external Studio contracts."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AssetStatus(str, Enum):
    DRAFT = "draft"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class CapabilityTier(str, Enum):
    PRESET = "preset"
    CURATED = "curated"
    SANDBOX = "sandbox"
    RELEASE = "release"


class RunStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    QUEUED = "queued"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class EventLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ArtifactRef(StudioModel):
    """An artifact reference safe to return through API/MCP clients."""

    artifact_id: str = Field(default_factory=lambda: new_id("art"))
    kind: str
    name: str
    mime_type: str = "application/octet-stream"
    relative_uri: str
    size_bytes: Optional[int] = Field(default=None, ge=0)
    sha256: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class AudioPolicy(StudioModel):
    """Scene-level sound direction independent of any individual audio file."""

    mode: Literal["auto", "suggest", "manual", "off"] = "suggest"
    music_mood: Optional[str] = None
    sfx_roles: List[str] = Field(default_factory=list)
    music_asset_id: Optional[str] = None
    sfx_asset_ids: List[str] = Field(default_factory=list)


class StoryboardScene(StudioModel):
    """One editable scene block prior to conversion into a renderer VideoSpec."""

    scene_id: str = Field(default_factory=lambda: new_id("scene"))
    preset: str
    title: Optional[str] = None
    text: str = ""
    props: Dict[str, Any] = Field(default_factory=dict)
    effects: List[str] = Field(default_factory=list)
    style_kit: Optional[str] = None
    duration_in_frames: Optional[int] = Field(default=None, ge=1)
    audio: AudioPolicy = Field(default_factory=AudioPolicy)
    evidence_claim_ids: List[str] = Field(default_factory=list)


class StoryboardDraft(StudioModel):
    """Versioned editable storyboard owned by a project."""

    draft_id: str = Field(default_factory=lambda: new_id("sb"))
    project_id: str = "default"
    revision: int = Field(default=1, ge=1)
    spec_version: str = SPEC_VERSION
    title: str = "Untitled video"
    language: str = "ru"
    scenes: List[StoryboardScene] = Field(default_factory=list)
    default_style_kit: Optional[str] = None
    research_id: Optional[str] = None
    script_id: Optional[str] = None
    capability_tier: CapabilityTier = CapabilityTier.PRESET
    status: AssetStatus = AssetStatus.DRAFT
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ValidationDiagnostic(StudioModel):
    code: str
    severity: Severity
    message: str
    scene_index: Optional[int] = Field(default=None, ge=0)
    suggested_presets: List[str] = Field(default_factory=list)


class ValidationResult(StudioModel):
    draft_id: str
    valid: bool
    diagnostics: List[ValidationDiagnostic] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=utc_now)


class SceneManifest(StudioModel):
    """Machine-readable description of a scene available to an agent or UI."""

    asset_id: str
    name: str
    version: str = "1.0.0"
    status: AssetStatus = AssetStatus.STABLE
    capability_tier: CapabilityTier = CapabilityTier.PRESET
    category: str = "general"
    summary: str = ""
    fields: List[str] = Field(default_factory=list)
    intent_tags: List[str] = Field(default_factory=list)
    data_driven: bool = False
    three: bool = False
    rotation_safe: bool = False
    required_data_hints: List[str] = Field(default_factory=list)
    compatible_effect_families: List[str] = Field(default_factory=list)
    recommended_audio_roles: List[str] = Field(default_factory=list)
    demo_available: bool = False


class RunRequest(StudioModel):
    """Validated request to execute the canonical LangGraph + Remotion path."""

    request_id: str = Field(default_factory=lambda: new_id("req"))
    project_id: str = "default"
    storyboard_id: Optional[str] = None
    topic: str = Field(min_length=3, max_length=400)
    text: Optional[str] = None
    preset: str = "HeroKinetic"
    # Named renderer style plus safe JSON-compatible overrides; actual visual
    # validation remains in the VideoSpec renderer boundary.
    style: Optional[str] = None
    style_config: Optional[Dict[str, Any]] = None
    voice: Optional[str] = None
    research: bool = False
    music: bool = True
    sfx: bool = True
    agent_level: int = Field(default=3, ge=1, le=5)
    approved: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class RunSnapshot(StudioModel):
    run_id: str
    request_id: str
    project_id: str
    status: RunStatus
    current_node: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    artifacts: List[ArtifactRef] = Field(default_factory=list)
    output_artifact_id: Optional[str] = None


class TraceSpan(StudioModel):
    """A redacted operational span suitable for a dashboard or support export."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    run_id: str
    name: str
    status: Literal["running", "ok", "error"] = "running"
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: Optional[datetime] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class RunEvent(StudioModel):
    event_id: str = Field(default_factory=lambda: new_id("evt"))
    run_id: str
    sequence: int = Field(ge=1)
    timestamp: datetime = Field(default_factory=utc_now)
    type: str
    node: Optional[str] = None
    level: EventLevel = EventLevel.INFO
    message: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)


class EvidenceSource(StudioModel):
    source_id: str = Field(default_factory=lambda: new_id("src"))
    url: str
    title: str
    publisher: str
    retrieved_at: datetime = Field(default_factory=utc_now)
    # Publication time is distinct from retrieval time. It lets a release-news
    # workflow reject an old article rediscovered today and is optional so old
    # evergreen research packs remain valid.
    published_at: Optional[datetime] = None
    source_type: Literal["primary", "official_docs", "reputable_reporting", "community", "unknown"]
    excerpt: str = Field(min_length=20, max_length=4000)


class EvidenceClaim(StudioModel):
    claim_id: str = Field(default_factory=lambda: new_id("claim"))
    statement: str = Field(min_length=12, max_length=600)
    source_ids: List[str] = Field(min_length=1)
    confidence: Literal["high", "medium", "low"] = "medium"
    claim_type: Literal["fact", "interpretation", "recommendation"] = "fact"
    freshness_days: Optional[int] = Field(default=None, ge=0)


class ResearchPack(StudioModel):
    research_id: str = Field(default_factory=lambda: new_id("research"))
    topic: str = Field(min_length=3, max_length=400)
    # Release packs are held to a stronger freshness policy than evergreen
    # explainers. This makes editorial freshness an explicit contract rather
    # than an informal instruction that an agent can forget.
    release_topic: bool = False
    release_date: Optional[datetime] = None
    sources: List[EvidenceSource] = Field(min_length=1)
    claims: List[EvidenceClaim] = Field(min_length=1)
    summary: Optional[str] = Field(default=None, max_length=4000)
    created_at: datetime = Field(default_factory=utc_now)


class ScriptLine(StudioModel):
    line_id: str = Field(default_factory=lambda: new_id("line"))
    kind: Literal["hook", "fact", "interpretation", "instruction", "cta"]
    narration: str = Field(min_length=2, max_length=500)
    on_screen_text: Optional[str] = Field(default=None, max_length=180)
    evidence_claim_ids: List[str] = Field(default_factory=list)
    scene_intent: str = "explainer"


class ScriptPlan(StudioModel):
    script_id: str = Field(default_factory=lambda: new_id("script"))
    research_id: Optional[str] = None
    title: str = Field(min_length=3, max_length=160)
    language: str = "ru"
    lines: List[ScriptLine] = Field(min_length=2, max_length=16)
    cta_handle: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class CatalogSearchResult(StudioModel):
    query: str = ""
    total: int
    items: List[SceneManifest]


class ResearchToScriptRequest(StudioModel):
    """Bounded request for the evidence-first short-video planning workflow."""

    topic: str = Field(min_length=3, max_length=400)
    audience: str = Field(default="широкая русскоязычная аудитория", min_length=3, max_length=180)
    cta_handle: str = Field(default="@llm_hubs", min_length=2, max_length=80)
    cta_asset: str = Field(default="готовый чек-лист и ссылки на источники", min_length=3, max_length=240)
    style_family: Optional[str] = Field(default=None, max_length=80)
    release_topic: bool = False
    provider: Literal["duckduckgo", "searxng"] = "duckduckgo"
    max_queries: int = Field(default=4, ge=1, le=4)
    max_sources: int = Field(default=8, ge=2, le=12)
    project_id: str = Field(default="default", min_length=1, max_length=120)


class ResearchMilestone(StudioModel):
    """Safe high-level workflow event; never stores hidden model reasoning."""

    phase: Literal[
        "query_plan_created",
        "sources_collected",
        "pages_extracted",
        "claims_validated",
        "script_composed",
        "storyboard_validated",
    ]
    message: str = Field(min_length=1, max_length=400)
    counts: Dict[str, int] = Field(default_factory=dict)


class ResearchToScriptResult(StudioModel):
    """Validated local research, script and editable storyboard produced from one topic."""

    request: ResearchToScriptRequest
    research: ResearchPack
    script: ScriptPlan
    storyboard: StoryboardDraft
    milestones: List[ResearchMilestone] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
