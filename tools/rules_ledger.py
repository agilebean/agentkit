#!/usr/bin/env python3
"""RULES.md as a ledger of sentences, so a redesign can prove that nothing was lost.

    python3 tools/rules_ledger.py build RULES.md LEDGER.tsv
    python3 tools/rules_ledger.py check LEDGER.tsv DEST.md [DEST.md ...]   exit 2 when a sentence stands in no destination
    python3 tools/rules_ledger.py stats LEDGER.tsv REGISTER.md
    python3 tools/rules_ledger.py evidence LEDGER.tsv REGISTER.md MAP.tsv   which units the register lacks, and where each goes
    python3 tools/rules_ledger.py apply LEDGER.tsv MAP.tsv REGISTER.md TAG   copies them into the register, word for word

Phases 0 and 1 of `docs/2026-11-23 rules redesign plan.md`. `build` splits RULES.md into units: a sentence
of a paragraph or bullet, a heading, a table row, a fenced code block. Each unit gets an identifier
(`R17.004` is the fourth unit of rule 17, `S2.001` the first unit of the second level-2 section
outside any rule) and a first-pass class: incident (a date, a quote of 25 characters or more, a
quoted user or a failure number), test, example, pointer, principle, heading, table or code.
`check` compares the ledger with the files the text moved to, whitespace-normalized, and names each
unit found in none of them. `stats` counts the classes and the quotes the register already holds.

`evidence` decides phase 1 for every unit of a paragraph from its first incident on: "copied" when the
register lacks it, "in register" when it stands there already, "pointer" when it only names a failure
number, and "rule" for every other unit, which stays in RULES.md alone. A paragraph that cites exactly
one failure of the register goes into that failure's entry; any other goes into the rule's entry
"Evidence for rule N" in the register's section "Evidence for the rules". The sentences after an
incident in its paragraph are copied with it, because an incident often runs on in sentences with no
date or quote of their own; a copied principle sentence is a harmless duplicate. `apply` writes the
copies, word for word, and copies nothing the register already holds, so a second run changes nothing.

The ledger and the map quote incidents, so they are written into a private repository (socrates), never agentkit.
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
MAP_FIELDS = ["id", "line", "kind", "decision", "destination"]
ANY_FAILURE = re.compile(r"(?i)\bfailures? (\d+)")
FAILURE_HEAD = re.compile(r"### Failure (\d+):")
POINTER_ONLY = re.compile(r"(?i)(?:Instance: )?`?agent/failures\.md`? failures? \d+(?:, rounds \w+ and \w+)?"
                          r"(?: carries the (?:cause )?analysis)?|Failure \d+ in agent/failures\.md")
EVIDENCE = "## Evidence for the rules"
BEFORE = "## Key learnings & principles"
INTRO = ("Each sentence of agentkit `RULES.md` that tells an instance, and that the failures below lacked, "
         "copied word for word by agentkit `tools/rules_ledger.py apply`: one entry per rule, each instance "
         "with the sentences after it in its paragraph, under the tag and lines it came from. A paragraph "
         "that cites one failure stands in that failure's entry instead, after a line that names its rule.")


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


def _scope(u: Unit) -> str:
    return u.id.split(".")[0]


def _pointer_only(u: Unit) -> bool:
    if DATE.search(u.text) or LONGQUOTE.search(u.text):
        return False
    return not re.sub(r"[\s.;:,]", "", POINTER_ONLY.sub("", u.text))


def evidence_plan(units: list[Unit], register: str) -> list[tuple[Unit, str, str]]:
    """Every unit with its phase-1 decision and destination ("failure N" or "evidence R17")."""
    hay = norm(register)
    failures = set(FAILURE_HEAD.findall(register))
    paras: dict[tuple[str, int], list[Unit]] = {}
    for u in units:
        if u.kind not in ("heading", "table", "code"):
            paras.setdefault((_scope(u), u.line), []).append(u)
    decided: dict[str, tuple[str, str]] = {}
    for (scope, _), us in paras.items():
        cited = {n for u in us for n in ANY_FAILURE.findall(u.text) if n in failures}
        dest = f"failure {next(iter(cited))}" if len(cited) == 1 else f"evidence {scope}"
        seen = False
        for u in us:
            seen = seen or u.kind == "incident"
            if not seen:
                continue
            if _pointer_only(u):
                decided[u.id] = ("pointer", "")
            elif norm(u.text) in hay:
                decided[u.id] = ("in register", "")
            else:
                decided[u.id] = ("copied", dest)
    return [(u, *decided.get(u.id, ("rule", ""))) for u in units]


def write_map(rows: list[tuple[Unit, str, str]], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        w.writerow(MAP_FIELDS)
        for u, decision, dest in rows:
            w.writerow([u.id, u.line, u.kind, decision, dest])


def read_map(units: list[Unit], path: Path) -> list[tuple[Unit, str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        got = {r["id"]: (r["decision"], r["destination"]) for r in csv.DictReader(f, delimiter="\t")}
    return [(u, *got.get(u.id, ("rule", ""))) for u in units]


def _title(u: Unit) -> str:
    return re.sub(r"^#{1,6} (?:\d+\. )?", "", u.text)


def _where(scope: str, titles: dict[str, str]) -> str:
    if scope.startswith("R"):
        return f"RULES.md rule {scope[1:]}"
    return "the RULES.md preamble" if scope == "S0" else f'the RULES.md section "{titles.get(scope, scope)}"'


def _entry_head(scope: str, titles: dict[str, str]) -> tuple[str, str]:
    """The entry's heading and the prefix that finds it again."""
    if scope.startswith("R"):
        prefix = f"### Evidence for rule {scope[1:]}:"
        return f"{prefix} {titles.get(scope, '')}".rstrip(), prefix
    head = f"### Evidence for {_where(scope, titles)}"
    return head, head


