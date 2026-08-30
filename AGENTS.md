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
- **Base binary:** `legacy/base-1.070ship.ttf` = Dropbox
  `Siyamrupali_1_070ship.ttf` (final 2011 release, 789 glyphs, GSUB+GPOS
  compiled by VOLT at export; passed 6/6 golden shaping unchanged).
  Archive fact: `*core.ttf` = pre-VOLT (no GSUB), `*ship.ttf` = post-VOLT.
- **UFO/fea path is PARKED.** `Siyamrupali_1_064.vfb` and `1.064.vtp` are
  divergent snapshots (different glyph sets/orders/names; bridge GID gate
  refuses, 606 vs 607). The vtp name drift vs 1.070 binaries (80/474) is
  moot while layout is never recompiled. `sources/` + `legacy/ref.ttf`
  are kept for provenance and a future redesign only.
- **Version line:** `1.100` (Term series fork; version history in the font
  binaries runs 1.002–1.070).
- **Naming:** `bn_` snake_case, inherited from the base binary; generated
  CV ligatures follow `bn_<base>_<matra>`.
- **fsType = 0** on output (we are the original author; ttfautohint also
  refuses the inherited restricted bit).
- **Source of truth:** `legacy/base-1.070ship.ttf` (read-only input) +
  `tools/mono_convert.py` + `tools/gen_cv_ligatures.py` (all mutations).
  Never hand-edit the built TTF; regenerate.

## Build (reproducible; no GNU make on this machine — drive directly)

```
PY=I:/projects/agentic-font-dev/.venv/Scripts/python.exe   # brain venv
$PY tools/mono_convert.py     legacy/base-1.070ship.ttf build/work.unhinted.ttf
$PY tools/gen_cv_ligatures.py legacy/base-1.070ship.ttf build/work.unhinted.ttf build/SiyamRupaliMono-Regular.ttf
$PY ../agentic-font-dev/scripts/hint.py build/SiyamRupaliMono-Regular.ttf
```

Gates (both must pass; never weaken to make them pass):
```
$PY ../agentic-font-dev/scripts/qa.py build/SiyamRupaliMono-Regular.ttf tests/conjuncts.txt --script beng --language ben
$PY tools/shape_check.py build/SiyamRupaliMono-Regular.ttf --matrix   # 0 overflow expected
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

1. Visual review at 12–16px (hb-view or FreeType render sheet) —
   condensation median 0.62 needs eyeballing; worst triple conjuncts 0.30.
2. Conjunct + spacing matra (র্কি class) still 2 cells — v2: contextual
   base alternates + matra-as-mark.
3. GPOS above-marks (anusvara/visarga) for কং -class clusters.
4. `ss01` hasanta-explicit fallback feature (plan Phase 3).
5. WOFF2 deliverable (needs brotli in a venv).
