"""Mechanical gate for a life-overview draft (checks T3 to T5).

Each failure names the sentence or section it rejects. Exit 1 on any failure.

    python overview_gate.py <draft.md> [--original <old.md>] [--challenges <note.md>] [--linked <note.md> ...]

T3  an Open tasks section, an email address or a phone number in the overview
    (the next moves live in the Life Challenges note); no link to a
    "YYYY-MM-DD Life Challenges" (or, before 2026-11-07, "Life Problems") note;
    with --challenges, a Takeaway bullet made mostly of the words of one of
    that note's decision questions, options, answers or Hand to me rows
    (numbers ignored).
T4  a body section with no note link (unless it says "no detail note");
    a note with zero links
T5  no indented bullet anywhere
T18 a number with a thousand separator ("10,000,000 won"; write 10000000)
T19 with --sources: a number or name in a section that the section's block in sources.md
    does not hold (the Takeaway may use every block)
T6  runs only on the note paths below (removed from the life overview on
    2026-11-07: its fixes put the clutter back). T6 is a date
    or number of --original that survives neither in the draft nor in a linked
    note (thousand separators and the digits inside a link's address ignored).

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
"note-gate:<sha>". Where that folder cannot be written (Claude Code's sandbox
allows ~/.cache but not ~/.local/state), the stamp goes to
~/.cache/agentkit/note-gate instead, and every reader checks both folders. The socrates Evernote CLI computes the same key and refuses a
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
LINK_TARGET = re.compile(r"\]\([^)\s]*\)")
LINK_ADDRESS = re.compile(r"(?:evernote|https?)://\S+")


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


CHALLENGES_LINK = re.compile(r"\[\d{4}-\d{2}-\d{2} Life (?:Challenges|Problems)\]\(evernote:///view/")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<![\d.-])0\d{1,2}[-.]\d{3,4}[-.]\d{4}(?![\d.-])")
ACTION_SECTIONS = ("your decisions", "decisions", "hand to me", "quick wins")


ITEM = re.compile(r"(?:[-*]|\d+[.)])\s+")


def challenges_items(md: str) -> list[str]:
    """Every decision question with its options or answers, and every Hand to me row, of a Life Challenges note.

    Reads both layouts: a decision as a bullet ending in "?" with its options indented under it, anywhere
    outside the Takeaway (the goal sections, from 2026-11-07), and the earlier "Your decisions" sections with
    numbered options under a question line.
    """
    out, h2, table, q_indent = [], "", 0, None
    for line in md.splitlines():
        m = re.match(r"##\s+(.*)", line)
        if m:
            h2, table, q_indent = m.group(1).strip().lower(), 0, None
            continue
        if h2.startswith("takeaway"):
            continue
        s = line.strip()
        if s.startswith("|"):
            table += 1
            if h2.startswith(("hand to me", "quick wins")) and table > 2:  # header and separator skipped
                out.append(" ".join(c.strip() for c in s.strip("|").split("|")))
            continue
        table = 0
        if not s or s.startswith("#"):
            continue
        indent, text = len(line) - len(line.lstrip()), ITEM.sub("", s, count=1)
        if s.endswith("?"):
            out.append(text)
            q_indent = indent
        elif q_indent is not None and indent > q_indent and ITEM.match(s):
            out.append(text)
        elif re.match(r"\d+[.)]\s", s) and h2.startswith(ACTION_SECTIONS):
            out.append(text)
        else:
            q_indent = None
    return out


def _overview_actions(draft: str, challenges: str | None) -> list[str]:
    out = []
    for title, _ in sections(draft):
        if title.lower().startswith("open tasks"):
            out.append(f"T3 an Open tasks section: the next moves live in the Life Challenges note; "
                       f"link it under '## Your decisions' instead: {title!r}")
    for line in draft.splitlines():
        if line.lstrip().startswith("!["):
            continue
        for hit in EMAIL.findall(line) + PHONE.findall(line):
            out.append(f"T3 a contact belongs in the Life Challenges note, with its step: {hit!r} in {line.strip()[:70]!r}")
    if not CHALLENGES_LINK.search(draft):
        out.append("T3 no link to the current Life Challenges note")
    for b in takeaway_bullets(draft) if challenges else []:
        claim = re.sub(r"\[[^\]]*\]\([^)]*\)", "", b)  # a link's title and address are not the bullet's words
        bw = {w for w in words(claim) if not w.isdigit()}
        for item in challenges_items(challenges):
            rw = {w for w in words(item) if not w.isdigit()}
            shared = len(bw & rw)
            if bw and rw and shared / len(rw) >= 0.5 and shared / len(bw) >= 0.3:
                out.append(f"T3 Takeaway bullet repeats the Life Challenges note: {b!r} ~ {item!r}")
                break
    return out


GROUND_NUMBER = re.compile(r"\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?")
NOT_NAMES = set("""You Your Yours The This That These Those Its It And But Or So If When Where What Which Who
Why How Detail Details See Today Tomorrow Yesterday Takeaway Monday Tuesday Wednesday Thursday Friday Saturday
Sunday January February March April May June July August September October November December Jan Feb Mar Apr
Jun Jul Aug Sep Sept Oct Nov Dec After Before Since From Until With Without For Each Every One Two Three Four
Five Six Seven Eight Nine Ten All Both Most Some Any No Not Only Also Then Than More Less Your Here There
In On At By Of To As Is Are Was Were Be Been Has Have Had Do Does Did Can Could Will Would Should Must May
Might Life Overview Challenges Decisions Evernote AUD USD KRW EUR DPS LDL HDL Korea Korean""".split())


def _sources_blocks(sources: str) -> dict[str, str]:
    """Each heading's lines; an h3 block also counts toward its h2 parent."""
    blocks: dict[str, list[str]] = {}
    h2 = h3 = ""
    for line in sources.splitlines():
        m = re.match(r"(#{2,3})\s+(.*)", line)
        if m:
            if len(m.group(1)) == 2:
                h2, h3 = m.group(2).strip().lower(), ""
            else:
                h3 = m.group(2).strip().lower()
            continue
        blocks.setdefault(h2, []).append(line)
        if h3:
            blocks.setdefault(h3, []).append(line)
    return {k: "\n".join(v) for k, v in blocks.items()}


