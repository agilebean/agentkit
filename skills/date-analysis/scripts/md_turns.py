#!/usr/bin/env python3
"""Turn Chaehan's transcript export (Whisper Transcription, Markdown with timestamps) into numbered turns.

Usage:
  md_turns.py EXPORT.md --out B/transcript.md [--map "Speaker 3=Other" ...] [--stats B/stats.md]
  md_turns.py EXPORT.md --speakers

The export holds blocks of a `**Name**` line, a `*05:17:42*` time line and the text; a block with a time
line and no name line continues the speaker above it. Every timed block stays its own turn, so each
keeps its time, and a line the export files under the wrong speaker is not merged into the turn before it
(on 2026-11-11 her "그러니까 뭔가 겁나 사람 만날 때" [5:10:56] sat under Chaehan, right after his
"무슨 무슨?"). Each turn is written as

  T0504 [5:17:42] Jiyoung: ...

which is the line `date_check.py` finds a quote in. `--speakers` prints each speaker's turns, characters
and longest turns, for step 2 of the skill. `--stats` writes characters and question lines per speaker,
overall and by hour of the recording. The export has start times only, so the shares are by characters.

This reads the file Chaehan exported; it never reads MacWhisper's database (Chaehan, 2026-11-14:
"do not transcribe the audio again, the transcript is at ...").
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict

NAME = re.compile(r"^\*\*(.+?)\*\*\s*$")
TIME = re.compile(r"^\*(\d{1,2}(?::\d{2}){1,2})\*\s*$")
QUESTION = re.compile(r"(\?|까요|나요|가요|어요\?|죠\?|니\?|래요\?)\s*$")


def seconds(stamp: str) -> int:
    parts = [int(p) for p in stamp.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def clock(sec: int) -> str:
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def blocks(text: str) -> list[tuple[str, int, str]]:
    """(speaker, start second, text) for every timed block, in file order."""
    out: list[tuple[str, int, str]] = []
    speaker, start, buf = None, None, []

    def flush():
        if speaker is not None and start is not None and " ".join(buf).strip():
            out.append((speaker, start, " ".join(" ".join(buf).split())))

    for line in text.splitlines():
        m = NAME.match(line)
        if m:
            flush()
            speaker, start, buf = m.group(1).strip(), None, []
            continue
        t = TIME.match(line)
        if t:
            flush()
            start, buf = seconds(t.group(1)), []
            continue
        if line.strip():
            buf.append(line.strip())
    flush()
    return out


def turns(text: str, mapping: dict[str, str] | None = None) -> list[tuple[int, str, str]]:
    """One turn per timed block: (start second, speaker, text)."""
    mapping = mapping or {}
    return [(start, mapping.get(who, who), words) for who, start, words in blocks(text)]


def render(ts: list[tuple[int, str, str]], source: str) -> str:
    end = clock(ts[-1][0]) if ts else "0:00:00"
    head = (f"# {source}\n\nChaehan's transcript export, read by md_turns.py; the last turn starts at {end}. "
            "One line per turn: turn number, time of its first words, speaker.\n\n")
    return head + "\n".join(f"T{i:04d} [{clock(s)}] {w}: {x}" for i, (s, w, x) in enumerate(ts, 1)) + "\n"


def speakers(ts: list[tuple[int, str, str]]) -> str:
    by = defaultdict(list)
    for s, w, x in ts:
        by[w].append((s, x))
    lines = []
    for w, rows in sorted(by.items(), key=lambda kv: -sum(len(x) for _, x in kv[1])):
        lines.append(f"## {w}: {len(rows)} turns, {sum(len(x) for _, x in rows)} characters")
        for s, x in sorted(rows, key=lambda r: -len(r[1]))[:8]:
            lines.append(f"  [{clock(s)}] {x[:160]}")
        lines.append("")
    return "\n".join(lines)


def stats(ts: list[tuple[int, str, str]]) -> str:
    total = defaultdict(lambda: [0, 0, 0])
    hours = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for s, w, x in ts:
        q = 1 if QUESTION.search(x) else 0
        total[w][0] += 1
        total[w][1] += len(x)
        total[w][2] += q
        hours[s // 3600][w][0] += len(x)
        hours[s // 3600][w][1] += q
    names = sorted(total, key=lambda w: -total[w][1])
    allc = sum(v[1] for v in total.values()) or 1
    out = ["# Talk statistics", "",
           "Shares are by characters, since the export holds start times only. Question lines end in a question "
           "mark or a Korean question ending; compare speakers and hours, never the absolute number.", "",
           "| Speaker | Turns | Characters | Share | Question lines |", "| --- | --- | --- | --- | --- |"]
    out += [f"| {w} | {total[w][0]} | {total[w][1]} | {round(100 * total[w][1] / allc)}% | {total[w][2]} |" for w in names]
    out += ["", "## By hour of the recording", "",
            "| Hour | " + " | ".join(f"{w} share" for w in names) + " |",
            "| --- | " + " | ".join("---" for _ in names) + " |"]
    for h in sorted(hours):
        c = sum(v[0] for v in hours[h].values()) or 1
        out.append(f"| {h}:00 to {h + 1}:00 | " + " | ".join(f"{round(100 * hours[h][w][0] / c)}%" for w in names) + " |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export")
    ap.add_argument("--out")
    ap.add_argument("--map", action="append", default=[], help="'Name in the export=Name in the turns'")
    ap.add_argument("--stats")
    ap.add_argument("--speakers", action="store_true")
    a = ap.parse_args(argv)
    mapping = {}
    for p in a.map:
        if "=" not in p:
            sys.exit(f"md_turns: --map takes 'Old=New', got {p!r}")
        k, v = p.split("=", 1)
        mapping[k.strip()] = v.strip()
    text = open(a.export, encoding="utf-8").read()
    ts = turns(text, mapping)
    if not ts:
        sys.exit("md_turns: no timed turns found; export the transcript with timestamps")
    if a.speakers:
        print(speakers(ts))
    if a.out:
        title = a.export.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        open(a.out, "w", encoding="utf-8").write(render(ts, title))
        print(f"md_turns: {len(ts)} turns written to {a.out}")
    if a.stats:
        open(a.stats, "w", encoding="utf-8").write(stats(ts))
        print(f"md_turns: statistics written to {a.stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
