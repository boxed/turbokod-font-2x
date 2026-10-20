"""Rasterize the reference Px437 8x16 TTF into glyphs/vga8x16.txt."""
from fontTools.ttLib import TTFont
from fontTools.pens.pointInsidePen import PointInsidePen

from glyphfile import write_glyphs

UNIT = 100  # font units per pixel in the reference
W, H, DESCENT = 8, 16, 4


def main():
    font = TTFont("reference/Px437_IBM_VGA_8x16.ttf")
    glyph_set = font.getGlyphSet()
    by_glyph = {}
    for cp, name in sorted(font.getBestCmap().items()):
        by_glyph.setdefault(name, []).append(cp)
    glyphs = []
    for name, cps in sorted(by_glyph.items(), key=lambda kv: kv[1][0]):
        rows = []
        for y in range(H):
            row = ""
            for x in range(W):
                pen = PointInsidePen(glyph_set, ((x + 0.5) * UNIT, (H - DESCENT - y - 0.5) * UNIT))
                glyph_set[name].draw(pen)
                row += "#" if pen.getResult() else "."
            rows.append(row)
        glyphs.append({"name": name, "codepoints": cps, "rows": rows})
    write_glyphs("glyphs/vga8x16.txt", glyphs)
    print(f"{len(glyphs)} glyphs")


if __name__ == "__main__":
    main()
