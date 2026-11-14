#!/usr/bin/env python3
"""Check a date-analysis draft before it goes to the note gate.

Usage:
  date_check.py DRAFT --transcript T.md [--verbatim FILE]

Three checks, each printed with the line to fix; exit 0 only when all pass.

1. Wording. The shared robot markers and this skill's `date_markers.tsv`, with
   every warn counted as a failure (wording_lint --strict). Chaehan's own words,
   passed with --verbatim, are left out of this check.
2. Quotes. Every quotation that holds Hangul carries the time of its turn,
   `"..." [1:02:03]`, copied from the transcript line, and the quoted words stand
   in that turn or one of the two turns around it. Words left out inside a quote
   are written "...". A quote without a time, or one the turn does not hold,
   fails: an invented or misplaced quote is the costliest error in this note.
3. Sections, depth and length. The H2 sections of SKILL.md, in that order; at
   least three quotes on sex and past relationships; at most 1500 words outside
   the quotes (Chaehan, 2026-11-12: "no quality over quantity").
4. Formula. One sentence opening (its first four words) used four times or
   more: on 2026-11-11 "You would think again if" closed all fourteen trait
   sections. A bullet that starts with a quote is left out.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
AGENTKIT = SKILL.parents[1]

SECTIONS = [
    "Takeaway",
    "Sex and past relationships",
    "Her feelings for you",
    "How it changed since your first meeting",
    "Compared with your other dates",
    "What you can do better",
    "What stands out about her",
    "Source",
]
OPTIONAL = {"Your feedback"}
MAX_WORDS = 1500          # outside quotes: Chaehan, 2026-11-12, "quality over quantity"
MIN_SEX_QUOTES = 3

HANGUL = re.compile(r"[\uac00-\ud7a3]")
QUOTE = re.compile(r"[\"“]([^\"”]*[\uac00-\ud7a3][^\"”]*)[\"”]")
TIME = re.compile(r"\[(\d+:\d\d:\d\d)\]")
TURN = re.compile(r"^T(\d{4,5}) \[(\d+:\d\d:\d\d)\] ([^:]+): (.*)$")


def _lint():
    spec = importlib.util.spec_from_file_location("wording_lint", AGENTKIT / "scripts" / "wording_lint.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm(s: str) -> str:
    """Hangul, Latin letters and digits only: the transcript's spacing and punctuation vary."""
    return re.sub(r"[^\w\uac00-\ud7a3]|_", "", s).lower()


def wording(draft: str, verbatim: str) -> list[str]:
    lint = _lint()
    rules = lint.load_robot_markers() + lint.load_robot_markers(str(SKILL / "date_markers.tsv"))
    his = {norm(p) for p in re.split(r"\n\s*\n", verbatim) if norm(p)}
    out = []
    for n, level, words, fix in lint.lint_text(draft, rules):
        line = draft.splitlines()[n - 1]
        if his and any(norm(line) and norm(line) in p for p in his):
            continue
        out.append(f"wording, line {n}: '{words}' - {fix}")
    return out


def load_turns(path: str) -> list[tuple[str, str, str]]:
    turns = []
    for line in open(path, encoding="utf-8"):
        m = TURN.match(line.rstrip("\n"))
        if m:
            turns.append((m.group(2), m.group(3), m.group(4)))
    return turns


def quotes(draft: str, turns: list[tuple[str, str, str]]) -> tuple[list[str], int]:
    by_time: dict[str, list[int]] = {}
    for i, (t, _w, _x) in enumerate(turns):
        by_time.setdefault(t, []).append(i)
    out, n_ok = [], 0
    for n, line in enumerate(draft.splitlines(), 1):
        for m in QUOTE.finditer(line):
            q = m.group(1)
            after = line[m.end():]
            nxt = QUOTE.search(after)
            tm = TIME.search(after[: nxt.start()] if nxt else after)
            if not tm:
                out.append(f"quote, line {n}: \"{q[:40]}\" has no [h:mm:ss] time of its turn")
                continue
            idx = by_time.get(tm.group(1))
            if not idx:
                out.append(f"quote, line {n}: no turn starts at [{tm.group(1)}]; copy the time from the transcript line")
                continue
            window = " ".join(turns[j][2] for i in idx for j in range(max(0, i - 2), min(len(turns), i + 3)))
            hay = norm(window)
            parts = [norm(p) for p in re.split(r"\.\.\.|…", q) if norm(p)]
            if all(p in hay for p in parts):
                n_ok += 1
            else:
                miss = next(p for p in re.split(r"\.\.\.|…", q) if norm(p) and norm(p) not in hay)
                out.append(f"quote, line {n}: \"{miss.strip()[:40]}\" is not in the turn at [{tm.group(1)}] "
                           f"or the two turns around it; quote the transcript's words as they stand")
    return out, n_ok


def sections(draft: str) -> list[str]:
    heads = [m.group(1).strip() for m in re.finditer(r"^## (.+)$", draft, re.M)]
    out = []
    got = [h for h in heads if h not in OPTIONAL]
    for want in SECTIONS:
        if not any(h.startswith(want) for h in got):
            out.append(f"sections: '## {want}' is missing")
    order = [next((i for i, w in enumerate(SECTIONS) if h.startswith(w)), None) for h in got]
    order = [o for o in order if o is not None]
    if order != sorted(order):
        out.append("sections: the H2 sections are out of the order SKILL.md gives")
    m = re.search(r"^## Sex and past relationships.*?(?=^## |\Z)", draft, re.M | re.S)
    if m and len(QUOTE.findall(m.group(0))) < MIN_SEX_QUOTES:
        out.append(f"depth: 'Sex and past relationships' quotes {len(QUOTE.findall(m.group(0)))} lines; "
                   f"it needs {MIN_SEX_QUOTES} or more, his own included (traits.md, the decoding table)")
    words = len(QUOTE.sub("", draft).split())
    if words > MAX_WORDS:
        out.append(f"length: {words} words outside the quotes; keep at most {MAX_WORDS}: "
                   f"keep a point only when it serves one of the five in SKILL.md")
    return out


def formula(draft: str, limit: int = 4) -> list[str]:
    """A sentence opening repeated `limit` times or more: a template, never a person talking."""
    seen: dict[str, list[int]] = {}
    for n, line in enumerate(draft.splitlines(), 1):
        s = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line).strip()
        if not s or s.startswith(("#", "|", '"', "\u201c")):
            continue
        words = re.findall(r"[\w']+", s.lower())
        if len(words) >= 4:
            seen.setdefault(" ".join(words[:4]), []).append(n)
    return [f"formula: \"{k}\" opens {len(v)} sentences (lines {v[:6]}); say each point in its own words"
            for k, v in seen.items() if len(v) >= limit]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--verbatim", help="Chaehan's own words in the draft, left out of the wording check")
    a = ap.parse_args(argv)
    draft = open(a.draft, encoding="utf-8").read()
    verbatim = open(a.verbatim, encoding="utf-8").read() if a.verbatim else ""
    turns = load_turns(a.transcript)
    if not turns:
        sys.exit(f"date_check: no turns in {a.transcript}; export it with mw_transcript.py export")
    fails = wording(draft, verbatim)
    qf, n_ok = quotes(draft, turns)
    fails += qf + sections(draft) + formula(draft)
    for f in fails:
        print("  " + f)
    print(f"date_check: {len(fails)} failure(s), {n_ok} quote(s) found in the transcript")
    print("PASS" if not fails else "FAIL")
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
