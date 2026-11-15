#!/usr/bin/env python3
"""Build Home Assistant brand icons from the official PS Audio logo.

Official sources (also stored as base64 under .github/brand-src/):

* Black mark, used as the psaudio.com header logo, favicon, and JSON-LD logo:
  https://www.psaudio.com/cdn/shop/files/ps-logo-icon-black.png?v=1758450286
* White mark, same artwork, for dark backgrounds:
  https://www.psaudio.com/cdn/shop/files/ps-logo-icon.png

The official mark is square, so logo.png is omitted; Home Assistant falls
back to the icon. dark_icon variants are included so the black mark is not
invisible on a dark UI.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".github" / "brand-src"
DEST = ROOT / "custom_components" / "psaudio_powerplant" / "brand"

SOURCES = {
    "icon": SRC / "ps-logo-icon-black.png.b64",
    "dark_icon": SRC / "ps-logo-icon.png.b64",
}


def load_source(path: Path) -> Image.Image:
    data = base64.b64decode(path.read_text())
    return Image.open(io.BytesIO(data)).convert("RGBA")


def fit_square(im: Image.Image, size: int) -> Image.Image:
    # The official assets already fill a square canvas (rounded square to the
    # edges), so they are not trimmed further.
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
