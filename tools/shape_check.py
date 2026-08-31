#!/usr/bin/env python3
"""Per-cluster shaping check for the mono conversion.

Shapes each test string (one grapheme cluster per line) and reports every
output glyph's advance and offset. The terminal-relevant number is the
TOTAL advance of the cluster: 1 cell = 1024 units at upem 2048. Anything
above 1 cell means the cluster overflows the wcwidth grid.

Usage: shape_check.py font.ttf [--cell N]
"""
import argparse
import sys

from vharfbuzz import Vharfbuzz

CLUSTERS = [
    "ক", "খ", "A", "a", "0", "7", " ", ".",
    "কি", "কী", "কু", "কূ", "কৃ", "কে", "কৈ", "কো", "কৌ",
    "র্ক", "র্খ", "ক্র", "ক্ষ", "ক্ষ্ম", "জ্ঞ", "ন্দ্র", "স্ত্র",
    "প্ল", "শ্র", "হ্ম", "ঙ্গ", "ক্ত", "ম্প", "ক্ট",
    "গ্ল", "দ্ভ", "ক্ষ্ণ", "স্ক্র", "ত্ত্ব",
    "ং", "ঃ", "ঁ",
]

# Context regression: mid-word ে/ৈ (init feature NOT applied) must still
# ligate via the _std rules. 2026-08-31 bug: only bn_initekaar/bn_initaikaar
# were covered, so ইউকে rendered as two cells while কে was one.
CONTEXT_RULES = [
    ("ইউকে", "bn_ka_ekaar_std"),
    ("ইউকি", "bn_ka_ikaar"),
    ("ইউকো", "bn_ka_okaar_std"),
    ("ইউকৌ", "bn_ka_aukaar_std"),
    ("কে", "bn_ka_ekaar"),
    ("কো", "bn_ka_okaar"),
]


def matrix_clusters():
    """All consonant x spacing-matra combos, as unicode cluster strings."""
    consonants = [
        "ক", "খ", "গ", "ঘ", "ঙ", "চ", "ছ", "জ", "ঝ", "ঞ",
        "ট", "ঠ", "ড", "ড়", "ঢ", "ঢ়", "ণ", "ত", "থ", "দ",
        "ধ", "ন", "প", "ফ", "ব", "ভ", "ম", "য", "য়", "র",
        "ল", "শ", "ষ", "স", "হ", "ৎ",
    ]
    matras = "\u09bf\u09c0\u09c7\u09c8\u09cb\u09cc\u09be"
    return [c + m for c in consonants for m in matras]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--max-cells", type=float, default=1.0,
                    help="allowed cluster width in cells (2.0 for the "
                         "WideCV build; strict gate stays 1.0)")
    ap.add_argument("--context", action="store_true",
                    help="also assert init-variant ligature coverage "
                         "(terminal builds with CV ligatures only; the "
                         "ligature-free Edit build must NOT pass this)")
    ap.add_argument("--matrix", action="store_true",
                    help="check all consonant x matra combos")
    args = ap.parse_args()

    vhb = Vharfbuzz(args.font)
    upm = vhb.hbfont.face.upem
    cell = args.cell or upm // 2
    feats = {"script": "beng", "language": "ben"}

    bad = 0
    tests = matrix_clusters() if args.matrix else CLUSTERS
    quiet = args.matrix
    for text in tests:
        buf = vhb.shape(text, feats)
        glyphs = []
        total = 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = vhb.hbfont.glyph_to_string(info.codepoint)
            glyphs.append(f"{name}[{pos.x_advance}@{pos.x_offset}]")
            total += pos.x_advance
        cells = total / cell
        flag = ""
        if total > cell * args.max_cells + 8:  # small tolerance
            flag = "  <-- OVERFLOW"
            bad += 1
        if not quiet or flag:
            print(f"{text!r:12} total={total:5} ({cells:.2f} cell) "
                  f"{' '.join(glyphs)}{flag}")

    for text, want in (CONTEXT_RULES if args.context else []):
        buf = vhb.shape(text, feats)
        names = [vhb.hbfont.glyph_to_string(i.codepoint)
                 for i in buf.glyph_infos]
        if want not in names:
            bad += 1
            print(f"CONTEXT FAIL {text!r}: want {want} in {names}")

    print(f"\n{bad} failure(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
