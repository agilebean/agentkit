#!/usr/bin/env python3
"""Count the terms of a private list in a tree or in a repository's history (DD-03, the history purge).

    python3 scripts/history_check.py --rules FILE --tree DIR
    python3 scripts/history_check.py --rules FILE --repo GITDIR

A rule is one line of the file: `literal==>replacement` or `regex:<python regex>==>replacement`.
A blank line and a line starting with `#` are skipped; a rule is named by its 1-based line number.

`--tree` searches every committed file of the folder: the paths `git ls-files` names, or every
text file of the folder when it is not inside a git repository. `--repo` searches every unique
blob reachable from any ref and every commit message.

The term is never printed: a rule with hits prints one line, `rule <line number>: <count> hits in
files` or `... in blobs`, and the last line is `history_check: <total> hits`. The exit code is 1
when the total is above 0 and 0 when it is 0, so a log of this check can be read by anyone.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__"}


class Rule:
    """One line of the rules file: a pattern to count, never the term it matches."""

    def __init__(self, lineno: int, pattern: str, regex: bool) -> None:
        self.lineno = lineno
        self.regex = regex
        self.pattern = re.compile(pattern if regex else re.escape(pattern))

    def count(self, text: str) -> int:
        return sum(1 for _ in self.pattern.finditer(text))


def parse_rules(path: Path) -> list[Rule]:
    """The rules of the file, comments and blank lines skipped, each with its line number."""
    rules: list[Rule] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        term, _, _replacement = line.partition("==>")
        if term.startswith("regex:"):
            rules.append(Rule(lineno, term[len("regex:"):], True))
        else:
            rules.append(Rule(lineno, term, False))
    return rules


def is_text(data: bytes) -> bool:
    """A NUL byte marks a binary file; a byte outside UTF-8 marks a file this check cannot read."""
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def git(cwd: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, check=True
    ).stdout


def tree_texts(tree: Path) -> list[tuple[str, str]]:
    """Every committed file of the folder as (path, text), or every text file outside git."""
    try:
        raw = git(tree, "ls-files", "-z").decode("utf-8")
        paths = [name for name in raw.split("\0") if name]
    except (OSError, subprocess.CalledProcessError):
        paths = []
        for root, dirs, files in os.walk(tree):
            dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
            paths.extend((Path(root) / name).relative_to(tree).as_posix() for name in sorted(files))
    texts: list[tuple[str, str]] = []
    for name in paths:
        try:
            data = (tree / name).read_bytes()
        except OSError:
            continue
        if is_text(data):
            texts.append((name, data.decode("utf-8")))
    return texts


def blob_texts(repo: Path) -> list[tuple[str, str]]:
    """Every unique blob reachable from any ref as (sha, text), binary blobs skipped."""
    listing = git(repo, "rev-list", "--all", "--objects").decode("utf-8", "replace")
    shas = sorted({line.split(" ", 1)[0] for line in listing.splitlines() if line.strip()})
    if not shas:
        return []
    out = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=("\n".join(shas) + "\n").encode(),
        capture_output=True,
        check=True,
    ).stdout
    texts: list[tuple[str, str]] = []
    pos = 0
    while pos < len(out):
        end = out.find(b"\n", pos)
        if end < 0:
            break
        header = out[pos:end].decode("utf-8", "replace").split()
        if len(header) != 3 or header[1] != "blob":
            pos = end + 1
            continue
        sha, _kind, size = header
        body = out[end + 1:end + 1 + int(size)]
        pos = end + 1 + int(size) + 1
        if is_text(body):
            texts.append((sha, body.decode("utf-8")))
    return texts


def commit_messages(repo: Path) -> list[tuple[str, str]]:
    """Every commit message of any ref as (sha, text)."""
    raw = git(repo, "log", "--all", "--format=%H%x00%B%x00").decode("utf-8", "replace")
    parts = raw.split("\0")
    return [(parts[i].strip(), parts[i + 1]) for i in range(0, len(parts) - 1, 2) if parts[i].strip()]


def count_in(rules: list[Rule], texts: list[tuple[str, str]]) -> dict[int, int]:
    """Hits per rule's line number across the texts."""
    counts = {rule.lineno: 0 for rule in rules}
    for _name, text in texts:
        for rule in rules:
            counts[rule.lineno] += rule.count(text)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Count a private list's terms, never printing them.")
    parser.add_argument("--rules", required=True, help="the rules file, one rule a line")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--tree", help="a folder: its committed files")
    where.add_argument("--repo", help="a git repository: every blob and every commit message")
    args = parser.parse_args(argv)

    rules_path = Path(args.rules)
    if not rules_path.is_file():
        print(f"history_check: no rules file at {rules_path}", file=sys.stderr)
        return 2
    rules = parse_rules(rules_path)
    if not rules:
        print("history_check: 0 hits")
        return 0

    if args.tree is not None:
        tree = Path(args.tree)
        if not tree.is_dir():
            print(f"history_check: {args.tree} is not a folder", file=sys.stderr)
            return 2
        noun, texts = "files", tree_texts(tree)
    else:
        repo = Path(args.repo)
        if not repo.is_dir():
            print(f"history_check: {args.repo} is not a folder", file=sys.stderr)
            return 2
        noun, texts = "blobs", blob_texts(repo) + commit_messages(repo)

    counts = count_in(rules, texts)
    total = 0
    for rule in rules:
        hits = counts[rule.lineno]
        total += hits
        if hits:
            print(f"rule {rule.lineno}: {hits} hits in {noun}")
    print(f"history_check: {total} hits")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
