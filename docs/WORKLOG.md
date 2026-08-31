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

## 2026-08-31 — readability review: cell-width variants + GPOS anchor fix

**Evidence:** author review of v1 Regular: CV matra clusters (কা কি কী
কে কৈ কো কৌ) "too thin almost unreadable". Measured root cause: median
CV cluster native ink 2969 units vs single letter 1785 (ka) — the 1024
cell (ink budget 942) forces clusters to ~0.32 uniform squeeze (letters
0.62). Fixed-region per-part layout made it worse (base art alone at
0.31–0.43 with mismatched stroke weights between parts).

**Decisions (see AGENTS.md / docs/TERMINAL.md):**

- Strict mono stands (1 cluster = 1 cell). The fix is widening the CELL,
  not widening clusters: ships as three variants sharing one pipeline —
  Regular 1024 (v1.100), Wide 1536 (v1.101, recommended), Fullwidth 2048
  (v1.102). Measured squeeze table in docs/TERMINAL.md.
- gen_cv_ligatures.py: new --cv-cell N wide mode — parts laid out
  left-to-right at ONE uniform scale (consistent stroke weight inside a
  cluster), centered in the frame; legacy 1024 keeps the fixed regions
  for reproducibility. New --family/--version for variant naming.
- 2-cell-cluster "WideCV" build (cv-cell 2048 with 1024 cells) was built
  and then deleted: kitty modify_font verified (docs, 2026-08-31) to
  support only underline/strikethrough/cell/baseline — no per-codepoint
  width; WezTerm/Windows Terminal likewise. 2-cell clusters would
  overlap the next column in every terminal.
- **Bug found & fixed in mono_convert.py:** MarkToBase base anchors were
  moved only when sx != 1.0, but identity glyphs (sx=1) are still
  re-centered by dx — below-marks drifted (কু x_offset -788 vs correct
  attachment) at cell 1536/2048 where most glyphs are identity. Anchors
  now move on every transformed base (X = sx*X + dx always). The 1024
  build was unaffected (all anchor-carrying bases were condensed there;
  31 moves before and after the fix).

**Environment note:** brain venv absent on this machine
(I:/projects/... missing). Built with system Python 3.12.10 + fontTools
4.63.0 + uharfbuzz 0.56.0 + vharfbuzz 0.3.1 (winget-installed). hint.py/
qa.py NOT run here; rerun in the brain venv.

**Gates:** shape_check --matrix 0 overflow on all three variants
(Regular --cell default, Wide --cell 1536, Fullwidth --cell 2048).
Logs: build/shape_matrix.log, build/fw_sample.log, build/orig_sample.log
(original-font ground truth: কু attaches at x_offset -448 at adv 1708).

### Verdict same day — Fullwidth adopted, Wide deleted

Author verdict on the Wide (1536) build: adds cell width without fixing
compression (clusters still 0.49x). **Fullwidth (2048) adopted as the
recommended build** (clusters 0.66x, letters unsqueezed). Wide deleted.

Key discovery while reviewing the author's observation that conjuncts
show "two blocks" while bare CV is one cell: the terminal grant per
cluster = SUM of wcwidth of codepoints. Bare ki = 1+0 = 1 cell (hard
ceiling, font-side unfixable); conjunct+matra = 1+0+1+0 = 2 cells. The
font already matches both grants; the asymmetry is Unicode/terminal
geometry, not a bug.

