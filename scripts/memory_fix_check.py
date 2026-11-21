#!/usr/bin/env python3
"""Refuse a proposed memory fix that changes a fact (DD-11, rules C1 to C5).

    python3 memory_fix_check.py PROPOSALS --root ~/Software/Prototypes/socrates
    exit 0 when every fix keeps the line's facts, exit 1 with one line per refusal

A proposals file holds one section per memory file, `## memory/<file>`, and one table:

    | Line | Check | Line now | Proposed line |

`Line now` is the file's line exactly, every `|` written `\\|`. `Proposed line` is the line as
it would stand after the fix, or `keep: <reason>`. This checker reads each section's memory file
under ROOT/memory, runs `memory_lint.lint` on it, and refuses:

C1  a flagged line of a memory file with no section or no row, and a row for a line the lint does
    not flag. This pass covers M1 (a relative time outside a quote) and M3 (an inference stated
    as fact) only: a line flagged M2 or M5 belongs to the other session of DD-11, so it is
    neither a missing row nor an extra one.
C2  a `Line now` that differs from the file's line.
C3  a proposed line on which `memory_lint.lint` still finds a check of any kind.
C4  a proposed line that drops a number, a date, a quoted text or a backtick span of the line now.
C5  a `keep` with no reason; an M1 `keep` whose reason is not `no date in the record`; an M1
    `keep: no date in the record` on a line that carries a date of its own; an M3 `keep` with an
    empty reason.

A `keep` names no change, so C3 and C4 do not apply to it.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_lint  # noqa: E402

SCOPE = ("M1", "M3")
CELL = re.compile(r"(?<!\\)\|")
DATE = re.compile(r"\d{4}-\d{2}(?:-\d{2})?(?!\d)")
NUMBER = re.compile(r"\d+(?:\.\d+)?")
BACKTICK = re.compile(r"`[^`]*`")
KEEP = re.compile(r"^keep:\s*(.*)$", re.S)


def cells(line: str) -> list[str]:
    """The row's cells, outer pipes dropped, every `\\|` read back as the pipe it writes.

    A line now keeps the indentation the file gives it: the one space that pads a table cell is
    removed here and no more, so a list item's own leading spaces survive the comparison.
    """
    parts = CELL.split(line.strip())
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    out = []
    for i, p in enumerate(parts):
        if i < 2:
            out.append(p.strip().replace("\\|", "|"))
        else:
            if p.startswith(" "):
                p = p[1:]
            if p.endswith(" ") and not p.endswith("\\ "):
                p = p[:-1]
            out.append(p.replace("\\|", "|"))
    return out


def is_separator(parts: list[str]) -> bool:
    return bool(parts) and all(set(p) <= set("-: ") and p for p in parts)


def sections(text: str) -> list[tuple[str, int, list[tuple[int, str, str]]]]:
    """(memory path, heading line, rows): each row as (line number, checks, cells)."""
    out: list[tuple[str, int, list[tuple[int, str, str]]]] = []
    current = None
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            name = line[3:].strip().strip("`")
            current = (name, n, []) if name.startswith("memory/") else None
            if current:
                out.append(current)
            continue
        if current is None or not line.lstrip().startswith("|"):
            continue
        parts = cells(line)
        if not parts or parts[0].lower() == "line" or is_separator(parts):
            continue
        current[2].append((n, line, parts))
    return out


def split_row(parts: list[str]) -> tuple[int | None, list[str], str, str]:
    """(line number, checks, line now, proposed line) of a table row."""
    try:
        number = int(parts[0])
    except (IndexError, ValueError):
        number = None
    checks = [c.strip() for c in (parts[1] if len(parts) > 1 else "").split(",") if c.strip()]
    now = parts[2] if len(parts) > 2 else ""
    proposed = " | ".join(parts[3:]) if len(parts) > 3 else ""
    return number, checks, now, proposed


def dropped(now: str, proposed: str) -> list[str]:
    """The facts of the line now that the proposed line no longer holds."""
    gone = []
    for token in DATE.findall(now):
        if token not in proposed:
            gone.append(f"date {token}")
    for token in NUMBER.findall(now):
        if not re.search(r"(?<![\d.])" + re.escape(token) + r"(?![\d.])", proposed):
            gone.append(f"number {token}")
    for token in memory_lint.QUOTE.findall(now):
        if token not in proposed:
            gone.append(f"quoted text {token}")
    for token in BACKTICK.findall(now):
        if token not in proposed:
            gone.append(f"backtick span {token}")
    return gone


def check(proposals: Path, root: Path) -> int:
    problems: list[str] = []
    text = proposals.read_text(encoding="utf-8")

    linted: dict[str, list[tuple[int, str, str]]] = {}
    if not (root / "memory").is_dir():
        print(f"memory_fix_check: FAIL no memory folder at {root / 'memory'}")
        return 1
    for path in sorted((root / "memory").glob("*.md")):
        linted[f"memory/{path.name}"] = memory_lint.lint(path.read_text(encoding="utf-8"))
    flagged = {
        name: sorted((n, code) for n, code, _ in hits if code in SCOPE)
        for name, hits in linted.items()
    }

    rows = 0
    seen: set[tuple[str, int]] = set()
    for name, heading, table in sections(text):
        if name not in linted:
            problems.append(f"C1 {name} (section at proposals line {heading}) names a file that does not exist")
            continue
        expected = {n: set(code for ln, code in flagged[name] if ln == n) for n, _ in flagged[name]}
        found: dict[int, set[str]] = {}
        source = (root / name).read_text(encoding="utf-8").splitlines()
        for rn, raw, parts in table:
            number, checks, now, proposed = split_row(parts)
            mine = [c for c in checks if c in SCOPE]
            if not mine:
                continue
            rows += 1
            where = f"{name}:{number}"
            if number is None:
                problems.append(f"C1 {name} row at proposals line {rn} carries no line number")
                continue
            for code in mine:
                found.setdefault(number, set()).add(code)
                if (number, code) not in [(n, c) for n, c in flagged[name]]:
                    problems.append(f"C1 {where} M1/M3 row for a line the lint does not flag {code}")
            if number < 1 or number > len(source):
                problems.append(f"C2 {where} is past the file's {len(source)} lines")
                continue
            if now != source[number - 1]:
                problems.append(f"C2 {where} Line now differs from the file's line")
            keep = KEEP.match(proposed)
            if keep:
                reason = keep.group(1).strip()
                if not reason:
                    problems.append(f"C5 {where} keep without its reason")
                elif "M1" in mine:
                    if reason != "no date in the record":
                        problems.append(f"C5 {where} an M1 keep reads: no date in the record")
                    elif DATE.search(source[number - 1]):
                        problems.append(f"C5 {where} keep: no date in the record, but the line carries a date")
                continue
            hits = memory_lint.lint(proposed)
            if hits:
                codes = " ".join(sorted({c for _, c, _ in hits}))
                problems.append(f"C3 {where} the proposed line is still flagged: {codes}")
            gone = dropped(source[number - 1], proposed)
            if gone:
                problems.append(f"C4 {where} the proposed line drops {', '.join(gone)}")
        for n in sorted(expected):
            for code in sorted(expected[n] - found.get(n, set())):
                problems.append(f"C1 {name}:{n} no row for the {code} flag")

    for name, hits in sorted(flagged.items()):
        if hits and not any(name == s[0] for s in sections(text)):
            lines = ", ".join(str(n) for n, _ in hits)
            problems.append(f"C1 {name} no section, and the lint flags line(s) {lines}")

    if problems:
        for p in problems:
            print(p)
        print(f"memory_fix_check: FAIL {len(problems)} problem(s)")
        return 1

    counts = {code: 0 for code in SCOPE}
    for name, hits in flagged.items():
        for _, code in hits:
            counts[code] += 1
    total = sum(counts.values())
    detail = " ".join(f"{c} {counts[c]}" for c in SCOPE)
    print(f"memory_fix_check: PASS {len(sections(text))} section(s), {rows} row(s) over {total} flag(s): {detail}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("proposals", type=Path)
    parser.add_argument("--root", type=Path, required=True, help="the folder that holds memory/")
    args = parser.parse_args(argv)
    if not args.proposals.is_file():
        print(f"memory_fix_check: FAIL no proposals file at {args.proposals}")
        return 1
    return check(args.proposals, args.root)


if __name__ == "__main__":
    sys.exit(main())
