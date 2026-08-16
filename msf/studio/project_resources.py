"""Local project resource inventory for MSF Studio.

Uploaded media is not a renderer input by itself. It becomes a typed, attributable
ProjectMedia record which can later be deliberately bound to a compatible scene.
The store lives under output/studio/projects/, preserving the repository source tree
and keeping user files local to the operator machine.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

from msf.studio.contracts import PinnedResearchSource, ProjectMedia


_REPO = Path(__file__).resolve().parents[2]
_PROJECTS_ROOT = _REPO / "output" / "studio" / "projects"
_PROJECT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
_ASSET_ID_RE = re.compile(r"media_[0-9a-f]{32}$")
_SOURCE_ID_RE = re.compile(r"pinned_[0-9a-f]{32}$")
_RUN_ID_RE = re.compile(r"run_[0-9a-f]{32}$")

_MEDIA_KINDS = {
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".webp": "image", ".gif": "image",
    ".mp4": "video", ".mov": "video", ".webm": "video", ".m4v": "video",
    ".wav": "audio", ".mp3": "audio", ".m4a": "audio", ".aac": "audio", ".ogg": "audio", ".flac": "audio",
    ".pdf": "document",
}
MEDIA_ROLES = frozenset({
    "hero_image", "screen_recording", "video_insert", "telegram_round",
    "channel_avatar", "supporting_image", "reference_audio",
})
_MAX_UPLOAD_BYTES = 250 * 1024 * 1024
_LOCK = threading.RLock()


class ProjectResourceError(ValueError):
    """Raised for a user-actionable resource contract violation."""


def _safe_project_id(project_id: str) -> str:
    if not _PROJECT_ID_RE.fullmatch(project_id):
        raise ProjectResourceError("project_id must use letters, numbers, _ or - (max 80 chars)")
    return project_id


def _project_dir(project_id: str) -> Path:
    return _PROJECTS_ROOT / _safe_project_id(project_id)


def _index_path(project_id: str) -> Path:
    return _project_dir(project_id) / "resources.json"


def _read_index(project_id: str) -> dict[str, Any]:
    path = _index_path(project_id)
    if not path.is_file():
        return {"version": 1, "project_id": project_id, "media": [], "pinned_sources": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProjectResourceError("project resource index is unreadable") from exc
    if not isinstance(raw, dict) or raw.get("project_id") != project_id or not isinstance(raw.get("media"), list):
        raise ProjectResourceError("project resource index has an invalid shape")
    raw.setdefault("pinned_sources", [])
    if not isinstance(raw["pinned_sources"], list):
        raise ProjectResourceError("project pinned source index has an invalid shape")
    return raw


def _write_index(project_id: str, data: dict[str, Any]) -> None:
    path = _index_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def media_kind(filename: str) -> str:
    kind = _MEDIA_KINDS.get(Path(filename).suffix.lower())
    if not kind:
        raise ProjectResourceError(f"unsupported media format: {Path(filename).suffix.lower() or '(none)'}")
    return kind


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metadata(path: Path, kind: str) -> dict[str, Any]:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {"mime_type": mime, "size_bytes": path.stat().st_size, "kind": kind}


def _to_public(project_id: str, raw: dict[str, Any]) -> ProjectMedia:
    # Relative storage key is intentionally not exposed as an arbitrary path. The
    # stable local API URI is the only endpoint the UI and renderer should use.
    public = {key: value for key, value in raw.items() if key != "storage_key"}
    public["relative_uri"] = f"/api/studio/projects/{project_id}/media/{raw['asset_id']}"
    return ProjectMedia.model_validate(public)


def list_media(project_id: str) -> list[ProjectMedia]:
    project_id = _safe_project_id(project_id)
    with _LOCK:
        index = _read_index(project_id)
        return [_to_public(project_id, item) for item in index["media"]]


def register_staged_media(
    project_id: str,
    staged_file: Path,
    original_name: str,
    role: str,
    caption: str = "",
) -> ProjectMedia:
    """Move one server-staged upload into a project inventory atomically."""
    project_id = _safe_project_id(project_id)
    if role not in MEDIA_ROLES:
        raise ProjectResourceError(f"unknown media role: {role}")
    clean_name = Path(original_name).name or "media.bin"
    kind = media_kind(clean_name)
    if not staged_file.is_file():
        raise ProjectResourceError("staged upload is missing")
    if staged_file.stat().st_size <= 0:
        raise ProjectResourceError("media file is empty")
    if staged_file.stat().st_size > _MAX_UPLOAD_BYTES:
        raise ProjectResourceError("media file exceeds 250 MB limit")

    asset = ProjectMedia(
        project_id=project_id,
        kind=kind,
        role=role,
        display_name=clean_name,
        caption=caption.strip()[:320],
    )
    suffix = Path(clean_name).suffix.lower()
    project_dir = _project_dir(project_id)
    media_dir = project_dir / "media"
    destination = media_dir / f"{asset.asset_id}{suffix}"
    with _LOCK:
        media_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged_file), str(destination))
        metadata = _metadata(destination, kind)
        record = asset.model_dump(mode="json")
        record.update({
            "storage_key": str(destination.relative_to(project_dir)).replace("\\", "/"),
            "sha256": _sha256(destination),
            **metadata,
        })
        index = _read_index(project_id)
        index["media"].append(record)
        _write_index(project_id, index)
    return _to_public(project_id, record)


def find_media(project_id: str, asset_id: str) -> tuple[ProjectMedia, Path]:
    project_id = _safe_project_id(project_id)
    if not _ASSET_ID_RE.fullmatch(asset_id):
        raise ProjectResourceError("unknown media asset")
    with _LOCK:
        index = _read_index(project_id)
        raw = next((item for item in index["media"] if item.get("asset_id") == asset_id), None)
        if raw is None:
            raise ProjectResourceError("unknown media asset")
        candidate = (_project_dir(project_id) / str(raw.get("storage_key", ""))).resolve()
        root = (_project_dir(project_id) / "media").resolve()
        if root not in candidate.parents or not candidate.is_file():
            raise ProjectResourceError("media asset file is unavailable")
        return _to_public(project_id, raw), candidate


def materialize_media_for_render(project_id: str, assets: Iterable[ProjectMedia], run_id: str) -> list[dict[str, str | int | None]]:
    """Copy registered project assets into the run-isolated Remotion public tree.

    The graph receives relative ``src`` paths only. It never receives the project
    storage path and therefore cannot ask the renderer to read arbitrary local files.
    """
    project_id = _safe_project_id(project_id)
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ProjectResourceError("invalid run id for media materialization")
    public_root = _REPO / "remotion" / "public" / "studio-resources" / run_id
    public_root.mkdir(parents=True, exist_ok=True)
    materialized: list[dict[str, str | int | None]] = []
    with _LOCK:
        for snapshot in assets:
            current, source_path = find_media(project_id, snapshot.asset_id)
            suffix = source_path.suffix.lower()
            target_name = f"{current.asset_id}{suffix}"
            target = public_root / target_name
            if not target.is_file():
                shutil.copy2(source_path, target)
            materialized.append({
                "asset_id": current.asset_id,
                "role": current.role,
                "kind": current.kind,
                "caption": current.caption,
                "src": f"studio-resources/{run_id}/{target_name}",
            })
    return materialized


def _safe_source_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ProjectResourceError("source URL must be a public http(s) URL without credentials")
    return parsed._replace(fragment="").geturl()


def list_pinned_sources(project_id: str) -> list[PinnedResearchSource]:
    project_id = _safe_project_id(project_id)
    with _LOCK:
        return [PinnedResearchSource.model_validate(item) for item in _read_index(project_id)["pinned_sources"]]


def add_pinned_source(project_id: str, url: str, mode: str, reason: str) -> PinnedResearchSource:
    project_id = _safe_project_id(project_id)
    safe_url = _safe_source_url(url)
    try:
        source = PinnedResearchSource(url=safe_url, mode=mode, reason=reason.strip())
    except ValueError as exc:
        raise ProjectResourceError(str(exc)) from exc
    with _LOCK:
        index = _read_index(project_id)
        if any(str(item.get("url")) == safe_url for item in index["pinned_sources"]):
            raise ProjectResourceError("this source URL is already pinned for the project")
        index["pinned_sources"].append(source.model_dump(mode="json"))
        _write_index(project_id, index)
    return source


def remove_pinned_source(project_id: str, source_id: str) -> None:
    project_id = _safe_project_id(project_id)
    if not _SOURCE_ID_RE.fullmatch(source_id):
        raise ProjectResourceError("unknown pinned source")
    with _LOCK:
        index = _read_index(project_id)
        if not any(item.get("source_id") == source_id for item in index["pinned_sources"]):
            raise ProjectResourceError("unknown pinned source")
        index["pinned_sources"] = [item for item in index["pinned_sources"] if item.get("source_id") != source_id]
        _write_index(project_id, index)


def remove_media(project_id: str, asset_id: str) -> None:
    project_id = _safe_project_id(project_id)
    with _LOCK:
        media, path = find_media(project_id, asset_id)
        index = _read_index(project_id)
        index["media"] = [item for item in index["media"] if item.get("asset_id") != media.asset_id]
        _write_index(project_id, index)
        path.unlink(missing_ok=True)


def write_upload_chunks(destination: Path, chunks: Iterable[bytes], max_bytes: int = _MAX_UPLOAD_BYTES) -> int:
    """Write streamed upload chunks with a hard limit, used by the local API only."""
    total = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("wb") as handle:
            for chunk in chunks:
                total += len(chunk)
                if total > max_bytes:
                    raise ProjectResourceError(f"media file exceeds {max_bytes // (1024 * 1024)} MB limit")
                handle.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    if total == 0:
        destination.unlink(missing_ok=True)
        raise ProjectResourceError("media file is empty")
    return total


__all__ = [
    "MEDIA_ROLES", "ProjectResourceError", "list_media", "register_staged_media",
    "find_media", "remove_media", "media_kind", "write_upload_chunks", "materialize_media_for_render",
    "list_pinned_sources", "add_pinned_source", "remove_pinned_source",
]
