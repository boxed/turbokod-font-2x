"""Load the complete 16x32 glyph set.

Layers, later ones winning: box drawing/blocks scaled from the reference,
the smoothed seed (glyphs/font16x32.txt), composites (an accented letter
whose reference is an ASCII letter plus marks above reuses that letter's final
16x32 shape, even when the composite itself is hand-drawn), hand-drawn glyphs
(glyphs/hand16x32.txt).
"""
import os

from glyphfile import read_glyphs, to_grid
from seed import is_generated


def nearest2x(grid):
    return [[v for v in row for _ in (0, 1)] for row in grid for _ in (0, 1)]


def load_reference():
    """codepoint -> 8x16 grid"""
    out = {}
    for g in read_glyphs("glyphs/vga8x16.txt"):
        for cp in g["codepoints"]:
            out[cp] = to_grid(g["rows"])
    return out


def composite_bases(reference_glyphs):
    """name -> (base name, first base row in the 8x16 reference)."""
    letters = [g for g in reference_glyphs
               if g["codepoints"][0] < 0x80 and chr(g["codepoints"][0]).isalpha()]
    out = {}
    for g in reference_glyphs:
        if g["codepoints"][0] < 0x80:
            continue
        for b in letters:
            top = next(i for i, r in enumerate(b["rows"]) if "#" in r)
            above_is_blank = all("#" not in r for r in b["rows"][:top])
            if above_is_blank and b["rows"][top:] == g["rows"][top:] and g["rows"][:top] != b["rows"][:top]:
                if g["name"] not in out or top < out[g["name"]][1]:
                    out[g["name"]] = (b["name"], top)
    return out


def load_glyphs():
    """List of {name, codepoints, grid} for the 16x32 font."""
    glyphs = []
    for g in read_glyphs("glyphs/vga8x16.txt"):
        if all(is_generated(cp) for cp in g["codepoints"]):
            glyphs.append({**g, "grid": nearest2x(to_grid(g["rows"]))})
    hand = read_glyphs("glyphs/hand16x32.txt") if os.path.exists("glyphs/hand16x32.txt") else []
    hand_names = {g["name"] for g in hand}
    auto = [g for g in read_glyphs("glyphs/font16x32.txt") if g["name"] not in hand_names]
    final = {g["name"]: to_grid(g["rows"]) for g in auto + hand}
    # composites always take the base part from the base letter, so a
    # hand-drawn composite only needs its marks drawn
    for name, (base, top) in composite_bases(read_glyphs("glyphs/vga8x16.txt")).items():
        final[name] = final[name][:2 * top] + final[base][2 * top:]
    # glyphs whose references are identical (☺ at U+0001 and U+263A, ...)
    # become one glyph, drawn as the one with a real name
    reference_rows = {g["name"]: tuple(g["rows"]) for g in read_glyphs("glyphs/vga8x16.txt")}
    groups = {}
    for g in auto + hand:
        groups.setdefault(reference_rows[g["name"]], []).append(g)
    for group in groups.values():
        group.sort(key=lambda g: (g["name"].startswith("uni"), g["codepoints"][0] < 0x20))
        name = group[0]["name"]
        grid = final[name]
        assert len(grid) == 32 and all(len(r) == 16 for r in grid), f"{name}: bad size"
        codepoints = sorted(cp for g in group for cp in g["codepoints"])
        glyphs.append({"name": name, "codepoints": codepoints, "grid": grid})
    return glyphs


def by_codepoint(glyphs):
    return {cp: g["grid"] for g in glyphs for cp in g["codepoints"]}
