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
Evernote CLI will accept.

    python3 note_build.py init <dir> <old.md> (--guid <guid> | --title <title> --notebook <name>)
    python3 note_build.py next <dir>
    python3 note_build.py verify <dir> <read-back.md>

`next` always prints the one step that is due, or what to fix in it.
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
LABELS = ("D", "S", "W", "K")
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
    return "\n".join(parts)


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


def invented(sentence: str, source: str) -> list[str]:
    """Numbers and names in a new sentence that neither the note nor Chaehan's record contains."""
    src = source.replace(",", "")
    have = set(NUMBER.findall(src))
    out = [n for n in NUMBER.findall(sentence.replace(",", "")) if n not in have]
    names = re.findall(r"\b[A-Z][A-Za-z-]{2,}\b", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", sentence))
    out += [n for n in names if n not in NOT_NAMES and n not in source]
    return out


# ---- steps ------------------------------------------------------------------

STEP1 = """Step 1 of 3: decisions, and where each old section goes.

Read the whole old note, {d}/original.md, and Chaehan's record of the topic:
{record}

Write {d}/decisions.md in two parts. If the brief gave Chaehan's decisions,
they are there already: keep them and add the second part.

First part: one line per decision Chaehan makes with this note, at most five,
as "D1: <what you decide>". A decision is something you will do or choose, and
it names places, dates and numbers from the note or the record. Take the
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
     place ruled out for a reason you do not need. No parent.
  K  known: you know it already, or the note says it again elsewhere, like an
     old summary line that repeats the body. No parent.

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
            errs.append(f"item {item}: label {label!r} is not one of D, S, W, K")
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
        if label == "D" and parent not in ds:
            errs.append(f"item {item}: a D item's parent is a decision ({', '.join(ds)}), not {parent!r}")
        if label == "S":
            if parent not in ds and got.get(parent, ("", ""))[0] not in ("D", "S"):
                errs.append(f"item {item}: an S item's parent is a decision or a kept item (D or S), not {parent!r}")
            elif loops(item):
                errs.append(f"item {item}: its parents lead back to itself")
    return errs


def check_new(rows: list[list[str]], ds: dict[str, str], g, source: str = "") -> list[str]:
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
        for name, s in (("summary line", summary), ("first line", first)):
            n = len(s.split())
            if n > 30:
                errs.append(f"{k} {name} has {n} words, keep at most 30: {s[:60]!r}")
            if not g.seat(s):
                errs.append(f"{k} {name} must start with You or Your ('You cap the hotel at ...'): {s[:70]!r}")
            for c in g.contrast(s):
                errs.append(f"{k} {name} uses a contrast: {c}")
            if copied(s):
                errs.append(f"{k} {name} copies the instructions' example: write it from this note")
            for m in re.finditer(r"\d{1,3}(?:,\d{3})+\b", s):
                errs.append(f"{k} {name} writes {m.group(0)!r} with a thousand separator: write the number without it (¥208333)")
            bad = invented(s, source + "\n" + "\n".join(ds.values())) if source else []
            if bad:
                errs.append(f"{k} {name} has {', '.join(bad)}, which is not in the note or the record")
            if META.search(s):
                errs.append(f"{k} {name} talks about the note, not about you: {s[:70]!r}; say the point itself")
        if g.words(summary) and len(g.words(summary) & g.words(first)) / len(g.words(summary)) >= 0.6:
            errs.append(f"{k} first line repeats the summary line: say what the section shows instead")
    return errs


# ---- assembly ---------------------------------------------------------------

def assemble(d: Path, items: list[dict], headings: list[str]) -> tuple[str, str, str, dict[int, str]]:
    """The draft, the cut list, the merged labels, and which item each draft line holds."""
    ds = decisions(d)
    labels = {r[0]: ((r + ["", ""])[1].upper(), (r + ["", "", ""])[2]) for r in effective(items, tsv(d / "labels.tsv"))}
    new = {r[0]: r for r in tsv(d / "new.tsv")}
    edits = {r[0]: r[1] for r in tsv(d / "edits.tsv") if len(r) >= 2}
    text = lambda it: edits.get(it["id"], it["text"])
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
    for k in ds:
        put(f"- {new[k][2]}")
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
            for row in text(it).splitlines():
                put(row, it["id"])
        put("")
    cuts: list[str] = []
    for it in items:
        label = labels.get(it["id"], ("", ""))[0]
        if label not in ("W", "K"):
            continue
        why = "world detail" if label == "W" else "known or said elsewhere"
        nums = NUMBER.findall(it["text"].replace(",", ""))
        key = ", ".join(dict.fromkeys(nums)) or " ".join(one_line(it).split()[:8])
        cuts.append(f"- {key}: cut, {why} (item {it['id']})")
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
        r = subprocess.run(CLI + ["get", a.guid, "--markdown"], cwd=SOCRATES, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"Reading note {a.guid} failed: {r.stderr.strip()[-300:]}", file=sys.stderr)
            return 1
        old = json.loads(r.stdout).get("content", "")
    else:
        old = ""
    (d / "original.md").write_text(old, encoding="utf-8")
    items, headings = split_items(old)
    (d / "items.json").write_text(json.dumps({"items": items, "headings": headings}, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
    (d / "items.tsv").write_text("".join(f"{it['id']}\t{it['line']}\t{one_line(it)}\n" for it in items), encoding="utf-8")
    if not a.guid and not (a.title and a.notebook):
        print("init needs --guid for an existing note, or --title and --notebook for a new one", file=sys.stderr)
        return 1
    (d / "meta.json").write_text(json.dumps({"guid": a.guid, "title": a.title, "notebook": a.notebook,
                                             "record": [str(Path(r).resolve()) for r in a.record or []]}),
                                 encoding="utf-8")
    if a.decisions:
        (d / "decisions.md").write_text(Path(a.decisions).read_text(encoding="utf-8"), encoding="utf-8")
    print(f"{len(items)} items in {d / 'items.tsv'}.\n")
    record = "\n".join(str(Path(r).resolve()) for r in a.record or []) or "(no record file named; use the brief)"
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
        print(STEP3.format(d=d, me=HERE))
        return 2
    errs = check_new(tsv(d / "new.tsv"), ds, g, source)
    if errs:
        print("Fix new.tsv:\n" + "\n".join(f"- {e}" for e in errs))
        return 2
    draft, cuts, merged, where = assemble(d, items, headings)
    for name, body in (("draft.md", draft), ("cuts.md", cuts), ("labels_merged.tsv", merged)):
        (d / name).write_text(body, encoding="utf-8")
    rows = effective(items, tsv(d / "labels.tsv"))
    kept = sum(1 for r in rows if r[1].upper() in ("D", "S"))
    keep_ids = {r[0] for r in rows if r[1].upper() in ("D", "S")}
    lost = [h for h in dict.fromkeys(it["section"] for it in items if not old_summary(it))
            if not any(it["id"] in keep_ids for it in items if it["section"] == h)
            and not mapping.get(h, "").startswith("drop")]
    original = (d / "original.md").read_text(encoding="utf-8")
    fails = g.check(draft, original, note=True, cuts=cuts, labels=merged)
    print(f"Assembled {d / 'draft.md'}: {kept} of {len(items)} items kept, "
          f"{len(original.split())} words before, {len(draft.split())} after.")
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
                hint = "  -> new.tsv, summary line"
            elif f.startswith("T13"):
                hint = "  -> new.tsv, first line"
            elif f.startswith("T12"):
                hint = "  -> labels.tsv: hang some of these items on the item they belong to (its id as parent)"
            elif f.startswith(("T6", "T7", "T14")):
                hint = "  -> labels.tsv"
            print(f"- {f}{hint}")
        return 1
    print(f"\nnote-gate:{g.stamp(draft).name}")
    print(f"\nPASS. The note text is stamped. Write it to Evernote, read it back and verify it with:\n"
          f"python3 {HERE} write {d}")
    return 0


CLI = ["mamba", "run", "-n", "socrates", "python", "-m", "projects.evernote.src.evernote_api"]


def cmd_write(a) -> int:
    """Write the stamped draft with the Evernote CLI, read it back, and verify the read-back."""
    d = Path(a.dir).resolve()
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    base = CLI
    draft = str(d / "draft.md")
    if meta.get("guid"):
        cmd = base + ["update", "--markdown", "--file", draft, meta["guid"]]
    else:
        cmd = base + ["create", "--markdown", "--file", draft, meta["title"], "--notebook", meta["notebook"]]
    w = subprocess.run(cmd, cwd=SOCRATES, capture_output=True, text=True)
    print(w.stdout.strip() or w.stderr.strip())
    if w.returncode != 0:
        print(f"The write failed (exit {w.returncode}). Exit 7 means the draft changed after its PASS: run next again.")
        return w.returncode
    guid = meta.get("guid") or json.loads(w.stdout).get("guid")
    r = subprocess.run(base + ["get", guid, "--markdown"], cwd=SOCRATES, capture_output=True, text=True)
    back = json.loads(r.stdout).get("content", "") if r.returncode == 0 else ""
    (d / "readback.md").write_text(back, encoding="utf-8")
    return cmd_verify(argparse.Namespace(dir=str(d), readback=str(d / "readback.md")))


def cmd_verify(a) -> int:
    d = Path(a.dir).resolve()
    g = gate()
    back = Path(a.readback).read_text(encoding="utf-8")
    fails = g.check(back, (d / "original.md").read_text(encoding="utf-8"), note=True,
                    cuts=(d / "cuts.md").read_text(encoding="utf-8"),
                    labels=(d / "labels_merged.tsv").read_text(encoding="utf-8"))
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
    n = sub.add_parser("next")
    n.add_argument("dir")
    w = sub.add_parser("write")
    w.add_argument("dir")
    v = sub.add_parser("verify")
    v.add_argument("dir")
    v.add_argument("readback")
    a = ap.parse_args(argv)
    return {"init": cmd_init, "next": cmd_next, "write": cmd_write, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
