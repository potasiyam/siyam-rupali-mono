# AGENTS.md — siyam-rupali-mono

Terminal/mono conversion of Siyam Rupali. Read the brain's spec first:
`../agentic-font-dev/AGENTS.md` (operational spec + named incidents) and the
global rules at `C:\Users\Siyam\.zcode\AGENTS.md`. This file pins only the
project-specific decisions. Session history + evidence: `docs/WORKLOG.md`.

## Project decisions (settled — do not relitigate without new evidence)

- **Architecture (2026-09-03, merged plan):** TWO canonical fonts from one
  pipeline — `docs/PLAN_DUO_MONO.md` is the spec.
  **`Siyam Rupali Mono` 0.1.0** (terminal: WT-native line, cell 1404,
  verbatim matra art at full-cell advance, 2-cell reph/ya-phala ligatures,
  contextual anusvara/visarga/aa tucks) and **`Siyam Rupali Duo` 0.1.0**
  (editor: Latin/danda 1024, Bengali art+advance uniformly zoomed ×1.378
  so the median letter = 2 cells with all native interlocks preserved).
  All specialist variants (Wide/WT/Edit/Console/Two/Proof/008/WT8–WT17)
  are RETIRED: unregistered on this box, regenerable, keep out of installs.
  Family names are canonical and stable; **never re-point a family at a
  file that was ever registered under another build** (cache-poisoning
  incidents, WORKLOG late 5 + 2026-09-01) — fresh filename per build.
- **Terminal model (final, 4th revision, PROOF + SPACING_REPORT
  2026-09-03):** Windows Terminal 1.24 runs FULL DirectWrite Bengali
  shaping (reorder + GSUB) for glyph rendering but charges grid columns
  per codepoint (conhost rules: Extend=0, mark-run collapse) and draws
  each shaped cluster compact at its FIRST charged column. WezTerm/
  Alacritty on Windows charge RAW CODEPOINT counts. Editors are
  gridless (advances rule). This supersedes every earlier "verified"
  model (late 5 "no shaping", late 6 "font-advance charging", late 9
  "pres without reorder") — those captures were taken while WT rendered
  fallback fonts. Consequence: no font can charge what it draws on all
  hosts; residuals (conjunct clusters +1 col in WT, ক্ +1 col in
  WezTerm-Windows) are terminal-side, documented, not bugs.
- **Base binary:** `legacy/base-1.070ship.ttf` = Dropbox
  `Siyamrupali_1_070ship.ttf` (final 2011 release, 789 glyphs, GSUB+GPOS
  compiled by VOLT at export; passed 6/6 golden shaping unchanged).
  Archive fact: `*core.ttf` = pre-VOLT (no GSUB), `*ship.ttf` = post-VOLT.
- **UFO/fea path is PARKED.** `Siyamrupali_1_064.vfb` and `1.064.vtp` are
  divergent snapshots (different glyph sets/orders/names; bridge GID gate
  refuses, 606 vs 607). `sources/` + `legacy/ref.ttf` are kept for
  provenance and a future redesign only.
- **Version line:** `0.1.0` = the canonical pair (alpha series 0.0.x
  preceded it; engineering builds 1.100–1.105 before that).
- **Naming:** `bn_` snake_case, inherited from the base binary; generated
  ligatures follow `bn_<base>_<form>` (`_reph2`, `_yaph2`, `_tuck` from
  gen_wt9_fixes.py). Non-bn names exist for danda (`danda`,
  `doubledanda`) — the Duo classifier keys on the `bn_` prefix.
- **fsType = 0** on output (we are the original author; ttfautohint also
  refuses the inherited restricted bit).
- **Source of truth:** `legacy/base-1.070ship.ttf` (read-only input) +
  `tools/mono_convert.py` (`--duo` = the Duo mode) +
  `tools/gen_wt9_fixes.py` (Mono step 2). `tools/gen_cv_ligatures.py`
  built the retired ligature line — keep for provenance. Never hand-edit
  the built TTFs; regenerate.
