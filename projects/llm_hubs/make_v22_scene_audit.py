"""Create labelled still-contact sheets for every final v2.2 scene.

This is a deterministic audit artifact, not a new visual asset: frames come from
actual encoded MP4s at a stable reading-dwell point in each VideoSpec scene.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "projects" / "llm_hubs"
GENERATED = PROJECT / "generated"
RENDERED = PROJECT / "rendered"
OUT = PROJECT / "qa_v22"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CELL_W, CELL_H = 252, 452
FRAME_W, FRAME_H = 234, 384
COLS = 5


def load_scene_frames(spec: dict) -> list[tuple[float, dict]]:
    fps = int(spec["fps"])
    cursor = 0
    selected: list[tuple[float, dict]] = []
    for scene in spec["scenes"]:
        duration = int(scene["durationInFrames"])
        # At 68%, animations have settled but the scene has not started exiting.
        point = (cursor + max(4, int(duration * 0.68))) / fps
        selected.append((point, scene))
        cursor += duration - int((scene.get("transition") or {}).get("durationInFrames", 0))
    return selected


def extract(video: Path, at: float, output: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(video),
        "-frames:v", "1", "-vf", f"scale={FRAME_W}:{FRAME_H}:force_original_aspect_ratio=decrease,pad={FRAME_W}:{FRAME_H}:(ow-iw)/2:(oh-ih)/2:#070a0a",
        str(output),
    ], check=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((GENERATED / "series_manifest.json").read_text(encoding="utf-8"))["videos"]
    frames: list[tuple[Path, str]] = []
    inventory: list[dict] = []
    for video_index, item in enumerate(manifest, start=1):
        spec = json.loads((ROOT / item["spec"]).read_text(encoding="utf-8"))
        video_path = RENDERED / f"{item['slug']}.mp4"
        for scene_index, (at, scene) in enumerate(load_scene_frames(spec), start=1):
            still = OUT / f"{video_index:02d}_{scene_index:02d}_{scene['preset']}.png"
            extract(video_path, at, still)
            label = f"{video_index}.{scene_index}  {scene['preset']}\n{scene['id']}  ·  {at:.1f}s"
            frames.append((still, label))
            inventory.append({"video": item["slug"], "scene": scene["id"], "preset": scene["preset"], "at_seconds": round(at, 2), "still": str(still.relative_to(ROOT))})

    rows = (len(frames) + COLS - 1) // COLS
    canvas = Image.new("RGB", (CELL_W * COLS, CELL_H * rows), "#06090a")
    title_font = ImageFont.truetype(FONT, 14)
    label_font = ImageFont.truetype(FONT_REGULAR, 11)
    for index, (path, label) in enumerate(frames):
        x = (index % COLS) * CELL_W
        y = (index // COLS) * CELL_H
        tile = Image.open(path).convert("RGB")
        canvas.paste(tile, (x + 9, y + 9))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((x + 8, y + 399, x + CELL_W - 8, y + CELL_H - 8), fill="#101819", outline="#00F0A8")
        head, tail = label.split("\n", 1)
        draw.text((x + 15, y + 405), head, font=title_font, fill="#F5FFFF")
        draw.text((x + 15, y + 424), tail, font=label_font, fill="#B8CBCB")
    sheet = OUT / "LLM_HUBS_V22_ALL_SCENES_AUDIT.png"
    canvas.save(sheet)
    (OUT / "scene_inventory.json").write_text(json.dumps({"scenes": inventory}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(sheet)


if __name__ == "__main__":
    main()
