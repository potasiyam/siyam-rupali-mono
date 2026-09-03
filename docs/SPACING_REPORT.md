# Spacing report — `কিংকর্তব্যবিমুঢ় বি বি` in Windows Terminal 1.24

Author report: this string "shows the spacing bug in WT". Measured with
all fonts, visually and programmatically. Companion to
`docs/REVIEW_TERM_VS_ALPHA.md` (independent verification ledger) — this
report extends the review's column model with a correction found by
bisecting this exact string.

## The two width notions

- **Shaped advance** (cells): what the shaper (HarfBuzz in
  kitty/WezTerm/editors; DWrite in WT) produces — sum of glyph
  advances ÷ cell width. This is the INK width a renderer draws.
- **Grid columns**: what WT's cursor/selection reserves per line.
  Measured in WT via cursor-position probes (`build/probe_spacing*.ps1`).

## Refined column model (correction to the review ledger)

The review's model — "SpacingMark = 1 column, Extend = 0" — fits its
probes but fails on this string: it predicts 18 columns; WT charges 17.
Bisecting per word (face = WT8):

| probe | columns | simple model | measured |
|---|---|---|---|
| কি | 2 | 2 ✓ | 2 |
| কং | 2 | 2 ✓ | 2 |
| **কিং** | **2** | 3 ✗ | **2** |
| কর্ত | 3 | 3 ✓ | 3 |
| কর্তব্য | 5 | 5 ✓ | 5 |
| বিমুঢ় | 4 | 4 ✓ | 4 |
| full string | — | 18 ✗ | **17** |

Refined rule that fits all 7 probes and the full string:
**Extend = 0 always; a combining mark charges 1 column only when it
follows a non-mark — runs of trailing marks collapse (mark-after-mark
= 0).** I.e. কি = 1+1, কং = 1+1, but কিং = 1+1+0. Equivalently: a
SpacingMark continues the previous mark's cell. (Likely conhost's
legacy wcwidth behaving as Mn=0 with a "combining run" quirk; the
review machine's WT may predate/postdate this — its simpler table fit
its own probes.)

## Programmatic widths — all fonts (shaped advance ÷ cell)

Test string: কিংকর্তব্যবিমুঢ় বি বি → grid = **17** (refined model).

| font | cell | shaped cells | grid | delta | note |
|---|---|---|---|---|---|
| **WT8** (no ligatures) | 1404 | **17.00** | 17 | **0** | grid-perfect on this string |
| Two (universal 0.0.8, ligatures) | 1404 | 13.00 | 17 | +4 | each কি-type ligature merges 2 glyphs → 1 cell while grid charges 2 |
| Edit 0.0.1 (no ligatures) | 1536 | 17.00 | 17 | 0 | same as WT8 |
| Wide 0.0.1 (ligatures) | 1536 | 13.00 | 17 | +4 | same as Two |
| original 1.070 | — | 5.91 em | 17 | — | proportional; not grid-comparable |

Decomposition of the deltas (why the numbers are what they are):
- **Reph** (কর্তব্য): the shaped reph glyph (`bn_half_ra`) has ZERO
  advance while the grid charges the র codepoint 1 column → +1 empty
  column, present in EVERY font including WT8/Edit.
- **CV ligatures** (কিং's কি, বিমুঢ়'s বি, বি, বি): ligature fonts
  merge base+matra into 1 cell while the grid charges 2 → +1 per
  cluster. 4 clusters here → +4. This is the big Two/Wide desync.
- **anusvara-after-matra** (কিং): the grid collapses ং to 0 while the
  shaped stream still advances it a full cell → −1 local overflow (ink
  spills into the NEXT cluster's first column).

## Live WT measurement (face = WT8)

Cursor after the full string: **17 columns** (matches refined model;
probe: `build/probe_spacing.ps1`, results
`build/probe/spacing_result*.txt`). Ink extent (PrintWindow capture,
`tools/win_capture.py`): ruler 18 X = 196 px ⇒ 10.89 px/column;
Bengali ink = 176 px ⇒ **16.2 columns of ink vs 17 charged** — the
residual gap is the reph's empty column, partly filled by কিং's ং
overflow. Visual: `build/probe/wt_spacing_zoom.png` — the line renders
fully shaped (ি over ব, reph over ত, ু under ম, real ঢ়): with WT8 the
text READS correctly and ends ~1 column short of the cursor; with
Two/Wide it would read correctly but end ~4 columns short (phantom
gaps mid-line).

## Verdicts

1. **WT8 / Edit are the grid-truest fonts in WT** (delta 0 on this
   string; +1 only for reph words). The author's preferred 2-glyph look
   and grid alignment coincide here.
2. **Two/Wide (ligature fonts) desync by design in WT** (+4 here, grows
   with cluster count). They are for shaping terminals that charge per
   cluster — the same file is correct in kitty/VTE/WezTerm-on-Unix.
3. **No font can charge exactly what it draws in WT for all text**:
   reph (grid 1 / glyph 0) and mark-run collapse (grid 0 / glyph 1)
   are terminal-side rules. WT8 minimizes the residual; the residuals
   are single columns adjacent to the features that cause them (reph
   words, ি+ং sequences).
4. The review's SpacingMark model needs this report's mark-run
   refinement; its font-independence conclusion stands (zero-advance
   probe font).

## How measured

- Programmatic: `tools/spacing_report.py` (vharfbuzz shaping + GCB
  table) — `python tools/spacing_report.py -v` dumps glyph streams.
- Grid: cursor-position probes inside WT (`build/probe_spacing*.ps1`,
  PS RawUI CursorPosition = conhost buffer model).
- Ink: PrintWindow capture (`tools/win_capture.py`) + PIL extents.

## ADDENDUM (same session, author-verified captures)

Author corrected two things about the first measurement pass:

1. **The proof grid was mis-scaled** — the capture had been taken with a
   stale window rect, so the drawn grid was wider than the real text
   grid. Recalibrated against the window's own ASCII prompt (pitch
   10.93 px at size 14). Corrected proof: `build/probe/console_grid.png`.
