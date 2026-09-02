#!/usr/bin/env python3
"""Spacing report: shaped-advance width vs reference grid width per font.

Two width notions collide in Windows Terminal:
  - shaped advance (HarfBuzz, what a shaping renderer draws/reserves)
  - grid columns (what a terminal reserves for the line)
Reference grid model (author directive 2026-09-03): Extend = 0; a
spacing mark charges 1 after a non-mark and collapses to 0 inside a
mark run (measured: ko = e+aa grants 1, probe table in
docs/SPACING_REPORT.md); anusvara/visarga charge 1 ALWAYS (author:
"ং should be 1" — they carry a full advance in the font; WT 1.24's
measured collapse-to-0 for ং is a terminal-side undercharge).
Delta = grid - shaped advance cells = empty grid columns when
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
FULL_MARKS = {0x0982, 0x0983}  # anusvara/visarga: charge 1 always


def gcb_columns(text):
    n = 0
    prev_mark = False
    for ch in text:
        cp = ord(ch)
        if cp in EXTEND:
            prev_mark = True
            continue
        if cp in FULL_MARKS:
            n += 1  # author directive: full advance -> full column
        elif cp in SPACING:
            if not prev_mark:  # mark runs collapse to one column
                n += 1
        else:
            n += 1  # bases and everything else
        prev_mark = cp in EXTEND or cp in FULL_MARKS or cp in SPACING
    return n


def analyze(font_path, text, declared_cell=None):
    tt = TTFont(font_path)
    cell = declared_cell or tt["head"].unitsPerEm
    vhb = Vharfbuzz(font_path)
    buf = vhb.shape(text, {"script": "beng", "language": "ben"})
    names = [vhb.hbfont.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    adv = sum(p.x_advance for p in buf.glyph_positions)
    shaped_cells = adv / cell
    grid = gcb_columns(text)
    glyphs = " ".join(names)
    return shaped_cells, grid, glyphs, cell


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
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
    print(f"reference grid columns (author model; WT quirks measured "
          f"in docs/SPACING_REPORT.md): {gcb_columns(text)}")
    print()
    print(f"{'font':24} {'cell':>6} {'shaped':>7} {'grid':>5} {'delta':>6}")
    for label, path, declared in fonts:
        if not path.exists():
            print(f"{label:24} MISSING: {path}")
            continue
        shaped, grid, glyphs, cell = analyze(str(path), text, declared)
        print(f"{label:24} {cell:>6} {shaped:>7.2f} {grid:>5} "
              f"{grid - shaped:>+6.2f}")
        if "-v" in sys.argv:
            print(f"    glyphs: {glyphs}")


if __name__ == "__main__":
    main()
