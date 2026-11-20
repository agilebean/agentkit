import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_p = Path(__file__).resolve().parents[1] / "scripts/report_check.py"
_spec = importlib.util.spec_from_file_location("report_check", _p)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)

GOOD_DONE = """done: 7 of 7 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the colour test in `tests/test_en_to_hanji.py` | 1 failed | 0 failed | `pytest -q tests/test_en_to_hanji.py` printed `8 passed` |
| tests that import the private converter | 14 failed without socrates | 14 skipped without socrates | `NOTE_BUILD_SOCRATES=/tmp/empty pytest -q tests/test_note_build.py` |
| tests that open a local port | no marker | 2 tests marked `local_port` | `pytest -m local_port --collect-only -q` lists `2 tests` |
| the workflow on main | none | success in 2 min | `gh run view 19876543210` reads `success` |
| the suite on the machine | 1 failed, 550 passed | 551 passed | `pytest -q` printed `551 passed in 18.33s` |

| Open item | Who decides | By when |
|---|---|---|
| a check for the personal terms through a secret | Chaehan, with DD-03 | 2026-11-27 |
"""

GOOD_NO_OPEN = """done: 3 of 3 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| `scripts/report_check.py` | none | 8 rules checked | `pytest -q tests/test_report_check.py` printed `20 passed` |

| Open item | Who decides | By when |
|---|---|---|
"""

GOOD_STOPPED = """stopped at T6: the workflow run on main failed in `tests/test_gmail.py`

| What changed | Before | After | Evidence |
|---|---|---|---|

| Open item | Who decides | By when |
|---|---|---|
| whether the Google client joins the install | Claude Opus 5.5 session | 2026-11-21 |
"""

BAD_PROSE = """## Summary

I fixed the red test and added the workflow. Everything passes now.

done: all tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the red test | 1 failed | 0 failed | `pytest -q` printed `551 passed` |

| Open item | Who decides | By when |
|---|---|---|
"""

BAD_EMPTY = """done: 2 of 2 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the red test | 1 | 0 | |
| the workflow | none | added | verified |

| Open item | Who decides | By when |
|---|---|---|
| a marker for ports | Chaehan | soon |
"""

BAD_WORDING = """done: 4 of 4 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the red test | 1 failed | 0 failed | `pytest -q` printed `551 passed`. The suite is green; nothing else changed. |
| the workflow, a robust pipeline | none | it leverages the cache — fully | `tests.yml` |
"""


def rules_of(text: str) -> set[str]:
    return {rule for _, rule, _ in rc.check(text)}


@pytest.mark.parametrize("report", [GOOD_DONE, GOOD_NO_OPEN, GOOD_STOPPED], ids=["done", "no-open", "stopped"])
def test_a_report_in_the_form_passes(report) -> None:
    assert rc.check(report) == []


def test_prose_around_the_tables_and_a_done_line_without_its_number_are_refused() -> None:
    problems = rc.check(BAD_PROSE)
    assert rules_of(BAD_PROSE) == {"R1", "R2"}
    assert [n for n, rule, _ in problems if rule == "R1"] == [3, 5]
    assert [n for n, rule, _ in problems if rule == "R2"] == [1]
    no_number = rc.check(BAD_PROSE.split("\n", 4)[4])
    assert [(n, rule) for n, rule, _ in no_number] == [(1, "R2")]


def test_an_empty_evidence_cell_bare_numbers_and_a_vague_deadline_are_refused() -> None:
    problems = rc.check(BAD_EMPTY)
    assert rules_of(BAD_EMPTY) == {"R4", "R5", "R8"}
    assert sum(1 for _, rule, _ in problems if rule == "R5") == 2
    assert any("Evidence is empty" in msg for _, _, msg in problems)
    assert any("Evidence 'verified'" in msg for _, _, msg in problems)


def test_two_clauses_in_a_cell_robot_markers_and_a_missing_table_are_refused() -> None:
    problems = rc.check(BAD_WORDING)
    assert rules_of(BAD_WORDING) == {"R3", "R6", "R7"}
    hits = " ".join(msg for _, rule, msg in problems if rule == "R7")
    assert "robust" in hits and "pipeline" in hits and "leverages" in hits and "—" in hits


@pytest.mark.parametrize("text", [
    "1 failed", "14 of 14 tests", "1 → 0 failures", "~75%", "$313 a year", "line 148", "rule 74", "Python 3.14",
    "T3", "DD-02", "18.33s", "commit 1ca5c84", "2026-11-20", "14:05", "pytest 9.0.3", "`exit 2`",
    "tests/test_x.py:148", "run #44301908629", "3-5 tests",
])
def test_a_number_with_its_unit_or_as_a_label_passes(text) -> None:
    assert rc.bare_numbers(text) == []


@pytest.mark.parametrize("text,bad", [
    ("1", ["1"]), ("0", ["0"]), ("rose from 1 to 3", ["1", "3"]), ("count: 5", ["5"]), ("is 5 and done", ["5"]),
    ("550 and 1", ["550", "1"]), ("ends at 3.", ["3"]),
])
def test_a_number_without_its_unit_is_named(text, bad) -> None:
    assert rc.bare_numbers(text) == bad


def test_one_clause_per_cell() -> None:
    assert rc.clause_problem("the workflow on main") is None
    assert rc.clause_problem("`a; b` printed `x. Y`") is None
    assert rc.clause_problem("e.g. Python runs") is None
    assert rc.clause_problem("one. Two") == "a second sentence"
    assert rc.clause_problem("one; two") == "a semicolon"
    assert rc.clause_problem("one<br>two") == "a line break"
    assert "more than 20 words" in rc.clause_problem(" ".join(["word"] * 21))


def test_a_pipe_inside_code_stays_in_its_cell() -> None:
    assert rc.split_row("| a | `x | y` | b \\| c |") == ["a", "`x | y`", "b | c"]


def test_the_tables_in_the_wrong_order_or_a_third_table_are_refused() -> None:
    swapped = GOOD_NO_OPEN.split("\n\n")
    text = "\n\n".join([swapped[0], swapped[2], swapped[1]]) + "\n"
    assert "R3" in rules_of(text)
    third = GOOD_DONE + "\n| Extra | Table |\n|---|---|\n| a | b |\n"
    assert rules_of(third) == {"R1"}


def test_a_done_report_without_a_change_row_is_refused() -> None:
    text = GOOD_STOPPED.replace("stopped at T6: the workflow run on main failed in `tests/test_gmail.py`",
                                "done: 6 of 6 acceptance tests pass")
    assert rules_of(text) == {"R4"}


def test_the_command_line_exits_0_on_a_pass_and_2_with_the_lines_on_a_refusal(tmp_path) -> None:
    good, bad = tmp_path / "good.md", tmp_path / "bad.md"
    good.write_text(GOOD_DONE)
    bad.write_text(BAD_EMPTY)
    ok = subprocess.run([sys.executable, str(_p), str(good)], capture_output=True, text=True)
    assert ok.returncode == 0 and "report_check: PASS" in ok.stdout
    no = subprocess.run([sys.executable, str(_p), str(bad)], capture_output=True, text=True)
    assert no.returncode == 2 and f"{bad}:5: R5" in no.stdout and "FAIL, 5 problem(s)" in no.stdout
