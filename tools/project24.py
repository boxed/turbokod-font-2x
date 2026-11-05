"""Project the 16x32 glyphs onto a 12x24 grid (3/4 scale) for a 24 ppem strike.

Run-based and separable: every horizontal run of on-pixels is mapped by
rounding its two edges (so a 4px stroke is always exactly 3px, whatever its
phase), then the same is done to vertical runs.
"""
import os

from fontdata import load_glyphs

HAND = "glyphs/hand12x24.txt"
# Hand-drawn glyph files, merged in order (later files win). Each group of glyphs has its own file.
HAND_FILES = ["glyphs/hand12x24.txt", "glyphs/latin12x24.txt", "glyphs/greek12x24.txt",
              "glyphs/symbols12x24.txt"]

SRC_W, SRC_H, DST_W, DST_H = 16, 32, 12, 24


def _map(i):
    return (3 * i + 2) // 4  # round(0.75 * i), halves up


def _runs(line):
    start = None
    for i, v in enumerate(list(line) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            yield start, i
            start = None


def _squeeze(line, size):
    out = [False] * size
    for a, b in _runs(line):
        a2, b2 = _map(a), _map(b)
        if b2 == a2:  # keep thin features alive
            b2 = a2 + 1
        for i in range(a2, min(b2, size)):
            out[i] = True
    return out


def shade(cp):
    """Regular dither for the shade blocks so they tile at any cell position."""
    if cp == 0x2592:
        return [[(x + y) % 2 == 0 for x in range(DST_W)] for y in range(DST_H)]
    on = cp == 0x2591
    return [[((x + 2 * (y % 2)) % 4 == 0) == on for x in range(DST_W)] for y in range(DST_H)]


def load_hand(path=HAND):
    """codepoint -> 12x24 grid, from glyphs/hand12x24.txt ('glyph U+XXXX top=N' + rows)."""
    out = {}
    if not os.path.exists(path):
        return out
    cp = top = None
    rows = []

    def flush():
        if cp is None:
            return
        assert top + len(rows) <= DST_H, f"U+{cp:04X}: too tall"
        grid = [[False] * DST_W for _ in range(DST_H)]
        for i, row in enumerate(rows):
            assert len(row) == DST_W, f"U+{cp:04X} row {i}: width {len(row)}"
            grid[top + i] = [c == "#" for c in row]
        out[cp] = grid

    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("#") and not line.startswith("# ") and False:
            continue
        if line.startswith("glyph "):
            flush()
            _, name, t = line.split()
            cp, top, rows = int(name[2:], 16), int(t[4:]), []
        elif line and not line.startswith("# ") and cp is not None:
            rows.append(line)
    flush()
    return out


_HAND = None


def _hand():
    global _HAND
    if _HAND is None:
        _HAND = {}
        for path in HAND_FILES:
            _HAND.update(load_hand(path))
    return _HAND


# accents: rows of 12 chars, placed at row `top` of the 24-row cell
ACCENTS_CAP = {  # two rows, rows 0-1, one blank row above the cap line (row 3)
    "acute": (0, ["......##....", "....##......"]),
    "grave": (0, ["....##......", "......##...."]),
    "circ": (0, ["....####....", "...##..##..."]),
    "diaer": (0, ["...##..##...", "...##..##..."]),
    "tilde": (0, ["...##..#....", "..#..##....."]),
    "ring": (0, [".....##.....", "....#..#....", ".....##....."]),
}
ACCENTS_LOW = {  # three rows, rows 4-6, one blank row above the x-height (row 8)
    "acute": (4, ["......##....", ".....##.....", "....##......"]),
    "grave": (4, ["....##......", ".....##.....", "......##...."]),
    "circ": (4, [".....##.....", "....####....", "...##..##..."]),
    "diaer": (5, ["...##..##...", "...##..##..."]),
    "tilde": (5, ["...##..#....", "..#..##....."]),
    "ring": (4, [".....##.....", "....#..#....", ".....##....."]),
}
CEDILLA = (18, [".....##.....", "......##....", "....###....."])

# codepoint -> (base, accent, table)
COMPOSE = {}
for _cp, _base, _acc in [
    (0xC4, "A", "diaer"), (0xC5, "A", "ring"), (0xC7, "C", "cedil"), (0xC9, "E", "acute"),
    (0xD1, "N", "tilde"), (0xD6, "O", "diaer"), (0xDC, "U", "diaer"),
    (0xE0, "a", "grave"), (0xE1, "a", "acute"), (0xE2, "a", "circ"), (0xE4, "a", "diaer"),
    (0xE5, "a", "ring"), (0xE7, "c", "cedil"), (0xE8, "e", "grave"), (0xE9, "e", "acute"),
    (0xEA, "e", "circ"), (0xEB, "e", "diaer"), (0xEC, "\u0131", "grave"), (0xED, "\u0131", "acute"),
    (0xEE, "\u0131", "circ"), (0xEF, "\u0131", "diaer"), (0xF1, "n", "tilde"),
    (0xF2, "o", "grave"), (0xF3, "o", "acute"), (0xF4, "o", "circ"), (0xF6, "o", "diaer"),
    (0xF9, "u", "grave"), (0xFA, "u", "acute"), (0xFB, "u", "circ"), (0xFC, "u", "diaer"),
    (0xFF, "y", "diaer"),
]:
    COMPOSE[_cp] = (_base, _acc)


def compose(cp):
    base, acc = COMPOSE[cp]
    if base == "\u0131":  # dotless i: the hand 'i' without its dot
        grid = [row[:] for row in _hand()[ord("i")]]
        for y in range(3, 6):
            grid[y] = [False] * DST_W
    else:
        grid = [row[:] for row in _hand()[ord(base)]]
    if acc == "cedil":
        top, rows = CEDILLA
    else:
        top, rows = (ACCENTS_CAP if base.isupper() else ACCENTS_LOW)[acc]
    for i, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#":
                grid[top + i][x] = True
    return grid


# Box drawing: the original puts the single horizontal on the lower stroke of the double one
# (source rows 14-15; double strokes are 10-11 and 14-15), so rows are picked, not squeezed.
DOUBLE_H = {0x2550, 0x2552, 0x2554, 0x2555, 0x2557, 0x2558, 0x255A, 0x255B, 0x255D, 0x255E,
            0x2560, 0x2561, 0x2563, 0x2564, 0x2566, 0x2567, 0x2569, 0x256A, 0x256C}
ROWS_DOUBLE = [0] * 9 + [10, 11, 12, 13, 14, 15] + [16] * 9   # strokes at rows 9-10 and 13-14
ROWS_SINGLE = [0] * 11 + [14, 15] + [16] * 11                 # stroke at rows 11-12


def box(grid, cp):
    rows = [_squeeze(r, DST_W) for r in grid]
    return [rows[y] for y in (ROWS_DOUBLE if cp in DOUBLE_H else ROWS_SINGLE)]


def project(grid, cp=None):
    if cp is not None and 0xE0A0 <= cp <= 0xE0BF:
        import powerline24
        return powerline24.load_12x24()[cp]
    hand = _hand()
    if cp in hand:
        return hand[cp]
    if cp in COMPOSE:
        return compose(cp)
    if cp is not None and 0x2500 <= cp <= 0x256C:
        return box(grid, cp)
    if cp in (0x2591, 0x2592, 0x2593):
        return shade(cp)
    rows = [_squeeze(r, DST_W) for r in grid]
    cols = [_squeeze([rows[y][x] for y in range(SRC_H)], DST_H) for x in range(DST_W)]
    return [[cols[x][y] for x in range(DST_W)] for y in range(DST_H)]


def project_all():
    return {g["name"]: {**g, "grid24": project(g["grid"])} for g in load_glyphs()}
