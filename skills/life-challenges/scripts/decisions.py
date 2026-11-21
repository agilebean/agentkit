#!/usr/bin/env python3
"""Chaehan's confirmed live decisions as data (human quality plan, HQ-02; his decision D2 of 2026-11-21).

After the life-challenges skill presents the challenges and before it creates the note, it asks Chaehan with
the question tool, one checkbox per decision, which decisions are valid, and writes only the checked ones to
`socrates/life/YYYY-MM-DD-decisions.tsv`. A line that starts with # is a comment; the rows have the columns of
the decision test's gold lists (scripts/decision_eval.py), so a note can be scored against the file:

    id  decision  deadline  options  depends  source

deadline is YYYY-MM-DD or none, options are separated by " / " (or none), and source names the record line
the decision comes from, as path:line. Nothing inferred becomes a row: each row was checked by Chaehan.

    python3 decisions.py check <file>                 # the form; exit 1 with the reasons
    python3 decisions.py list [--life <folder>]       # the latest file's rows, overdue first, then by deadline
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

LIFE = Path.home() / "Software" / "Prototypes" / "socrates" / "life"
COLUMNS = ["id", "decision", "deadline", "options", "depends", "source"]
NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-decisions\.tsv$")
SOURCE = re.compile(r"[\w./ -]+\.(?:md|csv|tsv|txt)(?::\d+(?:-\d+)?)?")


def read(path: Path) -> list[dict]:
    lines = [l for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE)]


def check(path: Path) -> list[str]:
    """The reasons a decisions file breaks the form; none when it holds."""
    path = Path(path)
    fails = []
    if not NAME.match(path.name):
        fails.append(f"{path.name}: name it YYYY-MM-DD-decisions.tsv, dated the day Chaehan confirmed it")
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    if not lines or lines[0].split("\t") != COLUMNS:
        return fails + [f"the header must be {' '.join(COLUMNS)}, tab-separated"]
    seen = set()
    for n, row in enumerate(read(path), 2):
        where = f"row {n} ({row.get('id') or 'no id'})"
        if not row.get("id") or row["id"] in seen:
            fails.append(f"{where}: every row has its own id")
        seen.add(row.get("id"))
        if not row.get("decision"):
            fails.append(f"{where}: the decision is empty")
        d = row.get("deadline", "")
        if d != "none":
            try:
                dt.date.fromisoformat(d)
            except ValueError:
                fails.append(f"{where}: the deadline is YYYY-MM-DD or none, not {d!r}")
        if not row.get("source") or not SOURCE.search(row["source"]):
            fails.append(f"{where}: the source names the record line, as path:line")
        if None in row or len([k for k in row if k]) != len(COLUMNS):
            fails.append(f"{where}: six tab-separated fields")
    return fails


def latest(folder: Path = LIFE) -> Path | None:
    files = sorted(p for p in Path(folder).glob("*-decisions.tsv") if NAME.match(p.name))
    return files[-1] if files else None


def by_deadline(rows: list[dict], today: dt.date) -> list[dict]:
    """Overdue first, then by deadline, then the rows with none, each group in the file's order."""
    def key(r):
        d = r["deadline"]
        return (2, "") if d == "none" else ((0 if d < today.isoformat() else 1), d)
    return sorted(rows, key=key)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check the form of a decisions file")
    c.add_argument("file", type=Path)
    ls = sub.add_parser("list", help="the latest file's rows by deadline")
    ls.add_argument("--life", type=Path, default=LIFE, help=f"the folder (default {LIFE})")
    ls.add_argument("--today", help="the day to count overdue from (default today)")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        fails = check(a.file)
        for f in fails:
            print(f)
        print(f"{a.file.name}: {'PASS' if not fails else f'{len(fails)} problems'}")
        return 1 if fails else 0
    path = latest(a.life)
    if not path:
        print(f"no *-decisions.tsv in {a.life}")
        return 1
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    print(f"{path.name}, confirmed by Chaehan")
    for r in by_deadline(read(path), today):
        late = " (overdue)" if r["deadline"] != "none" and r["deadline"] < today.isoformat() else ""
        print(f"{r['id']}\t{r['deadline']}{late}\t{r['decision']}" + (f"\t[{r['options']}]" if r["options"] not in ("", "none") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