def _end_of_entry(lines: list[str], i: int) -> int:
    j = i + 1
    while j < len(lines) and not lines[j].startswith(("### ", "## ")):
        j += 1
    while j > i + 1 and not lines[j - 1].strip():
        j -= 1
    return j


def _insert(lines: list[str], at: int, block: list[str]) -> None:
    if at < len(lines) and lines[at].strip():
        block = block + [""]
    lines[at:at] = block


def apply(units: list[Unit], rows: list[tuple[Unit, str, str]], register: str, tag: str) -> str:
    """The register with every copied unit added word for word; a unit it already holds is skipped."""
    hay = norm(register)
    titles: dict[str, str] = {}
    for u in units:
        if u.kind == "heading":
            titles.setdefault(_scope(u), _title(u))
    runs: list[tuple[str, str, int, list[str]]] = []
    last = None
    for u, decision, dest in rows:
        if decision != "copied" or norm(u.text) in hay:
            last = None
            continue
        key = (dest, _scope(u), u.line)
        if key == last:
            runs[-1][3].append(u.text)
        else:
            runs.append((dest, _scope(u), u.line, [u.text]))
        last = key
    lines = register.split("\n")
    heads = {m.group(1): i for i, ln in enumerate(lines) if (m := FAILURE_HEAD.match(ln))}
    to_failure: dict[str, list[str]] = {}
    for dest, scope, line, texts in runs:
        if dest.startswith("failure "):
            to_failure.setdefault(dest.split()[1], []).extend(
                ["", f"**From {_where(scope, titles)}**, tag `{tag}`, line {line}:", "", " ".join(texts)])
    for n in sorted(to_failure, key=lambda n: heads[n], reverse=True):
        _insert(lines, _end_of_entry(lines, heads[n]), to_failure[n])
    to_entry: dict[str, list[tuple[int, list[str]]]] = {}
    for dest, scope, line, texts in runs:
        if dest.startswith("evidence "):
            to_entry.setdefault(dest.split()[1], []).append((line, texts))
    if to_entry and EVIDENCE not in lines:
        at = lines.index(BEFORE) if BEFORE in lines else len(lines)
        _insert(lines, at, [EVIDENCE, "", INTRO, ""])
    for scope, items in to_entry.items():
        head, prefix = _entry_head(scope, titles)
        first, final = items[0][0], items[-1][0]
        span = f"line {first}" if first == final else f"lines {first} to {final}"
        body = [f"Tag `{tag}`, RULES.md {span}."]
        for _, texts in items:
            body += ["", " ".join(texts)]
        start = lines.index(EVIDENCE)
        stop = next((k for k in range(start + 1, len(lines)) if lines[k].startswith("## ")), len(lines))
        found = next((k for k in range(start + 1, stop) if lines[k].startswith(prefix)), None)
        if found is not None:
            _insert(lines, _end_of_entry(lines, found), [""] + body)
        else:
            k = stop
            while k > start + 1 and not lines[k - 1].strip():
                k -= 1
            _insert(lines, k, ["", head, ""] + body)
    return "\n".join(lines)


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
    if len(argv) == 4 and argv[0] == "evidence":
        units = read(Path(argv[1]))
        register = Path(argv[2]).read_text(encoding="utf-8")
        rows = evidence_plan(units, register)
        write_map(rows, Path(argv[3]))
        counts: dict[str, int] = {}
        for _, decision, _ in rows:
            counts[decision] = counts.get(decision, 0) + 1
        words = sum(len(u.text.split()) for u, d, _ in rows if d == "copied")
        found, total = quote_coverage(units, apply(units, rows, register, "TAG"))
        print(f"rules_ledger: {counts}, {words} words to copy; quotes in the register after apply: {found} of {total}")
        return 0
    if len(argv) == 5 and argv[0] == "apply":
        units = read(Path(argv[1]))
        register_path = Path(argv[3])
        register = register_path.read_text(encoding="utf-8")
        new = apply(units, read_map(units, Path(argv[2])), register, argv[4])
        register_path.write_text(new, encoding="utf-8")
        found, total = quote_coverage(units, new)
        print(f"rules_ledger: {len(new.split()) - len(register.split())} words added; quotes in the register: {found} of {total}")
        return 0
    print(__doc__.splitlines()[2].strip())
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
