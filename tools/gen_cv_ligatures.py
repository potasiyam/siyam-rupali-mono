#!/usr/bin/env python3
"""Generate CV ligatures so spacing-matra syllables fit ONE terminal cell.

Problem: the seven spacing matras (ি ী ে ৈ ো ৌ া) each carry their own
advance, so কি = 2 cells and কো = 3 cells while a terminal grants every
Bengali cluster exactly 1 cell (wcwidth). This tool composes base+matra
art (from the ORIGINAL proportional font) into single 1024-unit ligature
glyphs and adds GSUB ligature rules that consume the reordered stream
(e.g. কি shapes to [bn_ikaar, bn_ka] -> sub bn_ikaar bn_ka by bn_ka_ikaar).

Layout inside the cell (ink budget 942 = 0.92 * 1024):
  2-part, post matra (B+া, B+ী): base [0..565], matra [602..942]
  2-part, pre matra  (ি+B, ে+B, ৈ+B): matra [0..340], base [377..942]
  3-part (ো, ৌ): pre [0..230], base [267..675], post [712..942]

v1 scope: bare consonant bases only. Conjunct + matra (e.g. র্কি) keeps
the 2-cell overflow and is the documented v2 work item.

Usage: gen_cv_ligatures.py ORIGINAL.ttf CONVERTED.ttf OUT.ttf [--smoke]
"""
import argparse
import sys
from pathlib import Path

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from mono_convert import RoundingPen, draw_decomposed, glyph_bbox

CELL = 1024

# matra stream patterns: (suffix, pre glyph, post glyph)
PATTERNS = [
    ("ikaar", "bn_ikaar", None),
    ("iikaar", None, "bn_iikaar"),
    ("ekaar", "bn_initekaar", None),
    ("aikaar", "bn_initaikaar", None),
    ("aakaar", None, "bn_aakaar"),
    ("okaar", "bn_initekaar", "bn_aakaar"),
    ("aukaar", "bn_initekaar", "bn_aumark"),  # measured: ৌ pre-part = ে's
]

# ink regions per part within [0, 942]
REGIONS = {
    2: {"pre": (0, 340), "base": (377, 942), "post_base": (0, 565),
        "post": (602, 942)},
    3: {"pre": (0, 230), "base": (267, 675), "post": (712, 942)},
}

CONSONANT_GLYPHS = [
    "bn_ka", "bn_kha", "bn_ga", "bn_gha", "bn_nga", "bn_ca", "bn_cha",
    "bn_ja", "bn_jha", "bn_nya", "bn_tta", "bn_ttha", "bn_dda", "bn_ddha",
    "bn_nna", "bn_ta", "bn_tha", "bn_da", "bn_dha", "bn_na", "bn_pa",
    "bn_pha", "bn_ba", "bn_bha", "bn_ma", "bn_ya", "bn_ra", "bn_la",
    "bn_sha", "bn_ssa", "bn_sa", "bn_ha", "bn_half_ta", "bn_rra",
    "bn_rha", "bn_yya",
]


def part_transform(glyf, name, region, bbox_cache):
    """(sx, dx) mapping glyph ink into [region_start, region_end]."""
    x0, _, x1, _ = glyph_bbox(glyf, name, bbox_cache)
    r0, r1 = region
    sx = min(1.0, (r1 - r0) / (x1 - x0))
    dx = r0 - sx * x0
    return sx, dx


