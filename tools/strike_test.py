"""Check whether CoreText uses an embedded 8x16 bitmap strike at 16px.

    python tools/strike_test.py

Builds the font without a strike and with EBDT/EBLC, bdat/bloc and both,
renders a sample with CoreText (antialiasing off) at 16px, 32px and 16pt
through a 2x CTM (a Retina screen), and
compares every character cell with the 8x16 reference bitmap and the 16x32
glyph. Writes the renders to out/test/.
"""
import os
import subprocess
import sys

from PIL import Image

from build_ttf import build
from fontdata import by_codepoint, load_glyphs, load_reference

TEXT = "AVWXkx/\\<>@&%$#90Sg"
VARIANTS = [None, "ebdt", "bdat", "both"]
OUT = "out/test"


def render(font_path, size, png_path, scale=1):
    subprocess.run(["swift", "tools/coretext_render.swift", font_path, str(size), TEXT, png_path, str(scale)],
                   check=True)
    img = Image.open(png_path).convert("L")
    cell_w, cell_h = size * scale // 2, size * scale
    cells = []
    for i in range(len(TEXT)):
        cells.append([[img.getpixel((i * cell_w + x, y)) < 128 for x in range(cell_w)] for y in range(cell_h)])
    return cells


def matches(cells, expected):
    return sum(cell == expected[ord(ch)] for cell, ch in zip(cells, TEXT))


def main():
    os.makedirs(OUT, exist_ok=True)
    reference = load_reference()
    new = by_codepoint(load_glyphs())
    print(f"{len(TEXT)} characters: {TEXT}")
    print(f"{'variant':10} {'16px = original':>16} {'16px = outline':>15} {'32px = 16x32':>13} "
          f"{'16pt@2x = 16x32':>16}")
    outline_16 = None
    for variant in VARIANTS:
        name = variant or "none"
        font_path = f"{OUT}/tk-{name}.ttf"
        build(font_path, variant, f"TK Strike Test {name}")
        cells_16 = render(font_path, 16, f"{OUT}/tk-{name}-16.png")
        cells_32 = render(font_path, 32, f"{OUT}/tk-{name}-32.png")
        cells_retina = render(font_path, 16, f"{OUT}/tk-{name}-16@2x.png", scale=2)
        if variant is None:
            outline_16 = {ord(ch): cell for ch, cell in zip(TEXT, cells_16)}
        print(f"{name:10} {matches(cells_16, reference):>16} {matches(cells_16, outline_16):>15} "
              f"{matches(cells_32, new):>13} {matches(cells_retina, new):>16}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
