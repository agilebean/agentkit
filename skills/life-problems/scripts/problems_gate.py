"""Mechanical gate for a Life Problems map (the life-problems skill).

Each failure names the line, cell or section it rejects. Exit 1 on any failure.

    python problems_gate.py <draft.md> [--original <previous map.md> --cuts <cuts.md>]

It runs the note checks of the life-overview gate on everything above
"## Ready to use" (T5, T8, T10 to T13, T15, T16), the opening-sentence and
wording checks (T13, T16) on the instruments under it, the lost-fact check T6
against the previous map with the cut list (T9 for a cut without a reason),
and these:

P1  a heading with nothing under it before the next heading of its level
P2  "he", "his" or "him" in a note addressed to Chaehan
P3  a number with a thousand separator
P4  a required section missing or out of order
P5  a Problems row whose kind of stuck is not one of the five kinds
P6  a "What weighs on you" cell with no date, number or quotation, or with a
    label word ("anxiety", "avoidance", "bias") outside quotation marks
P7  a Quick wins row without its instrument, or without minutes
P8  a call or escalation whose script has no "- If" branch
P9  a decision not written as a dilemma: "You want" in its first sentence,
    an "- If" rule and a "- While you wait" default
P10 a Takeaway whose first bullet does not name the knot
P11 a verbatim block under "## Ready to use": the drafts are the writer's own
    text, and verbatim markers would hide them from the wording checks
P12 a social security number written out; write its last four digits
P13 a problem of the previous map that is neither in the new map nor in the
    cut list (only with --original)
P14 a Takeaway line that is not a bullet

A PASS writes the note-gate stamp of the life-overview gate and prints its
marker "note-gate:<sha>", which the Evernote write path requires.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path


def _overview_gate():
    path = Path(__file__).resolve().parents[2] / "life-overview" / "scripts" / "overview_gate.py"
    spec = importlib.util.spec_from_file_location("overview_gate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _overview_gate()

REQUIRED = ("takeaway", "the knot", "what you can put down", "quick wins", "decisions",
            "problems", "ready to use")
KINDS = ("deadline", "one missing fact", "waits on another decision", "someone else's move", "settled")
LABEL_WORDS = re.compile(
    r"\b(?:anxiety|anxious|avoidance|avoidant|procrastinat\w*|bias(?:es|ed)?|fear\w*|"
    r"paralysis|pattern\w*|tendency|tendencies|trait\w*|perfectionis\w*|binary framing)\b", re.I)
PRONOUN = re.compile(r"\b(?:he|his|him|himself)\b", re.I)
THOUSANDS = re.compile(r"(?<![\d.,])\d{1,3}(?:,\d{3})+(?!\d|,\d)")
LINK = re.compile(r"https?://|evernote:///")
QUOTE = re.compile(r"\"[^\"]+\"|“[^”]+”|'[^']{3,}'")
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
VERBATIM = re.compile(r"<!--\s*verbatim\s*-->", re.I)
IF_BULLET = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+If\b", re.M)
WAIT_BULLET = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+While you wait\b", re.M | re.I)


def _own_lines(md: str):
    """(line number, line) for the writer's own text: no verbatim excerpt, no inline code, no URL."""
    inside = False
    for n, line in enumerate(md.splitlines(), 1):
        if re.match(r"^\s*<!--\s*verbatim\s*-->\s*$", line):
            inside = True
            continue
        if re.match(r"^\s*<!--\s*end verbatim\s*-->\s*$", line):
            inside = False
            continue
        if not inside:
            yield n, re.sub(r"\]\([^)]*\)|`[^`]*`|https?://\S+", "]", line)


def split_ready(md: str) -> tuple[str, str]:
    """The note above "## Ready to use", and the instruments from that heading on."""
    m = re.search(r"^## Ready to use\b.*$", md, re.M | re.I)
    return (md, "") if not m else (md[:m.start()], md[m.start():])


def h2_sections(md: str) -> list[tuple[str, str]]:
    """The ## sections with their whole body, ### subsections included."""
    out, title, buf = [], None, []
    for line in md.splitlines():
        m = re.match(r"##\s+(.*)", line)
        if m and not line.startswith("###"):
            if title is not None:
                out.append((title, "\n".join(buf)))
            title, buf = m.group(1).strip(), []
        elif title is not None:
            buf.append(line)
    if title is not None:
        out.append((title, "\n".join(buf)))
    return out


def h3_sections(body: str) -> list[tuple[str, str]]:
    out, title, buf = [], None, []
    for line in body.splitlines():
        m = re.match(r"###\s+(.*)", line)
        if m:
            if title is not None:
                out.append((title, "\n".join(buf)))
            title, buf = m.group(1).strip(), []
        elif title is not None:
            buf.append(line)
    if title is not None:
        out.append((title, "\n".join(buf)))
    return out


def section(md: str, name: str) -> str | None:
    for title, body in h2_sections(md):
        if title.lower().startswith(name):
            return body
    return None


