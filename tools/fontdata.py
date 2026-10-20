"""Load the complete 16x32 glyph set.

Layers, later ones winning: box drawing/blocks scaled from the reference,
the smoothed seed (glyphs/font16x32.txt), hand-drawn glyphs
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


def load_glyphs():
    """List of {name, codepoints, grid} for the 16x32 font."""
    glyphs = []
    for g in read_glyphs("glyphs/vga8x16.txt"):
        if all(is_generated(cp) for cp in g["codepoints"]):
            glyphs.append({**g, "grid": nearest2x(to_grid(g["rows"]))})
    hand = read_glyphs("glyphs/hand16x32.txt") if os.path.exists("glyphs/hand16x32.txt") else []
    hand_names = {g["name"] for g in hand}
    auto = [g for g in read_glyphs("glyphs/font16x32.txt") if g["name"] not in hand_names]
    for g in auto + hand:
        grid = to_grid(g["rows"])
        assert len(grid) == 32 and all(len(r) == 16 for r in grid), f"{g['name']}: bad size"
        glyphs.append({**g, "grid": grid})
    return glyphs


def by_codepoint(glyphs):
    return {cp: g["grid"] for g in glyphs for cp in g["codepoints"]}