def _claims(text: str) -> tuple[set[str], set[str]]:
    """Numbers and names in a text, link targets and markup removed."""
    plain = re.sub(r"\[[^\]]*\]\(evernote:[^)]*\)", "", text)
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", plain).replace(",", "")
    nums = set(GROUND_NUMBER.findall(plain))
    words = re.findall(r"(?<![.!?:]\s)(?<!^)(?<!- )\b[A-Z][A-Za-z-]{2,}\b|[가-힣]{2,}", plain, re.M)
    return nums, {w for w in words if w not in NOT_NAMES}


def _grounding(draft: str, sources: str) -> list[str]:
    """T19: a number or a name in a section that the section's own block of sources.md does not hold.

    Each section of the note is a retelling of the record lines copied under its heading in
    sources.md (a computed number appears there as a "computed:" line with its arithmetic). A
    name or number found only elsewhere in the record is the joining that produced "Jaekeun
    signed the transfers" (2026-11-08); the Takeaway may draw on every block.
    """
    blocks = _sources_blocks(sources)
    everything = "\n".join(blocks.values()).replace(",", "")
    out = []
    for title, body in sections(draft):
        if title.lower().startswith("your decisions"):
            continue
        pool = everything if title.lower().startswith("takeaway") else blocks.get(title.lower(), "").replace(",", "")
        if not pool.strip():
            out.append(f"T19 section {title!r} has no block in sources.md: copy the lines it retells under '## {title}'")
            continue
        nums, names = _claims(body)
        have_nums = set(GROUND_NUMBER.findall(pool))
        missing = sorted(n for n in nums if n not in have_nums) + sorted(n for n in names if n not in pool)
        if missing:
            out.append(f"T19 not in the sources of {title!r}: {', '.join(missing)} (copy the line that states it, "
                       f"add a 'computed:' line, or cut it)")
    return out


