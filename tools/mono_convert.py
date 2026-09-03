#!/usr/bin/env python3
"""Convert proportional Siyam Rupali into a strict-terminal-mono font.

Model: every advance-bearing glyph occupies exactly ONE cell of `cell`
units (default: upem/2 = 1024). Outlines are x-condensed (y untouched) to
fit inside `ink_cap * cell`, then recentered in the cell. Marks (GDEF
class 3 or advance < mark_floor) keep their near-zero advances. Matra/
kar glyphs (is_kar / PREBASE_SHIFT_ALL) keep their ORIGINAL art
verbatim — the VOLT-era design positions their ink for codepoint-order
drawing, and recentering it destroyed that (the root cause of the
detached-matra bugs). Only the advance becomes the cell. GPOS
MarkToBase anchors move with each base glyph's transform. Legacy tables
that encode the OLD advances/bitmaps/hints are dropped.

This script is step 1 of the pipeline for BOTH deliverables:
  - terminal build: step 2 = gen_cv_ligatures.py (CV ligatures for
    shaping terminals)
  - editor build:   no step 2 (matras keep their own full cell)
See AGENTS.md / docs/TERMINAL.md.

Usage:
  mono_convert.py IN.ttf OUT.ttf [--cell N] [--ink-cap 0.92]
      [--family "Siyam Rupali Mono"] [--version 1.100]
"""
import argparse
import statistics
import sys

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


def draw_decomposed(glyph, table, pen):
    """Draw a glyph with composites flattened to contours.

    All components in the base font are offset-only (verified at audit
    time); a scaled component would silently drop its 2x2 here.
    """
    if glyph.isComposite():
        for comp in glyph.components:
            tpen = TransformPen(pen, (1, 0, 0, 1, comp.x, comp.y))
            draw_decomposed(table[comp.glyphName], table, tpen)
    else:
        glyph.draw(pen, glyfTable=table)

MARK_ADV_FLOOR = 300  # advances below this are treated as mark-ish, untouched

# Pre-base/above matras (drawn BEFORE the base in correct text, but typed
# and stored AFTER it). Terminal-land is split in two, measured
# 2026-08-31 (review session):
#   - Windows Terminal 1.24: NO Bengali shaping/reorder; columns charged
#     per codepoint from the Unicode GraphemeBreakProperty table
#     (SpacingMark = 1 column, Extend = 0), glyphs drawn in codepoint
#     order. The VOLT-era art was designed for exactly this: each matra's
#     ink already sits at its final visual position relative to the pen
#     (negative bearings, overlay bars), so codepoint-order drawing
#     interlocks correctly.
#   - kitty / VTE / foot / wezterm: HarfBuzz shaping; columns follow
#     clusters; CV ligatures from gen_cv_ligatures.py merge clusters.
# Since 0.0.6 the matras keep their ORIGINAL art verbatim (is_kar /
# PREBASE_SHIFT_ALL branch below), which serves both families without
# any shifting machinery. This set now only drives the restore-lookup
# coverage for legacy --prebase-shift builds and names the verbatim
# set for the 0.0.6 rule.
PREBASE_SHIFT = {
    "bn_ikaar",     # ?
    "bn_ekaar",     # ?
    "bn_aikaar",    # ?
    "bn_okaar",     # (?-part lands over the base, ?-part in own cell)
    "bn_aukaar",    # ?
    "bn_anusvara",  # ?
}

# 0.0.4 FLIP (review session): the cmap/default glyph carries CENTERED art
# (alacritty-class renderers merge zero-width matras into the base cell;
# shaping-terminal leftovers and editors want centered art in reordered
# position), and a <name>_shifted copy carries the one-cell-left art. Step
# 2 appends a pres restore (centered -> shifted) that fires in Windows
# Terminal (proven by the 0.0.2 forensics: WT applies pres WITHOUT
# reorder, so a SingleSubst on these names executes there) but is reached
# only after the ligature lookup in shaping renderers. The init forms are
# included so word-initial ে/ৈ (init swaps bn_ekaar->bn_initekaar) are
# covered by the restore in WT regardless of whether WT applies init.
PREBASE_SHIFT_ALL = PREBASE_SHIFT | {"bn_initekaar", "bn_initaikaar"}

# Kar (vowel-sign) glyphs are NEVER x-squeezed: author directive
# 2026-08-31 — keep native ink, center it in the cell (advance = cell),
# letting it overflow symmetrically into neighboring bearings instead of
# distorting the sign. Excluded: bn_okaar/bn_aukaar are independent
# VOWELS (base letters), not matras — those squeeze normally.
def is_kar(name):
    return (name.endswith("kaar")
            and not name.endswith(("okaar", "aukaar"))) or name == "bn_aumark"


