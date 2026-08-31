# Hand-designing glyph fixes — workflow guide

You (the author) review the alpha builds, redraw the characters you don't
like in FontLab, and the pipeline absorbs your drawings permanently via a
**fixes layer**. This document is the whole loop.

## 1. Install the alphas and test

Two fonts, two jobs (both `Version 0.0.1`):

| File | Family name | Test in |
|---|---|---|
| `build/SiyamRupaliMono-Wide.ttf` | Siyam Rupali Mono Wide | **Terminal** (Windows Terminal, kitty, WezTerm, foot…) |
| `build/SiyamRupaliMono-Edit.ttf` | Siyam Rupali Mono Edit | **Gridless editors** (VS Code, Notepad++, Word…) |

Install: right-click the TTF → *Install for me* (or copy into
`%LOCALAPPDATA%\Microsoft\Windows\Fonts`). Pick the family from the
terminal/editor font list.

What to look for while testing:

- **Terminal (Wide):** column alignment with mixed Bangla/ASCII text
  (e.g. paste a table), conjunct legibility (ক্ষ্ম, স্ত্র, ন্দ্র), CV
  clusters (কি কী কে কো), reph (র্ক), below-matras (কু কূ কৃ).
- **Editor (Edit):** general reading comfort — matras keep their own full
  cell here, so CV syllables are 2 cells (কি) / 3 cells (কো) wide. This
  surface exists to judge the letterforms unsqueezed.
- **Same characters in both** is the fastest way to tell "bad drawing"
  from "squeeze damage": if a glyph looks fine in Edit but wrong in Wide,
  the conversion squeezed it too hard; if wrong in both, the source art
  needs redrawing.

## 2. Find the glyph name

Everything in these fonts is named `bn_*` (inherited from your VOLT
project). To see which glyphs a string produces:

```
PY tools/shape_check.py build/SiyamRupaliMono-Wide.ttf --cell 1536
```

Every cluster line prints its glyphs, e.g. `'কি' ... bn_ka_ikaar`.
Naming scheme: `bn_<base>_<matra>` for generated CV ligatures, `_std`
suffix = the mid-word (non-initial) ে/ৈ art variant, everything else is
your original naming.

## 3. Draw the fix (FontLab)

1. Copy the build you're fixing:
   `build/SiyamRupaliMono-Wide.ttf` → `handfix/Wide-work.ttf`
   (Edit → `handfix/Edit-work.ttf`; keep the two surfaces in separate
   files — their cells/scales differ, so fixes are **per-surface**).
2. Open it in FontLab. Edit ONLY the outlines of the glyphs you dislike.
   Rules of the road:
   - **Don't rename, add, or delete glyphs** (the fixes layer matches by
     name; anything new is dropped with a warning).
   - **Don't worry about hinting** — the pipeline re-autohints everything
     at the end; your edits dropping old hints is expected.
   - **Advance widths are re-pinned automatically** to the cell (1536)
     when applied. Design inside the cell; the lsb you draw is kept.
3. Save as TrueType (`File → Save As…`, format TTF) over the same
   `handfix/Wide-work.ttf`. You can also keep testing this file directly
   (install it after removing the alpha, since both claim the same
   family name).

## 4. Absorb the fix into the pipeline

```
PY tools/extract_fixes.py handfix/Wide-work.ttf build/SiyamRupaliMono-Wide.ttf fixes/wide-0001.ttf
```

This diffs geometry (not hints) against the current build and writes only
your changed glyphs into `fixes/wide-0001.ttf`. Then rebuild with the fix:

```
# regenerate the build exactly as AGENTS.md describes, then:
PY tools/apply_fixes.py build/SiyamRupaliMono-Wide.ttf fixes/wide-0001.ttf
PY <brain>/scripts/hint.py   build/SiyamRupaliMono-Wide.ttf
# gates (AGENTS.md): qa.py + shape_check --cell 1536 --matrix --context
```

Commit the fragment (`fixes/*.ttf`) — that's the permanent record of your
hand work, replayed on top of every future rebuild. Apply multiple
fragments in order; later fragments win on overlap.

## 5. The lazy alternative

You can also just tell the agent: *"bn_ka_ikaar is too thin, bn_k_ssa
loop closes up"* — with the glyph names from §2. Programmatic fixes
(re-scales, stroke adjustments, spacing tweaks) go into the generator
tools and benefit every build; only true redraws need FontLab.
