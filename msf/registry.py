"""The scene registry, read from TypeScript so Python cannot disagree with it.

WHY THIS FILE EXISTS
--------------------
The registry lives in `remotion/src/registry/*.ts` because that is where the
components are. Python needs the same facts — which presets exist, which need
structured data, what fields each reads — and every previous attempt to have
both sides know that ended the same way: a hand-written Python list that drifted.

The damage was not theoretical. Measured against the registry at the time of
writing:

  * `_TEXT_SAFE_PRESETS` in video_graph.py listed 5 names. The registry marks 13
    as rotation-safe. So 8 finished presets — ScoreHud, SubscribeCTA, MusicPlayer,
    VinylRecord, VoiceMemo, BankCard, CountdownHero, ModelOrbit3D — could never
    appear in a generated video. Every narration-only render cycled the same five
    typography cards, which is exactly the "агенты используют первые 5 сцен"
    complaint.
  * `_DATA_DRIVEN_PRESETS` listed 11 of the registry's 25. The 14 missing ones
    (Leaderboard, QuizCard, TimelineReveal, PostCard, CommentWall, ...) were
    therefore eligible for blind rotation, which hands a data preset a scene
    carrying only narration and renders its ⚠ placeholder.
  * BankCard was listed as data-driven in Python and NOT in the registry, so it
    was excluded from rotation for a reason that no longer existed.

None of those states can be reached from here: both lists now come from the same
file the renderer imports.

WHY A REGEX AND NOT A NODE SUBPROCESS
-------------------------------------
Executing the TS would be exact, but it puts a node+esbuild round trip (~20s
cold) inside `import msf.graph.video_graph`, and makes the graph unimportable on
a machine where node is missing. The registry entries are declarative and
uniformly formatted, so parsing is reliable — and `tests/test_registry_parity.py`
diffs this parse against a real node evaluation of the same files, so a formatting
change that breaks the regex fails a test instead of silently shrinking the
library back to five presets.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

_REGISTRY_DIR = Path(__file__).resolve().parents[1] / "remotion" / "src" / "registry"

# Categories that describe a *scene*. Anything else in the directory
# (effects_*.ts, transitions.ts) shares the entry shape but is not a scene, and
# letting one through means an agent can name `Bloom` as a preset and get an
# error card.
_INDEX = "presets.ts"


@dataclass(frozen=True)
class PresetInfo:
    """One scene preset, as declared in the TypeScript registry."""

    name: str
    category: str
    summary: str
    fields: tuple[str, ...]
    data_driven: bool
    three: bool
    pack: str

    @property
    def rotation_safe(self) -> bool:
        """Can rotation substitute this preset into a narration-only scene?

        Mirrors ROTATION_SAFE in registry/presets.ts: safe iff not data-driven.
        """
        return not self.data_driven


def _merged_packs(index_text: str) -> List[str]:
    """Pack module names that presets.ts actually merges.

    Read from the mergeRegistries() call rather than from the imports: a pack may
    be imported for a re-export (COMMON_FIELDS) without contributing presets, and
    counting it would add names the renderer cannot resolve.
    """
    # The doc comment at the top of presets.ts also mentions `mergeRegistries()`
    # — with empty parens. A plain search finds THAT first and returns no packs,
    # which silently yields an empty registry. Require at least one *_PRESETS
    # identifier inside the parens so only the real call matches.
    call = re.search(r"mergeRegistries\(\s*([^)]*?_PRESETS[^)]*?)\)", index_text, re.S)
    if not call:
        return []
    consts = re.findall(r"([A-Z][A-Z0-9_]*_PRESETS)", call.group(1))
    packs: List[str] = []
    for const in consts:
        # `import { CORE_PRESETS, COMMON_FIELDS } from './core';`
        m = re.search(
            rf"import\s*\{{[^}}]*\b{const}\b[^}}]*\}}\s*from\s*'\./([A-Za-z0-9_]+)'",
            index_text,
        )
        if m:
            packs.append(m.group(1))
    return packs


def _parse_entry(block: str) -> Dict[str, object]:
    """Pull the metadata fields out of one registry entry body."""
    out: Dict[str, object] = {}

    m = re.search(r"category:\s*'([^']+)'", block)
    out["category"] = m.group(1) if m else "unknown"

    m = re.search(r"summary:\s*(['\"])(.*?)\1", block, re.S)
    out["summary"] = re.sub(r"\s+", " ", m.group(2)).strip() if m else ""

    # fields may be an inline array, a spread of COMMON_FIELDS, or both.
    m = re.search(r"fields:\s*\[(.*?)\]", block, re.S)
    names: List[str] = []
    if m:
        body = m.group(1)
        names = re.findall(r"'([^']+)'", body)
        if "COMMON_FIELDS" in body:
            names.append("...COMMON_FIELDS")
    out["fields"] = tuple(names)

    out["data_driven"] = bool(re.search(r"dataDriven:\s*true", block))
    out["three"] = bool(re.search(r"\bthree:\s*true", block))
    return out


@lru_cache(maxsize=1)
def load_registry() -> Dict[str, PresetInfo]:
    """Parse every merged pack into {name: PresetInfo}.

    Returns an empty dict when the registry is unreadable. Callers must treat
    empty as "cannot verify" and fail loudly rather than falling back to a short
    hardcoded list — a silent fallback is how the library shrank to five presets
    in the first place.
    """
    index = _REGISTRY_DIR / _INDEX
    if not index.is_file():
        return {}
    try:
        index_text = index.read_text(encoding="utf-8")
    except OSError:
        return {}

    common: tuple[str, ...] = ()
    presets: Dict[str, PresetInfo] = {}

    # `  PresetName: {` at two-space indent, followed by a `component:` line.
    entry_re = re.compile(r"^\s{2}([A-Z][A-Za-z0-9_]*):\s*\{", re.M)

    for pack in _merged_packs(index_text):
        path = _REGISTRY_DIR / f"{pack}.ts"
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        if not common:
            m = re.search(r"COMMON_FIELDS\s*=\s*\[(.*?)\]", text, re.S)
            if m:
                common = tuple(re.findall(r"'([^']+)'", m.group(1)))

        for match in entry_re.finditer(text):
            # Entry body: from the opening brace to the closing one at the same
            # indent. Registry entries are two-space indented objects, so the
            # terminator is a `  }` line.
            rest = text[match.end():]
            end = re.search(r"^\s{2}\},?\s*$", rest, re.M)
            block = rest[: end.start()] if end else rest[:800]
            if "component:" not in block:
                continue
            meta = _parse_entry(block)
            fields = tuple(meta["fields"])  # type: ignore[arg-type]
            if "...COMMON_FIELDS" in fields:
                fields = tuple(f for f in fields if f != "...COMMON_FIELDS") + common
            presets[match.group(1)] = PresetInfo(
                name=match.group(1),
                category=str(meta["category"]),
                summary=str(meta["summary"]),
                fields=fields,
                data_driven=bool(meta["data_driven"]),
                three=bool(meta["three"]),
                pack=pack,
            )

    return presets


def preset_names() -> List[str]:
    return sorted(load_registry())


def rotation_safe_presets() -> List[str]:
    """Presets that render correctly from narration text alone.

    Ordered for VISUAL VARIETY, not alphabetically. Rotation walks this list in
    order, so alphabetical order would put GridGridFloor and HeroKinetic
    back-to-back — two big title cards in a row, the very sameness this is meant
    to break. Interleaving categories guarantees consecutive scenes differ in
    silhouette even when the list grows.
    """
    infos = [p for p in load_registry().values() if p.rotation_safe]

    buckets: Dict[str, List[str]] = {}
    for p in sorted(infos, key=lambda x: x.name):
        buckets.setdefault(p.category, []).append(p.name)

    # Deal one from each category in turn (round-robin), so neighbours differ.
    order = sorted(buckets, key=lambda c: (-len(buckets[c]), c))
    out: List[str] = []
    while any(buckets[c] for c in order):
        for c in order:
            if buckets[c]:
                out.append(buckets[c].pop(0))
    return out


def data_driven_presets() -> frozenset[str]:
    return frozenset(p.name for p in load_registry().values() if p.data_driven)


def by_category() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for p in sorted(load_registry().values(), key=lambda x: x.name):
        out.setdefault(p.category, []).append(p.name)
    return out


def get(name: str) -> Optional[PresetInfo]:
    return load_registry().get(name)


# ---------------------------------------------------------------- effects

@dataclass(frozen=True)
class EffectInfo:
    """One effect from the effects registries.

    `family` is normalised across packs. effects.ts and effects_visual.ts declare
    it per entry; effects_scene.ts does not declare it at all, so it is derived
    from which exported const the entry sits in.
    """

    name: str
    family: str
    summary: str
    stochastic: bool
    pack: str


# All effect packs the renderer resolves against, and the family to assume for
# entries in a given exported const when the entry itself does not say.
#
# EffectStack.tsx looks a name up in EFFECTS, then VISUAL_EFFECTS, then
# SCENE_EFFECTS — all three are equally valid in a spec, so all three must be
# read. Reading only effects.ts reported 44 when the renderer accepts 96.
#
# TRANSITIONS is deliberately EXCLUDED from effects: it lives in the same file but
# its components take SceneTransitionProps, not EffectProps, and EffectStack does
# not look there. Offering a transition where an effect is expected would produce
# a console warning and a silently skipped wrapper. They are exposed separately by
# transition_names().
#
# The packs have separate owners and no shared merge call, so the list is explicit
# rather than parsed; test_registry_parity checks the totals against node.
_EFFECT_SECTIONS = {
    "effects": {"ENTRANCE_EFFECTS": None, "EXIT_EFFECTS": None, "EMPHASIS_EFFECTS": None},
    "effects_visual": {"VISUAL_EFFECTS": None},
    # effects_scene.ts omits `family:` on every entry — without a default here the
    # 12 atmosphere overlays are dropped from the catalogue while the renderer
    # still applies them.
    "effects_scene": {"SCENE_EFFECTS": "atmosphere"},
}


def _sections(text: str) -> List[tuple[str, str]]:
    """Split a pack into (const_name, body) pairs.

    Needed because one file can hold several registries and an entry's family may
    depend on which one it is in.

    `export` is OPTIONAL in the pattern: effects.ts declares ENTRANCE_EFFECTS,
    EXIT_EFFECTS and EMPHASIS_EFFECTS as plain module-private `const` and only
    exports the merged result. Requiring `export` matched none of them and quietly
    dropped all 44 entrance/exit/emphasis effects from the catalogue — the parse
    still "succeeded", reporting 52 effects instead of 96.
    """
    marks = [
        (m.group(1), m.end())
        for m in re.finditer(
            r"^(?:export\s+)?const ([A-Z][A-Z0-9_]*)\s*:[^=]*=\s*\{", text, re.M
        )
    ]
    out: List[tuple[str, str]] = []
    for i, (name, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        out.append((name, text[start:end]))
    return out


@lru_cache(maxsize=1)
def load_effects() -> Dict[str, EffectInfo]:
    """Parse every effect pack the renderer can resolve.

    Effects live in a SEPARATE registry from presets and must not be mixed with
    them: an effect wraps children, a preset IS the scene. Naming an effect as a
    preset renders an error card, which is why the preset parser above reads only
    the packs presets.ts merges.
    """
    effects: Dict[str, EffectInfo] = {}
    entry_re = re.compile(r"^\s{2}([A-Z][A-Za-z0-9_]*):\s*\{", re.M)

    for pack, sections in _EFFECT_SECTIONS.items():
        path = _REGISTRY_DIR / f"{pack}.ts"
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        for const_name, body in _sections(text):
            if const_name not in sections:
                continue
            default_family = sections[const_name]
            for match in entry_re.finditer(body):
                rest = body[match.end():]
                end = re.search(r"^\s{2}\},?\s*$", rest, re.M)
                block = rest[: end.start()] if end else rest[:600]
                if "component:" not in block:
                    continue
                fam = re.search(r"family:\s*'([^']+)'", block)
                family = fam.group(1) if fam else default_family
                if family is None:
                    # An entry with no family and no default is a registry shape
                    # this parser does not understand; skipping it silently is how
                    # catalogues go stale, so surface it as 'unknown'.
                    family = "unknown"
                summ = re.search(r"summary:\s*(['\"])(.*?)\1", block, re.S)
                effects[match.group(1)] = EffectInfo(
                    name=match.group(1),
                    family=family,
                    summary=re.sub(r"\s+", " ", summ.group(2)).strip() if summ else "",
                    stochastic=bool(re.search(r"stochastic:\s*true", block)),
                    pack=pack,
                )
    return effects


@lru_cache(maxsize=1)
def transition_names() -> List[str]:
    """Scene-to-scene transitions. NOT usable in a scene's `effects` list."""
    path = _REGISTRY_DIR / "effects_scene.ts"
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    for const_name, body in _sections(text):
        if const_name != "TRANSITIONS":
            continue
        return sorted(
            m.group(1) for m in re.finditer(r"^\s{2}([A-Z][A-Za-z0-9_]*):\s*\{", body, re.M)
        )
    return []


def effects_by_family() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for e in sorted(load_effects().values(), key=lambda x: x.name):
        out.setdefault(e.family, []).append(e.name)
    return out


__all__ = [
    "PresetInfo",
    "EffectInfo",
    "load_registry",
    "load_effects",
    "preset_names",
    "rotation_safe_presets",
    "data_driven_presets",
    "by_category",
    "effects_by_family",
    "transition_names",
    "get",
]