def table(body: str | None) -> tuple[list[str], list[list[str]]]:
    rows = [l.strip() for l in (body or "").splitlines() if l.strip().startswith("|")]
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
    cells = [c for c in cells if not all(re.fullmatch(r":?-+:?", x) for x in c if x)]
    return ([h.lower() for h in cells[0]], cells[1:]) if cells else ([], [])


def col(header: list[str], name: str) -> int | None:
    for i, h in enumerate(header):
        if name in gate._plain(h).lower():
            return i
    return None


def _empty_headings(md: str) -> list[str]:
    lines = md.splitlines()
    out = []
    for i, line in enumerate(lines):
        m = re.match(r"(#{1,6})\s+(.*)", line)
        if not m:
            continue
        level = len(m.group(1))
        nxt = next((l for l in lines[i + 1:] if l.strip()), None)
        n = re.match(r"(#{1,6})\s", nxt or "")
        if nxt is None or (n and len(n.group(1)) <= level):
            out.append(f"P1 empty heading at line {i + 1}: {m.group(2)!r}; fill it or delete it")
    return out


def _pronouns(md: str) -> list[str]:
    return [f"P2 line {n}: {m.group(0)!r} - the note is addressed to you: write \"you\", or the other person's name"
            for n, l in _own_lines(md) for m in PRONOUN.finditer(l)]


def _thousands(md: str) -> list[str]:
    return [f"P3 line {n}: {m.group(0)!r} - write numbers without thousand separators ({m.group(0).replace(',', '')})"
            for n, l in _own_lines(md) for m in THOUSANDS.finditer(l)]


def _required(md: str) -> list[str]:
    titles = [t.lower() for t, _ in h2_sections(md)]
    pos = []
    out = []
    for name in REQUIRED:
        hit = next((i for i, t in enumerate(titles) if t.startswith(name)), None)
        if hit is None:
            out.append(f"P4 section missing: '## {name.capitalize()}'")
        else:
            pos.append((hit, name))
    if [n for _, n in sorted(pos)] != [n for _, n in pos]:
        out.append("P4 sections out of order; the order is " + ", ".join(REQUIRED))
    return out


def _problems(md: str) -> list[str]:
    header, rows = table(section(md, "problems"))
    if not header:
        return ["P5 the Problems section has no table"]
    out = []
    kind, weigh = col(header, "kind of stuck"), col(header, "what weighs on you")
    if kind is None:
        out.append("P5 the Problems table has no 'Kind of stuck' column")
    if weigh is None:
        out.append("P6 the Problems table has no 'What weighs on you' column")
    for r in rows:
        name = gate._plain(r[0])[:40] if r else "?"
        if kind is not None:
            value = gate._plain(r[kind] if kind < len(r) else "").lower().strip()
            if not value.startswith(KINDS):
                out.append(f"P5 row {name!r}: kind of stuck {value!r} is not one of: " + ", ".join(KINDS))
        if weigh is not None:
            cell = gate._plain(r[weigh] if weigh < len(r) else "").strip()
            if not cell:
                out.append(f"P6 row {name!r}: 'What weighs on you' is empty")
                continue
            if not re.search(r"\d", cell) and not QUOTE.search(cell):
                out.append(f"P6 row {name!r}: {cell[:50]!r} names no date, number or quotation; "
                           f"build it from a fact on record or from your quoted words")
            bare = QUOTE.sub("", cell)
            m = LABEL_WORDS.search(bare)
            if m:
                out.append(f"P6 row {name!r}: {m.group(0)!r} labels your inner state; say the fact that "
                           f"makes it heavy, or quote your own words")
    return out


def _quick_wins(main: str, ready: str) -> list[str]:
    header, rows = table(section(main, "quick wins"))
    if not header:
        return ["P7 the Quick wins section has no table"]
    tool, effort = col(header, "ready to use"), col(header, "effort")
    if tool is None or effort is None:
        return ["P7 the Quick wins table needs an 'Effort' and a 'Ready to use' column"]
    subs = {gate._plain(t).lower().strip(): b for t, b in h3_sections(ready)}
    out = []
    for r in rows:
        name = gate._plain(r[0])[:40] if r else "?"
        cell = r[tool] if tool < len(r) else ""
        cost = gate._plain(r[effort] if effort < len(r) else "").lower()
        key = re.sub(r"^(?:see\s+)?|\s*(?:,?\s*below)\.?$", "", gate._plain(cell).lower().strip())
        sub = subs.get(key)
        if not re.search(r"\d+\s*min", cost):
            out.append(f"P7 row {name!r}: Effort {cost!r} gives no minutes; write '10 min' or '10 min, call'")
        if not LINK.search(cell) and sub is None:
            out.append(f"P7 row {name!r}: Ready to use {gate._plain(cell)[:40]!r} is neither a link nor the "
                       f"title of a '###' under '## Ready to use'")
            continue
        if re.search(r"\b(?:call|escalation)\b", cost) and (sub is None or not IF_BULLET.search(sub)):
            out.append(f"P8 row {name!r} is a {'call' if 'call' in cost else 'escalation'}: its script under "
                       f"'## Ready to use' needs one '- If ...' bullet per answer you can get")
    return out


