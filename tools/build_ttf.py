"""Build a TTF from the 16x32 glyphs.

    python tools/build_ttf.py out/font.ttf [--strike ebdt|bdat|both|none] [--family NAME]

Outlines are unions of whole pixel squares (64 units per pixel, 2048 upem).
The original 8x16 reference bitmaps are embedded as a 16 ppem bitmap strike
(--strike none leaves it out), so renderers that honor embedded bitmaps draw the original font at
16px and the 16x32 outlines at larger sizes. ebdt writes the OpenType
EBDT/EBLC tables, bdat writes Apple's bdat/bloc, both writes both.

The default is ebdt: CoreText honors either table pair on its own (tools/strike_test.py
checks this), FreeType and Windows read EBDT, and with both pairs present
CoreText ignores the strike.
"""
import argparse
import os
from xml.sax.saxutils import quoteattr

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import newTable

from fontdata import load_glyphs, load_reference
from smooth import corners, trace

UNIT = 64  # font units per pixel at the 32px design size
CELL_W, CELL_H = 16, 32
ASCENT_PX, DESCENT_PX = 24, 8
UPEM = CELL_H * UNIT

STRIKE_PPEM = 16
STRIKE_ASCENT, STRIKE_DESCENT = 12, 4

FAMILY = "TurboKod VGA 16x32"
VERSION = "0.1"


def draw_glyph(grid):
    pen = TTGlyphPen(None)
    if any(any(row) for row in grid):
        loops, _ = trace(grid)
        for loop in loops:
            # trace() keeps the inside on the right with y pointing down;
            # flipping y swaps that, and TrueType wants clockwise outer contours
            points = [(x * UNIT, (ASCENT_PX - y) * UNIT) for (x, y), _, _ in corners(loop)][::-1]
            pen.moveTo(points[0])
            for p in points[1:]:
                pen.lineTo(p)
            pen.closePath()
    return pen.glyph()


