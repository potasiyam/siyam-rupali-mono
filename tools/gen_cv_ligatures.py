#!/usr/bin/env python3
"""Generate CV ligatures so spacing-matra syllables fit ONE terminal cell.

Problem: the seven spacing matras (ি ী ে ৈ ো ৌ া) each carry their own
advance, so কি = 2 cells and কো = 3 cells while a terminal grants every
Bengali cluster exactly 1 cell (wcwidth). This tool composes base+matra
art (from the ORIGINAL proportional font) into single ligature glyphs
and adds GSUB ligature rules that consume the reordered stream
(e.g. কি shapes to [bn_ikaar, bn_ka] -> sub bn_ikaar bn_ka by bn_ka_ikaar).

v1 scope: bare consonant bases only. Conjunct + matra (e.g. ক্ষি) keeps
the multi-cell overflow and is the documented v2 work item.

Usage: gen_cv_ligatures.py ORIGINAL.ttf CONVERTED.ttf OUT.ttf [--smoke]
       [--cv-cell N] [--layout faithful|pack] [--ink-cap F] [--gap N]
       [--family NAME] [--version X.Y]

--cv-cell 1024 (default): legacy strict build — fixed sub-regions inside a
  single 1024-unit cell (kept for reproducibility of the v1.100 build).
Wider --cv-cell (e.g. 1536): parts laid out at a UNIFORM scale centered
  in the frame. Two layouts:
  faithful (default): parts keep their ORIGINAL pen offsets — the
    designed matra/base interlocks (matra inks legitimately overlap the
    base; bn_iikaar's ink is ~3x its advance) are preserved exactly.
  pack: bbox side-by-side with --gap air between parts (legacy).
Pre-base matras have TWO art variants (GSUB 'init' feature swaps
bn_ekaar->bn_initekaar word-initially); rules are emitted for BOTH, the
standard form getting a separate ligature glyph suffixed _std.
"""
import argparse
import sys
from pathlib import Path

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from mono_convert import RoundingPen, draw_decomposed, glyph_bbox

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


# Pre-base matras have TWO art variants in this font: the standard form and
# the word-initial form substituted by the GSUB 'init' feature (verified in
# the binary: init maps bn_ekaar->bn_initekaar, bn_aikaar->bn_initaikaar).
# Ligature rules must cover BOTH, otherwise mid-word ে/ৈ clusters (init
# not applied) fall back to two full cells — the ইউকে vs কে bug of
# 2026-08-31. The variants carry different outlines, so each gets its own
# ligature glyph, suffixed _std for the standard (non-init) form.
PRE_VARIANTS = {
    "bn_initekaar": ("bn_ekaar", "_std"),
    "bn_initaikaar": ("bn_aikaar", "_std"),
}

# glyphs that can appear as the pre-base matra part of a stream
PRE_GLYPHS = {"bn_ikaar", "bn_initekaar", "bn_ekaar",
              "bn_initaikaar", "bn_aikaar"}


def layout_proportional(orig, names, bbox_cache, frame, gap=30):
    """Lay parts left-to-right at ONE uniform scale, centered in `frame`.

    Uniform scale keeps stroke weight identical between base and matra
    (the per-part squeeze in the legacy regions made thin/thick mismatches
    inside a single ligature — the 'too thin' review of 2026-08-31).
    """
    boxes = [glyph_bbox(orig, n, bbox_cache) for n in names]
    widths = [b[2] - b[0] for b in boxes]
    avail = frame - gap * (len(names) - 1)
    s = min(1.0, avail / sum(widths))
    x = (frame - (s * sum(widths) + gap * (len(names) - 1))) / 2
    parts = []
    for name, box, w in zip(names, boxes, widths):
        parts.append((name, (s, x - s * box[0])))
        x += s * w + gap
    return parts, s


