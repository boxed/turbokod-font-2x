"""Render out/preview.png comparing the 8x16 reference with the 16x32 font."""
import os

from PIL import Image

from fontdata import load_reference, load_glyphs, by_codepoint

# VGA text-mode palette
PAL = {
    "k": (0, 0, 0), "b": (0, 0, 170), "g": (0, 170, 0), "c": (0, 170, 170),
    "r": (170, 0, 0), "m": (170, 0, 170), "y": (170, 85, 0), "w": (170, 170, 170),
    "K": (85, 85, 85), "B": (85, 85, 255), "G": (85, 255, 85), "C": (85, 255, 255),
    "R": (255, 85, 85), "M": (255, 85, 255), "Y": (255, 255, 85), "W": (255, 255, 255),
}

CODE = [
    "def scan(text: String) -> List[Token]:",
    "    var out = List[Token]()",
    "    var i = 0  # cursor",
    "    while i < len(text):",
    "        c = text[i]",
    "        if c == '{' or c == '}':",
    "            out.append(Token(c, i))",
    '        elif c in "[]()<>;:,":',
    "            out.append(Token(c, i))",
    "        x = (a * 3 + b) / 2 - 1 % 7",
    '        s = "~`!@#$%^&*_|\\\\?"',
    "        i += 1",
    "    return out^",
    "",
    "The quick brown fox jumps over",
    "the lazy dog. 0123456789 OIl1|",
    "Größe Ångström Façade Niño ½ ±",
]


def cp437_codepoints():
    cps = list(range(32))  # the reference maps the CP437 graphic glyphs here
    cps += list(range(32, 128))
    cps += [ord(bytes([b]).decode("cp437")) for b in range(128, 256)]
    return cps


class Screen:
    def __init__(self, cols, rows, fg="w", bg="k"):
        self.cols, self.rows = cols, rows
        self.cells = [[(32, fg, bg) for _ in range(cols)] for _ in range(rows)]

    def put(self, x, y, text, fg="w", bg="k"):
        for i, ch in enumerate(text):
            cp = ch if isinstance(ch, int) else ord(ch)
            if 0 <= x + i < self.cols and 0 <= y < self.rows:
                self.cells[y][x + i] = (cp, fg, bg)

    def fill(self, x0, y0, x1, y1, ch, fg, bg):
        for y in range(y0, y1):
            self.put(x0, y, ch * (x1 - x0), fg, bg)

    def recolor(self, x0, y0, x1, y1, fg, bg):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if 0 <= x < self.cols and 0 <= y < self.rows:
                    self.cells[y][x] = (self.cells[y][x][0], fg, bg)

    def render(self, glyphs, cw, ch, scale):
        img = Image.new("RGB", (self.cols * cw * scale, self.rows * ch * scale))
        px = img.load()
        for row in range(self.rows):
            for col in range(self.cols):
                cp, fg, bg = self.cells[row][col]
                grid = glyphs.get(cp) or glyphs[ord("?")]
                for gy in range(ch):
                    for gx in range(cw):
                        color = PAL[fg] if grid[gy][gx] else PAL[bg]
                        bx, by = (col * cw + gx) * scale, (row * ch + gy) * scale
                        for dy in range(scale):
                            for dx in range(scale):
                                px[bx + dx, by + dy] = color
        return img


def code_screen():
    s = Screen(40, len(CODE) + 2, "W", "k")
    for i, line in enumerate(CODE):
        s.put(1, i + 1, line, "Y" if i < 13 else "W", "k")
    return s


