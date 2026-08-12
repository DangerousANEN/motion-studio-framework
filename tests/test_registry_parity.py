"""The Python registry view must match what the renderer actually loads.

WHY THIS TEST EXISTS
--------------------
msf/registry.py parses TypeScript with regexes. That is a deliberate trade — it
keeps `import msf.graph.video_graph` from needing node — but a regex silently
returns FEWER results when formatting changes, and "fewer presets" is invisible:
the pipeline still runs, it just stops using half the library. That is precisely
the bug this whole change set exists to fix, so the parse is diffed against a real
node evaluation of the same files.

Failures found by exactly this comparison while writing it:

  1. `mergeRegistries()` appears in the doc comment of presets.ts with empty
     parens. A plain search matched the COMMENT, returned zero packs, and produced
     an EMPTY registry — every preset "missing", no error raised.
  2. effects.ts declares ENTRANCE_EFFECTS / EXIT_EFFECTS / EMPHASIS_EFFECTS as
     module-private `const`, not `export const`. Requiring `export` dropped 44 of
     96 effects.
  3. effects_scene.ts omits `family:` on every entry, so requiring that key
     dropped all 12 atmosphere overlays.

Every one of those parses "worked". Only the diff caught them.

If node is unavailable the test SKIPS rather than passes: a green run must mean
the comparison happened.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from msf import registry

REPO = Path(__file__).resolve().parents[1]
REMOTION = REPO / "remotion"

_DUMP_TS = """
import { PRESETS, PRESET_NAMES, ROTATION_SAFE, DATA_DRIVEN } from '../src/registry/presets';
import { EFFECTS } from '../src/registry/effects';
import { VISUAL_EFFECTS } from '../src/registry/effects_visual';
import { SCENE_EFFECTS, TRANSITIONS } from '../src/registry/effects_scene';

