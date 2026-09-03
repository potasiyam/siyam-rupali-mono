#!/usr/bin/env python3
"""WT9 terminal-column fixes on a mono-converted no-ligature build.

Measured model (docs/PROOF_2026-09-03.md): WT charges per codepoint
with mark-run collapse and draws shaped glyphs compact. Two residuals:

1. Reph gap: কর্ত charges 3 columns (র included) but the shaped reph
   glyph has zero advance -> the র column renders empty.
   Fix: LigatureSubst [consonant][bn_half_ra] -> <C>_reph2, a 2-cell
   composed glyph: consonant art shifted right one cell, reph hook
   centered over the LEFT cell (the charged র column).

2. Mark overhang: কিং charges 2 columns (ং collapses after a mark) but
   verbatim art is 3 cells -> ং spills into the next cluster.
   Fix: contextual tuck. anusvara/visarga gets a zero-advance _tuck
   copy (outline shifted one cell left) substituted when preceded by
   [post-base matra] or by [pre-base matra][base]. কং keeps its own
   full column (no context match).

Lookups append to 'pres' without touching existing GSUB (addOpenTypeFeatures
REPLACES GSUB - QA-proven 2026-08-30; otTables append only).
"""
import argparse
from pathlib import Path

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from mono_convert import RoundingPen, draw_decomposed, glyph_bbox

CONSONANT_GLYPHS = [
    "bn_ka", "bn_kha", "bn_ga", "bn_gha", "bn_nga", "bn_ca", "bn_cha",
    "bn_ja", "bn_jha", "bn_nya", "bn_tta", "bn_ttha", "bn_dda", "bn_ddha",
    "bn_nna", "bn_ta", "bn_tha", "bn_da", "bn_dha", "bn_na", "bn_pa",
    "bn_pha", "bn_ba", "bn_bha", "bn_ma", "bn_ya", "bn_ra", "bn_la",
    "bn_sha", "bn_ssa", "bn_sa", "bn_ha", "bn_rra", "bn_rha", "bn_j_nya",
]
# shaped pre-base matras (init + standard variants)
PREBASE_GLYPHS = ["bn_ikaar", "bn_iikaar", "bn_ekaar", "bn_aikaar",
                  "bn_initekaar", "bn_initaikaar"]
# shaped post-base SPACING matras (charged 1 column; keep own column)
POSTBASE_SP_GLYPHS = ["bn_aakaar", "bn_okaar", "bn_aukaar"]
MARKS = ["bn_anusvara", "bn_visarga"]


