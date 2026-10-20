"""Plain-text glyph format.

Each glyph is a header line followed by rows of '.' (off) and '#' (on):

    glyph A U+0041
    ................
    ...

Multiple codepoints may follow the name. Blank lines and lines starting with
';' between glyphs are ignored.
"""


def read_glyphs(path):
    glyphs = []
    current = None
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("glyph "):
                parts = line.split()
                current = {
                    "name": parts[1],
                    "codepoints": [int(p[2:], 16) for p in parts[2:]],
                    "rows": [],
                }
                glyphs.append(current)
            elif not line.strip() or line.startswith(";"):
                continue
            else:
                current["rows"].append(line)
    return glyphs


def write_glyphs(path, glyphs):
    with open(path, "w") as f:
        for g in glyphs:
            cps = " ".join(f"U+{cp:04X}" for cp in g["codepoints"])
            f.write(f"glyph {g['name']} {cps}\n")
            for row in g["rows"]:
                f.write(row + "\n")
            f.write("\n")


def to_grid(rows):
    return [[c == "#" for c in row] for row in rows]


def to_rows(grid):
    return ["".join("#" if v else "." for v in row) for row in grid]
