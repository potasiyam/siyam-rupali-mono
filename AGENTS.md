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
  variants get `_std` suffix (e.g. `bn_ka_ekaar_std`); shifted WT art
  lives under the ORIGINAL matra names with centered twins as
  `<name>_shaped` (restore lookup omitted by default — WT applies pres
  without reorder, WORKLOG late 9).
- **fsType = 0** on output (we are the original author; ttfautohint also
  refuses the inherited restricted bit).
- **Source of truth:** `legacy/base-1.070ship.ttf` (read-only input) +
  `tools/mono_convert.py` + `tools/gen_cv_ligatures.py` (all mutations).
  Never hand-edit the built TTF; regenerate.
- **Cell width variants (state 2026-08-31, universal era):** CV clusters
  carry ~1.7x a letter's ink, so at 1024 they squeeze to ~0.32
  (unreadable — author verdict). **PRIMARY DELIVERABLE = Universal
  `Siyam Rupali Mono` 0.0.3** (`--prebase-shift` + ligatures): one font
  that adapts to the renderer — the six pre-base/above-mark glyphs
  (ikaar ekaar aikaar okaar aukaar anusvara) carry SHIFTED art under
  their original names (Windows Terminal renders them codepoint-order,
  no reorder), `_shaped` copies hold centered art (unused unless the
  opt-in `--restore-shifted` is passed — see WORKLOG late 9 for why the
  restore misfires in WT), and appended pres LigatureSubst merges
  clusters for shaping renderers. Result: WT = correct split-cell look
  at WT's own per-codepoint grant; shaping terminals (kitty/VTE) =
  1-cell ligatures; editors = ligatures. Rules cover BOTH matra art
  variants (GSUB `init` swaps bn_ekaar→bn_initekaar word-initially;
  mid-word ে/ৈ need `_std` rules). Faithful ligature layout = original
  pen offsets (bbox packing double-counted interlocks: 0.52 vs 0.68).
  **Kar glyphs are never squeezed** (is_kar: native ink centered,
  advance = cell, symmetric overflow). Specialist variants (kept in
  build/, installed for the author's comparison): **Wide** (no
  prebase-shift; shaping terminals that grant 1 cell/cluster), **WT**
  (no ligatures; WT only), **Edit** (mono_convert only; matras keep own
  cell; gridless-editor maximalism). Tested-and-withdrawn: Fullwidth
  2048 (dead bearings around Latin), 2-cell "WideCV" (no terminal
  supports per-codepoint width), NBSP 2-cell system (designed,
  deferred — open work #6).

## Build (reproducible; drive the scripts directly — no GNU make here)

System env used for v1.104/v1.105: Python 3.12 + fontTools 4.63 +
uharfbuzz + vharfbuzz + wcwidth (brain venv absent on the Windows box).
`PY=<python>` below.

```
# UNIVERSAL build (primary; one font for WT + shaping terminals + editors) - 0.0.3
$PY tools/mono_convert.py     legacy/base-1.070ship.ttf build/work-uni.unhinted.ttf --cell 1536 --ink-cap 0.97 --prebase-shift
$PY tools/gen_cv_ligatures.py legacy/base-1.070ship.ttf build/work-uni.unhinted.ttf build/SiyamRupaliMono.ttf --cv-cell 1536 --ink-cap 0.97 --layout faithful --family "Siyam Rupali Mono" --version 0.0.3
# Terminal build WITHOUT prebase-shift (Wide; shaping terminals only) - 0.0.1
$PY tools/mono_convert.py     legacy/base-1.070ship.ttf build/work1536.unhinted.ttf --cell 1536 --ink-cap 0.97
$PY tools/gen_cv_ligatures.py legacy/base-1.070ship.ttf build/work1536.unhinted.ttf build/SiyamRupaliMono-Wide.ttf --cv-cell 1536 --ink-cap 0.97 --family "Siyam Rupali Mono Wide" --version 0.0.1
# Editor build (no cv ligatures, no shifts) - 0.0.1
$PY tools/mono_convert.py     legacy/base-1.070ship.ttf build/SiyamRupaliMono-Edit.ttf --cell 1536 --ink-cap 0.97 --family "Siyam Rupali Mono Edit" --version 0.0.1
# WT-only build (prebase-shift, NO ligature step) - 0.0.1
$PY tools/mono_convert.py     legacy/base-1.070ship.ttf build/SiyamRupaliMono-WT.ttf --cell 1536 --ink-cap 0.97 --family "Siyam Rupali Mono WT" --version 0.0.1 --prebase-shift
# Optional hand-designed glyph fixes (author redraws; see docs/FIXES.md):
#   $PY tools/apply_fixes.py build/SiyamRupaliMono.ttf fixes/<frag>.ttf   # BEFORE hinting
# Hinting (brain venv only): $PY ../agentic-font-dev/scripts/hint.py build/<ttf>
```

Gates (must pass; never weaken to make them pass):
```
$PY ../agentic-font-dev/scripts/qa.py build/SiyamRupaliMono.ttf tests/conjuncts.txt --script beng --language ben                      # 11/11
$PY tools/shape_check.py build/SiyamRupaliMono.ttf --cell 1536 --matrix --context                                                     # 0 failures
$PY tools/shape_check.py build/SiyamRupaliMono-Edit.ttf --cell 1536 --max-cells 3 --matrix                                            # 0 failures; NO --context (no ligatures by design)
$PY build/probe_restore.py                                                                                                            # 5/5: ligatures fire; leftovers KEEP shifted defaults (restore is OFF by default -- WT applies pres WITHOUT reorder, WORKLOG late 9)
```

Visual gates (unshaped render = WT's model; shaped render = kitty/editors):
```
$PY tools/render_probe.py build/SiyamRupaliMono.ttf --cell 1536 --tag UNI --unshaped   # eyeball build/probe/UNI_unshaped_*.png: matra curls sit OVER their base
$PY tools/render_probe.py build/SiyamRupaliMono.ttf --cell 1536 --tag UNI              # eyeball UNI_shaped_*.png: merged 1-cell clusters
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
1a. **RESOLVED by the Universal build (0.0.2), pending author verdict.**
   One font adapts to the renderer via shifted-default art + a pres
   restore lookup (see Cell width variants). Remaining WT-platform
   limit the font cannot fix: conjuncts render letter-by-letter in WT
   (hasanta visible, ক্ষ = ক+ষ; needs upstream shaping — terminal
   PR #16916, issues #17810, #18167). In shaping terminals conjunct+matra
   (ক্ষি) stays 2 cells (open work 2).
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
