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
list item. It also prints the words of the original that left (not a failure:
each is accounted for in the report).
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
          facts_only: bool = False, note: bool = False) -> list[str]:
    fails: list[str] = []
    if facts_only or note:
        if note:
            fails += _prose_sections(draft)
            fails += _empty_items(draft)
            if original is not None:
                fails += _lost_rows(draft, original)
        return fails + (_facts(draft, original, linked) if original is not None else [])
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


def lost_words(draft: str, original: str) -> list[str]:
    """Words of six letters or more that the original had and the draft lost.
    Rewording drops some; the rest are facts that left. Each is accounted for."""
    words = lambda x: {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z-]{5,}", x)}
    return sorted(words(original) - words(draft))


def _facts(draft: str, original: str, linked: list[str] | None) -> list[str]:
    pool = (draft + "\n" + "\n".join(linked or [])).replace(",", "")
    have = set(FACT.findall(pool))
    return [f"T6 fact lost: {f}" for f in sorted(set(FACT.findall(original.replace(",", ""))) - have)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--original")
    ap.add_argument("--linked", nargs="*", default=[])
    ap.add_argument("--facts-only", action="store_true", help="any note: only check that no date or number of --original is lost")
    ap.add_argument("--note", action="store_true", help="any note: the fact check plus no section written as prose of 3 or more sentences")
    a = ap.parse_args(argv)
    read = lambda p: open(p, encoding="utf-8").read()
    fails = check(read(a.draft), read(a.original) if a.original else None, [read(p) for p in a.linked], a.facts_only, a.note)
    for f in fails:
        print(f)
    if a.note and a.original:
        gone = lost_words(read(a.draft), read(a.original))
        if gone:
            print("CHECK words gone (each: the fact is still in the note, or it left on purpose): " + ", ".join(gone))
    print("PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