class RoundingPen:
    """Wrap a pen so all coordinates are ints (TrueType requirement)."""

    def __init__(self, pen):
        self._pen = pen

    def __getattr__(self, name):
        return getattr(self._pen, name)

    def moveTo(self, pt):
        self._pen.moveTo((round(pt[0]), round(pt[1])))

    def lineTo(self, pt):
        self._pen.lineTo((round(pt[0]), round(pt[1])))

    def qCurveTo(self, *pts):
        self._pen.qCurveTo(*[(round(x), round(y)) for x, y in pts])

    def curveTo(self, *pts):
        self._pen.curveTo(*[(round(x), round(y)) for x, y in pts])


def glyph_bbox(glyf, name, cache):
    """Ink bbox of a glyph with composites resolved (may recurse)."""
    if name in cache:
        return cache[name]
    g = glyf[name]
    xs, ys = [], []
    if g.isComposite():
        for comp in g.components:
            cx0, cy0, cx1, cy1 = glyph_bbox(glyf, comp.glyphName, cache)
            if getattr(comp, "transform", None):
                sys.exit("scaled composite components not supported "
                         f"({name} -> {comp.glyphName}); none existed at "
                         "authoring time — extend if the base changes")
            xs += [cx0 + comp.x, cx1 + comp.x]
            ys += [cy0 + comp.y, cy1 + comp.y]
    elif g.numberOfContours > 0:
        for x, y in g.coordinates:
            xs.append(x)
            ys.append(y)
    bbox = (min(xs), min(ys), max(xs), max(ys)) if xs else None
    cache[name] = bbox
    return bbox


