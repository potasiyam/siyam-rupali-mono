# Terminal usage — Siyam Rupali Mono variants

All variants are strict monospace: every Bengali grapheme cluster occupies
exactly the number of cells the terminal grants (sum of wcwidth of the
cluster's codepoints). No terminal configuration is required.

## The two variants

| Build | Cell | Letters | Bare CV clusters (কা কি কো…) | Use |
|---|---|---|---|---|
| Regular | 1024 (0.5 em) | 0.62x | 0.32x — too thin | dense output, ASCII-first work |
| **Fullwidth** | 2048 (1.0 em) | 1.00x | 0.66x | **recommended for reading Bangla** |

Measured native ink at upem 2048: single letter (ক) 1785 units, median CV
cluster 2969 units, worst (স্পে-class with two matra parts) 4026. A bare
consonant+matra cluster therefore can never be unsqueezed in one
terminal cell — 0.66x at the 1-em cell is the practical ceiling of the
honest path. Fullwidth cells are twice as wide as a typical terminal
font's; window density halves (think CJK fullwidth).

## Why bare CV clusters can't get 2 cells

The terminal grant per cluster is the sum of wcwidth over the cluster's
codepoints:

- কি = ক(1) + ি(0) → **1 cell**, always, in every terminal.
- র্কি = র(1) + ্(0) + ক(1) + ি(0) → **2 cells** (two advance-bearing
  codepoints). This is why conjunct+matra renders as two comfortable
  blocks while bare consonant+matra is squeezed — the asymmetry is the
  terminal's, not the font's. The font matches the grant in both cases.

Per-codepoint width overrides do not exist in kitty (`modify_font` =
underline/strikethrough/cell/baseline only, verified 2026-08-31),
WezTerm, or Windows Terminal, so the grant cannot be changed from the
font side. A NBSP-escape system (base + NBSP + matra = 2 cells, font
ligates the three, Avro keyboard emits the NBSP) was designed and
deferred — see WORKLOG 2026-08-31. Revisit if 0.66x proves still too
thin in daily use.

## Installing

1. Install `SiyamRupaliMono-Fullwidth.ttf` (and/or `-Regular.ttf`;
   distinct family names, they coexist).
2. Select the family:

```
# kitty.conf
font_family      Siyam Rupali Mono Fullwidth
bold_font        auto
```

```lua
-- wezterm.lua
wezterm.font('Siyam Rupali Mono Fullwidth')
```

Windows Terminal: Settings → profile → Appearance → Font face →
`Siyam Rupali Mono Fullwidth`.

## Known gaps (v1)

- Conjunct + spacing matra (র্কি class): renders at the terminal's
  2-cell grant, base conjunct + full-width matra. Matches the grid.
- Isolated marks (ং ঃ typed bare) render with a dotted circle; in real
  text they attach to a base.
- Hinting not yet applied (ttfautohint step needs the brain venv).
