# Siyam Rupali Mono — Terminal Conversion Plan

> **Execution status (2026-08-30):** v1 shipped as strict mono — see
> `docs/WORKLOG.md` and `AGENTS.md` for what changed during execution and
> why: (1) base is the `1.070ship` binary, not the vfb/UFO path (the 1.064
> vfb/vtp are divergent snapshots); (2) strict 1-cell mono replaced the
> 600/1200 hybrid (terminals derive width from wcwidth, so 2-cell Bengali
> desyncs the grid; Monotty, the reference model, is deprecated by its own
> maintainers); (3) upem is 2048 → cell = 1024; (4) spacing matras fixed
> via 252 generated CV ligatures. The original plan text follows unchanged.

> Goal: Convert Siyam Rupali (proportional Bangla) to `Siyam Rupali Mono/Term` — **hybrid mono/duo**: `1 grapheme cluster = 1 or 2 terminal cells` (adaptive width, fixed grid).
> Owner: potasiyam (original author) — no license fork issue.
> Reference model: `Monotty` (Tamil mono) + `Sarasa Term` (CJK duospace) — same `GSUB/GPOS -> 1 or 2 cells` constraint.
> Target cell: `UPM 1000 -> base 600` (half-width), `Bengali wide 1200` (full-width). Hybrid adaptive.

## 1. Constraints & Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Cell model** | **Hybrid duospace: 1 grapheme = 1 cell (600) OR 2 cells (1200)** | Best of both: simple akshars stay dense (1 cell), complex conjuncts breathe (2 cells). Grid stays aligned if terminal respects per-glyph advance. |
| **Width mapping** | `Latin/ASCII 600 (1 cell)`, `Bengali simple 600 (1 cell)`, `Bengali conjuncts/complex 1200 (2 cells)` | Prevents illegible squeeze of `ক্ষ্ম, ন্দ্র, জ্ঞ` at 600. See Phase 2 classification. |
| **Fallback** | Keep `hasanta-explicit` GSUB path via `ss01` for legacy `VTE/Alacritty` without shaping | Allows same file to degrade gracefully |
| **Line metrics** | `ascent 850 / descent -150 / lineGap 0` | Bangla `matra` + `phala/kar` above/below need 1000+ safe band |
| **Compatibility** | Requires `Kitty >=0.30, WezTerm, foot, Windows Terminal >=1.18` with HarfBuzz. Must enable per-glyph `wcwidth` (1 or 2) | `Alacritty/VTE/xterm` ignore variable advance -> fallback to `ss01` |
| **isFixedPitch flag** | Set `0` (proportional) or `2` (duospaced) per spec — **not** `1`, to signal hybrid | `1` = strict mono breaks 1200 glyphs; `0` is correct for duospaced |

### Why this is hard for Bangla (`CTL`)

Siyam Rupali uses `GSUB: blwf, half, pres, pstf, rphf, vatu, abvs, blws` + `GPOS: mark, mkmk` to shape:

* Reordering: `ে` before base, split `ো = ে+া`
* Conjuncts: `ক+্+ষ = ক্ষ (~250 ligatures)`, `র্+ক = র্ক`, `ক+্+র = ক্র`, `ৎ (khanda ta)`
* Marks: 6 vowel signs with left/right/above/below positioning

Simple akshars must fit `600` (`bb <= 552`); complex conjuncts allowed `1200` (`bb <= 1104`). Classification decides squeeze amount.

## 2. Source Audit

1.  Export `Siyam Rupali.sfd/.glyphs/.ufo` -> inventory:
    ```bash
    hb-shape SiyamRupali.ttf "ক্ষ জ্ঞ র্ক্য ক্র ো ৌ" --features="*"
    ttx -t GSUB -t GPOS SiyamRupali.ttf
    ```
2.  Count ligature glyphs: ~200-300 conjuncts. List those with `width > 600` or `bb > 552`.
3.  Audit anchors: `abvs` (above-base), `blws` (below-base), `mark/mkmk` for `kar/phala/hasanta`. Find overflows.

## 3. Conversion Pipeline

### Phase 0 — Scaffolding (1 day)
- [ ] Clone `Siyam Rupali` source into this repo `/sources`
- [ ] Add `sources/SiyamRupaliMono.sfd` copy, version bump `1.001 -> 1.100-Term`
- [ ] Set `fontTools` build env: `python3 -m venv venv; pip install fonttools fontforge`

### Phase 1 — Metrics Lock (1 day)
- [ ] `OS/2.xAvgCharWidth = 750` (avg of 600/1200), `OS/2.panose 2 11 6 9 ...`, `post.isFixedPitch = 0` (duospaced), `hhea.advanceWidthMax = 1200`
- [ ] `hhea/metrics`: `ascent 850, descent -150`, `winAscent 850, winDescent 150`
- [ ] Set `width = 600` for: `Latin, digits, punctuation, Bengali bases, vowel signs, simple CV`
- [ ] Set `width = 1200` for: `conjunct ligatures (2+ consonants), kssa/gya/ndra groups, reph+conjunct, split-vowel ligatures that overflow 600` — see `tools/classify_width.py`

