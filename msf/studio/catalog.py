"""Schema-first catalog backed by the live Remotion TypeScript registry."""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Optional

from msf import registry

from .assets import AssetVisibility, visible_assets
from .catalog_data import DEFAULT_AUDIO_ROLES, DEFAULT_INTENTS, SCENE_METADATA
from .contracts import AssetStatus, CapabilityTier, CatalogSearchResult, SceneManifest


class CatalogUnavailableError(RuntimeError):
    """Raised when the renderer source-of-truth registry cannot be parsed."""


@lru_cache(maxsize=1)
def _all_scene_manifests() -> tuple[SceneManifest, ...]:
    entries = registry.load_registry()
    if not entries:
        raise CatalogUnavailableError("TypeScript preset registry is unavailable; refusing stale fallback")
    effects = registry.load_effects()
    families = sorted({effect.family for effect in effects.values()})
    manifests: list[SceneManifest] = []
    for info in entries.values():
        metadata = SCENE_METADATA.get(info.name, {})
        manifests.append(
            SceneManifest(
                asset_id=f"scene:{info.name}@1.0.0",
                name=info.name,
                category=info.category,
                summary=info.summary,
                fields=list(info.fields),
                intent_tags=list(metadata.get("intent_tags", DEFAULT_INTENTS)),
                data_driven=info.data_driven,
                three=info.three,
                rotation_safe=info.rotation_safe,
                required_data_hints=list(metadata.get("required_data_hints", ())),
                compatible_effect_families=families,
                recommended_audio_roles=list(metadata.get("audio_roles", DEFAULT_AUDIO_ROLES)),
                demo_available=True,
            )
        )
    return tuple(sorted(manifests, key=lambda item: item.name.lower()))


def clear_catalog_cache() -> None:
    """Use after a renderer catalog release or while testing dynamic registry changes."""
    _all_scene_manifests.cache_clear()


def all_scenes(
    *,
    tier: CapabilityTier = CapabilityTier.PRESET,
    include_draft: bool = False,
) -> list[SceneManifest]:
    policy = AssetVisibility(tier=tier, include_draft=include_draft)
    return visible_assets(_all_scene_manifests(), policy)


def get_scene(name: str, *, tier: CapabilityTier = CapabilityTier.PRESET) -> SceneManifest:
    for manifest in all_scenes(tier=tier):
        if manifest.name == name:
            return manifest
    raise KeyError(name)


def search_scenes(
    query: str = "",
    *,
    intent_tags: Optional[Iterable[str]] = None,
    category: Optional[str] = None,
    tier: CapabilityTier = CapabilityTier.PRESET,
    limit: int = 30,
) -> CatalogSearchResult:
    """Rank stable scenes for an agent/UI without hardcoded scene lists."""
    tokens = {token.lower() for token in query.replace("_", " ").split() if token.strip()}
    requested_tags = {tag.lower() for tag in (intent_tags or [])}
    candidates: list[tuple[int, SceneManifest]] = []
    for item in all_scenes(tier=tier):
        if category and item.category != category:
            continue
        haystack = " ".join((item.name, item.category, item.summary, *item.intent_tags)).lower()
        score = sum(4 for token in tokens if token in item.name.lower())
        score += sum(2 for token in tokens if token in haystack)
        score += sum(5 for tag in requested_tags if tag in {item_tag.lower() for item_tag in item.intent_tags})
        if not tokens and not requested_tags:
            score = 1
        if score:
            candidates.append((score, item))
    candidates.sort(key=lambda pair: (-pair[0], pair[1].name.lower()))
    items = [item for _, item in candidates[: max(1, min(limit, 100))]]
    return CatalogSearchResult(query=query, total=len(candidates), items=items)
