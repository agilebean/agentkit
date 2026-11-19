#!/usr/bin/env python3
"""The wording measure: how each check scores Chaehan's labelled lines.

wording_cases.tsv holds 60 lines: 20 that Chaehan wrote or accepted, and 40
that he rejected, each with its fault. A check is good when it passes the
accepted lines and refuses the rejected ones. A change to a check, a marker or
a prompt is kept only when one of its two numbers rises and none falls (build
spec step 1, docs/2026-11-17 note wording build spec.md).

    python3 scripts/wording_eval.py                     # lint and seat
    python3 scripts/wording_eval.py --check seat --min-accept 13 --min-refuse 31
    python3 scripts/wording_eval.py --show              # the ids each check gets wrong
    python3 scripts/wording_eval.py --literal           # one DeepSeek call per line (step 4)
    python3 scripts/wording_eval.py --say --runs 3      # lines from pairs P09 to P19 (step 3)

Checks:
  lint     no flag and no warn of wording_lint.py (the strict reading)
  seat     overview_gate.seat(line), the gate's subject test
  literal  a fresh call can say what literally happens in the line
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "wording_cases.tsv"
PAIRS = ROOT / "wording_pairs.tsv"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mods: dict[str, object] = {}


def _mod(name: str):
    paths = {"wording_lint": ROOT / "scripts" / "wording_lint.py",
             "overview_gate": ROOT / "skills" / "life-overview" / "scripts" / "overview_gate.py",
             "say": ROOT / "scripts" / "say.py"}
    if name not in _mods:
        _mods[name] = _load(name, paths[name])
    return _mods[name]


def load_cases(path: Path = CASES) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE) if r.get("id")]


def _lint(line: str) -> bool:
    wl = _mod("wording_lint")
    if "rules" not in _mods:
        _mods["rules"] = wl.load_robot_markers()
    return not wl.lint_text(line, _mods["rules"])


def _seat(line: str) -> bool:
    return bool(_mod("overview_gate").seat(line))


CHECKS = {"lint": _lint, "seat": _seat}


def measure(rows: list[dict], check) -> tuple[int, int, int, int]:
    """(accepted that pass, accepted, rejected that are refused, rejected)."""
    acc = [r for r in rows if r["label"] == "accepted"]
    rej = [r for r in rows if r["label"] == "rejected"]
    return (sum(1 for r in acc if check(r["line"])), len(acc),
            sum(1 for r in rej if not check(r["line"])), len(rej))


def misses(rows: list[dict], check) -> tuple[list[str], list[str]]:
    """(ids of rejected lines the check passes, ids of accepted lines it refuses)."""
    return ([r["id"] for r in rows if r["label"] == "rejected" and check(r["line"])],
            [r["id"] for r in rows if r["label"] == "accepted" and not check(r["line"])])


# ---- step 4: the question of what literally happens ---------------------------

def literal_answers(lines: list[str], model: str | None = None, workers: int = 8) -> list[str]:
    return _mod("say").literal_answers(lines, model=model, workers=workers)


def measure_literal(rows: list[dict], model: str | None = None, out: Path | None = None) -> tuple[int, int, int, int]:
    answers = literal_answers([r["line"] for r in rows], model=model)
    verdict = {r["line"]: not _mod("say").cannot_say(a) for r, a in zip(rows, answers)}
    if out:
        out.write_text(json.dumps([{"id": r["id"], "label": r["label"], "line": r["line"], "answer": a}
                                   for r, a in zip(rows, answers)], ensure_ascii=False, indent=1), encoding="utf-8")
    missing = [r["id"] for r, a in zip(rows, answers) if a.startswith("no answer")]
    if missing:
        print(f"literal: no answer for {' '.join(missing)}; each counts as a line the reader can say")
    return measure(rows, lambda line: verdict[line])


# ---- step 3: lines written from the cards of pairs P09 to P19 ----------------

STOP = set("the a an of to in on at and or so is are was were be it its your you that this with for from "
           "which as by".split())


def content_words(s: str) -> set[str]:
    words = re.findall(r"[a-z0-9$¥.:가-힣]+", s.lower().replace("don't", "do not"))
    return {w for w in words if w.strip(".:") and w not in STOP}


def close(line: str, accepted: str) -> bool:
    """The line and the accepted line share 80% of each one's content words."""
    a, b = content_words(line), content_words(accepted)
    shared = len(a & b)
    return bool(a and b) and shared >= 0.8 * len(b) and shared >= 0.8 * len(a)


