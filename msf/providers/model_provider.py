"""3D model sourcing with an on-disk cache.

WHY THIS EXISTS
---------------
Scenes that show a real object (ModelOrbit3D, ExplodedView3D, CardScatter3D)
need a .glb file. Fetching it from the network at render time is wrong twice
over: a render is not reproducible if an upstream repo moves a file, and
Remotion renders each frame in a separate browser worker, so an uncached URL
would be re-fetched many times for one video.

So: resolve a short id like ``khronos:DamagedHelmet`` to a URL, download once
into ``assets/models/<provider>/<id>.glb``, and hand callers a local path.
Subsequent renders never touch the network.

PROVIDERS
---------
Verified by request (see docs/MASTER_PLAN_v5_APPENDIX_A.md A.5):

  khronos:<Name>   glTF-Sample-Assets, no key         -> works
  quaternius:<f>   CC0 packs, no key                  -> works
  kenney:<f>       CC0 low-poly props, no key         -> works
  url:<https://…>  direct link to any .glb            -> works
  sketchfab:<uid>  requires an OAuth token            -> 401 without one

Sketchfab's search endpoint answers 200 but /download returns 401, so it is
only usable when SKETCHFAB_TOKEN is set. It is registered here so the failure
is a clear message rather than a confusing 401 body.

LICENSING
---------
Deliberately not filtered — the client's instruction was "anything freely
downloadable". The sources above are CC0/CC-BY in practice.
"""
from __future__ import annotations

import os
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__all__ = [
    "ModelRef",
    "ModelResolutionError",
    "resolve_model",
    "model_cache_dir",
    "clear_model_cache",
]

# Repo root is three levels up from msf/providers/model_provider.py
_ROOT = Path(__file__).resolve().parents[2]
_CACHE_ROOT = _ROOT / "assets" / "models"

# A GLB starts with the ASCII magic "glTF". Anything else (an HTML error page,
# an LFS pointer, a truncated download) is rejected rather than cached, because
# a bad file cached once poisons every later render.
_GLB_MAGIC = b"glTF"
_MIN_PLAUSIBLE_BYTES = 1024

_KHRONOS_BASE = (
    "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models"
)
# Older mirror; still serves 104 models under 2.0/ and is used as a fallback
# when a name only exists in the legacy repo.
_KHRONOS_LEGACY = (
    "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0"
)
_QUATERNIUS_BASE = "https://quaternius.com/models"
_KENNEY_BASE = "https://kenney.nl/media/pages/assets"


class ModelResolutionError(RuntimeError):
    """Raised when a model id cannot be turned into a usable local .glb."""


@dataclass(frozen=True)
class ModelRef:
    """A resolved model: where it came from and where it now lives on disk."""

    provider: str
    model_id: str
    path: Path
    source_url: str
    bytes: int
    from_cache: bool

    @property
    def staticfile_path(self) -> str:
        """Path relative to the Remotion public/ dir, for staticFile()."""
        return f"models/{self.provider}/{self.model_id}.glb"


def model_cache_dir() -> Path:
    return _CACHE_ROOT


def _candidate_urls(provider: str, model_id: str) -> list[str]:
    if provider == "khronos":
        return [
            f"{_KHRONOS_BASE}/{model_id}/glTF-Binary/{model_id}.glb",
            f"{_KHRONOS_LEGACY}/{model_id}/glTF-Binary/{model_id}.glb",
        ]
    if provider == "quaternius":
        return [f"{_QUATERNIUS_BASE}/{model_id}.glb"]
    if provider == "kenney":
        return [f"{_KENNEY_BASE}/{model_id}.glb"]
    if provider == "url":
        return [model_id]
    if provider == "sketchfab":
        token = os.environ.get("SKETCHFAB_TOKEN")
        if not token:
            raise ModelResolutionError(
                "sketchfab: requires SKETCHFAB_TOKEN — the /download endpoint "
                "answers 401 without OAuth. Use khronos:, quaternius:, kenney: "
                "or a direct url: instead."
            )
        return [f"https://api.sketchfab.com/v3/models/{model_id}/download"]
    raise ModelResolutionError(
        f"unknown model provider {provider!r}. "
        "Expected one of: khronos, quaternius, kenney, url, sketchfab."
    )


