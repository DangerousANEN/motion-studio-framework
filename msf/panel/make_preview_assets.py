"""Generate the demo assets media presets need in order to preview at all.

WHY THIS EXISTS
---------------
Five presets host an external asset — ImageShowcase, VideoEmbed, ScreenRecord,
PhoneMockup and LyricLines' backdrop — and without one they render a loud
MISSING ASSET placeholder. `validate_spec` refuses such a spec outright, so the
panel could not preview them at all.

Committing binary sample media to the repo would be the obvious fix and a bad one:
it bloats clones forever and the files drift from what the presets read. Generating
them locally is a few hundred KB and reproducible.

Run: python -m msf.panel.make_preview_assets

PITFALL — ffmpeg drawtext on this machine
-----------------------------------------
The WinGet ffmpeg build has libfreetype but NO fontconfig configuration:

    Fontconfig error: Cannot load default config file: File not found

so `drawtext=text=...` silently produces no file unless `fontfile=` is given
explicitly, with the Windows path escaped as `C\\:/Windows/Fonts/arialbd.ttf`.
Stills are drawn with PIL instead, which avoids the issue entirely; only the video
uses ffmpeg, and it draws no text.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

REPO = Path(__file__).resolve().parents[2]
PREVIEW_DIR = REPO / "remotion" / "public" / "preview"

# Paths are relative to remotion/public/ because the presets pass anything not
# starting with http:// through Remotion's staticFile().
STILL_1 = "preview/demo_1.png"
STILL_2 = "preview/demo_2.png"
CLIP = "preview/demo_clip.mp4"

_STILLS: List[Tuple[str, Tuple[int, int, int], Tuple[int, int, int], str]] = [
    (STILL_1, (18, 32, 58), (31, 122, 90), "КАДР 1"),
    (STILL_2, (58, 18, 48), (122, 31, 74), "КАДР 2"),
]


def _font(size: int):
    from PIL import ImageFont

    # Cyrillic-capable fonts present on Windows. DejaVu (PIL's bundled fallback)
    # covers Cyrillic too but load_default() ignores the size argument, giving an
    # unreadable 11px label on a 1080px image.
    for name in ("arialbd.ttf", "arial.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_stills() -> List[Path]:
    from PIL import Image, ImageDraw

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    w, h = 1080, 1350  # 4:5, the shape a phone photo actually arrives in

    for rel, top, band, label in _STILLS:
        img = Image.new("RGB", (w, h), top)
        d = ImageDraw.Draw(img)
        # A vertical gradient plus a contrasting band: enough structure that
        # kenBurns drift and `fit: cover/contain` are visible in a still.
        for y in range(h):
            t = y / h
            d.line(
                [(0, y), (w, y)],
                fill=(
                    int(top[0] + (band[0] - top[0]) * t),
                    int(top[1] + (band[1] - top[1]) * t),
                    int(top[2] + (band[2] - top[2]) * t),
                ),
            )
        d.rectangle([0, h // 2 - 110, w, h // 2 + 110], fill=band)
        f = _font(120)
        box = d.textbbox((0, 0), label, font=f)
        d.text(
            ((w - (box[2] - box[0])) / 2, (h - (box[3] - box[1])) / 2 - box[1]),
            label, font=f, fill=(255, 255, 255),
        )
        out = REPO / "remotion" / "public" / rel
        img.save(out)
        written.append(out)
    return written


def make_clip() -> Path:
    """A 4-second test pattern. No drawtext — see the pitfall note above."""
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    out = REPO / "remotion" / "public" / CLIP
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-f", "lavfi",
         "-i", "testsrc2=s=1080x1350:d=4:r=30",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "32",
         str(out)],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0 or not out.is_file():
        tail = (proc.stderr or "").strip().splitlines()[-3:]
        raise RuntimeError(f"ffmpeg failed to build the demo clip: {' | '.join(tail)}")
    return out


def ensure() -> dict:
    """Create anything missing. Cheap enough to call on panel startup."""
    made: List[str] = []
    if not all((REPO / "remotion" / "public" / rel).is_file() for rel, *_ in _STILLS):
        made += [p.name for p in make_stills()]
    if not (REPO / "remotion" / "public" / CLIP).is_file():
        made.append(make_clip().name)
    return {
        "still_1": STILL_1,
        "still_2": STILL_2,
        "clip": CLIP,
        "created": made,
        "dir": str(PREVIEW_DIR),
    }


if __name__ == "__main__":
    info = ensure()
    print(f"preview assets in {info['dir']}")
    for k in ("still_1", "still_2", "clip"):
        p = REPO / "remotion" / "public" / info[k]
        print(f"  {info[k]:28} {'OK' if p.is_file() else 'MISSING':8} "
              f"{p.stat().st_size if p.is_file() else 0} bytes")
    print(f"created this run: {info['created'] or 'nothing (all present)'}")
