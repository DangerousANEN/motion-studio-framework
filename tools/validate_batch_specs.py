#!/usr/bin/env python3
"""Validate every generated MSF VideoSpec JSON in a batch directory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from msf.spec import validate_spec


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path, help="Directory holding *.spec.json files")
    args = parser.parse_args()
    paths = sorted(args.directory.glob("*.spec.json"))
    if not paths:
        raise SystemExit(f"No .spec.json files found in {args.directory}")
    for path in paths:
        spec = json.loads(path.read_text(encoding="utf-8"))
        validate_spec(spec)
        presets = [scene.get("preset", "?") for scene in spec.get("scenes", [])]
        print(f"OK {path.name}: {' → '.join(presets)}")


if __name__ == "__main__":
    main()