def check(draft: str, original: str | None = None, linked: list[str] | None = None,
          facts_only: bool = False, note: bool = False, cuts: str | None = None,
          labels: str | None = None, table_titles: bool = False,
          challenges: str | None = None, sources: str | None = None,
          verbatim: str | None = None, person: str | None = None) -> list[str]:
    """`verbatim` is text Chaehan wrote that the note carries as he wrote it: its lines are exempt from the form
    checks (T5, T12, T13, T16), and T20 fails when one of its sentences is missing or changed.

    `person` names the woman a date note is about (the date-analysis skill). Chaehan, 2026-11-12, chose that in
    such a note "she may lead": "she", "her" and her name count as a subject in T13 and T15 beside "you". T12's
    cap of seven items stays (Chaehan, 2026-11-12, of the first date-3 note: "no quality over quantity")."""
    fails: list[str] = []
    is_v = _verbatim_test(verbatim)
    pool = list(linked or [])
    if challenges:
        pool.append(challenges)
    if cuts:
        fails += _bad_cuts(cuts)
        pool.append(cuts)
    if facts_only or note:
        if note:
            fails += _prose_sections(draft, is_v)
            fails += _empty_items(draft)
            fails += _summary(draft)
            extra = person_words(person)
            fails += _flat_lists(draft, is_v)
            fails += _gists(draft, is_v, extra)
            fails += _summary_subjects(draft, extra)
            fails += _wording(draft, is_v)
            if verbatim:
                fails += _verbatim_kept(draft, verbatim)
            if table_titles:
                fails += _table_titles(draft)
            if labels is not None:
                fails += _labels(draft, labels)
            if original is not None:
                fails += _lost_rows(draft, original, cuts)
        return fails + (_facts(draft, original, pool) if original is not None else [])
    fails += _overview_actions(draft, challenges)
    if sources is not None:
        fails += _grounding(draft, sources)
    if not LINK.search(draft):
        fails.append("T4 the note carries no evernote:/// link")
    for title, body in sections(draft):
        if title.lower().startswith(NO_LINK_SECTIONS) or not body.strip():
            continue
        if not LINK.search(body) and "no detail note" not in body.lower():
            fails.append(f"T4 section without a link to its detail note: {title!r}")
    if not re.search(r"^[ \t]{2,}- ", draft, re.M):
        fails.append("T5 no indented bullet: every point is a sibling")
    # T18: in 9 DeepSeek runs of 2026-11-08, 3 wrote "10,000,000 won" against the
    # skill's "no thousand separators"; a rule the model drops gets a check.
    for line in draft.splitlines():
        if line.lstrip().startswith("![") or "evernote:///" in line and not re.sub(r"\]\([^)]*\)", "", line).strip():
            continue
        for hit in re.findall(r"(?<![\d.,])\d{1,3}(?:,\d{3})+(?![\d])", re.sub(r"\]\([^)]*\)", "]", line)):
            fails.append(f"T18 a thousand separator: {hit!r} in {line.strip()[:60]!r}")
    # T6 (every number of the previous snapshot survives) no longer runs on a
    # life overview: in six DeepSeek runs of 2026-11-07 it fired every time and
    # its fixes put the clutter back (booking figures, apartment prices, the
    # wrong gluten dates of failure 186). T5 was removed with it and came back
    # on 2026-11-08: the first note built without it had no sub-bullet at all.
    return fails


# ---- Chaehan's own words (2026-11-10: the gate turned his feedback paragraph into six bullets and demanded a
# lead line; "Fix the gate so it stops reshaping your verbatim words" - "Yes, fix it") ----

def _flat(text: str) -> str:
    """Text as words only: list markers, heading marks, markdown and line breaks gone, lower case."""
    lines = [re.sub(r"^\s*(?:[-*+]|\d+[.)]|#{1,6})\s+", "", l) for l in text.splitlines()]
    return " ".join(_plain(" ".join(lines)).split()).lower()


