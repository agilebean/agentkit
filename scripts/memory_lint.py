#!/usr/bin/env python3
"""Flag the lines of a memory file that a model reading it can misuse (RULES.md 17, 33, 34, 245).

    python3 memory_lint.py memory/health.md [memory/swim.md ...]   exit 2 on M1, M3, M4 or M6; M2 and M5 are review flags

A model that reads memory takes every line as a current fact about Chaehan, and fills any slot an
instruction names from the most plausible line. Four line shapes feed that error:

M1  a relative or modal time phrase outside a quote ("today", "next week", "in five days", "after 5d",
    "recently", "soon"): it is read against the reader's day, not the writer's (2026-11-11 was computed
    from "the next one in five days"). Write the date, or keep the phrase inside the quote with the date
    it was said.
M2  an old value kept beside its replacement ("superseded", "no longer", "was wrong", "Correction"):
    a reader can take the old value (the third 2026-11-07 overview printed a superseded test plan).
    State the value in force; an old value that still matters becomes a dated line under a History
    heading.
M3  an agent's conclusion stated as fact ("assessment:", "best-fitting", "leading cause") with no hedge
    in the line: say it with "likely" or "may" inside the sentence, or cut it. A hedge in the sentence
    is the mark ("after a long abstinence, the yellow sample color likely comes from sample vesicle
    fluid"), so "likely", "probably", "suggests" and their kin pass.
M4  a person entry with no date and no event ("- **Name:** ..."): a person's role is attached to a dated
    event in one line, or a model attaches the person to the next event it needs a helper for (Minho's
    wire transfers in the furniture shipment, 2026-11-08).

M5  a quote addressed to the agent ("i told you", "you forgot", "why didn't you"), a review flag: a note
    that retells the line quotes the instruction to its reader. Record the fact or the rule it states,
    dated, with Chaehan's own key words quoted; a rule moves to RULES.md or the skill.
M6  the label "the agent's reading" outside a quote: it adds words and leaves the sentence without its
    subject. Write the inference as one sentence with the hedge inside it (Chaehan, 2026-11-23: the
    label leaves notes and memory files alike).

Lines under a heading named History, Log, Archive or Evidence, and under its sub-headings, are history and are
not flagged for M2.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REL = re.compile(r"\b(today|tomorrow|yesterday|tonight|this (?:week|month|morning|evening)|"
                 r"next (?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
                 r"last (?:week|month|night)|in (?:a few|two|three|four|five|six|\d+) (?:days?|weeks?|months?)|"
                 r"after \d+ ?d\b|\d+ days? ago|recently|soon)\b", re.I)
# "Correction" counts as a label ("Correction (2026-09-15): ...", "Correction:"), and "corrected"/"corrects" when it
# names what it replaced; "correction tools", a market correction or a grade-correction window state no old value.
OLD = re.compile(r"(?i:\bsupersed\w*|\bno longer\b|\bwas wrong\b|\bcorrect(?:ed|s) (?:the earlier|from|\d{4}-\d{2})|"
                 r"\breplaced (?:the|an?) (?:first|earlier|old|previous)\b)"
                 r"|\bCorrection\s*[(:]|\bCorrected\b")
CONCLUDE = re.compile(r"\b(assessment:|best-fitting|leading cause)\b", re.I)
HEDGE = re.compile(r"\b(likely|unlikely|probabl\w*|plausibl\w*|possibl\w*|may|might|could|suggests?|"
                   r"appears? to|seems? to|his read|his own read|her read|Chaehan's read)\b", re.I)
LABEL = re.compile(r"agent's reading", re.I)
PERSON = re.compile(r"^\s*- \*\*(?!(?:Phone|Fax|Email|Hours|Address|Website|Web|Mail|Note|Status|Cost|Price|Date|Time|Source|Result|Plan|Rule)\b)[A-Z][a-z]+(?: [A-Z][a-z]+)?:\*\*")
DATED = re.compile(r"\d{4}-\d{2}(?:-\d{2})?|\b(?:19|20)\d\d\b")
HISTORY = re.compile(r"^#{1,4}\s+.*\b(history|log|archive|evidence)\b", re.I)
QUOTE = re.compile(r'"[^"]*"|“[^”]*”')
TO_AGENT = re.compile(r"\b(i told you|told you|you forgot|you must|you should|you mustn't|you did|you didn't|"
                      r"why didn'?t you|why don'?t you|can'?t you|don'?t you|you're wrong|you broke|you missed|"
                      r"you could have|you still|did you just|isn'?t (?:that|it) (?:common sense|obvious))\b", re.I)


def lint(text: str) -> list[tuple[int, str, str]]:
    out, in_history, history_level = [], False, 0
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if in_history and level > history_level:
                continue  # a sub-section of a History section is history too
            in_history = bool(HISTORY.match(line))
            history_level = level if in_history else 0
            continue
        bare = QUOTE.sub('""', line)
        for m in REL.finditer(bare):
            out.append((n, "M1", f"relative time {m.group(0)!r} outside a quote: write the date"))
        if not in_history and OLD.search(bare):
            out.append((n, "M2", "old value beside its replacement: state the value in force, move the old one to History"))
        m = CONCLUDE.search(bare)
        if m and not HEDGE.search(line):
            out.append((n, "M3", f"conclusion {m.group(0)!r} stated as fact: say it with likely or may inside the sentence, or cut it"))
        if LABEL.search(bare):
            out.append((n, "M6", "label 'the agent's reading': write the inference as one sentence with likely or may inside it"))
        for q in re.findall(r'"([^"]{8,})"', line):
            if TO_AGENT.search(q):
                out.append((n, "M5", f"quote addressed to the agent: record the fact it states: {q[:50]!r}"))
                break
        if PERSON.match(line) and not DATED.search(line):
            out.append((n, "M4", "person entry with no date or event: tie the role to a dated event"))
    return out


def main(argv: list[str] | None = None) -> int:
    paths = (argv if argv is not None else sys.argv[1:])
    if not paths:
        print(__doc__.splitlines()[2].strip())
        return 1
    total = 0
    for p in paths:
        hits = lint(Path(p).read_text(encoding="utf-8"))
        total += len(hits)
        for n, code, msg in hits:
            print(f"{p}:{n}: {code} {msg}")
    counts = {}
    for p in paths:
        for _, code, _ in lint(Path(p).read_text(encoding="utf-8")):
            counts[code] = counts.get(code, 0) + 1
    print(f"memory_lint: {len(paths)} file(s), {total} line(s) flagged " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    # M2 is a review flag: a line can name what it replaced while stating the value in force.
    return 2 if any(k not in ("M2", "M5") for k in counts) else 0


if __name__ == "__main__":
    sys.exit(main())
