"""Asset lifecycle helpers shared by catalog, skills and release workflows."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, TypeVar

from .contracts import AssetStatus, CapabilityTier


class LifecycleAsset(Protocol):
    status: AssetStatus
    capability_tier: CapabilityTier


@dataclass(frozen=True)
class AssetVisibility:
    """Policy describing which catalog entries a caller may discover."""

    tier: CapabilityTier = CapabilityTier.PRESET
    include_draft: bool = False


TAsset = TypeVar("TAsset", bound=LifecycleAsset)


def visible_assets(assets: Iterable[TAsset], policy: AssetVisibility) -> list[TAsset]:
    """Filter assets by release state and capability without relying on names.

    Preset/curated callers see stable entries only.  Sandbox callers may opt in to
    draft assets; release callers may also inspect deprecated entries for migration
    and rollback work.
    """
    output: list[TAsset] = []
    for asset in assets:
        if asset.status == AssetStatus.DEPRECATED and policy.tier != CapabilityTier.RELEASE:
            continue
        if asset.status == AssetStatus.DRAFT and not (
            policy.include_draft and policy.tier in {CapabilityTier.SANDBOX, CapabilityTier.RELEASE}
        ):
            continue
        output.append(asset)
    return output


def can_publish(asset: LifecycleAsset, actor_tier: CapabilityTier, quality_gate_passed: bool) -> bool:
    """Return whether a draft can transition to stable in the current release flow."""
    return (
        asset.status == AssetStatus.DRAFT
        and actor_tier == CapabilityTier.RELEASE
        and quality_gate_passed
    )
