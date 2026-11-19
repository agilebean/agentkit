#!/usr/bin/env python3
"""Fill the fact cards of a note's sections from sources.md (build spec step 2).

One DeepSeek call per piece of at most six record lines of a section, all at
once. Each call gets wording_fill_prompt.md as its system message and the
record lines, numbered, as its user message, and nothing else. The cards
it returns are appended to cards.tsv with their section, an id, and the record
line's location as src (memory/health.md:96).

    python3 scripts/card_fill.py sources.md --section "Health" --section "Partner search" \\
        --out <build>/cards.tsv

Then `card_fill.py sources.md --out cards.tsv --repair` checks the cards, fills each
refused card again once with the reasons, fills the cards a record line still
lacks (a name or number of the line that no card holds), and moves what stays
refused to cut.tsv. card_select.py then cuts what Chaehan stated himself. A call
for six record lines took 118 to 248 s; the pieces run in parallel.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "wording_fill_prompt.md"
MODEL = "deepseek/deepseek-v4.1-flash"
LOC = re.compile(r"\s*(?:[-*]\s+)?(\S+:\d+)\s+\|\s+(.*)")

_spec = importlib.util.spec_from_file_location("card_check", Path(__file__).resolve().parent / "card_check.py")
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)
FIELDS = cc.FIELDS
read_cards = cc.read_cards
write_cards = cc.write_cards


def complete(messages: list[dict], model: str | None = None, max_tokens: int = 24000, temperature: float = 0.3) -> str:
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


def section_lines(sources: str, section: str) -> list[tuple[str, str]]:
    """The record lines under '## <section>' of sources.md as (location, line)."""
    out: list[tuple[str, str]] = []
    inside = False
    for n, line in enumerate(sources.splitlines(), 1):
        m = re.match(r"(#{1,3})\s+(.*)", line)
        if m:
            if len(m.group(1)) <= 2:
                inside = m.group(2).strip().lower() == section.strip().lower()
            continue
        if not inside or not line.strip():
            continue
        lm = LOC.match(line)
        out.append((lm.group(1), lm.group(2).strip()) if lm else (f"sources.md:{n}", line.strip()))
    return out


def user_message(block: list[tuple[str, str]]) -> str:
    return "Record lines:\n" + "\n".join(f"{i}  {text}" for i, (_loc, text) in enumerate(block, 1))


def parse_cards(text: str, section: str, block: list[tuple[str, str]], start: int = 1) -> tuple[list[dict], list[str]]:
    """The cards of the call's answer, and the lines that are not a card."""
    cards, bad = [], []
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("```"):
            continue
        cells = [c.strip() for c in re.split(r"\s*\|\s*", line.strip())]
        if len(cells) != 7:
            bad.append(f"not seven fields: {line.strip()}")
            continue
        kind, thing, fact, so, do, said, src = cells
        if not src.isdigit() or not 1 <= int(src) <= len(block):
            bad.append(f"src {src!r} is no record line of the section: {line.strip()}")
            continue
        said = (re.findall(r"\d{4}-\d{2}-\d{2}", said) or [said])[0]
        cards.append({"section": section, "id": f"C{start + len(cards):02d}", "kind": kind.lower(),
                      "thing": thing, "fact": fact, "so": so, "do": do, "said": said,
                      "src": block[int(src) - 1][0]})
    return cards, bad


CHUNK = 6  # record lines per call: the pilot's size. A whole section of 9 to 15 lines ran out of its
# 24000 tokens in reasoning twice on 2026-11-17, and that one call stopped every section.


