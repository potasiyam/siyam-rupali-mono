# PLAN — Two canonical fonts: "Siyam Rupali Mono" + "Siyam Rupali Duo"

Merged architecture, 2026-09-03. Source material: the (fact-checked)
duospace/mono research plan + this project's measured renderer models
(docs/PROOF_2026-09-03.md, docs/SPACING_REPORT.md, WORKLOG late 5–9,
WT8→WT17 line). Supersedes the specialist-variant zoo (Wide / WT / Edit /
Console / Two / Proof / 008 / WT8–WT17 installs) with TWO deliverables.

## Deliverables

| font | family | file | target | version |
|---|---|---|---|---|
| Siyam Rupali Mono | `Siyam Rupali Mono` | `build/SiyamRupaliMono-0100.ttf` | terminals (WT-native line) | 0.1.0 |
| Siyam Rupali Duo | `Siyam Rupali Duo` | `build/SiyamRupaliDuo-0100.ttf` | editors (duospaced) | 0.1.0 |

Filenames stay versioned forever (font-cache poisoning lesson: never
re-point a family at a file that was ever registered under another build).

## Renderer models (measured, this box — the reason two targets exist)

- **Windows Terminal 1.24** runs FULL DirectWrite Bengali shaping
  (reorder + GSUB) for glyph rendering, but charges grid columns per
  codepoint with the conhost mark rules (Extend = 0, mark-run collapse)
  and draws each shaped cluster compact at its FIRST charged column
  (4th-revision model, SPACING_REPORT addendum).
- **WezTerm/Alacritty on Windows** (ConPTY) charge raw codepoint counts
  and shape fully (WezTerm) / not at all (Alacritty).
- **Editors (VS Code etc.)** are gridless: shaped advances rule.
- Consequence: no single font can charge what it draws on all hosts;
  the two families below are the font-side optimum per host class.
  Residuals (conjunct clusters in WT, ক্ in WezTerm) are terminal-side
  and documented, not bugs.

## Siyam Rupali Mono 0.1.0 (terminal target — strict 1-cell)

The WT17 lineage promoted to the canonical name. Spec = the verified
"1-grid + linearization" strategy, realized with the measured tricks the
generic plan lacked (verbatim matra art at full-cell advance, natural-
offset 2-cell reph/ya-phala ligatures, contextual anusvara/visarga/aa
tucks) so that shaped advance == charged columns on the common clusters.

Pipeline (build, hint, gate):

```
PY tools/mono_convert.py legacy/base-1.070ship.ttf build/SiyamRupaliMono-0100.ttf --family "Siyam Rupali Mono" --version 0.1.0
PY tools/gen_wt9_fixes.py build/SiyamRupaliMono-0100.ttf --cell 1404 --version 0.1.0
hint.py build/SiyamRupaliMono-0100.ttf            # brain venv
PY tools/shape_check.py build/SiyamRupaliMono-0100.ttf --cell 1404 --max-cells 3 --matrix   # 0 failures
```

- auto cell 1404 = median native advance (unchanged WT17 behavior);
  spacing matras carry the full cell (author directive 2026-09-03);
  vertical metrics NOT touched (the author's WT line-height is tuned;
  vertical clipping is a line-height-1.0 concern for editors, not WT).
- Reproduction gate: hmtx + glyphOrder must match the WT17 build
  byte-for-byte on advances (names/version differ by design).
- Reference grid checks (programmatic, spacing_report model):
  ka=1, ki=2, kiki=4, kang=2, king=2, korto=3, kortobbo=5.
- Known residuals (accepted, terminal-side): multi-consonant conjunct
  merges (+1 col in WT), ক্-class (+1 col in WezTerm-Windows only).

## Siyam Rupali Duo 0.1.0 (editor target — duospaced)

