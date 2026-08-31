#!/usr/bin/env python3
"""Merge a fixes fragment (from extract_fixes.py) into a pipeline build.

Replaces each fragment glyph's outline in the build and re-pins its
advance to the build's cell width (mono grid is law; the designer's lsb
is kept). Run AFTER mono_convert/gen_cv_ligatures, BEFORE hinting.

Usage: apply_fixes.py BUILD.ttf FRAGMENT.ttf
"""
import sys
from collections import Counter

from fontTools.ttLib import TTFont


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    build_path, frag_path = sys.argv[1:3]

    font = TTFont(build_path)
    frag = TTFont(frag_path)

    cell = Counter(font["hmtx"][g][0]
                   for g in font.getGlyphOrder()).most_common(1)[0][0]

    applied = 0
    for name in frag.getGlyphOrder():
        if name == ".notdef":
            continue
        if name not in font["glyf"].glyphs:
            print(f"  SKIP {name}: not in build (new glyphs unsupported)")
            continue
        font["glyf"][name] = frag["glyf"][name]
        _, lsb = frag["hmtx"][name]
        font["hmtx"].metrics[name] = (cell, lsb)
        print(f"  fixed {name} (adv pinned to {cell}, lsb {lsb})")
        applied += 1

    if not applied:
        print("nothing applied")
        return 1
    font.save(build_path)
    print(f"OK: {applied} fix(es) applied to {build_path} — now hint + gates")
    return 0


if __name__ == "__main__":
    main()
