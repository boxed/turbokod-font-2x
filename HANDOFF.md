# Handoff: a 16×32 pixel font in the spirit of Px437 IBM VGA 8×16

## Goal

Make a new **bitmap-style pixel font at double resolution** (16×32 cell
instead of 8×16). It should stay pixelated, crisp, and clean, and it should
keep the *feel* of the IBM VGA 8×16 font. It's for TurboKod (the Mojo Turbo
Vision port in `~/Projects/turbokod`), where the 8×16 font is the default
cell font.

A plain 2× nearest-neighbor upscale is *not* the goal, since that is just
the same font with bigger pixels. The point is to use the extra resolution:
diagonals and curves get smoother (O, S, @, digits, and the round parts of
a/b/d/e/g/p/q), there is room for finer detail, and stroke weight can be
tuned. The silhouettes, proportions, x-height, wide-and-friendly shapes, and
DOS character all have to stay recognizable.

## Source material

- `reference/Px437_IBM_VGA_8x16.ttf` is a copy of the font TurboKod ships
  (`turbokod/app/assets/`). It comes from VileR's **Oldschool PC Font Pack**
  (int10h.org). Its glyphs are outline squares on an 8×16 pixel grid. It is
  **CC BY-SA 4.0**, so a derivative has to keep attribution and use the same
  license.
- Coverage is CP437 (about 256 glyphs, mapped to Unicode). Box drawing,
  block elements (░▒▓█▀▄▌▐), and the shading glyphs matter a lot in TurboKod
  because the whole UI (window frames, scrollbars, shadows, menus) is drawn
  with them.

## Hard constraints (from how TurboKod renders)

- **Cell is exactly 16×32 px** at the design size, with a monospace advance.
  Every glyph's advance is half the em height.
- **Box drawing and block elements must tile seamlessly.** Lines run to the
  cell edges, single and double lines meet their neighbors at the same pixel
  rows and columns, and full blocks fill the whole cell with no gaps.
  Double-line spacing should look right at 2×. Shade patterns (░▒▓) should
  tile without visible seams.
- **No antialiasing is assumed.** At integer multiples of the design size
  TurboKod draws the font with antialiasing off, so pixels have to land on
  pixel boundaries exactly. Build outlines as unions of whole pixel squares
  on the grid (the same way Px437 does it), with no curves and no fractional
  coordinates.
- Keep CP437 coverage at minimum. Characters outside it (³, curly quotes,
  ellipsis, arrows, etc.) are a nice bonus, because TurboKod currently falls
  back to a system font for them.

## How TurboKod would consume it (for later, not this project)

`turbokod/app/swift/TurboKod.swift`:
- `loadCellFont` loads `Px437_IBM_VGA_8x16.ttf` from the bundle's Resources
  (copied there by `run_swift.sh`, line ~117).
- `BITMAP_FONT_DEFAULT_SIZE = 16` and `applyBundledCellFont` derive
  `CELL_W = size/2` and `CELL_H = size`. They treat sizes that are multiples
  of 16 as crisp (`cellFontIsBitmap`).
- A 16×32 font would have a 32px design size. Integrating it means either
  adding it as a second bundled option or making the design size a
  per-font value. Either way, the crisp path must use multiples of 32 for
  the new font.

TurboKod's terminal frontend doesn't use the font at all; the user's
terminal picks it.

## Suggested approach

1. **Tooling.** Python with `fontTools` (not installed yet, so use a venv
   or pixi in this project) to read the reference TTF and rasterize each
   glyph to an 8×16 bitmap. Store the glyphs in a simple editable text
   format, one file per glyph or one big file, using `.` and `#` rows.
   That format is the source of truth.
2. **Seed.** Generate a 16×32 starting point for each glyph. Nearest-
   neighbor 2× plus a pixel-art smoothing pass (EPX/Scale2x-style rules)
   is a good first draft that rounds corners and diagonals, and it is
   usually close to what a hand redraw wants.
3. **Hand-tune** the glyphs that matter most: letters, digits, and
   punctuation used in code (`{}[]()<>;:'"`,|/\_-=+*&^%$#@!~`). Box
   drawing and blocks should be *generated* from rules, not hand-drawn,
   so they tile.
4. **Build** a TTF from the bitmaps (pixel squares merged into outlines,
   correct `hmtx` / `hhea` / `OS/2` metrics, cmap matching the reference).
   Optionally also output BDF/PCF for terminal use.
5. **Preview tool.** Render a sample sheet to PNG with the 8×16 original
   and the new 16×32 font side by side (at 2× and 1× of the new one).
   Include a code sample, a TurboKod-style box-drawing window, and the
   full CP437 table. This is how the user will judge whether the "feel"
   survived, so make iterating on it fast.

## User preferences worth knowing

- US English spelling everywhere.
- Write temp/scratch files inside the project directory, never `/tmp`.
- Succinct commit messages that don't mention Claude.
- The user wants to *try* this, so get to a viewable preview early and
  iterate, rather than building the whole pipeline before showing
  anything.
