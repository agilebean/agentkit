#!/usr/bin/env python3
"""Write the lines of one note section from its fact cards (build spec step 3).

One request per section. Its system message is wording_writer_prompt.md (the
rules) followed by wording_writer_examples.md (eight card and line pairs
Chaehan accepted, kept with his other private data in socrates, under
docs/human quality/data); its user message is the section's
cards, one per line. Nothing else goes in: no skill, no memory file, no source
line. A pair whose `thing` shares a word with a card's `thing` is swapped for
the next unused row of wording_pairs.tsv, so a pair about the note's own topic
is not copied into the note.

Each line is then checked against its card:
  - every number and name of the card is in the line, and the line has none the card lacks
  - no "must", "have to", "need to" or "should", and no opening imperative, unless the card has a `do`
  - no six words in a row from the prompt
  - no flag of wording_lint.py (a warn is reported, since one accepted line has one)
A line that fails is asked for once more, with the reasons. When it fails again,
the script writes it from the card's fields.

    python3 scripts/say.py <build>/cards.tsv --section "Health" [--out <build>/lines.tsv] [--literal]

--literal asks a fresh call, for each line, what literally happens in it (step 4)
and lists the lines it cannot say. The list is for Chaehan; it stops nothing.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Chaehan's labelled lines and accepted examples are private: they live in socrates, never in this public repository.
DATA = Path(os.environ.get("HUMAN_QUALITY_DATA")
            or Path.home() / "Software" / "Prototypes" / "socrates" / "docs" / "human quality" / "data")
PROMPT = ROOT / "wording_writer_prompt.md"
EXAMPLES = DATA / "wording_writer_examples.md"
PAIRS = DATA / "wording_pairs.tsv"
LITERAL = ROOT / "wording_literal_prompt.md"
MODEL = "deepseek/deepseek-v4.1-flash"
NO_ANSWER = "no answer"
PAIRS_HEAD = "Cards and the lines Chaehan accepted for them:\n\n"
GROUPS_HEAD = "\n\nCards that share an id make one line together:\n\n"
TAIL = "\n\nReturn one line per id below: the id, a tab, the line."
NUMBER = re.compile(r"\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?")
NAME = re.compile(r"\b[A-Z][A-Za-z-]{2,}\b|[가-힣]{2,}")
OBLIGATION = re.compile(r"\b(?:must|have to|has to|had to|need to|needs to|should|ought to)\b", re.I)
# Words of four letters or more that say nothing about a topic: "your 400 m" and "your gym" share no topic.
FILLER = set("""your yours with from that this these those their there them they were been have has had
which when where what into onto only than then also just still more most very each every""".split())
NOT_NAMES = set("""You Your Yours I The A An This That These Those It Its If When Where What Which Who How
Why On In At By From For With Without Before After Until Since Once While Because Although Though Unless
Whether So And But Or Then Both Each Every All No None Nothing There Here Now Today She He Her His They
Their We Our Is Are Was Were Do Does Did Can Could Will Would Should May Might Must""".split())


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cache: dict[str, object] = {}


def _mod(name: str):
    paths = {"card_check": ROOT / "scripts" / "card_check.py",
             "wording_lint": ROOT / "scripts" / "wording_lint.py",
             "overview_gate": ROOT / "skills" / "life-overview" / "scripts" / "overview_gate.py"}
    if name not in _cache:
        _cache[name] = _load(name, paths[name])
    return _cache[name]


def _rules():
    if "rules" not in _cache:
        _cache["rules"] = _mod("wording_lint").load_robot_markers()
    return _cache["rules"]


def complete(messages: list[dict], model: str | None = None, max_tokens: int = 16000, temperature: float = 0.3) -> str:
    """One call through agentkit's OpenCode Go route; --model, then FAST_MODEL, then MODEL."""
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    from agentkit.llm import complete as _complete
    if model:
        os.environ["FAST_MODEL"] = model
    os.environ.setdefault("FAST_MODEL", MODEL)
    try:
        return _complete(messages, alias="fast", max_tokens=max_tokens, temperature=temperature)
    except Exception:  # a stream that ends empty (seen 2026-11-17, 1 of 60 calls) gets one more try
        return _complete(messages, alias="fast", max_tokens=max_tokens, temperature=temperature)


# ---- cards and pairs -------------------------------------------------------------

