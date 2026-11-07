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
under one parent; T13 a body section that does not open with one sentence of at
most 30 words whose subject is you, your thing or an action; T15 a summary
sentence whose subject is not you or an action, or that frames ", not a X";
T16 a wording-checker flag (agentkit/scripts/wording_lint.py) outside a table
row, so one PASS covers the wording too. Japanese in parentheses after its
English name (rule 123) is not a flag here; table rows belong to T7.

--labels <file> is note_build.py's merged label file, one line per item of the
original: "id<TAB>label<TAB>parent<TAB>text", label D, S, W or K. T14 is an item
without a label, or an item labelled W (world detail) or K (known) whose text is
still in the draft. On the command line --note with --original requires --labels
and --cuts: a rewrite is a selection, and a brief cannot switch that off.

A PASS writes a stamp: an empty file named by the SHA-256 of the draft's text
with its image lines dropped and its ends stripped (stamp_key), in
$NOTE_GATE_STAMPS or ~/.local/state/agentkit/note-gate, and prints the marker
"note-gate:<sha>". The socrates Evernote CLI computes the same key and refuses a
markdown or clean body write without a stamp; the note-gate plugin refuses an
MCP whole-body write whose code does not carry a marker of a stamp under 3 hours
old. The key drops image lines because a body write never carries its images:
they are re-embedded after it.

--cuts <file> is the cut list: one line per removal, "- <numbers or words>:
<where it went or why it left>". A number of the original passes T6 when the
cut list names it. T9 is a cut line with no reason. Cutting is the point of a
rewrite: the gate checks that each cut is declared, not that nothing was cut.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

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
          facts_only: bool = False, note: bool = False, cuts: str | None = None,
          labels: str | None = None, table_titles: bool = False) -> list[str]:
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
            fails += _gists(draft)
            fails += _summary_subjects(draft)
            fails += _wording(draft)
            if table_titles:
                fails += _table_titles(draft)
            if labels is not None:
                fails += _labels(draft, labels)
            if original is not None:
                fails += _lost_rows(draft, original, cuts)
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


def _lost_rows(draft: str, original: str, cuts: str | None = None) -> list[str]:
    """A table row of the original that is in neither the draft nor the cut list."""
    have = {_row(l) for l in (draft + "\n" + (cuts or "")).splitlines() if l.lstrip().startswith("|")}
    rows = [_row(l) for l in original.splitlines() if l.lstrip().startswith("|")]
    return [f"T7 table row lost: {r}" for r in rows if r not in have and not re.fullmatch(r"[|\s:-]+", r)]


def _bad_cuts(cuts: str) -> list[str]:
    return [f"T9 cut without a reason or destination: {l.strip()!r}" for l in cuts.splitlines()
            if l.strip() and not l.lstrip().startswith("|") and not re.match(r"\s*-?\s*[^:]+:\s*\S", l)]


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


# The seat test as a check a weaker model can meet: the sentence's subject is
# you, your thing, or an action you take. A leading clause of time or condition
# ("On 2026-12-04 you fly", "If the flat costs more, take the hotel") is read
# through to the clause that carries the subject.
YOU = {"you", "your", "yours", "you're", "you'll", "chaehan", "chaehan's"}
LEAD = set("""on in at by from until till before after for between during when if once since
with without as because while unless whether although though then now so and but or also
only every each""".split())
IMPERATIVE = set("""add allow apply arrive ask avoid book bring budget buy call cancel change
charge check choose compare confirm cut decide drink drop eat expect fill fly follow get give go
hold keep land leave let look make move note open order pack pay pick plan put rest read register
remember reserve return ride save see sell send shop sign skip sleep spend start stay stop store
swim take tap tell travel try use visit wait walk wake watch wear write""".split())
# The example comes from another domain than the notes it judges: a weaker model
# copies the accepted sentence's shape into the note (2026-11-06, Osaka note).
SUBJECT_EXAMPLE = ("rejected 'The locker has a quote and a size, not a booking.', "
                   "accepted 'You must still book the Mapo locker; it costs 72090 won a month.'")