def build_ligature(orig, parts, bbox_cache):
    """parts = [(glyph_name, (sx, dx)), ...] -> simple glyph + lsb."""
    pen = TTGlyphPen(None)
    x_min = None
    for name, (sx, dx) in parts:
        tpen = TransformPen(RoundingPen(pen), (sx, 0, 0, 1, dx, 0))
        draw_decomposed(orig[name], orig, tpen)
        ox0 = glyph_bbox(orig, name, bbox_cache)[0]
        nx = round(sx * ox0 + dx)
        x_min = nx if x_min is None else min(x_min, nx)
    glyph = pen.glyph()
    return glyph, (x_min if x_min is not None else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("converted")
    ap.add_argument("outfile")
    ap.add_argument("--smoke", action="store_true",
                    help="one ligature only (merge-behavior test)")
    args = ap.parse_args()

    orig = TTFont(args.original)
    font = TTFont(args.converted)
    oglyf = orig["glyf"]
    glyf = font["glyf"]
    bbox_cache = {}
    order = font.getGlyphOrder()
    existing = set(order)

    bases = CONSONANT_GLYPHS[:1] if args.smoke else CONSONANT_GLYPHS
    rules = []
    made = 0
    for base in bases:
        for suffix, pre, post in PATTERNS:
            new_name = f"{base}_{suffix}"
            if new_name in existing:
                print(f"  skip {new_name} (exists)")
                continue
            if pre and post:
                regs = REGIONS[3]
                parts = [
                    (pre, part_transform(oglyf, pre, regs["pre"], bbox_cache)),
                    (base, part_transform(oglyf, base, regs["base"], bbox_cache)),
                    (post, part_transform(oglyf, post, regs["post"], bbox_cache)),
                ]
                stream = [pre, base, post]
            elif pre:
                regs = REGIONS[2]
                parts = [
                    (pre, part_transform(oglyf, pre, regs["pre"], bbox_cache)),
                    (base, part_transform(oglyf, base, regs["base"], bbox_cache)),
                ]
                stream = [pre, base]
            else:
                regs = REGIONS[2]
                parts = [
                    (base, part_transform(oglyf, base, regs["post_base"],
                                          bbox_cache)),
                    (post, part_transform(oglyf, post, regs["post"],
                                          bbox_cache)),
                ]
                stream = [base, post]
            glyph, lsb = build_ligature(oglyf, parts, bbox_cache)
            glyf[new_name] = glyph  # auto-appends to glyphOrder (verified)
            font["hmtx"].metrics[new_name] = (CELL, lsb)
            existing.add(new_name)
            rules.append((stream, new_name))
            made += 1

    order = font.getGlyphOrder()
    assert len(order) == len(set(order)) == len(glyf.glyphs), (
        f"glyph order desync: {len(order)} names / {len(glyf.glyphs)} glyphs")
    print(f"generated {made} CV ligature glyphs "
          f"({len(order)} glyphs total)")

    fea_lines = ["# rules compiled into the existing GSUB by gen_cv_ligatures.py",
                 "# (addOpenTypeFeatures REPLACES GSUB — QA-proven on 2026-08-30;",
                 "#  this is why we append a lookup via otTables instead)"]
    for stream, out in rules:
        fea_lines.append(f"  sub {' '.join(stream)} by {out};")
    fea_path = Path(args.outfile).with_suffix(".gen.fea")
    fea_path.write_text("\n".join(fea_lines), encoding="utf-8")
    print(f"rule listing: {fea_path} ({len(rules)} rules)")

    # --- append one LigatureSubst lookup to every existing 'pres' feature ---
    # Rules grouped by first glyph of the (already reordered) stream.
    by_first = {}
    for stream, out in rules:
        first, rest = stream[0], list(stream[1:])
        lig = otTables.Ligature()
        lig.Component = rest
        lig.CompCount = len(stream)
        lig.LigGlyph = out
        by_first.setdefault(first, []).append(lig)
    # HarfBuzz takes the FIRST matching ligature per covered glyph — the
    # 3-part ো/ৌ rules must be listed before their 2-part ে/ৈ prefixes.
    for ligs in by_first.values():
        ligs.sort(key=lambda l: -l.CompCount)

    sub = otTables.LigatureSubst()
    sub.Format = 1
    sub.Coverage = otTables.Coverage()
    sub.Coverage.glyphs = sorted(by_first)
    sub.ligatures = {g: by_first[g] for g in sorted(by_first)}

    lookup = otTables.Lookup()
    lookup.LookupType = 4  # Ligature Substitution
    lookup.LookupFlag = 0
    lookup.SubTable = [sub]

    gs = font["GSUB"].table
    gs.LookupList.Lookup.append(lookup)
    gs.LookupList.LookupCount = len(gs.LookupList.Lookup)
    new_idx = gs.LookupList.LookupCount - 1

    touched = 0
    for fr in gs.FeatureList.FeatureRecord:
        if fr.FeatureTag != "pres":
            continue
        idxs = list(fr.Feature.LookupListIndex)
        idxs.append(new_idx)
        fr.Feature.LookupListIndex = idxs
        fr.Feature.LookupCount = len(idxs)
        touched += 1
    print(f"GSUB: lookup {new_idx} appended to {touched} 'pres' feature(s)")
    if not touched:
        sys.exit("no 'pres' feature found — refusing to create one blind")

    font.save(args.outfile)
    print(f"OK: {args.outfile}")


if __name__ == "__main__":
    main()
