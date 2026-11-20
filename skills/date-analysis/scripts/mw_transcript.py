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
  mw_transcript.py export <session> --out <file.md> [--map "Speaker 2=Mina" ...]
      The transcript as numbered turns, one line per turn:
      `T0123 [1:02:03] Mina: text`. Consecutive lines of one speaker are one
      turn. A speaker without a --map entry keeps its MacWhisper name.
  mw_transcript.py stats <session> [--map ...] [--out <file.md>]
      Talk time, turns, characters and questions per speaker; the same per hour
      of the recording; and each speaker's ten longest turns.
  mw_transcript.py md <session> [--her NAME] [--out <file.md>] [--force]
      The transcript in the Markdown Chaehan exports from the app (a `**Name**`
      line, a `*h:mm:ss*` line and the text), written beside the recording in
      the Affinity folder on Drive, with the two speakers who talk most named:
      Chaehan and her. A name the app already holds is kept; two unnamed
      speakers are told apart by voice pitch (his is the lower voice), read from
      the app's own copy of the audio. Needs numpy and ffmpeg, so run it as
      `mamba run -n socrates python mw_transcript.py md ...`. A file that is
      already there is Chaehan's own export and is never overwritten without
      --force (Chaehan, 2026-11-20: "can you export the transcripts as md file
      yourself ... label at least the first two speakers").

<session> is the recording's file name as MacWhisper shows it (for example
"2026-11-11 Mina Lee Date3" or "2026-11-11"), or the session id in hex.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sqlite3
import sys
import subprocess
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path

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


def nfc(s: str | None) -> str:
    return unicodedata.normalize("NFC", s or "")


def find_session(con: sqlite3.Connection, key: str) -> sqlite3.Row:
    """The newest live session whose id, file name or title is `key`, else whose file name holds it. The app
    stores a Korean file name decomposed (NFD), so names are compared composed: on 2026-11-20
    "2026-11-19 Date 지원" was not found by a plain SQL match."""
    rows = con.execute("select * from session where dateDeleted is null order by dateCreated desc").fetchall()
    k = nfc(key)
    hit = [r for r in rows if r["id"].hex().upper() == k.upper()
           or k in (nfc(r["originalFilename"]), nfc(r["userChosenTitle"]))]
    hit = hit or [r for r in rows if k and k in nfc(r["originalFilename"])]
    if not hit:
        sys.exit(f"mw_transcript: no live session matches {key!r}; run `list`")
    return hit[0]


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


UNNAMED = re.compile(r"^(Speaker \d+|\?)$")
MIN_GAP_HZ = 15  # on 2026-11-20 his voice read 26-96 Hz below hers in six recordings he had labelled himself


def audio_of(con: sqlite3.Connection, sid: bytes, db: str = DB) -> str | None:
    """The app's own copy of the recording (Database/ExternalMedia), or None."""
    try:
        row = con.execute("select filename from mediafile where sessionID = ? and type = 'original'", (sid,)).fetchone()
    except sqlite3.OperationalError:
        return None
    path = os.path.join(os.path.dirname(db), "ExternalMedia", row[0]) if row else None
    return path if path and os.path.exists(path) else None


