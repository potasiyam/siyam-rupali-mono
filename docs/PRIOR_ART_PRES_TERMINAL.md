# Prior art: how other fonts handled `pres`/shaping on terminals

Research note, 2026-09-03. Question: has anyone else solved the
Bengali/Indic `pres` (pre-base conjunct + reordering) problem in
terminal emulators from the FONT side? Short answer: **no shipping
font has; the most serious attempt withdrew and endorsed
terminal-side grapheme clustering.** Five strategy classes exist.

## A. Terminal-side shaping + grapheme-cluster grid (modern consensus)

- **Monotty** (https://github.com/monotty/fonts ,
  fork https://github.com/TheMadHau5/devanagary-mono ) — monospace
  Devanagari/Bengali/Gujarati, stroke-generated, every glyph exactly
  1/2 em. README update (May 2024): *"Practice has shown that for
  correct display of the Devanagari script in the terminal, there is
  no need for special fonts — those proportional ones that exist are
  quite sufficient (e.g. Noto Sans Devanagari). The only thing that is
  needed is the support for tailored grapheme clustering on the
  terminal side… The fonts in our repository are not correct, do not
  use them."* Their Bengali build (`<bng2>`) was never released
  (N/A). They targeted terminals with "character slicing" via
  Variation Selectors (terminal-wg spec issue 23,
  https://gitlab.freedesktop.org/terminal-wg/specifications/-/issues/23 ).
- The ecosystem standardized on **DECSET/DECRST 2027** (grapheme
  clustering, "Terminal Unicode Core"):
  - kitty: grapheme segmentation in `char-props`; discussion
    https://github.com/kovidgoyal/kitty/issues/7799
  - foot: PR https://codeberg.org/dnkl/foot/pulls/1489 implements
    mode 2027 by exposing its existing "grapheme shaping" option
  - Ghostty: Mitchell Hashimoto, "Grapheme Clusters and Terminal
    Emulators" https://mitchellh.com/writing/grapheme-clusters-in-terminals
  - overview: https://vtdn.dev/docs/decset/mode2027-grapheme/
- Under mode 2027 the font ships NORMAL GSUB `pres` and the terminal
  charges 1 column per shaped cluster → merged ligature = 1 column,
  grid aligned. This is the world where "fonts solved it" by doing
  nothing special.
- Caveat (our own measurements, docs/PROOF_2026-09-03.md): Windows
  Terminal shapes fully but charges per codepoint with mark-run
  collapse; Windows ConPTY ports (WezTerm/Alacritty) charge raw
  codepoints. Mode 2027 does not exist on Windows.

## B. Precomposed 1-cell `pres` ligatures in the font (our approach)

`tools/gen_cv_ligatures.py` appends a `pres` LigatureSubst with
1-cell merged CV forms to the VOLT font (0.0.4+; 0.0.8 = 396
ligatures, cell 1404). Same glyph-design idea as Monotty's
single-glyph cluster forms, bolted onto an existing font. State of
the art font-side for Bengali — ahead of anything shipped (Monotty's
bng2 = N/A; MitraMono is ISCII-era). Known limits: coverage explosion
(conjunct+matra ≈ 2600 glyphs, open work #2) and charged-but-empty
columns in WT (intrinsic, 4th-revision model).

## C. Legacy precomposed encodings (no GSUB reliance)

- **MitraMono** (packaging: https://github.com/mitradranirban/fbf-mitra-fonts )
  — *"a Bangla experimental monospace font with additional ISCII
  encodings required for some specialised applications like xterm,
  IE6."* Dual encoding: conjunct art placed AT codepoints so
  cmap-only renderers work. Same family as the ANSI/Bijoy fonts
  (SutonnyMJ etc.). Historically how xterm displayed Bangla
  conjuncts; not viable for modern Unicode terminals (wrong
  codepoints).

## D. Scripts where the problem structurally does not exist

- **Thai/Lao monospace** (TLWG Waree/Garuda Mono etc.): every vowel
  and tone mark is Mn (zero-width) — no reordering, no spacing marks;
  wcwidth already charges 0 columns. No `pres` needed.
- **Arabic monospace** (Kawkab Mono,
  https://github.com/aiaf/kawkab-mono ): shaping is mandatory
  (contextual forms) but there is no reordering and no multi-codepoint
  spacing marks — one codepoint shapes to one glyph; marks
  zero-width. Works in any HarfBuzz terminal.
- Bengali/Devanagari are hard precisely because of the three things
  those scripts lack: **pre-base reordering (ি ে), SpacingMark
  (Mc) matras (া ি ে), and virama conjunct formation.**

## E. Escape hatches (experimental, not adopted)

- Monotty's Variation-Selector size modifiers / character slicing
  (terminal-wg issue 23).
- This project's NBSP-escape 2-cell system (open work #6, designed,
  deferred) belongs to the same class — a font-side workaround for
  strict per-codepoint grids, consistent with the ecosystem
  conclusion that font-side hacks hit walls.

## Bottom line for Siyam Rupali Mono

No font has solved `pres` on terminals. The reference attempt
(Monotty) withdrew in favor of terminal-side clustering (mode 2027).
Our 0.0.8 universal — correct VOLT `pres` + appended 1-cell CV
ligatures — matches the state of the art for shaping terminals, and
the WT charged-but-empty residual is confirmed intrinsic from both
our measurements and the ecosystem's own direction (charge per
cluster = mode 2027; WT does not implement it).
