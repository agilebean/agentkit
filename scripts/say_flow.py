#!/usr/bin/env python3
"""Sentences that follow each other: one pass over the written lines of each section of a note (human quality
plan, task HQ-06).

say.py writes one line per card, so a section repeats a thing's full name in line after line ("Your right
shoulder flare ... Your right shoulder flare location ..."). This pass sends each section's lines, with their
place (lead, bullet, bullet under a bullet), to one fresh call with wording_flow_prompt.md: a thing is named in
full once and by a short form after, each sentence opens on what the one before said, and two lines next to
each other at one place may share a sentence. It reads the note's lines, not cards, so it runs on any built
note, A4 of the step 8 test included, and say.py's own lines and their measure stay as they are.

The answer is checked against the section it came from, with say.py's own checks: every line id once and in
order, a joined line made of neighbours at one place, every number of its lines (or said in an earlier
line of the section, as the number in a name like "Unit 1102" is) and none added, every name of
the section still in it and none added, no six words in a row from the prompt's example, and no flag of
wording_lint.py that the lines did not have. An answer that fails is asked for once more with the reasons; a
second failure keeps the section as it was. Tables, images, quotes and headings are never sent.
A second pass catches what the first left inside one line: on 2026-11-21 A4 went from 21 pairs of
sentences in a row naming one thing again to 5 after one pass and 2 after two.

    python3 scripts/say_flow.py <note.md> --out <new.md> [--passes 2]   # the pass, measured before and after
    python3 scripts/say_flow.py <note.md> --measure          # the measure alone

The measure counts, in each section, the pairs of sentences in a row that share three words of which two are
content words ("your right shoulder", "the renewal date"), the median words a sentence, and the lint flags.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "wording_flow_prompt.md"
HEADING = re.compile(r"^#{1,6}\s")
SECTION = re.compile(r"^##\s")
ITEM = re.compile(r"^(?P<pad>\s*)(?P<mark>(?:[-*]|\d+\.)\s+)?(?P<text>\S.*)$")
ANSWER = re.compile(r"^\s*[-*]?\s*(L\d+(?:\s*,\s*L\d+)*)\s*(?:\t|:\s)\s*(.+?)\s*$")
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[\"“(]?[A-Z0-9가-힣])")
TOKEN = re.compile(r"[a-z가-힣][a-z가-힣'*-]*|\d[\d.:/-]*")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


say = _load("say")
STOP = say.FILLER | set("the a an of to in on at and or so is are was were be it its for by as not no you i he she "
                        "we our my his her him me us is am do does did".split())


def complete(messages: list[dict], model: str | None = None) -> str:
    return say.complete(messages, model=model, max_tokens=16000, temperature=0.3)


# ---- the lines of a section ----------------------------------------------------------

def items_of(lines: list[str]) -> list[dict]:
    """The lines of one section that read as sentences: a lead or a bullet. A heading, a table row, an image, a
    quote or a code fence is never sent and never moves."""
    out = []
    for at, raw in enumerate(lines):
        s = raw.strip()
        if not s or HEADING.match(s) or s.startswith(("|", "!", ">", "```", "<")):
            continue
        m = ITEM.match(raw)
        out.append({"id": f"L{len(out) + 1}", "at": at, "pad": m["pad"], "mark": m["mark"] or "", "text": m["text"]})
    return out


def place(item: dict) -> str:
    if not item["mark"]:
        return "lead"
    return "bullet under the bullet before" if item["pad"] else "bullet"


def message(items: list[dict], refused: tuple[str, list[str]] | None = None) -> str:
    msg = "\n".join(f"{i['id']} ({place(i)})\t{i['text']}" for i in items)
    if refused:
        msg += (f"\n\nYour answer was refused:\n{refused[0]}\nWhy: {'; '.join(refused[1])}.\n"
                f"Write the section again from its lines.")
    return msg


def parse(answer: str) -> list[tuple[list[str], str]]:
    out = []
    for line in answer.splitlines():
        m = ANSWER.match(line)
        if m:
            out.append(([x.strip() for x in m.group(1).split(",")], m.group(2)))
    return out


# ---- the checks --------------------------------------------------------------------------

def _flags(text: str) -> set[str]:
    return {match.strip() for _n, level, match, _fix in say._mod("wording_lint").lint_text(text, say._rules())
            if level == "flag"}


def check(items: list[dict], groups: list[tuple[list[str], str]], prompt: str) -> list[str]:
    """The reasons an answer fails against the section's lines; none when it passes."""
    ids = [i["id"] for i in items]
    pos = {i["id"]: n for n, i in enumerate(items)}
    by_id = {i["id"]: i for i in items}
    order = [x for g, _ in groups for x in g]
    if order != ids:
        return [f"give every line id once and in order, {', '.join(ids)}; the answer gave {', '.join(order) or 'none'}"]
    fails, said = [], set()
    source = " ".join(i["text"] for i in items)
    for g, text in groups:
        members = [by_id[x] for x in g]
        if any(pos[b] != pos[a] + 1 for a, b in zip(g, g[1:])) or len({(m["pad"], place(m)) for m in members}) > 1:
            fails.append(f"{','.join(g)} joins lines that are not neighbours at one place: join only those")
        held = set().union(*(say._numbers(m["text"]) for m in members))
        # A number inside a full name ("Unit 1102") leaves with the name when an earlier line said it.
        lost, added = sorted(held - say._numbers(text) - said), sorted(say._numbers(text) - held)
        said |= say._numbers(text)
        if lost:
            fails.append(f"{','.join(g)} loses {', '.join(lost)}: keep every number of its lines")
        if added:
            fails.append(f"{','.join(g)} adds {', '.join(added)}: add no number")
        new = sorted(n for n in say._names(text, True) if n not in source)
        if new:
            fails.append(f"{','.join(g)} adds {', '.join(new)}, which the lines lack: add no name")
        if (say._shingles(text) & say._shingles(prompt)) - say._shingles(source):
            fails.append(f"{','.join(g)} copies six words in a row from the example: write it from its lines")
        flags = _flags(text) - _flags(" ".join(m["text"] for m in members))
        if flags:
            fails.append(f"{','.join(g)} has {', '.join(sorted(flags))}, which wording_lint.py flags")
    out = " ".join(t for _, t in groups)
    lost_names = sorted(n for n in say._names(source, False) if n not in out)
    if lost_names:
        fails.append(f"the section loses {', '.join(lost_names)}: name each thing in full once")
    return fails


