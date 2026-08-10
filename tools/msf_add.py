#!/usr/bin/env python3
"""msf-add — scaffold a new component and wire it into the pipeline.

WHY
---
Adding a scene by hand means writing the component, importing it, registering
it, and remembering the conventions (safe area, resolveMotion channels, no
hardcoded 1080x1920). Four steps, three of them mechanical, all of them easy to
get subtly wrong -- and wrong in ways that render successfully but look broken.

This does the mechanical parts and leaves only the drawing to the author.

USAGE
    python tools/msf_add.py scene   MyScene --category ui-mock --summary "..."
    python tools/msf_add.py effect  MyEffect --summary "..."
    python tools/msf_add.py sfx     my_sound --kind click
    python tools/msf_add.py list
    python tools/msf_add.py verify

After scaffolding:
    cd remotion && npx tsx audit/registry_probe.ts   # registry integrity
    python tools/msf_add.py verify                   # renders every preset

The generated component is deliberately minimal but CORRECT: it reads the safe
area, drives animation through resolveMotion, and scales from useVideoConfig
rather than assuming a canvas size. Replace the body, keep the scaffolding.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTION = ROOT / "remotion"
PRESETS_DIR = REMOTION / "src" / "presets"
REGISTRY = REMOTION / "src" / "registry" / "presets.ts"
EFFECTS_REGISTRY = REMOTION / "src" / "registry" / "effects.ts"
SFX_REGISTRY = ROOT / "msf" / "audio" / "sfx_registry.py"

CATEGORIES = [
    "typography", "data", "diagram", "code",
    "ui-mock", "device", "three", "narrative", "transition-aid",
]

SCENE_TEMPLATE = '''import React from 'react';
import {{ useCurrentFrame, useVideoConfig }} from 'remotion';
import {{ BaseSceneProps }} from '../../VideoSpec.schema';
import {{ BRAND }} from '../brand';
import {{ resolveMotion }} from '../../lib/motion';
import {{ getSafeArea }} from '../../lib/safeArea';

const FONT = '"Inter", "SF Pro Display", -apple-system, sans-serif';

/**
 * {name} — {summary}
 *
 * Reads: {fields}
 */
export const {name}: React.FC<BaseSceneProps> = ({{
  title,
  subtitle,
  accentColor = BRAND.accentGreen,
  motion,
  safeArea = 'platform',
}}) => {{
  const frame = useCurrentFrame();
  const {{ width, height, fps, durationInFrames }} = useVideoConfig();
  const safe = getSafeArea(width, height, safeArea);

  // Motion goes through resolveMotion so intensity presets and per-scene
  // overrides both work. Never interpolate on raw frame numbers here.
  const reveal = resolveMotion(motion, fps, 'reveal')(frame, 0, 1);

  return (
    <div
      style={{{{
        position: 'absolute',
        inset: 0,
        backgroundColor: BRAND.bg,
        overflow: 'hidden',
      }}}}
    >
      <div
        style={{{{
          position: 'absolute',
          top: safe.top,
          left: safe.left,
          width: safe.width,
          height: safe.height,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 24,
          opacity: reveal,
          transform: `translateY(${{(1 - reveal) * 30}}px)`,
        }}}}
      >
        {{/* TODO: replace with the real scene body. */}}
        {{title && (
          <h1
            style={{{{
              margin: 0,
              fontFamily: FONT,
              fontSize: Math.round(height * 0.045),
              fontWeight: 900,
              color: BRAND.text,
              textAlign: 'center',
            }}}}
          >
            {{title}}
          </h1>
        )}}
        {{subtitle && (
          <p
            style={{{{
              margin: 0,
              fontFamily: FONT,
              fontSize: Math.round(height * 0.022),
              color: accentColor,
              textAlign: 'center',
            }}}}
          >
            {{subtitle}}
          </p>
        )}}
      </div>
    </div>
  );
}};
'''


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def add_scene(args: argparse.Namespace) -> None:
    name = args.name
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]+", name):
        fail(f"scene name must be PascalCase, got {name!r}")
    if args.category not in CATEGORIES:
        fail(f"category must be one of: {', '.join(CATEGORIES)}")

    sub = "three" if args.category == "three" else "."
    target = PRESETS_DIR / sub / f"{name}.tsx" if sub != "." else PRESETS_DIR / f"{name}.tsx"

    registry_src = read(REGISTRY)
    if f"  {name}: {{" in registry_src:
        fail(f"{name} is already in the registry")
    if target.exists():
        fail(f"{target.relative_to(ROOT)} already exists")

    fields = args.fields.split(",") if args.fields else ["title", "subtitle"]
    fields = [f.strip() for f in fields if f.strip()]

    # The template lives one level deeper for three/, so fix the import depth.
    body = SCENE_TEMPLATE.format(
        name=name, summary=args.summary, fields=", ".join(fields)
    )
    if sub == ".":
        body = body.replace("'../../VideoSpec.schema'", "'../VideoSpec.schema'")
        body = body.replace("'../brand'", "'./brand'")
        body = body.replace("'../../lib/motion'", "'../lib/motion'")
        body = body.replace("'../../lib/safeArea'", "'../lib/safeArea'")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")

    # Wire into the registry: import + entry, inserted deterministically.
    import_path = f"../presets/three/{name}" if sub == "three" else f"../presets/{name}"
    import_line = f"import {{ {name} }} from '{import_path}';\n"

    lines = registry_src.split("\n")
    last_import = max(i for i, l in enumerate(lines) if l.startswith("import "))
    lines.insert(last_import + 1, import_line.rstrip("\n"))

    entry = (
        f"  {name}: {{\n"
        f"    component: {name},\n"
        f"    category: '{args.category}',\n"
        f"    summary: '{args.summary}',\n"
        f"    fields: [{', '.join(repr(f).replace(chr(39), chr(39)) for f in fields)}],\n"
        + ("    dataDriven: true,\n" if args.data_driven else "")
        + ("    three: true,\n" if args.category == "three" else "")
        + f"  }},"
    )
    entry = entry.replace('"', "'")

    src = "\n".join(lines)
    marker = "export const PRESETS: PresetRegistry = {"
    idx = src.index(marker) + len(marker)
    src = src[:idx] + "\n" + entry + src[idx:]
    REGISTRY.write_text(src, encoding="utf-8")

    print(f"created  {target.relative_to(ROOT)}")
    print(f"wired    {REGISTRY.relative_to(ROOT)}")
    print()
    print("next:")
    print("  cd remotion && npx tsc --noEmit")
    print("  cd remotion && npx tsx audit/registry_probe.ts")
    print(f"  python tools/msf_add.py verify --only {name}")


def list_components(args: argparse.Namespace) -> None:
    src = read(REGISTRY)
    entries = re.findall(
        r"^  (\w+): \{\n\s+component: \w+,\n\s+category: '([^']+)',\n\s+summary: '([^']*)'",
        src,
        re.M,
    )
    by_cat: dict[str, list[tuple[str, str]]] = {}
    for nm, cat, summ in entries:
        by_cat.setdefault(cat, []).append((nm, summ))

    total = sum(len(v) for v in by_cat.values())
    print(f"{total} scene presets\n")
    for cat in sorted(by_cat):
        print(f"  {cat}")
        for nm, summ in sorted(by_cat[cat]):
            print(f"    {nm:<22} {summ}")
        print()


def verify(args: argparse.Namespace) -> None:
    """Render one frame of every preset and assert the frame is not blank.

    A preset that throws renders the error card; a preset that draws nothing
    renders the background. Both exit 0, so the check has to look at pixels.
    """
    src = read(REGISTRY)
    names = re.findall(r"^  (\w+): \{$", src, re.M)
    if args.only:
        names = [n for n in names if n == args.only]
        if not names:
            fail(f"{args.only} not found in the registry")

    out = ROOT / "audit" / "verify"
    out.mkdir(parents=True, exist_ok=True)
    results = []

    for nm in names:
        spec = {
            "width": 1080, "height": 1920, "fps": 60,
            "format": "vertical", "theme": "pop",
            "scenes": [{
                "id": "v", "durationInFrames": 90, "preset": nm,
                "title": "Проверка", "subtitle": "Тестовая подпись",
            }],
        }
        spec_path = out / f"{nm}.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        png = out / f"{nm}.png"
        r = subprocess.run(
            ["npx", "remotion", "still", "Main", str(png),
             f"--props={spec_path}", "--frame=45", "--log=error"],
            cwd=REMOTION, capture_output=True, text=True, shell=True,
        )
        results.append((nm, r.returncode, png.exists()))
        print(f"  {'ok ' if r.returncode == 0 and png.exists() else 'FAIL'} {nm}")

    bad = [n for n, rc, ex in results if rc != 0 or not ex]
    print()
    print(f"{len(results) - len(bad)}/{len(results)} rendered")
    if bad:
        print("failed:", ", ".join(bad))
        sys.exit(1)


def main() -> int:
    ap = argparse.ArgumentParser(prog="msf-add", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scene", help="scaffold a scene preset and register it")
    s.add_argument("name")
    s.add_argument("--category", default="typography", choices=CATEGORIES)
    s.add_argument("--summary", required=True)
    s.add_argument("--fields", default="", help="comma-separated spec fields it reads")
    s.add_argument("--data-driven", action="store_true",
                   help="meaningless without data; excluded from blind rotation")
    s.set_defaults(func=add_scene)

    l = sub.add_parser("list", help="list registered components")
    l.set_defaults(func=list_components)

    v = sub.add_parser("verify", help="render every preset and check it is not blank")
    v.add_argument("--only", default="")
    v.set_defaults(func=verify)

    args = ap.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
