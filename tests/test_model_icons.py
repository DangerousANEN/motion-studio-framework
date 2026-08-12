"""Model brand icons: mapping correctness and the asset contract.

WHY THIS TEST EXISTS
--------------------
A missing or unmatched icon does not throw. `resolveModelIcon` returns null and
the preset draws a gradient letter avatar instead — which looks like a
deliberate design choice, not a broken asset list. Before the brand icons
landed, Leaderboard rendered five identical purple "U" circles for five
different models and passed a glance.

Three separate things can break silently, so all three are asserted:
  1. the label -> slug mapping (pattern matching over real pipeline strings),
  2. the file for every referenced slug actually existing in public/,
  3. the SVGs being usable inside an <img> at all.

On (3): roughly half the vendor icons ship `fill="currentColor"`. Inside an
<img> there is no inherited colour for currentColor to resolve against, so the
browser paints BLACK — an invisible logo on this library's dark backdrop, with
no error anywhere. scripts/sync-model-icons.mjs rewrites it to white; these
tests prove the rewrite ran and keep a future re-sync honest.

stdlib unittest + esbuild, matching tests/test_transition_parity.py — the
project has no vitest.
Run: python tests/test_model_icons.py
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTION = ROOT / "remotion"
ICON_DIR = REMOTION / "public" / "model-icons"
MAPPING_TS = REMOTION / "src" / "lib" / "modelIcons.ts"

# Real strings the pipeline produces, NOT canonical vendor slugs. That gap is the
# whole reason the resolver is pattern matching instead of a lookup table.
EXPECTED = [
    ("Qwen3.6-235B-A22B", "qwen-color"),
    ("DeepSeek-R2-Lite", "deepseek-color"),
    ("Llama-4-Scout-109B", "meta-color"),
    ("GLM-5.2-Air", "zhipu-color"),
    ("Claude-Opus-4.6", "claude-color"),
    ("GPT-5.2-turbo", "openai"),
    ("Gemini-3.6-Flash", "gemini-color"),
    ("Mistral-Large-3", "mistral-color"),
    ("Kimi-K3", "kimi-color"),
    ("Grok-4", "grok"),
    ("Nemotron-5-340B", "nvidia-color"),
    ("Phi-5-mini", "microsoft-color"),
    ("Command-R-Plus", "cohere-color"),
    ("DBRX-Instruct", "dbrx-color"),
    ("Hunyuan-Large", "hunyuan-color"),
    ("ERNIE-5.0", "wenxin-color"),
    ("Doubao-Pro", "doubao-color"),
    ("Baichuan-3", "baichuan-color"),
    ("InternLM3-8B", "internlm-color"),
    # Case and separators must not matter.
    ("claude opus 4.6", "claude-color"),
    ("QWEN3-MAX", "qwen-color"),
    # Must survive version bumps: a lookup table would miss the next release and
    # silently degrade to a letter avatar.
    ("Qwen7-Ultra-2030", "qwen-color"),
    ("DeepSeek-R9", "deepseek-color"),
    # Ordering: specific brand must win when several patterns could match.
    ("Llama-4-Scout", "meta-color"),
    ("Claude-Sonnet", "claude-color"),
]

# Null is the CONTRACT, not a failure: the caller draws a letter avatar. Handing
# back a generic "AI" glyph would make an unknown model look identified.
EXPECTED_NULL = ["Aria Chen", "Marcus Webb", "", None]


class TestIconMapping(unittest.TestCase):
    """Runs the real TypeScript resolver through esbuild + node."""

    @classmethod
    def setUpClass(cls):
        cls.results = cls._run_resolver()

    @staticmethod
    def _run_resolver():
        esbuild = REMOTION / "node_modules" / ".bin" / "esbuild.cmd"
        if not esbuild.exists():
            esbuild = REMOTION / "node_modules" / ".bin" / "esbuild"
        labels = [lbl for lbl, _ in EXPECTED] + [
            x for x in EXPECTED_NULL if x is not None
        ]
        entry = REMOTION / ".model_icons_probe.entry.ts"
        # `remotion` is stubbed: staticFile() needs a bundler/browser context and
        # this probe only cares about which slug the rules pick.
        entry.write_text(
            "import { resolveModelIcon, REFERENCED_SLUGS } from './src/lib/modelIcons';\n"
            f"const labels = {json.dumps(labels, ensure_ascii=False)};\n"
            "const out = labels.map((l) => {\n"
            "  const r = resolveModelIcon(l);\n"
            "  return { label: l, slug: r ? r.slug : null, src: r ? r.src : null };\n"
            "});\n"
            "console.log(JSON.stringify({ out, slugs: REFERENCED_SLUGS,\n"
            "  undef: resolveModelIcon(undefined) }));\n",
            encoding="utf-8",
        )
        bundle = REMOTION / ".model_icons_probe.js"
        try:
            subprocess.run(
                [
                    str(esbuild), str(entry), "--bundle", "--platform=node",
                    "--format=cjs", f"--outfile={bundle}", "--log-level=error",
                    # staticFile() is the only thing needed from remotion here.
                    "--define:process.env.NODE_ENV=\"test\"",
                    "--alias:remotion=./tests/fixtures/remotion_stub.ts",
                ],
                cwd=str(REMOTION), check=True, capture_output=True, timeout=180,
            )
            proc = subprocess.run(
                ["node", str(bundle)], cwd=str(REMOTION), check=True,
                capture_output=True, text=True, timeout=120,
            )
            return json.loads(proc.stdout.strip())
        finally:
            entry.unlink(missing_ok=True)
            bundle.unlink(missing_ok=True)

    def test_labels_resolve_to_expected_brands(self):
        by_label = {r["label"]: r["slug"] for r in self.results["out"]}
        for label, slug in EXPECTED:
            with self.subTest(label=label):
                self.assertEqual(
                    by_label.get(label), slug,
                    f"{label!r} resolved to {by_label.get(label)!r}, expected "
                    f"{slug!r}. A wrong slug puts a competitor's logo on screen.",
                )

    def test_non_models_resolve_to_null(self):
        by_label = {r["label"]: r["slug"] for r in self.results["out"]}
        for label in EXPECTED_NULL:
            if label is None:
                self.assertIsNone(self.results["undef"])
                continue
            with self.subTest(label=label):
                self.assertIsNone(
                    by_label.get(label),
                    f"{label!r} is not a model but matched "
                    f"{by_label.get(label)!r}; the letter avatar is correct here.",
                )

    def test_src_points_into_public_model_icons(self):
        for r in self.results["out"]:
            if r["slug"]:
                self.assertIn("model-icons/", r["src"])


class TestIconAssets(unittest.TestCase):
    """The files themselves, independent of the mapping."""

    def test_every_referenced_slug_has_a_file(self):
        # Remotion resolves staticFile() against public/ only. A slug with no
        # file 404s in a render while looking fine in the dev bundler — green
        # locally, blank logos in the delivered MP4.
        slugs = TestIconMapping._run_resolver()["slugs"]
        missing = [s for s in slugs if not (ICON_DIR / f"{s}.svg").exists()]
        self.assertEqual(
            missing, [],
            f"missing icon files: {missing}. Run "
            "`node scripts/sync-model-icons.mjs` in remotion/.",
        )

    def test_no_icon_paints_with_currentcolor(self):
        offenders = [
            p.name for p in ICON_DIR.glob("*.svg")
            if "currentColor" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            offenders, [],
            f"{offenders} still use currentColor, which resolves to BLACK inside "
            "an <img> — an invisible logo on a dark backdrop.",
        )

    def test_icons_declare_pixel_dimensions(self):
        offenders = [
            p.name for p in ICON_DIR.glob("*.svg")
            if '="1em"' in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            offenders, [], f"{offenders} still size in 1em, meaningless in <img>."
        )

    def test_icon_dir_is_not_empty(self):
        # Guards the whole suite passing vacuously if public/model-icons vanished.
        self.assertGreater(len(list(ICON_DIR.glob("*.svg"))), 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