def say_acceptance(runs: int, first: str, last: str, model: str | None, out: Path | None) -> list[dict]:
    say = _mod("say")
    pairs = [r for r in say.load_pairs(PAIRS) if first <= r["id"] <= last]
    cards = [say.pair_card(r) for r in pairs]
    results = []
    for k in range(1, runs + 1):
        t = time.time()
        report = say.say(cards, model=model)
        lines = {c["id"]: report["lines"].get(c["id"], "") for c in cards}
        n_close = sum(close(lines[r["id"]], r["line"]) for r in pairs)
        same = sum(lines[r["id"]].rstrip(".") == r["line"].rstrip(".") for r in pairs)
        obl = [c["id"] for c in cards if not c.get("do") and say.OBLIGATION.search(lines[c["id"]])
               and not say.OBLIGATION.search(say.card_text(c))]
        results.append({"run": k, "close": n_close, "of": len(pairs), "same": same, "obligation": obl,
                        "how": report["how"], "calls": report["calls"], "seconds": round(time.time() - t),
                        "swapped": report["swapped"], "lines": lines})
        print(f"run {k}: close to the accepted line {n_close} of {len(pairs)}, word for word {same}, "
              f"obligation added {len(obl)}, retried {sum(h == 'retry' for h in report['how'].values())}, "
              f"written by the script {sum(h == 'script' for h in report['how'].values())}, "
              f"{report['calls']} calls, {results[-1]['seconds']} s")
    if out:
        out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", type=Path, default=CASES, help="the labelled lines (default: wording_cases.tsv)")
    ap.add_argument("--check", action="append", choices=sorted(CHECKS), help="a check to run; repeat for several (default: all)")
    ap.add_argument("--min-accept", type=int, help="exit 1 when a check passes fewer accepted lines")
    ap.add_argument("--min-refuse", type=int, help="exit 1 when a check refuses fewer rejected lines")
    ap.add_argument("--show", action="store_true", help="list the ids each check gets wrong")
    ap.add_argument("--literal", action="store_true", help="also ask the literal question, one call per line")
    ap.add_argument("--say", action="store_true", help="write lines from the cards of pairs P09 to P19 and compare")
    ap.add_argument("--runs", type=int, default=3, help="runs of --say (default 3)")
    ap.add_argument("--pairs", default="P09-P19", help="the pairs --say writes from (default P09-P19)")
    ap.add_argument("--model", help="the model of --literal and --say (default: say.py's)")
    ap.add_argument("--out", type=Path, help="write the raw answers of --literal or --say to this JSON file")
    a = ap.parse_args(argv)

    if a.say:
        first, last = a.pairs.split("-")
        results = say_acceptance(a.runs, first, last, a.model, a.out)
        low = min(r["close"] for r in results)
        obl = sum(len(r["obligation"]) for r in results)
        if a.min_accept is not None and low < a.min_accept:
            return 1
        return 1 if obl else 0

    rows = load_cases(a.cases)
    names = a.check or list(CHECKS)
    scores = {n: measure(rows, CHECKS[n]) for n in names}
    if a.literal:
        scores["literal"] = measure_literal(rows, model=a.model, out=a.out)
    print(f"{'check':<9}{'accepted that pass':<22}rejected that are refused")
    failed = False
    for n, (pa, na, rr, nr) in scores.items():
        print(f"{n:<9}{f'{pa} of {na}':<22}{rr} of {nr}")
        if (a.min_accept is not None and pa < a.min_accept) or (a.min_refuse is not None and rr < a.min_refuse):
            failed = True
        if a.show and n in CHECKS:
            passed, refused = misses(rows, CHECKS[n])
            print(f"  accepted it refuses: {' '.join(refused) or '-'}")
            print(f"  rejected it passes: {' '.join(passed) or '-'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
