"""Per-glyph review images in scratch/review/: 32 glyphs each at 6x with cap/x-height/baseline guides.

    python tools/review24.py
"""
import os

from PIL import Image, ImageDraw

from fontdata import by_codepoint, load_glyphs
from project24 import project

SCALE, PER_ROW, ROWS = 6, 8, 4
CAP_TOP, X_TOP, BASELINE = 3, 8, 18


def tile(grid, cp):
    w, h = 12 * SCALE, 24 * SCALE
    img = Image.new("RGB", (w + 8, h + 24), (30, 30, 36))
    d = ImageDraw.Draw(img)
    d.text((4, 4), f"{cp:04X} {chr(cp) if cp >= 32 and cp != 127 else ''}", fill=(255, 255, 255))
    ox, oy = 4, 20
    d.rectangle((ox, oy, ox + w - 1, oy + h - 1), fill=(0, 0, 0))
    for y in range(24):
        for x in range(12):
            if grid[y][x]:
                d.rectangle((ox + x * SCALE, oy + y * SCALE, ox + (x + 1) * SCALE - 1, oy + (y + 1) * SCALE - 1),
                            fill=(235, 235, 235))
    for row, color in ((CAP_TOP, (200, 60, 60)), (X_TOP, (60, 160, 60)), (BASELINE, (70, 110, 220))):
        d.line((ox, oy + row * SCALE, ox + w, oy + row * SCALE), fill=color)
    d.line((ox + 6 * SCALE, oy, ox + 6 * SCALE, oy + h), fill=(90, 90, 40))  # cell center
    return img


def main():
    new = by_codepoint(load_glyphs())
    cps = sorted(new)
    os.makedirs("scratch/review", exist_ok=True)
    per = PER_ROW * ROWS
    for n in range(0, len(cps), per):
        chunk = cps[n:n + per]
        t0 = tile(project(new[chunk[0]], chunk[0]), chunk[0])
        sheet = Image.new("RGB", (PER_ROW * t0.width, ROWS * t0.height), (30, 30, 36))
        for i, cp in enumerate(chunk):
            sheet.paste(tile(project(new[cp], cp), cp), ((i % PER_ROW) * t0.width, (i // PER_ROW) * t0.height))
        sheet.save(f"scratch/review/{n // per:02d}.png")
    print(len(cps), "glyphs,", -(-len(cps) // per), "images")


if __name__ == "__main__":
    main()
