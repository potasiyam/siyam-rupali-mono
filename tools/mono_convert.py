#!/usr/bin/env python3
"""Convert proportional Siyam Rupali into a strict-terminal-mono font.

Model: every advance-bearing glyph occupies exactly ONE cell of `cell`
units (default: upem/2 = 1024). Outlines are x-condensed (y untouched) to
fit inside `ink_cap * cell`, then recentered in the cell. Marks (GDEF
class 3 or advance < mark_floor) keep their near-zero advances. Kar
(vowel-sign) glyphs are exempt from squeezing (is_kar). GPOS MarkToBase
anchors move with each base glyph's transform. Legacy tables that encode
the OLD advances/bitmaps/hints are dropped.

This script is step 1 of the pipeline for BOTH deliverables:
  - terminal build: step 2 = gen_cv_ligatures.py (CV ligatures, 1 cell)
  - editor build:   no step 2 (matras keep their own full cell)
See AGENTS.md / docs/TERMINAL.md.

Usage:
  mono_convert.py IN.ttf OUT.ttf [--cell N] [--ink-cap 0.92]
      [--family "Siyam Rupali Mono"] [--version 1.100]
"""
import argparse
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


def transform_glyph(glyf, orig, name, sx, dx):
    """Rebuild glyph as a simple (decomposed) glyph under (sx, dx) x-map."""
    pen = TTGlyphPen(None)
    tpen = TransformPen(RoundingPen(pen), (sx, 0, 0, 1, dx, 0))
    draw_decomposed(orig[name], orig, tpen)
    glyf[name] = pen.glyph()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--cell", type=int, default=None,
                    help="cell width in units (default: upem/2)")
    ap.add_argument("--ink-cap", type=float, default=0.92)
    ap.add_argument("--family", default="Siyam Rupali Mono")
    ap.add_argument("--subfamily", default="Regular")
    ap.add_argument("--version", default="1.100")
    args = ap.parse_args()

    f = TTFont(args.infile)
    upm = f["head"].unitsPerEm
    cell = args.cell or upm // 2
    ink_max = args.ink_cap * cell

    glyf = f["glyf"]
    names = f.getGlyphOrder()
    # Freeze original glyph objects so composite decomposition never sees a
    # already-condensed component (would double-scale).
    orig = {n: glyf[n] for n in names}

    gdef = f["GDEF"].table
    gdef_classes = gdef.GlyphClassDef.classDefs if gdef.GlyphClassDef else {}

    bbox_cache = {}
    factors = {}  # name -> (sx, dx)
    stats = {"untouched_mark": 0, "identity": 0, "condensed": 0}
    squeeze = []

    for name in names:
        adv = f["hmtx"][name][0]
        if gdef_classes.get(name) == 3 or adv < MARK_ADV_FLOOR:
            stats["untouched_mark"] += 1
            factors[name] = None
            continue
        bb = glyph_bbox(glyf, name, bbox_cache)
        if bb is None:  # empty glyph (space & friends): just set the cell
            f["hmtx"][name] = (cell, 0)
            factors[name] = None
            stats["identity"] += 1
            continue
        x0, _, x1, _ = bb
        bw = x1 - x0
        if is_kar(name):
            # kars: never squeeze — native ink, centered (author directive)
            sx = 1.0
        else:
            sx = min(1.0, ink_max / bw)
        # recenter ink in the cell
        dx = (cell - sx * bw) / 2 - sx * x0
        factors[name] = (sx, dx)
        if sx < 1.0:
            stats["condensed"] += 1
            squeeze.append((sx, name))
        else:
            stats["identity"] += 1
        transform_glyph(glyf, orig, name, sx, dx)
        f["hmtx"][name] = (cell, round(sx * x0 + dx))

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
    print(f"GPOS base anchors moved: {moved}")

    # --- metrics & flags ---
    f["hhea"].advanceWidthMax = cell
    f["hhea"].numberOfHMetrics = len(names)
    f["OS/2"].xAvgCharWidth = cell
    f["OS/2"].fsType = 0  # our own font; clears the inherited restricted bit
    f["OS/2"].panose.bProportion = 9  # monospaced
    f["post"].isFixedPitch = 1

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
