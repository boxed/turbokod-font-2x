"""Powerline glyphs (U+E0A0-U+E0A2, U+E0B0-U+E0B3) and the Nerd Fonts
extra separators (U+E0B4-U+E0BF: half circles and slants).

The separators are generated so they fill the whole cell height and meet a
full block with no seam: the solid arrow grows 1px per row to the full cell
width at mid height, the thin arrow is the outer edge of the solid one. The
half circle is a disc of radius w centered on the left edge. The slant
triangles step 1px every 2 rows and are each other's exact complement, so
a lower-left and an upper-right one with swapped colors tile. The
icons are hand-drawn in glyphs/powerline16x32.txt and glyphs/powerline8x16.txt
(the latter goes into the 16px bitmap strike).
"""
from glyphfile import read_glyphs, to_grid


def arrow(w, h, solid, thickness):
    """Right-pointing arrow filling a w x h cell."""
    grid = []
    for y in range(h):
        reach = min(y, h - 1 - y) * 2 * w // h + 1
        start = 0 if solid else max(0, reach - thickness)
        grid.append([start <= x < reach for x in range(w)])
    return grid


def half_circle(w, h, solid, thickness):
    """Right half of a disc of radius w centered on the left edge at mid height."""
    inner = 0 if solid else (w - thickness) ** 2
    return [[inner < (x + 0.5) ** 2 + (y + 0.5 - h / 2) ** 2 <= w * w for x in range(w)] for y in range(h)]


def slant(w, h, solid, thickness):
    """Lower-left triangle (solid) or its hypotenuse, from the top-left to the bottom-right corner."""
    if solid:
        return [[x < (y + 1) * w // h for x in range(w)] for y in range(h)]
    return [[(y - thickness + 1) * w // h <= x <= (y + thickness - 1) * w // h for x in range(w)]
            for y in range(h)]


def mirror(grid):
    return [row[::-1] for row in grid]


def flip(grid):
    return grid[::-1]


def separators(w, h, thickness):
    right, thin = arrow(w, h, True, thickness), arrow(w, h, False, thickness)
    disc, ring = half_circle(w, h, True, thickness), half_circle(w, h, False, thickness)
    lower_left, backslash = slant(w, h, True, thickness), slant(w, h, False, thickness)
    return {
        0xE0B0: right, 0xE0B1: thin, 0xE0B2: mirror(right), 0xE0B3: mirror(thin),
        0xE0B4: disc, 0xE0B5: ring, 0xE0B6: mirror(disc), 0xE0B7: mirror(ring),
        0xE0B8: lower_left, 0xE0B9: backslash, 0xE0BA: mirror(lower_left), 0xE0BB: mirror(backslash),
        0xE0BC: flip(lower_left), 0xE0BD: mirror(backslash),
        0xE0BE: mirror(flip(lower_left)), 0xE0BF: backslash,
    }


def load(path, w, h, thickness):
    """List of {name, codepoints, grid} for one size."""
    glyphs = [{"name": g["name"], "codepoints": g["codepoints"], "grid": to_grid(g["rows"])}
              for g in read_glyphs(path)]
    glyphs += [{"name": f"uni{cp:04X}", "codepoints": [cp], "grid": grid}
               for cp, grid in separators(w, h, thickness).items()]
    for g in glyphs:
        assert len(g["grid"]) == h and all(len(r) == w for r in g["grid"]), f"{g['name']}: bad size"
    return glyphs


def load_16x32():
    return load("glyphs/powerline16x32.txt", 16, 32, 2)


def load_8x16():
    return load("glyphs/powerline8x16.txt", 8, 16, 1)