Verified blueprint: Latin 1 cell, Bengali ~2 cells, editors shape with
font advances. Design decision (measured, see WORKLOG): an EXACT uniform
2-cell advance for every Bengali glyph severs the akshar — native letter
ink (~1785 units) would leave ~260-unit headline gaps against a 2048
advance. Bengali joins by design (matra interlocks); breaking them is
the one thing an editor font must not do. Therefore:

**Uniform Bengali zoom.** One global factor
`s = beng_cell / median(native Bengali letters+conjuncts advances)`
= 2048 / 1487 ≈ 1.377 multiplies EVERY Bengali glyph's art AND advance
(left-aligned, dx = 0 — all designed interlocks scale together exactly;
the stream geometry is the original font's, enlarged). Marks scale art
and their GPOS anchors, keep ~0 advance. Latin/neutral glyphs convert
to a 1024-unit cell (advance-ratio center-preserving rule, unchanged).
Median Bengali letter lands exactly on 2 Latin cells; individual widths
stay proportional (conjuncts wider, matras narrower — by design).

Classes:
- `bn_*` glyphs (Bengali cmap entries + GSUB outputs): art ×s,
  advance = round(native × s). Includes digits (bn_zero..nine, they
  scale with the Bengali design) and all 79 spacing-matra forms.
- everything else (Latin, punctuation incl. danda, symbols): cell 1024
  via the existing sx = min(1, C/A, ink_cap·C/bw) centering rule.
- GDEF-3 / adv < 300 marks: art ×s, advance untouched, anchors ×s.

Pipeline:

```
PY tools/mono_convert.py legacy/base-1.070ship.ttf build/SiyamRupaliDuo-0100.ttf --duo --ink-cap 0.97 --family "Siyam Rupali Duo" --version 0.1.0
hint.py build/SiyamRupaliDuo-0100.ttf
PY tools/shape_check.py build/SiyamRupaliDuo-0100.ttf --cell 1024 --max-cells 6 --matrix   # 0 failures (proportional sanity, no 1-cell gate)
```

- NO CV ligature step (editors use advances; unsqueezed art is the
  point). VOLT GSUB untouched: conjuncts shape normally in editors.
- Vertical bounds fixed (plan Step 2): ink reaches y −921..2493 vs
  declared 2360/−731 — hhea/OS/2 win metrics extended to cover ink
  (+2% pad) so line-height-1.0 renderers don't clip reph/uku stacks.
- Spot gates: width("A") == 1024; width("ক") == 2352 (≈2.30 cells);
  width("কি") == ikaar+ka ≈ 3097; Latin cluster ("code") == 4·1024±.
- Tunables for author iteration: `--beng-cell` (default 2048),
  `--latin-cell` (default 1024), `--ink-cap`.

## Install / ops (poison-lesson discipline)

1. Uninstall EVERY registered `Siyam Rupali Mono*` family value in
   HKCU fonts (12 entries incl. WT8/WT10/WT15/WT16/WT17/Two/Edit/Wide/
   Console/WT/008); delete their files where not locked.
2. Install the two new files under the canonical family names, fresh
   filenames, per-user registry, WM_FONTCHANGE broadcast both ways.
3. Patch WT settings.json profile faces "Siyam Rupali Mono WT17" →
   "Siyam Rupali Mono" (backup first). .wezterm.lua already targets
   family "Siyam Rupali Mono" — correct after re-registration.
4. Verify WHICH file resolves (Rule 5): fresh-process DWrite probe must
   show width(কি)/width(ক) = 2.0 (Mono's verbatim pair; a stale 008
   ligature build measures 1.0) and width(ক)/width(A) ≈ 2.30 (Duo).
   If stale: restart FontCache service (admin) — documented last resort.
5. Live WT cursor probe on the canonical family: ka=1, ki=2, kiki=4,
   king=2, korto=3.

## Out of scope (open work, unchanged)

- 2-cell wide conjuncts for WT's conjunct residual (open work 2).
- ss01 hasanta fallback (open work 4), WOFF2 (5), NBSP-escape system (6).
