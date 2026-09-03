from vharfbuzz import Vharfbuzz
from fontTools.ttLib import TTFont
p = "build/SiyamRupaliMono-Proof.ttf"
tt = TTFont(p)
cell = tt["hfea"].advanceWidthMax if "hfea" in tt else tt["hhea"].advanceWidthMax
name = tt["name"]
fam = name.getDebugName(1); ver = name.getDebugName(5)
vhb = Vharfbuzz(p)
cases = {
    "ka": "\u0995", "kaa": "\u0995\u09be", "ki": "\u0995\u09bf",
    "kang": "\u0995\u0982", "king": "\u0995\u09bf\u0982",
    "ko": "\u0995\u09cb", "kou": "\u0995\u09cc",
    "korto": "\u0995\u09b0\u09cd\u09a4",
    "kortobbo": "\u0995\u09b0\u09cd\u09a4\u09ac\u09cd\u09af",
    "bimurho": "\u09ac\u09bf\u09ae\u09c1\u09a2\u09bc",
    "iuke": "\u0987\u0989\u0995\u09c7",
    "full": ("\u0995\u09bf\u0982\u0995\u09b0\u09cd\u09a4\u09ac\u09cd\u09af"
             "\u09ac\u09bf\u09ae\u09c1\u09a2\u09bc \u09ac\u09bf \u09ac\u09bf"),
}
print(f"family={fam!r} version={ver!r} cell={cell}")
for k, s in cases.items():
    buf = vhb.shape(s, {"script": "beng", "language": "ben"})
    adv = sum(g.x_advance for g in buf.glyph_positions)
    ng = len(buf.glyph_infos)
    print(f"{k:9} shaped={adv/cell:6.2f} cells  glyphs={ng}")