- **Duo zoom rule (design decision):** an exact uniform 2-cell advance
  for every Bengali glyph severs the akshar (native ink ~1785 vs 2048
  advance → ~260-unit headline gaps). Bengali joins by design, so Duo
  scales ALL Bengali art AND advances by ONE global factor
  `s = beng_cell / median(native Bengali letters+conjuncts)` (≈1.378),
  left-aligned dx=0 — interlocks survive exactly; median letter lands on
  2 cells; widths stay proportional. Marks zoom art+anchors, keep ~0
  advance. Vertical bounds extended to cover ink (plan Step 2); Mono's
  vertical metrics deliberately untouched (author's WT line-height tune).

## Build (reproducible; drive the scripts directly — no GNU make here)

Brain venv: `I:/projects/agentic-font-dev/.venv/Scripts/python.exe`
(has fontTools + uharfbuzz + vharfbuzz; system python 3.10 lacks
vharfbuzz). `PY=<python>` below.

```
# MONO (terminal, canonical) - 0.1.0
$PY tools/mono_convert.py    legacy/base-1.070ship.ttf build/SiyamRupaliMono-0100.ttf --family "Siyam Rupali Mono" --version 0.1.0
$PY tools/gen_wt9_fixes.py   build/SiyamRupaliMono-0100.ttf --cell 1404 --version 0.1.0    # in place; NO --family here
# DUO (editor, canonical) - 0.1.0
$PY tools/mono_convert.py    legacy/base-1.070ship.ttf build/SiyamRupaliDuo-0100.ttf --duo --ink-cap 0.97 --family "Siyam Rupali Duo" --version 0.1.0
# Both: hint (brain venv), e.g.
$PY ../agentic-font-dev/scripts/hint.py build/SiyamRupaliMono-0100.ttf
# Install/retire (poison-lesson discipline):
powershell -ExecutionPolicy Bypass -File tools/install_canonical.ps1
# Optional hand-designed glyph fixes (author redraws; docs/FIXES.md):
#   $PY tools/apply_fixes.py build/<ttf> fixes/<frag>.ttf   # BEFORE hinting
```

Gates (must pass; never weaken to make them pass):
```
$PY tools/shape_check.py build/SiyamRupaliMono-0100.ttf --cell 1404 --max-cells 3 --matrix   # 0 failures
$PY tools/shape_check.py build/SiyamRupaliDuo-0100.ttf  --cell 1024 --max-cells 6 --matrix   # 0 failures (proportional sanity)
# Mono reference grid rows (shaped cells == WT charge): ka=1 ki=2 kiki=4
# kang=2 king=2 korto=3 kortobbo=5 gar-to=3 bidya=4  (vharfbuzz one-liner,
# see WORKLOG 2026-09-03 two-fonts entry)
# Mono repro gate: hmtx+glyphOrder identical to the previous build of the
# lineage (WT17) — names/version differ by design.
```

Ops probes: fresh-process WPF width probe (which-file gate: Mono
ki/ka ratio must be 2.0; a stale ligature build reads 1.0) + live WT
cursor probe (`build/probe_canonical.ps1` in a `wt new-tab`; result in
`build/probe/canonical_result.txt`).

## Hard rules for this repo (incident-derived)

- **Never compile fea into this font with `addOpenTypeFeatures`** — it
  REPLACES the shipped GSUB (conjuncts die; QA goes 0/6). Append lookups
  via otTables instead (gen_cv_ligatures.py / gen_wt9_fixes.py).
- **Ligature entries per covered glyph must be sorted longest-first**
  (HarfBuzz takes the first match — 3-part ো/ৌ before 2-part ে/ৈ).
- **`glyf[name] = glyph` already appends to glyphOrder** — don't append
  manually (duplicate → maxp assert at save).
- **ChainContextSubst fmt 3 in fontTools: set the record list under BOTH
  names** (`SubLookupRecord` fresh, `SubstLookupRecord` after round-trip)
  or records silently drop; **Coverage arrays must sort by glyph id
  against the CURRENT order**; a nested single-subst must never be
  referenced by a feature directly (unconditional-fire bug).
- **Verify WHICH font an artifact rendered** before believing a capture
  (family-name cache poisoning served fallback pixels twice).
- Verify shaping claims against the vtp-era *binary* streams, not
  assumptions (ৌ's pre-part is `bn_initekaar`, not `bn_initaikaar`).

## Open work (priority order)

0. **Author testing of the canonical pair** (Mono in terminals, Duo in
   editors; findings via the fixes layer, docs/FIXES.md). Verify a
   fully-restarted WT resolves the canonical family (long-running
   processes cache the old mapping; documented restart = FontCache
   service, admin).
1. WT conjunct residual (ক্ত-class +1 col): scoped 2026-09-03 — 247
   reachable conjunct glyphs, 180/247 fit a 2-cell frame at natural
   size (WORKLOG late 3). Shared-Mono wide conjuncts would OVERLAP the
   next cluster on 1-cell-grant hosts (kitty/VTE/WezTerm-Unix);
   specialist build vs shared change vs accept = author decision.
2. `ss01` hasanta-explicit fallback feature.
3. WOFF2 deliverable (needs brotli in a venv).
4. NBSP-escape 2-cell system (font GSUB + Avro terminal-mode) —
   designed, deferred; only path to unsqueezed bare CV clusters in a
   strict terminal grid.
5. Retired-line cleanup: Makefile + gen_cv_ligatures gates in this file
   reference retired builds; refresh if a ligature terminal build is
   ever wanted again (kitty/VTE-targeted).
