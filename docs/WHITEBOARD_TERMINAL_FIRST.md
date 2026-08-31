# Whiteboard: Terminal-First Monospace Bangla (output-only, no Avro)

**Goal restated (2026-08-31):** Any CLI that prints Bangla must render correctly in a monospace Bangla font. Input/writing is out of scope.

## 1. Grid grant is the boss (wcwidth)

Measured with `wcwidth` (same table as VTE/kitty/Windows Terminal pre-1.23):

- Consonant / digit / independent vowel (U+0980..09FF Lo, etc) = 1 cell
- Combining mark (Mn Mc Me): 09BC 09BE 09BF 09C0 09C1 09C2 09C3 09C4 09C7 09C8 09CB 09CC 09CD 09D7 09E2 09E3 0981..0983 = 0 cells
- Virama 09CD = 0, hasanta-combining

Cluster grant = sum of codepoints:

- ক (0995) = 1
- কা কি কী কে কৈ কো কৌ = 0995 + matra(0) = 1
- ক্ষ র্ক = 0995+09CD+09B7 (etc) = 2 (two 1-cell bases)
- র্কি ক্ষি = +09BF (0) = 2 (inherits 2 from conjunct)
- কং কঃ = 0995 + 0982/0983(0) = 1

Consequence: a bare CV like কি must fit ONE cell; a conjunct+matra like র্কি already has TWO. This is why conjuncts looked "two blocks" and bare CV looked "compressed" — it is terminal math, not a font bug.

Incoming change: kitty 0.48 spec (issue #8533, 2025-04) proposes SPACING marks (Mc/Sm: 09BE 09BF 09C0..) become 1 cell each, so কি would be 2 cells, কো 3 cells. Quote: "a base character plus a 1-cell-wide spacing mark means a 2-cell-wide EGC". Not shipped as default yet.

## 2. What terminals actually shape

- Windows Terminal (AtlasEngine, 2024-2025): DirectWrite shaping for Indic via Universal Shaping Engine. PR #20377 added BiDi rendering, PR #20470 fixed OutputCellView::Columns()==1 for combining marks so marks now correctly 0 columns. Full Bengali reordering+conjuncts works when font has GSUB/GPOS/GDEF. Grapheme-cluster support landed via #16916 (1.22, textMeasurement modes).

- kitty: HarfBuzz for every run (HB_BUFFER_CLUSTER_LEVEL_MONOTONE_CHARACTERS, force_ltr opt). Shapes N codepoints into M glyphs, then groups glyphs back onto cells (group_normal vs group_iosevka). Ligatures can span cells.

- WezTerm: HarfBuzz in Rust (HB_BUFFER_CLUSTER_LEVEL_MONOTONE_GRAPHEMES). ClusterResolver maps info.cluster into byte_len + cell_width (via presentation_width or unicode_column_width). Issue #1333 shows বাংলা ভাষা measured as 5 columns but 65px (8 cells) — 3 cells of overflow; acknowledged fix would be scaling or variable-column mode.

- foot: Optional HarfBuzz + utf8proc grapheme segmentation. grapheme-width-method = {wcswidth, double-width(caps at 2), max} — wcswidth sums per grapheme, double-width caps at 2 columns.

All three CAN shape Bengali if font supplies Indic2 tables.

## 3. Cell grant vs glyph advance (why fonts look clipped)

- If glyph.advance <= grant*cell_width : glyph centered, bearings empty.
- If glyph.advance > grant*cell_width : behavior depends:
  - foot double-width/max: caps grant, glyph clips/overlaps.
  - wezterm: distributes glyphs across cell_width; overflow glyphs overlap next column (cursor mismatch as in #1333).
  - kitty: renders the shaped run at shaped advances; visually overlaps following cells if advance > granted cells.
  - Windows Terminal (Atlas): "Centering glyphs in their cell isn't trivial because ligatures can span arbitrary columns... simpler to left-align" (#17810). Gaps vs overlap tradeoff.

No terminal currently scales a glyph down to fit the grant (scaling proposal in kitty #8533 says "Future refinements could horizontally scale EGCs from Devanagari/Bengali... we would have to experiment"). So a font that draws a 2-cell-wide কি as one glyph while the terminal grants 1 cell WILL overlap.

mlterm is the outlier: --varwidth (use_variable_column_width = true) and --ctl/--otl make column width = glyph advance. It ships with old ISCII bitmap fonts (BNDR0ntt for Bengali) and fontconfig-2.8.0-fix4indic patch. No OpenType GSUB; uses libind/libotf. True variable width — no squeeze needed, but cursor math is variable-width (TUIs break differently).

## 4. What actually ships as terminal CTL fonts

- Noto Sans Mono: Latin/Cyrillic/Greek only (3,787 glyphs). No Bengali. The 2025 Fedora change adds fallback monospace for Bengali etc., but it still falls back to proportional Noto Sans Bengali — not a mono grid.
- Monotty (github.com/monotty/fonts): explicit note on README — "Practice has shown that for correct display of Devanagari in the terminal, there is no need for special fonts — proportional ones are quite sufficient. Monotty fonts are not correct, do not use them." Bengali: N/A. Two other builds (Devanagari variants) are deprecated.
- Sarasa / Iosevka CJK monos: unrelated — they solve EastAsianWidth 2-column, not reordering/virama.

Conclusion: no production monospace Bengali terminal font exists; the field has settled on "use the proportional Indic font + let the terminal handle grapheme clusters" (freedesktop.org terminal-wg spec issue #23, referenced by Monotty).

## 5. Hard constraints for Siyam Rupali Mono (design phase next)

If we keep the constraint "any CLI, any wcwidth=1 terminal, strict cells":

- Single-CV clusters (কা..কৌ) have 2969 units of native ink (median) vs a letter's 1785 — 1.7x. To stay in 1 cell at upem 2048: 1024 cell gives squeeze 0.32x, 2048 cell gives 0.66x. Legible at 1024 is impossible without a NEW condensed drawing; 2048 is the practical ceiling we hit.

- The only terminal-agnostic way to give কি 2 cells is to change the TEXT (NBSP hack) or wait for kitty's spacing-mark=1 spec — both violate "any CLI output".

- Variable-width terminals (mlterm --varwidth) remove the cell wall but sacrifice column-aligned TUIs. Windows Terminal/kitty/wezterm default to fixed grid.

Design implication: a terminal Bangla that is readable AND grid-faithful at 1 cell must be DESIGNED as a condensed monospace from scratch (narrow vertical stems, matra forms that share the cell instead of sitting beside the base). Squeezing the proportional outlines centers glyphs in empty space — the "huge gap between characters" the author correctly flagged at 1536/2048. A real design reuses the gap with stroke logic, not empty bearings.

Next: design-first research — what does a condensed Bengali mono need to look like, and is a single 1-cell style even plausible vs a 2-cell EGC future?