def _dilemmas(main: str) -> list[str]:
    body = section(main, "decisions")
    if body is None:
        return []
    out = []
    subs = h3_sections(body)
    if not subs:
        out.append("P9 the Decisions section has no '###' decision")
    for title, sub in subs:
        lines = [l.strip() for l in sub.splitlines() if l.strip()]
        first = (gate._sentences(lines[0]) or [""])[0] if lines else ""
        if "you want" not in first.lower():
            out.append(f"P9 decision {title!r} opens without the dilemma: write 'You want A and B, and C makes "
                       f"you choose.' ({first[:50]!r})")
        if not IF_BULLET.search(sub):
            out.append(f"P9 decision {title!r} has no '- If ...' bullet with the rule that settles it")
        if not WAIT_BULLET.search(sub):
            out.append(f"P9 decision {title!r} has no '- While you wait ...' bullet with the default you can undo")
    return out


def _knot_first(main: str) -> list[str]:
    bullets = gate._bullets(section(main, "takeaway") or "")
    knot = [l.strip() for l in (section(main, "the knot") or "").splitlines() if l.strip()]
    if not bullets or not knot:
        return []
    shared = gate.words(bullets[0]) & gate.words(knot[0])
    if len(shared) < 2:
        return [f"P10 the first Takeaway bullet does not name the knot: {bullets[0][:60]!r} shares no words "
                f"with {knot[0][:60]!r}"]
    return []


def _own_drafts(ready: str) -> list[str]:
    if VERBATIM.search(ready):
        return ["P11 a verbatim block under '## Ready to use': your drafts are your own text, so they are "
                "checked like the rest; keep verbatim markers for another author's words"]
    return []


def _identifiers(md: str) -> list[str]:
    return [f"P12 line {n}: a social security number is written out; write 'SSN ending {m.group(0)[-4:]}', "
            f"and the full number goes in when you send" for n, l in enumerate(md.splitlines(), 1)
            for m in SSN.finditer(l)]


def previous_problems(original: str) -> list[str]:
    """The previous map's problems: its Problems table's first column, else its ### headings."""
    _, rows = table(section(original, "problems"))
    if rows:
        return [gate._plain(r[0]).strip() for r in rows if r and r[0].strip()]
    names = []
    for line in original.splitlines():
        m = re.match(r"###\s+(?:\d+[.)]\s*)?(.*)", line)
        if m and m.group(1).strip():
            names.append(gate._plain(m.group(1)).strip())
    return names


def _dropped(draft: str, original: str, cuts: str | None) -> list[str]:
    pool = (gate._plain(draft) + "\n" + (cuts or "")).lower()
    return [f"P13 problem {name!r} of the previous map is gone: give it a row (settled, if done) or a cut "
            f"line '- {name}: <why it left>'" for name in previous_problems(original) if name.lower() not in pool]


def _takeaway_bullets_only(main: str) -> list[str]:
    body = section(main, "takeaway") or ""
    return [f"P14 Takeaway line is not a bullet: {l.strip()[:60]!r}; make it a bullet or cut it"
            for l in body.splitlines() if l.strip() and not re.match(r"\s*(?:[-*]|\d+[.)])\s", l)]


def check(draft: str, original: str | None = None, cuts: str | None = None) -> list[str]:
    main, ready = split_ready(draft)
    fails = gate.check(main, note=True)
    if ready:
        fails += gate._gists(ready) + gate._wording(ready)
    fails += _empty_headings(draft) + _pronouns(draft) + _thousands(draft) + _required(draft)
    fails += _problems(main) + _quick_wins(main, ready) + _dilemmas(main) + _knot_first(main)
    fails += _own_drafts(ready) + _identifiers(draft) + _takeaway_bullets_only(main)
    if original is not None:
        if cuts is None:
            fails.append("T6 a map built on a previous one needs --cuts: one line per number it drops, with the reason")
        else:
            fails += gate._bad_cuts(cuts)
        fails += gate._facts(draft, original, [cuts] if cuts else [])
        fails += _dropped(draft, original, cuts)
    return fails


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("--original", help="the previous Life Problems map, as markdown")
    ap.add_argument("--cuts", help="the cut list: '- <numbers>: <where it went or why it left>' per line")
    a = ap.parse_args(argv)
    read = lambda p: open(p, encoding="utf-8").read()
    draft = read(a.draft)
    fails = check(draft, read(a.original) if a.original else None, read(a.cuts) if a.cuts else None)
    for f in fails:
        print(f)
    if not fails:
        try:
            print(f"note-gate:{gate.stamp(draft).name}")
        except OSError as e:
            print(f"PASS, but the stamp was not written ({e}); the Evernote write will refuse this text "
                  f"until the gate runs where {gate.stamp_dir()} is writable")
            return 2
    print("PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
