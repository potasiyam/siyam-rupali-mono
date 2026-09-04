#!/usr/bin/env python3
"""Render test strings with HB shaping + FreeType raster and a cell grid.

Simulates what a terminal shows: every advance = one cell. Produces a PNG
per (font, string) pair so spacing problems can be seen, not guessed.

--unshaped: skip HarfBuzz and draw cmap glyphs in codepoint order with
their font advances -- the Windows Terminal rendering model (measured
2026-08-31: WT does no cross-codepoint shaping for Bengali).
"""
import argparse
from pathlib import Path

import freetype
from PIL import Image, ImageDraw
from fontTools.ttLib import TTFont
from vharfbuzz import Vharfbuzz

STRINGS = [
    "আমার নাম সিয়াম",
    "কা কি কী কে কৈ কো কৌ",
    "কাকিকীকেকৈকোকৌ",
    "যন্ত্র সংস্কৃত আত্মহত্যা বিদ্যালয়",
]


def shape_glyphs(font_path, text, unshaped):
    """Return [(glyph_name, x_advance_units, x_offset_units)]."""
    if unshaped:
        tt = TTFont(font_path)
        cmap = tt.getBestCmap()
        out = []
        for ch in text:
            name = cmap.get(ord(ch))
            if name is None:
                continue
            out.append((name, tt["hmtx"][name][0], 0))
        return out
    vhb = Vharfbuzz(str(font_path))
    buf = vhb.shape(text, {"script": "beng", "language": "ben"})
    return [(vhb.hbfont.glyph_to_string(i.codepoint), pos.x_advance,
             pos.x_offset)
            for i, pos in zip(buf.glyph_infos, buf.glyph_positions)]


def render(font_path, text, cell_units, upem, out_png, cell_px=36,
           grid=True, unshaped=False):
    glyphs = shape_glyphs(font_path, text, unshaped)
    names = [g[0] for g in glyphs]

    em_px = cell_px * upem / cell_units
    face = freetype.Face(str(font_path))
    face.set_pixel_sizes(0, round(em_px))
    face.select_charmap(freetype.FT_ENCODING_IDENTITY) if hasattr(
        freetype, "FT_ENCODING_IDENTITY") else None

    baseline = int(cell_px * 1.5)
    total_units = sum(a for _, a, _ in glyphs)
    width_px = int(total_units / cell_units * cell_px) + 2 * cell_px
    height_px = int(cell_px * 2.2)
    img = Image.new("RGB", (width_px, height_px), (24, 24, 24))
    draw = ImageDraw.Draw(img)

    x = cell_px
    if grid:
        for _, adv, _ in glyphs:
            for _ in range(max(1, round(adv / cell_units))):
                x2 = x + cell_px
                draw.line([(x2, 0), (x2, height_px)],
                          fill=(70, 20, 20), width=1)
                x = x2

    pen_units = 0
    for name, adv, xoff in glyphs:
        gid = face.get_name_index(name.encode("ascii"))
        if gid == 0:
            print(f"  !! glyph name not found: {name}")
        face.load_glyph(gid, freetype.FT_LOAD_RENDER
                        | freetype.FT_LOAD_DEFAULT)
        bm = face.glyph.bitmap
        pen_px = cell_px + pen_units / cell_units * cell_px
        dx = (pen_px + face.glyph.bitmap_left
              + xoff / cell_units * cell_px)
        dy = baseline - face.glyph.bitmap_top
        if bm.width:
            glyph_img = Image.frombytes("L", (bm.width, bm.rows),
                                        bytes(bm.buffer))
            ink = Image.new("RGB", glyph_img.size, (230, 230, 230))
            img.paste(ink, (int(dx), int(dy)), glyph_img)
        pen_units += adv

    draw.line([(0, baseline), (width_px, baseline)], fill=(40, 90, 40))
    img.save(out_png)
    cells = [round(a / cell_units, 2) for _, a, _ in glyphs]
    print(f"{Path(out_png).name}: {len(names)} glyphs, cells={cells}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("--cell", type=int, required=True)
    ap.add_argument("--tag", default="probe")
    ap.add_argument("--unshaped", action="store_true")
    args = ap.parse_args()

    outdir = Path("build/probe")
    outdir.mkdir(parents=True, exist_ok=True)
    upem = TTFont(args.font)["head"].unitsPerEm
    mode = "unshaped" if args.unshaped else "shaped"
    for i, text in enumerate(STRINGS):
        render(args.font, text, args.cell, upem,
               outdir / f"{args.tag}_{mode}_{i}.png", unshaped=args.unshaped)


if __name__ == "__main__":
    main()
