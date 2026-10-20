"""Render a short text sample to out/sample.png: zoomed new, actual-size old vs new.

    python tools/sample.py "text to show" [zoom]
"""
import sys

from PIL import Image

from fontdata import load_reference, load_glyphs, by_codepoint
from preview import Screen


def main():
    text = sys.argv[1]
    zoom = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    s = Screen(len(text), 1, "W", "k")
    s.put(0, 0, text, "W", "k")
    new = by_codepoint(load_glyphs())
    parts = [s.render(new, 16, 32, zoom), s.render(load_reference(), 8, 16, 2), s.render(new, 16, 32, 1)]
    gap = 16
    img = Image.new("RGB", (max(p.width for p in parts) + 2 * gap, sum(p.height for p in parts) + gap * 4), (40, 40, 48))
    y = gap
    for p in parts:
        img.paste(p, (gap, y))
        y += p.height + gap
    img.save("out/sample.png")


if __name__ == "__main__":
    main()
