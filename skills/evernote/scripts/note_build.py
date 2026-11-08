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
LABELS = ("D", "S", "W", "K", "M")
LINK = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
NUMBER = re.compile(r"\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?")
SUMMARY_HEADS = ("summary", "takeaway", "tl;dr")
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
    own = _shingles(STEP1 + STEP2 + STEP3)
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

STEP1 = """Step 1 of 3: decisions, and where each old section goes.

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

Second part: one line for every heading of the old note, as
"<heading exactly as written> -> D<n>". Every section Chaehan has in his note
is there because he asked for it. A section that serves none of your decisions
gets "<heading> -> ask": the script then stops, and you ask Chaehan with the
question tool whether it leaves his note. Write his answer back as
"<heading> -> D<n>", or as "<heading> -> drop (Chaehan, <date>)" only when he
said yes. The old Summary needs no line.

  The form, from another note:
  D2: Do you renew the Mapo storage locker for another month at 72090 won?
  Storage options -> D2

Then run: python3 {me} next {d}
"""

STEP2 = """Step 2 of 3: labels.

{d}/items.tsv lists the {n} items of the old note, one per line: id, line, text.
Write {d}/labels.tsv with one line per item: id<TAB>label<TAB>parent.
Label each item on its own, by what it does for one of the decisions in
decisions.md:

  D  decides: it changes a decision. Parent: that decision, D1 to D{k}.
  S  supports: a detail you need to act on a kept item. Parent: that item's
     id. A detail can hang on another detail.
  W  world detail: true, but you will not act on it. Market statistics, a
     second source saying the same, a price of something you will not buy, a
     place ruled out for a reason you do not need, an option kept only for
     comparison, and a side trip the decisions do not need. No parent.
  K  known: you know it already, or the note says it again elsewhere, like an
     old summary line that repeats the body. No parent.
  M  moved: it now lives in another note. Parent: that note's exact title.

Your own bookings, dates, prices you paid, references and constraints are D or
S, never W or K. The script cuts the old Summary's items itself: label them K.
To fix a label later, append a corrected line: the last line for an item wins. A table is one item and is labelled as a whole. Keep only what
you act on: most notes lose a third of their items or more.

  Accepted lines:
  7<TAB>D<TAB>D1     Your flight leaves Seoul at 09:40 on 2027-01-12.
  8<TAB>S<TAB>7      Check-in closes 60 minutes before departure.
  9<TAB>W<TAB>       The airline carried 21 million passengers in 2025.

Then run: python3 {me} next {d}
"""

STEP3 = """Step 3 of 3: the new sentences.

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

Every number and name in your sentences comes from the note or the record.
Write your own words: a sentence that repeats these instructions is refused.

  The form, from another note:
  Rejected: The clothes have no home after 2026-12-04.
  Accepted: You must still book a locker for your winter clothes before 2026-12-04.

Then run: python3 {me} next {d}
"""


def check_decisions(ds: dict[str, str], mapping: dict[str, str], headings: list[str], source: str) -> tuple[list[str], list[str]]:
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
    body = [h for h in headings if not h.lower().startswith(SUMMARY_HEADS)]
    missing = [h for h in body if h not in mapping]
    if missing:
        errs.append("decisions.md has no '<heading> -> D<n>' line for: " + "; ".join(missing))
    for h, target in mapping.items():
        if h not in body:
            errs.append(f"decisions.md maps {h!r}, which is not a heading of the old note (copy it exactly)")
        elif not (target in ds or target == "ask" or target.startswith("drop")):
            errs.append(f"{h!r} -> {target!r}: the target is a decision ({', '.join(ds)}), ask, or drop (Chaehan, <date>)")
        elif target.startswith("drop") and "chaehan" not in target.lower():
            errs.append(f"{h!r} is dropped without Chaehan's answer: write '-> ask' and ask him")
    for k in ds:
        if mapping and k not in mapping.values():
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

    for it in items:
        if it["kind"] == "image" and labels.get(it["id"], ("W",))[0] in "DS":
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
        if label not in ("W", "K", "M"):
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
    if a.old:
        old = Path(a.old).read_text(encoding="utf-8")
    elif a.guid:
        # The note is read through the Evernote MCP, never the CLI (Chaehan, 2026-11-07): the agent runs the
        # printed code in one execute call, and the bridge finishes the init from the get_note result.
        args = {k: getattr(a, k) for k in ("guid", "title", "notebook", "decisions", "record", "chaehan", "section")}
        (d / "init_args.json").write_text(json.dumps(args), encoding="utf-8")
        port = start_bridge(d, "init")
        print("Run this code in ONE execute call, exactly as printed. It reads the note and starts the build.\n")
        print(EXECUTE_INIT.replace("PORT", str(port)).replace("GUID", a.guid))
        return 0
    else:
        old = ""
    return finish_init(d, old, {k: getattr(a, k) for k in ("guid", "title", "notebook", "decisions", "record",
                                                            "chaehan", "section")})


