#!/usr/bin/env python3
"""Choose the cards a note says, their order and what sits under what (the skill's Moves 1, 2 and 4).

One DeepSeek call per section, all sections at once. Each call gets wording_choose_prompt.md as its
system message and, as its user message, today's date, the section's name and its cards. It answers with
card ids only, in an outline:

    lead: C19
    - C20, C22
      - C49
    out: C26, C27

A script checks the answer: every id once, a lead first, at most three bullets, at most three cards a
line, an indent only under a bullet (in "What went well": no lead, any number of bullets, up to four
cards a line). With --priorities, every call also gets his order of priorities from his record, so the
matter he ranks first in a section leads it. An answer that breaks a rule is asked for once more with the reasons; a second one is
replaced by the script's own choice: the first cards Chaehan did not state himself, a lead and three
bullets. The Takeaway takes each section's lead, as Move 4 asks for one bullet per block, its first
matter. The plan is written in the columns of map.tsv, so say.py can write it.

    python3 scripts/card_choose.py <build>/cards.tsv --sources sources.md --out <build>/plan.tsv \
        --priorities memory/optimize-my-life.md
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "wording_choose_prompt.md"
WINS = "what went well"
ID = re.compile(r"\b[A-Za-z]+\d+[a-z]?\b")
LINE = re.compile(r"^(?P<pad>\s*)(?P<mark>lead:|out:|[-*])\s*(?P<ids>.*)$", re.I)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mods: dict[str, object] = {}


def _mod(name: str):
    if name not in _mods:
        _mods[name] = _load(name)
    return _mods[name]


def complete(messages: list[dict], model: str | None = None, max_tokens: int = 32000, temperature: float = 0.3) -> str:
    # 16000 tokens ran out in reasoning twice for one section on 2026-11-20.
    return _mod("say").complete(messages, model=model, max_tokens=max_tokens, temperature=temperature)


def _answer(messages: list[dict], model: str | None) -> tuple[str, list[str]]:
    """The call's answer, or no answer and the reason: a failed call never stops the other sections."""
    try:
        return complete(messages, model=model), []
    except Exception as e:
        return "", [f"no answer ({str(e)[:100]})"]


def user_message(section: str, cards: list[dict], date: str, priorities: str | None = None) -> str:
    rows = [f"{c['id']}\t{_mod('say').card_text(c)}" + (f" | said={c['said']}" if c.get("said") else "") for c in cards]
    order = f"His order of priorities: {priorities}\n" if priorities else ""
    return f"Today is {date}. Section: {section}\n{order}Cards:\n" + "\n".join(rows)


def priorities_of(path: Path) -> str | None:
    """The lines under the heading "Life priorities" of a memory file, joined, as his record states them."""
    m = re.search(r"^#+\s*Life priorities\s*$(.*?)(?=^#|\Z)", Path(path).read_text(encoding="utf-8"), re.M | re.S)
    text = " ".join(line.strip() for line in m.group(1).splitlines() if line.strip()) if m else ""
    return text or None


def parse_answer(text: str, ids: list[str], section: str) -> tuple[list[dict], list[str], list[str]]:
    """(the lines as rows of kind, indent and cards, the ids left out, the rules the answer breaks)."""
    wins = section.strip().lower() == WINS
    rows, out, problems, seen = [], [], [], set()
    for raw in text.splitlines():
        m = LINE.match(raw.rstrip())
        if not m or raw.strip().lower().startswith("answer"):
            continue
        found = ID.findall(m.group("ids"))
        for cid in found:
            if cid not in ids:
                problems.append(f"{cid} is no card of this section")
            elif cid in seen:
                problems.append(f"{cid} appears twice: give each card one place")
            seen.add(cid)
        found = [c for c in dict.fromkeys(found) if c in ids]
        mark = m.group("mark").lower()
        if mark == "out:":
            out += found
            continue
        if not found:
            continue
        indent = len(m.group("pad").replace("\t", "  ")) // 2
        kind = "lead" if mark == "lead:" else "bullet"
        if indent and (not rows or rows[-1]["kind"] == "lead"):
            problems.append(f"{', '.join(found)} is indented under the lead: indent a card only under a bullet")
        rows.append({"kind": kind, "indent": min(indent, 1), "cards": found})
    limit = 4 if wins else 3
    for r in rows:
        if len(r["cards"]) > limit:
            problems.append(f"a line holds more than {'four' if wins else 'three'} cards: {', '.join(r['cards'])}")
    leads = [r for r in rows if r["kind"] == "lead"]
    if wins and leads:
        problems.append("What went well has no lead: write each thing he achieved as a bullet")
    if not wins:
        if not leads or rows[0]["kind"] != "lead":
            problems.append("the answer has no lead first: begin with 'lead:' and the card that says where this "
                            "part of his life stands")
        if len(leads) > 1:
            problems.append("the answer has more than one lead")
        if sum(1 for r in rows if r["kind"] == "bullet" and r["indent"] == 0) > 3:
            problems.append("the answer has more than three bullets under the lead")
    out += [c for c in ids if c not in seen]
    return rows, list(dict.fromkeys(out)), problems