def fill_section(sources: str, section: str, model: str | None = None) -> tuple[list[dict], list[str], float]:
    """The section's cards, from calls of at most CHUNK record lines each, sent at once. A call that fails
    is reported among the lines not kept and stops no other call."""
    block = section_lines(sources, section)
    if not block:
        return [], [f"section {section!r} has no record lines in sources.md"], 0.0
    t = time.time()
    prompt = PROMPT.read_text(encoding="utf-8")
    chunks = [block[i:i + CHUNK] for i in range(0, len(block), CHUNK)]

    def one(chunk: list[tuple[str, str]]) -> tuple[list[dict], list[str]]:
        try:
            answer = complete([{"role": "system", "content": prompt},
                               {"role": "user", "content": user_message(chunk)}], model=model)
        except Exception as e:
            return [], [f"record lines {chunk[0][0]} to {chunk[-1][0]} got no cards: {str(e)[:120]}"]
        return parse_cards(answer, section, chunk)

    with ThreadPoolExecutor(max_workers=len(chunks)) as pool:
        results = list(pool.map(one, chunks))
    cards = [c for new, _bad in results for c in new]
    for i, c in enumerate(cards, 1):
        c["id"] = f"C{i:02d}"
    return cards, [b for _new, bad in results for b in bad], time.time() - t


# ---- repair: a refused card is filled again once, and a record line's facts without a card get theirs ----

NUMBER = re.compile(r"\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?")
NAME = re.compile(r"(?<![.:;!?(*|\-]\s)(?<!^)\b[A-Z][A-Za-z-]{2,}\b|[가-힣]{2,}", re.M)
NOT_COVERED = {"Chaehan", "Evernote", "The", "This", "That", "His", "Her", "Their", "She", "They", "You", "Your"}


def card_row(card: dict, n: int = 1) -> str:
    return " | ".join([card["kind"], card["thing"], card["fact"], card["so"], card["do"], card["said"], str(n)])


def _ask(section: str, loc: str, text: str, ask: str, model: str | None) -> tuple[list[dict], list[str]]:
    msg = f"{user_message([(loc, text)])}\n\n{ask}"
    try:
        answer = complete([{"role": "system", "content": PROMPT.read_text(encoding="utf-8")},
                           {"role": "user", "content": msg}], model=model)
    except Exception as e:
        return [], [f"{loc}: no answer ({str(e)[:120]})"]
    return parse_cards(answer, section, [(loc, text)])


def uncovered(cards: list[dict], loc: str, text: str) -> list[str]:
    """The names and numbers of a record line that no card of that line holds."""
    held = " ".join(f"{c['thing']} {c['fact']} {c['so']} {c['do']} {c['said']}" for c in cards if c["src"] == loc)
    held = cc.iso_dates(held).replace(",", "").lower()
    plain = cc.iso_dates(text).replace(",", "")
    words = [w for w in dict.fromkeys(NAME.findall(plain)) if w not in NOT_COVERED and w.lower() not in held]
    nums = [n for n in dict.fromkeys(NUMBER.findall(plain)) if n not in set(NUMBER.findall(held))]
    return words + nums


