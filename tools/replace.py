"""Add or replace hand-drawn glyphs in glyphs/hand16x32.txt.

    python tools/replace.py patch.txt

The patch uses the glyph file format; codepoints on the header may be
omitted (they are taken from the generated glyph of the same name).
Hand-drawn glyphs override glyphs/font16x32.txt, which seed.py regenerates.
"""
import os
import sys

from glyphfile import read_glyphs, write_glyphs

HAND = "glyphs/hand16x32.txt"
AUTO = "glyphs/font16x32.txt"


def main():
    hand = read_glyphs(HAND) if os.path.exists(HAND) else []
    index = {g["name"]: g for g in hand}
    auto = {g["name"]: g for g in read_glyphs(AUTO)}
    for patch in read_glyphs(sys.argv[1]):
        rows = patch["rows"]
        assert len(rows) == 32 and all(len(r) == 16 for r in rows), f"{patch['name']}: bad size"
        name = patch["name"]
        if name in index:
            index[name]["rows"] = rows
        else:
            g = {"name": name, "codepoints": patch["codepoints"] or auto[name]["codepoints"], "rows": rows}
            hand.append(g)
            index[name] = g
        print(f"set {name}")
    hand.sort(key=lambda g: g["codepoints"][0])
    write_glyphs(HAND, hand)


if __name__ == "__main__":
    main()
