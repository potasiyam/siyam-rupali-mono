#!/usr/bin/env python3
"""Spacing report: shaped-advance width vs GCB grid width per font.

Two width notions collide in Windows Terminal:
  - shaped advance (HarfBuzz, what a shaping renderer draws/reserves)
  - GCB columns (what WT's grid charges: SpacingMark=1, Extend=0,
    Other=1, charged per codepoint, font-independent)
Delta = GCB columns - shaped advance cells = empty grid columns when
positive (the "merged glyph + empty column" effect). Pass -v to dump
glyph streams.
"""
import sys
from pathlib import Path

from vharfbuzz import Vharfbuzz
from fontTools.ttLib import TTFont

# Bengali GCB categories (Unicode GraphemeBreakProperty)
EXTEND = {0x0981, 0x09BC, 0x09C1, 0x09C2, 0x09C3, 0x09C4, 0x09CD}
SPACING = {0x09BE, 0x09BF, 0x09C0, 0x09C7, 0x09C8, 0x09CB, 0x09CC,
           0x09D7}


def gcb_columns(text):
    n = 0
    for ch in text:
        cp = ord(ch)
        if cp in EXTEND:
            continue
        n += 1  # SpacingMark and Other both charge 1 in WT
    return n


def analyze(font_path, text):
    tt = TTFont(font_path)
    cell = tt["hhea"].advanceWidthMax
    vhb = Vharfbuzz(font_path)
    buf = vhb.shape(text, {"script": "beng", "language": "ben"})
    names = [vhb.hbfont.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    adv = sum(p.x_advance for p in buf.glyph_positions)
    shaped_cells = adv / cell
    grid = gcb_columns(text)
    glyphs = " ".join(names)
    return shaped_cells, grid, glyphs, cell


def main():
    here = Path(__file__).parent.parent
    lf = Path("C:/Users/Siyam/AppData/Local/Microsoft/Windows/Fonts")
    fonts = [
        ("WT8 (no ligatures)", here / "build/SiyamRupaliMono-WT8.ttf", 1404),
        ("Two (universal 0.0.8)", lf / "SiyamRupaliMono-Two.ttf", 1404),
        ("Edit 0.0.1", lf / "SiyamRupaliMono-Edit.ttf", 1536),
        ("Wide 0.0.1", lf / "SiyamRupaliMono-Wide-Alpha.ttf", 1536),
        ("original 1.070", here / "legacy/base-1.070ship.ttf", None),
    ]
    text = ("\u0995\u09bf\u0982\u0995\u09b0\u09cd\u09a4\u09ac\u09cd\u09af"
            "\u09ac\u09bf\u09ae\u09c1\u09a2\u09bc \u09ac\u09bf "
            "\u09ac\u09bf")
    print(f"string: {text!r}")
    print(f"GCB grid columns (WT charges, font-independent): "
          f"{gcb_columns(text)}")
    print()
    print(f"{'font':24} {'cell':>6} {'shaped':>7} {'grid':>5} {'delta':>6}")
    for label, path, _ in fonts:
        if not path.exists():
            print(f"{label:24} MISSING: {path}")
            continue
        shaped, grid, glyphs, cell = analyze(str(path), text)
        print(f"{label:24} {cell:>6} {shaped:>7.2f} {grid:>5} "
              f"{grid - shaped:>+6.2f}")
        if "-v" in sys.argv:
            print(f"    glyphs: {glyphs}")


if __name__ == "__main__":
    main()
