#!/usr/bin/env python3
"""Render test strings with HB shaping + FreeType raster and a cell grid.

Simulates what a terminal shows: every advance = one cell. Produces a PNG
per (font, string) pair so spacing problems can be seen, not guessed.
"""
import sys
from pathlib import Path

import freetype
from PIL import Image, ImageDraw
from vharfbuzz import Vharfbuzz

CELLS_PER_FONT = {"Wide": 1536, "Edit": 1536}
STRINGS = [
    "আমার নাম সিয়াম",
    "কা কি কী কে কৈ কো কৌ",
]


def render(font_path, text, cell_units, upem, out_png, cell_px=36,
           grid=True):
    vhb = Vharfbuzz(str(font_path))
    buf = vhb.shape(text, {"script": "beng", "language": "ben"})
    names = [vhb.hbfont.glyph_to_string(i.codepoint) for i in buf.glyph_infos]

    em_px = cell_px * upem / cell_units
    face = freetype.Face(str(font_path))
    face.set_pixel_sizes(0, round(em_px))

    asc, desc = face.ascender, face.descender  # 26.6 fixed point
    asc = asc >> 6
    desc = desc >> 6
    pen_units = 0
    advance_units = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        advance_units.append(pos.x_advance)
        pen_units += pos.x_advance

    total_cells_units = pen_units
    width_px = int(total_cells_units / cell_units * cell_px) + 2 * cell_px
    height_px = int(cell_px * 2.2)
    baseline = int(cell_px * 1.5)
    img = Image.new("RGB", (width_px, height_px), (24, 24, 24))
    draw = ImageDraw.Draw(img)

    # cell grid from x=cell_px, one cell per advance unit-block
    x = cell_px
    if grid:
        for adv in advance_units:
            n = round(adv / cell_units)
            for k in range(n):
                x2 = x + cell_px
                draw.line([(x2, 0), (x2, height_px)],
                          fill=(70, 20, 20), width=1)
                x = x2

    # rasterize each glyph at cumulative advance
    pen_units = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gid = info.codepoint
        face.load_glyph(gid, freetype.FT_LOAD_RENDER
                        | freetype.FT_LOAD_DEFAULT)
        bm = face.glyph.bitmap
        pen_px = cell_px + pen_units / cell_units * cell_px
        dx = pen_px + face.glyph.bitmap_left + pos.x_offset / cell_units * cell_px
        dy = baseline - face.glyph.bitmap_top - pos.y_offset / cell_units * cell_px
        if bm.width:
            glyph_img = Image.frombytes("L", (bm.width, bm.rows), bytes(bm.buffer))
            black = Image.new("RGB", glyph_img.size, (230, 230, 230))
            img.paste(black, (int(dx), int(dy)), glyph_img)
        pen_units += pos.x_advance

    draw.line([(0, baseline), (width_px, baseline)], fill=(40, 90, 40))
    img.save(out_png)
    cells = [round(a / cell_units, 2) for a in advance_units]
    print(f"{Path(out_png).name}: {len(names)} glyphs, cells/adv={cells}")
    print("  glyphs:", " ".join(names))


def main():
    outdir = Path("build/probe")
    outdir.mkdir(parents=True, exist_ok=True)
    fonts = {
        "Wide": Path("build/SiyamRupaliMono-Wide.ttf"),
        "Edit": Path("build/SiyamRupaliMono-Edit.ttf"),
    }
    for tag, path in fonts.items():
        from fontTools.ttLib import TTFont
        upem = TTFont(path)["head"].unitsPerEm
        cell = CELLS_PER_FONT[tag]
        for i, text in enumerate(STRINGS):
            render(path, text, cell, upem,
                   outdir / f"{tag}_{i}.png")


if __name__ == "__main__":
    main()