def load_pairs(path: Path = PAIRS) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE) if r.get("id")]


def pair_card(row: dict) -> dict:
    return {"section": "", "id": row["id"], "kind": row["kind"], "thing": row["thing"], "fact": row["fact"],
            "so": row["so"], "do": row["do"], "said": "", "src": f"wording_pairs.tsv:{row['id']}"}


def card_text(card: dict) -> str:
    """kind=... | thing=... | fact=... | so=... | do=..., an empty field left out."""
    parts = [f"kind={card['kind']}", f"thing={card['thing']}"]
    return " | ".join(parts + [f"{k}={card[k]}" for k in ("fact", "so", "do") if card.get(k)])


def prompt_text() -> str:
    """The writer prompt as tested and sent: the rules of PROMPT, then the examples of EXAMPLES."""
    return PROMPT.read_text(encoding="utf-8") + EXAMPLES.read_text(encoding="utf-8")


def split_prompt(text: str | None = None) -> tuple[str, list[str], str]:
    """The prompt's rules, the ids of the single-card pairs it shows in order, and its block of lines made of
    several cards (2026-11-20: one card a sentence made a bullet of three facts read as three sentences)."""
    text = prompt_text() if text is None else text
    head, rest = text.split(PAIRS_HEAD, 1)
    block, rest = rest.split(GROUPS_HEAD, 1)
    groups = rest.split(TAIL, 1)[0]
    by_card = {card_text(pair_card(r)): r for r in load_pairs()}
    ids = []
    for m in re.finditer(r"^card: (.*)\nline: (.*)$", block, re.M):
        card, line = m.group(1), m.group(2)
        row = by_card.get(card)
        if row is None:
            raise SystemExit(f"say.py: the prompt's pair {card!r} is not a row of {PAIRS.name}")
        if line != row["line"]:
            raise SystemExit(f"say.py: the prompt's line for {row['id']} is not the row's: "
                             f"{line!r} != {row['line']!r}")
        ids.append(row["id"])
    return head, ids, groups


def build_prompt(head: str, pairs: list[dict], groups: str) -> str:
    shown = "\n\n".join(f"card: {card_text(pair_card(r))}\nline: {r['line']}" for r in pairs)
    return head + PAIRS_HEAD + shown + GROUPS_HEAD + groups + TAIL + "\n"


