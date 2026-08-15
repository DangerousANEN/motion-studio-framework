"""Build labeled contact sheets and an index for the MSF v2.3 expansion catalog."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "remotion" / "out" / "expansion-catalog"
THUMB_W, THUMB_H = 324, 576
COLS, ROWS = 5, 2
PAD, LABEL_H = 24, 78
BG, INK, MUTED, ACCENT = "#0C1220", "#F3F6FF", "#AAB5CD", "#58D9FF"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if bold else ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",)
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def main() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    f_title, f_meta = font(24, True), font(16)
    per_page = COLS * ROWS
    index_lines = ["# MSF Studio v2.3 — All Expansion Scene Previews", "", "| № | Scene | Style | Preview |", "|---:|---|---|---|"]

    for start in range(0, len(manifest), per_page):
        items = manifest[start:start + per_page]
        page = start // per_page + 1
        canvas = Image.new("RGB", (COLS * THUMB_W + (COLS + 1) * PAD, ROWS * (THUMB_H + LABEL_H) + (ROWS + 1) * PAD), BG)
        draw = ImageDraw.Draw(canvas)
        for offset, item in enumerate(items):
            col, row = offset % COLS, offset // COLS
            x = PAD + col * (THUMB_W + PAD)
            y = PAD + row * (THUMB_H + LABEL_H + PAD)
            with Image.open(OUT / item["preview"]) as image:
                thumbnail = image.convert("RGB").resize((THUMB_W, THUMB_H), Image.Resampling.LANCZOS)
            canvas.paste(thumbnail, (x, y))
            draw.rounded_rectangle((x, y, x + THUMB_W, y + THUMB_H), radius=12, outline=ACCENT, width=2)
            draw.text((x, y + THUMB_H + 9), f"{item['number']:02d} · {item['preset']}", fill=INK, font=f_title)
            draw.text((x, y + THUMB_H + 42), str(item["style"]), fill=MUTED, font=f_meta)
        destination = OUT / f"catalog-page-{page}.png"
        canvas.save(destination, quality=95)
        print(destination)

    for item in manifest:
        index_lines.append(f"| {item['number']} | `{item['preset']}` | `{item['style']}` | `{item['preview']}` |")
    (OUT / "CATALOG_INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
