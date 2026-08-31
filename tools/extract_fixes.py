#!/usr/bin/env python3
"""Extract hand-edited glyphs from a designer-worked TTF into a fixes fragment.

Workflow (see docs/FIXES.md): the designer copies a pipeline build, fixes
glyphs in FontLab/FontForge, saves the TTF. This tool diffs that file
against the pipeline build (outline geometry only — hint bytecode is
ignored, we re-autohint) and writes the changed glyphs into a minimal
"fixes fragment" TTF that apply_fixes.py merges into future builds.

The fragment reuses the edited font's own head/post/name/hhea objects and
prunes glyf/hmtx to the changed set — post 2.0 keeps the bn_* names alive
in the fragment (without it fontTools synthesizes glyphNN names).

Usage:
  extract_fixes.py EDITED.ttf REFERENCE.ttf OUT_FRAGMENT.ttf
"""
import sys

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from mono_convert import draw_decomposed


def glyph_signature(font, name):
    """Geometry signature: recorded outline ops, composites decomposed
    (an editor re-linking a component is still caught)."""
    glyf = font["glyf"]
    rec = RecordingPen()
    try:
        draw_decomposed(glyf[name], glyf, rec)
    except Exception:
        return "UNREADABLE"
    return repr(rec.value)


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    edited_path, ref_path, out_path = sys.argv[1:4]

    edited = TTFont(edited_path)
    ref = TTFont(ref_path)
    ref_names = set(ref.getGlyphOrder())
    # Force-decompile every table we will later prune — lazy loading after
    # the order is pruned would IndexError (hmtx decompile reads it).
    for tag in ("glyf", "hmtx", "maxp", "hhea", "head", "post", "name"):
        edited[tag]

    changed = [n for n in ref.getGlyphOrder()
               if n != ".notdef"
               and glyph_signature(edited, n) != glyph_signature(ref, n)]

    extra = [g for g in edited.getGlyphOrder()
             if g not in ref_names and g != ".notdef"]
    if extra:
        print("WARNING: new glyphs (unsupported by the fixes layer, dropped):")
        for g in extra:
            print("  +", g)

    if not changed:
        print("No changed glyphs found — nothing to extract.")
        return 0

    keep = [".notdef"] + changed
    # Reuse the edited font's own table objects, pruned to the changed set.
    edited["glyf"].glyphs = {n: edited["glyf"][n] for n in keep}
    edited["glyf"].glyphOrder = keep
    edited.setGlyphOrder(keep)  # font-level order (maxp.recalc reads it)
    edited["hmtx"].metrics = {n: edited["hmtx"][n] for n in keep}
    edited["maxp"].numGlyphs = len(keep)
    edited["hhea"].numberOfHMetrics = len(keep)
    for tag in ("GSUB", "GPOS", "GDEF", "cmap", "cvt ", "fpgm", "prep",
                "gasp", "EBDT", "EBLC", "kern", "hdmx", "LTSH", "VDMX"):
        if tag in edited:
            del edited[tag]
    edited.save(out_path)

    print(f"{len(changed)} changed glyph(s) -> {out_path}:")
    for name in changed:
        adv, lsb = edited["hmtx"][name]
        print(f"  {name}  adv={adv} lsb={lsb}")
    print(f"Next: rebuild pipeline, then: apply_fixes.py BUILD.ttf {out_path}")


if __name__ == "__main__":
    main()