### Phase 2 — Conjunct Scaling & Width Classification (load-bearing, 5-7 days)
- [ ] Classify glyphs into `W=600` vs `W=1200`:
  ```python
  # tools/classify_width.py
  SIMPLE = set(["ka", "kha", ...]) # 1 consonant + optional vowel
  COMPLEX = set(gsub_ligatures) # any 2+ consonants: kssa, gya, ndra, rkra etc.
  for g in font.glyphs():
      g.width = 1200 if g.glyphname in COMPLEX else 600
  ```
- [ ] Auto-scale pass (FontForge python) — different caps:
  ```python
  for g in font.glyphs():
    W = g.width  # 600 or 1200
    M = 0.92*W
    bb=g.boundingBox(); gw=bb[2]-bb[0]
    if gw > M:
        s=M/gw; g.transform((s,0,0,1,0,0))
        g.left_side_bearing = (W - (g.boundingBox()[2]-g.boundingBox()[0]))/2
  ```
  `600` glyphs: max squeeze `0.85x` before switching to `1200` bucket. `1200` glyphs: squeeze `0.80-0.95x` only.
- [ ] Manual review: `ক্ষ (600 OK?), ক্ষ্ম/জ্ঞ/ন্দ্র/ত্ত্ব (promote to 1200)`, `র্ক/ক্র/র্য (600)` — hybrid keeps density where legible.
- [ ] Re-create split vowels `ো, ৌ, ৈ` as `600` ligatures if `bb<=552`, else promote to `1200`

### Phase 3 — GPOS/Anchor Fixup (2 days)
- [ ] Re-attach `abvs/blws` anchors to stay inside `y=[-80, 750]` band
- [ ] Set `hasanta, reph, raphala` as `0-width` marks via `GDEF` mark class
- [ ] Add `ss01` stylistic set: `hasanta-explicit` (no conjunct) for debug/legacy terminals

### Phase 4 — Build & Flags
- [ ] Generate `TTF/OTF/WOFF2`:
  ```bash
  fontforge -lang=ff -c 'Open("SiyamRupaliMono.sfd"); Generate("build/SiyamRupaliMono-Regular.ttf")'
  ```
- [ ] Post-process with `fontTools` to enforce `hmtx` and `isFixedPitch` (script in `tools/fix_monospace.py`)
- [ ] Hint with `ttfautohint` (Bangla `matra` needs strong stem hints)

### Phase 5 — Verification (hybrid-aware)
- [ ] `hb-shape` must emit 1 glyph per grapheme with correct advance:
  ```bash
  hb-shape build/*.ttf "ক ক্ষ্ম র্ক" --show-positions | grep -E "advance=(600|1200)"
  # ক=600, ক্ষ=600, ক্ষ্ম=1200, র্ক=600
  ```
- [ ] `hb-view` screenshots at 12, 14, 16, 20px dark/light terminal
- [ ] `wcwidth` must be **variable**: `wcwidth("ক")=1, wcwidth("ক্ষ্ম")=2`
  ```python
  # tools/test_wcwidth.py — uses font's hmtx to derive expected wcwidth
  assert wcwidth.wcswidth("ক", font) == 1
  assert wcwidth.wcswidth("ক্ষ্ম", font) == 2
  ```
- [ ] Test matrix:
  | Terminal | Expected advance |
  |---|---|
  | Kitty (`modify_font_cell_width`), WezTerm (`harfbuzz_features`), foot | `ক` 1 cell, `ক্ষ্ম` 2 cells, cursor moves 1 or 2 |
  | Alacritty, VTE, xterm | falls back to `ss01` (hasanta visible, 1 cell/codepoint) |
- [ ] Grid test: `nvim` + `tmux` — draw `┌─┐` borders, verify `ক্ষ্ম` does not break alignment when 2 cells wide

## 4. Deliverables

```
build/
  SiyamRupaliMono-Regular.ttf        # hybrid: 600/1200
  SiyamRupaliMono-StrictMono.ttf     # optional pure 600 (1 cell only)
  SiyamRupaliMono-Regular.woff2
tools/
  fix_monospace.py
  classify_width.py   # 600 vs 1200 decision
  scale_ligatures.py
docs/
  TERMINAL.md   # user guide: which terminals, kitty.conf/wezterm.lua for 1/2 cell
```

## 5. Risks & Mitigations

*   **Illegibility when squeezed to 600** -> Solved by hybrid: promote only complex conjuncts to 1200; simple keeps 600 density. Much more readable than pure 600.
*   **Cursor desync in legacy terminals** -> `ss01` fallback + `docs/TERMINAL.md` lists supported terminals; no fix for `wcwidth` without terminal-side `LD_PRELOAD`.
*   **Upstream drift** -> Keep `sources/` as git submodule of `potasiyam/siyam-rupali`; rebase `Term` branch on releases.

## 6. Execution Order

1.  Phase 0-1 scaffolding + metrics lock
2.  Phase 2 auto-scale + manual top-30 ligatures
3.  Phase 3 anchors
4.  Phase 4-5 build & matrix test -> iterate Phase 2

## 7. Next Step

Review this plan; if approved, run Phase 0: copy `Siyam Rupali` source into `sources/` and execute `tools/scale_ligatures.py` on a test build.
