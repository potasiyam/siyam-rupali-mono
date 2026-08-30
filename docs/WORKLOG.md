# WORKLOG — siyam-rupali-mono

Running record. Newest first. Follows the brain's discipline: decisions,
evidence, and named incidents — so future sessions don't re-derive or
re-break them.

## 2026-08-30 — v1 strict-mono build (1.100) shipped from 1.070ship

**Deliverable:** `build/SiyamRupaliMono-Regular.ttf` — 1041 glyphs,
1041 = 789 original + 252 CV ligatures; every advance-bearing glyph at
exactly 1024 units (1 cell at upem 2048), 36 combining marks near-zero.
Golden shaping 11/11; 36-consonant × 7-matra matrix: 0 clusters overflow
1 cell. ttfautohinted (99% glyph coverage).

### The pivot: UFO/fea path → TTF-direct (named incident class: verified, not assumed)

The settled plan (brain pipeline: `.vfb` → UFO → bridge → fontmake)
**does not execute on this source pair** — evidence:

- `Siyamrupali_1_064.vfb` → UFO = 607 glyphs; `1.064.vtp` = 606 — and not
  a superset: substantially different glyph SETS (vtp has conjuncts the
  vfb lacks and vice versa), different orders, different naming styles
  (`glyph90`/`bn_akaar` vs `bn_aakaar`/`bn_zero`). The brain's
  `bridge_names.py` GID gate correctly refused (count mismatch + the
  positional diff showed 14 divergent blocks, ~zero positional agreement
  past glyph 100).
- **"core" TTFs have no GSUB; "ship" TTFs have GSUB** (scanned all 39
  archive TTFs). VOLT compiled the vtp layout into the ship binaries at
  export time. So the ship binary IS the matched, proven layout+outline
  artifact; the vtp/fea name drift against 1.070 binaries is moot if we
  never recompile layout.
- **Decision:** work directly on `Siyamrupali_1_070ship.ttf` (final 2011
  release, 789 glyphs, GSUB+GPOS compiled, 6/6 golden on arrival). The
  `.vfb`/UFO route is parked for a future redesign, not for this fork.
  `sources/`, `legacy/ref.ttf` kept for provenance.

### Why strict mono, not the planned 600/1200 hybrid

Terminals decide cell count from Unicode width (wcwidth), never from
font advances: every Bengali grapheme cluster is granted exactly 1 cell.
A 1200-unit Bengali glyph would desync the grid in every terminal. The
plan's hybrid requires "per-glyph wcwidth" terminals that don't exist.
Reference-model check (Rule 1): **Monotty is deprecated by its own
maintainers** ("fonts in our repository are not correct, do not use
them") — their conclusion was that terminal-side grapheme clustering is
the real fix (terminal-wg spec proposal, unimplemented). Links in the
session transcript: github.com/monotty/fonts.

Model chosen: **every advance-bearing glyph = exactly 1 cell** (upem is
2048, so cell = 1024 = half-em, same geometry as Monotty's half-em).
Conjuncts x-condense to fit (median 0.618, worst 0.304 on triple
conjuncts like স্প্ল — the legibility watch-item for v2).

### The spacing-matra problem and the CV ligature fix

Measured reality: the 7 spacing matras (ি ী ে ৈ ো ৌ া) each carried a
full advance → কি = 2 cells, কো = 3. Fix: generate
`bn_<base>_<matra>` ligature glyphs (36 consonants × 7 matras = 252),
composing original art into fixed cell regions
(pre [0..340] / base [377..942]; 3-part: [0..230]/[267..675]/[712..942]),
and append ONE LookupType-4 to the existing GSUB `pres` features.

### Named incidents (this repo)

1. **`addOpenTypeFeatures` REPLACES GSUB; it does not merge** (caught by
   the golden gate, 0/6 conjuncts after a "one rule" smoke). Fix:
   append the lookup via otTables surgery (LookupList append +
   LookupCount bump + extend each `pres` FeatureRecord's
   LookupListIndex). feaLib's builder assumes the fea file is the
   complete layout source — fine for the brain's overlay (font had no
   GSUB), fatal when appending to a compiled one.
2. **HarfBuzz takes the first matching ligature per covered glyph** —
   the 3-part ো/ৌ rules must be listed before their 2-part ে/ৈ prefixes
   (same covered first glyph). Symptom: কো ligated, কৌ fell through to
   the 2-part rule + trailing া.
3. **ৌ's pre-base part is `bn_initekaar` — the same glyph ে uses**
   (measured; assumed `bn_initaikaar` first). Only ঐ uses
   `bn_initaikaar`.
4. **`glyf[name] = glyph` auto-appends to glyphOrder** (fontTools) — a
   manual `order.append` duplicates the entry and trips maxp's
   `len(glyphOrder) == len(glyphs)` assert at save.
5. Test-string bug: a literal `ড়` in a matrix generator is TWO
   codepoints, so standalone `়`+matra clusters (invalid input) were
   counted as font failures. Invalid clusters get dotted circles by
   design — test with proper cluster strings.

### Tooling notes

- **No GNU make on this machine** (only Embarcadero's). The Makefile is
  kept GNU-compatible; commands are driven directly via the brain venv:
  `I:/projects/agentic-font-dev/.venv/Scripts/python.exe`.
- ttfautohint refuses fonts with OS/2.fsType restricted bit — cleared to
  0 in mono_convert (we are the original author; permissive for a
  terminal font).
- Composites in the base are offset-only (no 2x2) — asserted in code.

### Build pipeline (reproduce)

```
PY=I:/projects/agentic-font-dev/.venv/Scripts/python.exe
$PY tools/mono_convert.py      legacy/base-1.070ship.ttf build/work.unhinted.ttf
$PY tools/gen_cv_ligatures.py  legacy/base-1.070ship.ttf build/work.unhinted.ttf build/SiyamRupaliMono-Regular.ttf
$PY <brain>/scripts/hint.py    build/SiyamRupaliMono-Regular.ttf
$PY <brain>/scripts/qa.py      build/SiyamRupaliMono-Regular.ttf tests/conjuncts.txt --script beng --language ben
$PY tools/shape_check.py       build/SiyamRupaliMono-Regular.ttf --matrix
```

### Known v1 limitations (documented, deliberate)

- **Conjunct + spacing matra** (র্কি, স্টে, ন্ট্রো…): conjunct ligature +
  matra still = 2 cells (no ligature generated; 382 conjuncts × matras
  is glyph-explosion scale). Falls back to today's terminal behavior
  (clip/overlap). v2 options: contextual base alternates + matra-as-mark.
- **Standalone ং ঃ** emit dotted-circle (invalid-sequence path): 2 cells.
- **Visual polish unreviewed**: no hb-view render pass yet; condensation
  ratios (median 0.62) need eyeballing at 12–16px; GPOS below-mark
  anchors were scaled geometrically, not re-designed.
- **ss01 hasanta-explicit fallback** (plan Phase 3): not implemented.
- **Hybrid 2048-cell experiment** (plan's original model): parked with
  rationale above; revisit only if terminal-side width overrides become
  real.