const meta: Record<string, any> = {};
for (const n of PRESET_NAMES) {
  const p = PRESETS[n];
  meta[n] = { category: p.category, dataDriven: !!p.dataDriven, fields: p.fields };
}
console.log(JSON.stringify({
  presets: PRESET_NAMES,
  rotation_safe: ROTATION_SAFE,
  data_driven: DATA_DRIVEN,
  meta,
  effects: [
    ...Object.keys(EFFECTS),
    ...Object.keys(VISUAL_EFFECTS),
    ...Object.keys(SCENE_EFFECTS),
  ].sort(),
  transitions: Object.keys(TRANSITIONS).sort(),
}));
"""


@pytest.fixture(scope="module")
def truth() -> dict:
    """Evaluate the TypeScript registries with node and return the real contents."""
    # On Windows the executables are npx.cmd / node.exe. subprocess with
    # shell=False cannot run a bare "npx" — it raises WinError 2 — so resolve the
    # real path first. shutil.which() handles PATHEXT, so this works on both
    # platforms and keeps shell=False (no quoting hazards).
    npx = shutil.which("npx")
    node = shutil.which("node")
    if not npx or not node:
        pytest.skip("npx/node unavailable — cannot verify the parse against the renderer")
    if not (REMOTION / "node_modules").is_dir():
        pytest.skip("remotion/node_modules missing — run npm install first")

    scripts = REMOTION / "scripts"
    scripts.mkdir(exist_ok=True)
    ts = scripts / ".registry_parity_dump.ts"
    bundle = REMOTION / ".registry_parity.cjs"
    ts.write_text(_DUMP_TS, encoding="utf-8")
    try:
        build = subprocess.run(
            [
                npx, "esbuild", str(ts.relative_to(REMOTION)),
                "--bundle", "--platform=node", "--format=cjs",
                f"--outfile={bundle.name}", "--external:react", "--log-level=error",
            ],
            cwd=REMOTION, capture_output=True, text=True, timeout=300,
        )
        if build.returncode != 0:
            pytest.skip(f"esbuild failed, cannot verify: {build.stderr[:300]}")
        run = subprocess.run(
            [node, bundle.name], cwd=REMOTION,
            capture_output=True, text=True, timeout=120,
        )
        if run.returncode != 0:
            pytest.skip(f"node failed, cannot verify: {run.stderr[:300]}")
        return json.loads(run.stdout)
    finally:
        ts.unlink(missing_ok=True)
        bundle.unlink(missing_ok=True)


# --------------------------------------------------------------------- presets

def test_preset_names_match_exactly(truth: dict) -> None:
    parsed = set(registry.preset_names())
    real = set(truth["presets"])
    assert parsed == real, (
        f"missing from the Python parse: {sorted(real - parsed)}; "
        f"invented by the Python parse: {sorted(parsed - real)}"
    )


def test_the_parse_is_not_empty(truth: dict) -> None:
    """An empty parse is the failure mode that hides: no exception, no presets."""
    assert len(registry.preset_names()) > 20, (
        "the registry parse collapsed — this is how the library silently shrank "
        "to five rotating presets"
    )


def test_data_driven_flags_match(truth: dict) -> None:
    assert registry.data_driven_presets() == frozenset(truth["data_driven"])


def test_rotation_safe_is_the_same_set(truth: dict) -> None:
    """Order differs deliberately (we interleave categories); the SET must match."""
    assert set(registry.rotation_safe_presets()) == set(truth["rotation_safe"])


def test_categories_match(truth: dict) -> None:
    for name, info in registry.load_registry().items():
        assert info.category == truth["meta"][name]["category"], name


def test_declared_fields_match(truth: dict) -> None:
    """`fields` is what an agent is told it may pass; a wrong list is a dead end."""
    for name, info in registry.load_registry().items():
        assert set(info.fields) == set(truth["meta"][name]["fields"]), name


# --------------------------------------------------------------------- effects

def test_effect_names_match_every_pack_the_renderer_resolves(truth: dict) -> None:
    """EffectStack resolves EFFECTS ∪ VISUAL_EFFECTS ∪ SCENE_EFFECTS."""
    parsed = set(registry.load_effects())
    real = set(truth["effects"])
    assert parsed == real, (
        f"missing: {sorted(real - parsed)}; invented: {sorted(parsed - real)}"
    )


def test_transitions_are_separate_from_effects(truth: dict) -> None:
    """A transition in an `effects` list is skipped with a console warning.

    So the catalogue must not offer them interchangeably.
    """
    assert registry.transition_names() == truth["transitions"]
    overlap = set(registry.transition_names()) & set(registry.load_effects())
    assert not overlap, f"transitions leaked into the effects catalogue: {sorted(overlap)}"


def test_every_effect_has_a_resolved_family() -> None:
    """'unknown' means the parser met a shape it did not understand."""
    unknown = [e.name for e in registry.load_effects().values() if e.family == "unknown"]
    assert not unknown, f"effects with an unresolved family: {unknown}"


# ------------------------------------------------- the graph uses the registry

def test_rotation_no_longer_uses_a_hardcoded_five() -> None:
    from msf.graph import video_graph

    assert len(video_graph._TEXT_SAFE_PRESETS) > 5, (
        "rotation is back to a short hardcoded list — every video will look the same"
    )
    assert len(video_graph._DATA_DRIVEN_PRESETS) == len(registry.data_driven_presets())


def test_rotation_never_substitutes_a_data_driven_preset() -> None:
    from msf.graph import video_graph

    for name in video_graph._TEXT_SAFE_PRESETS:
        assert name not in registry.data_driven_presets(), (
            f"{name} needs structured data; rotating it into a narration-only scene "
            "renders its placeholder"
        )


def test_rotation_excludes_presets_that_invent_their_own_content() -> None:
    """ScoreHud/SubscribeCTA/BankCard/CountdownHero render convincing FICTION.

    Verified by rendering each with only a title and text: they showed PLAYER 1,
    TechChannel / 142.0K подписчиков, ALEXEY NIKITIN / ···· 4242 and "СТАРТ"
    respectively — none of it from the script.
    """
    from msf.graph import video_graph

    for name in ("ScoreHud", "SubscribeCTA", "BankCard", "CountdownHero"):
        assert name not in video_graph._TEXT_SAFE_PRESETS, (
            f"{name} would put invented content on screen"
        )
