"""Mechanical gate for a life-overview draft (checks T3 to T6).

Each failure names the sentence or section it rejects. Exit 1 on any failure.

    python overview_gate.py <draft.md> [--original <old.md>] [--linked <note.md> ...]

T3  a Takeaway bullet made mostly of an Open tasks row's words (numbers ignored)
T4  a body section with no note link (unless it says "no detail note");
    a note with zero links
T5  no indented bullet anywhere
T6  a date or number of the original that survives neither in the draft nor in a
    linked note (only with --original; thousand separators ignored)

--facts-only runs T6 alone, for any note that is not a life overview.
--note runs T6 plus T5 for any note: a section of 3 or more sentences with no
list in it is named; T7 a table row of the original that is gone; T8 an empty
list item; T10 a summary of more than 5 lines or a line over 30 words; T11 a
summary line that repeats a body line; T12 more than 7 list items at one level
under one parent.

--cuts <file> is the cut list: one line per removal, "- <numbers or words>:
<where it went or why it left>". A number of the original passes T6 when the
cut list names it. T9 is a cut line with no reason. Cutting is the point of a
rewrite: the gate checks that each cut is declared, not that nothing was cut.
"""

from __future__ import annotations

import argparse
import re
import sys

STOP = set(
    "the and for with that this from your you are was has have not into only "
    "until when then than what which will been before after there their them "
    "about still also each more most less does".split()
)
NO_LINK_SECTIONS = ("takeaway", "what went well", "open tasks", "the route")
LINK = re.compile(r"evernote:///view/")
FACT = re.compile(r"\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?")


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9가-힣]+", text.lower()) if len(w) >= 4 and w not in STOP}


def sections(md: str) -> list[tuple[str, str]]:
    out, title, buf = [], "", []
    for line in md.splitlines():
        m = re.match(r"#{2,3}\s+(.*)", line)
        if m:
            out.append((title, "\n".join(buf)))
            title, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    out.append((title, "\n".join(buf)))
    return [(t, b) for t, b in out if t]


def takeaway_bullets(md: str) -> list[str]:
    for title, body in sections(md):
        if title.lower().startswith("takeaway"):
            return [l[2:].strip() for l in body.splitlines() if l.startswith("- ")]
    return []


def task_rows(md: str) -> list[str]:
    for title, body in sections(md):
        if "open tasks" in title.lower():
            rows = [l for l in body.splitlines() if l.startswith("|")]
            return [r for r in rows[2:]]
    return []


def check(draft: str, original: str | None = None, linked: list[str] | None = None,
          facts_only: bool = False, note: bool = False, cuts: str | None = None) -> list[str]:
    fails: list[str] = []
    pool = list(linked or [])
    if cuts:
        fails += _bad_cuts(cuts)
        pool.append(cuts)
    if facts_only or note:
        if note:
            fails += _prose_sections(draft)
            fails += _empty_items(draft)
            fails += _summary(draft)
            fails += _flat_lists(draft)
            if original is not None:
                fails += _lost_rows(draft, original)
        return fails + (_facts(draft, original, pool) if original is not None else [])
    rows = task_rows(draft)
    for b in takeaway_bullets(draft):
        bw = {w for w in words(b) if not w.isdigit()}
        for r in rows:
            cells = [c for c in r.strip().strip("|").split("|")]
            rw = {w for w in words(" ".join(cells)) if not w.isdigit()}
            shared = len(bw & rw)
            if bw and rw and shared / len(rw) >= 0.5 and shared / len(bw) >= 0.3:
                fails.append(f"T3 Takeaway bullet repeats a task row: {b!r} ~ {r.strip()!r}")
                break
    if not LINK.search(draft):
        fails.append("T4 the note carries no evernote:/// link")
    for title, body in sections(draft):
        if title.lower().startswith(NO_LINK_SECTIONS) or not body.strip():
            continue
        if not LINK.search(body) and "no detail note" not in body.lower():
            fails.append(f"T4 section without a link to its detail note: {title!r}")
    if not re.search(r"^[ \t]{2,}- ", draft, re.M):
        fails.append("T5 no indented bullet: every point is a sibling")
    if original is not None:
        fails += _facts(draft, original, linked)
    return fails


