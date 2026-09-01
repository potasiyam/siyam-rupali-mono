# Review: Term-series (v1.105) vs Alpha-series (0.0.3) â€” verified claim ledger

Review branch. **Method:** no claim from either branch accepted without
independent verification. Verification tools used: (a) fresh empirical
probes written from scratch this session (`tools/wt_column_probe.ps1`,
`tools/wt_probe_run.ps1`, `tools/wt_probe_zero_run.ps1` â€” cursor-column
measurement inside WT 1.24.11911 + PrintWindow capture, original Siyam
Rupali AND a purpose-built zero-advance probe font), (b) internet
sources (microsoft/terminal issues, kitty/foot source & docs),
(c) direct binary/font inspection (fontTools, uniseg). Environment:
WT 1.24.11911.0, fonts: original Siyam Rupali 1.070 (installed),
probe font (temporary install, removed after test).

## Verified WT column-charging model (NEW finding â€” corrects both branches)

Measured columns (cursor delta, per string, in WT):

| Probe | Columns | font-adv model predicts | wcwidth-cluster predicts | GCB model predicts |
|---|---|---|---|---|
| à¦• | 1 | 1 | 1 | 1 |
| à¦•à¦¿ | **2** | 2 | 1 | **2** |
| à¦•à§ | **1** | 1 | 1 | **1** |
| à¦•à¦‚ | **2** | 2 | 1 | **2** |
| à¦•à§‡ | **2** | 2 | 1 | **2** |
| à¦•à§à¦· | 2 | 2 | 2 | 2 |
| à¦•à¦(nukta) | **1** | **2 âœ—** | 1 | **1** |
| à¦•à§ | 1 | 1 | 1 | 1 |
| à¦‡à¦‰à¦•à§‡ | 4 | 4 | 3 | 4 |

Decisive experiment: a probe font with ikaar/e-kar/anusvara advances
ZEROED charged IDENTICAL columns (ki=2, kang=2, ke=2) â†’ column count is
**font-independent**. Nukta (font adv 63) charged 0 columns â†’ advances
never enter the calculation at all.

**The table is Unicode GraphemeBreakProperty, charged per codepoint**:
`SpacingMark â†’ 1 column`, `Extend â†’ 0 columns`, `Other â†’ 1 column`.
Verified correlation (uniseg GCB lookup): 09BF SpacingMark=1 âœ“,
09C7 SpacingMark=1 âœ“, 0982 SpacingMark=1 âœ“, 09C1 Extend=0 âœ“,
09BC Extend=0 âœ“, 09CD Extend=0 âœ“. 6/6.

This is consistent with WT 1.22's grapheme-cluster work (microsoft/
terminal PR #16916) and with kitty issue #8533, which documents the
same "spacing marks = 1 cell per codepoint" model as the terminal
split. ConPTY column tables differ by version (nukta: WT 1.24 = 0,
wezterm's bundled conpty = 1 â€” origin's observation, consistent).

## Verdicts on origin's claims (other-PC session)

| Claim | Verdict | Evidence |
|---|---|---|
| WT charges à¦•à¦¿=2, à¦•à§‹=2, à¦•à§à¦·=2, à¦•à¦‚=2, à¦•à§=1 | **VERIFIED** | my probe reproduces exactly |
| "columns = sum of per-codepoint FONT advances; font data IS the WT grid" | **REFUTED** (mechanism) | zero-advance probe font â†’ unchanged columns; nukta adv 63 â†’ 0 cols. Their measured counts stand; mechanism is the GCB table, not the font |
| WT applies GSUB `pres` (SingleSubst fired) but NO Bengali reorder | **PARTIAL** | "no reorder" VERIFIED visually: my capture shows à¦¿ drawn AFTER/right of à¦•, à¦‚ beside base, à¦•à§à¦· letter-by-letter with visible hasanta (matches #17838 "poor complex script support", closed not-planned). "pres fires" not independently reproduced (needs their 0.0.2 font; plausible â€” DWrite does run GSUB features) |
| WT stale DirectWrite font cache; fix = new filename + WM_FONTCHANGE | PLAUSIBLE (ops) | consistent with known DWrite caching; not re-tested here |
| WT conjuncts render letter-by-letter (à¦•à§à¦· = à¦•+à¦·) | **VERIFIED** | my capture shows hasanta + separated à¦· |
| WezTerm Windows: HarfBuzz shapes (ligatures fire) but ConPTY charges per-codepoint â†’ phantom gap | PARTIAL | plausible; consistent with ConPTY being the buffer authority + wezterm docs; not re-run here (wezterm cursor probe not repeated) |
| kitty/VTE-family: shaped, cluster-granted, à¦•à¦¿ = 1 column | VERIFIED-by-source | kitty fonts.c (hb_shape + cell grouping), foot docs grapheme-width-method, VTE shaper; no Windows kitty to test |

## Verdicts on local Term-series premises (v1.105)

| Claim | Verdict |
|---|---|
| "terminals take cell count from wcwidth (Bengali clusters = 1 cell always)" | **REFUTED for WT** â€” WT uses GCB per-codepoint table (à¦•à¦¿ = 2). Holds for kitty/VTE/foot (shaping family) |
| Wide/Edit useful split | STILL SOUND but per a different mechanism: Edit (matras own cell) is grid-perfect in WT *because* WT charges SpacingMark 1 col â€” every Edit glyph lands in a granted cell. Wide's ligatures work on shaping terminals only |
| Faithful layout, kar no-squeeze, init/std coverage | INHERITED by 0.0.3 (verified present on main: is_kar, layout_faithful, PRE_VARIANTS, CONTEXT_RULES) |

## Implication for "best outcome"

0.0.3's universal architecture is validated by my independent
measurements (its design used cluster COUNTS, which I confirmed; only
its mechanism narrative was wrong). Both branches' engineering survives
inside it. The review outcome should be: adopt universal 0.0.3 as the
primary deliverable; keep Edit as the maximal-readability alternative;
retire Wide-as-separate-family only after a shaping-terminal regression
pass (its 1-cell ligature behavior is already inside Universal via pres
ligatures). Open items that remain real: conjunct+matra leftovers keep
shifted art in shaping renderers (cosmetic), WT conjunct letter-by-letter
is upstream-blocked, and the `--restore-shifted` opt-in should stay OFF
(verified logic: restore keyed on original names fires in WT's pres
without reorder â€” origin's own probe_restore caught this; consistent).

## Addendum: Alacritty retest (correct font) + comment corrections

The first Alacritty capture rendered a FALLBACK font: the harness passed
the family via -o with quoting that got mangled, so the family never
applied. With a proper config file (APPDATA/alacritty/alacritty.toml),
alacritty -vv logs 'Loading Siyam Rupali Mono font' and the render shows
the correct letterforms. Harness tools fixed (run_alacritty_cfg.ps1).

Alacritty 0.0.6 verdict (correct font): original-art matras overlay
their base acceptably at codepoint order (ki/ke/kaa ok); ko/kau show
dotted circles (09CB/09CC cannot split without shaping); kssi jammed.
All three are alacritty's lack of shaping - no font can fix.

Comment corrections (author directive): obsolete mechanism notes removed
- 'columns = per-codepoint font advances' (refuted by zero-advance probe
font: the table is Unicode GCB) and wcwidth-cluster framing in docstrings
replaced by the two-family model; VOLT-era matra design acknowledged as
intentional (codepoint-order rendering), not a defect.
