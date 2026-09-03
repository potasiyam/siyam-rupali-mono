# REPORT — Two canonical fonts: Siyam Rupali Mono + Siyam Rupali Duo 0.1.0

Session report, 2026-09-03. Directive: merge the fact-checked duospace
research plan into this project as two fonts ("Siyam Rupali Mono" and
"Siyam Rupali Duo"), plan in depth, execute, then commit and push.

## 1. What was asked and delivered

| Deliverable | Status |
|---|---|
| In-depth merged plan | `docs/PLAN_DUO_MONO.md` |
| **Siyam Rupali Mono 0.1.0** (terminal) | `build/SiyamRupaliMono-0100.ttf` — built, hinted, gated, installed |
| **Siyam Rupali Duo 0.1.0** (editor) | `build/SiyamRupaliDuo-0100.ttf` — built, hinted, gated, installed |
| Variant zoo retired | 11 `Siyam Rupali Mono *` families unregistered, files deleted |
| Verification | fresh-process WPF probe + live WT cursor probe — all exact |
| Docs | AGENTS.md rewritten to the two-font state; VERSIONS.md updated; WORKLOG entries; plan doc |
| This report + commit/push | this file; pushed to `origin/review/term-vs-alpha` |

## 2. Research fact-check (inputs to the merge)

Verified claims before adopting the pasted plan (sources in the session
transcript; summary in the conversation):

- **Correct:** `pres` pipeline position (after reorder/half, before
  abvs/blws/psts); `bng2` tag; abugida framing; matra-continuity and
  vertical-clipping concerns; monoline advice; Mitra Mono is real
  (Mukti lineage, xterm); the two-target (editor vs terminal) split.
- **Wrong:** "Noto Sans Mono" as duospaced-Bangla (it has NO Bengali);
  GNU Unifont as a shaping duospace (dual-width bitmap, no shaping at
  all); duospaced 2-cell "maintains strict terminal alignment" (only
  CJK has the Unicode width property that makes terminals grant 2
  cells — Bengali clusters charge 1 column, or per raw codepoint on
  ConPTY hosts); "Sublime fully supports GSUB"; "FreeType validates
  shaping" (it rasterizes).
- **Invalid as written:** many-to-many FEA substitution (feaLib:
  "Direct substitution of multiple glyphs by multiple glyphs is not
  supported"); i-kar as a GPOS anchor mark (pre-base matras are
  reordered spacing signs, not anchored marks).
- **Omitted:** `cjct` (the v2 conjunct stage) — the authoritative
  HarfBuzz order is nukt akhn rphf rkrf pref blwf half abvf pstf vatu
  **cjct** init pres abvs blws psts haln.
- **Measured locally:** the doc's wide-glyph examples fail against our
  base font (য = 1288 units is among the NARROWEST; only ঞ = 2227 is
  actually wide). The doc's "HarfBuzz CLI + real terminals" validation
  advice was adopted; its terminal expectations were corrected to the
  measured 4th-revision model.

## 3. Design decisions (full rationale in PLAN_DUO_MONO.md)

- **Mono = the WT17 lineage promoted to the canonical name.** It is the
  measured font-side optimum for WT-family hosts: shaped advance equals
  charged columns on all common clusters (verbatim matra art at
  full-cell advance, natural-offset 2-cell reph/ya-phala ligatures,
  contextual anusvara/visarga/aa tucks).
- **Duo = uniform Bengali zoom, not exact-2C widths.** An exact 2-cell
  advance for every Bengali glyph severs the akshar (native letter ink
  ~1785 units vs a 2048 advance → ~260-unit headline gaps; Bengali
  joins by design). Instead ONE factor s = 2048/1486 ≈ 1.378 scales
  every `bn_*` glyph's art AND advance (left-aligned), preserving all
  interlocks exactly; median Bengali letter lands exactly on 2 Latin
  cells; Latin/danda/space convert to a 1024 cell; marks zoom art and
  GPOS anchors with ~0 advance kept. Duo also fixes the inherited
  vertical-bounds clipping risk (ink −921..2493 vs declared 2360/−731
  → now 2542/−939).

