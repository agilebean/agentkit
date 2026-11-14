"""Build an Evernote note from Chaehan's decisions, in steps a weaker model can do.

A whole-note rewrite asks for one judgment over every sentence at once, and a
weaker model answers it by translating sentence for sentence (failures 163 and
164 in socrates memory/agentic_ai.md). This script splits that judgment into
tasks done one item at a time, and does the rest itself:

1. the model lists the decisions Chaehan makes with the note (decisions.md);
2. the model labels every item of the old text, one by one (labels.tsv);
3. the model writes only the new sentences: a heading, a summary line and a
   first line per decision (new.tsv), each checked as it is written.

The script then assembles the note. Items labelled world detail or known go to
the cut list, so the cutting is done here. Each decision becomes a section that
opens with its first line, so every section states its point. Supporting items
are indented under the item they support, so the hierarchy comes from the
labels. The note gate checks the result, and its PASS stamps the exact text the
write may send.

Evernote is read and written through the Evernote MCP only. `init --guid`,
`link` and `write` print JavaScript for one execute call in opencode, and a
local bridge hands that call its data and checks what comes back.

    python3 note_build.py init <dir> (--guid <guid> | <old.md> --title <title> --notebook <name>)
    python3 note_build.py next <dir>
    python3 note_build.py link "<words>"
    python3 note_build.py write <dir>

`next` always prints the one step that is due, or what to fix in it.

`init --as-is <file>` takes a text written elsewhere (by Claude in Claude Code, or by Chaehan) as the note:
no selection steps, only the gate. `next` reruns the gate after an edit of draft.md, and `write` writes it.
Image lines at the top of a draft that point at files on this Mac (`![name](</path/with spaces.jpg>)`) are
uploaded by `write` through the MCP and put above the text, in the same execute call.

`init --dest hanji` builds a new note for Hanji: `write` then creates it with the
hanji skill's hanji_note.py, reads it back and verifies it, with no execute
call. The default destination is Evernote.

A note whose Summary is not one line per section writes its Summary lines into
`summary.md` in the build folder, one to three bullets, each checked like a
summary line; new.tsv's summary cells are then "-". The life-challenges skill's
topic note uses it: its big picture, then the question that decides it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
GATE_PATH = HERE.parents[2] / "life-overview" / "scripts" / "overview_gate.py"
import os
import subprocess

SOCRATES = Path(os.environ.get("NOTE_BUILD_SOCRATES") or Path.home() / "Software" / "Prototypes" / "socrates")
HANJI_NOTE = HERE.parents[2] / "hanji" / "scripts" / "hanji_note.py"
DESTS = ("evernote", "hanji")
LABELS = ("D", "S", "W", "K", "M")
LINK = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
NUMBER = re.compile(r"\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?")
SUMMARY_HEADS = ("summary", "takeaway", "tl;dr")
# The heading under which init --new puts facts the note does not hold yet (a finding, a test result).
NEW_HEAD = "New facts"
# At most this many supporting items hang under one item: the life overview's "at most three" (Move 2).
MAX_KIDS = 3
# A sentence about the note instead of about you: copied from the instruction's
# own words in the first deepseek run ("the section below ranks ...").
META = re.compile(r"\b(?:the|this) (?:section|note|table|list)\b|\bbelow (?:shows|lists|ranks|compares|prices|covers)\b",
                  re.I)


def old_summary(item: dict) -> bool:
    """An item of the old note's summary: the new summary replaces it, so the script cuts it."""
    return item["section"].lower().startswith(SUMMARY_HEADS)


def effective(items: list[dict], rows: list[list[str]]) -> list[list[str]]:
    """The model's labels with the old summary's items set to K."""
    summary = {it["id"] for it in items if old_summary(it)}
    out = [r for r in rows if r and r[0] not in summary]
    return out + [[i, "K", ""] for i in sorted(summary, key=int)]


def gate():
    spec = importlib.util.spec_from_file_location("overview_gate", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sentences(text: str) -> list[str]:
    """Split a line into sentences without cutting inside a markdown link."""
    links: list[str] = []

    def hide(m: re.Match) -> str:
        links.append(m.group(0))
        return f"\x00{len(links) - 1}\x00"

    hidden = LINK.sub(hide, text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9¥€$(\x00])", hidden)
    back = lambda s: re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], s)
    return [back(p).strip() for p in parts if p.strip()]


def split_items(md: str) -> tuple[list[dict], list[str]]:
    """Items of the old text (sentences, tables, images) and its old headings."""
    items: list[dict] = []
    headings: list[str] = []
    lines = md.splitlines()
    section = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        h = re.match(r"#{1,6}\s+(.*)", line)
        if h:
            section = h.group(1).strip()
            headings.append(section)
            i += 1
            continue
        if line.lstrip().startswith("|"):
            start = i
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                i += 1
            items.append({"kind": "table", "line": start + 1, "section": section,
                          "text": "\n".join(lines[start:i])})
            continue
        if re.match(r"\s*(?:!\[|<img|<en-media)", line):
            items.append({"kind": "image", "line": i + 1, "section": section, "text": line.strip()})
            i += 1
            continue
        for s in sentences(MARKER.sub("", line).strip()):
            items.append({"kind": "sentence", "line": i + 1, "section": section, "text": s})
        i += 1
    for n, item in enumerate(items, 1):
        item["id"] = str(n)
    return items, headings


def one_line(item: dict) -> str:
    if item["kind"] == "table":
        return "TABLE " + " ".join(item["text"].splitlines()[0].split())
    return item["text"]


# ---- files ------------------------------------------------------------------