def finish_init(d: Path, old: str, a: dict) -> int:
    """Split the old text into items and write the build folder; print step 1."""
    (d / "original.md").write_text(old, encoding="utf-8")
    items, headings = split_items(old)
    (d / "items.json").write_text(json.dumps({"items": items, "headings": headings}, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
    (d / "items.tsv").write_text("".join(f"{it['id']}\t{it['line']}\t{one_line(it)}\n" for it in items), encoding="utf-8")
    if not a["guid"] and not (a["title"] and a["notebook"]):
        print("init needs --guid for an existing note, or --title and --notebook for a new one", file=sys.stderr)
        return 1
    (d / "meta.json").write_text(json.dumps({"guid": a["guid"], "title": a["title"], "notebook": a["notebook"],
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
    errs, asks = check_decisions(ds, mapping, headings, source)
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
            and not mapping.get(h, "").startswith("drop")]
    original = (d / "original.md").read_text(encoding="utf-8")
    fails = g.check(draft, original, note=True, cuts=cuts, labels=merged, table_titles=True)
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
  const made = await tools.evernote.create_note(opts);
  id = JSON.stringify(made).match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/)[0];
  await fetch(B + "/created", { method: "POST", body: id });
  await tools.evernote.edit_note({ noteId: id, mode: "append", content: plan.content });
} else {
  await tools.evernote.edit_note({ noteId: id, mode: "replace", find: plan.find, content: plan.content });
}
const after = await tools.evernote.get_note({ noteId: id });
return await (await fetch(B + "/done", { method: "POST", body: JSON.stringify({ id, after }) })).text();"""


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


LEADING_MEDIA = re.compile(r"^(?:\s*<en-media\b[^>]*/>\s*)+")


def body_key(body: str) -> str:
    """A fingerprint of a note body's text, images aside, to see whether anyone edited it since the build read it."""
    import hashlib
    text = enml_module().enml_to_markdown("<en-note>" + LEADING_MEDIA.sub("", body) + "</en-note>")
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()


def plan_write(d: Path, linked: dict, before) -> dict:
    """What the write replaces, or why it is refused: the stamp, every link's title, images that would be lost."""
    g = gate()
    draft = (d / "draft.md").read_text(encoding="utf-8")
    if not (g.stamp_dir() / g.stamp_key(draft)).exists():
        return {"error": "the draft changed after its PASS: run next again"}
    titles = {gid: find_key(n, "title") or "" for gid, n in linked.items()}
    cache_p = d / "links.json"
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    cache.update({k: v for k, v in titles.items() if v})
    cache_p.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    errs = []
    for name, url in EVERNOTE_LINK.findall(draft):
        m = GUID.search(url)
        t = titles.get(m.group(0), "") if m else ""
        if not t:
            errs.append(f"link {name!r} points at no note: find it with: python3 {HERE} link <words>")
        elif t != name:
            errs.append(f"link {name!r} must carry the note's exact title {t!r} (edits.tsv)")
    content = inner(enml_module().markdown_to_enml(draft))
    plan = {"content": content}
    if before is not None:
        old = find_enml(before)
        if not old:
            return {"error": "get_note returned no ENML for the note"}
        body = inner(old)
        lead = LEADING_MEDIA.match(body)
        rest = body[lead.end():] if lead else body
        if "<en-media" in rest:
            # An image at the top stays untouched (the replace starts after it); one inside the text would be lost.
            errs.append("the note holds an image inside its text, which a full rewrite would drop")
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        if meta.get("body_key") and meta["body_key"] != body_key(body):
            errs.append("the note was edited since the build read it (Chaehan's edits): carry them into the build "
                        "with init --guid on the current note, then write")
        plan["find"] = rest
    if errs:
        return {"error": "; ".join(errs)}
    return plan


def done_write(d: Path, gid: str, after) -> str:
    """Keep the guid, convert the read-back with the same converter, and verify it."""
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
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
    return json.dumps({"guid": gid, "title": title, "written": True}) + "\n" + buf.getvalue() + ("" if rc == 0 else "VERIFY FAILED\n")


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
            elif self.path == "/done":
                body = json.loads(raw)
                self.reply(done_write(d, body["id"], body["after"]))
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
    if not (g.stamp_dir() / sha).exists():
        print("The draft has no PASS stamp: run next until it prints PASS, then write.")
        return 7
    port = start_bridge(d, "write")
    print("Run this code in ONE execute call, exactly as printed. It writes the note, reads it back and returns "
          "the verify result. A line starting REFUSED names what to fix before you run write again.\n")
    print(EXECUTE_WRITE.replace("PORT", str(port)).replace("STAMP", sha))
    return 0


def cmd_verify(a) -> int:
    d = Path(a.dir).resolve()
    g = gate()
    back = Path(a.readback).read_text(encoding="utf-8")
    fails = g.check(back, (d / "original.md").read_text(encoding="utf-8"), note=True,
                    cuts=(d / "cuts.md").read_text(encoding="utf-8"),
                    labels=(d / "labels_merged.tsv").read_text(encoding="utf-8"), table_titles=True)
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
    i.add_argument("--section", help="with --guid, --title and --notebook: build a new note from this section")
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