def layout_faithful(ofont, names, bbox_cache, frame):
    """Place parts at their ORIGINAL pen offsets, scale the assembly.

    The original advance-based layout already encodes the designed
    interlock between base and matra (e.g. bn_iikaar's ink is ~3x its
    advance because the curl sweeps across the base's x-range; matra
    strokes JOIN the base — that is the script's design, not collision).
    Bbox side-by-side packing double-counts those overlap zones and
    severs the connections; this layout preserves them exactly.

    Scale = frame / advance-span; the scaled ink block is centered. If
    the ink block (curls can overshoot the span) exceeds the frame, it
    is shrunk to fit.
    """
    hmtx = ofont["hmtx"]
    pens = []
    pen = 0.0
    for n in names:
        pens.append(pen)
        pen += hmtx[n][0]
    span = pen
    boxes = [glyph_bbox(ofont["glyf"], n, bbox_cache) for n in names]
    x0s = [p + b[0] for p, b in zip(pens, boxes)]
    x1s = [p + b[2] for p, b in zip(pens, boxes)]
    ink_lo, ink_hi = min(x0s), max(x1s)
    s = min(1.0, frame / span, frame / (ink_hi - ink_lo))
    lo = ink_lo * s
    dx = (frame - (ink_hi - ink_lo) * s) / 2 - lo
    parts = [(n, (s, pens[i] * s + dx)) for i, n in enumerate(names)]
    return parts, s


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
    ap.add_argument("--cv-cell", type=int, default=1024,
                    help="advance per ligature glyph: 1024 (strict, "
                         "fixed regions) or wider (uniform scale)")
    ap.add_argument("--ink-cap", type=float, default=0.92,
                    help="fraction of cv-cell usable as ink (wide mode)")
    ap.add_argument("--gap", type=int, default=30,
                    help="units between parts in wide mode")
    ap.add_argument("--layout", choices=("faithful", "pack"), default="faithful",
                    help="wide-mode part layout: faithful = original pen "
                         "offsets (preserves designed matra interlocks, "
                         "default); pack = bbox side-by-side with --gap")
    ap.add_argument("--family", default=None,
                    help="rename family (e.g. 'Siyam Rupali Mono Wide')")
    ap.add_argument("--version", default=None,
                    help="version string, e.g. 1.101")
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
    scales = []

    def make_ligature(stream, out_name):
        """Lay out, build, and register one CV ligature glyph + rule."""
        nonlocal made
        if args.cv_cell == 1024:
            # legacy strict layout: fixed hand-tuned sub-regions
            # (kept for reproducibility of the v1.100 build)
            if len(stream) == 3:
                regs = REGIONS[3]
                parts = [
                    (stream[0], part_transform(oglyf, stream[0], regs["pre"], bbox_cache)),
                    (stream[1], part_transform(oglyf, stream[1], regs["base"], bbox_cache)),
                    (stream[2], part_transform(oglyf, stream[2], regs["post"], bbox_cache)),
                ]
            elif stream[0] in PRE_GLYPHS:
                regs = REGIONS[2]
                parts = [
                    (stream[0], part_transform(oglyf, stream[0], regs["pre"], bbox_cache)),
                    (stream[1], part_transform(oglyf, stream[1], regs["base"], bbox_cache)),
                ]
            else:
                regs = REGIONS[2]
                parts = [
                    (stream[0], part_transform(oglyf, stream[0], regs["post_base"],
                                               bbox_cache)),
                    (stream[1], part_transform(oglyf, stream[1], regs["post"],
                                               bbox_cache)),
                ]
            s = 1.0
        else:
            # wide layout
            if args.layout == "faithful":
                parts, s = layout_faithful(orig, stream, bbox_cache,
                                           int(args.ink_cap * args.cv_cell))
            else:
                parts, s = layout_proportional(
                    oglyf, stream, bbox_cache,
                    int(args.ink_cap * args.cv_cell), gap=args.gap)
            scales.append(s)
        glyph, lsb = build_ligature(oglyf, parts, bbox_cache)
        glyf[out_name] = glyph  # auto-appends to glyphOrder (verified)
        font["hmtx"].metrics[out_name] = (args.cv_cell, lsb)
        existing.add(out_name)
        rules.append((stream, out_name))
        made += 1

    for base in bases:
        for suffix, pre, post in PATTERNS:
            new_name = f"{base}_{suffix}"
            if new_name in existing:
                print(f"  skip {new_name} (exists)")
                continue
            stream = [p for p in (pre, base, post) if p]
            make_ligature(stream, new_name)
            if pre in PRE_VARIANTS:
                alias, tag = PRE_VARIANTS[pre]
                vstream = [alias if g == pre else g for g in stream]
                vname = new_name + tag
                if vname not in existing:
                    make_ligature(vstream, vname)

    order = font.getGlyphOrder()
    assert len(order) == len(set(order)) == len(glyf.glyphs), (
        f"glyph order desync: {len(order)} names / {len(glyf.glyphs)} glyphs")
    print(f"generated {made} CV ligature glyphs "
          f"({len(order)} glyphs total, advance {args.cv_cell})")
    if scales:
        scales.sort()
        print(f"uniform scale: min={scales[0]:.3f} "
              f"median={scales[len(scales)//2]:.3f} max={scales[-1]:.3f}")

    if args.family or args.version:
        fam = args.family or "Siyam Rupali Mono"
        sub = "Regular"
        ps = fam.replace(" ", "") + "-" + sub
        full = f"{fam} {sub}"
        ver = f"Version {args.version or '1.100'}"
        name = font["name"]
        for nid, val in ((1, fam), (2, sub), (3, f"{ps};{ver};mono-term"),
                         (4, full), (5, ver), (6, ps), (16, fam), (17, sub)):
            name.setName(val, nid, 3, 1, 0x409)
            name.setName(val, nid, 1, 0, 0)
        major, minor = (args.version or "1.100").split(".")[:2]
        font["head"].fontRevision = float(f"{major}.{minor}")

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
