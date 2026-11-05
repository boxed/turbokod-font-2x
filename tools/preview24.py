"""Render out/preview24_full.png: a review sheet for the 12x24 (24 ppem) strike.

    python tools/preview24.py
"""
import os

from PIL import Image, ImageDraw

import preview as P
from fontdata import by_codepoint, load_glyphs
from project24 import project

BG = (40, 40, 48)
FG = (225, 225, 235)
MARGIN = 24


def grids():
    new = by_codepoint(load_glyphs())
    return new, {cp: project(g, cp) for cp, g in new.items()}


def screen(lines, cols=None, fg="W", bg="k"):
    s = P.Screen(cols or max(len(l) for l in lines), len(lines), fg, bg)
    for i, line in enumerate(lines):
        s.put(0, i, line)
    return s


def table_screen():
    s = P.Screen(32, 16, "W", "k")
    for i, cp in enumerate(P.cp437_codepoints()):
        s.put((i % 16) * 2, i // 16, [cp], "W", "k")
    return s


def sheet(sections):
    """sections: list of (title, image); stacked on one canvas."""
    height = MARGIN
    for _, img in sections:
        height += img.height + 48
    out = Image.new("RGB", (max(img.width for _, img in sections) + 2 * MARGIN, height), BG)
    draw = ImageDraw.Draw(out)
    y = MARGIN
    for title, img in sections:
        draw.text((MARGIN, y), title, fill=FG)
        out.paste(img, (MARGIN, y + 18))
        y += img.height + 48
    return out


def main():
    new, p24 = grids()
    sections = []

    letters = screen(["ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz", "0123456789 !\"#$%&'()*+,-./",
                      ":;<=>?@[\\]^_`{|}~ ½±°"])

    words = screen(["Hamburgefonstiv Quickly jumps", "The quick brown fox jumps over",
                    "the lazy dog. wizards vex NW", "bdpq hnmr aegs wWmM NZzk il1I|", "O0 oQ 5S 2Z 8B {x} [y] <z> a/b"])


    boxes = screen([
        "┌─┬─┐ ╔═╦═╗ ╒═╤═╕ ╓─╥─╖",
        "│ │ │ ║ ║ ║ │ │ │ ║ ║ ║",
        "├─┼─┤ ╠═╬═╣ ╞═╪═╡ ╟─╫─╢",
        "│ │ │ ║ ║ ║ │ │ │ ║ ║ ║",
        "└─┴─┘ ╚═╩═╝ ╘═╧═╛ ╙─╨─╜",
        "░░▒▒▓▓██ ▀▀▄▄ ▌▐▌▐ ■▬▲►▼◄",
    ], 28)


    # everything at 1x (real pixels)
    cps = sorted(p24)
    cols = 40
    allg = P.Screen(cols, -(-len(cps) // cols), "W", "k")
    for i, cp in enumerate(cps):
        allg.put(i % cols, i // cols, [cp], "W", "k")
    sections.append((f"1x: every glyph, {len(cps)} codepoints in codepoint order", allg.render(p24, 12, 24, 1)))
    sections.append(("1x: CP437 table", table_screen().render(p24, 12, 24, 1)))
    sections.append(("1x: code", P.code_screen().render(p24, 12, 24, 1)))
    sections.append(("1x: window", P.window_screen().render(p24, 12, 24, 1)))
    sections.append(("1x: powerline", P.powerline_screen().render(p24, 12, 24, 1)))
    sections.append(("1x: words", words.render(p24, 12, 24, 1)))

    os.makedirs("out", exist_ok=True)
    img = sheet(sections)
    img.save("out/preview24_full.png")
    print("out/preview24_full.png", img.size)


if __name__ == "__main__":
    main()
