#!/usr/bin/env python3
"""Check the fact cards of a note's build folder (build spec step 2).

A card is one fact of Chaehan's record in seven fields, one row of cards.tsv
with the note section and the card's id in front:

    section  id  kind  thing  fact  so  do  said  src

  kind   measure, state, act, cond, open, todo or instr
  thing  what the line is about, named so a stranger knows which one
  fact   what is true of the thing; thing + fact reads as one sentence
  so     what follows for Chaehan, only when the record says it
  do     the action, for todo and instr only; a card has so or do, never both
  said   the date on which Chaehan stated the fact himself
  src    the record line, as memory/health.md:96

Each refusal names the card, the field, the rule and the fix. A `so` that
repeats its fact is emptied in the file, since that is the only fix. The
record line of `src` is read from sources.md when the note has one (its lines
read "memory/health.md:96 | <the line>"), else from the file itself.

    python3 scripts/card_check.py <build>/cards.tsv --sources sources.md
    python3 scripts/card_check.py <build>/cards.tsv --root ~/Software/Prototypes/socrates

Exit 1 when a card is refused.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import re
import sys
from typing import NamedTuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("section", "id", "kind", "thing", "fact", "so", "do", "said", "src")
KINDS = ("measure", "state", "act", "cond", "open", "todo", "instr")
ACTION_KINDS = ("todo", "instr")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
# The fact continues the sentence the thing starts ("your antibiotic course" + "ended after 7 days"),
# so it opens on a verb, never on a word that starts a new subject.
NEW_SUBJECT = {"the", "a", "an", "it", "its", "this", "that", "their", "his", "her", "there"}
# A `do` opens on its verb: "renew the parking permit". The gate's IMPERATIVE list is too short for
# this test (it lacks "renew", the fill prompt's own example, and "exclude"), so the card is refused
# only when the first word cannot start an action: a pronoun, an article, a modal, "to" or "not".
NOT_A_VERB = {"you", "your", "i", "we", "he", "she", "they", "it", "its", "my", "his", "her", "their", "our",
              "the", "a", "an", "this", "that", "these", "those", "there", "to", "not", "no", "must",
              "should", "can", "could", "will", "would", "may", "might", "shall", "please"}
STOP = set("""the a an of to in on at and or so is are was were be been being it its your you yours that
this these those with for from which as by can could will would may might must not no his her their there
them they he she we i me my our do does did has have had if then than also only still just""".split())
MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
MONTH_DATE = re.compile(r"\b(?:(?P<d1>\d{1,2})\s+(?P<m1>[A-Z][a-z]{2,8})\.?,?\s+(?P<y1>\d{4})"
                        r"|(?P<m2>[A-Z][a-z]{2,8})\.?\s+(?P<d2>\d{1,2}),?\s+(?P<y2>\d{4}))\b")


class Refusal(NamedTuple):
    card: str
    field: str
    rule: str
    text: str

    def __str__(self) -> str:
        return f"{self.card} {self.field}: {self.text}"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cache: dict[str, object] = {}


def _note_build():
    if "nb" not in _cache:
        _cache["nb"] = _load("note_build", ROOT / "skills" / "evernote" / "scripts" / "note_build.py")
    return _cache["nb"]


def lint_rules():
    if "rules" not in _cache:
        _cache["lint"] = _load("wording_lint", ROOT / "scripts" / "wording_lint.py")
        _cache["rules"] = _cache["lint"].load_robot_markers()
    return _cache["rules"]


# ---- cards.tsv ----------------------------------------------------------------

def read_cards(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return [{k: (r.get(k) or "").strip() for k in FIELDS} | ({"reason": r["reason"]} if r.get("reason") else {})
                for r in csv.DictReader(fh, delimiter="\t")]


def write_cards(path: Path, cards: list[dict], extra: tuple[str, ...] = ()) -> None:
    cols = FIELDS + extra
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar="\\")
        w.writerow(cols)
        for c in cards:
            w.writerow([str(c.get(k, "")).replace("\t", " ").replace("\n", " ") for k in cols])


def read_sources(path: Path | None) -> dict[str, str]:
    """The record lines of sources.md by location: "memory/health.md:96 | <line>"."""
    out: dict[str, str] = {}
    if not path or not Path(path).exists():
        return out
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        m = re.match(r"\s*(?:[-*]\s+)?(\S+:\d+)\s+\|\s+(.*)", line)
        if m:
            out[m.group(1)] = m.group(2)
        out[f"sources.md:{n}"] = line
    return out


def source_text(src: str, sources: dict[str, str], root: Path) -> str | None:
    if src in sources:
        return sources[src]
    m = re.fullmatch(r"(.+):(\d+)", src)
    if not m:
        return None
    path = root / m.group(1)
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    n = int(m.group(2))
    return lines[n - 1] if 1 <= n <= len(lines) else None


# ---- the rules ------------------------------------------------------------------

def _with_iso_dates(text: str) -> str:
    """The text with each date written in words ("June 3, 2026") also written as 2026-06-03."""
    extra = []
    for m in MONTH_DATE.finditer(text):
        mon = (m.group("m1") or m.group("m2"))[:3].lower()
        if mon in MONTHS:
            day = m.group("d1") or m.group("d2")
            year = m.group("y1") or m.group("y2")
            extra.append(f"{year}-{MONTHS[mon]:02d}-{int(day):02d}")
    return text + ("\n" + " ".join(extra) if extra else "")


def content_words(text: str) -> set[str]:
    words = (w.strip(".:,;'-") for w in re.findall(r"[a-z0-9$¥€.:,'-]+|[가-힣]+", text.lower().replace(",", "")))
    return {w for w in words if w and w not in STOP}


def so_repeats(card: dict) -> bool:
    """True when at most half of the content words of `so` are new against thing and fact."""
    so = content_words(card["so"])
    if not so:
        return bool(card["so"].strip())
    new = so - content_words(card["thing"] + " " + card["fact"])
    return len(new) * 2 <= len(so)


def check_card(card: dict, src: str | None, rules) -> tuple[list[Refusal], bool]:
    """The refusals of one card, and whether its `so` repeats its fact (the caller empties it)."""
    cid = card.get("id") or "?"
    out: list[Refusal] = []

    def refuse(field: str, rule: str, text: str) -> None:
        out.append(Refusal(cid, field, rule, text))

    kind, thing, fact, so, do, said = (card[k] for k in ("kind", "thing", "fact", "so", "do", "said"))
    if kind not in KINDS:
        refuse("kind", "kind", f"{kind!r} is no kind: write one of {', '.join(KINDS)}")
    if not re.search(r"\byou(?:r)?\b|\b[A-Z][A-Za-z-]+|\d|[가-힣]", thing):
        refuse("thing", "which one", f"{thing!r} does not say which one: name it by 'your', its name, its date "
                                     f"or its place (\"the daily iron tablet\", never \"the tablet\")")
    if kind not in ACTION_KINDS and not fact:
        refuse("fact", "fact", "the card has no fact: write what is true of the thing, starting with its verb")
    first = (re.findall(r"[a-z']+", fact.lower()) or [""])[0]
    if fact and first in NEW_SUBJECT:
        refuse("fact", "continues the thing", f"{fact!r} starts with {first!r}: start with the verb, so that "
                                             f"\"{thing} {fact}\" reads as one sentence")
    if kind in ACTION_KINDS and not do:
        refuse("do", "do", f"a {kind} card has no 'do': write the action, starting with its verb")
    if do and kind not in ACTION_KINDS:
        refuse("do", "do", f"'do' belongs to todo and instr cards: this {kind} card says it under 'so', or drops it")
    verb = (re.findall(r"[a-z']+", do.lower()) or [""])[0]
    if do and verb in NOT_A_VERB:
        refuse("do", "starts with a verb", f"{do!r} starts with {verb!r}: write the action as its verb first "
                                           f"(\"renew the parking permit\")")
    if so and do:
        refuse("so", "so or do", "the card has both 'so' and 'do': keep 'do' for todo and instr, 'so' for the rest")
    if said and not DATE.fullmatch(said):
        refuse("said", "date", f"{said!r} is no date: write YYYY-MM-DD or leave it empty")
    for field in ("thing", "fact", "so", "do"):
        value = card[field]
        if not value:
            continue
        nb = _note_build()
        seen: set[str] = set()
        for m in nb.SEPARATOR.finditer(value):
            seen.add(m.group(0).lower())
            refuse(field, "separator", f"{m.group(0)!r} has a thousand separator: write {m.group(0).replace(',', '')}")
        for m in nb.APPROX.finditer(value):
            seen.add(m.group(0).strip().lower())
            refuse(field, "about", f"{m.group(0).strip()!r} before a number: write ~N (~25 years)")
        for _line, level, match, fix in _cache["lint"].lint_text(value, rules):
            if level == "flag" and match.strip().lower() not in seen:
                refuse(field, "wording", f"{match.strip()!r}: {fix}")
    if src is None:
        refuse("src", "exists", f"{card.get('src')!r} is no record line: write the file and line, as memory/health.md:96")
        return out, False
    grounded = _with_iso_dates(src)
    if said and said not in grounded:
        refuse("said", "in the record", f"{said} is not in the record line: 'said' holds the date on which "
                                        f"the line says Chaehan stated the fact, or stays empty")
    nb = _note_build()
    for field in ("thing", "fact", "so", "do"):
        if card[field]:
            bad = [w for w in nb.invented(card[field], grounded) if w not in ("You", "Your")]
            if bad:
                refuse(field, "in the record", f"{', '.join(bad)} is not in the record line {card['src']}: "
                                               f"copy it as the line has it, or cut it")
    return out, bool(so) and so_repeats(card)


def check_file(path: Path, sources: Path | None = None, root: Path | None = None) -> tuple[list[Refusal], list[str]]:
    """Check every card of cards.tsv; empty each `so` that repeats its fact, and write the file back."""
    rules = lint_rules()
    cards = read_cards(path)
    smap = read_sources(sources)
    root = Path(root) if root else Path.cwd()
    refusals: list[Refusal] = []
    emptied: list[str] = []
    for card in cards:
        out, repeats = check_card(card, source_text(card["src"], smap, root), rules)
        refusals += out
        if repeats:
            card["so"] = ""
            emptied.append(card["id"])
    if emptied:
        write_cards(path, cards)
    return refusals, emptied


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", type=Path, help="the build folder's cards.tsv")
    ap.add_argument("--sources", type=Path, help="the note's sources.md, which holds the record lines")
    ap.add_argument("--root", type=Path, help="where a src path such as memory/health.md starts (default: here)")
    a = ap.parse_args(argv)
    refusals, emptied = check_file(a.cards, a.sources, a.root)
    for cid in emptied:
        print(f"  {cid} so: emptied, it repeats the fact")
    for r in refusals:
        print(f"  {r}")
    n = len(read_cards(a.cards))
    print(f"card_check: {n} cards, {len(refusals)} refused, {len(emptied)} 'so' emptied")
    return 1 if refusals else 0


if __name__ == "__main__":
    sys.exit(main())
