# MSF Studio v2 — техническая спецификация вертикального среза

## 1. Назначение

MSF Studio v2 добавляет application layer поверх существующего LangGraph + Remotion pipeline. В v2 не заменяется renderer и не меняется TypeScript как источник истины для визуальных presets/effects/transitions/style kits. Вместо этого вводятся versioned Python contracts, asset catalog, storyboard preflight, run events и API/MCP adapters, которые обращаются к одному каноническому execution service.

## 2. Границы миграции

Текущий `msf/contracts/models.py` сохраняется как legacy contract layer для `PipelineOrchestrator`. Новый runtime не должен импортировать его типы для новых API, чтобы не смешивать старый Playwright/HTML pipeline с LangGraph/Remotion. Все v2-типы располагаются в `msf/studio/`.

```text
msf/
├── studio/
│   ├── __init__.py
│   ├── contracts.py       # Pydantic v2 domain/API contracts
│   ├── catalog.py         # scene/effect/audio discovery and manifests
│   ├── storyboard.py      # draft store + schema/readability validation
│   ├── events.py          # structured append-only event store
│   ├── runs.py            # canonical RunVideoJob façade and state lifecycle
│   ├── mcp_adapter.py     # transport-agnostic MCP application operations
│   └── assets.py          # stable/draft asset lifecycle helpers
├── panel/server.py        # thin REST endpoints over studio services
└── graph/video_graph.py   # existing renderer/orchestrator retained
```

## 3. Domain contracts

### 3.1 Identity and lifecycle

`StudioProject`, `StoryboardDraft`, `RunRequest`, `RunSnapshot`, `ArtifactRef` and `RunEvent` use explicit UUID-like identifiers, ownership fields, creation timestamp and `spec_version="2.0"`. Run state follows:

```text
DRAFT → VALIDATED → QUEUED → RUNNING → {COMPLETED | FAILED | CANCELLED}
                              ↘ RETRYING → RUNNING
```

The initial implementation is process-local and file-backed under `output/studio/`; the contract intentionally does not reveal absolute paths to API clients. The persistence adapter can later be replaced with SQLite/PostgreSQL without changing API/MCP schemas.

### 3.2 Asset lifecycle

Every manifest has `asset_id`, `kind`, semantic version, `status` (`stable`, `draft`, `deprecated`), `capability_tier`, tags, owner/release metadata and `compatibility`. Only `stable` assets are returned to preset-tier discovery by default.

### 3.3 Scene catalog

`SceneManifest` wraps live registry information from TypeScript with v2 metadata. Existing preset fields, category, summary and data-driven flags remain dynamically discovered. v2 adds `intent_tags`, required data hints, recommended audio roles and capability tier. Built-in overrides reside in `msf/studio/catalog_data.py`; unlisted scenes still appear with conservative defaults rather than disappearing.

### 3.4 Storyboard validation

`StoryboardScene` carries preset, title/text, arbitrary props, effects, style kit and audio policy. `StoryboardValidator` performs:

1. scene existence and stable-status checks;
2. gate against data-driven scene use without declared data fields;
3. readability budget using existing constants from `msf.spec`;
4. effect and style-kit existence checks from live registry;
5. duplicate/unsafe root-vs-scene audio guard;
6. compatibility checks and structured diagnostics.

Validation is advisory for a draft and strict before production render. It never fabricates fallback props. Each diagnostic has `code`, `severity`, `scene_index`, `message` and optional `suggested_presets`.

## 4. Canonical application service

`StudioRunService` is the sole v2 entry point for graph execution. It accepts a validated `RunRequest`, creates a run directory, persists the immutable request/spec, emits events and starts the existing `build_msf_graph()` in a controlled child process. A process wrapper preserves the current isolation benefits for CUDA/Node/ffmpeg and keeps the panel responsive.

The v2 service does not invoke the legacy `PipelineOrchestrator`. Existing `msf.cli` remains untouched for compatibility during this vertical slice, but README/technical docs mark it as legacy pending migration.

## 5. Event model

Every run writes JSONL events as the source of diagnostic truth. An event envelope is:

```json
{
  "event_id": "evt_…",
  "run_id": "run_…",
  "sequence": 7,
  "timestamp": "2026-08-14T…Z",
  "type": "node.completed",
  "node": "build_spec",
  "level": "info",
  "message": "VideoSpec validated",
  "payload": {"scene_count": 4}
}
```

Initial event types: `run.created`, `validation.completed`, `run.queued`, `run.started`, `node.started`, `node.completed`, `node.failed`, `artifact.created`, `run.completed`, `run.failed`, `run.cancelled`. Stdout is mirrored as a redacted `log.line` event only for compatibility. UI and MCP read events; they do not parse stdout.

## 6. MCP application adapter

`mcp_adapter.py` contains framework-independent methods designed for direct use from the official MCP Python SDK or test clients:

- `search_library(query, intent_tags, include_draft=False)`;
- `get_scene_manifest(scene_id)`;
- `create_storyboard_draft(project_id, scenes, policy)`;
- `validate_storyboard(draft_id)`;
- `get_run_snapshot(run_id)`;
- `get_run_events(run_id, after_sequence=0)`.

Production rendering is intentionally not auto-exposed in the first adapter. It is a `compute` capability that later requires explicit approval/quota policy. This prevents a new MCP integration from becoming an unbounded GPU-spend endpoint.

## 7. Panel API additions

All new endpoints are additive under `/api/studio/`:

| Endpoint | Operation |
|---|---|
| `GET /api/studio/catalog/scenes` | Filtered scene manifests and live registry data. |
| `GET /api/studio/catalog/scenes/{id}` | One full scene manifest. |
| `POST /api/studio/storyboards` | Create versioned draft. |
| `POST /api/studio/storyboards/{id}/validate` | Return structured validation result. |
| `GET /api/studio/runs/{id}` | Return snapshot without filesystem paths. |
| `GET /api/studio/runs/{id}/events` | Read events after sequence; suitable for polling/SSE adapter. |

## 8. New content assets

The v2 content pack adds at least three universal scenes that have broad business use and simple strict schemas:

- `StepList`: numbered explanation or procedure;
- `BeforeAfter`: direct comparison of an initial and final state;
- `MetricTrend`: one metric changing over time with labelled data points.

Each scene includes TypeScript component, registry entry, demo props, manifest metadata and sound-design roles. This first release proves the asset lifecycle without attempting an unverified bulk library expansion.

## 9. Tests

New tests must cover catalog discovery, stable/draft filtering, storyboard diagnostics, event sequence ordering, run directory isolation, MCP adapter responses and v2 panel endpoints. Existing tests remain the regression suite for the renderer/registry/audio behaviors.
