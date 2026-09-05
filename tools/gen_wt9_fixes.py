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

from fontTools.pens.boundsPen import BoundsPen
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
    """parts = [(glyph_name, (sx, dx[, dy])), ...] -> simple glyph + metrics."""
    glyf = font["glyf"]
    cache = {}
    pen = TTGlyphPen(None)
    x_min = None
    for name, t in parts:
        sx, dx = t[0], t[1]
        dy = t[2] if len(t) > 2 else 0.0
        tpen = TransformPen(RoundingPen(pen), (sx, 0, 0, 1, dx, dy))
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fontfile", help="mono-converted TTF, modified in place")
    ap.add_argument("--original", default="legacy/base-1.070ship.ttf",
                    help="original font: source of NATURAL advances for "
                         "ligature composition (the converted font gives "
                         "bn_yaphala a full 1404 advance, which Detaches "
                         "the stroke a full cell right - 2026-09-03 bug)")
    ap.add_argument("--cell", type=int, default=1404)
    ap.add_argument("--family", default=None)
    ap.add_argument("--version", default=None)
    args = ap.parse_args()

    font = TTFont(args.fontfile)
    orig = TTFont(args.original)
    glyf = font["glyf"]
    cell = args.cell
    known = set(font.getGlyphOrder())
    rules = []
    frame = int(0.97 * 2 * cell)

    def compose_pair(first, second, out_name):
        """Author directive 2026-09-03: NATURAL SIZE, center maintained.
        first at pen 0, second at pen = ORIGINAL advance of first, both at
        scale 1.0 (no stretching); the combined ink block is centered in
        the 2-cell frame. wt14's column-filling stretch (0.9x on the ্-
        stroke) was rejected — extending a glyph's width area must keep
        the glyph's ink size and center, never rescale the art."""
        op = orig["hmtx"]
        pen2 = float(op[first][0])
        cache = {}
        bx0, _, bx1, _ = glyph_bbox(glyf, first, cache)
        sx0, _, sx1, _ = glyph_bbox(glyf, second, cache)
        lo = min(bx0, pen2 + sx0)
        hi = max(bx1, pen2 + sx1)
        dx = (frame - (hi - lo)) / 2 - lo
        pen = TTGlyphPen(None)
        for gname, (gx, gdx) in ((first, (1.0, dx)),
                                 (second, (1.0, pen2 + dx))):
            tpen = TransformPen(RoundingPen(pen), (gx, 0, 0, 1, gdx, 0))
            draw_decomposed(glyf[gname], glyf, tpen)

        glyph = pen.glyph()
        glyf[out_name] = glyph  # auto-appends to glyphOrder
        lsb = int(round(bx0 + dx))
        font["hmtx"].metrics[out_name] = (2 * cell, lsb)

    # --- 1. reph + ya-phala 2-cell ligatures --------------------------
    assert "bn_half_ra" in known, "no bn_half_ra (reph) glyph"
    made = 0
    for c in CONSONANT_GLYPHS:
        if c not in known:
            continue
        for form, suffix in (("bn_half_ra", "reph2"), ("bn_yaphala", "yaph2")):
            if form not in known:
                continue
            out = f"{c}_{suffix}"
            if out in known:
                continue
            compose_pair(c, form, out)
            rules.append(f"sub {c} {form} by {out};")
            made += 1
    print(f"reph/ya-phala ligatures: {made} glyphs (advance {2 * cell}, "
          f"natural offset)")

    # --- 2. mark + aakaar tuck copies ---------------------------------
    # Author bug 2026-09-03: the tucked ং collided with ক in কিং — the
    # marks are STANDALONE-LETTER designs (bn_anusvara ink spans y 2..1527
    # while bases top out ~1543), so a same-height shift lands inside the
    # base ink. Raise the tuck so its visual ink mass clears the tallest
    # common base top (~1543) + pad, capped under the ascent.
    from fontTools.pens.recordingPen import RecordingPen

    def visual_bottom(gname, table):
        """y below which only ~5% of contour points sit (cuts the
        baseline-anchor tail of standalone mark designs)."""
        rp = RecordingPen()
        draw_decomposed(table[gname], table, rp)
        ys = []
        for op, pts in rp.value:
            if op in ("moveTo", "lineTo", "qCurveTo", "curveTo"):
                for pt in pts:
                    if pt is not None and not isinstance(pt, str):
                        ys.append(pt[1])
        if not ys:
            return 0
        ys.sort()
        return ys[max(0, int(len(ys) * 0.05) - 1)]

    def ink_top(gname, table):
        return glyph_bbox(table, gname, {})[3]

    TARGET_BOTTOM = 1600   # above base-ink top (median 1543) + pad
    ASCENT_CEIL = 2300     # stay under hhea ascent 2360
    tuck_map = {}
    for m in MARKS + ["bn_aakaar"]:
        if m not in known:
            continue
        tuck = f"{m}_tuck"
        dy = 0.0
        if m in MARKS:
            vb = visual_bottom(m, glyf)
            dy = max(0.0, TARGET_BOTTOM - vb)
            if ink_top(m, glyf) + dy > ASCENT_CEIL:
                dy = max(0.0, ASCENT_CEIL - ink_top(m, glyf))
            print(f"  tuck raise {m}: visual bottom {vb} -> "
                  f"{vb + dy:.0f} (dy {dy:.0f})")
        compose(font, tuck, [(m, (1.0, -float(cell), dy))], 0)
        tuck_map[m] = tuck
        rules.append(f"tuck: {m} -> {tuck} (0 adv, shifted -{cell}, "
                     f"raised {dy:.0f})")
    print(f"tuck copies: {len(tuck_map)} ({', '.join(tuck_map.values())})")

    order = font.getGlyphOrder()
    assert len(order) == len(set(order)) == len(glyf.glyphs), "order desync"

    # --- 3. GSUB lookups ------------------------------------------------
    gs = font["GSUB"].table

    # L1: LigatureSubst [C][form] -> C_reph2 / C_yaph2, grouped by first
    # glyph. HarfBuzz takes the first matching ligature per covered glyph;
    # each first glyph has at most one entry per component set here.
    by_first = {}
    order_now = set(font.getGlyphOrder())
    for c in CONSONANT_GLYPHS:
        if c not in order_now:
            continue
        for form, suffix in (("bn_half_ra", "reph2"), ("bn_yaphala", "yaph2")):
            out = f"{c}_{suffix}"
            if out not in order_now:
                continue
            lig = otTables.Ligature()
            lig.Component = [form]
            lig.CompCount = 2
            lig.LigGlyph = out
            by_first.setdefault(c, []).append(lig)
    if not by_first:
        raise SystemExit("no ligature glyphs found - nothing to wire")
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
        # Coverage format 1 MUST be sorted by glyph id (binary search).
        # Filter against the CURRENT order - ligature glyphs composed
        # above are not in the load-time `known` set (2026-09-03: rule C
        # silently got an empty coverage because of the stale set).
        present = [n for n in names if n in set(font.getGlyphOrder())]
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

    # rule C: aakaar after a reph2/yaph2 ligature tucks. Measured
    # 2026-09-03: WT collapses া to 0 columns after any multi-glyph
    # cluster (dyaa=2, byaa=2, korta=3, bidya=4) while the composed
    # ligature art spans both columns -> 1-column overhang. The tuck
    # draws the া one cell left, over the ligature's second column
    # (correct position: right of the base).
    # NOTE: coverage against the CURRENT glyph order - the ligature
    # glyphs were composed above and are not in the load-time `known`.
    order_now = set(font.getGlyphOrder())
    lig_glyphs = [f"{c}_{s}" for c in CONSONANT_GLYPHS
                  for s in ("reph2", "yaph2") if f"{c}_{s}" in order_now]
    if not lig_glyphs:
        raise SystemExit("rule C: no ligature glyphs found")
    st_c = otTables.ChainContextSubst()
    st_c.Format = 3
    st_c.BacktrackCoverage = [cov(lig_glyphs)]
    st_c.InputCoverage = [cov(["bn_aakaar"])]
    st_c.LookAheadCoverage = []
    st_c.SubstCount = 1
    rec_c = otTables.SubstLookupRecord()
    rec_c.SequenceIndex = 0
    rec_c.LookupListIndex = 0  # patched after indices known
    st_c.SubLookupRecord = [rec_c]
    st_c.SubstLookupRecord = [rec_c]  # both names (see duality note below)
    # fontTools duality: fresh tables expose the record list as
    # 'SubLookupRecord' (getConverters) but the compiler/decompiler use
    # 'SubstLookupRecord' (2026-09-03: records silently dropped on save
    # when only one name was set). Set BOTH.
    st_a.SubstLookupRecord = [rec_a]
    st_b.SubstLookupRecord = [rec_b]

    lk_ctx = otTables.Lookup()
    lk_ctx.LookupType = 6  # Chain Context Substitution
    lk_ctx.LookupFlag = 0
    lk_ctx.SubTable = [st_a, st_b, st_c]

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

    # --- 4. wide conjuncts ---------------------------------------------
    # Author bug 2026-09-03: আত্ম drew 1 cell of merged art against 3-4
    # charged columns. WT charges k columns for k consonants (virama = 0),
    # so every conjunct output of k consonants gets a k-cell wide copy
    # composed from the ORIGINAL natural art; a pres single-subst wired
    # AFTER all other lookups substitutes conjunct -> conjunct_w.
    # Excludes reph2/yaph2 outputs (already multi-cell) and consonant/
    # matra glyph names. Shared-Mono trade-off (author decision
    # 2026-09-03): 1-cell-grant hosts (kitty/VTE) overlap instead of gap.
    # Enumeration shapes the font WITH the reph2/tuck rules wired; write
    # it to a temp file for vharfbuzz (saving the output and rewriting it
    # later fails on Windows: the hb blob keeps the file locked).
    import os
    tmp_enum = args.fontfile + ".enum.ttf"
    font.save(tmp_enum)
    from vharfbuzz import Vharfbuzz
    from copy import deepcopy
    vhb = Vharfbuzz(tmp_enum)
    feats = {"script": "beng", "language": "ben"}
    rev = {}
    for cp, gname in TTFont(args.original).getBestCmap().items():
        rev.setdefault(gname, chr(cp))
    H = "\u09CD"
    cons_set = set(CONSONANT_GLYPHS)
    cons_chars = [rev[c] for c in CONSONANT_GLYPHS if c in rev]
    skip_suffix = ("kaar", "aumark", "reph2", "yaph2", "_tuck",
                   "yaphala", "half_ra", "raphala", "half_ta")

    def candidates(names):
        out = []
        for n in names:
            if (n in cons_set or not n.startswith("bn_") or "_" not in n
                    or n.endswith(skip_suffix) or n.startswith("bn_half_")):
                continue
            out.append(n)
        return out

    conj_k = {}
    cache = {}
    # WT live measurement 2026-09-03 (probe_canonical2): a RA-PHALA-final
    # consonant (hasanta+র) charges 0 columns (ত্র=2, ন্ত্র=2), while
    # yaphala-য charges 1 (বিদ্যা=4). So the wide frame k = consonant
    # count minus a trailing hasanta+র; k_eff of 1 means: do not widen.
    ra = rev.get("bn_ra")

    def name_k(n):
        """WT live truth (probe_canonical2 + probe_ra, 2026-09-03): every
        conjunct cluster charges exactly 2 columns — 3-consonant clusters
        collapse to 2 as well (ন্ত্র=2, স্প্ল=2, ক্ষ্ম=2 live-probed), and
        standalone-hasanta forms stay 1-cell (ক্=1)."""
        seg = n.split("_")[1:]
        if not seg or any("hasanta" in x for x in seg):
            return 1
        return 2

    def store(names):
        for n in candidates(names):
            k = name_k(n)
            if k < 2:
                continue
            if n not in conj_k or k < conj_k[n]:
                conj_k[n] = k

    for a in cons_chars:
        for b in cons_chars:
            two = a + H + b
            names = cache.get(two)
            if names is None:
                names = [vhb.hbfont.glyph_to_string(i.codepoint)
                         for i in vhb.shape(two, feats).glyph_infos]
                cache[two] = names
            store(names)
    merged_pairs = [t for t, names in cache.items()
                    if len(names) == 1 and candidates(names)]
    for two in merged_pairs:
        for c in cons_chars:
            three = two + H + c
            names = [vhb.hbfont.glyph_to_string(i.codepoint)
                     for i in vhb.shape(three, feats).glyph_infos]
            store(names)
    print(f"wide conjunct stage: {len(conj_k)} distinct conjunct glyphs "
          f"(2-consonant: {sum(1 for k in conj_k.values() if k == 2)}, "
          f"3-consonant: {sum(1 for k in conj_k.values() if k == 3)})")
    del vhb  # release the blob before touching the output file again
    try:
        os.remove(tmp_enum)
    except OSError:
        pass

    order_now = set(font.getGlyphOrder())
    # fontTools trap: getGlyphID caches the reverse map at first call;
    # wide glyphs added after that are invisible to it (same class as the
    # stale-Coverage incident). Sort against the LIVE order list instead.
    def gid(name):
        return font.getGlyphOrder().index(name)
    made_wide = {}
    for g, k in sorted(conj_k.items()):
        if g not in order_now or g not in orig["glyf"].keys():
            continue
        wide = g + "_w"
        frame = k * cell
        cap = 0.97 * frame
        bcache = {}
        bx0, _, bx1, _ = glyph_bbox(orig["glyf"], g, bcache)
        bw = bx1 - bx0
        s = min(1.0, cap / bw)
        dx = (frame - s * bw) / 2.0 - s * bx0
        pen = TTGlyphPen(None)
        tpen = TransformPen(RoundingPen(pen), (s, 0, 0, 1, dx, 0))
        draw_decomposed(orig["glyf"][g], orig["glyf"], tpen)
        glyf[wide] = pen.glyph()  # auto-appends to glyphOrder
        font["hmtx"].metrics[wide] = (frame, round(s * bx0))
        made_wide[g] = (wide, s, dx)

    # GPOS: marks attaching to a widened conjunct must attach to the wide
    # copy too (base anchors transform with (s, dx)).
    gpos_moved = 0
    if made_wide:
        gp = font["GPOS"].table
        for lk in gp.LookupList.Lookup:
            for st in lk.SubTable:
                ext = getattr(st, "ExtSubTable", None)
                if ext is not None:
                    st = ext
                if st.__class__.__name__ != "MarkBasePos":
                    continue
                for i, gname in enumerate(list(st.BaseCoverage.glyphs)):
                    if gname not in made_wide:
                        continue
                    wide, s, dx = made_wide[gname]
                    if wide in st.BaseCoverage.glyphs:
                        continue
                    st.BaseCoverage.glyphs.append(wide)
                    st.BaseCoverage.glyphs.sort(key=gid)
                    j = st.BaseCoverage.glyphs.index(wide)
                    src = st.BaseArray.BaseRecord[i]
                    rec = otTables.BaseRecord()
                    rec.BaseAnchor = []
                    for anc in src.BaseAnchor:
                        if anc is not None:
                            na = deepcopy(anc)
                            na.XCoordinate = round(s * na.XCoordinate + dx)
                            rec.BaseAnchor.append(na)
                        else:
                            rec.BaseAnchor.append(None)
                    st.BaseArray.BaseRecord.insert(j, rec)
                    st.BaseArray.BaseCount = len(st.BaseArray.BaseRecord)
                    gpos_moved += 1
        print(f"GPOS: wide-conjunct base records added: {gpos_moved}")

    if made_wide:
        # extend rule C (aa-tuck) backtrack coverage: aa after a conjunct
        # collapses to 0 charged columns in WT just like after reph2/yaph2
        # (wt13), so the tuck must fire there too. The chain lookup runs
        # BEFORE the wide substitution, so the backtrack must carry the
        # ORIGINAL conjunct names (the pre-wide stream), not the _w names.
        st_c.BacktrackCoverage[0].glyphs.extend(made_wide.keys())
        st_c.BacktrackCoverage[0].glyphs.sort(key=gid)

    # --- 4b. prebase-matra cancellation --------------------------------
    # WT live (probe_ra): a PRE-BASE matra following a conjunct cluster in
    # codepoint order (দ্বিতীয়'s ি, ক্রোধ's ো) collapses to 0 charged
    # columns, so those clusters must STAY 1 cell wide. Contextual rule:
    # [conjunct][pre-base matra] -> conjunct_n (composite alias, 1 cell),
    # wired BEFORE the wide-ss so the alias misses the wide substitution.
    aliases = {}
    if made_wide:
        from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
        for g in made_wide:
            alias = g + "_n"
            if alias in font.getGlyphOrder():
                continue
            gl = Glyph()
            comp = GlyphComponent()
            comp.glyphName = g
            comp.x, comp.y = 0, 0
            gl.components = [comp]
            gl.numberOfComponents = 1
            glyf[alias] = gl  # auto-appends to glyphOrder
            font["hmtx"].metrics[alias] = (cell, font["hmtx"][g][1])
            aliases[g] = alias
        print(f"prebase-cancel aliases: {len(aliases)}")

    if made_wide and aliases:
        mapping = {g: made_wide[g][0] for g in
                   sorted(made_wide, key=gid)}
        m = otTables.SingleSubst()
        m.mapping = mapping
        lk_w = otTables.Lookup()
        lk_w.LookupType = 1
        lk_w.LookupFlag = 0
        lk_w.SubTable = [m]

        ss_n = otTables.SingleSubst()
        ss_n.mapping = {g: aliases[g] for g in sorted(aliases, key=gid)}
        lk_sn = otTables.Lookup()
        lk_sn.LookupType = 1
        lk_sn.LookupFlag = 0
        lk_sn.SubTable = [ss_n]

        pre = [q for q in PREBASE_GLYPHS if q in set(font.getGlyphOrder())]
        st_x = otTables.ChainContextSubst()
        st_x.Format = 3
        # pre-base matras REORDER to the left: the matra is the BACKTRACK
        # of [matra][conjunct], not the lookahead
        st_x.BacktrackCoverage = [cov(pre)]
        st_x.InputCoverage = [cov(list(aliases.keys()))]
        st_x.LookAheadCoverage = []
        st_x.SubstCount = 1
        rec_x = otTables.SubstLookupRecord()
        rec_x.SequenceIndex = 0
        rec_x.LookupListIndex = 0  # patched after indices known
        st_x.SubLookupRecord = [rec_x]
        st_x.SubstLookupRecord = [rec_x]  # both names (duality note)
        lk_cx = otTables.Lookup()
        lk_cx.LookupType = 6
        lk_cx.LookupFlag = 0
        lk_cx.SubTable = [st_x]

        gs.LookupList.Lookup.extend([lk_sn, lk_cx, lk_w])
        base_idx = gs.LookupList.LookupCount
        gs.LookupList.LookupCount = base_idx + 3
        rec_x.LookupListIndex = base_idx  # the narrow single-subst
        # NOTE: the narrow-ss must NOT appear in any feature's index list
        # (unconditional-fire bug, qa-proven 2026-08-30) — it is reachable
        # only as the chain's nested lookup. pres gets chain + wide-ss.
        for fr in gs.FeatureList.FeatureRecord:
            if fr.FeatureTag != "pres":
                continue
            idxs = list(fr.Feature.LookupListIndex)
            idxs.extend([base_idx + 1, base_idx + 2])
            fr.Feature.LookupListIndex = idxs
            fr.Feature.LookupCount = len(idxs)
        rules.append(f"wide: {len(mapping)} conjuncts -> *_w; "
                     f"prebase-cancel aliases: {len(aliases)}")
        print(f"GSUB: lookups {base_idx}(narrow-ss) "
              f"{base_idx + 1}(narrow-chain) {base_idx + 2}(wide-ss) "
              f"appended to pres (last)")

    # --- 4c. aa-after-cluster natural ligatures -------------------------
    # Author bug 2026-09-05: in হত্যা the aa-tuck (-1 cell) drew the া ON
    # TOP of the ্য stroke inside C_yaph2 (same class on wide conjuncts:
    # স্বা). Natural compose instead: [C][yaphala][aa] / [conjunct][aa]
    # at ORIGINAL relative offsets, scaled to the 2-cell frame. Keyed on
    # the ALREADY-TUCKED pair [prefix][bn_aakaar_tuck] — HB applies
    # lookups in lookup-index order, so this (last) runs after the chain
    # that produces the tuck.
    aa_pairs = {}
    for c in CONSONANT_GLYPHS:
        y = f"{c}_yaph2"
        if y in font.getGlyphOrder() and c in orig["glyf"].keys():
            aa_pairs[y] = (f"{y}_aa",
                           [(c, 0.0),
                            ("bn_yaphala", float(orig["hmtx"][c][0])),
                            ("bn_aakaar", float(orig["hmtx"][c][0]
                                               + orig["hmtx"]["bn_yaphala"][0]))])
    for g in made_wide:
        if g in orig["glyf"].keys():
            # key on the _w NAME: by lookup-20 time the wide-ss has
            # already renamed the stream glyph
            wide = made_wide[g][0]
            aa_pairs[wide] = (f"{wide}_aa",
                              [(g, 0.0),
                               ("bn_aakaar", float(orig["hmtx"][g][0]))])
    made_aa = {}
    for prefix, (out, parts) in aa_pairs.items():
        cache3 = {}
        xs = []
        for gname, pen in parts:
            b = glyph_bbox(orig["glyf"], gname, cache3)
            xs += [pen + b[0], pen + b[2]]
        lo, hi = min(xs), max(xs)
        bw = hi - lo
        sc = min(1.0, 0.97 * cell / bw)
        dx = (2 * cell - sc * bw) / 2.0 - sc * lo
        pen3 = TTGlyphPen(None)
        for gname, pen in parts:
            tpen = TransformPen(RoundingPen(pen3),
                                (sc, 0, 0, 1, sc * pen + dx, 0))
            draw_decomposed(orig["glyf"][gname], orig["glyf"], tpen)
        glyf[out] = pen3.glyph()  # auto-appends to glyphOrder
        font["hmtx"].metrics[out] = (2 * cell, round(sc * lo + dx))
        made_aa[prefix] = out
    print(f"aa natural ligatures: {len(made_aa)} glyphs (advance {2 * cell})")

    if made_aa:
        by_first = {}
        for prefix, out in made_aa.items():
            lig = otTables.Ligature()
            lig.Component = ["bn_aakaar_tuck"]
            lig.CompCount = 2
            lig.LigGlyph = out
            by_first.setdefault(prefix, []).append(lig)
        sub_aa = otTables.LigatureSubst()
        sub_aa.Format = 1
        sub_aa.Coverage = otTables.Coverage()
        sub_aa.Coverage.glyphs = sorted(by_first, key=gid)
        sub_aa.ligatures = {k: by_first[k] for k in sorted(by_first, key=gid)}
        lk_aa = otTables.Lookup()
        lk_aa.LookupType = 4
        lk_aa.LookupFlag = 0
        lk_aa.SubTable = [sub_aa]
        gs.LookupList.Lookup.append(lk_aa)
        aa_idx = gs.LookupList.LookupCount
        gs.LookupList.LookupCount = aa_idx + 1
        for fr in gs.FeatureList.FeatureRecord:
            if fr.FeatureTag != "pres":
                continue
            idxs = list(fr.Feature.LookupListIndex)
            idxs.append(aa_idx)
            fr.Feature.LookupListIndex = idxs
            fr.Feature.LookupCount = len(idxs)
        print(f"GSUB: aa-ligature lookup {aa_idx} appended to pres (last)")

    # invalidate the cached reverse glyph map so save-time Coverage
    # compiles see glyphs added after the first getGlyphID call
    font.setGlyphOrder(font.getGlyphOrder())

    # 2026-09-03 incident: this block ran on --version alone and clobbered
    # mono_convert's family ("Siyam Rupali Mono WT9") back to the default
    # "Siyam Rupali Mono" -> internal-name collision with the 008 install
    # -> font-cache poisoning. Rewrite names ONLY when --family is given;
    # --version alone touches ID5 + fontRevision.
    if args.family:
        fam = args.family
        subname = "Regular"
        ps = fam.replace(" ", "") + "-" + subname
        full = f"{fam} {subname}"
        name = font["name"]
        for nid, val in ((1, fam), (2, subname), (3, f"{ps};mono-term"),
                         (4, full), (6, ps), (16, fam), (17, subname)):
            name.setName(val, nid, 3, 1, 0x409)
            name.setName(val, nid, 1, 0, 0)
    if args.version:
        ver = f"Version {args.version}"
        font["name"].setName(ver, 5, 3, 1, 0x409)
        font["name"].setName(ver, 5, 1, 0, 0)
        major, minor = args.version.split(".")[:2]
        font["head"].fontRevision = float(f"{major}.{minor}")

    listing = Path(args.fontfile).with_suffix(".wt9.fea")
    listing.write_text("\n".join(rules), encoding="utf-8")
    print(f"rule listing: {listing}")
    font.save(args.fontfile)
    print(f"OK: {args.fontfile}")


if __name__ == "__main__":
    main()
