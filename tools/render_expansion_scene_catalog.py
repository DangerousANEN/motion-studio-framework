"""Render the v2.3 expansion-scene visual catalog as standalone Remotion stills.

Run after build_expansion_scene_catalog.py from the repository root:
    PYTHONPATH=. python3 tools/render_expansion_scene_catalog.py
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTION = REPO / "remotion"
OUT = REMOTION / "out" / "expansion-catalog"
CLI = REMOTION / "node_modules" / ".bin" / "remotion"


def main() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    rendered: list[str] = []
    for item in manifest:
        spec = OUT / str(item["spec"])
        preview = OUT / str(item["preview"])
        command = [
            str(CLI), "still", "src/index.ts", "Main", str(preview),
            f"--props={spec}", f"--frame={item['frame']}",
            "--browser-executable=/usr/bin/chromium", "--log=error",
        ]
        print(f"rendering {item['number']:02d} {item['preset']} → {preview.name}", flush=True)
        subprocess.run(command, cwd=REMOTION, check=True, timeout=180)
        rendered.append(preview.name)
    (OUT / "rendered_files.txt").write_text("\n".join(rendered) + "\n", encoding="utf-8")
    print(f"rendered={len(rendered)} out={OUT}")


if __name__ == "__main__":
    main()