2. **Gaps after র্ত and after বি/কি/নি persist with the no-ligature
   build too.** With the grid calibrated, the clusters render COMPACT
   (matra drawn at/over the base — full shaping) and the second charged
   column of each CV cluster is EMPTY. So:

**FINAL WT rendering model (4th revision, author-confirmed):**
Windows Terminal 1.24 runs full Bengali shaping (reorder + GSUB, marks
positioned) but draws each shaped cluster compact at its FIRST charged
column, and charges columns per codepoint with the mark-run-collapse
rule. Therefore the second column of every CV cluster and the reph's
column are charged-but-empty FOR ANY FONT — ligature fonts (merged
glyph in col 1) and no-ligature fonts (matra+base compact in col 1)
produce the same empty-column signature. The earlier "WT8 is
grid-perfect (delta 0)" statement was a TOTAL-width coincidence: totals
can match while every cluster boundary still carries a one-column
residual.

Consequence: no font can eliminate the empty columns in WT 1.24; the
font-side choice is only which ART fills column 1 (compact shaped
cluster). The residual is intrinsic until WT charges shaped cluster
widths (upstream: PR #16916 direction). In shaping terminals
(kitty/VTE/WezTerm-Unix) the same fonts align 1 cluster = 1 column.

## MODEL UPDATE (2026-09-03, author directive): ং charges 1

The mark-run-collapse rule above is rejected as the REFERENCE model
for anusvara/visarga: they carry a full advance in the font, so the
model charges them 1 always (কিং = 3, full string = 18). WT 1.24's
measured collapse-to-0 (কিং = 2) stands as a terminal-side
undercharge — the mirror image of the reph's overcharge (+1), and
equally intrinsic. Collapse itself is kept for SpacingMark runs (কো =
ে+া granting 1 is still measured). `tools/spacing_report.py`
implements this model (EXTEND = 0, SpacingMark collapse, FULL_MARKS =
1 always) and now writes UTF-8 regardless of console codepage. The
original-font row divides by upem (8.61 em for this string), not
advanceWidthMax. Note: the WT8/Two/Wide-Alpha rows require the other
session's machine — those files are not on this box.

## Complex-word validation — WT10 build (2026-09-03, this box)

Font: review-branch wt14 state (`mono_convert` verbatim-matra + auto
cell 1404 + `gen_wt9_fixes.py`: reph2/yaph2 2-cell ligatures +
contextual anusvara/visarga tuck), family
"Siyam Rupali Mono WT10" 0.0.10, installed and live in WT.

Cursor-measured (WT grid) vs shaped vs refined-model charge:

| word | shaped | WT grid | verdict |
|---|---|---|---|
| কর্তব্য | 5 | 5 | ✓ reph2 + yaph2 fill their columns |
| গর্ত | 3 | 3 | ✓ reph hook per author verdict |
| দীর্ঘ | 4 | 4 | ✓ |
| কিংকর্তব্য | 7 | 7 | ✓ ং tucked, reph2, yaph2 |
| বিজ্ঞান | 5 | 5 | ✓ |
| স্বাধীনতা | 7 | 7 | ✓ |
| দ্বিতীয় | 5 | 5 | ✓ |
| যন্ত্র | 2 | 3 | +1 residual (ন্ত্র merges 3 cps → 1 cell) |
| সংস্কৃত | 4 | 5 | +1 residual (স্ক merge) |
| আত্মহত্যা | 5 | 6 | +1 residual (ত্ম+ত্য merges) |

6/9 words grid-perfect including every reph/yaphala/anusvara case (the
wt9–wt14 directives did exactly what they claim). The residual class =
multi-consonant CONJUNCTS: the original font's precomposed conjunct
glyphs occupy 1 cell while conhost charges per consonant (partially
self-collapsing — e.g. দ্বিতীয়/বিজ্ঞান/স্বাধীনতা measure = shaped
because conhost collapses those clusters too). Closing this = the
documented v2 item (2-cell variants for wide conjuncts, the reph2
pattern generalized, ~2600 glyphs) or accept as the WT residual.
