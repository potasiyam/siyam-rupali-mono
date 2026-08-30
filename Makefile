# SiyamRupaliMono — thin build wrapper. Pipeline scripts live in the brain.
# The brain defaults to ../agentic-font-dev; override with: make BRAIN=/path
BRAIN ?= ../agentic-font-dev

# This project has no local venv by design: it reuses the brain's verified
# environment (Python 3.10.6, pinned fontTools 4.63.0 stack). If the brain
# venv is missing, run `make bootstrap` there first.
ifeq ($(OS),Windows_NT)
PY := $(BRAIN)/.venv/Scripts/python.exe
else
PY := $(BRAIN)/.venv/bin/python
endif

UFO    := sources/font.ufo
FEA    := sources/features.fea
VTP    := sources/layout.vtp
VFB    := sources/font.vfb
GOADB  := sources/glyphorder
REF_TTF := legacy/ref.ttf
LEGACY_TTF := legacy/ref.ttf
TESTS  := tests/conjuncts.txt
TTF    := build/SiyamRupaliMono.ttf
SCRIPT := beng
LANG_SYS := ben

# Name-bridge: reconcile VOLT mnemonic names (features.fea, bn_*) with
# vfb3ufo's unicode-sequence UFO names (u09XX...). ALWAYS ON for this font —
# the drift is structural (same class as Kalpurush, AGENTS.md incident #5).
BRIDGE_DIR := build/bridged
BRIDGE_JSON := $(BRIDGE_DIR)/name_bridge.json
BRIDGE_FEA  := $(BRIDGE_DIR)/features.bridged.fea
BRIDGE_UFO  := $(BRIDGE_DIR)/font.aliased.ufo
USE_BRIDGE  := 1

.PHONY: all bootstrap doctor convert ufo glyphorder matrix resolve-names normalize-names name-audit \
        check-glyphorder bridge bridge-names rewrite-fea apply-postscript-names \
        overlay verify-hints build hint inspect qa bakery \
        set-meta export-meta import-meta bump-version backport-vfb clean help

BUILD_MODE ?= new
ifeq ($(BUILD_MODE),old)
all: overlay inspect qa
else
all: check-glyphorder build hint inspect qa
endif

bootstrap doctor:
	@test -x "$(PY)" || (echo "brain venv missing at $(PY) — run make bootstrap in $(BRAIN)" && exit 1)
	@$(PY) -c "import fontTools, ufoLib2, fontmake, uharfbuzz, vharfbuzz, vfbLib; print('env OK (brain venv, fontTools', fontTools.version + ')')"

convert:
	$(PY) $(BRAIN)/scripts/convert_volt.py $(VTP) $(FEA)

ufo:
	$(PY) $(BRAIN)/scripts/convert_vfb.py $(VFB) $(UFO)

glyphorder:
	$(PY) $(BRAIN)/scripts/build_glyphorder.py $(VTP) $(GOADB)

check-glyphorder:
	$(PY) $(BRAIN)/scripts/check_glyphorder.py $(GOADB) $(FEA) $(UFO)

matrix:
	$(PY) $(BRAIN)/scripts/naming_matrix.py $(VTP) $(VTP_TTF) $(SHIP_TTF) $(GOADB) build/naming_review.html
	@echo "Open build/naming_review.html in a browser to review names."

resolve-names:
	$(PY) $(BRAIN)/scripts/resolve_names.py $(VTP) $(REF_TTF) build/name_resolution.html
	@echo "Open build/name_resolution.html in a browser to review."

normalize-names:
	$(PY) $(BRAIN)/scripts/normalize_names.py $(VTP) $(GOADB) build/normalize_names.html $(REF_TTF)
	@echo "Open build/normalize_names.html in a browser to review."

name-audit:
	$(PY) $(BRAIN)/scripts/name_audit.py \
	  --vfb $(VFB) --ufo $(UFO) --vtp $(VTP) \
	  --ttf $(LEGACY_TTF) --glyphorder $(GOADB) \
	  --out build/name_audit.html
	@echo "Open build/name_audit.html in a browser to review."

