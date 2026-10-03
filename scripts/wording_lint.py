#!/usr/bin/env python3
"""Check text for the robot markers of RULES.md rule 2.

Usage:
  python3 scripts/wording_lint.py [--markers PATH] FILE [FILE ...]

Reads the shared marker list (`robot_markers.tsv`, at this repo's root) and
reports each hit as `<file>:<line>: <level> '<matched words>' - <fix>`. A
`flag` hit fails the run with exit 2; a `warn` hit is reported only. The list
is the checkable subset by design: three-item runs, embedded clauses, headings
over one sentence and colon-field blocks stay a writer's pass.

Every project runs this same list. A project pipeline may wrap the checker for
its own files (socrates: `projects/kubs_dt/pipeline.py lint --session N`).
"""
from __future__ import annotations

import argparse
import os
import re
import sys

DEFAULT_MARKERS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "robot_markers.tsv")


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
    name is not prose.
    """
    hits = []
    seen = set()
    for lineno, line in enumerate(text.splitlines(), 1):
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
    print(f"wording_lint: {len(args.files)} file(s), {flags} flag(s), {warns} warn(s)")
    return 2 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
