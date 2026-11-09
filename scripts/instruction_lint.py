#!/usr/bin/env python3
"""Flag instruction paragraphs that ask a model for an element without its source or its empty case (RULES.md 245).

    python3 instruction_lint.py skills/*/SKILL.md commands/*.md [...]   exit 2 when anything is flagged

A model that follows instructions reads each element an instruction names ("name who helped and how",
"the fact that would reverse it", "the consequence") as a requirement and an empty place as a failure,
so where the record holds nothing it fills the place with the most plausible thing in its context
("Jaekeun signed the transfers", 2026-11-08). A paragraph is flagged when it asks for such an element and
says nothing about what to write when the record has none.

I1  a request for an element (who, why, how, the reason, the cause, the consequence, what it took or
    cost, a helper, a benchmark) with no empty case in the paragraph ("when the record holds one",
    "only where", "leave it out", "when none")
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ASK = re.compile(
    r"\b(?:name|names|state|states|give|gives|add|adds|say|says|write|writes|include|includes|cite|cites|"
    r"list|lists|explain|explains|show|shows)\b[^.\n]{0,80}?\b(?:who\b|why\b|how\b|the reason|its reason|"
    r"the cause|its cause|the consequence|its consequence|what it (?:took|cost|costs|makes|gives|means)|"
    r"the helper|who helped|the person|the people|a benchmark|the benchmark|the fact that would|"
    r"what changed and why)", re.I)
EMPTY = re.compile(
    r"when the record (?:holds|has|gives|states)|if the record|only (?:when|where|if)\b|when none|if none|"
    r"leave (?:it |them )?out|left out|stays out|has none|no such line|when it has one|when there is one|"
    r"when one exists|or nothing|is never a failure|never invent|from (?:a|one) (?:record )?line|"
    r"when the record|when available|is asked|asks? (?:Chaehan|him)|^(?:When|If)\b", re.I | re.M)


def paragraphs(text: str):
    start, buf = 1, []
    for n, line in enumerate(text.splitlines() + [""], 1):
        if line.strip() and not line.startswith("#") and not line.startswith("```"):
            if not buf:
                start = n
            buf.append(line)
        elif buf:
            yield start, " ".join(buf)
            buf = []


def lint(text: str) -> list[tuple[int, str]]:
    out = []
    for n, para in paragraphs(text):
        if para.lstrip().startswith(("|", "name:", "description:", "0 ", "- **", "- Not:")) and "---" not in para[:4]:
            continue  # tables, frontmatter, exit-code lists, rule lists and Not/Write example pairs are not slot requests
        para = re.sub(r'"[^"]*"|`[^`]*`', '""', para)  # quoted examples are not requests
        m = ASK.search(para)
        if m and not EMPTY.search(para):
            out.append((n, m.group(0)))
    return out


def main(argv: list[str] | None = None) -> int:
    paths = argv if argv is not None else sys.argv[1:]
    total = 0
    for p in paths:
        for n, hit in lint(Path(p).read_text(encoding="utf-8")):
            total += 1
            print(f"{p}:{n}: I1 asks for an element with no empty case: {hit!r}")
    print(f"instruction_lint: {len(paths)} file(s), {total} paragraph(s) flagged")
    return 2 if total else 0


if __name__ == "__main__":
    sys.exit(main())
