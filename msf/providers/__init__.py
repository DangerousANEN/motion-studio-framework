"""External asset providers behind one interface each.

Currently: 3D models (model_provider). Research/text providers live in
msf/agents/ for historical reasons.
"""
from msf.providers.model_provider import (
    ModelRef,
    ModelResolutionError,
    clear_model_cache,
    model_cache_dir,
    resolve_model,
)

__all__ = [
    "ModelRef",
    "ModelResolutionError",
    "clear_model_cache",
    "model_cache_dir",
    "resolve_model",
]
