#!/usr/bin/env python3
"""The decision test for a whole note (human quality plan, task HQ-01).

After one read of a note, can its decisions, their deadlines and what each depends on be named? A fresh
DeepSeek call with no other context reads the note and lists the decisions it states, one row each: what
Chaehan decides, by when, the options, and the note's first line that states it. A second fresh call reads
the Takeaway alone. A matching step pairs each call's rows with the gold list Chaehan confirmed for the
note's date (decision D1 of the plan), by shared content words or by a judge call that sees one pair at a
time. The script prints recall overall and within the Takeaway, the decisions the note states that the
gold list lacks, the wrong deadlines, and the Takeaway line on which the decision due soonest appears.

    python3 scripts/decision_eval.py <note.md> --gold <gold.tsv> [--date 2026-11-09] [--runs 3]
    python3 scripts/decision_eval.py --pairs [<pairs.tsv>] --runs 3 --out runs.json
    python3 scripts/decision_eval.py --pairs [<pairs.tsv>] --from runs.json     # score saved reads again

A gold file is a TSV with the columns id, decision, deadline (YYYY-MM-DD or none), options, depends and
source; a line that starts with # is a comment. A pairs file has the columns pair, date, preferred,
rejected and gold, with paths relative to its own folder, and may have a column role: acceptance (the
default) or control, a pair whose Takeaways are the same text and must tie. Its default is
decision_test/pairs.tsv in the human quality data folder in socrates, since the gold lists and the notes
are Chaehan's private data. With --pairs the script exits 0 when a matching method ranks every preferred
build above its rejected one on Takeaway recall in every run of every acceptance pair, 1 when none does,
and 2 when a call failed in some run, since such a run measures the route and not the note.

Overall recall comes from the read of the whole note, Takeaway recall from the read of the Takeaway alone,
so a decision the Takeaway only hints at counts where a reader of the Takeaway would find it. The soonest
decision is the gold row with the earliest deadline on or after the note's date; rows that share that
deadline are all reported. A decision is due within 30 days when its deadline falls on or before the
note's date plus 30 days, an overdue one included.

Every call goes through one gate of --calls at a time (default 4), and a call refused with HTTP 429 waits
15, 30, 60 and 120 s before it gives up: on 2026-11-20 four notes with eight judge calls each in flight
drew rate-limit refusals from the OpenCode Go route, and every call after them failed within a second.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


DATA = _mod("say").DATA
PAIRS = DATA / "decision_test" / "pairs.tsv"
METHODS = ("words", "judge")

READ_PROMPT = """You read a note written for Chaehan. List every decision the note says he faces: a choice he \
has to make, or a step only he can take, that is still open on the note's date. Leave out what the note \
reports as done, decided with nothing left to do, or in other people's hands.

Write one line per decision, with four fields separated by a tab:
decision<TAB>deadline<TAB>options<TAB>first line

- decision: what he decides or has to do, in one short sentence.
- deadline: the date by which it has to be done or decided, as YYYY-MM-DD, when the note gives one; \
otherwise none.
- options: the choices the note names for it, separated by " / "; none when it names none.
- first line: the first line of the note in which this decision appears, copied exactly.