## 4. Build + gates (all green)

- Mono: `mono_convert` (auto cell 1404) → `gen_wt9_fixes --cell 1404`
  → ttfautohint. **Reproduction gate:** glyphOrder 862 == WT17 and
  **zero** hmtx mismatches — the lineage is byte-faithful under the
  canonical name/version. `shape_check --cell 1404 --max-cells 3
  --matrix` = **0 failures**.
- Mono reference grid rows (vharfbuzz shaped cells vs WT charge):
  ka 1/1, ki 2/2, kiki 4/4, kang 2/2, king 2/2, korto 3/3,
  kortobbo 5/5, গর্ত 3/3, বিদ্যা 4/4 — **9/9 exact**.
- Duo: `mono_convert --duo --ink-cap 0.97` → ttfautohint.
  `shape_check --cell 1024 --max-cells 6 --matrix` = **0 failures**.
  Shaping intact (ক্ত→bn_k_ta 2.46 cells, ক্ষ→bn_k_ssa 2.47,
  জ্ঞ→bn_j_nya, বিদ্যা 5.64); A/space/danda exactly 1.000 cells;
  ক 2.30, কি 3.03; vertical bounds 2542/−939; fsType 0.

## 5. Install/ops

`tools/install_canonical.ps1`: uninstalled **11** variant families
(Edit/Wide/WT/008/Two/WT8b/Console/WT10/WT15/WT16/WT17 — all files
deleted, none locked), registered the two canonical families from fresh
filenames (`-0100`), broadcast WM_FONTCHANGE, patched WT settings.json
faces to "Siyam Rupali Mono" (backup: `settings.json.bak-canonical`).
`.wezterm.lua` untouched — it already targets family "Siyam Rupali
Mono", which now resolves to the canonical terminal build.

## 6. Verification (Rule 5 — which font, measured)

- **Fresh-process WPF/DWrite:** Mono width(কি)/width(ক) = **2.00** (a
  stale ligature-era cache would read 1.0 → the family resolves to the
  NEW file); width(A) = 32.91 px = 1404/2048 @ 48 px exactly. Duo
  width(A) = 24.0 px exactly; ক 55.17 px = 2.30 cells; কি 72.66 px =
  3.03 cells — all match design to the pixel.
- **Live Windows Terminal cursor probe** (`build/probe_canonical.ps1`
  in a fresh tab): ka=1, ক্=1, ক্ষ=2, ক্ত=2, ki=2, kiki=4, king=2,
  korto=3 — **8/8 exact** on the canonical family.
- Caveat: a WT process that was already open during the re-registration
  keeps its per-process DWrite mapping — fully restart WT if any old
  window still shows retired glyphs (FontCache service restart is the
  documented admin last resort).

## 7. Known residuals (terminal-side, accepted + documented)

- Conjunct clusters (ক্ত-class) leave charged-but-empty columns in WT
  (+1) and WezTerm-Windows (+2, raw-codepoint charging); ক্ charges 2
  in WezTerm-Windows vs 1 drawn. No font can fill those columns while
  shaping merges the cluster; upstream fix direction = terminals
  charging shaped cluster widths (PR #16916 direction). The font-side
  lever that remains: 2-cell wide conjuncts (reph2 pattern generalized,
  open work 1).

## 8. Files changed

- `tools/mono_convert.py` — `--duo/--latin-cell/--beng-cell` modes,
  mark-anchor scaling, vertical-bounds fix, per-class cells.
- `tools/install_canonical.ps1` — canonical install/retire ops.
- `docs/PLAN_DUO_MONO.md`, `docs/REPORT_2026-09-03_two_fonts.md` (this
  file), `docs/VERSIONS.md`, `docs/WORKLOG.md`, `AGENTS.md`.
- `build/` artifacts (SiyamRupaliMono-0100.ttf, SiyamRupaliDuo-0100.ttf,
  probe_canonical.ps1, probe results) are gitignored by design;
  everything regenerates from the tracked sources.