def _topic(thing: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", thing.lower()) if w not in FILLER}


def choose_pairs(cards: list[dict]) -> tuple[list[dict], list[tuple[str, str | None]]]:
    """The prompt's pairs with each one that shares a topic word with a card swapped for an unused row."""
    rows = load_pairs()
    by_id = {r["id"]: r for r in rows}
    _head, shown, _groups = split_prompt()
    topics = set().union(*(_topic(c["thing"]) for c in cards)) if cards else set()
    sent = {c["id"] for c in cards}
    used = set(shown)
    chosen, swapped = [], []
    for pid in shown:
        if not _topic(by_id[pid]["thing"]) & topics:
            chosen.append(by_id[pid])
            continue
        spare = next((r for r in rows if r["id"] not in used and r["id"] not in sent
                      and not _topic(r["thing"]) & topics), None)
        swapped.append((pid, spare["id"] if spare else None))
        if spare:
            used.add(spare["id"])
            chosen.append(spare)
    return chosen, swapped


def line_id(card: dict) -> str:
    """The id of the line a card belongs to: its own id unless it shares a line with other cards."""
    return card.get("line") or card["id"]


def user_message(cards: list[dict], refused: dict[str, tuple[str, list[str]]] | None = None) -> str:
    msg = "Cards:\n" + "\n".join(f"{line_id(c)}\t{card_text(c)}" for c in cards)
    for lid, (line, reasons) in (refused or {}).items():
        msg += (f"\n\nYour line for {lid} was refused: {line}\nWhy: {'; '.join(reasons)}.\n"
                f"Write the line again from its cards.")
    return msg


def parse_answer(text: str, ids: list[str]) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        m = re.match(r"\s*[-*]?\s*([A-Za-z]+\d+)\s*(?:\t|:\s|\s)\s*(.+)$", line)
        if m and m.group(1) in ids and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip()
    return out


# ---- the line checks ---------------------------------------------------------------

def _numbers(text: str) -> set[str]:
    return set(NUMBER.findall(text.replace(",", "")))


def _sentence_starts(text: str) -> set[int]:
    starts = {0}
    for m in re.finditer(r"[.!?]\s+", text):
        starts.add(m.end())
    return starts


def _names(text: str, skip_starts: bool) -> set[str]:
    starts = _sentence_starts(text) if skip_starts else set()
    return {m.group(0) for m in NAME.finditer(text) if m.group(0) not in NOT_NAMES and m.start() not in starts}


def _shingles(text: str, n: int = 6) -> set[tuple]:
    w = re.findall(r"[a-z0-9¥€$']+", text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def check_line(line: str, card: dict | list[dict], prompt: str) -> tuple[list[str], list[str]]:
    """(the reasons the line fails, the lint warns it only reports), for one card or the cards of one line."""
    cards = card if isinstance(card, list) else [card]
    fields = " ".join(c[k] for c in cards for k in ("thing", "fact", "so", "do") if c.get(k))
    card = {"do": " ".join(c.get("do", "") for c in cards).strip()}
    fails = []
    lost = sorted(_numbers(fields) - _numbers(line)) + sorted(n for n in _names(fields, False) if n not in line)
    if lost:
        fails.append(f"it loses {', '.join(lost)}, which the card has: copy it exactly")
    added = sorted(_numbers(line) - _numbers(fields)) + sorted(n for n in _names(line, True) if n not in fields)
    if added:
        fails.append(f"it adds {', '.join(added)}, which the card lacks: write only what the card holds")
    if not card.get("do"):
        m = OBLIGATION.search(line)
        if m and not re.search(rf"\b{re.escape(m.group(0))}\b", fields, re.I):
            fails.append(f"it says {m.group(0)!r}, but the card has no 'do': state the fact as the card does")
        first = (re.findall(r"[a-z']+", line.lower()) or [""])[0]
        if first in _mod("overview_gate").IMPERATIVE and not re.match(rf"(?i)\s*{first}\b", fields):
            fails.append(f"it opens on the instruction {first!r}, but the card has no 'do': "
                         f"open with what the line is about")
    own = _shingles(fields + " " + " ".join(script_line(c) for c in cards))
    if (_shingles(line) & _shingles(prompt)) - own:
        fails.append("it copies six words in a row from the examples: write it from the card")
    warns = []
    for _n, level, match, fix in _mod("wording_lint").lint_text(line, _rules()):
        (fails if level == "flag" else warns).append(f"{match.strip()!r}: {fix}")
    return fails, warns


# ---- the line the script writes ----------------------------------------------------

def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def script_line(card: dict) -> str:
    """The card's own words as a line: the last resort after two failed answers."""
    kind, thing, fact, so, do = (card.get(k, "").strip().rstrip(".") for k in ("kind", "thing", "fact", "so", "do"))
    if kind == "todo":
        line = f"You must still {do}"
    elif kind == "instr":
        line = _cap(do)
    elif kind == "cond":
        line = f"If {thing} {fact}" + (f", {so}" if so else "")
    else:
        line = _cap(f"{thing} {fact}".strip()) + (f", so {so}" if so else "")
    return line + "."


# ---- the call -------------------------------------------------------------------------

def say(cards: list[dict], model: str | None = None, workers: int = 4, literal: bool = False) -> dict:
    """Lines for the cards of one section, by line id, with how each was made: model, retry or script. Cards
    that share a "line" key make one line; a card without one is a line of its own."""
    t = time.time()
    head, _ids, groups_text = split_prompt()
    pairs, swapped = choose_pairs(cards)
    prompt = build_prompt(head, pairs, groups_text)
    system = {"role": "system", "content": prompt}
    groups: dict[str, list[dict]] = {}
    for c in cards:
        groups.setdefault(line_id(c), []).append(c)
    answer = parse_answer(complete([system, {"role": "user", "content": user_message(cards)}], model=model),
                          list(groups))
    calls = 1
    lines, how, fails, warns = {}, {}, {}, {}
    retry: dict[str, tuple[str, list[str]]] = {}
    for lid, members in groups.items():
        line = answer.get(lid, "")
        bad, warn = check_line(line, members, prompt) if line else (["the answer has no line for this id"], [])
        if bad:
            retry[lid] = (line, bad)
        else:
            lines[lid], how[lid], warns[lid] = line, "model", warn

    def again(lid: str) -> tuple[str, str]:
        msg = user_message(groups[lid], {lid: retry[lid]} if retry[lid][0] else None)
        return lid, parse_answer(complete([system, {"role": "user", "content": msg}], model=model), [lid]).get(lid, "")

    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(retry) or 1))) as pool:
        second = list(pool.map(again, list(retry)))
    calls += len(second)
    for lid, line in second:
        bad, warn = check_line(line, groups[lid], prompt) if line else (["no line again"], [])
        if not bad:
            lines[lid], how[lid], warns[lid] = line, "retry", warn
        else:
            lines[lid], how[lid] = " ".join(script_line(c) for c in groups[lid]), "script"
            warns[lid] = check_line(lines[lid], groups[lid], prompt)[1]
        fails[lid] = retry[lid][1] + ([f"retry: {'; '.join(bad)}"] if bad else [])
    report = {"lines": {lid: lines[lid] for lid in groups}, "how": {lid: how[lid] for lid in groups},
              "fails": fails, "warns": {k: v for k, v in warns.items() if v}, "calls": calls,
              "swapped": swapped, "seconds": round(time.time() - t, 1)}
    if literal:
        answers = literal_answers([report["lines"][lid] for lid in groups], model=model)
        report["literal"] = dict(zip(groups, answers))
        report["cannot_say"] = [lid for lid, a in report["literal"].items() if cannot_say(a)]
    return report