def compose(font, out_name, parts, advance):
    """parts = [(glyph_name, (sx, dx)), ...] -> simple glyph + metrics."""
    glyf = font["glyf"]
    cache = {}
    pen = TTGlyphPen(None)
    x_min = None
    for name, (sx, dx) in parts:
        tpen = TransformPen(RoundingPen(pen), (sx, 0, 0, 1, dx, 0))
        draw_decomposed(glyf[name], glyf, tpen)
        ox0 = glyph_bbox(glyf, name, cache)[0]
        nx = round(sx * ox0 + dx)
        x_min = nx if x_min is None else min(x_min, nx)
    glyf[out_name] = glyph = pen.glyph()  # auto-appends to glyphOrder
    font["hmtx"].metrics[out_name] = (advance,
                                      x_min if x_min is not None else 0)
    return glyph


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fontfile", help="mono-converted TTF, modified in place")
    ap.add_argument("--cell", type=int, default=1404)
    ap.add_argument("--family", default=None)
    ap.add_argument("--version", default=None)
    args = ap.parse_args()

    font = TTFont(args.fontfile)
    glyf = font["glyf"]
    cell = args.cell
    known = set(font.getGlyphOrder())
    rules = []

    # --- 1. reph 2-cell ligatures ------------------------------------
    assert "bn_half_ra" in known, "no bn_half_ra (reph) glyph"
    hb_x0, _, hb_x1, _ = glyph_bbox(glyf, "bn_half_ra", {})
    reph_dx = cell / 2 - (hb_x0 + hb_x1) / 2   # hook centered over col 1
    made = 0
    for c in CONSONANT_GLYPHS:
        if c not in known:
            continue
        out = f"{c}_reph2"
        if out in known:
            continue
        compose(font, out, [(c, (1.0, float(cell))),
                            ("bn_half_ra", (1.0, reph_dx))], 2 * cell)
        rules.append(f"sub {c} bn_half_ra by {out};")
        made += 1
    print(f"reph ligatures: {made} glyphs (advance {2 * cell})")

    # --- 2. mark tuck copies ------------------------------------------
    tuck_map = {}
    for m in MARKS:
        if m not in known:
            continue
        tuck = f"{m}_tuck"
        compose(font, tuck, [(m, (1.0, -float(cell)))], 0)
        tuck_map[m] = tuck
        rules.append(f"tuck: {m} -> {tuck} (0 adv, shifted -{cell})")
    print(f"tuck copies: {len(tuck_map)} ({', '.join(tuck_map.values())})")

    order = font.getGlyphOrder()
    assert len(order) == len(set(order)) == len(glyf.glyphs), "order desync"

    # --- 3. GSUB lookups ------------------------------------------------
    gs = font["GSUB"].table

    # L1: LigatureSubst [C][bn_half_ra] -> C_reph2, grouped by first glyph
    by_first = {}
    for c in CONSONANT_GLYPHS:
        out = f"{c}_reph2"
        if out not in set(font.getGlyphOrder()):
            continue
        lig = otTables.Ligature()
        lig.Component = ["bn_half_ra"]
        lig.CompCount = 2
        lig.LigGlyph = out
        by_first.setdefault(c, []).append(lig)
    sub = otTables.LigatureSubst()
    sub.Format = 1
    sub.Coverage = otTables.Coverage()
    sub.Coverage.glyphs = sorted(by_first)
    sub.ligatures = {g: by_first[g] for g in sorted(by_first)}
    lk_lig = otTables.Lookup()
    lk_lig.LookupType = 4
    lk_lig.LookupFlag = 0
    lk_lig.SubTable = [sub]

    # L2: the nested single substitution (mark -> tuck)
    ss = otTables.SingleSubst()
    ss.mapping = tuck_map
    lk_ss = otTables.Lookup()
    lk_ss.LookupType = 1
    lk_ss.LookupFlag = 0
    lk_ss.SubTable = [ss]

    def cov(names):
        c = otTables.Coverage()
        # Coverage format 1 MUST be sorted by glyph id (binary search)
        present = [n for n in names if n in known]
        present.sort(key=font.getGlyphID)
        c.glyphs = present
        return c

    # L3: chain context, format 3 (one rule per subtable).
    # Field names verified against fontTools converters:
    # SubstCount + SubLookupRecord(SequenceIndex, LookupListIndex).
    st_a = otTables.ChainContextSubst()
    st_a.Format = 3
    st_a.BacktrackCoverage = [cov(POSTBASE_SP_GLYPHS)]
    st_a.InputCoverage = [cov(tuck_map)]
    st_a.LookAheadCoverage = []
    st_a.SubstCount = 1
    rec_a = otTables.SubstLookupRecord()
    rec_a.SequenceIndex = 0
    rec_a.LookupListIndex = 0  # patched after indices known
    st_a.SubLookupRecord = [rec_a]

    st_b = otTables.ChainContextSubst()
    st_b.Format = 3
    st_b.BacktrackCoverage = [cov(PREBASE_GLYPHS)]
    st_b.InputCoverage = [cov(CONSONANT_GLYPHS), cov(tuck_map)]
    st_b.LookAheadCoverage = []
    st_b.SubstCount = 1
    rec_b = otTables.SubstLookupRecord()
    rec_b.SequenceIndex = 1
    rec_b.LookupListIndex = 0  # patched after indices known
    st_b.SubLookupRecord = [rec_b]
    # fontTools duality: fresh tables expose the record list as
    # 'SubLookupRecord' (getConverters) but the compiler/decompiler use
    # 'SubstLookupRecord' (2026-09-03: records silently dropped on save
    # when only one name was set). Set BOTH.
    st_a.SubstLookupRecord = [rec_a]
    st_b.SubstLookupRecord = [rec_b]

    lk_ctx = otTables.Lookup()
    lk_ctx.LookupType = 6  # Chain Context Substitution
    lk_ctx.LookupFlag = 0
    lk_ctx.SubTable = [st_a, st_b]

    # NOTE: the single-subst lookup must NOT be referenced by any feature —
    # standalone it would tuck EVERY anusvara/visarga (the kang bug of
    # 2026-09-03: কং collapsed to 1 cell). It lives in the LookupList and
    # is reachable only as the nested lookup of the chain-context lookup.
    for lk in (lk_lig, lk_ss, lk_ctx):
        gs.LookupList.Lookup.append(lk)
    first = gs.LookupList.LookupCount
    gs.LookupList.LookupCount = first + 3
    # nested lookup indices point at the single-subst lookup (first+1)
    for st in lk_ctx.SubTable:
        st.SubLookupRecord[0].LookupListIndex = first + 1
    print(f"GSUB: lookups {first}(lig) {first + 1}(ss, nested-only) "
          f"{first + 2}(chain) appended")

    touched = 0
    for fr in gs.FeatureList.FeatureRecord:
        if fr.FeatureTag != "pres":
            continue
        idxs = list(fr.Feature.LookupListIndex)
        idxs.extend([first, first + 2])
        fr.Feature.LookupListIndex = idxs
        fr.Feature.LookupCount = len(idxs)
        touched += 1
    print(f"GSUB: lookups appended to {touched} 'pres' feature(s)")
    if not touched:
        raise SystemExit("no 'pres' feature found - refusing to continue")

    if args.family or args.version:
        fam = args.family or "Siyam Rupali Mono"
        subname = "Regular"
        ps = fam.replace(" ", "") + "-" + subname
        ver = f"Version {args.version or '1.100'}"
        name = font["name"]
        for nid, val in ((1, fam), (2, subname), (3, f"{ps};{ver};mono-term"),
                         (4, f"{fam} {subname}"), (5, ver), (6, ps),
                         (16, fam), (17, subname)):
            name.setName(val, nid, 3, 1, 0x409)
            name.setName(val, nid, 1, 0, 0)
        major, minor = (args.version or "1.100").split(".")[:2]
        font["head"].fontRevision = float(f"{major}.{minor}")

    listing = Path(args.fontfile).with_suffix(".wt9.fea")
    listing.write_text("\n".join(rules), encoding="utf-8")
    print(f"rule listing: {listing}")
    font.save(args.fontfile)
    print(f"OK: {args.fontfile}")


if __name__ == "__main__":
    main()