def _parse(ref: str) -> tuple[str, str]:
    """Split ``provider:id``. A bare https:// URL is treated as ``url:``."""
    if ref.startswith("http://") or ref.startswith("https://"):
        return "url", ref
    if ":" not in ref:
        raise ModelResolutionError(
            f"model ref {ref!r} has no provider prefix. "
            "Use e.g. 'khronos:DamagedHelmet' or a direct https:// URL."
        )
    provider, _, model_id = ref.partition(":")
    return provider.strip().lower(), model_id.strip()


def _cache_key(provider: str, model_id: str) -> str:
    """Filesystem-safe name. A URL id is hashed; others keep their readable id."""
    if provider == "url":
        import hashlib

        return hashlib.sha1(model_id.encode("utf-8")).hexdigest()[:16]
    return model_id.replace("/", "_")


def _validate_glb(path: Path) -> None:
    size = path.stat().st_size
    if size < _MIN_PLAUSIBLE_BYTES:
        raise ModelResolutionError(
            f"downloaded file is {size} bytes — too small to be a model. "
            "The URL probably returned an error page."
        )
    with path.open("rb") as fh:
        magic = fh.read(4)
    if magic != _GLB_MAGIC:
        raise ModelResolutionError(
            f"downloaded file is not a binary glTF (magic={magic!r}, expected "
            f"{_GLB_MAGIC!r}). Only .glb is supported; a .gltf with external "
            "textures would need its whole directory fetched."
        )


def resolve_model(
    ref: str,
    *,
    force: bool = False,
    timeout: int = 120,
    public_dir: Optional[Path] = None,
) -> ModelRef:
    """Resolve ``provider:id`` to a cached local .glb, downloading if needed.

    Args:
        ref: e.g. ``khronos:DamagedHelmet``, or a direct https URL.
        force: re-download even when a cached copy exists.
        timeout: per-request timeout in seconds.
        public_dir: when given, the model is also copied into
            ``<public_dir>/models/<provider>/<id>.glb`` so Remotion's
            staticFile() can reach it.

    Raises:
        ModelResolutionError: unknown provider, network failure, or a payload
            that is not a valid GLB.
    """
    provider, model_id = _parse(ref)
    key = _cache_key(provider, model_id)
    cache_path = _CACHE_ROOT / provider / f"{key}.glb"

    if cache_path.exists() and not force:
        _validate_glb(cache_path)
        resolved = ModelRef(
            provider=provider,
            model_id=key,
            path=cache_path,
            source_url="(cache)",
            bytes=cache_path.stat().st_size,
            from_cache=True,
        )
        if public_dir is not None:
            _publish(resolved, public_dir)
        return resolved

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    for url in _candidate_urls(provider, model_id):
        # Download to a temp name first: a partial file left at the cache path
        # would be treated as a valid cache hit on the next run.
        tmp_path = cache_path.with_suffix(".glb.part")
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "motion-studio-framework/1.0"}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                with tmp_path.open("wb") as fh:
                    shutil.copyfileobj(response, fh)
            _validate_glb(tmp_path)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            tmp_path.unlink(missing_ok=True)
            errors.append(f"{url} -> {type(exc).__name__}: {exc}")
            continue
        except ModelResolutionError as exc:
            tmp_path.unlink(missing_ok=True)
            errors.append(f"{url} -> {exc}")
            continue

        tmp_path.replace(cache_path)
        resolved = ModelRef(
            provider=provider,
            model_id=key,
            path=cache_path,
            source_url=url,
            bytes=cache_path.stat().st_size,
            from_cache=False,
        )
        if public_dir is not None:
            _publish(resolved, public_dir)
        return resolved

    raise ModelResolutionError(
        f"could not fetch {ref!r}. Tried:\n  " + "\n  ".join(errors)
    )


def _publish(model: ModelRef, public_dir: Path) -> Path:
    """Copy a cached model into Remotion's public/ tree for staticFile()."""
    target = public_dir / "models" / model.provider / f"{model.model_id}.glb"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.stat().st_size != model.bytes:
        shutil.copyfile(model.path, target)
    return target


def clear_model_cache(provider: Optional[str] = None) -> int:
    """Delete cached models. Returns the number of files removed."""
    root = _CACHE_ROOT / provider if provider else _CACHE_ROOT
    if not root.exists():
        return 0
    removed = 0
    for path in root.rglob("*.glb"):
        path.unlink()
        removed += 1
    return removed