def repair(path: Path, sources: Path, root: Path | None = None, model: str | None = None) -> dict:
    """Check cards.tsv; fill each refused card again once with the reasons; fill the cards a record line still
    lacks; check again, and move what is still refused to cut.tsv. One call per card or line, all at once."""
    text = sources.read_text(encoding="utf-8")
    smap = cc.read_sources(sources)
    root = Path(root) if root else Path.cwd()
    refusals, _emptied, fixed = cc.check_file(path, sources, root)
    cards = read_cards(path)
    why: dict[str, list[str]] = {}
    for r in refusals:
        why.setdefault(r.card, []).append(f"{r.field}: {r.text}")
    by_id = {c["id"]: c for c in cards}

    def again(cid: str):
        c = by_id[cid]
        src = cc.source_text(c["src"], smap, root) or ""
        return cid, _ask(c["section"], c["src"], src, f"Your card for line 1 was refused:\n{card_row(c)}\n"
                         f"Why: {'; '.join(why[cid])}.\nWrite the card again from line 1, or return nothing "
                         f"when the line gives no card for it.", model)

    gaps = []
    for section in dict.fromkeys(c["section"] for c in cards):
        for loc, line in section_lines(text, section):
            missing = uncovered(cards, loc, line)
            if missing:
                gaps.append((section, loc, line, missing))

    def cover(gap):
        section, loc, line, missing = gap
        held = "\n".join(card_row(c) for c in cards if c["src"] == loc) or "none"
        return gap, _ask(section, loc, line, f"The cards you filled from line 1:\n{held}\nThese words and numbers of "
                         f"line 1 stand in no card: {', '.join(missing)}. Fill a card for each fact of line 1 that "
                         f"holds them. Return only the new cards.", model)

    with ThreadPoolExecutor(max_workers=8) as pool:
        redone = list(pool.map(again, list(why)))
        covered = list(pool.map(cover, gaps))
    out, report = [], {"fixed": fixed, "refilled": {}, "covered": {}, "not cards": []}
    redo = dict(redone)
    for c in cards:
        if c["id"] not in redo:
            out.append(c)
            continue
        new, bad = redo[c["id"]]
        report["not cards"] += bad
        for i, n in enumerate(new):
            n["id"] = c["id"] + ("" if i == 0 else "bcdefgh"[i - 1])
            out.append(n)
        report["refilled"][c["id"]] = [n["id"] for n in new]
    n_next = 1 + max([int(re.sub(r"\D", "", c["id"]) or 0) for c in cards] or [0])
    for (section, loc, _line, missing), (new, bad) in covered:
        report["not cards"] += bad
        for n in new:
            n["id"] = f"C{n_next:02d}"
            n_next += 1
            out.append(n)
        report["covered"][loc] = {"missing": missing, "new": [n["id"] for n in new]}
    write_cards(path, out)
    refusals, _emptied, fixed2 = cc.check_file(path, sources, root)
    report["fixed"] += fixed2
    still = {r.card for r in refusals}
    kept = [c for c in read_cards(path) if c["id"] not in still]
    cut = [c | {"reason": "refused: " + "; ".join(r.text for r in refusals if r.card == c["id"])}
           for c in read_cards(path) if c["id"] in still]
    write_cards(path, kept)
    if cut:
        cut_path = path.with_name("cut.tsv")
        write_cards(cut_path, read_cards(cut_path) + cut, extra=("reason",))
    report["cut as refused"] = [c["id"] for c in cut]
    report["calls"] = len(redone) + len(covered)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", type=Path, help="the note's sources.md")
    ap.add_argument("--section", action="append", help="a section heading; repeat for several")
    ap.add_argument("--out", type=Path, required=True, help="the build folder's cards.tsv (cards are appended)")
    ap.add_argument("--repair", action="store_true", help="check --out, fill each refused card again once, fill "
                    "the cards a record line still lacks, and cut what stays refused")
    ap.add_argument("--root", type=Path, help="where a src path such as memory/health.md starts (default: here)")
    ap.add_argument("--model", help=f"the model (default: FAST_MODEL, else {MODEL})")
    a = ap.parse_args(argv)
    if a.repair:
        t = time.time()
        r = repair(a.out, a.sources, a.root, a.model)
        for f in r["fixed"]:
            print(f"  fixed {f}")
        for cid, new in r["refilled"].items():
            print(f"  refilled {cid}: {' '.join(new) or 'no card'}")
        for loc, c in r["covered"].items():
            print(f"  {loc} lacked {', '.join(c['missing'])}: {' '.join(c['new']) or 'no card'}")
        for b in r["not cards"]:
            print(f"    not kept, {b}")
        print(f"card_fill --repair: {r['calls']} calls, {len(r['cut as refused'])} cut as refused, {time.time() - t:.0f} s")
        return 0
    if not a.section:
        ap.error("give --section, or --repair")
    sources = a.sources.read_text(encoding="utf-8")
    t = time.time()
    with ThreadPoolExecutor(max_workers=min(8, len(a.section))) as pool:
        results = list(pool.map(lambda s: fill_section(sources, s, a.model), a.section))
    cards = read_cards(a.out)
    for section, (new, bad, secs) in zip(a.section, results):
        for c in new:
            c["id"] = f"C{len(cards) + 1:02d}"
            cards.append(c)
        print(f"  {section}: {len(new)} cards in {secs:.0f} s")
        for b in bad:
            print(f"    not kept, {b}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    write_cards(a.out, cards)
    print(f"card_fill: {len(cards)} cards in {a.out}, {time.time() - t:.0f} s")
    return 0 if all(new for new, _b, _s in results) else 1


if __name__ == "__main__":
    sys.exit(main())
