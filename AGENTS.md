# AGENTS.md — siyam-rupali-mono

Terminal/mono conversion of Siyam Rupali. Read the brain's spec first:
`../agentic-font-dev/AGENTS.md` (operational spec + named incidents) and the
global rules at `C:\Users\Siyam\.zcode\AGENTS.md`. This file pins only the
project-specific decisions. Session history + evidence: `docs/WORKLOG.md`.

## Project decisions (settled — do not relitigate without new evidence)

- **Goal:** terminal mono Bangla font. **Strict mono**: every advance-bearing
  glyph = exactly 1 cell (1024 units at upem 2048). The plan's 600/1200
  hybrid was replaced — terminals take cell count from wcwidth (Bengali
  clusters = 1 cell always), so 2-cell advances desync the grid. Monotty
  (the plan's reference model) is deprecated by its own maintainers.
  Full rationale: WORKLOG 2026-08-30.
  **CHALLENGED 2026-08-31 (evidence, WT 1.24 cursor probe):** Windows
  Terminal does NOT use wcwidth grapheme clusters and does NOT honor
  shaped ligature advances — it grants columns as the SUM of
  per-codepoint FONT advances (GDEF-3 marks ~0, spacing signs 1) and
  draws cmap glyphs in codepoint order with no shaping: কি=2, কো=2,
  ক্ষ=2, কং=2, কু=1, measured directly (WORKLOG late 5). Terminal
  ecosystems are split: WT-family (per-codepoint, unshaped) vs
  pango/VTE-family (shaped, cluster-granted). WT-native variant built
  (open work 1a); decision on its adoption is the author's.
- **Base binary:** `legacy/base-1.070ship.ttf` = Dropbox
  `Siyamrupali_1_070ship.ttf` (final 2011 release, 789 glyphs, GSUB+GPOS
  compiled by VOLT at export; passed 6/6 golden shaping unchanged).
  Archive fact: `*core.ttf` = pre-VOLT (no GSUB), `*ship.ttf` = post-VOLT.
- **UFO/fea path is PARKED.** `Siyamrupali_1_064.vfb` and `1.064.vtp` are
  divergent snapshots (different glyph sets/orders/names; bridge GID gate
  refuses, 606 vs 607). The vtp name drift vs 1.070 binaries (80/474) is
  moot while layout is never recompiled. `sources/` + `legacy/ref.ttf`
  are kept for provenance and a future redesign only.
- **Version line:** `1.100`-`1.105` (Term series fork; version history in
  the font binaries runs 1.002–1.070). Wide/Edit current = 1.105.
- **Naming:** `bn_` snake_case, inherited from the base binary; generated
  CV ligatures follow `bn_<base>_<matra>`; standard (non-init) matra
  variants get `_std` suffix (e.g. `bn_ka_ekaar_std`).
- **fsType = 0** on output (we are the original author; ttfautohint also
  refuses the inherited restricted bit).
- **Source of truth:** `legacy/base-1.070ship.ttf` (read-only input) +
  `tools/mono_convert.py` + `tools/gen_cv_ligatures.py` (all mutations).
  Never hand-edit the built TTF; regenerate.
- **Cell width variants (final state 2026-08-31):** CV clusters carry
  ~1.7x a letter's ink, so at 1024 they squeeze to ~0.32 (unreadable —
  author verdict). Terminal grant per cluster = sum of wcwidth; bare কি
  = 1 cell forever. **REVISED same day (WT evidence):** Windows Terminal
  grants columns per CODEPOINT (font-advance sum, no shaping, no
  clusters) — see the challenge note under Goal and WORKLOG late 5/6.
  Three deliverables:
  **Wide v1.105/0.0.1** `--cell 1536 --ink-cap 0.97` + `--layout faithful`
  (pango/VTE-family terminals + shaping-aware grids; CV ligatures 1
  cell/cluster; rules cover BOTH matra art variants — GSUB `init` swaps
  bn_ekaar→bn_initekaar word-initially, so mid-word ে/ৈ need the `_std`
  rules too), **WT 0.0.1** `--prebase-shift` (Windows Terminal-native:
  no ligatures; pre-base matra + anusvara ink shifted one cell left so
  codepoint-order rendering puts the curl over the base — verified in
  unshaped render; grid = WT's own grant, self-consistent), and
  **Edit 0.0.1** (mono_convert only — no CV ligatures; matras keep
  their own full cell, everything unsqueezed below the cap; for
  gridless editors where font advances rule). Faithful layout = parts
  at original pen offsets, preserving designed matra/base interlocks
  (bbox packing double-counted those zones: 0.52 vs 0.68). **Kar glyphs
  are never squeezed** (is_kar: native ink centered, advance = cell,
  symmetric overflow). Tested-and-withdrawn: Fullwidth 2048 (dead
  bearings around Latin), 2-cell "WideCV" (no terminal supports
  per-codepoint width), NBSP 2-cell system (designed, deferred — open
  work #6).

## Build (reproducible; drive the scripts directly — no GNU make here)

System env used for v1.104/v1.105: Python 3.12 + fontTools 4.63 +
uharfbuzz + vharfbuzz + wcwidth (brain venv absent on the Windows box).
`PY=<python>` below.

```
# Terminal build (cv ligatures, 1-cell clusters) - v1.105
$PY tools/mono_convert.py     legacy/base-1.070ship.ttf build/work1536.unhinted.ttf --cell 1536 --ink-cap 0.97
$PY tools/gen_cv_ligatures.py legacy/base-1.070ship.ttf build/work1536.unhinted.ttf build/SiyamRupaliMono-Wide.ttf --cv-cell 1536 --ink-cap 0.97 --family "Siyam Rupali Mono Wide" --version 1.105
# Editor build (no cv ligatures; matras keep their own cell) - v1.105
$PY tools/mono_convert.py     legacy/base-1.070ship.ttf build/SiyamRupaliMono-Edit.ttf --cell 1536 --ink-cap 0.97 --family "Siyam Rupali Mono Edit" --version 1.105
# Windows Terminal build (pre-base matras shifted 1 cell left; no ligatures) - 0.0.1
$PY tools/mono_convert.py     legacy/base-1.070ship.ttf build/SiyamRupaliMono-WT.ttf --cell 1536 --ink-cap 0.97 --family "Siyam Rupali Mono WT" --version 0.0.1 --prebase-shift
# Optional Regular 1024 variant: same as terminal build but --cell default (1024), version 1.100
# Optional hand-designed glyph fixes (author redraws; see docs/FIXES.md):
#   $PY tools/apply_fixes.py build/SiyamRupaliMono-Wide.ttf fixes/<frag>.ttf   # BEFORE hinting
# Hinting (brain venv only): $PY ../agentic-font-dev/scripts/hint.py build/<ttf>
```

Gates (must pass; never weaken to make them pass):
```
$PY ../agentic-font-dev/scripts/qa.py build/SiyamRupaliMono-Wide.ttf tests/conjuncts.txt --script beng --language ben
$PY tools/shape_check.py build/SiyamRupaliMono-Wide.ttf --cell 1536 --matrix --context   # 0 failures
$PY tools/shape_check.py build/SiyamRupaliMono-Edit.ttf --cell 1536 --max-cells 3 --matrix   # 0 failures; NO --context (no ligatures by design)
$PY tools/shape_check.py build/SiyamRupaliMono-WT.ttf --cell 1536 --max-cells 3 --matrix     # 0 failures; NO --context, NO qa.py (goldens expect ligatures; WT font has none BY DESIGN - WT does not shape)
```

Visual gates for the WT variant (unshaped render = WT's model):
```
$PY tools/render_probe.py build/SiyamRupaliMono-WT.ttf --cell 1536 --tag WT --unshaped   # eyeball build/probe/WT_unshaped_*.png: matra curls must sit OVER their base
```

The Makefile mirrors these for GNU-make environments; on this Windows
box `make` is Embarcadero's and cannot parse it.

## Hard rules for this repo (incident-derived)

- **Never compile fea into this font with `addOpenTypeFeatures`** — it
  REPLACES the shipped GSUB (conjuncts die; QA goes 0/6). Append lookups
  via otTables instead (see gen_cv_ligatures.py).
- **Ligature entries per covered glyph must be sorted longest-first**
  (HarfBuzz takes the first match — 3-part ো/ৌ before 2-part ে/ৈ).
- **`glyf[name] = glyph` already appends to glyphOrder** — don't append
  manually (duplicate → maxp assert at save).
- Verify shaping claims against the vtp-era *binary* streams, not
  assumptions (ৌ's pre-part is `bn_initekaar`, not `bn_initaikaar`).

## Open work (priority order)

0. **Alpha 0.0.1 author testing** (Wide in terminals, Edit in editors;
   findings flow through the fixes layer, docs/FIXES.md). NOTE 2026-08-31:
   in Windows Terminal specifically, use **Edit** — it is the only
   grid-perfect build there (see 1a).
1a. **WT-matched variant — BUILT 0.0.1 (`--prebase-shift`), awaiting
   author verdict.** WT 1.24 does NO cross-codepoint shaping for Bengali:
   columns = sum of per-codepoint font advances, glyphs drawn in
   codepoint order (measured + screen-verified, WORKLOG late 5/6). The
   WT build shifts pre-base matra/anusvara ink one cell left so
   codepoint-order rendering reads correctly; grid = WT's own grant.
   Remaining: conjuncts render letter-by-letter in WT (hasanta visible,
   ক্ষ = ক+ষ) — platform limitation, upstream is working on shaping
   (terminal PR #16916, issues #17810, #18167). Wide stays for
   pango/VTE-family terminals; Edit for editors.
1. Visual review of Wide 1536 + Edit at 12-16px (hb-view or FreeType
   render sheet) - cluster squeeze 0.68 median is the accepted ceiling;
   eyeball before wide release. tools/render_probe.py renders test
   strings with a cell grid (HB shaping + freetype).
2. Conjunct + spacing matra (ক্ষি class) renders as two full cells in
   the terminal build (conjuncts outside the 36-base ligature scope) -
   v2: extend CV ligature coverage to conjunct outputs (automatable,
   ~2600 glyphs) or accept.
3. GPOS above-marks (anusvara/visarga) for কং-class clusters - they are
   GDEF class 1 (bases) in the VOLT font, so কং = 2 cells vs a 1-cell
   grant (overlap); needs abvs anchors + zero-advance marks. (WT grants
   কং=2 columns anyway — see 1a.)
4. `ss01` hasanta-explicit fallback feature (plan Phase 3).
5. WOFF2 deliverable (needs brotli in a venv).
6. NBSP-escape 2-cell system (font GSUB + Avro terminal-mode) -
   designed, deferred; only path to unsqueezed bare CV clusters in a
   strict terminal grid.
