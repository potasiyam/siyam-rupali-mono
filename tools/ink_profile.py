"""Pixel-forensics: ink column profile of a terminal line vs cell grid."""
from PIL import Image
import sys

img = Image.open(sys.argv[1]).convert("L")
# the output line band (raw window coords)
y0, y1 = 590, 650
x0, x1 = 40, 460
band = img.crop((x0, y0, x1, y1))
w, h = band.size
px = band.load()

col_ink = []
for x in range(w):
    n = sum(1 for y in range(h) if px[x, y] > 100)
    col_ink.append(n)

# print a compact profile: one char per column, digit = ink strength bucket
line = "".join(
    "." if n == 0 else str(min(9, 1 + n * 9 // h)) for n in col_ink)
print("band x from", x0, "to", x1)
for i in range(0, len(line), 100):
    print(f"{x0 + i:4d} {line[i:i + 100]}")

# cell boundaries: size 30 -> cell = 30 * 1536/2048 = 22.5 px.
# find line start: first column with ink
first = next(i for i, n in enumerate(col_ink) if n > 0)
print("first ink col at x =", x0 + first)
