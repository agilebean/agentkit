#!/usr/bin/env python3
"""Check the report of a runbook run against the form of the DeepSeek delegation plan (task DD-01).

    python3 scripts/report_check.py REPORT.md      exit 0 when it passes, 2 with one line per problem

The report is the one text of a DeepSeek run that reaches Chaehan, so its form is fixed and this script,
not the model, decides whether it holds (`docs/deepseek delegation plan.md`, "The report you get"):

    done: 14 of 14 acceptance tests pass

    | What changed | Before | After | Evidence |
    |---|---|---|---|
    | the red test | 1 failed | 0 failed | `pytest -q tests/test_x.py` printed `3 passed` |

    | Open item | Who decides | By when |
    |---|---|---|
    | the history rewrite | Chaehan | 2026-11-27 |

R1  text outside the three parts: a heading, a paragraph, a list, a third table
R2  a first line that is neither `done: <number with its unit> ...` nor `stopped at <test id>: <reason>`
R3  a table whose header differs from the form, or a row with another number of cells
R4  an empty cell (blank, a dash, n/a), an Evidence cell with no command, file or output line in backticks,
    or a `done` report without a change row
R5  a number without its unit: `1` or `0` alone in a cell, where `1 failed` and `0 flags` are meant
R6  a cell of more than one clause: a sentence break, a semicolon, a line break or more than 20 words
R7  a hit of `wording_lint.py --strict` (the robot markers of RULES.md rule 2, Han characters)
R8  a By when cell without a date YYYY-MM-DD

What counts as a unit: a word after the number (`3 tests`, `14 of 14 tests`, `1 → 0 failures`), `%`, a
currency sign before it. A number glued to letters (T3, DD-02, 18s, a commit hash), a date, a time, a version
x.y.z, a number after a label word (`line 148`, `rule 74`, `Python 3.14`) and everything in backticks is not a
quantity and needs none.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wording_lint  # noqa: E402

CHANGES = ["What changed", "Before", "After", "Evidence"]
OPEN = ["Open item", "Who decides", "By when"]
FIRST = re.compile(r"^(?:done: (?P<done>\S.*)|stopped at (?P<id>[A-Z][A-Za-z]*-?\d+(?:\.\d+)*): (?P<why>\S.*))$")
EMPTY = re.compile(r"^\s*(?:|-+|–|—|n/?a|tbd|\?|\.\.\.|…)\s*$", re.I)
SEPARATOR = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
MAX_WORDS = 20

# Words that are no unit after a number and no label before one: "is 5", "rose from 1", "at 3".
FUNCTION = set("""a an the and or nor but so then of to from in on at by for with into onto as than per each every
after before under over within about above below between is are was were be been being has have had do does did
not no only all any some this that these those it its""".split())
# Exempt from R5 before numbers are read: code, links, dates, times, versions, and tokens that hold a letter
# and a digit together (T3, DD-02, 18s, 1ca5c84, py3) or a slash and a letter (tests/x.py:148).
MASKS = [re.compile(p) for p in (
    r"`[^`]*`",
    r"\]\([^)]*\)|https?://\S+",
    r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{1,2}:\d{2}(?::\d{2})?)?\b",
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b",
    r"\bv?\d+(?:\.\d+){2,}\b",
    r"\S*[A-Za-z]\S*/\S*|\S*/\S*[A-Za-z]\S*",
    r"[A-Za-z_][\w.-]*\d[\w.-]*|\d[\w.-]*[A-Za-z_][\w.-]*",
)]
NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?!\w|\.\d)")
CHAIN = re.compile(r"(?:\s*(?:of|to|or|and|/|-|–|→|->|x|×)\s*~?\d+(?:\.\d+)?)*\s*")
UNIT = re.compile(r"%|°|[A-Za-z][\w-]*")


def split_row(line: str) -> list[str]:
    """The cells of a table row; a pipe inside backticks or after a backslash belongs to its cell."""
    body = line.strip()
    body = body[1:] if body.startswith("|") else body
    body = body[:-1] if body.endswith("|") and not body.endswith("\\|") else body
    cells, cur, code = [], "", False
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            cur += "|"
            i += 2
            continue
        if ch == "`":
            code = not code
        if ch == "|" and not code:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
        i += 1
    cells.append(cur.strip())
    return cells


def masked(text: str) -> str:
    for m in MASKS:
        text = m.sub(lambda x: "§" * len(x.group(0)), text)
    return text


def bare_numbers(text: str) -> list[str]:
    """The numbers in a cell that stand without a unit (R5)."""
    t = masked(text)
    bad = []
    for m in NUMBER.finditer(t):
        before = t[:m.start()]
        if re.search(r"[$€¥₩£#]\s?$", before):
            continue
        label = re.search(r"([A-Za-z][\w-]*)\s+$", before)
        if label and label.group(1).lower() not in FUNCTION:
            continue
        rest = t[m.end():]
        chain = CHAIN.match(rest)
        unit = UNIT.match(rest, chain.end())
        if unit and unit.group(0).lower() not in FUNCTION:
            continue
        bad.append(m.group(0))
    return bad


def clause_problem(text: str) -> str | None:
    """Why a cell holds more than one clause (R6), or None."""
    t = re.sub(r"`[^`]*`", "code", text)
    if re.search(r"<br\s*/?>", t, re.I):
        return "a line break"
    if ";" in t:
        return "a semicolon"
    if re.search(r"(?<!\b[A-Za-z])(?<!\be\.g)(?<!\bi\.e)[.!?]\s+[A-Z]", t):
        return "a second sentence"
    words = len(re.findall(r"[^\s|]+", t))
    if words > MAX_WORDS:
        return f"{words} words, more than {MAX_WORDS} words"
    return None


def check(text: str, rules=None) -> list[tuple[int, str, str]]:
    """Every problem of a report as (line, rule, message); an empty list is a pass."""
    rules = rules if rules is not None else wording_lint.load_robot_markers()
    lines = text.splitlines()
    problems: list[tuple[int, str, str]] = []

    def cell_checks(lineno: int, name: str, value: str) -> None:
        for n in bare_numbers(value):
            problems.append((lineno, "R5", f"{name} '{value}': the number {n} needs its unit ('{n} tests', '{n} files')"))
        why = clause_problem(value)
        if why:
            problems.append((lineno, "R6", f"{name} '{value}': one clause per cell, this one has {why}"))
        for _, _, match, fix in wording_lint.lint_text(value, rules):
            problems.append((lineno, "R7", f"{name} '{value}': '{match}' - {fix}"))
        for _, char, _ in wording_lint.script_hits(value):
            problems.append((lineno, "R7", f"{name} '{value}': '{char}' - Han characters, write it in English"))

    first = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first is None:
        return [(1, "R2", "the report is empty")]
    head = lines[first].strip()
    m = FIRST.match(head)
    if first != 0:
        problems.append((first + 1, "R1", "the outcome is the first line of the file"))
    if not m:
        problems.append((first + 1, "R2", f"first line '{head}': write 'done: <number> <unit> ...' or "
                                          "'stopped at <test id>: <reason>'"))
    else:
        if m.group("done") is not None and not NUMBER.search(masked(m.group("done"))):
            problems.append((first + 1, "R2", f"first line '{head}': a done line states its number, "
                                              "'done: 6 of 6 acceptance tests pass'"))
        cell_checks(first + 1, "first line", head)

    blocks: list[tuple[int, list[str]]] = []
    i = first + 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith("|"):
            start, rows = i, []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i])
                i += 1
            blocks.append((start, rows))
            continue
        problems.append((i + 1, "R1", f"text outside the outcome line and the two tables: '{line.strip()[:80]}'"))
        i += 1

    tables = {}
    for n, (start, rows) in enumerate(blocks):
        header = split_row(rows[0])
        if header == CHANGES and "changes" not in tables:
            kind = "changes"
        elif header == OPEN and "open" not in tables:
            kind = "open"
        else:
            problems.append((start + 1, "R1" if n >= 2 else "R3",
                             f"table header {header}: the report holds two tables, "
                             f"{CHANGES} and then {OPEN}"))
            continue
        if kind == "open" and "changes" not in tables:
            problems.append((start + 1, "R3", "the table of changes comes before the table of open items"))
        if len(rows) < 2 or not SEPARATOR.match(rows[1].strip()):
            problems.append((start + 2, "R3", "the header row is followed by a separator row |---|"))
            body = rows[1:]
            offset = 1
        else:
            body = rows[2:]
            offset = 2
        tables[kind] = []
        for k, row in enumerate(body):
            lineno = start + offset + k + 1
            cells = split_row(row)
            if len(cells) != len(header):
                problems.append((lineno, "R3", f"a row of {len(cells)} cells under a header of {len(header)} cells"))
                continue
            tables[kind].append(cells)
            for name, value in zip(header, cells):
                if EMPTY.match(value) or (name == "Evidence" and value.strip().lower() in ("none", "ok", "done", "yes")):
                    problems.append((lineno, "R4", f"{name} is empty: write what it holds"))
                    continue
                if name == "Evidence" and "`" not in value:
                    problems.append((lineno, "R4", f"Evidence '{value}': put the command, file or output line "
                                                   "in backticks"))
                if name == "By when" and not DATE.search(value):
                    problems.append((lineno, "R8", f"By when '{value}': a date YYYY-MM-DD"))
                cell_checks(lineno, name, value)
    for kind, header in (("changes", CHANGES), ("open", OPEN)):
        if kind not in tables:
            problems.append((len(lines), "R3", f"the table {header} is missing; write its header even with no rows"))
    if m and m.group("done") is not None and "changes" in tables and not tables["changes"]:
        problems.append((first + 1, "R4", "a done report has at least one change row"))
    return problems


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0].startswith("-"):
        print(__doc__.split("\n\n")[1])
        return 1
    path = Path(argv[0])
    if not path.is_file():
        print(f"report_check: no file at {path}")
        return 1
    problems = check(path.read_text(encoding="utf-8"))
    for lineno, rule, message in sorted(problems):
        print(f"{path}:{lineno}: {rule} {message}")
    if problems:
        print(f"report_check: FAIL, {len(problems)} problem(s); fix each line named and run it again")
        return 2
    print("report_check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
