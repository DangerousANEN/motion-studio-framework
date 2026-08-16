from __future__ import annotations

from msf.studio.catalog import search_scenes


def test_search_scenes_offset_pages_cover_full_catalog() -> None:
    """The catalog UI can page beyond the per-response maximum of 100 items."""
    first = search_scenes(limit=100, offset=0)
    second = search_scenes(limit=100, offset=len(first.items))

    names = [item.name for item in first.items + second.items]
    assert len(first.items) == min(100, first.total)
    assert len(names) == first.total
    assert len(set(names)) == first.total
    assert second.total == first.total
