#!/usr/bin/env python3
"""Check text for the robot markers of RULES.md rule 2, and for a reply written
in the wrong script.

Usage:
  python3 scripts/wording_lint.py [--markers PATH] FILE [FILE ...]

Reads the shared marker list (`robot_markers.tsv`, at this repo's root) and
reports each hit as `<file>:<line>: <level> '<matched words>' - <fix>`. A
`flag` hit fails the run with exit 2; a `warn` hit is reported only. The list
is the checkable subset by design: three-item runs, embedded clauses, headings
over one sentence and colon-field blocks stay a writer's pass.

The language check is mechanical because the drift is not: a Han character in
the writer's own text is a `flag` (RULES.md rule 217). Chaehan reads English,
German and Korean; Chinese in a reply is unreadable to him, and twice in one
session it went out unchecked. Hangul is left alone - a Korean reply is a
legitimate thread language. Inline code and a declared excerpt are skipped, so
a quoted filename or a source's own characters do not trip it.

Every project runs this same list. A project pipeline may wrap the checker for
its own files (socrates: `projects/kubs_dt/pipeline.py lint --session N`).

A quoted excerpt is the source's own text, kept verbatim, and the checker
leaves it alone: its lines sit between `<!-- verbatim -->` and
`<!-- end verbatim -->`. Another author's punctuation, word choices and
sentence shapes are not the writer's to repair, and flagging them trains the
reader to ignore the list. The two marker lines are comments, so a renderer
that shows raw HTML as text would print them; the path that renders an
artifact drops them first (socrates: `script_html` in
`projects/kubs_dt/pipeline.py`, held by its printout test).
"""
from __future__ import annotations

import argparse
import os
import re
import sys

DEFAULT_MARKERS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "robot_markers.tsv")

# A declared quoted excerpt: the lines between these two markers are another
# author's text, and the checker does not read them.
EXCERPT_OPEN = re.compile(r"^\s*<!--\s*verbatim\s*-->\s*$")
EXCERPT_CLOSE = re.compile(r"^\s*<!--\s*end verbatim\s*-->\s*$")

# Han characters: the script of a reply that is not being written in English,
# German or Korean. Kana and Hangul are outside these ranges.
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def script_hits(text: str) -> list[tuple[int, str, str]]:
    """Han characters in the writer's own words: (line, the character, the line).

    Inline code is stripped and a declared excerpt is skipped, so a quoted
    filename or another author's characters stay out of the check.
    """
    hits = []
    in_excerpt = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if EXCERPT_OPEN.match(line):
            in_excerpt = True
            continue
        if EXCERPT_CLOSE.match(line):
            in_excerpt = False
            continue
        if in_excerpt:
            continue
        clean = re.sub(r"`[^`]*`", "", line)
        m = HAN.search(clean)
        if m:
            hits.append((lineno, m.group(0), clean.strip()[:90]))
    return hits


def load_robot_markers(path: str = DEFAULT_MARKERS) -> list[tuple[str, re.Pattern, str, re.Pattern | None]]:
    rules = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cells = line.split("\t")
            if len(cells) < 3 or cells[0] not in ("flag", "warn"):
                sys.exit(f"{path}:{lineno}: a rule reads 'flag|warn <TAB> pattern <TAB> fix [<TAB> exception]'")
            rules.append((cells[0], re.compile(cells[1], re.I), cells[2],
                          re.compile(cells[3], re.I) if len(cells) > 3 and cells[3] else None))
    return rules


def lint_text(text: str, rules) -> list[tuple[int, str, str, str]]:
    """The robot markers in a text: (line, level, the matched words, the fix).

    One hit per line and span: a phrase caught by two rules is reported once.
    Inline code (`pipeline.py`) is stripped before matching: a command's own
    name is not prose. A declared quoted excerpt is skipped whole - the
    checker reads the writer's words, not the source's.
    """
    hits = []
    seen = set()
    in_excerpt = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if EXCERPT_OPEN.match(line):
            in_excerpt = True
            continue
        if EXCERPT_CLOSE.match(line):
            in_excerpt = False
            continue
        if in_excerpt:
            continue
        clean = re.sub(r"`[^`]*`", "", line)
        for level, pattern, fix, except_ in rules:
            m = pattern.search(clean)
            if not m or (except_ and except_.search(clean)):
                continue
            key = (lineno, m.start(), m.end())
            if key in seen:
                continue
            seen.add(key)
            hits.append((lineno, level, m.group(0), fix))
    return hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markers", default=DEFAULT_MARKERS, help="override: the robot marker list to read")
    ap.add_argument("files", nargs="+", help="files to check")
    args = ap.parse_args(argv)
    if not os.path.exists(args.markers):
        sys.exit(f"wording_lint: no marker list at {args.markers}")
    rules = load_robot_markers(args.markers)
    flags = warns = 0
    for path in args.files:
        if not os.path.exists(path):
            print(f"  missing: {path}")
            continue
        body = open(path, encoding="utf-8").read()
        for lineno, level, match, fix in lint_text(body, rules):
            print(f"  {path}:{lineno}: {level} '{match}' - {fix}")
            if level == "flag":
                flags += 1
            else:
                warns += 1
        for lineno, char, line in script_hits(body):
            print(f"  {path}:{lineno}: flag '{char}' - Han characters in your own text: "
                  f"write it in the thread's language (RULES.md 217) | {line}")
            flags += 1
    print(f"wording_lint: {len(args.files)} file(s), {flags} flag(s), {warns} warn(s)")
    return 2 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