def script_choice(section: str, cards: list[dict]) -> tuple[list[dict], list[str]]:
    """The last resort: the first cards Chaehan did not state himself, as a lead and three bullets."""
    pick = [c for c in cards if not c.get("said")] or cards
    if section.strip().lower() == WINS:
        rows = [{"kind": "bullet", "indent": 0, "cards": [c["id"]]} for c in cards]
        return rows, []
    rows = [{"kind": "lead" if i == 0 else "bullet", "indent": 0, "cards": [c["id"]]} for i, c in enumerate(pick[:4])]
    used = {c for r in rows for c in r["cards"]}
    return rows, [c["id"] for c in cards if c["id"] not in used]


def choose_section(section: str, cards: list[dict], date: str, model: str | None = None,
                   priorities: str | None = None) -> dict:
    t = time.time()
    ids = [c["id"] for c in cards]
    system = {"role": "system", "content": PROMPT.read_text(encoding="utf-8")}
    msg = user_message(section, cards, date, priorities)
    text, failed = _answer([system, {"role": "user", "content": msg}], model)
    rows, out, problems = parse_answer(text, ids, section)
    problems = failed or problems
    calls, how, first = 1, "model", problems
    if problems:
        again = msg if failed else msg + ("\n\nYour last answer broke these rules: " + "; ".join(problems) +
                                          ". Answer again.")
        text, failed = _answer([system, {"role": "user", "content": again}], model)
        rows, out, problems = parse_answer(text, ids, section)
        problems = failed or problems
        calls, how = 2, "retry"
        if problems:
            rows, out = script_choice(section, cards)
            how = "script"
    return {"rows": rows, "out": out, "how": how, "problems": first + problems, "calls": calls,
            "seconds": round(time.time() - t, 1)}


def plan(cards_path: Path, out_path: Path, date: str, model: str | None = None, workers: int = 8,
         priorities: str | None = None) -> dict:
    """Choose every section of cards.tsv and write the plan in the columns of map.tsv."""
    cards = _mod("card_check").read_cards(cards_path)
    sections = list(dict.fromkeys(c["section"] for c in cards))
    t = time.time()
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(sections)))) as pool:
        chosen = dict(zip(sections, pool.map(
            lambda s: choose_section(s, [c for c in cards if c["section"] == s], date, model, priorities), sections)))
    lines = [("Takeaway", "bullet", 0, r["cards"]) for s in sections if s.strip().lower() != WINS
             for r in chosen[s]["rows"][:1] if r["kind"] == "lead"]
    lines += [(s, r["kind"], r["indent"], r["cards"]) for s in sections for r in chosen[s]["rows"]]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("section\tkind\tindent\tcards\ttoday\n")
        for s, kind, indent, ids in lines:
            fh.write(f"{s}\t{kind}\t{indent}\t{','.join(ids)}\t\n")
    return {"how": {s: c["how"] for s, c in chosen.items()},
            "out": {s: c["out"] for s, c in chosen.items() if c["out"]},
            "problems": {s: c["problems"] for s, c in chosen.items() if c["problems"]},
            "calls": sum(c["calls"] for c in chosen.values()), "seconds": round(time.time() - t),
            "chosen": sum(len(r["cards"]) for c in chosen.values() for r in c["rows"]), "cards": len(cards)}


def date_of(sources: Path) -> str | None:
    m = re.search(r"\d{4}-\d{2}-\d{2}", Path(sources).read_text(encoding="utf-8").splitlines()[0])
    return m.group(0) if m else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", type=Path, help="the build folder's cards.tsv, after card_fill.py --repair")
    ap.add_argument("--out", type=Path, required=True, help="the plan, in the columns of map.tsv")
    ap.add_argument("--sources", type=Path, help="sources.md: its first heading gives today's date")
    ap.add_argument("--date", help="today's date, YYYY-MM-DD (default: from --sources)")
    ap.add_argument("--priorities", type=Path, help="the memory file whose heading 'Life priorities' holds his "
                    "order, such as memory/optimize-my-life.md; each call gets it above the cards")
    ap.add_argument("--model", help="the model (default: say.py's)")
    a = ap.parse_args(argv)
    date = a.date or (date_of(a.sources) if a.sources else None)
    if not date:
        ap.error("give --date, or --sources whose first heading holds the date")
    order = priorities_of(a.priorities) if a.priorities else None
    if a.priorities and not order:
        ap.error(f"{a.priorities} has no heading 'Life priorities' with lines under it")
    r = plan(a.cards, a.out, date, a.model, priorities=order)
    for s, how in r["how"].items():
        print(f"  {s}: {how}" + (f", {'; '.join(r['problems'][s])}" if s in r["problems"] else ""))
    print(f"card_choose: {r['chosen']} of {r['cards']} cards in {a.out}, {r['calls']} calls, {r['seconds']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