def _verbatim_test(verbatim: str | None):
    """A test for one line of the draft: True when it is Chaehan's own words, copied from `verbatim`."""
    if not verbatim:
        return lambda line: False
    whole = _flat(verbatim)

    def is_v(line: str) -> bool:
        f = _flat(line)
        return len(f.split()) >= 3 and f in whole
    return is_v


def _verbatim_kept(draft: str, verbatim: str) -> list[str]:
    """T20: every paragraph Chaehan wrote is in the draft as one unbroken run of his words.

    A paragraph may become list items (markers and line breaks do not count), but a word added, changed or
    dropped breaks the run, and the sentence where it breaks is named."""
    have = _flat(draft)
    out = []
    for para in re.split(r"\n\s*\n|\n(?=\s*(?:[-*+]|\d+[.)])\s)", verbatim):
        if not _flat(para) or _flat(para) in have:
            continue
        sents = [s for s in re.split(r"(?<=[.!?])\s+", para.strip()) if _flat(s)]
        bad = next((s for s in sents if _flat(s) not in have), None)
        if bad is None:  # each sentence is there, but something stands between two of them
            bad = next((s for prev, s in zip(sents, sents[1:]) if _flat(prev + " " + s) not in have), sents[0])
        out.append(f"T20 your words are missing or changed: {bad.strip()[:70]!r}; keep them as you wrote them")
    return out


def _prose_sections(md: str, is_v=lambda l: False) -> list[str]:
    out = []
    for title, body in sections(md):
        lines = [l for l in body.splitlines() if l.strip() and not is_v(l)]
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


def _flat_lists(md: str, is_v=lambda l: False) -> list[str]:
    out = []
    for title, body in sections(md):
        body = "\n".join(l for l in body.splitlines() if not is_v(l))  # his own list counts as he wrote it
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


def person_words(person: str | None) -> frozenset[str]:
    """The subject words a date note about `person` may lead with: she, her, and each part of her name."""
    if not person:
        return frozenset()
    names = {p.lower() for p in re.findall(r"[A-Za-z'-]+", person)}
    return frozenset({"she", "her", "hers", "she's", "she'll"} | names | {n + "'s" for n in names})


def seat(sentence: str, extra: frozenset[str] = frozenset()) -> bool:
    """True when the sentence's subject is you, your thing, or an imperative (or, in a date note, she)."""
    subj = YOU | extra
    for clause in re.split(r"[,:;]", sentence):
        w = re.findall(r"[a-z0-9'-]+", clause.lower())
        if not w:
            continue
        if w[0] in IMPERATIVE or subj & set(w[:2]):
            return True
        if w[0] in LEAD or re.match(r"\d", w[0]):
            if subj & set(w[:8]):
                return True
            continue
        return False
    return False


def _gists(md: str, is_v=lambda l: False, extra: frozenset[str] = frozenset()) -> list[str]:
    out = []
    for title, body in sections(md):
        if title.lower().startswith(SUMMARY_HEADS):
            continue
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        if not lines or all(l.startswith("|") for l in lines):
            continue  # empty, or an H3 that titles one table
        if is_v(lines[0]):
            continue  # a section that opens with his own words opens as he wrote it
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
        elif not seat(sent, extra):
            out.append(f"T13 section {title!r} opens on an object, not on you: {sent[:60]!r}. Write it with you, "
                       f"your thing or an action as subject: rejected 'Osaka city has no soapland district.', "
                       f"accepted 'You will find no soapland district in Osaka city.'")
    return out


def _summary_subjects(md: str, extra: frozenset[str] = frozenset()) -> list[str]:
    out = []
    summ = [b for t, b in sections(md) if t.lower().startswith(SUMMARY_HEADS)]
    if not summ:
        return out
    for line in _bullets(summ[0]):
        titles = {t.strip() for t in re.findall(r"\[([^\]]+)\]\([^)]*\)", line)}
        for sent in _sentences(line):
            if len(sent.split()) < 4 or sent.rstrip(".") in titles:
                continue
            if not seat(sent, extra):
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


