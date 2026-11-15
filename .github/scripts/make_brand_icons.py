#!/usr/bin/env python3
"""Build Home Assistant brand icons from the official PS Audio blue logo.

Official source (also stored as base64 under .github/brand-src/):

https://us1.discourse-cdn.com/flex015/uploads/psaudio/original/3X/f/0/f0618c574cd33d419ec538679491374dc01db460.png

This is the official 1000x1000 PNG of the blue sine-wave mark used as
the PS Audio forum favicon and apple-touch-icon (the site icon browsers
show in search suggestions). See .github/brand-src/SOURCE.md.

The official mark is square, so logo.png is omitted; Home Assistant falls
back to the icon. dark_icon uses the same official blue asset.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".github" / "brand-src"
DEST = ROOT / "custom_components" / "psaudio_powerplant" / "brand"

BLUE = SRC / "ps-audio-logo-blue.png.b64"
SOURCES = {
    "icon": BLUE,
    "dark_icon": BLUE,
}


def load_source(path: Path) -> Image.Image:
    data = base64.b64decode(path.read_text())
    return Image.open(io.BytesIO(data)).convert("RGBA")


def fit_square(im: Image.Image, size: int) -> Image.Image:
    # The official asset already fills a square canvas (rounded square
    # with a transparent wave cutout), so it is not trimmed further.
    if im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    return im


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for stem, src in SOURCES.items():
        original = load_source(src)
        for name, size in ((f"{stem}.png", 256), (f"{stem}@2x.png", 512)):
            path = DEST / name
            icon = fit_square(original, size)
            icon.save(path, format="PNG", optimize=True, compress_level=9)
            print(f"wrote {path} ({size}x{size}, {path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