def transform_glyph(glyf, orig, name, sx, dx, target=None):
    """Rebuild glyph as a simple (decomposed) glyph under (sx, dx) x-map."""
    pen = TTGlyphPen(None)
    tpen = TransformPen(RoundingPen(pen), (sx, 0, 0, 1, dx, 0))
    draw_decomposed(orig[name], orig, tpen)
    glyf[target or name] = pen.glyph()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--cell", type=int, default=None,
                    help="cell width in units (default: auto = median "
                         "advance of the font's own glyphs)")
    ap.add_argument("--ink-cap", type=float, default=0.92)
    ap.add_argument("--family", default="Siyam Rupali Mono")
    ap.add_argument("--subfamily", default="Regular")
    ap.add_argument("--version", default="1.100")
    ap.add_argument("--prebase-shift", action="store_true",
                    help="shift pre-base matra/above-mark ink one cell left "
                         "(Windows Terminal-native variant: WT draws "
                         "codepoint-order with no shaping)")
    ap.add_argument("--duo", action="store_true",
                    help="duospaced EDITOR build (docs/PLAN_DUO_MONO.md): "
                         "Latin/neutral glyphs convert to --latin-cell; "
                         "every bn_* glyph's art AND advance scale by one "
                         "global factor so the Bengali design keeps all "
                         "native interlocks (median letter lands on "
                         "--beng-cell). dx stays 0: the stream geometry is "
                         "the original font's, enlarged.")
    ap.add_argument("--latin-cell", type=int, default=None,
                    help="[duo] Latin/neutral cell (default upem//2)")
    ap.add_argument("--beng-cell", type=int, default=None,
                    help="[duo] nominal Bengali letter advance (default "
                         "2x latin-cell; drives the zoom factor only)")
    args = ap.parse_args()

    f = TTFont(args.infile)
    upm = f["head"].unitsPerEm
    if args.cell is None:
        # auto width: the median advance of the font's own advance-bearing
        # glyphs — the most neutral mono cell for THIS design (half the
        # glyphs pad, half trim, squeeze spread evenly). Pass --cell to
        # override (e.g. 1024 = classic 0.5em, 1536 = 0.75em airy).
        cls0 = f["GDEF"].table.GlyphClassDef.classDefs
        cand = sorted(f["hmtx"][g][0] for g in f.getGlyphOrder()
                      if cls0.get(g) != 3 and f["hmtx"][g][0] >= MARK_ADV_FLOOR)
        args.cell = int(statistics.median(cand)) if cand else upm // 2
        print(f"cell auto = median advance {args.cell} "
              f"({args.cell/upm:.2f} em)")
    cell = args.cell
    ink_max = args.ink_cap * cell

    glyf = f["glyf"]
    # snapshot: glyf[name] = glyph appends to the LIVE order list; adding
    # the _shaped copies mid-loop would otherwise grow the iteration
    names = list(f.getGlyphOrder())
    # Freeze original glyph objects so composite decomposition never sees a
    # already-condensed component (would double-scale).
    orig = {n: glyf[n] for n in names}

    gdef = f["GDEF"].table
    gdef_classes = gdef.GlyphClassDef.classDefs if gdef.GlyphClassDef else {}

    if args.duo:
        lat = args.latin_cell or upm // 2
        beng_target = args.beng_cell or 2 * lat
        bn_pool = [n for n in names if n.startswith("bn_")
                   and gdef_classes.get(n) != 3
                   and f["hmtx"][n][0] >= MARK_ADV_FLOOR
                   and not is_kar(n) and n not in PREBASE_SHIFT_ALL]
        med = int(statistics.median(sorted(f["hmtx"][n][0] for n in bn_pool)))
        s = beng_target / med
        print(f"duo: latin cell {lat}, bengali zoom s={s:.4f} "
              f"(= {beng_target}/{med}), anchor pool n={len(bn_pool)}")
    else:
        lat = cell
        s = 1.0

    bbox_cache = {}
    factors = {}  # name -> (sx, dx)
    stats = {"untouched_mark": 0, "identity": 0, "condensed": 0}
    squeeze = []

    for name in names:
        adv = f["hmtx"][name][0]
        if gdef_classes.get(name) == 3 or adv < MARK_ADV_FLOOR:
            if args.duo:
                # marks zoom with the Bengali design; ~0 advance kept,
                # GPOS mark anchors scaled below via factors
                if glyph_bbox(glyf, name, bbox_cache) is not None:
                    transform_glyph(glyf, orig, name, s, 0)
                    a0, l0 = f["hmtx"][name]
                    f["hmtx"][name] = (a0, round(s * l0))
                    factors[name] = (s, 0.0)
                else:
                    factors[name] = None
                stats["mark_zoom"] = stats.get("mark_zoom", 0) + 1
            else:
                stats["untouched_mark"] += 1
                factors[name] = None
            continue
        if args.duo and name.startswith("bn_"):
            # uniform zoom: art and advance scale together, left-aligned
            # (dx=0) so every designed interlock survives exactly.
            if glyph_bbox(glyf, name, bbox_cache) is None:
                f["hmtx"][name] = (lat, 0)
                factors[name] = None
                stats["identity"] += 1
                continue
            transform_glyph(glyf, orig, name, s, 0)
            lsb0 = f["hmtx"][name][1]
            f["hmtx"][name] = (round(adv * s), round(s * lsb0))
            factors[name] = (s, 0.0)
            stats["bengali_zoom"] = stats.get("bengali_zoom", 0) + 1
            continue
        tcell = lat if args.duo else cell
        tink = tcell * args.ink_cap
        bb = glyph_bbox(glyf, name, bbox_cache)
        if bb is None:  # empty glyph (space & friends): just set the cell
            f["hmtx"][name] = (tcell, 0)
            factors[name] = None
            stats["identity"] += 1
            continue
        x0, _, x1, _ = bb
        bw = x1 - x0
        if not args.duo and (is_kar(name) or name in PREBASE_SHIFT_ALL):
            # 0.0.6 (author directive): matras keep the ORIGINAL ART
            # VERBATIM - no scale, no move. Compare with original Siyam
            # Rupali: the VOLT-era design already positions the ink
            # (negative bearings, overlay bars) for codepoint-order
            # drawing. Advance = the CELL (author 2026-09-03: give i-kaar
            # & co a full 1-col advance so a shaped CV pair fills both
            # charged columns exactly — natural small advances leave a
            # snap gap after every cluster). Overflow cases (o-kar/
            # au-kar ink 2577/2565 > cell) are accepted as-is.
            factors[name] = None  # matras are not MarkToBase bases
            orig_lsb = f["hmtx"][name][1]
            f["hmtx"][name] = (tcell, orig_lsb)
            stats["kar_verbatim"] = stats.get("kar_verbatim", 0) + 1
            continue
        sx = min(1.0, tink / bw)
        # 0.0.7 (author directive): scale by the ADVANCE ratio about the
        # glyph's own center — never re-center the ink. Old advance 800 ->
        # cell 1000 adds (1000-800)/2 = 100 to each bearing; 1200 -> 1000
        # removes 100 from each; ink that still cannot fit compresses
        # further, but the glyph's center stays exactly at the cell center.
        # Preserving the advance-box center keeps the original font's
        # rhythm (each glyph shrinks by its own advance ratio) and keeps
        # designed asymmetries (f/j/comma lean) intact.
        A = adv
        sx = min(1.0, tcell / A, tink / bw)
        dx = tcell / 2.0 - sx * (A / 2.0)
        factors[name] = (sx, dx)
        if sx < 1.0:
            stats["condensed"] += 1
            squeeze.append((sx, name))
        else:
            stats["identity"] += 1
        transform_glyph(glyf, orig, name, sx, dx)
        f["hmtx"][name] = (tcell, round(sx * x0 + dx))

    squeeze.sort()
    print(f"cell={cell} ink_max={ink_max:.0f} upm={upm}")
    print(f"marks untouched: {stats['untouched_mark']}, "
          f"identity: {stats['identity']}, condensed: {stats['condensed']}")
    if squeeze:
        sx_med = squeeze[len(squeeze) // 2][0]
        print(f"condense factors: min={squeeze[0][0]:.3f} "
              f"median={sx_med:.3f} max={squeeze[-1][0]:.3f}")
        print("worst 15:", ", ".join(f"{n}={s:.2f}" for s, n in squeeze[:15]))

    # --- GPOS: move MarkToBase base anchors with each base's transform ---
    gp = f["GPOS"].table
    moved = 0
    for lk in gp.LookupList.Lookup:
        for st in lk.SubTable:
            ext = getattr(st, "ExtSubTable", None)
            if ext is not None:
                st = ext
            if st.__class__.__name__ != "MarkBasePos":
                continue
            for i, gname in enumerate(st.BaseCoverage.glyphs):
                fct = factors.get(gname)
                if not fct:
                    continue
                sx, dx = fct
                rec = st.BaseArray.BaseRecord[i]
                for anchor in rec.BaseAnchor:
                    # move on EVERY transformed base: sx condenses, but dx
                    # recenters even identity (sx=1) glyphs — skipping dx
                    # left marks at the original x while ink re-centered
                    # (exposed at cell 1536/2048 where most glyphs are
                    # identity; কু drifted -788 units off-base).
                    if anchor is not None:
                        anchor.XCoordinate = round(sx * anchor.XCoordinate + dx)
                        moved += 1
            if args.duo:
                # duo zooms mark ART, so the mark-side anchors must zoom too
                for i, gname in enumerate(st.MarkCoverage.glyphs):
                    fct = factors.get(gname)
                    if fct:
                        anchor = st.MarkArray.MarkRecord[i].MarkAnchor
                        if anchor is not None:
                            anchor.XCoordinate = round(fct[0] * anchor.XCoordinate + fct[1])
                            moved += 1
            continue
    print(f"GPOS base anchors moved: {moved}")

    # --- metrics & flags ---
    f["hhea"].advanceWidthMax = max(f["hmtx"][n][0] for n in f.getGlyphOrder())
    f["hhea"].numberOfHMetrics = len(f.getGlyphOrder())
    f["OS/2"].xAvgCharWidth = lat
    f["OS/2"].fsType = 0  # our own font; clears the inherited restricted bit
    f["OS/2"].panose.bProportion = 9  # monospaced
    f["post"].isFixedPitch = 1
    if args.duo:
        # plan Step 2: vertical bounds must cover the ink (base declares
        # 2360/-731 but ink reaches 2493/-921 — line-height-1.0 renderers
        # would clip reph/uku stacks). Win metrics +2% pad; typo metrics
        # keep the design values.
        ymax = max(bb[3] for bb in bbox_cache.values() if bb)
        ymin = min(bb[1] for bb in bbox_cache.values() if bb)
        asc = max(f["hhea"].ascent, int(ymax * 1.02))
        dsc = max(-f["hhea"].descent, int(-ymin * 1.02))
        f["hhea"].ascent = asc
        f["hhea"].descent = -dsc
        f["OS/2"].usWinAscent = max(f["OS/2"].usWinAscent, asc)
        f["OS/2"].usWinDescent = max(f["OS/2"].usWinDescent, dsc)
        print(f"duo vertical bounds: asc {asc} desc -{dsc} "
              f"(ink {ymin}..{ymax})")

    # --- names & version ---
    fam, sub = args.family, args.subfamily
    ps = f"{fam.replace(' ', '')}-{sub}"
    full = f"{fam} {sub}"
    ver = f"Version {args.version}"
    major, minor = args.version.split(".")[:2]
    f["head"].fontRevision = float(f"{major}.{minor}")
    name = f["name"]
    for nid, val in ((1, fam), (2, sub), (3, f"{ps};{ver};mono-term"),
                     (4, full), (5, ver), (6, ps), (16, fam), (17, sub)):
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)

    # --- drop stale tables (old widths/bitmaps/hints) ---
    for tag in ("EBDT", "EBLC", "LTSH", "VDMX", "hdmx", "kern",
                "cvt ", "fpgm", "prep", "gasp"):
        if tag in f:
            del f[tag]
    # embedded-bitmap heads in other tables are gone with EBDT/EBLC;
    # keep GDEF/GSUB/GPOS untouched.

    f.save(args.outfile)
    print(f"OK: {args.outfile}")


if __name__ == "__main__":
    main()
