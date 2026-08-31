# Siyam Rupali Mono — version history & what's installed

The full session-by-session record lives in `docs/WORKLOG.md`. This file
is the readable map: what each version was, why the next one happened,
and which fonts are on your machine right now.

Everything regenerates from one source of truth:
`legacy/base-1.070ship.ttf` + `tools/mono_convert.py` +
`tools/gen_cv_ligatures.py` (build commands in AGENTS.md).

---

## The original (not ours to manage here)

| Family | What | Where |
|---|---|---|
| **Siyam Rupali** | Your 2011 proportional font, final release 1.070. Full shaping, natural letter widths. | Installed by Avro Keyboard system-wide. Untouched by this project. |

Not a mono font — included in every comparison only as the reference.

---

## Term series — engineering builds (never released)

Strict-mono conversion experiments while finding the right cell size.

| Version | What it was | Why it died / evolved |
|---|---|---|
| 1.100 | First strict mono: every glyph = 1 cell of 1024 units; CV ligatures in fixed sub-regions | CV clusters squeezed to ~0.32× — unreadable (your verdict). Layout code kept for reproducibility. |
| (experiments) | Fullwidth 2048; 2-cell "WideCV" | Fullwidth: dead bearings around Latin. WideCV: no terminal grants per-codepoint widths. Both withdrawn. |
| 1.104 | Cell widened to 1536; ligatures re-laid out uniformly; `_std` matra variants added (mid-word ে/ৈ bug) | Superseded within a day. (Its install got file-locked — root of a later WT font-cache mystery.) |
| 1.105 | Two-surface split: **Wide** (terminals, ligatures) + **Edit** (editors, unsqueezed); kar glyphs never squeezed | Worked, but built on a wrong assumption about terminals (see 0.0.1). |

---

## Alpha series — author-test builds (2026-08-31)

### 0.0.1 — `Siyam Rupali Mono Wide` + `Siyam Rupali Mono Edit`

First builds meant for your hands. Wide = terminal (cell 1536, 396 CV
ligature rules, 1 cell per cluster), Edit = editors (matras keep their
own full cell). Both hinted, both fully gated.

**What testing revealed:** Windows Terminal could not even find Wide
(stale DirectWrite font cache from the file-locked 1.104 install — the
"screenshot was a fallback font" incident), and deeper probing proved
**WT does no Bengali shaping at all**: it charges columns per codepoint
and draws glyphs in typed order. So Wide's ligatures could never fire
in WT, and Edit's matras landed on the wrong side of the letter.

### 0.0.1 — `Siyam Rupali Mono WT`

Windows Terminal-native experiment: the six pre-base/above marks
(ি ে ৈ ো ৌ ং) carry their ink **pre-shifted one cell left**, so in WT's
typed order the curl lands over the base. No ligatures (useless in WT).
Correct in WT, wrong anywhere that shapes — a specialist, not the
answer.

### 0.0.2 — `Siyam Rupali Mono` (first universal — one bug)

One font that adapts to the renderer: the six pre-base/above marks
(ি ে ৈ ো ৌ ং) ship with **shifted art under their original names** (for
Windows Terminal's codepoint-order rendering), `_shaped` twins hold
centered art, a GSUB restore lookup swaps shifted → centered for
shaping renderers, and CV ligatures give shaping terminals exact
1-cell clusters.

**Bug found in author testing:** WT *does* apply GSUB `pres` lookups
(correcting an earlier wrong conclusion — it just never does the
Bengali reordering). The restore therefore misfired in WT, pulling the
centered ি into its own cell — detached from the ক.

### 0.0.3 — `Siyam Rupali Mono` (CURRENT)

Same universal architecture, **restore lookup removed** (now an
opt-in flag). Result:

| Where | What you see |
|---|---|
| Windows Terminal | 2 columns per কি-class cluster, split art, curl over the base — the reported bug fixed |
| WezTerm (Windows) | Merged ligature art + a phantom gap per cluster (ConPTY charges 2, art uses 1) |
| kitty / VTE / WezTerm-on-Linux | Merged ligature exactly 1 column — grid-perfect |
| Editors (VS Code, Word…) | Ligatures; non-ligated leftovers keep shifted art (rare, already-degraded cases) |

Known platform limit (no font can fix): WT renders conjuncts
letter-by-letter (ক্ষ = ক+ষ) until WT itself ships Bengali shaping
(upstream work in progress).

---

## What's installed on this machine right now

| Family (font picker name) | File | Version | Status |
|---|---|---|---|
| **Siyam Rupali Mono** | `%LOCALAPPDATA%\Microsoft\Windows\Fonts\SiyamRupaliMono-003.ttf` | 0.0.3 | **USE THIS** — universal, works everywhere |
| Siyam Rupali Mono Edit | `…\SiyamRupaliMono-Edit.ttf` | 0.0.1 | Optional — unsqueezed 2-cell view for editors |
| Siyam Rupali Mono Wide | `…\SiyamRupaliMono-Wide-Alpha.ttf` | 0.0.1 | Superseded by 0.0.3 — safe to uninstall |
| Siyam Rupali Mono WT | `…\SiyamRupaliMono-WT.ttf` | 0.0.1 | Superseded by 0.0.3 — safe to uninstall |
| Siyam Rupali | Avro's folder (system) | 1.070 | Original — managed by Avro, leave it |

To uninstall the superseded ones yourself: Windows Settings →
Personalization → Fonts → pick the family → Uninstall. Or just say the
word and the agent removes Wide/WT/Edit in one step (they regenerate
from `build/` any time).

## Which font to use where (TL;DR)

- **Windows Terminal → `Siyam Rupali Mono`**
- **WezTerm → `Siyam Rupali Mono`**
- **VS Code / editors → `Siyam Rupali Mono`** (or `…Edit` if you prefer
  the bigger unsqueezed matras while reading)
- **Documents/Word → original `Siyam Rupali`** (or the Mono — your call)