def rewrite(lines: list[str], items: list[dict], groups: list[tuple[list[str], str]]) -> list[str]:
    """The section's lines with each group written at its first line's place and its other lines removed."""
    by_id = {i["id"]: i for i in items}
    new, drop = {}, set()
    for g, text in groups:
        first = by_id[g[0]]
        new[first["at"]] = f"{first['pad']}{first['mark']}{text}"
        drop |= {by_id[x]["at"] for x in g[1:]}
    return [new.get(n, line) for n, line in enumerate(lines) if n not in drop]


# ---- the pass ----------------------------------------------------------------------------

def flow_section(lines: list[str], model: str | None = None) -> dict:
    """One section through the pass: its new lines, how they came (model, retry, kept or alone), the reasons
    an answer failed, and the calls it took."""
    items = items_of(lines)
    if len(items) < 2:
        return {"lines": lines, "how": "alone", "fails": [], "calls": 0}
    prompt = PROMPT.read_text(encoding="utf-8")
    system = {"role": "system", "content": prompt}
    answer = complete([system, {"role": "user", "content": message(items)}], model=model)
    groups = parse(answer)
    fails = check(items, groups, prompt)
    if not fails:
        return {"lines": rewrite(lines, items, groups), "how": "model", "fails": [], "calls": 1}
    answer2 = complete([system, {"role": "user", "content": message(items, (answer.strip(), fails))}], model=model)
    groups2 = parse(answer2)
    fails2 = check(items, groups2, prompt)
    if not fails2:
        return {"lines": rewrite(lines, items, groups2), "how": "retry", "fails": fails, "calls": 2}
    return {"lines": lines, "how": "kept", "fails": fails + [f"retry: {'; '.join(fails2)}"], "calls": 2}


