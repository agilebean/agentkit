#!/usr/bin/env python3
"""Read a date recording's transcript out of MacWhisper (the "Whisper
Transcription" app) and count who talked how much.

MacWhisper keeps every transcript in a SQLite database inside its sandbox
container. This script copies that database (with its write-ahead log) to a
temporary folder and reads the copy, so the running app is never touched.

Usage:
  mw_transcript.py list
      The recent sessions: file name, audio length, whether transcription and
      speaker recognition finished, and the speakers it found.
  mw_transcript.py speakers <session>
      Per raw speaker: talk time, turn count and their eight longest turns, so
      the agent can tell who is who before it names them.
  mw_transcript.py export <session> --out <file.md> [--map "Speaker 2=Jiyoung" ...]
      The transcript as numbered turns, one line per turn:
      `T0123 [1:02:03] Jiyoung: text`. Consecutive lines of one speaker are one
      turn. A speaker without a --map entry keeps its MacWhisper name.
  mw_transcript.py stats <session> [--map ...] [--out <file.md>]
      Talk time, turns, characters and questions per speaker; the same per hour
      of the recording; and each speaker's ten longest turns.

<session> is the recording's file name as MacWhisper shows it (for example
"2026-11-11 Jiyoung Kim Date3" or "2026-11-11"), or the session id in hex.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from collections import defaultdict

DB = os.path.expanduser(
    "~/Library/Containers/com.goodsnooze.MacWhisper/Data/Library/Application Support/"
    "MacWhisper/Database/main.sqlite")

# A Korean or English question: a question mark, or a sentence-final ending
# that asks (까, 니, 나요, 래요, 죠 with rising intent is too ambiguous to count).
QUESTION = re.compile(r"\?\s*$|(?:까요|나요|니까|을까|ㄹ까|는지요|어때요|뭐예요|뭐에요|왜요)\.?\s*$")


def hms(ms: int) -> str:
    s = int(ms // 1000)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


def open_copy(db: str = DB) -> sqlite3.Connection:
    """A read-only connection to a fresh copy of MacWhisper's database."""
    if not os.path.exists(db):
        sys.exit(f"mw_transcript: no MacWhisper database at {db}")
    tmp = tempfile.mkdtemp(prefix="mw_")
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(db + suffix):
            shutil.copy2(db + suffix, os.path.join(tmp, "main.sqlite" + suffix))
    con = sqlite3.connect(os.path.join(tmp, "main.sqlite"))
    con.row_factory = sqlite3.Row
    return con


def find_session(con: sqlite3.Connection, key: str) -> sqlite3.Row:
    rows = con.execute(
        "select * from session where dateDeleted is null and "
        "(hex(id) = upper(?) or originalFilename = ? or userChosenTitle = ?) "
        "order by dateCreated desc", (key, key, key)).fetchall()
    if not rows:
        rows = con.execute(
            "select * from session where dateDeleted is null and originalFilename like ? "
            "order by dateCreated desc", (f"%{key}%",)).fetchall()
    if not rows:
        sys.exit(f"mw_transcript: no live session matches {key!r}; run `list`")
    return rows[0]


def lines_of(con: sqlite3.Connection, sid: bytes) -> list[dict]:
    q = ("select t.text, t.start, t.end, coalesce(sp.name, '?') as speaker "
         "from transcriptline t left join speaker sp on sp.id = t.speakerID "
         "where t.sessionId = ? order by t.orderIndex, t.start")
    return [dict(r) for r in con.execute(q, (sid,))]


def parse_map(pairs: list[str]) -> dict[str, str]:
    out = {}
    for p in pairs or []:
        if "=" not in p:
            sys.exit(f"mw_transcript: --map takes 'Raw name=New name', got {p!r}")
        raw, new = p.split("=", 1)
        out[raw.strip()] = new.strip()
    return out


def turns_of(lines: list[dict], names: dict[str, str]) -> list[dict]:
    """Consecutive lines of one speaker joined into one turn."""
    turns: list[dict] = []
    for ln in lines:
        who = names.get(ln["speaker"], ln["speaker"])
        text = ln["text"].strip()
        if not text:
            continue
        if turns and turns[-1]["speaker"] == who:
            t = turns[-1]
            t["text"] += " " + text
            t["end"] = ln["end"]
            t["talk"] += max(0, ln["end"] - ln["start"])
            t["lines"].append(text)
        else:
            turns.append({"speaker": who, "start": ln["start"], "end": ln["end"], "text": text,
                          "talk": max(0, ln["end"] - ln["start"]), "lines": [text]})
    for i, t in enumerate(turns, 1):
        t["n"] = i
    return turns


def is_question(text: str) -> bool:
    return bool(QUESTION.search(text.strip()))


