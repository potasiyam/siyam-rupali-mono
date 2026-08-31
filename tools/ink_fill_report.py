#!/usr/bin/env python3
"""Ink-width distribution of CV ligature glyphs vs cell (raggedness report)."""
import sys
from collections import defaultdict

from fontTools.ttLib import TTFont
from mono_convert import glyph_bbox

font = TTFont(sys.argv[1] if len(sys.argv) > 1 else
              "build/SiyamRupaliMono-Wide.ttf")
cell = font["hhea"].advanceWidthMax
glyf = font["glyf"]
cache = {}

SUFFIXES = ("_aakaar", "_ikaar", "_iikaar", "_ekaar", "_aikaar",
            "_okaar", "_aukaar")

rows = []
for name in font.getGlyphOrder():
    if not name.startswith("bn_"):
        continue
    if not any(name.endswith(s) or name.endswith(s + "_std")
               for s in SUFFIXES):
        continue
    bb = glyph_bbox(glyf, name, cache)
    if bb is None:
        continue
    w = bb[2] - bb[0]
    rows.append((w / cell, name))

rows.sort()
fills = [r[0] for r in rows]
n = len(fills)
print(f"{n} ligature glyphs, cell={cell}")
print(f"ink fill: min={fills[0]:.2f} p10={fills[n//10]:.2f} "
      f"p25={fills[n//4]:.2f} median={fills[n//2]:.2f} "
      f"p75={fills[3*n//4]:.2f} p90={fills[9*n//10]:.2f} max={fills[-1]:.2f}")

by_decile = defaultdict(int)
for f in fills:
    by_decile[round(f, 1)] += 1
for d in sorted(by_decile):
    print(f"  {d:.1f}: {'#' * by_decile[d]} ({by_decile[d]})")

print("\nnarrowest 12 (floaters, biggest side gaps):")
for f, name in rows[:12]:
    print(f"  {f:.2f}  {name}")
print("widest 6:")
for f, name in rows[-6:]:
    print(f"  {f:.2f}  {name}")

# the ka-* family specifically (the user's test line)
print("\nka family (user test line):")
for f, name in rows:
    if name.startswith("bn_ka_"):
        print(f"  {f:.2f}  {name}")
