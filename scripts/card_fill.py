#!/usr/bin/env python3
"""Fill the fact cards of a note's sections from sources.md (build spec step 2).

One DeepSeek call per section, all sections at once. Each call gets
wording_fill_prompt.md as its system message and the section's record lines
from sources.md, numbered, as its user message, and nothing else. The cards
it returns are appended to cards.tsv with their section, an id, and the record
line's location as src (memory/health.md:96).

    python3 scripts/card_fill.py sources.md --section "Health" --section "Partner search" \\
        --out <build>/cards.tsv

Then run card_check.py and card_select.py on cards.tsv. A pilot call took
118 s and 185 s for six record lines; the sections run in parallel.
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", type=Path, help="the note's sources.md")
    ap.add_argument("--section", action="append", required=True, help="a section heading; repeat for several")
    ap.add_argument("--out", type=Path, required=True, help="the build folder's cards.tsv (cards are appended)")
    ap.add_argument("--model", help=f"the model (default: FAST_MODEL, else {MODEL})")
    a = ap.parse_args(argv)
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
