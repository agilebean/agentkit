"""The wording measure (scripts/wording_eval.py), build spec step 1.

wording_cases.tsv holds Chaehan's 20 accepted and 40 rejected lines. These tests
hold the numbers each check scores on the table as shipped, so a change to a
check, a marker or the table shows up as a changed number.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("wording_eval", ROOT / "scripts" / "wording_eval.py")
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)


def test_the_table_holds_20_accepted_and_40_rejected_lines() -> None:
    rows = ev.load_cases()
    assert sum(r["label"] == "accepted" for r in rows) == 20
    assert sum(r["label"] == "rejected" for r in rows) == 40
    assert all(r["fault"] for r in rows if r["label"] == "rejected")


def test_lint_and_seat_score_the_shipped_numbers() -> None:
    rows = ev.load_cases()
    assert ev.measure(rows, ev.CHECKS["lint"]) == (19, 20, 10, 40)
    assert ev.measure(rows, ev.CHECKS["seat"]) == (13, 20, 31, 40)


def test_a_minimum_above_the_score_exits_1(capsys) -> None:
    assert ev.main(["--check", "seat", "--min-accept", "13", "--min-refuse", "31"]) == 0
    assert ev.main(["--check", "seat", "--min-accept", "14"]) == 1
    assert ev.main(["--check", "lint", "--min-refuse", "11"]) == 1
    out = capsys.readouterr().out
    assert "13 of 20" in out and "31 of 40" in out


def test_misses_names_the_lines_a_check_gets_wrong() -> None:
    rows = ev.load_cases()
    passed_rejected, refused_accepted = ev.misses(rows, ev.CHECKS["lint"])
    assert len(refused_accepted) == 1
    assert len(passed_rejected) == 30


def test_an_appended_row_changes_the_totals(tmp_path) -> None:
    table = tmp_path / "cases.tsv"
    text = (ROOT / "wording_cases.tsv").read_text(encoding="utf-8")
    table.write_text(text + "A21\taccepted\t\tYour 200 m took 3:41 on 2026-11-02.\n"
                     "R41\trejected\tpicture\tThe week buys you a quiet start.\n", encoding="utf-8")
    rows = ev.load_cases(table)
    _, n_acc, _, n_rej = ev.measure(rows, ev.CHECKS["seat"])
    assert (n_acc, n_rej) == (21, 41)



def test_literal_counts_cannot_say_as_a_refusal(monkeypatch) -> None:
    answers = {"Your 400 m went from 8:08 to 8:04.": "Your 400 m time fell from 8:08 to 8:04.",
               "The plan buys you a calm week.": "cannot say"}
    monkeypatch.setattr(ev, "literal_answers", lambda lines, **kw: [answers[l] for l in lines])
    rows = [{"id": "A1", "label": "accepted", "fault": "", "line": "Your 400 m went from 8:08 to 8:04."},
            {"id": "R1", "label": "rejected", "fault": "picture", "line": "The plan buys you a calm week."}]
    assert ev.measure_literal(rows) == (1, 1, 1, 1)