def window_screen():
    s = Screen(40, 18, "b", "b")
    s.fill(0, 1, 40, 17, "░", "b", "w")
    s.fill(0, 0, 40, 1, " ", "k", "w")
    s.put(1, 0, " File  Edit  Search  Run  Window ", "k", "w")
    s.recolor(2, 0, 3, 1, "r", "w")
    s.recolor(8, 0, 9, 1, "r", "w")
    s.put(0, 17, " F1 Help │ F2 Save │ F10 Menu       ", "k", "w")
    x0, y0, x1, y1 = 2, 2, 35, 14
    s.fill(x0, y0, x1, y1, " ", "W", "b")
    s.put(x0, y0, "╔" + "═" * (x1 - x0 - 2) + "╗", "W", "b")
    s.put(x0 + 3, y0, "[■]", "W", "b")
    s.put(x0 + 11, y0, " main.mojo ", "W", "b")
    s.put(x1 - 5, y0, "[↕]", "W", "b")
    for y in range(y0 + 1, y1 - 1):
        s.put(x0, y, "║", "W", "b")
        s.put(x1 - 1, y, "▒", "b", "c")
    s.put(x1 - 1, y0 + 1, "▲", "b", "c")
    s.put(x1 - 1, y0 + 3, "■", "b", "c")
    s.put(x1 - 1, y1 - 2, "▼", "b", "c")
    s.put(x0, y1 - 1, "╚══ 1:1 " + "═" * 6, "W", "b")
    s.put(x0 + 16, y1 - 1, "░" * 6 + "■" + "▒" * 8 + "┘", "b", "c")
    lines = ["fn main():", "    print(\"Hello, VGA\")", "    let x = 42", "",
             "┌──┬──┐ ╔═╦╗ ╒╤╕ ╓╥╖",
             "├──┼──┤ ╠═╬╣ ╞╪╡ ╟╫╢",
             "└──┴──┘ ╚═╩╝ ╘╧╛ ╙╨╜",
             "█▓▒░ ▀▄▌▐ ■▬ ☺☻♥♦♣♠"]
    for i, line in enumerate(lines):
        s.put(x0 + 2, y0 + 1 + i, line, "Y" if i < 3 else "W", "b")
    # dialog with shadow
    dx0, dy0, dx1, dy1 = 20, 8, 38, 14
    s.recolor(dx0 + 2, dy1, dx1 + 2, dy1 + 1, "K", "k")
    s.recolor(dx1, dy0 + 1, dx1 + 2, dy1, "K", "k")
    s.fill(dx0, dy0, dx1, dy1, " ", "k", "w")
    s.put(dx0, dy0, "┌" + "─" * (dx1 - dx0 - 2) + "┐", "W", "w")
    for y in range(dy0 + 1, dy1 - 1):
        s.put(dx0, y, "│", "W", "w")
        s.put(dx1 - 1, y, "│", "W", "w")
    s.put(dx0, dy1 - 1, "└" + "─" * (dx1 - dx0 - 2) + "┘", "W", "w")
    s.put(dx0 + 5, dy0, " Save? ", "W", "w")
    s.put(dx0 + 2, dy0 + 2, " Yes ▄", "W", "g")
    s.recolor(dx0 + 7, dy0 + 2, dx0 + 8, dy0 + 3, "k", "w")
    s.put(dx0 + 3, dy0 + 3, "▀▀▀▀▀", "k", "w")
    s.put(dx0 + 10, dy0 + 2, " No ▄", "k", "g")
    s.recolor(dx0 + 14, dy0 + 2, dx0 + 15, dy0 + 3, "k", "w")
    s.put(dx0 + 11, dy0 + 3, "▀▀▀▀", "k", "w")
    return s


def table_screen():
    s = Screen(32, 16, "W", "k")
    cps = cp437_codepoints()
    for i, cp in enumerate(cps):
        s.put((i % 16) * 2, i // 16, [cp], "W", "k")
    return s


ZOOM_LINES = [
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789 {}[]()<>;:'\"`,.",
    "|/\\_-=+*&^%$#@!~? åäöÅÄÖéüß½",
]


def zoom_screen():
    s = Screen(max(len(l) for l in ZOOM_LINES), len(ZOOM_LINES), "W", "k")
    for i, line in enumerate(ZOOM_LINES):
        s.put(0, i, line, "W", "k")
    return s


def main():
    ref = load_reference()
    new = by_codepoint(load_glyphs())
    gap = 24
    bg = (40, 40, 48)

    def pair(screen):
        a = screen.render(ref, 8, 16, 2)
        b = screen.render(new, 16, 32, 1)
        img = Image.new("RGB", (a.width + gap + b.width, a.height), bg)
        img.paste(a, (0, 0))
        img.paste(b, (a.width + gap, 0))
        return img

    blocks = [pair(code_screen()), pair(window_screen()), pair(table_screen())]
    z = zoom_screen()
    for i in range(z.rows):
        line = Screen(z.cols, 1)
        line.cells = [z.cells[i]]
        blocks.append(line.render(ref, 8, 16, 4))
        blocks.append(line.render(new, 16, 32, 2))
    width = max(b.width for b in blocks) + 2 * gap
    height = sum(b.height for b in blocks) + gap * (len(blocks) + 1)
    sheet = Image.new("RGB", (width, height), bg)
    y = gap
    for b in blocks:
        sheet.paste(b, (gap, y))
        y += b.height + gap
    os.makedirs("out", exist_ok=True)
    sheet.save("out/preview.png")
    print(f"out/preview.png {sheet.size}")


if __name__ == "__main__":
    main()