def _prose_sections(md: str) -> list[str]:
    out = []
    for title, body in sections(md):
        lines = [l for l in body.splitlines() if l.strip()]
        if any(re.match(r"\s*(?:[-*]|\d+[.)]|[a-z]\))\s", l) for l in lines):
            continue
        prose = " ".join(l for l in lines if not l.lstrip().startswith("|"))
        n = len(re.findall(r"[.!?](?:\s|$)", prose))
        if n >= 3:
            out.append(f"T5 section is prose of {n} sentences, write it as a list: {title!r}")
    return out


def _empty_items(md: str) -> list[str]:
    return [f"T8 empty list item at line {i}" for i, l in enumerate(md.splitlines(), 1)
            if re.fullmatch(r"\s*(?:[-*]|\d+[.)]|[a-z]\))\s*", l)]


def _row(l: str) -> str:
    return " ".join(l.split())


def _lost_rows(draft: str, original: str) -> list[str]:
    have = {_row(l) for l in draft.splitlines() if l.lstrip().startswith("|")}
    rows = [_row(l) for l in original.splitlines() if l.lstrip().startswith("|")]
    return [f"T7 table row lost: {r}" for r in rows if r not in have and not re.fullmatch(r"[|\s:-]+", r)]


def _bad_cuts(cuts: str) -> list[str]:
    return [f"T9 cut without a reason or destination: {l.strip()!r}" for l in cuts.splitlines()
            if l.strip() and not re.match(r"\s*-?\s*[^:]+:\s*\S", l)]


SUMMARY_HEADS = ("summary", "takeaway")


def _bullets(body: str) -> list[str]:
    return [re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", l).strip() for l in body.splitlines()
            if re.match(r"\s*(?:[-*]|\d+[.)])\s+\S", l)]


def _summary(md: str) -> list[str]:
    out = []
    secs = sections(md)
    summ = [b for t, b in secs if t.lower().startswith(SUMMARY_HEADS)]
    if not summ:
        return out
    lines = _bullets(summ[0])
    if len(lines) > 5:
        out.append(f"T10 summary has {len(lines)} lines, keep at most 5: one per decision, move the rest down")
    body = [b for t, b in secs if not t.lower().startswith(SUMMARY_HEADS)]
    body_lines = [x for b in body for x in _bullets(b)]
    for l in lines:
        n = len(l.split())
        if n > 30:
            out.append(f"T10 summary line of {n} words, keep at most 30: {l[:60]!r}")
        lw = words(l)
        for bl in body_lines:
            bw = words(bl)
            if lw and len(lw & bw) / len(lw) >= 0.6:
                out.append(f"T11 summary line repeats a body line: {l[:60]!r} ~ {bl[:60]!r}")
                break
    return out


def _flat_lists(md: str) -> list[str]:
    out = []
    for title, body in sections(md):
        runs: dict[tuple[int, int], int] = {}
        stack: list[tuple[int, int]] = []
        for i, l in enumerate(body.splitlines()):
            m = re.match(r"(\s*)(?:[-*]|\d+[.)])\s+\S", l)
            if not m:
                continue
            ind = len(m.group(1).expandtabs(4))
            while stack and stack[-1][0] >= ind:
                stack.pop()
            key = (ind, stack[-1][1] if stack else -1)
            runs[key] = runs.get(key, 0) + 1
            stack.append((ind, i))
        n = max(runs.values(), default=0)
        if n > 7:
            out.append(f"T12 {n} list items at one level in {title!r}: group them under at most 7 points, cut the detail Chaehan does not decide on")
    return out


def _facts(draft: str, original: str, linked: list[str] | None) -> list[str]:
    """Numbers of the original found neither in the draft, a linked note, nor the cut list."""
    pool = (draft + "\n" + "\n".join(linked or [])).replace(",", "")
    have = set(FACT.findall(pool))
    return [f"T6 fact lost: {f}" for f in sorted(set(FACT.findall(original.replace(",", ""))) - have)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--original")
    ap.add_argument("--linked", nargs="*", default=[])
    ap.add_argument("--facts-only", action="store_true", help="any note: only check that no date or number of --original is lost")
    ap.add_argument("--note", action="store_true", help="any note: facts, lists, summary size and duplicates (T5-T12)")
    ap.add_argument("--cuts", help="the cut list: one line per removal, '- <numbers or words>: <destination or reason>'")
    a = ap.parse_args(argv)
    read = lambda p: open(p, encoding="utf-8").read()
    fails = check(read(a.draft), read(a.original) if a.original else None, [read(p) for p in a.linked],
                  a.facts_only, a.note, read(a.cuts) if a.cuts else None)
    for f in fails:
        print(f)
    print("PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