def _wording(md: str, is_v=lambda l: False) -> list[str]:
    lint = _lint()
    lines = md.splitlines()
    table = lambda n: lines[n - 1].lstrip().startswith("|")
    out = [f"T16 line {n}: '{words_}' - {fix}" for n, level, words_, fix in lint.lint_text(md, lint.load_robot_markers())
           if level == "flag" and not table(n) and not is_v(lines[n - 1])]
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


def stamp_dirs() -> list[Path]:
    """Every folder a stamp may sit in: the main one, then the fallback a sandboxed agent can write.

    Claude Code's sandbox refuses writes to ~/.local/state and allows ~/.cache, so a gate run there stamped
    nothing and needed the sandbox lifted (2026-11-10). $NOTE_GATE_STAMPS (tests) names the one folder."""
    if os.environ.get("NOTE_GATE_STAMPS"):
        return [stamp_dir()]
    return [stamp_dir(), Path.home() / ".cache/agentkit/note-gate"]


def stamped(text: str) -> bool:
    """Whether this text passed the gate: its stamp exists in any stamp folder."""
    key = stamp_key(text)
    return any((d / key).exists() for d in stamp_dirs())


def stamp_key(text: str) -> str:
    """The contract with the Evernote CLI: SHA-256 of the text without image lines, ends stripped."""
    body = "\n".join(l for l in text.splitlines() if not re.fullmatch(r"\s*!\[[^\]]*\]\([^)]*\)\s*", l))
    return hashlib.sha256(body.strip().encode()).hexdigest()


def stamp(text: str) -> Path:
    """Record that this text passed the gate (the Evernote CLI and the note-gate plugin read it)."""
    err = None
    for d in stamp_dirs():
        try:
            d.mkdir(parents=True, exist_ok=True)
            f = d / stamp_key(text)
            f.touch()
            return f
        except OSError as e:  # a folder the sandbox refuses: try the next one
            err = e
    raise SystemExit(f"The gate passed, but no stamp folder can be written ({err}). Run the same command "
                     f"outside the sandbox.")


def _facts(draft: str, original: str, linked: list[str] | None) -> list[str]:
    """Numbers of the original found neither in the draft, a linked note, nor the cut list."""
    def plain(text: str) -> str:  # a link's address is not a fact: drop it, keep its title
        return LINK_ADDRESS.sub("", LINK_TARGET.sub("]", text)).replace(",", "")
    have = set(FACT.findall(plain(draft + "\n" + "\n".join(linked or []))))
    return [f"T6 fact lost: {f}" for f in sorted(set(FACT.findall(plain(original))) - have)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--original")
    ap.add_argument("--linked", nargs="*", default=[])
    ap.add_argument("--facts-only", action="store_true", help="any note: only check that no date or number of --original is lost")
    ap.add_argument("--note", action="store_true", help="any note: facts, lists, summary size and duplicates (T5-T12)")
    ap.add_argument("--cuts", help="the cut list: one line per removal, '- <numbers or words>: <destination or reason>'")
    ap.add_argument("--labels", help="note_build.py's merged label file: id, label, parent, text per item")
    ap.add_argument("--challenges", help="the current Life Challenges note, exported: T3 compares the Takeaway with it")
    ap.add_argument("--sources", help="sources.md: the record lines each section retells; T19 checks every name and number against them")
    ap.add_argument("--verbatim", help="Chaehan's own words the note carries as he wrote them: exempt from the form "
                    "checks, and T20 fails when one of their sentences is missing or changed")
    a = ap.parse_args(argv)
    read = lambda p: open(p, encoding="utf-8").read()
    draft = read(a.draft)
    fails = check(draft, read(a.original) if a.original else None, [read(p) for p in a.linked],
                  a.facts_only, a.note, read(a.cuts) if a.cuts else None, read(a.labels) if a.labels else None,
                  challenges=read(a.challenges) if a.challenges else None,
                  sources=read(a.sources) if a.sources else None,
                  verbatim=read(a.verbatim) if a.verbatim else None)
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