Write these lines and nothing else."""

JUDGE_PROMPT = """You compare two decisions. The first comes from a list the reader confirmed; the second was \
read out of a note. Answer same when both are one decision about one matter, even when the wording, the \
detail or the options differ. Answer different when they concern different matters, or when the second is \
a fact or an event that leaves nothing to decide or do. Answer with the one word same or different."""

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RULE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")
TAKEAWAY = re.compile(r"^(takeaway|summary)\b", re.I)
MARK = re.compile(r"^(\d+[.)]|[-*•]|\|)\s*")
REFUSED = re.compile(r"\b429\b|rate.?limit", re.I)
WAITS = (15, 30, 60, 120)
GATE = threading.BoundedSemaphore(4)


def complete(messages: list[dict], model: str | None = None, max_tokens: int = 32000, temperature: float = 0.3) -> str:
    return _mod("say").complete(messages, model=model, max_tokens=max_tokens, temperature=temperature)


def _call(messages: list[dict], model: str | None, temperature: float = 0.3) -> tuple[str, str]:
    """(the answer, "") or ("", the reason). A rate-limit refusal waits and tries again; any other failure,
    or the last refusal, is returned as the reason, so a failed call never stops the other notes."""
    reason = ""
    for wait in (*WAITS, None):
        with GATE:
            try:
                return complete(messages, model=model, temperature=temperature), ""
            except Exception as e:  # noqa: BLE001 - any failure of the route is reported, not raised
                reason = str(e)
        if wait is None or not REFUSED.search(reason):
            break
        time.sleep(wait)
    return "", f"no answer ({reason[:100]})"


# ---- gold lists and notes ---------------------------------------------------------

def date_of(text: str | None) -> str | None:
    m = DATE.search(text or "")
    return m.group(0) if m else None


def load_tsv(path: Path) -> list[dict]:
    lines = [l for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE)]


def load_gold(path: Path) -> list[dict]:
    rows = load_tsv(path)
    for r in rows:
        r["deadline"] = date_of(r.get("deadline"))
        r["options"] = "" if r.get("options", "").lower() == "none" else r.get("options", "")
    return rows


def body(text: str) -> str:
    """The note without its title line: the call is told the date, and a title that names the build
    (step 8's "version A4: cards chosen by card_choose.py") says nothing about decisions."""
    return "\n".join(l for l in text.splitlines() if not re.match(r"#\s", l)).strip() + "\n"


def takeaway(text: str) -> str:
    """The Takeaway or Summary section with its heading and subsections, up to the next # or ## heading."""
    out, inside = [], False
    for line in text.splitlines():
        m = HEADING.match(line)
        if m and len(m.group(1)) <= 2:
            if inside:
                break
            inside = len(m.group(1)) == 2 and bool(TAKEAWAY.match(m.group(2)))
        if inside:
            out.append(line)
    return "\n".join(out).strip() + "\n" if out else ""


def lines_of(text: str) -> list[str]:
    """The lines a reader counts: every line but a blank, a heading and a table's rule."""
    return [l.strip() for l in text.splitlines() if l.strip() and not HEADING.match(l) and not RULE.match(l.strip())]


def words(text: str) -> set[str]:
    """The content words of wording_eval.py, without a year or a one- or two-digit number, which any two
    dated lines share."""
    out = {w.strip(".:") for w in _mod("wording_eval").content_words(text or "")}
    return {w for w in out if w and not re.fullmatch(r"\d{1,2}|20\d\d", w)}


# ---- the read -------------------------------------------------------------------------

def parse_rows(text: str) -> list[dict]:
    """The reader's lines as rows of decision, deadline, options and the line it copied."""
    rows = []
    for raw in text.splitlines():
        parts = [p.strip() for p in raw.strip().strip("`").split("\t")]
        if len(parts) < 2 and " | " in raw:
            parts = [p.strip() for p in raw.strip().strip("|").split(" | ")]
        if len(parts) < 2:
            continue
        decision = MARK.sub("", parts[0].replace("**", "")).strip()
        if not re.search(r"\w", decision) or (decision.lower() == "decision" and parts[1].lower() == "deadline"):
            continue
        options = parts[2] if len(parts) > 2 else ""
        rows.append({"decision": decision, "deadline": date_of(parts[1]),
                     "options": "" if options.lower() in ("none", "-", "") else options,
                     "line": "\t".join(parts[3:]).strip()})
    return rows


def read(text: str, date: str | None, model: str | None) -> tuple[list[dict], str, bool]:
    """A fresh call with the reading prompt and the text, and nothing else: (rows, the raw answer or the
    reason it failed, whether it failed)."""
    head = f"The note is dated {date}.\n\n" if date else ""
    answer, why = _call([{"role": "system", "content": READ_PROMPT}, {"role": "user", "content": head + text}], model)
    return (parse_rows(answer), answer, False) if not why else ([], why, True)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", MARK.sub("", s.strip()).replace("**", "")).strip().lower()


def locate(quote: str, lines: list[str]) -> int | None:
    """The index of the line a quote was copied from: one holds the other, else the line that shares the
    most of the quote's content words, 60% or more."""
    q = _norm(quote)
    if not q:
        return None
    for i, line in enumerate(lines):
        n = _norm(line)
        if n and (q in n or (len(n) >= 12 and n in q)):
            return i
    qw = words(quote)
    best, at = 0.0, None
    for i, line in enumerate(lines):
        if qw and (share := len(qw & words(line)) / len(qw)) > best:
            best, at = share, i
    return at if best >= 0.6 else None


# ---- matching ---------------------------------------------------------------------------

def text_of(row: dict) -> str:
    return f"{row['decision']} {row.get('options', '')}"


def word_score(a: dict, b: dict) -> float:
    """Shared content words over the shorter row's count, decision and options together."""
    wa, wb = words(text_of(a)), words(text_of(b))
    return len(wa & wb) / min(len(wa), len(wb)) if wa and wb else 0.0


def _assign(candidates: list[tuple[float, int, int]]) -> dict[int, int]:
    """One gold row to one note row, highest score first: {gold index: row index}."""
    out, used = {}, set()
    for _, g, r in sorted(candidates, key=lambda t: -t[0]):
        if g not in out and r not in used:
            out[g] = r
            used.add(r)
    return out


def match_words(gold: list[dict], rows: list[dict], threshold: float = 0.34) -> dict[int, int]:
    return _assign([(s, g, r) for g, gr in enumerate(gold) for r, rr in enumerate(rows)
                    if (s := word_score(gr, rr)) >= threshold])


def judge(gold_row: dict, row: dict, model: str | None) -> bool | None:
    """One fresh call on one pair, at temperature 0: does the note's row state the gold decision? None when
    the call failed, which never counts as "different". The gold row brings what it depends on, which is
    often how a note names it ("your deciding question is the job offer" for the flat that depends on it).
    On 2026-11-20 a judge at 0.3 called one pair same for one read and different for the other."""
    pair = (f"First: {gold_row['decision']}\nOptions: {gold_row.get('options') or 'none'}\n"
            f"Depends on: {gold_row.get('depends') or 'none'}\n\n"
            f"Second: {row['decision']}\nOptions: {row.get('options') or 'none'}")
    answer, why = _call([{"role": "system", "content": JUDGE_PROMPT}, {"role": "user", "content": pair}], model, 0.0)
    if why:
        return None
    m = re.search(r"\b(same|different)\b", answer.lower())
    return bool(m) and m.group(1) == "same"


def match_judge(gold: list[dict], rows: list[dict], model: str | None, candidates: int = 3,
                workers: int = 8) -> tuple[dict[int, int], list[list]]:
    """Each gold row against the note rows that share the most words with it, one judge call a pair:
    ({gold index: row index}, every pair judged as [gold id, row index, same, different or failed])."""
    pairs = []
    for g, gr in enumerate(gold):
        ranked = sorted(((word_score(gr, rr), r) for r, rr in enumerate(rows)), key=lambda t: (-t[0], t[1]))
        pairs += [(s, g, r) for s, r in ranked[:candidates]]
    if not pairs:
        return {}, []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        verdicts = list(pool.map(lambda p: judge(gold[p[1]], rows[p[2]], model), pairs))
    judged = [[gold[g]["id"], r, {True: "same", False: "different", None: "failed"}[v]]
              for (_, g, r), v in zip(pairs, verdicts)]
    return _assign([p for p, v in zip(pairs, verdicts) if v]), judged


def match(method: str, gold: list[dict], rows: list[dict], model: str | None, candidates: int = 3,
          workers: int = 8) -> tuple[dict[int, int], list[list]]:
    if method == "words":
        return match_words(gold, rows), []
    return match_judge(gold, rows, model, candidates, workers)


# ---- the numbers -----------------------------------------------------------------------

def log(message: str) -> None:
    """Progress on stderr, so a run in the background shows where it is."""
    print(message, file=sys.stderr, flush=True)


def plus(date: str, days: int) -> str:
    return (dt.date.fromisoformat(date) + dt.timedelta(days=days)).isoformat()


def soonest(gold: list[dict], date: str | None) -> list[int]:
    """The gold rows with the earliest deadline on or after the note's date (any date when none is left)."""
    dated = [g["deadline"] for g in gold if g["deadline"]]
    pool = [d for d in dated if not date or d >= date] or dated
    return [i for i, g in enumerate(gold) if pool and g["deadline"] == min(pool)]


def measure(gold: list[dict], whole: list[dict], m_whole: dict[int, int], tk: list[dict],
            m_tk: dict[int, int], date: str | None) -> dict:
    due = [i for i, g in enumerate(gold) if date and g["deadline"] and g["deadline"] <= plus(date, 30)]
    first = {}
    for i in soonest(gold, date):
        if i in m_tk:
            at = tk[m_tk[i]].get("at")
            first[gold[i]["id"]] = at + 1 if at is not None else "Takeaway, line not found"
        else:
            first[gold[i]["id"]] = "body" if i in m_whole else "absent"
    return {
        "gold": len(gold),
        "recall": len(m_whole),
        "takeaway": len(m_tk),
        "due": len(due),
        "due_in_takeaway": sum(1 for i in due if i in m_tk),
        "found": [gold[i]["id"] for i in sorted(m_whole)],
        "in_takeaway": [gold[i]["id"] for i in sorted(m_tk)],
        "invented": [r["decision"] for j, r in enumerate(whole) if j not in m_whole.values()],
        "wrong_deadline": [[gold[g]["id"], whole[r]["deadline"], gold[g]["deadline"]] for g, r in sorted(m_whole.items())
                           if gold[g]["deadline"] and whole[r]["deadline"] and whole[r]["deadline"] != gold[g]["deadline"]],
        "no_deadline": [gold[g]["id"] for g, r in sorted(m_whole.items()) if gold[g]["deadline"] and not whole[r]["deadline"]],
        "soonest": first,
    }


def evaluate(note: str, gold: list[dict], date: str | None, model: str | None = None,
             methods: tuple[str, ...] = METHODS, candidates: int = 3, workers: int = 8, label: str = "") -> dict:
    """One run on one note: the two reads, then every matching method on the same rows. "failed" counts
    the calls that gave no answer; a run with any is incomplete."""
    t = time.time()
    whole, whole_raw, f1 = read(body(note), date, model)
    log(f"{label}read the whole note: {len(whole)} rows, {round(time.time() - t)} s" + (f", {whole_raw}" if f1 else ""))
    tk_text = takeaway(note)
    tk, tk_raw, f2 = read(tk_text, date, model) if tk_text else ([], "the note has no Takeaway or Summary", False)
    log(f"{label}read the Takeaway: {len(tk)} rows, {round(time.time() - t)} s" + (f", {tk_raw}" if f2 else ""))
    tk_lines = lines_of(tk_text)
    for row in tk:
        row["at"] = locate(row["line"], tk_lines)
    out = {"whole": whole, "whole_raw": whole_raw, "takeaway_rows": tk, "takeaway_raw": tk_raw,
           "takeaway_lines": len(tk_lines), "calls": 2, "failed": int(f1) + int(f2), "by": {}}
    for method in methods:
        m_whole, j1 = match(method, gold, whole, model, candidates, workers)
        m_tk, j2 = match(method, gold, tk, model, candidates, workers)
        failed = sum(1 for j in j1 + j2 if j[2] == "failed")
        out["calls"] += len(j1) + len(j2)
        out["failed"] += failed
        if method == "judge":
            log(f"{label}judged {len(j1) + len(j2)} pairs, {failed} failed, {round(time.time() - t)} s")
        out["by"][method] = measure(gold, whole, m_whole, tk, m_tk, date) | {
            "pairs_whole": {gold[g]["id"]: r for g, r in m_whole.items()},
            "pairs_takeaway": {gold[g]["id"]: r for g, r in m_tk.items()},
            "judged_whole": j1, "judged_takeaway": j2}
    out["seconds"] = round(time.time() - t)
    return out


def summary(m: dict) -> str:
    wrong = ", ".join(f"{g} (note {n}, gold {d})" for g, n, d in m["wrong_deadline"]) or "none"
    first = ", ".join(f"{g} " + (f"line {v}" if isinstance(v, int) else str(v)) for g, v in m["soonest"].items()) or "no dated decision"
    return (f"recall {m['recall']} of {m['gold']}, Takeaway {m['takeaway']} of {m['gold']}"
            f" (due within 30 days {m['due_in_takeaway']} of {m['due']}); invented {len(m['invented'])};"
            f" wrong deadline {wrong}; no deadline {', '.join(m['no_deadline']) or 'none'}; soonest {first}")


# ---- pairs --------------------------------------------------------------------------------

def note_date(path: Path, text: str) -> str | None:
    title = next((l for l in text.splitlines() if l.startswith("# ")), "")
    return date_of(title) or date_of(path.name)


def run_pairs(path: Path, runs: int, methods: tuple[str, ...], model: str | None, candidates: int,
              workers: int, notes: int = 4) -> list[dict]:
    """Every pair, each build, each run, read and matched: the results, one per note and run."""
    base, pairs = path.parent, load_tsv(path)
    jobs = [(p, k, side) for k in range(1, runs + 1) for p in pairs for side in ("preferred", "rejected")]
    golds = {p["pair"]: load_gold(base / p["gold"]) for p in pairs}

    def one(job):
        p, k, side = job
        note = (base / p[side]).read_text(encoding="utf-8")
        return {"pair": p["pair"], "run": k, "side": side, "note": p[side], "date": p["date"],
                "role": p.get("role") or "acceptance",
                **evaluate(note, golds[p["pair"]], p["date"] or None, model, methods, candidates, workers,
                           label=f"{p['pair']} run {k} {side}: ")}

    with ThreadPoolExecutor(max_workers=notes) as pool:
        return list(pool.map(one, jobs))


def report(path: Path, results: list[dict], methods: tuple[str, ...]) -> tuple[dict[str, int], int, int]:
    """Each pair of the pairs file against the results of its two notes, found by pair, run and note path,
    so a preference Chaehan changes after a run (2026-11-21: A4 over B) is scored from the same reads:
    (separated acceptance pair-runs per method, acceptance pair-runs, pair-runs with a failed call)."""
    separated, total, incomplete = {m: 0 for m in methods}, 0, 0
    for p in load_tsv(path):
        control = (p.get("role") or "acceptance") == "control"
        print(f"{p['pair']} ({p['date']}{', control: the Takeaways are one text and must tie' if control else ''}):"
              f" preferred {p['preferred']}, rejected {p['rejected']}")
        runs = sorted({r["run"] for r in results if r["pair"] == p["pair"]})
        for k in runs:
            pref = next(r for r in results if r["pair"] == p["pair"] and r["run"] == k and r["note"] == p["preferred"])
            rej = next(r for r in results if r["pair"] == p["pair"] and r["run"] == k and r["note"] == p["rejected"])
            broken = pref["failed"] + rej["failed"]
            incomplete += bool(broken)
            total += not control
            for m in methods:
                a, b = pref["by"][m]["takeaway"], rej["by"][m]["takeaway"]
                if not control and not broken:
                    separated[m] += a > b
                verdict = "preferred above" if a > b else ("tie" if a == b else "rejected above")
                note = f"; incomplete, {broken} calls failed" if broken else ""
                print(f"  run {k}, {m}: Takeaway recall {a} of {pref['by'][m]['gold']} against {b}, {verdict}{note}")
                print(f"    preferred: {summary(pref['by'][m])}")
                print(f"    rejected:  {summary(rej['by'][m])}")
    return separated, total, incomplete


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("note", nargs="?", type=Path, help="the note to read (Markdown)")
    ap.add_argument("--gold", type=Path, help="the gold list for the note's date (TSV)")
    ap.add_argument("--date", help="the note's date, YYYY-MM-DD (default: the first date in its title or file name)")
    ap.add_argument("--pairs", nargs="?", const=PAIRS, type=Path, help=f"run every pair of a pairs file (default {PAIRS})")
    ap.add_argument("--runs", type=int, default=1, help="runs per note (default 1)")
    ap.add_argument("--match", choices=("words", "judge", "both"), default="both", help="the matching step (default both)")
    ap.add_argument("--candidates", type=int, default=3, help="note rows the judge sees per gold row, by shared words (default 3)")
    ap.add_argument("--model", help="the model of every call (default: say.py's)")
    ap.add_argument("--calls", type=int, default=4, help="calls in flight at once (default 4)")
    ap.add_argument("--notes", type=int, default=4, help="notes read at once with --pairs (default 4)")
    ap.add_argument("--out", type=Path, help="write every answer, row, pairing and number to this JSON file")
    ap.add_argument("--from", dest="saved", type=Path, help="with --pairs: score the results of an earlier --out file "
                    "against the pairs file as it is now, with no call")
    a = ap.parse_args(argv)
    methods = METHODS if a.match == "both" else (a.match,)
    global GATE
    GATE = threading.BoundedSemaphore(max(1, a.calls))

    if a.pairs:
        if a.saved:
            results = json.loads(a.saved.read_text(encoding="utf-8"))
            methods = tuple(m for m in methods if all(m in r["by"] for r in results))
        else:
            results = run_pairs(a.pairs, a.runs, methods, a.model, a.candidates, max(1, a.calls), max(1, a.notes))
        if a.out:
            a.out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        separated, total, incomplete = report(a.pairs, results, methods)
        print("separated: " + "; ".join(f"{m} {separated[m]} of {total} acceptance pair-runs" for m in methods))
        if incomplete:
            print(f"incomplete: {incomplete} pair-runs had a failed call; their numbers measure the route, not the note")
            return 2
        return 0 if total and any(separated[m] == total for m in methods) else 1

    if not a.note or not a.gold:
        ap.error("give a note and --gold, or --pairs")
    text = a.note.read_text(encoding="utf-8")
    date = a.date or note_date(a.note, text)
    gold = load_gold(a.gold)
    results = []
    for k in range(1, a.runs + 1):
        r = evaluate(text, gold, date, a.model, methods, a.candidates, max(1, a.calls), label=f"run {k}: ")
        results.append({"run": k, "note": str(a.note), "date": date, **r})
        for m in methods:
            print(f"run {k}, {m}: {summary(r['by'][m])}")
        print(f"  {r['calls']} calls, {r['failed']} failed, {r['seconds']} s")
    if a.out:
        a.out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    return 2 if any(r["failed"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