def strike_xml(tag, glyph_order, bitmaps):
    """TTX XML for an EBLC/EBDT (or bloc/bdat) pair with one 16 ppem strike."""
    loc_tag, data_tag = {"ebdt": ("EBLC", "EBDT"), "bdat": ("bloc", "bdat")}[tag]
    line_metrics = "".join(
        f'<{name} value="{value}"/>'
        for name, value in [("ascender", STRIKE_ASCENT), ("descender", -STRIKE_DESCENT),
                            ("widthMax", CELL_W // 2), ("caretSlopeNumerator", 1),
                            ("caretSlopeDenominator", 0), ("caretOffset", 0), ("minOriginSB", 0),
                            ("minAdvanceSB", 0), ("maxBeforeBL", STRIKE_ASCENT),
                            ("minAfterBL", -STRIKE_DESCENT), ("pad1", 0), ("pad2", 0)])
    last = len(glyph_order) - 1
    locs = "".join(f"<glyphLoc name={quoteattr(name)}/>" for name in glyph_order)
    eblc = (
        f'<{loc_tag}><header version="2.0"/><strike index="0"><bitmapSizeTable>'
        f'<sbitLineMetrics direction="hori">{line_metrics}</sbitLineMetrics>'
        f'<sbitLineMetrics direction="vert">{line_metrics}</sbitLineMetrics>'
        f'<colorRef value="0"/><startGlyphIndex value="0"/><endGlyphIndex value="{last}"/>'
        f'<ppemX value="{STRIKE_PPEM}"/><ppemY value="{STRIKE_PPEM}"/><bitDepth value="1"/><flags value="1"/>'
        f'</bitmapSizeTable><eblc_index_sub_table_1 imageFormat="1" firstGlyphIndex="0" '
        f'lastGlyphIndex="{last}">{locs}</eblc_index_sub_table_1></strike></{loc_tag}>'
    )
    metrics = (f'<SmallGlyphMetrics><height value="{STRIKE_PPEM}"/><width value="{CELL_W // 2}"/>'
               f'<BearingX value="0"/><BearingY value="{STRIKE_ASCENT}"/>'
               f'<Advance value="{CELL_W // 2}"/></SmallGlyphMetrics>')
    glyphs = []
    for name in glyph_order:
        rows = "".join(
            '<row value="%s"/>' % "".join("@" if v else "." for v in row) for row in bitmaps[name])
        glyphs.append(f'<{tag}_bitmap_format_1 name={quoteattr(name)}>{metrics}'
                      f'<bitwiseimagedata bitDepth="1" width="{CELL_W // 2}" height="{STRIKE_PPEM}">'
                      f'{rows}</bitwiseimagedata></{tag}_bitmap_format_1>')
    ebdt = f'<{data_tag}><header version="2.0"/><strikedata index="0">{"".join(glyphs)}</strikedata></{data_tag}>'
    return eblc + ebdt


def build(path, strike=None, family=FAMILY):
    glyphs = sorted(load_glyphs(), key=lambda g: g["codepoints"][0])
    glyph_order = [".notdef"] + [g["name"] for g in glyphs]
    notdef = [[False] * CELL_W for _ in range(CELL_H)]
    for y in range(4, 24):
        for x in range(1, 13):
            notdef[y][x] = y in (4, 5, 22, 23) or x in (1, 2, 11, 12)

    fb = FontBuilder(UPEM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({cp: g["name"] for g in glyphs for cp in g["codepoints"]})
    fb.setupGlyf({".notdef": draw_glyph(notdef), **{g["name"]: draw_glyph(g["grid"]) for g in glyphs}})
    glyf = fb.font["glyf"]
    fb.setupHorizontalMetrics({name: (CELL_W * UNIT, getattr(glyf[name], "xMin", 0)) for name in glyph_order})
    fb.setupHorizontalHeader(ascent=ASCENT_PX * UNIT, descent=-DESCENT_PX * UNIT, lineGap=0)
    ps_name = family.replace(" ", "")
    fb.setupNameTable({
        "familyName": family,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{ps_name}:{VERSION}",
        "fullName": family,
        "psName": ps_name,
        "version": f"Version {VERSION}",
        "copyright": "Based on Px437 IBM VGA 8x16 by VileR (int10h.org)",
        "licenseDescription": "Creative Commons Attribution-ShareAlike 4.0 International",
        "licenseInfoURL": "http://creativecommons.org/licenses/by-sa/4.0/",
    })
    fb.setupOS2(
        sTypoAscender=ASCENT_PX * UNIT, sTypoDescender=-DESCENT_PX * UNIT, sTypoLineGap=0,
        usWinAscent=ASCENT_PX * UNIT, usWinDescent=DESCENT_PX * UNIT,
        xAvgCharWidth=CELL_W * UNIT,
    )
    fb.font["OS/2"].panose.bFamilyType = 2
    fb.font["OS/2"].panose.bProportion = 9  # monospaced
    fb.setupPost(isFixedPitch=1)
    fb.font["head"].flags |= 0x8  # integer ppem scaling
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x2}  # as in the reference font
    fb.font["gasp"] = gasp

    if strike:
        reference = load_reference()
        empty = [[False] * (CELL_W // 2) for _ in range(STRIKE_PPEM)]
        bitmaps = {".notdef": empty, **{g["name"]: reference[g["codepoints"][0]] for g in glyphs}}
        xml = "".join(strike_xml(tag, glyph_order, bitmaps)
                      for tag in (["ebdt", "bdat"] if strike == "both" else [strike]))
        os.makedirs("scratch", exist_ok=True)
        xml_path = "scratch/strike.ttx"
        with open(xml_path, "w") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?><ttFont>{xml}</ttFont>')
        fb.font.importXML(xml_path)

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fb.save(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--strike", choices=["ebdt", "bdat", "both", "none"], default="ebdt")
    parser.add_argument("--family", default=FAMILY)
    args = parser.parse_args()
    build(args.path, None if args.strike == "none" else args.strike, args.family)
    print(args.path)


if __name__ == "__main__":
    main()