def stats_md(turns: list[dict], title: str) -> str:
    who = sorted({t["speaker"] for t in turns}, key=lambda w: -sum(t["talk"] for t in turns if t["speaker"] == w))
    total = sum(t["talk"] for t in turns) or 1
    out = [f"# Talk statistics: {title}", "",
           "Talk time sums the spoken spans MacWhisper timed for each line; silence and overlap are not counted. "
           "Question lines are lines that end in a question mark or a Korean question ending; MacWhisper adds "
           "question marks freely, so compare the two speakers and the hours, never the absolute number.",
           "", "| Speaker | Talk min | Share | Turns | Characters | Question lines | Median turn s |",
           "| --- | --- | --- | --- | --- | --- | --- |"]
    for w in who:
        ts = [t for t in turns if t["speaker"] == w]
        talk = sum(t["talk"] for t in ts)
        chars = sum(len(t["text"]) for t in ts)
        qs = sum(1 for t in ts for s in t["lines"] if is_question(s))
        med = sorted(t["talk"] for t in ts)[len(ts) // 2] / 1000 if ts else 0
        out.append(f"| {w} | {talk / 60000:.0f} | {100 * talk / total:.0f}% | {len(ts)} | {chars} | {qs} | {med:.0f} |")
    out += ["", "## By hour of the recording", "",
            "| Hour | " + " | ".join(f"{w} share" for w in who[:3]) + " | " + " | ".join(f"{w} question lines" for w in who[:3]) + " |",
            "| --- |" + " --- |" * (2 * len(who[:3]))]
    hours = defaultdict(lambda: defaultdict(int))
    qh = defaultdict(lambda: defaultdict(int))
    for t in turns:
        h = t["start"] // 3600000
        hours[h][t["speaker"]] += t["talk"]
        qh[h][t["speaker"]] += sum(1 for s in t["lines"] if is_question(s))
    for h in sorted(hours):
        tot = sum(hours[h].values()) or 1
        out.append(f"| {h}:00 to {h + 1}:00 | " + " | ".join(f"{100 * hours[h][w] / tot:.0f}%" for w in who[:3])
                   + " | " + " | ".join(str(qh[h][w]) for w in who[:3]) + " |")
    for w in who[:2]:
        out += ["", f"## {w}: the ten longest turns", "", "| Turn | Start | Seconds | Opening words |", "| --- | --- | --- | --- |"]
        for t in sorted((t for t in turns if t["speaker"] == w), key=lambda t: -t["talk"])[:10]:
            out.append(f"| T{t['n']:04d} | {hms(t['start'])} | {t['talk'] / 1000:.0f} | {t['text'][:60].replace('|', '/')} |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=DB, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sp = sub.add_parser("speakers"); sp.add_argument("session")
    ex = sub.add_parser("export"); ex.add_argument("session"); ex.add_argument("--out", required=True)
    ex.add_argument("--map", action="append", default=[])
    st = sub.add_parser("stats"); st.add_argument("session"); st.add_argument("--out")
    st.add_argument("--map", action="append", default=[])
    a = ap.parse_args(argv)
    con = open_copy(a.db)

    if a.cmd == "list":
        for r in con.execute("select * from session where dateDeleted is null order by dateCreated desc limit 12"):
            spk = [x[0] for x in con.execute(
                "select distinct coalesce(sp.name,'?') from transcriptline t left join speaker sp on sp.id=t.speakerID "
                "where t.sessionId=?", (r["id"],))]
            print(f"{r['originalFilename'] or r['userChosenTitle']} | {hms(int((r['playbackDuration'] or 0) * 1000))} | "
                  f"transcribed {bool(r['transcriptionDidSucceed'])} | speakers recognised {bool(r['hasBeenDiarized'])} | "
                  f"{', '.join(sorted(spk))} | {r['id'].hex()}")
        return 0

    s = find_session(con, a.session)
    title = s["originalFilename"] or s["userChosenTitle"] or s["id"].hex()
    if not s["transcriptionDidSucceed"]:
        print(f"mw_transcript: {title!r} is still being transcribed (or failed); wait for MacWhisper to finish",
              file=sys.stderr)
        return 3
    lines = lines_of(con, s["id"])

    if a.cmd == "speakers":
        raw = turns_of(lines, {})
        for w in sorted({t["speaker"] for t in raw}, key=lambda w: -sum(t["talk"] for t in raw if t["speaker"] == w)):
            ts = [t for t in raw if t["speaker"] == w]
            print(f"\n## {w}: {sum(t['talk'] for t in ts) / 60000:.0f} min, {len(ts)} turns")
            for t in sorted(ts, key=lambda t: -len(t["text"]))[:8]:
                print(f"  [{hms(t['start'])}] {t['text'][:160]}")
        return 0

    turns = turns_of(lines, parse_map(a.map))
    if a.cmd == "export":
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(f"# {title}\n\nAutomatic transcript from MacWhisper, {hms(int(s['playbackDuration'] * 1000))} of audio. "
                     f"One line per turn: turn number, time into the recording, speaker.\n\n")
            for t in turns:
                fh.write(f"T{t['n']:04d} [{hms(t['start'])}] {t['speaker']}: {t['text']}\n")
        print(f"wrote {a.out}: {len(turns)} turns, {sum(len(t['text']) for t in turns)} characters")
        return 0

    md = stats_md(turns, title)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(md)
        print(f"wrote {a.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
