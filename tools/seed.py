"""Generate the initial 16x32 glyph source from the 8x16 reference.

Safe to rerun: hand-drawn glyphs live in glyphs/hand16x32.txt and override
these. Box drawing, block elements and shades are excluded: build.py generates them
from the reference with an exact 2x scale so they keep tiling.
"""
from glyphfile import read_glyphs, write_glyphs, to_grid, to_rows
from smooth import upscale

OUT = "glyphs/font16x32.txt"


def is_generated(cp):
    return 0x2500 <= cp <= 0x259F


def main():
    glyphs = []
    for g in read_glyphs("glyphs/vga8x16.txt"):
        if all(is_generated(cp) for cp in g["codepoints"]):
            continue
        glyphs.append({**g, "rows": to_rows(upscale(to_grid(g["rows"])))})
    write_glyphs(OUT, glyphs)
    print(f"{len(glyphs)} glyphs -> {OUT}")


if __name__ == "__main__":
    main()
