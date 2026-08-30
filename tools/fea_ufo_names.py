#!/usr/bin/env python3
"""Quick advisory check: do all glyph-name tokens in features.fea exist in the UFO?

Not a gate — a triage tool. Tells us whether feaLib can compile the fea
against this UFO directly, or whether the name bridge is required first.
"""
import re
import sys

import ufoLib2

KEYWORDS = {
    "languagesystem", "script", "language", "feature", "lookup", "sub", "by",
    "from", "pos", "mark", "base", "ligature", "exclude", "include", "ignore",
    "substitute", "position", "useExtension", "reversi", "lookupflag",
    "RightToLeft", "IgnoreLigatures", "IgnoreMarks", "IgnoreBaseGlyphs",
    "RequiredFeature", "NULL", "anchor", "contour", "component", "curs",
    "prop", "DEF_GLYPH", "DEF_GROUP", "END", "IN_CLASS", "CMAP",
}
FEATURE_TAGS = {
    "blwf", "blws", "half", "haln", "init", "locl", "pres", "pstf", "psts",
    "rphf", "vatu", "akhn", "abvm", "blwm", "ccmp", "kern", "mkmk", "calt",
    "liga", "dlig", "ss01", "ss02", "ss03", "bn", "ben", "bng2", "dflt",
    "latn", "Deva", "DEVA", "2.0", "1.0",
}


def main(ufo_path, fea_path):
    ufo = ufoLib2.Font.open(ufo_path)
    ufo_names = set(ufo.keys())
    src = open(fea_path, encoding="utf-8").read()
    src = re.sub(r"#.*", "", src)
    src = re.sub(r"^\s*\w+\s*;", "", src)  # lookupflag value statements
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]{2,}", src))
    missing = sorted(
        t for t in tokens
        if t not in ufo_names and t not in KEYWORDS and t not in FEATURE_TAGS
    )
    print(f"{len(missing)} fea glyph tokens missing from {ufo_path}")
    for m in missing:
        print(" ", m)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
