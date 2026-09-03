# Siyam Rupali Mono — version history & what's installed

The full session-by-session record lives in `docs/WORKLOG.md`. This file
is the readable map: what each version was, why the next one happened,
and which fonts are on your machine right now.

Everything regenerates from one source of truth:
`legacy/base-1.070ship.ttf` + `tools/mono_convert.py` (build commands in
AGENTS.md; the two-font architecture in `docs/PLAN_DUO_MONO.md`).

---

## CURRENT — the two canonical fonts (2026-09-03, v0.1.0)

The merged terminal/editor architecture ("Siyam Rupali Mono" +
"Siyam Rupali Duo", `docs/PLAN_DUO_MONO.md`). Every specialist variant
(Wide, WT, Edit, Console, Two, Proof, 008, WT8–WT17) is RETIRED —
unregistered from the machine, regenerable from `build/` sources.

| Family | File | Version | Use it for |
|---|---|---|---|
| **Siyam Rupali Mono** | `SiyamRupaliMono-0100.ttf` | 0.1.0 | **Terminals** (Windows Terminal, WezTerm, kitty/VTE). WT-native line: verbatim matra art at full-cell advance, 2-cell reph/ya-phala ligatures, contextual anusvara/visarga/aa tucks. Grid-exact on all reference words (ka=1, ki=2, kiki=4, king=2, korto=3). |
| **Siyam Rupali Duo** | `SiyamRupaliDuo-0100.ttf` | 0.1.0 | **Editors** (VS Code etc.). Duospaced: Latin/danda 1 cell (1024), Bengali art+advance uniformly zoomed ×1.378 so the median letter = 2 cells with ALL native interlocks preserved. Unsqueezed conjuncts (~2.5 cells). |

Known platform residuals (terminal-side, no font can fix; see
SPACING_REPORT / PROOF): conjunct clusters leave charged-but-empty
columns in WT (+1) and WezTerm-Windows (+2, raw-codepoint charging);
ক্ charges 2 in WezTerm-Windows vs 1 drawn. Upstream fix direction:
terminals charging shaped cluster widths.

---

## History (summary; full record in WORKLOG.md)

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

### 0.0.3 — `Siyam Rupali Mono` (superseded by the canonical 0.1.0 pair)

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
| **Siyam Rupali Mono** | `%LOCALAPPDATA%\Microsoft\Windows\Fonts\SiyamRupaliMono-0100.ttf` | 0.1.0 | **USE THIS in terminals** |
| **Siyam Rupali Duo** | `…\SiyamRupaliDuo-0100.ttf` | 0.1.0 | **USE THIS in editors** |
| Siyam Rupali | Avro's folder (system) | 1.070 | Original — managed by Avro, leave it |

All `Siyam Rupali Mono <variant>` families (Edit/Wide/WT/WT8/WT10/
WT15/WT16/WT17/Two/Console/008) were unregistered on 2026-09-03.
If a long-running app still shows old glyphs, restart it (DWrite
caches per process); if the family itself resolves stale, restart
the FontCache service (admin) — the documented last resort.

## Which font to use where (TL;DR)

- **Windows Terminal / any terminal → `Siyam Rupali Mono`**
- **VS Code / editors → `Siyam Rupali Duo`**
- **Documents/Word → original `Siyam Rupali`** (or Duo — your call)