def _plain(text: str) -> str:
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[*_`]", "", text)


def _sentences(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9¥€$])", _plain(text)) if x.strip()]


def seat(sentence: str) -> bool:
    """True when the sentence's subject is you, your thing, or an imperative."""
    for clause in re.split(r"[,:;]", sentence):
        w = re.findall(r"[a-z0-9'-]+", clause.lower())
        if not w:
            continue
        if w[0] in IMPERATIVE or YOU & set(w[:2]):
            return True
        if w[0] in LEAD or re.match(r"\d", w[0]):
            if YOU & set(w[:8]):
                return True
            continue
        return False
    return False


def _gists(md: str) -> list[str]:
    out = []
    for title, body in sections(md):
        if title.lower().startswith(SUMMARY_HEADS):
            continue
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        if not lines or all(l.startswith("|") for l in lines):
            continue  # empty, or an H3 that titles one table
        first = lines[0]
        if re.match(r"(?:[-*]|\d+[.)]|\||!\[|<)", first) or not re.search(r"[a-z]{3}", _plain(first)):
            out.append(f"T13 section {title!r} must open with one sentence that tells you its point, "
                       f"before any list, table or image: {first[:50]!r}")
            continue
        sent = (_sentences(first) or [first])[0]
        if len(sent.split()) > 30:
            out.append(f"T13 section {title!r} opens with {len(sent.split())} words, keep at most 30: {sent[:50]!r}")
        elif re.search(r"\b(?:the|this) (?:section|note|table|list)\b|\bbelow (?:shows|lists|ranks|compares|prices|covers)\b", sent, re.I):
            out.append(f"T13 section {title!r} opens by talking about the note: {sent[:60]!r}; say the point itself")
        elif contrast(sent):
            out.append(f"T13 section {title!r} opens with a contrast: {sent[:60]!r}; {contrast(sent)[0]}")
        elif not seat(sent):
            out.append(f"T13 section {title!r} opens on an object, not on you: {sent[:60]!r}. Write it with you, "
                       f"your thing or an action as subject: rejected 'Osaka city has no soapland district.', "
                       f"accepted 'You will find no soapland district in Osaka city.'")
    return out


def _summary_subjects(md: str) -> list[str]:
    out = []
    summ = [b for t, b in sections(md) if t.lower().startswith(SUMMARY_HEADS)]
    if not summ:
        return out
    for line in _bullets(summ[0]):
        titles = {t.strip() for t in re.findall(r"\[([^\]]+)\]\([^)]*\)", line)}
        for sent in _sentences(line):
            if len(sent.split()) < 4 or sent.rstrip(".") in titles:
                continue
            if not seat(sent):
                out.append(f"T15 summary sentence has no you or action as subject: {sent[:70]!r}; {SUBJECT_EXAMPLE}")
            for c in contrast(sent):
                out.append(f"T15 summary sentence uses a contrast: {sent[:70]!r}; {c}")
    return out


def _table_titles(md: str) -> list[str]:
    """T17: every table carries an H3 title on the line above it (blank lines aside)."""
    lines = md.splitlines()
    out = []
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|") or (i and lines[i - 1].lstrip().startswith("|")):
            continue
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j < 0 or not lines[j].startswith("### "):
            out.append(f"T17 table without an H3 title above it: {line.strip()[:70]!r}")
    return out


def _lint():
    import importlib.util
    path = Path(__file__).resolve().parents[3] / "scripts" / "wording_lint.py"
    spec = importlib.util.spec_from_file_location("wording_lint", path)
    lint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lint)
    return lint


def contrast(sentence: str) -> list[str]:
    """The contrast frames in a sentence: the marker rows whose fix starts "contrast frame"."""
    lint = _lint()
    rules = [r for r in lint.load_robot_markers() if r[2].startswith("contrast frame")]
    return [f"{fix} ({m.group(0).strip()!r})" for _level, pat, fix, _exc in rules for m in [pat.search(sentence)] if m]


def _wording(md: str) -> list[str]:
    lint = _lint()
    lines = md.splitlines()
    table = lambda n: lines[n - 1].lstrip().startswith("|")
    out = [f"T16 line {n}: '{words_}' - {fix}" for n, level, words_, fix in lint.lint_text(md, lint.load_robot_markers())
           if level == "flag" and not table(n)]
    for n, char, line in lint.script_hits(md):
        outside = re.sub(r"\([^)]*\)", "", re.sub(r"\]\([^)]*\)", "]", lines[n - 1]))
        if not table(n) and lint.HAN.search(outside):
            out.append(f"T16 line {n}: '{char}' - Japanese or Chinese leads the name; write the English name "
                       f"first and the characters after it in parentheses (rule 123)")
    return out


def _norm(text: str) -> str:
    return " ".join(_plain(text).split()).lower()


def _labels(draft: str, labels: str) -> list[str]:
    out = []
    body = _norm(draft)
    for line in labels.splitlines():
        if not line.strip():
            continue
        cells = line.split("\t")
        while len(cells) < 4:
            cells.append("")
        item, label, _parent, text = cells[0].strip(), cells[1].strip().upper(), cells[2].strip(), cells[3]
        if label not in ("D", "S", "W", "K", "M"):
            out.append(f"T14 item {item} has no label (D decides, S supports, W world detail, K known, "
                       f"M moved to another note): {text[:50]!r}")
        elif label in ("W", "K", "M") and len(text.split()) >= 5 and _norm(text) in body:
            out.append(f"T14 item {item} is labelled {label} but is still in the draft: {text[:60]!r}")
    return out


def stamp_dir() -> Path:
    return Path(os.environ.get("NOTE_GATE_STAMPS") or Path.home() / ".local/state/agentkit/note-gate")


def stamp_key(text: str) -> str:
    """The contract with the Evernote CLI: SHA-256 of the text without image lines, ends stripped."""
    body = "\n".join(l for l in text.splitlines() if not re.fullmatch(r"\s*!\[[^\]]*\]\([^)]*\)\s*", l))
    return hashlib.sha256(body.strip().encode()).hexdigest()


def stamp(text: str) -> Path:
    """Record that this text passed the gate (the Evernote CLI and the note-gate plugin read it)."""
    d = stamp_dir()
    d.mkdir(parents=True, exist_ok=True)
    f = d / stamp_key(text)
    f.touch()
    return f


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
    ap.add_argument("--labels", help="note_build.py's merged label file: id, label, parent, text per item")
    a = ap.parse_args(argv)
    read = lambda p: open(p, encoding="utf-8").read()
    draft = read(a.draft)
    fails = check(draft, read(a.original) if a.original else None, [read(p) for p in a.linked],
                  a.facts_only, a.note, read(a.cuts) if a.cuts else None, read(a.labels) if a.labels else None)
    if a.note and a.original and not (a.labels and a.cuts):
        fails.append("T14 a rewrite needs --labels and --cuts: build it with note_build.py "
                     "(agentkit/skills/evernote/scripts), which writes both")
    for f in fails:
        print(f)
    if not fails and not a.facts_only:
        print(f"note-gate:{stamp(draft).name}")
    print("PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
