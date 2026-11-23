#!/usr/bin/env python3
"""RULES.md as a ledger of sentences, so a redesign can prove that nothing was lost.

    python3 tools/rules_ledger.py build RULES.md LEDGER.tsv
    python3 tools/rules_ledger.py check LEDGER.tsv DEST.md [DEST.md ...]   exit 2 when a sentence stands in no destination
    python3 tools/rules_ledger.py stats LEDGER.tsv REGISTER.md

Phase 0 of `docs/2026-11-23 rules redesign plan.md`. `build` splits RULES.md into units: a sentence
of a paragraph or bullet, a heading, a table row, a fenced code block. Each unit gets an identifier
(`R17.004` is the fourth unit of rule 17, `S2.001` the first unit of the second level-2 section
outside any rule) and a first-pass class: incident (a date, a quote of 25 characters or more, a
quoted user or a failure number), test, example, pointer, principle, heading, table or code.
`check` compares the ledger with the files the text moved to, whitespace-normalized, and names each
unit found in none of them. `stats` counts the classes and the quotes the register already holds.

The ledger quotes incidents, so it is written into a private repository (socrates), never agentkit.
"""
from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
LONGQUOTE = re.compile(r'"([^"\n]{25,})"|“([^”\n]{25,})”')
FAILURE = re.compile(r"\bfailures? (\d+)")
QUOTED_USER = re.compile(r"\bChaehan(?:, 20\d\d-\d\d-\d\d)?:|\b[Tt]he user(?:, 20\d\d-\d\d-\d\d)?:")
TEST = re.compile(r"^(?:\*\*)?Test\b|\btests?/|\b\w+\.py\b|\b(?:the|a) (?:test|check|gate)\b|\blint\b", re.I)
EXAMPLE = re.compile(r"\be\.g\.|\bfor example\b|\bfor instance\b|\bsuch as\b", re.I)
POINTER = re.compile(r"\b(?:see|per) (?:rule|RULES\.md)\b|\bRULES\.md \d+\b|\brules? \d+\b")
ABBR = {"e.g.", "i.e.", "vs.", "cf.", "p.", "pp.", "ch.", "no.", "fig.", "approx.", "etc.", "dr.", "mr.", "st."}
BULLET = re.compile(r"\s*(?:[-*+]|\d+\.)\s")
FIELDS = ["id", "line", "kind", "dates", "failures", "text"]


@dataclass
class Unit:
    id: str
    line: int
    kind: str
    text: str
    dates: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def norm(text: str) -> str:
    return " ".join(text.split())


def classify(text: str) -> str:
    if DATE.search(text) or LONGQUOTE.search(text) or QUOTED_USER.search(text) or FAILURE.search(text):
        return "incident"
    if TEST.search(text):
        return "test"
    if EXAMPLE.search(text):
        return "example"
    if POINTER.search(text) and len(text.split()) < 25:
        return "pointer"
    return "principle"


def _open_quote(text: str) -> bool:
    return text.count('"') % 2 == 1 or text.count("“") > text.count("”")


def sentences(text: str) -> list[str]:
    words = norm(text).split(" ")
    out, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        nxt = words[k + 1] if k + 1 < len(words) else ""
        core = w.rstrip('"”’\')]*`')
        ends = core.endswith((".", "!", "?")) and w.lower() not in ABBR and core.lower() not in ABBR
        starts = bool(nxt) and (nxt[0].isupper() or nxt[0].isdigit() or nxt[0] in '"“*`')
        if ends and starts and not _open_quote(" ".join(cur)):
            out.append(" ".join(cur))
            cur = []
    if cur and cur != [""]:
        out.append(" ".join(cur))
    return out


def split(source: str) -> list[Unit]:
    lines = source.splitlines()
    units: list[Unit] = []
    counters: dict[str, int] = {}
    scope, section = "S0", 0
    para: list[str] = []
    para_line = 0

    def emit(kind: str, text: str, line: int) -> None:
        text = norm(text)
        if not text:
            return
        counters[scope] = counters.get(scope, 0) + 1
        kind = kind or classify(text)
        units.append(Unit(f"{scope}.{counters[scope]:03d}", line, kind, text,
                          DATE.findall(text), FAILURE.findall(text)))

    def flush() -> None:
        nonlocal para
        if para:
            for s in sentences(" ".join(para)):
                emit("", s, para_line)
        para = []

    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.lstrip().startswith("```"):
            flush()
            start, block = i + 1, [ln]
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                block.append(lines[i])
                i += 1
            if i < len(lines):
                block.append(lines[i])
            emit("code", "\n".join(block), start)
        elif re.match(r"#{1,6} ", ln):
            flush()
            if m := re.match(r"### (\d+)\. ", ln):
                scope = f"R{m.group(1)}"
            elif ln.startswith("## "):
                section += 1
                scope = f"S{section}"
            emit("heading", ln, i + 1)
        elif ln.lstrip().startswith("|"):
            flush()
            emit("table", ln, i + 1)
        elif not ln.strip():
            flush()
        elif BULLET.match(ln):
            flush()
            para, para_line = [ln], i + 1
        else:
            if not para:
                para_line = i + 1
            para.append(ln)
        i += 1
    flush()
    return units


def write(units: list[Unit], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        w.writerow(FIELDS)
        for u in units:
            w.writerow([u.id, u.line, u.kind, ",".join(u.dates), ",".join(u.failures), u.text])


def read(path: Path) -> list[Unit]:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return [Unit(r["id"], int(r["line"]), r["kind"], r["text"],
                 [d for d in r["dates"].split(",") if d], [n for n in r["failures"].split(",") if n]) for r in rows]


def check(units: list[Unit], destinations: list[Path]) -> list[Unit]:
    hay = norm(" ".join(Path(p).read_text(encoding="utf-8") for p in destinations))
    return [u for u in units if norm(u.text) not in hay]


def quote_coverage(units: list[Unit], register_text: str) -> tuple[int, int]:
    hay = norm(register_text)
    quotes = {norm(a or b) for u in units for a, b in LONGQUOTE.findall(u.text)}
    return sum(1 for q in quotes if q in hay), len(quotes)


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "build":
        units = split(Path(argv[1]).read_text(encoding="utf-8"))
        write(units, Path(argv[2]))
        print(f"rules_ledger: {len(units)} units written to {argv[2]}")
        return 0
    if len(argv) >= 3 and argv[0] == "check":
        missing = check(read(Path(argv[1])), [Path(p) for p in argv[2:]])
        for u in missing:
            print(f"{u.id} (line {u.line}, {u.kind}): {u.text[:100]}")
        print(f"rules_ledger: {len(missing)} unit(s) in no destination")
        return 2 if missing else 0
    if len(argv) == 3 and argv[0] == "stats":
        units = read(Path(argv[1]))
        counts: dict[str, int] = {}
        words: dict[str, int] = {}
        for u in units:
            counts[u.kind] = counts.get(u.kind, 0) + 1
            words[u.kind] = words.get(u.kind, 0) + len(u.text.split())
        for k in sorted(counts, key=lambda k: -words[k]):
            print(f"{k:10s} {counts[k]:5d} units {words[k]:6d} words")
        found, total = quote_coverage(units, Path(argv[2]).read_text(encoding="utf-8"))
        print(f"quotes of 25 characters or more: {total}, in the register: {found}")
        return 0
    print(__doc__.splitlines()[2].strip())
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
