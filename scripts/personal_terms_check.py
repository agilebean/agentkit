#!/usr/bin/env python3
"""Find Chaehan's personal terms in a tree without printing them (DD-03, step 3).

    python3 personal_terms_check.py --terms-file PATH --tree PATH
    python3 personal_terms_check.py --from-env VAR --tree PATH
    exit 0 when the tree holds no term, exit 1 with one line per hit

The list of terms stays in socrates. A file holds one term a line; a blank line and a line
starting with `#` are skipped, and a term is numbered by its 1-based position among the terms,
not among the file's lines. The default list is
`~/Software/Prototypes/socrates/docs/agentkit personal terms.txt`, so `--tree .` alone runs it
against agentkit. `--from-env` reads the same text from an environment variable, for a caller
that holds it that way.

A hit is printed as `path:line: term N`, the path relative to the tree. The term itself is never
printed, so a log of this check can be read by anyone. `.git`, `__pycache__` and a file that is
not UTF-8 text are skipped: text means no NUL byte and a clean decode.

With no list, or an empty one, the check has nothing to search for: it prints
`personal_terms_check: no terms list, check skipped` and exits 0, so a checkout without the
socrates list stays green.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__"}
SKIPPED = "personal_terms_check: no terms list, check skipped"


def parse_terms(text: str) -> list[str]:
    """The terms of a list, in order: a blank line and a `#` line skipped."""
    terms: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        terms.append(line)
    return terms


def read_list(terms_file: str | None, from_env: str | None) -> list[str]:
    """The terms from the file or the environment variable, `[]` when there are none to read."""
    if from_env is not None:
        return parse_terms(os.environ.get(from_env, ""))
    path = Path(terms_file or "")
    if not path.is_file():
        return []
    return parse_terms(path.read_text(encoding="utf-8", errors="replace"))


def is_text(data: bytes) -> bool:
    """A NUL byte marks a binary file; a byte outside UTF-8 marks a file this check cannot read."""
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def text_files(tree: Path):
    """Every text file under the tree, `.git` and `__pycache__` skipped, in a stable order."""
    for root, dirs, files in os.walk(tree):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
        for name in sorted(files):
            path = Path(root) / name
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if not is_text(data):
                continue
            yield path, data.decode("utf-8")


def scan(tree: Path, terms: list[str], skip: Path | None = None) -> list[str]:
    """One `path:line: term N` line per hit, by path, then line, then term.

    The list a check is given is never itself searched when it stands inside the tree.
    """
    hits: list[tuple[str, int, int]] = []
    leave_out = skip.resolve() if skip is not None else None
    for path, text in text_files(tree):
        if leave_out is not None and path.resolve() == leave_out:
            continue
        try:
            shown = path.relative_to(tree).as_posix()
        except ValueError:
            shown = path.as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            for position, term in enumerate(terms, start=1):
                if term in line:
                    hits.append((shown, lineno, position))
    hits.sort()
    return [f"{shown}:{lineno}: term {position}" for shown, lineno, position in hits]


SOCRATES_TERMS = Path.home() / "Software/Prototypes/socrates/docs/agentkit personal terms.txt"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find personal terms in a tree, never printing them.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--terms-file",
        default=str(SOCRATES_TERMS),
        help="a file holding one term a line, the socrates list by default",
    )
    source.add_argument("--from-env", metavar="VAR", help="an environment variable holding the same text")
    parser.add_argument("--tree", default=".", help="the folder to search, the current one by default")
    args = parser.parse_args(argv)

    terms = read_list(args.terms_file, args.from_env)
    if not terms:
        print(SKIPPED)
        return 0

    tree = Path(args.tree)
    if not tree.is_dir():
        print(f"personal_terms_check: {args.tree} is not a folder", file=sys.stderr)
        return 2

    hits = scan(tree, terms, Path(args.terms_file) if args.terms_file else None)
    for hit in hits:
        print(hit)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
