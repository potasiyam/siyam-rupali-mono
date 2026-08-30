#!/usr/bin/env python3
"""Audit the base TTF for the mono conversion: metrics, layout structure,
advance-width distribution, conjunct (ligature-output) inventory.

Usage: audit_base.py font.ttf
"""
import statistics
import sys
from collections import Counter

from fontTools.ttLib import TTFont


def gsub_ligature_outputs(font):
    """Glyphs produced by any GSUB ligature substitution (2+ components)."""
    outs = {}
    gs = font["GSUB"].table
    for lr in gs.LookupList.Lookup:
        for st in lr.SubTable:
            ext = getattr(st, "ExtSubTable", None)
            if ext is not None:
                st = ext
            if hasattr(st, "ligatures"):
                for first, ligs in st.ligatures.items():
                    for lig in ligs:
                        comps = [first] + lig.Component
                        outs.setdefault(lig.LigGlyph, []).append(tuple(comps))
    return outs


def main(path):
    f = TTFont(path)
    names = f.getGlyphOrder()
    upm = f["head"].unitsPerEm
    print(f"upem={upm} hhea={f['hhea'].ascent}/{f['hhea'].descent}/{f['hhea'].lineGap}")
    print(f"win={f['OS/2'].usWinAscent}/{f['OS/2'].usWinDescent} "
          f"typo={f['OS/2'].sTypoAscender}/{f['OS/2'].sTypoDescender} "
          f"xAvg={f['OS/2'].xAvgCharWidth} isFixedPitch={f['post'].isFixedPitch}")

    gs = f["GSUB"].table
    gsub_feats = Counter(fr.FeatureTag for fr in gs.FeatureList.FeatureRecord)
    print("GSUB features:", dict(gsub_feats))
    gp = f["GPOS"].table
    gpos_feats = Counter(fr.FeatureTag for fr in gp.FeatureList.FeatureRecord)
    print("GPOS features:", dict(gpos_feats))

    gdef = f["GDEF"].table
    mc = gdef.GlyphClassDef.classDefs if gdef.GlyphClassDef else {}
    print("GDEF classes (1=base 2=lig 3=mark 4=component):",
          dict(Counter(mc.values())))

    ligs = gsub_ligature_outputs(f)
    print(f"ligature outputs: {len(ligs)}")

    w = {g: f["hmtx"][g][0] for g in names}
    marks = [g for g in names if mc.get(g) == 3]
    print(f"marks (GDEF 3): {len(marks)}, all zero-advance: "
          f"{all(w[g] == 0 for g in marks)}")

    def bbox_w(g):
        if g not in f["glyf"].glyphs:
            return None
        bb = f["glyf"][g]
        if bb.numberOfContours == 0:
            return None
        return bb.xMax - bb.xMin

    print("\n-- advance distribution (non-mark, advance>0) --")
    pos = sorted(w[g] for g in names if w[g] > 0 and mc.get(g) != 3)
    buckets = Counter((v // 128) * 128 for v in pos)
    for b in sorted(buckets):
        bar = "#" * max(1, buckets[b] // 3)
        print(f"  {b:5}-{b+127:5} {buckets[b]:4} {bar}")

    print("\n-- probe glyphs --")
    for g in ["space", "A", "a", "zero", "bn_ka", "bn_k_ssa", "bn_k_ta",
              "bn_s_t_ra", "bn_au", "bn_ekaar", "bn_repha", "bn_hasanta"]:
        if g in names:
            print(f"  {g:14} adv={w[g]:5} bbox_w={bbox_w(g)} "
                  f"lig={'Y' if g in ligs else 'n'} "
                  f"cls={mc.get(g, '-')}")
        else:
            print(f"  {g:14} ABSENT")

    # conjunct vs base advance stats
    lig_ws = [w[g] for g in ligs if w[g] > 0]
    base_ws = [w[g] for g in names if g not in ligs and w[g] > 0 and mc.get(g) != 3]
    if lig_ws:
        print(f"\nligature advances: n={len(lig_ws)} min={min(lig_ws)} "
              f"max={max(lig_ws)} mean={statistics.mean(lig_ws):.0f}")
    if base_ws:
        print(f"non-lig advances:  n={len(base_ws)} min={min(base_ws)} "
              f"max={max(base_ws)} mean={statistics.mean(base_ws):.0f}")
    # Latin block widths
    lat = [w[g] for g in names if g in ("A", "B", "H", "n", "o", "zero", "period")]
    print("latin probes:", lat)


if __name__ == "__main__":
    main(sys.argv[1])
