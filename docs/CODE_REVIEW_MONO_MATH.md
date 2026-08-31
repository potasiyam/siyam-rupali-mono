# Code review: mono conversion math (2026-08-31)

Scope: `tools/mono_convert.py`, `tools/gen_cv_ligatures.py` — every number
below measured on `legacy/base-1.070ship.ttf` and the rebuilt intermediates
(`build/review_math.log`, `build/review_math2.log`).

## What the pipeline actually does (verified)

`mono_convert.py:132-156` per glyph:

1. Skip if `GDEF class == 3` or `advance < 300` (mark machinery) — 36 glyphs.
2. Empty glyph → advance = cell.
3. Else: `sx = min(1.0, 0.92*cell / ink_width)`, `dx` re-centers ink,
   glyph redrawn decomposed under `(sx, 0, 0, 1, dx, 0)`, advance = cell.

Invariant checks on the output: every converted glyph is exactly 1024
(n=0 violations); untouched advances are all ligature machinery
(hasanta 3, phalas 3-216, half_ra 3, nukta 63); `hhea.numberOfHMetrics=599`
with 1041 glyphs is spec-legal trailing-advance sharing (readers reuse the
tail advance), not a bug.

`gen_cv_ligatures.py` ligature injection: 3-part (ো/ৌ) rules verified
listed before 2-part (ে) prefixes for the same covered glyph (HarfBuzz
first-match requirement); appended lookup runs last in `pres`
(idx list [9, 14]); কি/কো/কৌ shape to single 1-cell glyphs; র্কি collapses
to 1 cell too (bn_ka_ikaar + half_ra[3] = 1027).

## Finding 1 — the "huge gaps", measured (root cause of the author's complaint)

`mono_convert.py:146-148`: narrow glyphs are **centered**, not normalized.
Anything with ink below `0.92*cell` keeps native width and floats mid-cell.

| Glyph | ink fill | lsb = rsb |
|---|---|---|
| Bengali bases (all 36) | 0.92 | 41 |
| m, w | 0.92 | 41 |
| f | 0.71 | 150 |
| t | 0.61 | 201 |
| j | 0.43 | 292 |
| period | 0.31 | 353 |
| i | 0.21 | 406 |
| l | 0.18 | 421 |

lsb spread across Latin: 41..421 — a 10x variance. A designed mono
normalizes stem positions/sidebearings; this conversion produces dead
bearings around every narrow glyph. At cell 1536/2048 the dead space
scales with the cell — exactly "the gap becomes huge... looks even bad".
Cross-script: Bengali uniformly fills 0.92 while Latin median is 0.85
with wild tails — two rhythms in one font.

## Finding 2 — VOLT classes the 7 spacing matras (and anusvara/visarga) as BASES

Measured in the base font: bn_ikaar cls=1 adv=541, bn_iikaar 533,
bn_initekaar 744, bn_initaikaar 691, bn_aakaar 536, bn_anusvara 810,
bn_visarga 730 (bn_okaar/aukaar 2458/2392 are precomposed অ-vowels).
Only the below-marks (ukaar, uukaar, rikaar) are GDEF class 3.

So `mono_convert` converts matras to full-cell glyphs. Consequences:

- Conjunct + matra (ক্ষি, স্ত্রি — conjunct outputs are NOT in the 36-base
  CV ligature scope): renders as [matra cell][conjunct cell] = the "two
  separate blocks" the author observed. (Bare কি is saved by the ligature;
  র্কি incidentally fires it too via [ikaar, ka] adjacency.)
- কং / কঃ = base cell + full-cell anusvara = 2 cells vs a 1-cell wcwidth
  grant → overlap. Meanwhile কঁ (candrabindu, adv 3) stays 1 cell —
  inconsistent treatment within the same class of clusters.
- The whole GPOS contains exactly ONE lookup: MarkBasePos under `blwm`
  (below-base marks). There is no abvs attachment; above-mark placement
  in the original font is advance-based (side-by-side), which mono
  conversion preserves as extra cells.

## Finding 3 — squeeze target destroys cross-script weight parity

Uniform "fit to 0.92*cell" means stroke weight varies by native ink width:
Bengali bases median 0.62x, Latin ~0.85-1.0x at cell 1024 — Bengali reads
visibly lighter/thinner than Latin in the same line. In `gen_cv_ligatures`
strict mode the fixed REGIONS made it worse: base inside a CV ligature
gets [0..565] = 0.55 fill vs 0.92 for the standalone letter (the original
"কি too thin" report). The uniform-scale wide mode fixed intra-cluster
consistency but not cross-script parity.

## Finding 4 — minor / cosmetic

- `mono_convert.py:14-16` docstring references a `--cell-beng` flag that
  does not exist (stale hybrid-era text).
- Unused imports: `newTable` (`mono_convert.py:27`), `Glyph` (`:28`).
- RoundingPen + lsb rounding can drift ±1 unit from glyf xMin; fontTools
  recalcs bboxes at save; shape tolerance +8 covers it. Harmless.
- `hhea.numberOfHMetrics` explicitly set at `mono_convert.py:197` is
  recomputed by fontTools on compile (599) — the manual set is a no-op.
- No GPOS PairPos / kern survives (kern table dropped, only blwm lookup
  exists) — nothing can break the mono advance after conversion. Good.

## Verdict

The math is internally correct (invariants hold, ligature ordering right,
anchor moves right after the 2026-08-31 fix), but the *model* —
per-glyph fit-and-center of proportional art — cannot produce mono
typography: it manufactures bearing variance (Finding 1) and inherits
VOLT's matras-as-bases classes (Finding 2), which is why every cell-width
variant failed the eye test. A readable strict-mono Bangla needs drawn
(narrow-stem, normalized-sidebearing) glyph designs and matra glyphs that
are zero-advance marks positioned by GPOS — not converted spacing glyphs.
