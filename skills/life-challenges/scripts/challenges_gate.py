"""Mechanical gate for a Life Challenges note (the life-challenges skill).

Each failure names the line, cell or section it rejects. Exit 1 on any failure.

    python challenges_gate.py <draft.md> [--original <previous note.md> --cuts <cuts.md>]

It runs the note checks of the life-overview gate (T5, T8, T10 to T13, T15,
T16), the lost-fact check T6 against the previous note with the cut list (T9
for a cut without a reason), and these:

C1  a heading with nothing under it before the next heading of its level
C2  "he", "his" or "him" in a note addressed to Chaehan
C3  a number with a thousand separator
C4  Takeaway not first, no goal section between it and Hand to me, Hand to
    me missing, or a section after Settled
C5  a decision bullet (ending with "?") without two to four options indented
    under it, or a label word ("anxiety", "avoidance", "bias") outside
    quotation marks in a goal section
C6  a Hand to me row with an empty cell, a command that is not "/life
    <keyword>", a keyword used twice, or a draft under the table
C7  a Takeaway line that is not a bullet, or more than three bullets
C8  a social security number written out; write its last four digits
C9  an issue of the previous note that is neither in this note nor in the cut
    list (only with --original)

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

FIXED = ("takeaway", "hand to me", "settled")
LABEL_WORDS = re.compile(
    r"\b(?:anxiety|anxious|avoidance|avoidant|procrastinat\w*|bias(?:es|ed)?|fear\w*|"
    r"paralysis|pattern\w*|tendency|tendencies|trait\w*|perfectionis\w*|binary framing)\b", re.I)
PRONOUN = re.compile(r"\b(?:he|his|him|himself)\b", re.I)
THOUSANDS = re.compile(r"(?<![\d.,])\d{1,3}(?:,\d{3})+(?!\d|,\d)")
QUOTE = re.compile(r"\"[^\"]+\"|“[^”]+”|'[^']{3,}'")
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
COMMAND = re.compile(r"^`?/life ([a-z0-9-]+)`?$")
BULLET = re.compile(r"^\s*[-*]\s+\S", re.M)


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
    return ([gate._plain(h).lower() for h in cells[0]], cells[1:]) if cells else ([], [])


def _lines(body: str) -> list[str]:
    return [l.strip() for l in body.splitlines() if l.strip()]


def _empty_headings(md: str) -> list[str]:
    lines = md.splitlines()
    out = []
    for i, line in enumerate(lines):
        m = re.match(r"(#{1,6})\s+(.*)", line)
        if not m:
            continue
        nxt = next((l for l in lines[i + 1:] if l.strip()), None)
        n = re.match(r"(#{1,6})\s", nxt or "")
        if nxt is None or (n and len(n.group(1)) <= len(m.group(1))):
            out.append(f"C1 empty heading at line {i + 1}: {m.group(2)!r}; fill it or delete it")
    return out


def _pronouns(md: str) -> list[str]:
    return [f"C2 line {n}: {m.group(0)!r} - the note is addressed to you: write \"you\", or the other person's name"
            for n, l in _own_lines(md) for m in PRONOUN.finditer(l)]


def _thousands(md: str) -> list[str]:
    return [f"C3 line {n}: {m.group(0)!r} - write numbers without thousand separators ({m.group(0).replace(',', '')})"
            for n, l in _own_lines(md) for m in THOUSANDS.finditer(l)]


def _sections(md: str) -> list[str]:
    titles = [t.lower() for t, _ in h2_sections(md)]
    out = []
    if not titles or not titles[0].startswith("takeaway"):
        out.append("C4 the note must open with '## Takeaway'")
    hand = next((i for i, t in enumerate(titles) if t.startswith("hand to me")), None)
    if hand is None:
        out.append("C4 section missing: '## Hand to me'")
    elif not any(not t.startswith(FIXED) for t in titles[1:hand]):
        out.append("C4 no goal section between Takeaway and Hand to me: write one per live goal")
    settled = next((i for i, t in enumerate(titles) if t.startswith("settled")), None)
    if settled is not None and settled != len(titles) - 1:
        out.append("C4 '## Settled' must be the last section")
    if hand is not None and settled is not None and settled < hand:
        out.append("C4 '## Settled' comes after '## Hand to me'")
    return out


def _goal_sections(md: str) -> list[tuple[str, str]]:
    return [(t, b) for t, b in h2_sections(md) if not t.lower().startswith(FIXED)]


def _decisions(md: str) -> list[str]:
    out = []
    for title, body in _goal_sections(md):
        lines = body.splitlines()
        for i, line in enumerate(lines):
            m = re.match(r"(\s*)[-*]\s+(.*\?)\s*$", line)
            if not m:
                continue
            ind = len(m.group(1).expandtabs(4))
            subs = 0
            for nxt in lines[i + 1:]:
                if not nxt.strip():
                    continue
                n = re.match(r"(\s*)[-*]\s+\S", nxt)
                if not n or len(n.group(1).expandtabs(4)) <= ind:
                    break
                if len(n.group(1).expandtabs(4)) > ind and len(n.group(1).expandtabs(4)) <= ind + 4:
                    subs += 1
            if not 2 <= subs <= 4:
                out.append(f"C5 decision in {title!r} has {subs} options under it; give two to four, "
                           f"each a clickable answer: {gate._plain(m.group(2))[:60]!r}")
        hit = LABEL_WORDS.search(QUOTE.sub("", gate._plain(body)))
        if hit:
            out.append(f"C5 {title!r}: {hit.group(0)!r} labels your inner state; say the fact that "
                       f"makes it heavy, or quote your own words")
    return out


def _hand_to_me(md: str) -> list[str]:
    body = section(md, "hand to me")
    if body is None:
        return []
    out = []
    if re.search(r"^###\s", body, re.M):
        out.append("C6 a '###' under '## Hand to me': drafts and scripts are made by /life on demand, "
                   "never kept in the note")
    header, rows = table(body)
    want = ("issue", "i do", "you decide", "command")
    if [h.strip() for h in header] != list(want):
        return out + ["C6 the Hand to me table needs exactly the columns: Issue | I do | You decide | Command"]
    seen = {}
    for r in rows:
        name = gate._plain(r[0])[:40] if r else "?"
        if len(r) < 4 or not all(gate._plain(c).strip() for c in r[:4]):
            out.append(f"C6 row {name!r} has an empty cell")
            continue
        m = COMMAND.match(r[3].strip())
        if not m:
            out.append(f"C6 row {name!r}: command {r[3].strip()!r} is not '/life <keyword>'")
            continue
        if m.group(1) in seen:
            out.append(f"C6 keyword {m.group(1)!r} is used by {seen[m.group(1)]!r} and {name!r}; make each unique")
        seen[m.group(1)] = name
    return out


def _takeaway(md: str) -> list[str]:
    body = section(md, "takeaway") or ""
    out = [f"C7 Takeaway line is not a bullet: {l[:60]!r}" for l in _lines(body) if not BULLET.match(l)]
    n = len(BULLET.findall(body))
    if n > 3:
        out.append(f"C7 Takeaway has {n} bullets; keep at most three")
    return out


def _identifiers(md: str) -> list[str]:
    return [f"C8 line {n}: a social security number is written out; write 'SSN ending {m.group(0)[-4:]}'"
            for n, l in enumerate(md.splitlines(), 1) for m in SSN.finditer(l)]


def previous_issues(original: str) -> list[str]:
    """The previous note's issues, whichever format it has."""
    names = []
    for name in ("your decisions",):
        names += [gate._plain(t).strip() for t, _ in h3_sections(section(original, name) or "")]
    for name in ("hand to me", "problems"):
        _, rows = table(section(original, name))
        names += [gate._plain(r[0]).strip() for r in rows if r and r[0].strip()]
    if not names:
        for line in original.splitlines():
            m = re.match(r"###\s+(?:\d+[.)]\s*)?(.*)", line)
            if m and m.group(1).strip():
                names.append(gate._plain(m.group(1)).strip())
    return names


def _dropped(draft: str, original: str, cuts: str | None) -> list[str]:
    pool = (gate._plain(draft) + "\n" + (cuts or "")).lower()
    return [f"C9 issue {name!r} of the previous note is gone: give it a place here, or a cut line "
            f"'- {name}: <why it left>'" for name in previous_issues(original) if name.lower() not in pool]


def check(draft: str, original: str | None = None, cuts: str | None = None) -> list[str]:
    fails = gate.check(draft, note=True)
    fails += _empty_headings(draft) + _pronouns(draft) + _thousands(draft) + _sections(draft)
    fails += _decisions(draft) + _hand_to_me(draft) + _takeaway(draft) + _identifiers(draft)
    if original is not None:
        if cuts is None:
            fails.append("T6 a note built on a previous one needs --cuts: one line per number it drops, with the reason")
        else:
            fails += gate._bad_cuts(cuts)
        fails += gate._facts(draft, original, [cuts] if cuts else [])
        fails += _dropped(draft, original, cuts)
    return fails


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("--original", help="the previous note, as markdown")
    ap.add_argument("--cuts", help="the cut list: '- <numbers or issue>: <where it went or why it left>' per line")
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
