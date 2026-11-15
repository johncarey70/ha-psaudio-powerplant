#!/usr/bin/env python3
"""Generate local brand icons for HACS / Home Assistant."""

from __future__ import annotations

from math import pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def _wave_points(amp, phase, y_mid, cycles, samples, x0, x1):
    points = []
    for i in range(samples + 1):
        t = i / samples
        x = x0 + t * (x1 - x0)
        y = y_mid + amp * sin(2 * pi * cycles * t + phase)
        points.append((x, y))
    return points


def make_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = max(1, size // 64)
    radius = int(size * 0.22)
    draw.rounded_rectangle(
        (margin, margin, size - 1 - margin, size - 1 - margin),
        radius=radius,
        fill=(18, 22, 28, 255),
    )

    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(highlight).rounded_rectangle(
        (margin, margin, size - 1 - margin, size // 2),
        radius=radius,
        fill=(255, 255, 255, 18),
    )
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rectangle((0, int(size * 0.28), size, size), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=size * 0.08))
    inv = mask.point(lambda p: 255 - p)
    highlight.putalpha(
        Image.composite(Image.new("L", (size, size), 0), highlight.split()[-1], inv)
    )
    img = Image.alpha_composite(img, highlight)

    x0 = int(size * 0.16)
    x1 = int(size * 0.84)
    y_mid = size * 0.52
    samples = max(80, size)
    thickness = max(3, int(size * 0.045))

    dirty = _wave_points(
        amp=size * 0.10,
        phase=0.4,
        y_mid=y_mid + size * 0.01,
        cycles=3.0,
        samples=samples,
        x0=x0,
        x1=x1,
    )
    dlayer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(dlayer).line(
        dirty, fill=(160, 80, 70, 90), width=max(2, thickness // 2), joint="curve"
    )
    img = Image.alpha_composite(
        img, dlayer.filter(ImageFilter.GaussianBlur(radius=max(0.5, size / 400)))
    )

    clean = _wave_points(
        amp=size * 0.16,
        phase=0.0,
        y_mid=y_mid,
        cycles=1.5,
        samples=samples,
        x0=x0,
        x1=x1,
    )
    wlayer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(wlayer).line(
        clean, fill=(120, 200, 220, 70), width=thickness * 3, joint="curve"
    )
    img = Image.alpha_composite(
        img, wlayer.filter(ImageFilter.GaussianBlur(radius=max(1, size / 80)))
    )

    clayer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clayer)
    cd.line(clean, fill=(210, 230, 235, 255), width=thickness, joint="curve")
    cap = thickness / 2
    cd.ellipse(
        (clean[0][0] - cap, clean[0][1] - cap, clean[0][0] + cap, clean[0][1] + cap),
        fill=(210, 230, 235, 255),
    )
    cd.ellipse(
        (
            clean[-1][0] - cap,
            clean[-1][1] - cap,
            clean[-1][0] + cap,
            clean[-1][1] + cap,
        ),
        fill=(210, 230, 235, 255),
    )
    return Image.alpha_composite(img, clayer)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    dest = root / "custom_components" / "psaudio_powerplant" / "brand"
    dest.mkdir(parents=True, exist_ok=True)
    for name, size in (("icon.png", 256), ("icon@2x.png", 512)):
        path = dest / name
        make_icon(size).save(path, "PNG", optimize=True)
        print(f"wrote {path} ({size}x{size})")


if __name__ == "__main__":
    main()
