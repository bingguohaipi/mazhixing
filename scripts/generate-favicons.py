#!/usr/bin/env python3
"""Regenerate public/imgs favicons from imgs/icon.png (trim + fill canvas)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_CANDIDATES = (ROOT / "imgs" / "icon.png", ROOT / "public" / "imgs" / "icon.png")
OUT_DIR = ROOT / "public" / "imgs"


def load_source() -> Path:
    for path in SRC_CANDIDATES:
        if not path.is_file():
            continue
        try:
            Image.open(path).load()
            return path
        except OSError:
            continue
    raise SystemExit("No readable icon.png in imgs/ or public/imgs/")


def trim_star(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    min_x, min_y, max_x, max_y = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 20:
                continue
            if r < 15 and g < 15 and b < 15:
                continue
            found = True
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if not found:
        return rgba
    return rgba.crop((min_x, min_y, max_x + 1, max_y + 1))


def render(cropped: Image.Image, size: int, fill: float = 0.98) -> Image.Image:
    # 透明底，避免浏览器标签栏出现黑方块
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cw, ch = cropped.size
    scale = (size * fill) / max(cw, ch)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (size - nw) // 2
    y = (size - nh) // 2
    canvas.paste(resized, (x, y), resized)
    return canvas


def main() -> None:
    src = load_source()
    cropped = trim_star(Image.open(src))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [
        (32, "favicon-32.png"),
        (48, "favicon-48.png"),
        (180, "apple-touch-icon.png"),
        (192, "favicon-192.png"),
        (512, "favicon-512.png"),
    ]
    for size, name in outputs:
        render(cropped, size).save(OUT_DIR / name, optimize=True)
    render(cropped, 1024).save(OUT_DIR / "icon.png", optimize=True)
    print(f"Generated favicons from {src}")


if __name__ == "__main__":
    main()