def pitch_hz(path: str, spans: list[tuple[int, int]]) -> float | None:
    """Median voice pitch over the spans (ms), by autocorrelation of 64 ms frames: the loudest 40% of frames,
    a lag between 2.5 ms (400 Hz) and 14 ms (70 Hz), a peak of at least 0.4. Each span is cut by ffmpeg."""
    import numpy as np
    sr, w, h = 16000, 1024, 320
    per = []
    for a, b in spans:
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{a / 1000:.2f}", "-t", f"{(b - a) / 1000:.2f}", "-i", path,
                              "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
        y = np.frombuffer(raw, dtype=np.float32)
        if len(y) < sr // 2:
            continue
        fr = np.stack([y[i * h:i * h + w] for i in range(1 + (len(y) - w) // h)])
        fr = fr - fr.mean(1, keepdims=True)
        e = (fr ** 2).sum(1)
        fr = fr[e > np.percentile(e, 60)]
        spec = np.fft.rfft(fr, 2 * w)
        ac = np.fft.irfft(spec * np.conj(spec))[:, :w]
        ac = ac / np.maximum(ac[:, :1], 1e-12)
        lo, hi = sr // 400, sr // 70
        lag = lo + ac[:, lo:hi].argmax(1)
        f = sr / lag[ac[np.arange(len(ac)), lag] > 0.4]
        if len(f) > 5:
            per.append(float(np.median(f)))
    return float(np.median(per)) if len(per) >= 5 else None


def spans_of(lines: list[dict], who: str, n: int = 25) -> list[tuple[int, int]]:
    """Up to n of a speaker's lines of 2 to 8 s, spread evenly over the recording."""
    ok = [(ln["start"], ln["end"]) for ln in lines if ln["speaker"] == who and 2000 <= ln["end"] - ln["start"] <= 8000]
    step = max(1, len(ok) // n)
    return ok[::step][:n]


TITLE_WORDS_FILE = Path(os.path.expanduser(
    os.environ.get("AGENTKIT_DATE_TITLE_WORDS", "~/.config/agentkit/date_title_words.txt")))


def title_words() -> list[str]:
    """The words your recording titles carry besides the date, such as an agency name."""
    try:
        raw = TITLE_WORDS_FILE.read_text(encoding="utf-8")
    except OSError:
        return []
    return [w.strip() for w in re.split(r"[,\n]", raw) if w.strip()]


def her_name(title: str) -> str:
    """Her name from a recording title: the words left after the date, the title words and Date<N>.

    The title words are what your own recordings carry besides the date, such as an agency name,
    read from `~/.config/agentkit/date_title_words.txt` one per line or comma-separated. The script
    ships with none, so a public title parses as it stands."""
    stop = "|".join([r"\d{4}-\d{2}-\d{2}", r"Date\d*"] + [re.escape(w) for w in title_words()])
    words = [w for w in nfc(title).split() if not re.fullmatch(stop, w, re.I)]
    return " ".join(words)


def name_speakers(lines: list[dict], her: str, audio: str | None,
                  pitch=pitch_hz) -> tuple[dict[str, str], str]:
    """Names for the two speakers who talk most, and one line saying how they were told apart.

    A name the app holds is kept. One unnamed speaker beside a named one takes the other name. Two unnamed
    speakers are told apart by pitch: the lower voice is Chaehan. Closer than MIN_GAP_HZ, or without the
    audio, they stay unnamed and the agent names them by their words (skill step 2)."""
    talk: dict[str, int] = defaultdict(int)
    for ln in lines:
        talk[ln["speaker"]] += max(0, ln["end"] - ln["start"])
    top = sorted(talk, key=lambda w: -talk[w])[:2]
    if len(top) < 2:
        return {}, "one speaker only: nothing to tell apart"
    unnamed = [w for w in top if UNNAMED.match(w)]
    if not unnamed:
        return {}, f"kept the app's names: {top[0]} and {top[1]}"
    if len(unnamed) == 1:
        named = next(w for w in top if w not in unnamed)
        other = her if named == "Chaehan" else "Chaehan"
        return {unnamed[0]: other}, f"{named} kept from the app, so {unnamed[0]} is {other}"
    if not audio:
        return {}, "no audio in the app's store: both speakers stay unnamed; name them by their words"
    try:
        hz = {w: pitch(audio, spans_of(lines, w)) for w in top}
    except ImportError:
        return {}, "numpy is missing (run with mamba run -n socrates python): both speakers stay unnamed"
    if None in hz.values():
        return {}, f"pitch unreadable ({hz}): both speakers stay unnamed; name them by their words"
    low, high = sorted(top, key=lambda w: hz[w])
    if hz[high] - hz[low] < MIN_GAP_HZ:
        return {}, (f"voices too close ({low} {hz[low]:.0f} Hz, {high} {hz[high]:.0f} Hz): both stay unnamed; "
                    "name them by their words")
    return {low: "Chaehan", high: her}, (f"by pitch: {low} {hz[low]:.0f} Hz is Chaehan, "
                                          f"{high} {hz[high]:.0f} Hz is {her}")


def export_md(title: str, lines: list[dict], names: dict[str, str]) -> str:
    """Chaehan's export format: a name line where the speaker changes, a time line and the text per line."""
    out, last = [f"# {nfc(title)}", ""], None
    for ln in lines:
        text = ln["text"].strip()
        if not text:
            continue
        who = names.get(ln["speaker"], ln["speaker"])
        if who != last:
            out += [f"**{who}**", ""]
            last = who
        out += [f"*{hms(ln['start'])}*", "", text, ""]
    return "\n".join(out)


def affinity_dir() -> Path | None:
    hits = sorted(Path.home().glob("Library/CloudStorage/GoogleDrive-*/My Drive/1 Projects/Affinity"))
    return hits[0] if hits else None


def md_target(title: str) -> Path | None:
    """Beside the recording's audio in the Affinity folder tree, else in the Affinity folder itself."""
    root = affinity_dir()
    if not root:
        return None
    stem = nfc(title)
    for p in root.rglob("*"):
        if p.suffix.lower() in (".m4a", ".mp3", ".wav") and nfc(p.stem) == stem:
            return p.with_name(stem + ".md")
    return root / (stem + ".md")


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
    md = sub.add_parser("md"); md.add_argument("session"); md.add_argument("--her"); md.add_argument("--out")
    md.add_argument("--force", action="store_true")
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

    if a.cmd == "md":
        out = Path(a.out) if a.out else md_target(title)
        if out is None:
            sys.exit("mw_transcript: no Affinity folder on Drive; give --out")
        if out.exists() and not a.force:
            print(f"mw_transcript: {out} exists, and it is Chaehan's own export: use it, or pass --force", file=sys.stderr)
            return 4
        names, how = name_speakers(lines, a.her or her_name(title) or "Her", audio_of(con, s["id"], a.db))
        out.write_text(export_md(title, lines, names), encoding="utf-8")
        print(f"wrote {out}: {len(lines)} lines; {how}")
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