def tsv(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            rows.append([c.strip() for c in line.split("\t")])
    return rows


def decisions(d: Path) -> dict[str, str]:
    p = d / "decisions.md"
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-?\s*(D\d+)\s*:\s*(.+)", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def section_map(d: Path) -> dict[str, str]:
    """decisions.md's lines "<old heading> -> D2", "-> ask" or "-> drop (Chaehan, <date>)"."""
    p = d / "decisions.md"
    out = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*-?\s*(.+?)\s*->\s*(.+)", line)
            if m and not re.match(r"D\d+\s*:", m.group(1)):
                out[m.group(1).strip()] = m.group(2).strip()
    return out


def source_text(d: Path) -> str:
    """The old note and Chaehan's record of the topic: what a new sentence may draw on."""
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    parts = [(d / "original.md").read_text(encoding="utf-8")]
    parts += [Path(r).read_text(encoding="utf-8") for r in meta.get("record") or [] if Path(r).exists()]
    # Chaehan's words from the brief, and research with a source URL per fact.
    parts += [(d / f).read_text(encoding="utf-8") for f in ("chaehan.md", "found.md") if (d / f).exists()]
    return "\n".join(parts)


EVERNOTE_LINK = re.compile(r"\[([^\]]+)\]\((evernote:///view/[^)\s]+)\)")
LINK_FORM = "evernote:///view/39d2f74/s365/{g}/{g}/"
GUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
APPROX = re.compile(r"\b(?:about|around|roughly|approximately)\s+(?=[~¥€$]?\d)", re.I)
SEPARATOR = re.compile(r"\d{1,3}(?:,\d{3})+\b")


def note_title(guid: str, d: Path) -> str:
    """The exact title of a linked note, as the last write fetched it through the MCP ("?" when not fetched yet)."""
    cache_p = d / "links.json"
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    return cache.get(guid, "?")


def bad_links(text: str, d: Path) -> list[str]:
    """Evernote links whose guid is no note, or whose text is not that note's exact title."""
    out = []
    for name, url in EVERNOTE_LINK.findall(text):
        m = GUID.search(url)
        if not m or url != LINK_FORM.format(g=m.group(0)):
            out.append(f"link {name!r} has the wrong form: write [<exact title>]({LINK_FORM.format(g='<guid>')})")
            continue
        title = note_title(m.group(0), d)
        if not title:
            out.append(f"link {name!r} points at no note (guid {m.group(0)}): find it with: python3 {HERE} link <words>")
        elif title != "?" and title != name:
            out.append(f"link {name!r} must carry the note's exact title: {title!r}")
    return out


def new_text_errors(label: str, s: str, source: str) -> list[str]:
    """Checks on any text the model writes: copies, inventions, separators, approximate numbers."""
    out = []
    if copied(s):
        out.append(f"{label} copies the instructions' example: write it from this note")
    bad = invented(s, source) if source else []
    if bad:
        out.append(f"{label} has {', '.join(bad)}, which is not in the note, the record, chaehan.md or found.md")
    if s[:1].islower():
        out.append(f"{label} starts with a small letter: write a whole sentence of your own, not a pasted phrase")
    for m in SEPARATOR.finditer(s):
        out.append(f"{label} writes {m.group(0)!r} with a thousand separator: write the number without it (¥208333)")
    for m in APPROX.finditer(s):
        out.append(f"{label} writes {m.group(0).strip()!r} before a number: write ~N (~65 minutes)")
    return out


def _shingles(text: str, n: int = 6) -> set[tuple]:
    w = re.findall(r"[a-z0-9¥€$']+", text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def copied(sentence: str) -> bool:
    """True when the sentence repeats six words in a row of this script's own instructions."""
    own = _shingles(STEP1 + STEP2 + STEP3 + STEP4)
    return bool(_shingles(sentence) & own)


NOT_NAMES = {"You", "Your", "I", "On", "In", "At", "By", "From", "If", "When", "Before", "After", "Take", "Book",
             "Buy", "Skip", "Reserve", "Leave", "Use", "Keep", "Search", "Do", "Which", "Where", "What", "How",
             "Is", "Are", "Should", "Can", "Will", "The", "A", "An", "Then", "And", "But", "Or"}


NUMBER_WORDS = set("""one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen
twenty thirty forty fifty hundred first second third fourth fifth half""".split())


def invented(sentence: str, source: str) -> list[str]:
    """Numbers and names in a new sentence that neither the note nor Chaehan's record contains."""
    src = source.replace(",", "")
    have = set(NUMBER.findall(src))
    # A link to another note is checked against that note by bad_links; a link target is no fact.
    plain = re.sub(r"\[[^\]]*\]\(evernote:[^)]*\)", "", sentence)
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", plain)
    out = [n for n in NUMBER.findall(plain.replace(",", "")) if n not in have]
    names = re.findall(r"\b[A-Z][A-Za-z-]{2,}\b", plain)
    verbs = getattr(gate(), "IMPERATIVE", set())  # "Eat Kobe beef ..." opens on a verb, not a name
    words = NUMBER_WORDS  # "Six swims ..." opens on a number, not a name
    out += [n for n in names if n not in NOT_NAMES and n.lower() not in verbs | words and n not in source]
    return out


# ---- steps ------------------------------------------------------------------

STEP1 = """Step 1 of 4: decisions, and where each old section goes.

Every note is written in the life overview's style. Read its section
"3. Write the snapshot" in ~/Software/Prototypes/agentkit/skills/life-overview/SKILL.md:
Moves 1 to 3 and the accepted and rejected lines. The Takeaway's life order,
the Life Challenges link and its gate belong to the overview alone.

Read the whole old note, {d}/original.md, and Chaehan's record of the topic:
{record}

Write {d}/decisions.md in two parts. If the brief gave Chaehan's decisions,
they are there already: keep them and add the second part.

First part: one line per decision Chaehan makes with this note, at most five,
as "D1: <what you decide>". A decision is something you will do or choose, and
it names places, dates and numbers from the note or the record. List the
decisions in the order he acts on them, the highest priority first: the
sections come out in that order, and a brief may fix the order for its format.
Take the
decisions from the record and from the note's sections, never from the old
note's summary alone: an old summary drops what its writer thought minor.
A question that Chaehan's own observations have settled (what he felt,
measured or tested) is written as settled: the decision is what he does with
the answer, and the candidates his observations ruled out leave the note.
Lines Chaehan wrote out for a section are that section, as he wrote them:
his first sentence becomes its first line in step 3, each of his bullets is
an item labelled D, each indented bullet an S under the bullet above it, and
nothing else is added to it. They reach the build as items through init's
--new file.

Second part: one line for every heading of the old note, as
"<heading exactly as written> -> D<n>". Every section Chaehan has in his note
is there because he asked for it. A section that serves none of your decisions
gets "<heading> -> ask": the script then stops, and you ask Chaehan with the
question tool whether it leaves his note. The "New facts" heading, which
init --new adds, needs no line: its items are labelled one by one in step 2. Write his answer back as
"<heading> -> D<n>", or as "<heading> -> drop (Chaehan, <date>)" only when he
said yes. The old Summary needs no line.

  The form, from another note:
  D2: Do you renew the Mapo storage locker for another month at 72090 won?
  Storage options -> D2

Then run: python3 {me} next {d}
"""

STEP2 = """Step 2 of 4: labels.

{d}/items.tsv lists the {n} items of the old note, one per line: id, line, text.
Write {d}/labels.tsv with one line per item: id<TAB>label<TAB>parent.
Label each item on its own, by what it does for one of the decisions in
decisions.md:

  D  decides: it changes a decision. Parent: that decision, D1 to D{k}.
     At most three per decision: the three whose deletion would change most
     what Chaehan does.
  S  supports: a fact that would change the kept item above it if it were
     different. Parent: that item's id. A detail can hang on another detail.
     At most three hang under one item: keep the three that change it most.
     Only a detail that passes the deletion test below may be folded into
     its parent's wording as a parenthesis (edits.tsv, the detail labelled
     K); a detail that fails the test is cut, never folded. A sentence
     Chaehan called clutter leaves the note, whole or as a clause. How a test, a drug or a study works is W unless a
     decision changes with it.
  W  world detail: true, but you will not act on it. Market statistics, a
     second source saying the same, a price of something you will not buy, a
     place ruled out for a reason you do not need, an option kept only for
     comparison, and a side trip the decisions do not need. No parent.
  K  known: you know it already, or the note says it again elsewhere, like an
     old summary line that repeats the body. No parent.
  M  moved: it now lives in another note. Parent: that note's exact title.

Where a decision asks how two things connect (a cause, an earlier episode
and this one) and no line of the record, chaehan.md or found.md states the
link, one sentence says the link is open and names the possibilities, and
nothing fills the gap: a connection the record does not state is an
invention, however plausible. Write that sentence as an item's new wording
in edits.tsv or as the section's first line in step 3.

Your own bookings, dates, prices you paid, references and constraints are D or
S, never W or K. The script cuts the old Summary's items itself: label them K.
Test every item before you label it D or S: if it were deleted, would
Chaehan decide or do anything differently, or be unable to act? If not, it
is W or K, however true, interesting or his own: his facts that no point of
the note needs stay in his memory record or in the note it links.
A note that was rewritten before still loses whatever fails the test.
To fix a label later, append a corrected line: the last line for an item wins. A table is one item and is labelled as a whole.

  Accepted lines:
  7<TAB>D<TAB>D1     Your flight leaves Seoul at 09:40 on 2027-01-12.
  8<TAB>S<TAB>7      Check-in closes 60 minutes before departure.
  9<TAB>W<TAB>       The airline carried 21 million passengers in 2025.

Then run: python3 {me} next {d}
"""

STEP3 = """Step 3 of 4: the new sentences.

Write {d}/new.tsv with one line per decision:
D1<TAB>heading<TAB>summary line<TAB>first line

  heading       2 to 6 words naming what the section is about.
  summary line  one sentence, at most 30 words: the answer and the number
                that decides it.
  first line    one sentence, at most 30 words: the section's point, said as
                a fact about you, in other words than the summary line.

Both sentences start with You or Your, with an action (Book, Take, Skip), or
with a time or condition followed by you ("On 2027-01-12 you fly ..."). Say
what you have and what you must still do. Never write "X, not Y", and never
write about the note itself ("the section below shows").

  Accepted first line: You swim three mornings a week at the Mapo pool, which opens at 06:00.

Every table you keep gets a title of 2 to 6 words, written to {d}/titles.tsv
as id<TAB>title, one line per table: {tables}

Every number and name in your sentences comes from the note or the record,
and a number you restate keeps what it counts in the line it comes from:
"two nights at ¥20000" is ¥40000 in total, never ¥40000 a night. A rewording
that changes what a number counts is wrong even when every digit is there.
Write your own words: a sentence that repeats these instructions is refused.

  The form, from another note:
  Rejected: The clothes have no home after 2026-12-04.
  Accepted: You must still book a locker for your winter clothes before 2026-12-04.

Then run: python3 {me} next {d}
"""


STEP4 = """Step 4 of 4: overlaps.

Chaehan's first rule for a note: cut the overlaps. An overlap is a fact said
twice, or a second line that says more of the same. Each pair below shares
words. Judge each pair and append one line per pair to {d}/overlaps.tsv:

  a<TAB>b<TAB>same<TAB>c        when one says what the other says, or more of
                                the same; c is the item you cut (an item id),
                                and you append c<TAB>K<TAB> to labels.tsv.
  a<TAB>b<TAB>partial<TAB>c     when both repeat one fact and each adds its own;
                                the repeated fact leaves line c (edits.tsv for
                                an item, new.tsv for a first line), which keeps
                                only what it alone says. The script measures
                                the pair again.
  a<TAB>b<TAB>different<TAB>w   when each tells Chaehan something the other
                                does not; w is the words one line says that
                                the other does not, copied from that line.

D1, D2 ... are the sections' first lines. A first line states its section's
point: when it overlaps an item, cut the item. Never reword a line to get
past this step: only the repeated fact leaves, the rest stays as it was.

{pairs}
Then run: python3 {me} next {d}
"""


def check_decisions(ds: dict[str, str], mapping: dict[str, str], headings: list[str], source: str,
                    has_new: bool = False) -> tuple[list[str], list[str]]:
    """Errors in decisions.md, and the old sections whose fate the agent must ask Chaehan about."""
    errs = []
    if not ds:
        errs.append("decisions.md has no line of the form 'D1: <what you decide>'")
    if len(ds) > 5:
        errs.append(f"decisions.md has {len(ds)} decisions, keep at most 5")
    for k, text in ds.items():
        if copied(text):
            errs.append(f"{k} copies the example of step 1: write the decision from this note")
        bad = invented(text, source)
        if bad:
            errs.append(f"{k} names {', '.join(bad)}, which neither the note nor the record contains: {text[:60]!r}")
    body = [h for h in headings if not h.lower().startswith(SUMMARY_HEADS) and h != NEW_HEAD]
    missing = [h for h in body if h not in mapping]
    if missing:
        errs.append("decisions.md has no '<heading> -> D<n>' line for: " + "; ".join(missing))
    for h, target in mapping.items():
        if h == NEW_HEAD:
            continue
        if h not in body:
            errs.append(f"decisions.md maps {h!r}, which is not a heading of the old note (copy it exactly)")
        elif not (target in ds or target == "ask" or target.startswith("drop")):
            errs.append(f"{h!r} -> {target!r}: the target is a decision ({', '.join(ds)}), ask, or drop (Chaehan, <date>)")
        elif target.startswith("drop") and "chaehan" not in target.lower():
            errs.append(f"{h!r} is dropped without Chaehan's answer: write '-> ask' and ask him")
    for k in ds:
        # A decision that only new facts carry is checked later: it must keep a D item of its own.
        if mapping and k not in mapping.values() and not has_new:
            errs.append(f"{k} has no section of the old note behind it: map a section to it, or remove it")
    asks = [h for h, target in mapping.items() if target == "ask"]
    return errs, asks


def check_labels(items: list[dict], rows: list[list[str]], ds: dict[str, str]) -> list[str]:
    ids = {it["id"] for it in items}
    got: dict[str, tuple[str, str]] = {}
    errs = []
    for r in rows:
        r = (r + ["", "", ""])[:3]
        item, label, parent = r[0], r[1].upper(), r[2]
        if item not in ids:
            errs.append(f"labels.tsv names item {item!r}, which items.tsv does not have")
            continue
        if label not in LABELS:
            errs.append(f"item {item}: label {label!r} is not one of D, S, W, K, M")
            continue
        got[item] = (label, parent)
    missing = [i for i in sorted(ids, key=int) if i not in got]
    if missing:
        errs.append(f"{len(missing)} items have no label: {', '.join(missing[:25])}"
                    + (" ..." if len(missing) > 25 else ""))
    def loops(item: str, seen: tuple = ()) -> bool:
        parent = got[item][1]
        if parent in ds or parent not in got:
            return False
        return parent in seen or loops(parent, seen + (item,))

    under: dict[str, list[str]] = {}
    top: dict[str, list[str]] = {}
    for item, (label, parent) in got.items():
        if label == "S" and parent in got:
            under.setdefault(parent, []).append(item)
        if label in ("D", "S") and parent in ds:
            top.setdefault(parent, []).append(item)
    for k, its in sorted(top.items()):
        if len(its) > MAX_KIDS:
            errs.append(f"{k} keeps {len(its)} items at the top of its section ({', '.join(its)}): keep the "
                        f"{MAX_KIDS} whose deletion would change what Chaehan does; hang a detail that passes that test "
                        f"under the item it qualifies (S) and label the rest W or K")
    for parent, kids_ in sorted(under.items(), key=lambda kv: int(kv[0])):
        if len(kids_) > MAX_KIDS:
            errs.append(f"item {parent} carries {len(kids_)} supporting items ({', '.join(kids_)}): keep the "
                        f"{MAX_KIDS} that would change it most and label the rest W or K; only a detail that would "
                        f"change it may go into item {parent}'s wording as a parenthesis (edits.tsv)")
    for item, (label, parent) in got.items():
        if label == "M" and not parent.strip():
            errs.append(f"item {item}: an M item's parent is the exact title of the note it moves to")
        if label == "D" and parent not in ds:
            errs.append(f"item {item}: a D item's parent is a decision ({', '.join(ds)}), not {parent!r}")
        if label == "S":
            if parent not in ds and got.get(parent, ("", ""))[0] not in ("D", "S"):
                errs.append(f"item {item}: an S item's parent is a decision or a kept item (D or S), not {parent!r}")
            elif loops(item):
                errs.append(f"item {item}: its parents lead back to itself")
    return errs


def check_new_facts(items: list[dict], rows: list[list[str]], d: Path, source: str) -> list[str]:
    """Numbers and names in a kept new fact that neither the record, chaehan.md nor found.md holds."""
    keep = {r[0] for r in rows if len(r) > 1 and r[1].upper() in ("D", "S")}
    edits = {r[0] for r in tsv(d / "edits.tsv") if len(r) >= 2}
    out = []
    for it in items:
        if it["section"] != NEW_HEAD or it["id"] not in keep or it["id"] in edits or it["kind"] != "sentence":
            continue
        s = it["text"]
        bad = invented(s[:1].lower() + s[1:], source)  # a sentence's first word is no name
        if bad:
            out.append(f"item {it['id']}: {', '.join(bad)} in {s[:70]!r}")
    return out


OVERLAP_STOP = set("""that this with from your have when what which into than then them they their there these those
been were will would could should about after before over under while where only also more most such each other every
some same just very much many does done gets give gives gave takes take make makes made both once until because""".split())
OVERLAP_MIN = 0.25  # shared content words over the shorter line's
OVERLAP_MAX_PAIRS = 12


def content_words(s: str) -> set[str]:
    """The words that carry a line's content: no link, no date, no small word."""
    s = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"\d{4}-\d{2}(?:-\d{2})?", " ", s)
    words = re.findall(r"[a-z][a-z'-]{3,}|\d+(?:\.\d+)?%?", s.lower())
    return {re.sub(r"(?:'s|s)$", "", w) for w in words if w not in OVERLAP_STOP}


def kept_lines(d: Path, items: list[dict]) -> list[tuple[str, str]]:
    """Each section's first line (D1, D2 ...) and every kept sentence item, in the wording the draft will use."""
    rows = effective(items, tsv(d / "labels.tsv"))
    kept = {r[0] for r in rows if len(r) > 1 and r[1].upper() in ("D", "S")}
    edits = {r[0]: r[1] for r in tsv(d / "edits.tsv") if len(r) >= 2}
    lines = [(r[0], r[3]) for r in tsv(d / "new.tsv") if len(r) >= 4]
    return lines + [(it["id"], edits.get(it["id"], it["text"])) for it in items
                    if it["id"] in kept and it["kind"] == "sentence"]


def overlap_pairs(d: Path, items: list[dict]) -> list[tuple[str, str, str, str]]:
    """Pairs of kept lines (items and each section's first line) that share enough words to say the same thing."""
    lines = kept_lines(d, items)
    scored = []
    for i, (a, ta) in enumerate(lines):
        for b, tb in lines[i + 1:]:
            wa, wb = content_words(ta), content_words(tb)
            shared = wa & wb
            if len(shared) >= 2 and wa and wb and len(shared) / min(len(wa), len(wb)) >= OVERLAP_MIN:
                scored.append((len(shared) / min(len(wa), len(wb)), a, b, ta, tb))
    scored.sort(key=lambda x: -x[0])
    return [(a, b, ta, tb) for _, a, b, ta, tb in scored[:OVERLAP_MAX_PAIRS]]


def misplaced(d: Path, items: list[dict]) -> list[str]:
    """Details that share more words with another line of their section than with the line they hang under."""
    rows = effective(items, tsv(d / "labels.tsv"))
    lab = {r[0]: ((r + ["", ""])[1].upper(), (r + ["", "", ""])[2]) for r in rows}
    text = dict(kept_lines(d, items))

    def root(i: str, seen: tuple = ()) -> str:
        parent = lab.get(i, ("", ""))[1]
        return parent if parent not in lab or parent in seen else root(parent, seen + (i,))

    def under(i: str, top: str) -> bool:
        while i in lab and i != top:
            i = lab[i][1]
        return i == top

    out = []
    for i, (label, parent) in lab.items():
        if label != "S" or parent not in text or i not in text:
            continue
        k = root(i)
        mine = content_words(text[i])
        fit = len(mine & content_words(text[parent]))
        others = [(len(mine & content_words(text[j])), j) for j in text
                  if j not in (i, parent) and not under(j, i) and (j == k or (j in lab and root(j) == k))]
        best = max(others, default=(0, ""))
        if best[0] > fit:
            j = best[1]
            shared = ", ".join(sorted(mine & content_words(text[j])))
            where = f"label it D under {k}" if j == k else f"hang it under item {j} (S)"
            out.append(f"item {i} hangs under item {parent} but supports {'the first line of ' + k if j == k else 'item ' + j} "
                       f"more ({shared}): {where}")
    return out


def check_overlaps(d: Path, items: list[dict], pairs: list[tuple[str, str, str, str]]) -> tuple[list[str], list[str]]:
    """Errors in overlaps.tsv, and the listed pairs that have no verdict yet."""
    verdicts = {}
    for r in tsv(d / "overlaps.tsv"):
        if len(r) >= 3:
            verdicts[frozenset(r[:2])] = (r[2].lower(), (r + [""])[3])
    labels = {r[0]: r[1].upper() for r in effective(items, tsv(d / "labels.tsv")) if len(r) > 1}
    text = dict(kept_lines(d, items))
    listed = {frozenset((a, b)): (ta, tb) for a, b, ta, tb in pairs}
    errs, missing = [], []
    for key, (verdict, cut) in verdicts.items():
        name = " and ".join(sorted(key))
        if verdict == "different" and all(k in text for k in key):
            # A "different" names what one line adds, copied from it: a verdict without it was given to
            # every pair alike (14 of 14 on 2026-11-09), so it is no judgment.
            a, b = sorted(key)
            words = cut.strip().lower()
            in_a, in_b = bool(words) and words in text[a].lower(), bool(words) and words in text[b].lower()
            if not words or in_a == in_b:
                errs.append(f"{name}: name the words one line says that the other does not, copied from that line: "
                            f"{a}<TAB>{b}<TAB>different<TAB><words>")
            elif not content_words(words) - content_words(text[b] if in_a else text[a]):
                errs.append(f"{name}: {cut!r} adds nothing the other line lacks; judge the pair same or partial")
        if verdict == "partial" and cut not in key:
            errs.append(f"{name}: the line that gives up the shared fact must be one of the two")
        elif verdict == "partial" and key in listed:
            ta, tb = listed[key]
            shared = ", ".join(sorted(content_words(ta) & content_words(tb)))
            errs.append(f"{name} still share {shared}: take the shared fact out of {cut} "
                        f"({'new.tsv, its first line' if re.fullmatch(r'D[0-9]+', cut) else 'edits.tsv'}) "
                        f"and keep what only it says")
        if verdict == "same" and cut in labels and labels[cut] in ("D", "S"):
            errs.append(f"you judged {' and '.join(sorted(key))} the same, but item {cut} is still kept: "
                        f"append '{cut}<TAB>K<TAB>' to labels.tsv")
        if verdict == "same" and cut not in key:
            errs.append(f"{' and '.join(sorted(key))}: the item you cut must be one of the two, an item id")
        if verdict == "same" and re.fullmatch(r"D\d+", cut or ""):
            errs.append(f"{' and '.join(sorted(key))}: a first line states its section's point; cut the item")
        if verdict not in ("same", "partial", "different"):
            errs.append(f"{name}: the verdict is 'same', 'partial' or 'different', not {verdict!r}")
    for a, b, ta, tb in pairs:
        if frozenset((a, b)) not in verdicts:
            missing.append(f"  {a}  {ta}\n  {b}  {tb}\n")
    return errs, missing


JOINED = re.compile(r"(?<=[a-z0-9¥%)\]])([.!?])(?=[A-Z][a-z])")


def space_sentences(text: str) -> str:
    """Put back the space between two sentences run together ("¥340.At"), outside link targets."""
    parts = re.split(r"(\]\([^)]*\)|https?://\S+)", text)
    return "".join(p if i % 2 else JOINED.sub(r"\1 ", p) for i, p in enumerate(parts))


def kept_tables(items: list[dict], d: Path) -> str:
    rows = {r[0]: r for r in effective(items, tsv(d / "labels.tsv"))}
    keep = [it for it in items if it["kind"] == "table" and (rows.get(it["id"], ["", ""]) + [""])[1].upper() in ("D", "S")]
    return "".join(f"\n  {it['id']}: {it['text'].splitlines()[0][:100]}" for it in keep) or " (none kept)"


def check_titles(items: list[dict], d: Path) -> list[str]:
    rows = {r[0]: r for r in effective(items, tsv(d / "labels.tsv"))}
    titles = {r[0]: (r + [""])[1].strip() for r in tsv(d / "titles.tsv")}
    errs = []
    for it in items:
        if it["kind"] != "table" or (rows.get(it["id"], ["", ""]) + [""])[1].upper() not in ("D", "S"):
            continue
        t = titles.get(it["id"], "")
        if not t:
            errs.append(f"table {it['id']} has no title: add {it['id']}<TAB><2 to 6 words> ({it['text'].splitlines()[0][:60]})")
        elif not 2 <= len(t.split()) <= 6:
            errs.append(f"table {it['id']} title has {len(t.split())} words, use 2 to 6: {t!r}")
        elif copied(t):
            errs.append(f"table {it['id']} title copies the instructions")
    return errs


def check_edits(items: list[dict], d: Path, source: str) -> list[str]:
    ids = {it["id"] for it in items}
    errs = []
    for r in tsv(d / "edits.tsv"):
        if len(r) < 2 or r[0] not in ids:
            errs.append(f"edits.tsv line {r[:1]} needs an item id from items.tsv and the new text")
            continue
        errs += new_text_errors(f"edit of item {r[0]}", r[1].replace("\\n", "\n"), source)
    return errs


def given_summary(d: Path) -> list[str] | None:
    """The Summary lines from summary.md, when the note gives its own; None for one line per section."""
    p = d / "summary.md"
    if not p.exists():
        return None
    return [MARKER.sub("", l).strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def sentence_errors(k: str, name: str, s: str, g, source: str, ds: dict[str, str]) -> list[str]:
    errs = []
    n = len(s.split())
    if n > 30:
        errs.append(f"{k} {name} has {n} words, keep at most 30: {s[:60]!r}")
    if not g.seat(s):
        errs.append(f"{k} {name} must start with You or Your ('You cap the hotel at ...'): {s[:70]!r}")
    for c in g.contrast(s):
        errs.append(f"{k} {name} uses a contrast: {c}")
    if copied(s):
        errs.append(f"{k} {name} copies the instructions' example: write it from this note")
    for m in SEPARATOR.finditer(s):
        errs.append(f"{k} {name} writes {m.group(0)!r} with a thousand separator: write the number without it (¥208333)")
    for m in APPROX.finditer(s):
        errs.append(f"{k} {name} writes {m.group(0).strip()!r} before a number: write ~N (~65 minutes)")
    bad = invented(s, source + "\n" + "\n".join(ds.values())) if source else []
    if bad:
        errs.append(f"{k} {name} has {', '.join(bad)}, which is not in the note or the record")
    if META.search(s):
        errs.append(f"{k} {name} talks about the note, not about you: {s[:70]!r}; say the point itself")
    return errs


def check_summary(lines: list[str], ds: dict[str, str], g, source: str = "") -> list[str]:
    if not 1 <= len(lines) <= 3:
        return [f"summary.md has {len(lines)} lines, write one to three"]
    return [e for i, l in enumerate(lines, 1) for e in sentence_errors("summary.md", f"line {i}", l, g, source, ds)]


def check_new(rows: list[list[str]], ds: dict[str, str], g, source: str = "",
              own_summary: bool = False) -> list[str]:
    errs = []
    have = {}
    for r in rows:
        if len(r) < 4:
            errs.append(f"new.tsv line {r[:1]} needs four cells: decision, heading, summary line, first line")
            continue
        have[r[0]] = r
    for k in ds:
        if k not in have:
            errs.append(f"new.tsv has no line for {k}")
    for k, (_, heading, summary, first) in ((k, have[k][:4]) for k in have):
        if not 2 <= len(heading.split()) <= 6:
            errs.append(f"{k} heading has {len(heading.split())} words, use 2 to 6: {heading!r}")
        pairs = (("first line", first),) if own_summary else (("summary line", summary), ("first line", first))
        for name, s in pairs:
            errs += sentence_errors(k, name, s, g, source, ds)
        if own_summary:
            continue
        if g.words(summary) and len(g.words(summary) & g.words(first)) / len(g.words(summary)) >= 0.6:
            errs.append(f"{k} first line repeats the summary line: say what the section shows instead")
    return errs


# ---- assembly ---------------------------------------------------------------

def assemble(d: Path, items: list[dict], headings: list[str]) -> tuple[str, str, str, dict[int, str]]:
    """The draft, the cut list, the merged labels, and which item each draft line holds."""
    ds = decisions(d)
    labels = {r[0]: ((r + ["", ""])[1].upper(), (r + ["", "", ""])[2]) for r in effective(items, tsv(d / "labels.tsv"))}
    new = {r[0]: r for r in tsv(d / "new.tsv")}
    edits = {r[0]: r[1].replace("\\n", "\n") for r in tsv(d / "edits.tsv") if len(r) >= 2}
    titles = {r[0]: (r + [""])[1].strip() for r in tsv(d / "titles.tsv")}
    text = lambda it: space_sentences(edits.get(it["id"], it["text"]))
    out: list[str] = []
    where: dict[int, str] = {}

    def put(line: str, item: str = "") -> None:
        out.append(line)
        if item:
            where[len(out)] = item

    in_place = bool(json.loads((d / "meta.json").read_text(encoding="utf-8")).get("guid"))
    for it in items:
        if it["kind"] == "image" and not in_place and labels.get(it["id"], ("W",))[0] in "DS":
            put(text(it), it["id"])
            put("")
    put("## Summary")
    put("")
    for line in given_summary(d) or [new[k][2] for k in ds]:
        put(f"- {line}")
    put("")
    for k in ds:
        put(f"## {new[k][1]}")
        put("")
        put(new[k][3])
        put("")
        tops = [it for it in items if labels.get(it["id"]) == ("D", k)
                or (labels.get(it["id"], ("",))[0] == "S" and labels[it["id"]][1] == k)]
        tables = [it for it in tops if it["kind"] == "table"]

        def branch(nodes: list[dict], depth: int) -> None:
            prev = None
            for it in nodes:
                if it["kind"] == "table":
                    tables.append(it)
                    continue
                # Sentences of one old bullet stay one bullet while they share a place.
                same = (prev is not None and prev["line"] == it["line"]
                        and labels[prev["id"]] == labels[it["id"]] and not kids(items, labels, prev))
                if same:
                    out[-1] += " " + text(it)
                    where[len(out)] = where.get(len(out), it["id"]) + "," + it["id"]
                else:
                    put(f"{'  ' * min(depth, 2)}- {text(it)}", it["id"])
                prev = it
                branch(kids(items, labels, it), depth + 1)

        branch([it for it in tops if it["kind"] == "sentence"], 0)
        for it in tables:
            put("")
            if titles.get(it["id"]):
                put(f"### {titles[it['id']]}")
                put("")
            for row in text(it).splitlines():
                put(row, it["id"])
        put("")
    cuts: list[str] = []
    for it in items:
        label, parent = labels.get(it["id"], ("", ""))
        if label not in ("W", "K", "M") or (it["kind"] == "image" and in_place):
            continue
        why = {"W": "world detail", "K": "known or said elsewhere", "M": f"moved to the note {parent!r}"}[label]
        nums = NUMBER.findall(it["text"].replace(",", ""))
        key = ", ".join(dict.fromkeys(nums)) or " ".join(one_line(it).split()[:8])
        cuts.append(f"- {key}: {'' if label == 'M' else 'cut, '}{why} (item {it['id']})")
        if it["kind"] == "table":
            cuts += ["  " + row for row in it["text"].splitlines()]
    head_nums = [n for h in headings for n in NUMBER.findall(h.replace(",", ""))]
    if head_nums:
        cuts.append(f"- {', '.join(dict.fromkeys(head_nums))}: old section headings, the new headings name each decision")
    merged = "\n".join(f"{it['id']}\t{labels.get(it['id'], ('', ''))[0]}\t{labels.get(it['id'], ('', ''))[1]}\t"
                       f"{' '.join(one_line(it).split())}" for it in items)
    return "\n".join(out).rstrip() + "\n", "\n".join(cuts) + "\n", merged + "\n", where


def kids(items: list[dict], labels: dict, parent: dict) -> list[dict]:
    return [it for it in items if labels.get(it["id"]) == ("S", parent["id"])]


# A photo for the top of the note: an image line of its own above the first text, pointing at a file on this
# Mac. The angle-bracket form carries a path with spaces.
LOCAL_IMAGE = re.compile(r"^\s*!\[([^\]]*)\]\((?:<([^>]+)>|((?:/|~/)[^)\s]*))\)\s*$")
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif",
        ".heic": "image/heic", ".webp": "image/webp", ".pdf": "application/pdf"}


def image_info(path: Path) -> dict:
    """What the MCP upload needs about one file: MD5, size, type, name, and the pixel size when readable."""
    import hashlib
    data = path.read_bytes()
    info = {"path": str(path), "name": path.name, "hash": hashlib.md5(data).hexdigest(), "size": len(data),
            "mime": MIME.get(path.suffix.lower(), "application/octet-stream")}
    try:
        from PIL import Image
        with Image.open(path) as im:
            info["width"], info["height"] = im.size
    except Exception:
        pass
    return info


def local_images(draft: str) -> tuple[list[dict], str, list[str]]:
    """The photos at the top of the draft, the draft without their lines, and what is wrong with any of them."""
    imgs, keep, errs, top = [], [], [], True
    for line in draft.split("\n"):
        m = LOCAL_IMAGE.match(line)
        if m:
            path = Path(os.path.expanduser(m.group(2) or m.group(3)))
            if not top:
                errs.append(f"the image {path.name} stands below the text: write puts new images above it only")
            elif not path.is_file():
                errs.append(f"no file {path}")
            else:
                imgs.append(image_info(path))
            continue
        if line.strip():
            top = False
        keep.append(line)
    return imgs, "\n".join(keep).lstrip("\n"), errs


def verbatim_text(d: Path) -> str | None:
    """Chaehan's own words the note carries as he wrote them (init --verbatim), or None."""
    p = d / "verbatim.md"
    return p.read_text(encoding="utf-8") if p.exists() else None


def keep_verbatim(d: Path, files) -> None:
    """Store the --verbatim files in the build folder, where next, write and verify find them."""
    files = [files] if isinstance(files, str) else list(files or [])
    if files:
        (d / "verbatim.md").write_text("\n\n".join(Path(f).read_text(encoding="utf-8").strip() for f in files) + "\n",
                                       encoding="utf-8")


def write_command(d: Path) -> str:
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    base = f"cd {SOCRATES} && mamba run -n socrates python -m projects.evernote.src.evernote_api"
    if meta.get("guid"):
        return f"{base} update --markdown --file {d / 'draft.md'} {meta['guid']}"
    return f"{base} create --markdown --file {d / 'draft.md'} \"{meta['title']}\" --notebook \"{meta['notebook']}\""


# ---- commands ---------------------------------------------------------------

def cmd_init(a) -> int:
    d = Path(a.dir).resolve()
    d.mkdir(parents=True, exist_ok=True)
    if a.as_is:
        return init_as_is(d, a)
    if a.dest == "hanji" and (a.guid or not a.old):
        print("init --dest hanji builds a new note from a file: pass the file, --title and --notebook "
              "(an existing Hanji note is edited with the hanji skill)", file=sys.stderr)
        return 1
    if a.old:
        old = Path(a.old).read_text(encoding="utf-8")
    elif a.guid:
        # The note is read through the Evernote MCP, never the CLI (Chaehan, 2026-11-07): the agent runs the
        # printed code in one execute call, and the bridge finishes the init from the get_note result.
        args = {k: getattr(a, k) for k in ("guid", "title", "notebook", "decisions", "record", "chaehan", "section", "new",
                                           "verbatim")}
        (d / "init_args.json").write_text(json.dumps(args), encoding="utf-8")
        port = start_bridge(d, "init")
        print("Run this code in ONE execute call, exactly as printed. It reads the note and starts the build.\n")
        print(EXECUTE_INIT.replace("PORT", str(port)).replace("GUID", a.guid))
        return 0
    else:
        old = ""
    return finish_init(d, old, {k: getattr(a, k) for k in ("guid", "title", "notebook", "decisions", "record",
                                                            "chaehan", "section", "dest", "new", "verbatim")})


def init_as_is(d: Path, a) -> int:
    """A text written elsewhere becomes the note as it stands; only the gate checks it (Chaehan, 2026-11-10:
    "fix the evernote skill so it can be used by you as well")."""
    if not a.guid and not (a.title and a.notebook):
        print("init --as-is needs --guid for an existing note, or --title and --notebook for a new one",
              file=sys.stderr)
        return 1
    if a.guid and not a.base:
        print("init --as-is --guid needs --base <file>: the note's text as you read it (the readback.md of its last "
              "write, or its markdown export), so the write never covers an edit made in Evernote since",
              file=sys.stderr)
        return 1
    text = Path(a.as_is).read_text(encoding="utf-8")
    keep_verbatim(d, a.verbatim)
    meta_section = {}
    if a.replace_section:
        # One section of the note is written; every other byte of it stays (Chaehan's own edits, images in a
        # table). The draft is that section, under its heading, so the gate reads it as one.
        if not a.guid:
            print("init --replace-section needs --guid and --base", file=sys.stderr)
            return 1
        h = a.replace_section
        body = re.sub(rf"^\s*#{{1,3}}\s+{re.escape(h)}\s*\n", "", text, count=1)
        text = f"## {h}\n\n{body.strip()}\n"
        old = section_of(Path(a.base).read_text(encoding="utf-8"), h)
        if old is None:
            print(f"the base has no section {h!r}", file=sys.stderr)
            return 1
        meta_section = {"replace_section": h, "section_key": text_key(old)}
    for name, body in (("draft.md", text), ("original.md", text), ("cuts.md", ""), ("labels_merged.tsv", "")):
        (d / name).write_text(body, encoding="utf-8")
    meta_base = {"body_key": text_key(Path(a.base).read_text(encoding="utf-8"))} if a.base and not meta_section else {}
    meta_base.update(meta_section)
    (d / "meta.json").write_text(json.dumps({**meta_base, "guid": a.guid, "title": a.title, "notebook": a.notebook,
                                             "dest": a.dest, "new": False, "as_is": True,
                                             "person": getattr(a, "person", None),
                                             "record": [str(Path(r).resolve()) for r in a.record or []]}),
                                 encoding="utf-8")
    return check_as_is(d)


def check_as_is(d: Path) -> int:
    """Run the gate on draft.md as it stands; on PASS stamp it and print the write command."""
    g = gate()
    draft = (d / "draft.md").read_text(encoding="utf-8")
    _imgs, text, errs = local_images(draft)
    # The read-back is checked against this text; photo lines leave it, since their paths are no facts.
    (d / "original.md").write_text(text, encoding="utf-8")
    person = json.loads((d / "meta.json").read_text(encoding="utf-8")).get("person")
    fails = errs + g.check(text, None, note=True, table_titles=True, verbatim=verbatim_text(d), person=person)
    if fails:
        print(f"The gate fails the text. Edit {d / 'draft.md'}, then run next again:")
        for f in fails:
            print(f"- {f}")
        return 1
    print(f"note-gate:{g.stamp(draft).name}")
    print(f"\nPASS. The note text is stamped. Write it to Evernote, read it back and verify it with:\n"
          f"python3 {HERE} write {d}")
    return 0


def finish_init(d: Path, old: str, a: dict) -> int:
    """Split the old text into items and write the build folder; print step 1."""
    (d / "original.md").write_text(old, encoding="utf-8")
    keep_verbatim(d, a.get("verbatim"))
    new = a.get("new") or []
    new = new if isinstance(new, list) else [new]
    added = "\n\n".join(Path(f).read_text(encoding="utf-8").strip() for f in new)
    if added:
        (d / "new_facts.md").write_text(added + "\n", encoding="utf-8")
    items, headings = split_items(old.rstrip() + (f"\n\n## {NEW_HEAD}\n\n{added}\n" if added else "\n"))
    (d / "items.json").write_text(json.dumps({"items": items, "headings": headings}, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
    (d / "items.tsv").write_text("".join(f"{it['id']}\t{it['line']}\t{one_line(it)}\n" for it in items), encoding="utf-8")
    if not a["guid"] and not (a["title"] and a["notebook"]):
        print("init needs --guid for an existing note, or --title and --notebook for a new one", file=sys.stderr)
        return 1
    (d / "meta.json").write_text(json.dumps({"guid": a["guid"], "title": a["title"], "notebook": a["notebook"],
                                             "dest": a.get("dest") or "evernote", "new": bool(added),
                                             "record": [str(Path(r).resolve()) for r in a["record"] or []]}),
                                 encoding="utf-8")
    if a["decisions"]:
        (d / "decisions.md").write_text(Path(a["decisions"]).read_text(encoding="utf-8"), encoding="utf-8")
    if a["chaehan"]:
        files = a["chaehan"] if isinstance(a["chaehan"], list) else [a["chaehan"]]
        (d / "chaehan.md").write_text("\n\n".join(Path(f).read_text(encoding="utf-8") for f in files), encoding="utf-8")
    print(f"{len(items)} items in {d / 'items.tsv'}.\n")
    record = "\n".join(str(Path(r).resolve()) for r in a["record"] or []) or "(no record file named; use the brief)"
    print(STEP1.format(d=d, me=HERE, record=record))
    return 0


def cmd_next(a) -> int:
    d = Path(a.dir).resolve()
    if json.loads((d / "meta.json").read_text(encoding="utf-8")).get("as_is"):
        return check_as_is(d)
    data = json.loads((d / "items.json").read_text(encoding="utf-8"))
    items, headings = data["items"], data["headings"]
    g = gate()
    ds = decisions(d)
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    record = "\n".join(meta.get("record") or []) or "(no record file named; use the brief)"
    if not (d / "decisions.md").exists():
        print(STEP1.format(d=d, me=HERE, record=record))
        return 2
    source = source_text(d)
    mapping = section_map(d)
    errs, asks = check_decisions(ds, mapping, headings, source, has_new=bool(meta.get("new")))
    if errs:
        print("Fix decisions.md:\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    if asks:
        print("Ask Chaehan with the question tool before you go on. These sections of his note serve none of "
              "your decisions. For each one, does it stay (and under which decision) or leave his note?")
        for h in asks:
            print(f"- {h}")
        print("Write his answer into decisions.md as '<heading> -> D<n>' or '<heading> -> drop (Chaehan, <date>)', "
              "then run next again.")
        return 3
    if not (d / "labels.tsv").exists():
        print(STEP2.format(d=d, me=HERE, n=len(items), k=len(ds)))
        return 2
    errs = check_labels(items, effective(items, tsv(d / "labels.tsv")), ds)
    if errs:
        print("Fix labels.tsv:\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    errs = check_new_facts(items, effective(items, tsv(d / "labels.tsv")), d, source)
    if errs:
        print("Fix the new facts: a number or name with no line behind it in Chaehan's record, chaehan.md or "
              "found.md is an invention. Add the line it comes from to found.md with its source, or label the "
              "item W:\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    if not (d / "new.tsv").exists():
        print(STEP3.format(d=d, me=HERE, tables=kept_tables(items, d)))
        return 2
    own = given_summary(d)
    errs = check_new(tsv(d / "new.tsv"), ds, g, source, own_summary=own is not None)
    if errs:
        print("Fix new.tsv:\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    errs = check_summary(own, ds, g, source) if own is not None else []
    if errs:
        print("Fix summary.md:\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    errs = check_titles(items, d)
    if errs:
        print("Fix titles.tsv:\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    errs = check_edits(items, d, source + "\n" + "\n".join(ds.values()))
    if errs:
        print("Fix edits.tsv:\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    errs = misplaced(d, items)
    if errs:
        print("Fix labels.tsv: a detail hangs under the line it supports.\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    pairs = overlap_pairs(d, items)
    errs, missing = check_overlaps(d, items, pairs)
    if errs or missing:
        if errs:
            print("Fix overlaps.tsv or labels.tsv:\n" + "\n".join(f"- {e}" for e in errs))
        if missing:
            print(STEP4.format(d=d, me=HERE, pairs="\n".join(missing)))
        return 2
    draft, cuts, merged, where = assemble(d, items, headings)
    errs = bad_links(draft, d)
    if errs:
        print("Fix the links (edits.tsv):\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    for name, body in (("draft.md", draft), ("cuts.md", cuts), ("labels_merged.tsv", merged)):
        (d / name).write_text(body, encoding="utf-8")
    rows = effective(items, tsv(d / "labels.tsv"))
    kept = sum(1 for r in rows if r[1].upper() in ("D", "S"))
    keep_ids = {r[0] for r in rows if r[1].upper() in ("D", "S")}
    lost = [h for h in dict.fromkeys(it["section"] for it in items if not old_summary(it))
            if not any(it["id"] in keep_ids for it in items if it["section"] == h)
            and not mapping.get(h, "").startswith("drop") and h != NEW_HEAD]
    original = (d / "original.md").read_text(encoding="utf-8")
    fails = g.check(draft, original, note=True, cuts=cuts, labels=merged, table_titles=True, verbatim=verbatim_text(d))
    print(f"Assembled {d / 'draft.md'}: {kept} of {len(items)} items kept, "
          f"{len(original.split())} words before, {len(draft.split())} after.")
    empty = [k for k in ds if not any(r[1].upper() == "D" and (r + ["", ""])[2] == k for r in rows)]
    if empty:
        print("\nThese decisions keep no item, so their sections are a heading and one line. Label a deciding item "
              "D with the decision as parent, or fold the decision into another one in decisions.md:")
        for k in empty:
            print(f"- {k}: {ds[k][:80]}  -> labels.tsv or decisions.md")
        return 2
    if lost:
        print("\nThese sections keep none of their items, although decisions.md keeps them in the note. Label "
              "their deciding items D or S, or ask Chaehan and map them '-> drop (Chaehan, <date>)':")
        for h in lost:
            print(f"- {h}  -> labels.tsv")
        return 2
    if fails:
        print("\nThe gate fails the draft. Fix the file named after each line, then run next again:")
        for f in fails:
            m = re.match(r"T16 line (\d+)", f)
            hint = ""
            if m and int(m.group(1)) in where:
                hint = f"  -> write the item's new wording into edits.tsv as {where[int(m.group(1))].split(',')[0]}<TAB><text>"
            elif f.startswith(("T10", "T11", "T15")):
                hint = "  -> summary.md" if own is not None else "  -> new.tsv, summary line"
            elif f.startswith("T13"):
                hint = "  -> new.tsv, first line"
            elif f.startswith("T12"):
                hint = "  -> labels.tsv: hang some of these items on the item they belong to (its id as parent)"
            elif f.startswith("T17"):
                hint = "  -> titles.tsv"
            elif f.startswith(("T6", "T7", "T14")):
                hint = "  -> labels.tsv"
            print(f"- {f}{hint}")
        return 1
    print(f"\nnote-gate:{g.stamp(draft).name}")
    print(f"\nPASS. The note text is stamped. Write it to Evernote, read it back and verify it with:\n"
          f"python3 {HERE} write {d}")
    return 0


# ---- the Evernote MCP bridge ---------------------------------------------------
# Every read and write goes through the Evernote MCP (Chaehan, 2026-11-07: "only use the evernote mcp not
# cli! the cli is buggy"). The script cannot call the MCP; the agent in opencode can. So a command prints
# JavaScript for ONE execute call, and a local bridge on 127.0.0.1 hands that call its data and checks
# what comes back. Claude Code reaches it by launching opencode with note_test.py.

EXECUTE_INIT = """const n = await tools.evernote.get_note({ noteId: "GUID" });
return await (await fetch("http://127.0.0.1:PORT/init", { method: "POST", body: JSON.stringify(n) })).text();"""

EXECUTE_LINK = """const r = await tools.evernote.search_notes({ query: WORDS, maxResults: N });
return (r.hits || []).map(h => "[" + h.title + "](evernote:///view/39d2f74/s365/" + h.noteId + "/" + h.noteId + "/)").join("\\n") || "no note found; try fewer or other words";"""

EXECUTE_WRITE = """// note-gate:STAMP
const B = "http://127.0.0.1:PORT";
const job = await (await fetch(B + "/job")).json();
const linked = {};
for (const g of job.linked) linked[g] = await tools.evernote.get_note({ noteId: g });
let id = job.guid;
const before = id ? await tools.evernote.get_note({ noteId: id }) : null;
const plan = await (await fetch(B + "/plan", { method: "POST", body: JSON.stringify({ linked, before }) })).json();
if (plan.error) return "REFUSED: " + plan.error + " Do not change the note any other way: report this line.";
if (!id) {
  let opts = { title: job.title };
  if (job.notebook) {
    const r = await tools.evernote.search_notebooks({ query: job.notebook, maxResults: 20 });
    const hit = (r.hits || []).find(h => h.label === job.notebook);
    if (!hit) return "REFUSED: no notebook named " + job.notebook;
    opts.notebookId = hit.notebookId;
  }
  // A second note with the same title is a duplicate (RULES.md 31): update that note instead.
  const same = await tools.evernote.search_notes({ query: 'intitle:"' + job.title + '"', maxResults: 10 });
  const dup = (same.hits || []).find(h => h.title === job.title);
  if (dup) return "REFUSED: a note titled " + job.title + " exists already (" + dup.noteId + "): update it with init --guid, or choose another title.";
  const made = await tools.evernote.create_note(opts);
  id = JSON.stringify(made).match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/)[0];
  await fetch(B + "/created", { method: "POST", body: id });
  await tools.evernote.edit_note({ noteId: id, mode: "append", content: plan.content });
} else {
  await tools.evernote.edit_note({ noteId: id, mode: "replace", find: plan.find, content: plan.content });
}
// Photos for the top: the bytes go up through the bridge, the tags go in before finalize binds them.
const up = {};
for (const im of plan.images) {
  const s = await tools.evernote.start_attachment_upload({ noteId: id, hash: im.hash, sizeBytes: im.size });
  up[im.hash] = s.alreadyUploaded ? "already uploaded" :
    await (await fetch(B + "/upload", { method: "POST", body: JSON.stringify({ hash: im.hash, url: s.uploadUrl }) })).text();
}
if (plan.images.length) {
  await tools.evernote.edit_note({ noteId: id, mode: "prepend",
    content: plan.images.map(im => '<div><en-media hash="' + im.hash + '" type="' + im.mime + '"/></div>').join("") });
  for (const im of plan.images) {
    const f = { noteId: id, hash: im.hash, sizeBytes: im.size, mimeType: im.mime, filename: im.name };
    if (im.width) { f.width = im.width; f.height = im.height; }
    await tools.evernote.finalize_attachment(f);
  }
}
const after = await tools.evernote.get_note({ noteId: id });
const got = {};
for (const im of plan.images) got[im.hash] = await tools.evernote.get_attachment({ noteId: id, hash: im.hash });
return await (await fetch(B + "/done", { method: "POST", body: JSON.stringify({ id, after, up, got }) })).text();"""


def enml_module():
    """The socrates ENML converter, the one place markdown and ENML are turned into each other."""
    if str(SOCRATES) not in sys.path:
        sys.path.insert(0, str(SOCRATES))
    from projects.evernote.src import enml  # noqa: E402
    return enml


def find_key(obj, key: str):
    """The first value under `key` anywhere in a get_note result, whatever its wrapping."""
    if isinstance(obj, str) and obj.lstrip().startswith(("{", "[")):
        try:
            return find_key(json.loads(obj), key)
        except ValueError:
            return None
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], str):
            return obj[key]
        for v in obj.values():
            r = find_key(v, key)
            if r:
                return r
    if isinstance(obj, list):
        for v in obj:
            r = find_key(v, key)
            if r:
                return r
    return None


def find_enml(obj) -> str | None:
    """The ENML string inside a get_note result."""
    if isinstance(obj, str):
        if "<en-note" in obj and not obj.lstrip().startswith(("{", "[")):
            return obj
        try:
            return find_enml(json.loads(obj))
        except ValueError:
            return None
    if isinstance(obj, dict):
        for v in obj.values():
            r = find_enml(v)
            if r:
                return r
    if isinstance(obj, list):
        for v in obj:
            r = find_enml(v)
            if r:
                return r
    return None


def inner(enml: str) -> str:
    """The body between <en-note ...> and </en-note>, byte for byte."""
    m = re.search(r"<en-note[^>]*>(.*)</en-note>", enml, re.S)
    return m.group(1) if m else ""


# Images at the top of a note, bare or each in its own <div>, the form write's prepend gives them (2026-11-10: a
# second write of a note with two such photos was refused as "an image inside its text").
# An empty line (<div><br/></div>) may stand before them: the body a new note starts with.
LEADING_MEDIA = re.compile(r"^(?:\s*(?:<div>\s*(?:<br\s*/>)?\s*</div>\s*)*(?:<div>\s*)?<en-media\b[^>]*/>\s*(?:</div>\s*)?)+")
# Images at the foot of a note, where Chaehan put a picture, with the empty lines Evernote keeps after them.
TRAILING_MEDIA = re.compile(r"(?:\s*<en-media\b[^>]*/>\s*(?:<div>\s*<br\s*/>\s*</div>\s*)*)+$")


def text_key(md: str) -> str:
    """body_key for a note's text read through the converter (a readback.md): its words, images aside."""
    import hashlib
    text = "\n".join(l for l in md.splitlines() if not re.fullmatch(r"\s*!\[[^\]]*\]\([^)]*\)\s*", l))
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()


def body_key(body: str) -> str:
    """A fingerprint of a note body's text, images aside, to see whether anyone edited it since the build read it."""
    import hashlib
    # Images at the top and at the foot both leave, as text_key drops every image line (2026-11-14: a photo at the
    # foot of "2026-11-07 Right shoulder flare" made the two keys differ and refused every write as an edit).
    body = LEADING_MEDIA.sub("", body)
    body = TRAILING_MEDIA.sub("", body)
    text = enml_module().enml_to_markdown("<en-note>" + body + "</en-note>")
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()


def plan_write(d: Path, linked: dict, before) -> dict:
    """What the write replaces, or why it is refused: the stamp, every link's title, images that would be lost."""
    g = gate()
    draft = (d / "draft.md").read_text(encoding="utf-8")
    if not g.stamped(draft):
        return {"error": "the draft changed after its PASS: run next again"}
    images, draft, img_errs = local_images(draft)
    (d / "images.json").write_text(json.dumps(images), encoding="utf-8")
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    if meta.get("replace_section"):
        return plan_section(d, meta, draft, before, img_errs + (["a section write takes no photos"] if images else []))
    titles = {gid: find_key(n, "title") or "" for gid, n in linked.items()}
    cache_p = d / "links.json"
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    cache.update({k: v for k, v in titles.items() if v})
    cache_p.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    errs = list(img_errs)
    for name, url in EVERNOTE_LINK.findall(draft):
        m = GUID.search(url)
        t = titles.get(m.group(0), "") if m else ""
        if not t:
            errs.append(f"link {name!r} points at no note: find it with: python3 {HERE} link <words>")
        elif t != name:
            errs.append(f"link {name!r} must carry the note's exact title {t!r} (edits.tsv)")
    content = inner(enml_module().markdown_to_enml(draft))
    plan = {"content": content, "images": [{k: v for k, v in im.items() if k != "path"} for im in images]}
    if before is not None:
        old = find_enml(before)
        if not old:
            return {"error": "get_note returned no ENML for the note"}
        body = inner(old)
        # A photo the note holds already is not put in again: a second write of the same build would double it.
        have = set(re.findall(r'hash="([0-9a-f]{32})"', body))
        images = [im for im in images if im["hash"] not in have]
        (d / "images.json").write_text(json.dumps(images), encoding="utf-8")
        plan["images"] = [{k: v for k, v in im.items() if k != "path"} for im in images]
        lead = LEADING_MEDIA.match(body)
        rest = body[lead.end():] if lead else body
        trail = TRAILING_MEDIA.search(rest)
        rest = rest[:trail.start()] if trail else rest
        if "<en-media" in rest:
            # Images at the top and at the foot stay untouched (the replace runs between them); one inside the
            # text would be lost.
            errs.append("the note holds an image inside its text, which a full rewrite would drop")
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        if meta.get("body_key") and meta["body_key"] != body_key(body):
            errs.append("the note was edited since the build read it (Chaehan's edits): carry them into the build "
                        "with init --guid on the current note, then write")
        plan["find"] = rest
    if errs:
        return {"error": "; ".join(errs)}
    return plan


def gcs_upload(url: str, path: Path) -> str:
    """Put a file's bytes at the signed upload URL start_attachment_upload gave: a resumable start, then one PUT.

    The execute sandbox has no binary request body, so the bridge does this step (evernote skill, "the binary
    bridge"); the headers are the ones of the curl calls that worked on 2026-11-10."""
    import urllib.request
    data = path.read_bytes()
    start = urllib.request.Request(url, data=b"", method="POST", headers={
        "x-goog-resumable": "start", "x-upload-content-length": str(len(data)), "Content-Length": "0"})
    with urllib.request.urlopen(start, timeout=60) as r:
        loc = r.headers.get("Location")
    if not loc:
        return "no upload session"
    put = urllib.request.Request(loc, data=data, method="PUT", headers={
        "Content-Length": str(len(data)), "x-upload-content-length": str(len(data))})
    with urllib.request.urlopen(put, timeout=600) as r:
        return f"PUT {r.status}"


def check_images(d: Path, after, got: dict) -> list[str]:
    """The photos of this write: at the top of the note in their order, no broken tag, each download its MD5."""
    import hashlib
    import urllib.request
    p = d / "images.json"
    images = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    body = inner(find_enml(after) or "")
    lead = re.findall(r'hash="([0-9a-f]{32})"', (LEADING_MEDIA.match(body) or [""])[0])
    if not images:  # every photo of the draft was in the note already, or the draft has none
        return [f"images: {len(lead)} at the top, none new"] if lead else []
    want = [im["hash"] for im in images]
    out = []
    if lead[:len(want)] != want:
        out.append(f"IMAGES FAILED: the note opens with {lead[:len(want)]}, not {want}")
    if "<img" in body:
        out.append("IMAGES FAILED: the note holds a broken <img> tag")
    ok = 0
    for im in images:
        url = find_key(got.get(im["hash"]), "downloadUrl") or ""
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                same = hashlib.md5(r.read()).hexdigest() == im["hash"]
        except Exception as e:  # an expired or refused link is reported, never retried here
            out.append(f"IMAGES FAILED: {im['name']} could not be downloaded ({e})")
            continue
        ok += same
        if not same:
            out.append(f"IMAGES FAILED: {im['name']} downloads with another MD5")
    out.insert(0, f"images: {len(lead)} at the top, {ok} of {len(images)} downloads match their MD5")
    return out


def section_span(enml_body: str, heading: str) -> tuple[int, int] | None:
    """Where one section stands in a note body: from its heading to the next heading of its level or higher.
    Evernote's app writes its own attributes into a heading (<h2 style="--en-nodeId:...">)."""
    m = re.search(rf"<h([1-6])\b[^>]*>\s*{re.escape(heading)}\s*</h\1>", enml_body)
    if not m:
        return None
    nxt = re.search(rf"<h[1-{m.group(1)}]\b", enml_body[m.end():])
    return m.start(), m.end() + (nxt.start() if nxt else len(enml_body) - m.end())


def section_text(enml_body: str, span: tuple[int, int]) -> str:
    """The section's text without its heading, through the converter, as text_key reads it."""
    md = enml_module().enml_to_markdown("<en-note>" + enml_body[span[0]:span[1]] + "</en-note>")
    return re.sub(r"^\s*#{1,6}\s+.*\n", "", md, count=1)


def plan_section(d: Path, meta: dict, draft: str, before, errs: list[str]) -> dict:
    """The write of one section: its old ENML as find, the draft's section as content, nothing else touched."""
    h = meta["replace_section"]
    body = inner(find_enml(before) or "")
    span = section_span(body, h)
    if span is None:
        errs.append(f"the note has no heading {h!r}")
    else:
        if "<en-media" in body[span[0]:span[1]]:
            errs.append(f"the section {h!r} holds an image, which this write would drop")
        if text_key(section_text(body, span)) != meta.get("section_key"):
            errs.append(f"the section {h!r} was edited since the build read it: start again from the current note")
    if errs:
        return {"error": "; ".join(errs)}
    meta["outside_key"] = text_key(enml_module().enml_to_markdown("<en-note>" + body[:span[0]] + body[span[1]:] + "</en-note>"))
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return {"find": body[span[0]:span[1]], "content": inner(enml_module().markdown_to_enml(draft)), "images": []}


def done_section(d: Path, meta: dict, after) -> tuple[int, str]:
    """Verify a section write: the section reads as the draft, and the rest of the note is as it was."""
    body = inner(find_enml(after) or "")
    span = section_span(body, meta["replace_section"])
    if span is None:
        return 1, f"FAIL: the note lost its heading {meta['replace_section']!r}\n"
    draft = (d / "draft.md").read_text(encoding="utf-8")
    want = re.sub(r"^\s*#{1,6}\s+.*\n", "", draft, count=1)
    outside = enml_module().enml_to_markdown("<en-note>" + body[:span[0]] + body[span[1]:] + "</en-note>")
    out = []
    if text_key(section_text(body, span)) != text_key(want):
        out.append("FAIL: the section does not read back as the draft")
    if text_key(outside) != meta.get("outside_key"):
        out.append("FAIL: the rest of the note changed")
    (d / "readback.md").write_text(section_text(body, span), encoding="utf-8")
    return (1 if out else 0), "".join(l + "\n" for l in out) + ("" if out else "PASS: the section reads back as the "
                                                                     "draft and the rest of the note is unchanged\n")


def done_write(d: Path, gid: str, after, got: dict | None = None, up: dict | None = None) -> str:
    """Keep the guid, convert the read-back with the same converter, and verify it."""
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    if meta.get("replace_section"):
        rc, msg = done_section(d, meta, after)
        title = find_key(after, "title") or meta.get("title") or ""
        result = (json.dumps({"guid": gid, "title": title, "written": True}) + "\n" + msg
                  + ("" if rc == 0 else "VERIFY FAILED\n"))
        (d / "write_result.txt").write_text(result, encoding="utf-8")
        return result
    meta["guid"] = gid  # a created note is updated from now on
    meta["body_key"] = body_key(inner(find_enml(after) or ""))  # the next write checks nobody edited it since
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    back = enml_module().enml_to_markdown(find_enml(after) or "")
    (d / "readback.md").write_text(back, encoding="utf-8")
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cmd_verify(argparse.Namespace(dir=str(d), readback=str(d / "readback.md")))
    title = find_key(after, "title") or meta.get("title") or ""
    imgs = check_images(d, after, got or {})
    if up:
        imgs.insert(0, "uploads: " + ", ".join(f"{h[:8]} {v}" for h, v in up.items()))
    failed = rc != 0 or any(l.startswith("IMAGES FAILED") for l in imgs)
    result = (json.dumps({"guid": gid, "title": title, "written": True}) + "\n" + buf.getvalue()
              + "".join(l + "\n" for l in imgs) + ("VERIFY FAILED\n" if failed else ""))
    (d / "write_result.txt").write_text(result, encoding="utf-8")  # note_test.py --write reads the verdict here
    return result


def start_bridge(d: Path, mode: str) -> int:
    """Start the bridge for one execute call in the background; return its port."""
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
    log = open(d / f"bridge_{mode}.log", "w")
    env_py = Path.home() / "Software" / "miniforge3" / "envs" / "socrates" / "bin" / "python"
    py = str(env_py) if env_py.exists() else sys.executable  # the converter needs the socrates packages
    subprocess.Popen([py, str(HERE), "serve", str(d), "--port", str(port), "--mode", mode],
                     stdout=log, stderr=log, start_new_session=True, env=dict(os.environ))
    import time as _t
    for _ in range(50):  # wait until it listens, so the execute call never races it
        with socket.socket() as sk:
            if sk.connect_ex(("127.0.0.1", port)) == 0:
                break
        _t.sleep(0.1)
    return port


def cmd_serve(a) -> int:
    """The bridge: answers one execute call, then exits (10 minutes at most)."""
    from http.server import BaseHTTPRequestHandler, HTTPServer
    d = Path(a.dir).resolve()
    state = {"done": False}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            draft = (d / "draft.md").read_text(encoding="utf-8")
            linked = sorted({m.group(0) for _n, url in EVERNOTE_LINK.findall(draft) for m in [GUID.search(url)] if m})
            self.reply(json.dumps({"guid": meta.get("guid"), "title": meta.get("title"),
                                   "notebook": meta.get("notebook"), "linked": linked}))

        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
            import contextlib
            import io
            if self.path == "/init":
                args = json.loads((d / "init_args.json").read_text(encoding="utf-8"))
                enml = find_enml(raw)
                if not enml:
                    self.reply("get_note returned no ENML: check the guid")
                    state["done"] = True
                    return
                old = enml_module().enml_to_markdown(enml)
                key = body_key(inner(enml))
                if args.get("section"):
                    old = section_of(old, args["section"])
                    if old is None:
                        self.reply(f"no heading of the note contains {args['section']!r}")
                        state["done"] = True
                        return
                    args["guid"] = None  # the section becomes a new note
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    finish_init(d, old, args)
                if args.get("guid") and (d / "meta.json").exists():
                    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
                    meta["body_key"] = key
                    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
                self.reply(buf.getvalue())
                state["done"] = True
            elif self.path == "/plan":
                body = json.loads(raw)
                self.reply(json.dumps(plan_write(d, body.get("linked") or {}, body.get("before"))))
            elif self.path == "/created":
                meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
                meta["guid"] = raw.strip()  # kept at once, so a failed append is retried on this note
                (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
                self.reply("ok")
            elif self.path == "/upload":
                body = json.loads(raw)
                images = json.loads((d / "images.json").read_text(encoding="utf-8"))
                im = next((i for i in images if i["hash"] == body.get("hash")), None)
                try:
                    self.reply(gcs_upload(body["url"], Path(im["path"])) if im else "no such image in this write")
                except Exception as e:
                    self.reply(f"upload failed: {e}")
            elif self.path == "/done":
                body = json.loads(raw)
                self.reply(done_write(d, body["id"], body["after"], body.get("got"), body.get("up")))
                state["done"] = True

    srv = HTTPServer(("127.0.0.1", a.port), H)
    srv.timeout = 5
    import time as _t
    end = _t.time() + 600
    while not state["done"] and _t.time() < end:
        srv.handle_request()
    return 0


def cmd_link(a) -> int:
    """Print the execute code that lists the exact link of each note whose title matches the words."""
    print("Run this code in ONE execute call; copy a printed link into edits.tsv exactly.\n")
    print(EXECUTE_LINK.replace("WORDS", json.dumps(a.words)).replace("N", str(a.n)))
    return 0


def section_of(md: str, heading: str) -> str | None:
    """The body of the first section whose heading contains the words, without its heading."""
    lines = md.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"#{1,3}\s+", l) and heading.lower() in l.lower()), None)
    if start is None:
        return None
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    end = next((i for i in range(start + 1, len(lines)) if re.match(rf"#{{1,{level}}}\s+", lines[i])), len(lines))
    return "\n".join(lines[start + 1:end]).strip() + "\n"


def cmd_extract(a) -> int:
    """Copy one section of the old note, word for word, into a file: the findings for a new note."""
    d = Path(a.dir).resolve()
    lines = (d / "original.md").read_text(encoding="utf-8").splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"#{1,3}\s+", l) and a.heading.lower() in l.lower()), None)
    if start is None:
        print(f"no heading contains {a.heading!r}", file=sys.stderr)
        return 1
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    end = next((i for i in range(start + 1, len(lines)) if re.match(rf"#{{1,{level}}}\s+", lines[i])), len(lines))
    Path(a.out).write_text("\n".join(lines[start + 1:end]).strip() + "\n", encoding="utf-8")
    print(f"{end - start - 1} lines of '{lines[start].lstrip('# ')}' written to {Path(a.out).resolve()}")
    return 0


def cmd_write(a) -> int:
    """Print the execute code that writes the stamped draft through the MCP, reads it back and verifies it."""
    d = Path(a.dir).resolve()
    g = gate()
    draft = (d / "draft.md").read_text(encoding="utf-8")
    sha = g.stamp_key(draft)
    if not g.stamped(draft):
        print("The draft has no PASS stamp: run next until it prints PASS, then write.")
        return 7
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    if meta.get("dest") == "hanji":
        return write_hanji(d, meta)
    port = start_bridge(d, "write")
    print("Run this code in ONE execute call, exactly as printed. It writes the note, reads it back and returns "
          "the verify result. A line starting REFUSED names what to fix before you run write again.\n")
    print(EXECUTE_WRITE.replace("PORT", str(port)).replace("STAMP", sha))
    return 0


def hanji(*args: str) -> subprocess.CompletedProcess:
    """The hanji skill's helper; NOTE_BUILD_HANJI_DB points it at a scratch database (tests)."""
    db = os.environ.get("NOTE_BUILD_HANJI_DB")
    return subprocess.run([sys.executable, str(HANJI_NOTE), *(["--db", db] if db else []), *args],
                          capture_output=True, text=True)


def write_hanji(d: Path, meta: dict) -> int:
    """Create the stamped draft as a new Hanji note, read it back and verify it."""
    # Hanji names a file by the line's alt text and reads its type from that name, so a photo line goes in with
    # the file's own name (2026-11-10: "![us](<...png>)" became a file "us" of no image type).
    lines = []
    for line in (d / "draft.md").read_text(encoding="utf-8").split("\n"):
        m = LOCAL_IMAGE.match(line)
        if m:
            path = Path(os.path.expanduser(m.group(2) or m.group(3)))
            line = f"![{path.name}](<{path}>)"
        lines.append(line)
    (d / "draft_hanji.md").write_text("\n".join(lines), encoding="utf-8")
    r = hanji("create", "--notebook", meta["notebook"], "--title", meta["title"], "--file", str(d / "draft_hanji.md"))
    if r.returncode:
        print(f"REFUSED: {r.stderr.strip() or r.stdout.strip()}")
        return r.returncode
    made = json.loads(r.stdout)
    nid = made.get("id", "")
    if made.get("verified") is False:
        print(f"VERIFY FAILED: Hanji's read-back of note {nid} differs from the draft: {r.stdout.strip()[:400]}")
        return 4
    back = hanji("get", nid or meta["title"])
    if back.returncode:
        print(f"REFUSED: the read-back failed: {back.stderr.strip()}")
        return back.returncode
    lines = back.stdout.split("\n")
    if lines and lines[0].strip() == f"# {meta['title']}":
        lines = lines[1:]
    (d / "readback.md").write_text("\n".join(lines).lstrip("\n"), encoding="utf-8")
    (d / "written.json").write_text(json.dumps({"dest": "hanji", "id": nid, "title": meta["title"]}), encoding="utf-8")
    print(json.dumps({"dest": "hanji", "id": nid, "title": meta["title"], "written": True,
                      "verified_by_hanji": made.get("verified")}))
    rc = cmd_verify(argparse.Namespace(dir=str(d), readback=str(d / "readback.md")))
    if rc:
        print("VERIFY FAILED")
    return rc


def cmd_verify(a) -> int:
    d = Path(a.dir).resolve()
    g = gate()
    back = Path(a.readback).read_text(encoding="utf-8")
    fails = g.check(back, (d / "original.md").read_text(encoding="utf-8"), note=True,
                    cuts=(d / "cuts.md").read_text(encoding="utf-8"),
                    labels=(d / "labels_merged.tsv").read_text(encoding="utf-8"), table_titles=True,
                    verbatim=verbatim_text(d),
                    person=json.loads((d / "meta.json").read_text(encoding="utf-8")).get("person"))
    for f in fails:
        print(f)
    print("PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("dir")
    i.add_argument("old", nargs="?", help="the old text; left out with --guid, the script reads the note itself")
    i.add_argument("--guid")
    i.add_argument("--title")
    i.add_argument("--notebook")
    i.add_argument("--decisions", help="Chaehan's decisions from the brief, one 'D1: ...' line each")
    i.add_argument("--record", action="append", help="Chaehan's record of the topic, e.g. socrates memory/travel.md")
    i.add_argument("--chaehan", action="append", help="Chaehan's instructions and new facts, his words (repeatable)")
    i.add_argument("--new", action="append", help="facts the note does not hold yet, one per line; they become items "
                                                  "under 'New facts' and are checked against the record (repeatable)")
    i.add_argument("--section", help="with --guid, --title and --notebook: build a new note from this section")
    i.add_argument("--dest", choices=DESTS, default="evernote", help="where write puts the note (default evernote)")
    i.add_argument("--verbatim", action="append", help="Chaehan's own words the note carries as he wrote them (a file, "
                   "repeatable): the gate leaves their form alone and fails when one of their sentences is missing or changed")
    i.add_argument("--replace-section", dest="replace_section", help="with --as-is --guid --base: write only this "
                   "section of the note (its heading's text) and leave every other byte as it stands")
    i.add_argument("--base", help="with --as-is --guid: the note's text as you read it; the write refuses when the "
                   "note changed since")
    i.add_argument("--person", help="with --as-is: the woman a date note is about (date-analysis skill); the gate "
                   "takes she, her and her name as a subject beside you "
                   "(Chaehan, 2026-11-12: \"she may lead\")")
    i.add_argument("--as-is", dest="as_is", help="a text written elsewhere (Claude, Chaehan) is the note: only the gate "
                   "checks it; photo lines at its top are uploaded by write")
    lk = sub.add_parser("link", help="print the exact Evernote link for notes matching the words")
    lk.add_argument("words")
    lk.add_argument("-n", type=int, default=5)
    sv = sub.add_parser("serve", help="the MCP bridge for one execute call (started by init and write)")
    sv.add_argument("dir")
    sv.add_argument("--port", type=int, required=True)
    sv.add_argument("--mode", choices=("init", "write"), required=True)
    ex = sub.add_parser("extract", help="copy one old section into a findings file for a new note")
    ex.add_argument("dir")
    ex.add_argument("heading")
    ex.add_argument("out")
    n = sub.add_parser("next")
    n.add_argument("dir")
    w = sub.add_parser("write")
    w.add_argument("dir")
    v = sub.add_parser("verify")
    v.add_argument("dir")
    v.add_argument("readback")
    a = ap.parse_args(argv)
    return {"init": cmd_init, "next": cmd_next, "write": cmd_write, "verify": cmd_verify, "link": cmd_link,
            "extract": cmd_extract, "serve": cmd_serve}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