bridge: bridge-names rewrite-fea apply-postscript-names
	@echo "OK: bridge complete -> $(BRIDGE_DIR)/"

bridge-names:
	@mkdir -p $(BRIDGE_DIR)
	$(PY) $(BRAIN)/scripts/bridge_names.py $(VTP) $(UFO) $(REF_TTF) $(BRIDGE_JSON)

rewrite-fea:
	$(PY) $(BRAIN)/scripts/rewrite_fea.py $(FEA) $(BRIDGE_JSON) $(BRIDGE_FEA)

apply-postscript-names:
	$(PY) $(BRAIN)/scripts/apply_postscript_names.py $(UFO) $(BRIDGE_JSON) $(BRIDGE_UFO)

ifdef USE_BRIDGE
build: bridge
	$(PY) $(BRAIN)/scripts/build.py $(UFO) $(FEA) build/ SiyamRupaliMono $(BRIDGE_DIR)
else
build:
	$(PY) $(BRAIN)/scripts/build.py $(UFO) $(FEA) build/ SiyamRupaliMono
endif

overlay:
	$(PY) $(BRAIN)/scripts/layout_overlay.py $(LEGACY_TTF) $(VTP) $(UFO) build/SiyamRupaliMono.overlay.ttf

verify-hints:
	$(PY) $(BRAIN)/scripts/verify_hints.py $(LEGACY_TTF) build/SiyamRupaliMono.overlay.ttf

export-meta:
	@test -n "$(META)" || (echo "usage: make export-meta META=meta.json" && exit 1)
	$(PY) $(BRAIN)/scripts/set_meta.py $(TTF) --export $(META)

import-meta:
	@test -n "$(META)" || (echo "usage: make import-meta META=meta.json" && exit 1)
	$(PY) $(BRAIN)/scripts/set_meta.py $(TTF) --import $(META)

set-meta:
	@test -n "$(ARGS)" || (echo 'usage: make set-meta ARGS=...' && exit 1)
	$(PY) $(BRAIN)/scripts/set_meta.py $(TTF) $(ARGS)

bump-version:
	@test -n "$(VER)" || (echo "usage: make bump-version VER=1.100" && exit 1)
	$(PY) $(BRAIN)/scripts/set_meta.py $(TTF) --bump-version $(VER)

backport-vfb:
	@test -n "$(OUT)" || (echo "usage: make backport-vfb OUT=x" && exit 1)
	$(PY) $(BRAIN)/scripts/backport_vfb_names.py $(VFB) $(VTP) $(OUT)

hint:
	$(PY) $(BRAIN)/scripts/hint.py $(TTF)

inspect:
	$(PY) $(BRAIN)/scripts/inspect_font.py $(TTF)

qa:
	$(PY) $(BRAIN)/scripts/qa.py $(TTF) $(TESTS) --script $(SCRIPT) --language $(LANG_SYS)

bakery:
	$(PY) -m fontbakery check-universal $(TTF)

clean:
	rm -rf build/*.ttf build/*.otf build/bridged build/overlay

help:
	@echo "SiyamRupaliMono targets (scripts in $(BRAIN)):"
	@echo "  make bootstrap/doctor   verify brain venv"
	@echo "  make ufo                font.vfb -> sources/font.ufo (headless)"
	@echo "  make glyphorder         build sources/glyphorder from the .vtp"
	@echo "  make check-glyphorder   HARD gate: fea + UFO names vs glyphorder"
	@echo "  make bridge             reconcile fea/UFO naming drift (always-on here)"
	@echo "  make build              UFO + fea -> build/SiyamRupaliMono.ttf"
	@echo "  make hint               ttfautohint the built TTF"
	@echo "  make qa                 shape Bangla, diff vs tests/conjuncts.txt"
	@echo "  make all                full release path"
	@echo "  make inspect            table-level smoke check"
	@echo "  mono-specific tools live in tools/ (see PLAN.md)"