def split_sections(md: str) -> list[tuple[str, list[str]]]:
    """The note as (heading, lines) parts: the part before the first ## heading, then each ## section with
    its subsections."""
    parts: list[tuple[str, list[str]]] = [("", [])]
    for line in md.splitlines():
        if SECTION.match(line):
            parts.append((line[2:].strip(), [line]))
        else:
            parts[-1][1].append(line)
    return parts


def flow_note(md: str, model: str | None = None, workers: int = 4) -> tuple[str, dict]:
    """Every ## section of a note through the pass, all at once: (the new note, a report per section)."""
    parts = split_sections(md)

    def one(part):
        head, lines = part
        if not head:
            return {"lines": lines, "how": "title", "fails": [], "calls": 0}
        try:
            return flow_section(lines, model)
        except Exception as e:  # noqa: BLE001 - a failed call keeps its section
            return {"lines": lines, "how": "kept", "fails": [f"no answer ({str(e)[:100]})"], "calls": 1}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        done = list(pool.map(one, parts))
    text = "\n".join(line for d in done for line in d["lines"])
    return text + ("\n" if md.endswith("\n") else ""), {h or "(title)": d for (h, _), d in zip(parts, done)}


# ---- the measure ---------------------------------------------------------------------------

def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE.split(text) if s.strip()]


def _content_trigrams(sentence: str) -> set[tuple[str, ...]]:
    words = TOKEN.findall(sentence.lower().replace("**", ""))
    return {t for t in zip(words, words[1:], words[2:])
            if sum(1 for w in t if w[0].isalpha() and w not in STOP) >= 2}


def measure(md: str) -> dict:
    """Per note: sentences, the median words a sentence, the pairs of sentences in a row within a section that
    share three words of which two are content words, and wording_lint.py's flags."""
    counts, repeats = [], []
    for head, lines in split_sections(md):
        if not head:
            continue
        said = [s for i in items_of(lines) for s in sentences(i["text"])]
        counts += [len(s.split()) for s in said]
        for a, b in zip(said, said[1:]):
            shared = _content_trigrams(a) & _content_trigrams(b)
            if shared:
                repeats.append({"section": head, "words": " ".join(sorted(shared)[0]), "first": a, "second": b})
    flags = [m for _n, level, m, _f in say._mod("wording_lint").lint_text(md, say._rules()) if level == "flag"]
    return {"sentences": len(counts), "median_words": statistics.median(counts) if counts else 0,
            "repeats": len(repeats), "repeat_pairs": repeats, "flags": len(flags), "words": len(md.split())}


def describe(m: dict) -> str:
    return (f"{m['words']} words, {m['sentences']} sentences, median {m['median_words']} words a sentence, "
            f"{m['repeats']} pairs in a row naming one thing again, {m['flags']} lint flags")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("note", type=Path, help="the note (Markdown)")
    ap.add_argument("--out", type=Path, help="write the note after the pass here")
    ap.add_argument("--measure", action="store_true", help="print the measure and the repeated pairs, and stop")
    ap.add_argument("--passes", type=int, default=1, help="passes at most, while the repeats keep falling (default 1)")
    ap.add_argument("--model", help="the model (default: say.py's)")
    a = ap.parse_args(argv)
    md = a.note.read_text(encoding="utf-8")
    before = measure(md)
    print(f"before: {describe(before)}")
    if a.measure:
        for r in before["repeat_pairs"]:
            print(f"  {r['section']}: \"{r['words']}\" in \"{r['first'][:70]}\" and \"{r['second'][:70]}\"")
        return 0
    if not a.out:
        ap.error("give --out, or --measure")
    t, text, last, calls = time.time(), md, before, 0
    for k in range(1, max(1, a.passes) + 1):
        new, report = flow_note(text, a.model)
        after = measure(new)
        calls += sum(r["calls"] for r in report.values())
        print(f"pass {k}: {describe(after)}")
        for head, r in report.items():
            if r["how"] != "title":
                print(f"  {head}: {r['how']}" + (f" ({'; '.join(r['fails'])})" if r["fails"] else ""))
        if after["repeats"] >= last["repeats"] and k > 1:
            break
        text, last = new, after
        if not after["repeats"]:
            break
    a.out.write_text(text, encoding="utf-8")
    print(f"kept: {describe(last)}; {calls} calls, {round(time.time() - t)} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
