from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "output" / "studio" / "element_builder" / "demos" / "textured_3d"
out.mkdir(parents=True, exist_ok=True)
asset = json.loads(Path("/tmp/texture_upload.json").read_text(encoding="utf-8"))["asset"]
resource_id = asset["asset_id"]
graph = {
    "version": 1,
    "background": "#08101d",
    "camera": {"preset": "orbit", "position": [0, 1.2, 7], "fov": 42},
    "lights": [
        {"type": "ambient", "intensity": 0.55},
        {"type": "directional", "position": [4, 6, 5], "intensity": 1.3, "color": "#ffffff"},
        {"type": "point", "position": [-3, 2, 2], "intensity": 4.0, "color": "#52ff9a"},
    ],
    "grid": {"enabled": True, "size": 16, "divisions": 16, "color": "#2d604d", "secondaryColor": "#152936"},
    "nodes": [
        {
            "id": "textureCard",
            "type": "plane",
            "position": [-1.6, 0.8, 0],
            "rotation": [0, 0.12, 0],
            "scale": [1.9, 1.15, 1],
            "resourceId": resource_id,
            "doubleSided": True,
            "motion": {"from": {"position": [-2.4, 0.8, 0]}, "to": {"position": [-1.6, 0.8, 0]}, "start": 0, "end": 48, "ease": "easeOut"},
        },
        {
            "id": "signalCore",
            "type": "icosahedron",
            "position": [1.25, 0.2, 0.3],
            "scale": [1.15, 1.15, 1.15],
            "color": "#76a7ff",
            "emissive": "#355fe0",
            "motion": {"from": {"rotation": [0, 0, 0]}, "to": {"rotation": [0, 6.28, 0]}, "start": 0, "end": 180, "loop": "repeat"},
        },
        {"id": "orbitRing", "type": "torus", "position": [1.25, 0.2, 0.3], "rotation": [1.1, 0, 0], "scale": [1.8, 1.8, 1.8], "color": "#52ff9a", "wireframe": True},
        {"id": "captionPanel", "type": "box", "position": [0, -1.35, 0], "scale": [2.9, 0.12, 0.08], "color": "#52ff9a", "emissive": "#1d8c61"},
    ],
}
request = {
    "name": "TextureSignalGallery",
    "summary": "3D image texture gallery with animated signal core",
    "style_id": "llm_hubs_neon",
    "project_id": "default",
    "graph": graph,
}
base = "http://localhost:8765/api/studio/element-builder/3d"
for mode in ("preview", "motion", "register"):
    response = requests.post(f"{base}/{mode}", json=request, timeout=180)
    response.raise_for_status()
    data = response.json()
    (out / f"textured_3d_{mode}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if data.get("url"):
        media = requests.get("http://localhost:8765" + data["url"], timeout=60)
        media.raise_for_status()
        suffix = ".mp4" if mode == "motion" else ".png"
        (out / f"texture_signal_gallery{suffix}").write_bytes(media.content)
(out / "textured_3d_graph.json").write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"resource_id": resource_id, "output": str(out)}, ensure_ascii=False))