NBSP-escape system designed and deferred (AGENTS.md open work #6):
base + NBSP + matra = 1+1+0 = 2-cell grant; font ligates [base NBSP
matra] into a 2048-unit glyph of unsqueezed art; contextual rule
zeroes standalone NBSP; requires an Avro terminal-mode to emit NBSP.
Cost: text carries NBSP (search/copy implications). Only viable path
to unsqueezed bare CV clusters.

Deliverables now: SiyamRupaliMono-Regular.ttf (v1.100),
SiyamRupaliMono-Fullwidth.ttf (v1.102). docs/TERMINAL.md rewritten
around the two-variant story + grant table.

## 2026-08-31 (late) - faithful ligature layout; Wide 1536 rebuilt

Author insight: matra signs JOIN the base by design (the script's akshar
system) - touching/overlap between base and matra parts is intended, not
collision. Measured proof in the base font: bn_ikaar ink 660 vs advance
541; bn_iikaar ink 1636 vs advance 533 (the curl sweeps across the base
x-range); bn_ka ink 1785 vs advance 1708.

Consequence: the bbox side-by-side packing (layout_proportional) double-
counted the designed interlock zones AND inserted gaps that severed the
akshar. New layout_faithful(): parts placed at original pen offsets
(sum of original advances), whole assembly scaled to the frame, ink
block centered, safety shrink if curls overshoot the span.

Numbers at cell 1536, ink-cap 0.97: CV cluster scale median 0.523 ->
0.677 (+29pct less squeeze), min 0.416, max 0.945. Letters unchanged
(median 0.85, mono_convert --ink-cap 0.97). Gates: matrix 0 overflow,
all clusters exactly 1 cell, below-marks attach at sane offsets.

Deliverable: build/SiyamRupaliMono-Wide.ttf v1.103 (family 'Siyam
Rupali Mono Wide'). gen_cv_ligatures gained --layout {faithful,pack}
(faithful default), --ink-cap, --gap. mono_convert run with
--cell 1536 --ink-cap 0.97.

## 2026-08-31 (late 2) - init-variant coverage bug (user-reported)

Bug: mid-word ে/ৈ clusters did NOT ligate (e.g. kUke rendered 2 cells
while ke was 1). Root cause (verified in binary GSUB): init feature maps
bn_ekaar->bn_initekaar, bn_aikaar->bn_initaikaar at word starts; CV
ligature rules only covered the init forms. HarfBuzz applies init after
word boundaries so all our golden tests passed; the author's renderer
applies init differently, exposing it. Also explains the earlier
'line widths do not match' report (renderer-dependent init -> some
clusters ligated, others not).

Fix: PRE_VARIANTS in gen_cv_ligatures - standard forms get their own
ligature glyphs (bn_ka_ekaar_std etc, 144 new glyphs; outlines verified
DIFFERENT from init forms, so aliasing was not an option) and rules
keyed on both bn_initekaar and bn_ekaar (initaikaar/bn_aikaar).
make_ligature() refactor (strict/wide paths unified).

Gate: shape_check gained CONTEXT_RULES (kUke must produce
bn_ka_ekaar_std etc). All pass; user strings verified: kUke/kUko/kUkau
now 3 cells (ligated), both test lines identical widths in spaced AND
unspaced variants. Deliverable: build/SiyamRupaliMono-Wide-v1104.ttf
v1.104, 1185 glyphs (396 CV ligature rules). Old Wide ttf was file-
locked (installed font); new build written under -v1104 name.

## 2026-08-31 (late 3) - two-surface deliverable + kar no-squeeze rule

Author decision: font must serve BOTH surfaces. Deliverables now:
- build/SiyamRupaliMono-Wide-v1105.ttf - TERMINAL build (cv ligatures,
  init+std coverage, 1-cell clusters). family 'Siyam Rupali Mono Wide'.
- build/SiyamRupaliMono-Edit.ttf - EDITOR build (mono_convert only, NO
  cv ligatures): matras keep their own full cell, everything unsqueezed
  below the 0.97 cap. family 'Siyam Rupali Mono Edit'. In gridless
  editors font advances rule, so 2-cell ka-kaar / 3-cell ko/au is
  correct and maximally readable. Gate: --max-cells 3, 0 failures
  (context rules are terminal-only, now behind --context flag).

Kar no-squeeze rule (author directive): vowel-sign glyphs are never
x-condensed - native ink centered in the cell, advance = cell,
symmetric overflow into neighboring bearings instead of distortion
(mono_convert is_kar(): *kaar except okaar/aukaar independent vowels,
plus bn_aumark). Caught bn_ikaar native ink 1541 > 1490 cap being
silently squeezed; now renders native with lsb=rsb=-2. Condensed count
drops 325 -> 258.

## 2026-08-31 (late 4) — alpha 0.0.1 + hand-fixes layer

Author wants to test the two surfaces personally and hand-design
character fixes. Version line moved to **0.0.1** (alpha series;
1.10x numbers were pre-release engineering builds).

Built in the brain venv (this machine) — closing the gap noted in
"readability review" (v1.10x was built on system Python with hint/qa
skipped): both surfaces rebuilt, hinted, and gated here:
- build/SiyamRupaliMono-Wide.ttf 0.0.1 (1185 glyphs): qa 11/11,
  shape_check --cell 1536 --matrix --context = 0 failures.
- build/SiyamRupaliMono-Edit.ttf 0.0.1 (789 glyphs): shape_check
  --cell 1536 --max-cells 3 --matrix = 0 failures.
Measured: Wide letters median 0.851 condense, worst 0.54 (triple
conjuncts); CV ligature uniform scale median 0.647.

**Fixes layer (new):** author redraws survive rebuilds via
tools/extract_fixes.py + tools/apply_fixes.py + fixes/*.ttf fragments.
Round-trip tested with a synthetic 2-glyph edit: extract diffs geometry
(RecordingPen signature, composites decomposed — hint bytecode ignored
since we re-autohint), apply merges and re-pins advances to the cell.
Full designer workflow: docs/FIXES.md (FontLab-centric: edit a copy of
the build, outlines only, no rename/add/delete; fragments are
per-surface and committed as the permanent record).

fontTools gotchas hit while building the fragment (both fixed in code):
lazy table decompile after pruning glyphOrder IndexErrors (hmtx reads
the order at decompile — force-decompile everything first); the
fragment must keep a post 2.0 table or TTFont synthesizes glyphNN
names and the bn_* names are lost.

## 2026-08-31 (late 5) — WT alpha diagnosis: font-cache fallback + WT grid semantics

Author report: "mono wide spacing is not correct" in Windows Terminal
(WT 1.24) with `আমার নাম সিয়াম` / `কা কি কী কে কৈ কো কৌ`. Two stacked
root causes found; neither is the font binary.

**Cause 1 — WT could not find the Wide font (stale DirectWrite font
cache).** Setting the WT face to "Siyam Rupali Mono Wide" popped
"Unable to find the following fonts: Siyam Rupali Mono Wide". The
registry entry and file were correct (hashes matched build/), but the
Wide install had history: the v1.104-era install was file-locked when
replaced, and the cache never refreshed. Edit (clean install) resolved
fine — which is why the author's Edit screenshot was our font but the
Wide screenshot was a FALLBACK font (proportional matras crammed into
per-codepoint cells — the "wrong spacing" look). Fix: re-registered
under a new filename (SiyamRupaliMono-Wide-Alpha.ttf) + WM_FONTCHANGE
broadcast (build/fix_wide_install.ps1). Warning gone. Rule 5 lesson:
the WT dialog was ground truth; two vision passes on the screenshot
both misread it.

**Cause 2 — WT grants columns by per-codepoint sum, not clusters, not
advances.** Measured via cursor-position probe (build/probe_wt2.ps1,
probe_wt3.ps1; PS prints string, reads RawUI cursor X in cells, writes
result file — no vision involved): কা/কি/কী/কে/কৈ/কো/কৌ = 2 cells
each, ক্ষ/ক্ত = 2, কু/ড়/ক্ = 1, কং = 2. That is exactly
sum(per-codepoint width) with Mn=0, Mc=1 — WT ignores the font's
1-cell ligature advances for its grid. Cross-checks: HarfBuzz ligates
all of them (shape_check); WPF/DirectWrite also applies our appended
pres lookup (build/probe_dwrite.ps1: width(কা)=width(ক)=36px, কো=36px
vs Edit 72/108px) — so the font and DWrite are correct; WT's grid
layer is the odd one out. v1.104's "3 cells (ligated)" observation was
this same behavior (ink joins, grid still charges per matra).

Consequences:
- In WT today, **Edit is the grid-perfect build** (its per-glyph
  advances equal WT's grant exactly). Wide renders joined ligature ink
  + trailing slack per cluster.
- The strict-mono premise "terminals: Bengali cluster = 1 cell" is
  wrong for WT (right for pango/VTE-family). AGENTS.md decision block
  annotated; open work 1a added: accept Edit-in-WT, or a WT-matched
  variant with ligature advance = granted cells (plan hybrid
  resurrected), or wait for upstream (terminal PR #16916, #17810,
  #18167).

Ops notes: WT settings.json was backed up, flipped to Wide for
testing, and restored byte-identical (face back to Edit). Probe tabs
may be left open in WT. New tools: tools/render_probe.py (HB+freetype
render with cell grid), tools/ink_fill_report.py (ligature ink fill:
396 glyphs all 0.93-0.97 of cell — between-cluster raggedness ruled
out), build/probe_dwrite.ps1 (WPF/DWrite shaping probe),
build/probe_wt2/3.ps1 (WT cursor-column probes).

## 2026-08-31 (late 6) — author retest confirms unshaped rendering; WT-native variant 0.0.1

Author retested both fonts in WT (screenshots). Wide now actually loads
(cache fix worked — condensed letterforms visible) and both surfaces
show the SAME structural behavior: matra ink drawn AFTER the base in
its own cell, i.e. **WT draws cmap glyphs in codepoint order with NO
cross-codepoint shaping**. Combined with the late-5 column probes, WT's
full model: columns = sum of per-codepoint font advances (GDEF-3 marks
~0, spacing signs 1 cell), rendering unshaped. GDEF spot-check matches
every probe: bn_ikaar GDEF1 adv541->cell => কি=2; bn_ukaar GDEF3 adv0
=> কু=1; bn_anusvara GDEF1 adv810 => কং=2. Font data IS the WT grid.

**WT-native variant built** (`--prebase-shift` in mono_convert.py):
PREBASE_SHIFT = {ikaar, ekaar, aikaar, okaar, aukaar, anusvara} — these
carry pre-base/above art but land AFTER the base in codepoint order, so
their ink shifts LEFT one cell (dx -= cell after centering) and the
curl sits over the base cell; the matra's own cell is (near-)empty —
correct look across the columns WT already grants. No ligatures (WT
cannot fire them). build/SiyamRupaliMono-WT.ttf 0.0.1: letters median
0.851 condense (same as Wide), okaar/aukaar 0.58 (independent-vowel
squeeze path), hinted, shape_check --max-cells 3 --matrix = 0 failures.
qa.py intentionally NOT run: goldens expect ligature glyph names; WT
font has none BY DESIGN. render_probe.py gained --unshaped (cmap order
+ font advances = WT's model): WT_unshaped_0/1/2.png eyeballed — আমার
নাম সিয়াম and কা কি কী কে কৈ কো কৌ (spaced + unspaced) all read
correctly with grid-aligned ink. Installed for the author
(build/install_wt.ps1, fresh filename, per-user).

Deliverable reality is now THREE surfaces: Wide (pango/VTE terminals,
shaped), WT (Windows Terminal, unshaped-by-design), Edit (gridless
editors). Known WT-platform limit the font cannot fix: conjuncts render
letter-by-letter with visible hasanta (ক্ষ = ক+ষ; no shaping in WT
until upstream lands it — PR #16916, #17810, #18167). AGENTS.md updated
(goal challenge note + variants + build/gates + open work 1a).

## 2026-08-31 (late 7) — UNIVERSAL "Siyam Rupali Mono" 0.0.2: one font, renderer-adaptive

Author verdict: "I want a universal mono font" — not three specialists.
Built. Mechanism (renderer-adaptive art):
- mono_convert --prebase-shift now ships the six pre-base/above-mark
  glyphs (ikaar ekaar aikaar okaar aukaar anusvara) WITH SHIFTED art
  under their ORIGINAL names (WT renders them unshaped, codepoint
  order) and stores centered art in new <name>_shaped copies.
  Verified first: NO VOLT lookup covers these six glyphs (coverage scan
  empty) — they are pure cmap entry points; hb does reordering/splitting
  at codepoint level, so in-place art shifting is invisible to shaping.
- gen_cv_ligatures appends pres lookups in a LOAD-BEARING order:
  LigatureSubst (14) first — keyed on the original names, fires before
  anything renames them — then a SingleSubst restore (15)
  {bn_X -> bn_X_shaped} for non-ligated leftovers (conjunct+matra,
  stray anusvara) so shaping renderers draw centered art on the correct
  side. In WT no GSUB runs: shifted art + cell advances = correct look
  at WT's own grant (2 cols/cluster).

fontTools traps (both named for the next session):
1. SingleSubst in fontTools 4.63 is FormatSwitching — construct with
   .mapping = {cov: sub} dict. Manual Format/Coverage/substitute attrs
   are silently ignored and the compiled lookup comes out EMPTY
   (restore dead; caught by probe_restore.py asserting bn_ikaar_shaped).
2. f.getGlyphOrder() returns the LIVE list: glyf[name]=glyph inside the
   conversion loop appends mid-iteration (KeyError on the new name).
   Snapshot with list(...) — mono_convert does now.

Gates on build/SiyamRupaliMono.ttf 0.0.2 (hinted): qa 11/11; shape_check
--matrix --context 0 failures; probe_restore ligatures+restore all
correct (k_ssa_i -> bn_ikaar_shaped bn_k_ssa; ka_ng -> bn_ka
bn_anusvara_shaped); render_probe shaped = merged 1-cell clusters,
unshaped = split-cell correct-side curls. Installed for the author as
"Siyam Rupali Mono" (build/install_universal.ps1). Wide/WT/Edit remain
installed for comparison; expect them to be retired on author verdict.
Trade-off recorded: in the universal font, editors ALSO see 1-cell
ligatures (not Edit's unsqueezed 2-cell layout) — that is what makes it
universal; Edit survives as the maximal-readability alternative.

## 2026-08-31 (late 8) — WezTerm (Windows) test of Universal 0.0.2

Author has WezTerm 20240203 (bundled conpty.dll + OpenConsole). Temp
config ~/.wezterm.lua (font = 'Siyam Rupali Mono', size 14 — LEFT IN
PLACE for author testing; delete or edit to revert). Cursor probe
(build/probe_wt2.ps1 via cmd /k) + screenshot:

- Render: SHAPED — merged CV ligature art (pres fires under wezterm's
  harfbuzz; ি curls over the base, all seven test clusters correct).
  First Windows terminal besides raw DWrite to apply our lookups.
- Cursor/grid: SAME per-codepoint model as WT (clusters8=14, spaced7=20,
  each CV cluster = 2 columns) because on Windows wezterm inherits
  ConPTY's buffer model. Result: ligature ink fills 1 column + a
  phantom empty column per cluster — art correct, cursor aligned,
  rhythm airy.
- Difference vs WT numbers: name=15 here vs WT 14 — wezterm's bundled
  conpty charges the nukta in য় 1 column while WT's newer OpenConsole
  gives it 0. ConPTY width tables differ by version; the font cannot
  control this.
- Takeaway: Universal degrades gracefully across column models —
  merged art + phantom gap on 2-col hosts (WT-style grids), exact
  1-cell fit on 1-col hosts (kitty/VTE/wezterm-on-Unix). The split-art
  design (WT font) would fill wezterm-Windows' extra column but would
  OVERLAP on 1-col hosts — universal stays the right default.

Probe windows left open in wezterm for the author (title
C:\Windows\system32\cmd.EXE with the Bengali lines is the live one).