# ---- step 4: the question of what literally happens ------------------------------------

def literal_answers(lines: list[str], model: str | None = None, workers: int = 8) -> list[str]:
    """One fresh call per line: what literally happens in it, or "cannot say"."""
    question = LITERAL.read_text(encoding="utf-8").strip()

    def ask(line: str) -> str:
        try:
            return complete([{"role": "user", "content": f"{question}\n\nThe line: {line}"}],
                            model=model, max_tokens=8000).strip()
        except Exception as e:  # one line without an answer never stops the others
            return f"{NO_ANSWER} ({str(e)[:120]})"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(ask, lines))


def unanswered(answer: str) -> bool:
    return answer.startswith(NO_ANSWER)


def cannot_say(answer: str) -> bool:
    return re.sub(r"^[\s\"'*`]+|[\s\"'.*`]+$", "", answer).lower() == "cannot say"


# ---- command line --------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", type=Path, help="the build folder's cards.tsv, after card_check and card_select")
    ap.add_argument("--section", required=True, help="the section whose cards become lines")
    ap.add_argument("--out", type=Path, help="append the lines to this TSV: section, id, how, line")
    ap.add_argument("--literal", action="store_true", help="list the lines a fresh call cannot say literally")
    ap.add_argument("--model", help=f"the model (default: FAST_MODEL, else {MODEL})")
    a = ap.parse_args(argv)
    cards = [c for c in _mod("card_check").read_cards(a.cards) if c["section"].lower() == a.section.lower()]
    if not cards:
        print(f"say: no cards of section {a.section!r} in {a.cards}", file=sys.stderr)
        return 1
    r = say(cards, model=a.model, literal=a.literal)
    for cid, line in r["lines"].items():
        print(f"{cid}\t{line}")
    if a.out:
        new = not a.out.exists()
        with open(a.out, "a", encoding="utf-8") as fh:
            if new:
                fh.write("section\tid\thow\tline\n")
            for cid, line in r["lines"].items():
                fh.write(f"{a.section}\t{cid}\t{r['how'][cid]}\t{line}\n")
    err = sys.stderr
    for pid, new in r["swapped"]:
        print(f"  pair {pid} shares a topic word with a card: {'swapped for ' + new if new else 'left out'}", file=err)
    for cid, reasons in r["fails"].items():
        print(f"  {cid} {r['how'][cid]}: {'; '.join(reasons)}", file=err)
    for cid, w in r["warns"].items():
        print(f"  {cid} warn: {'; '.join(w)}", file=err)
    for cid in r.get("cannot_say", []):
        print(f"  {cid} for Chaehan: a fresh reader cannot say what literally happens in it", file=err)
    n = {h: sum(v == h for v in r["how"].values()) for h in ("model", "retry", "script")}
    print(f"say: {len(cards)} lines, {n['model']} as written, {n['retry']} on retry, {n['script']} by the script, "
          f"{r['calls']} calls, {r['seconds']} s", file=err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
