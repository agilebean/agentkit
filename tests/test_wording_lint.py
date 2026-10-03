"""The shared wording checker (scripts/wording_lint.py): RULES.md rule 2, checked.

The list lives in robot_markers.tsv at the repo root; the checker ships here so
every project runs one list. These tests hold the contract: flag hits fail the
command, warn hits report only, an exception keeps its line out (the feedback
grid's "my biggest insight" is the case). The KUBS pipeline in the socrates repo
consumes the same list through this module.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "wording_lint.py"
_spec = importlib.util.spec_from_file_location("wording_lint", SCRIPT_PATH)
assert _spec and _spec.loader
wording = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wording)


def _rules():
    return wording.load_robot_markers()


def test_the_marker_list_loads() -> None:
    rules = _rules()
    assert len(rules) >= 20
    assert all(level in ("flag", "warn") for level, _p, _f, _e in rules)


def test_the_list_lives_in_agentkit() -> None:
    assert Path(wording.DEFAULT_MARKERS).resolve() == (SCRIPT_PATH.parents[1] / "robot_markers.tsv").resolve()
    assert Path(wording.DEFAULT_MARKERS).exists()


def test_an_em_dash_flags() -> None:
    hits = wording.lint_text("The filters \u2014 the three of them - matter.", _rules())
    assert any(level == "flag" and "\u2014" in match for _line, level, match, _fix in hits)


def test_a_formula_flags() -> None:
    hits = wording.lint_text("It's not just a question of time.", _rules())
    assert any("not just" in match for _line, _level, match, _fix in hits)


def test_the_feedback_grids_insight_is_exempt() -> None:
    hits = wording.lint_text("What I like, what I wish, my biggest insight, my open question", _rules())
    assert not any("insight" in match for _line, _level, match, _fix in hits)


def test_the_session_plan_word_warns_but_does_not_flag() -> None:
    hits = wording.lint_text("## Run of show", _rules())
    assert [level for _l, level, _m, _f in hits] == ["warn"]


def test_the_matched_span_is_reported_once() -> None:
    rules = [("flag", re.compile(r"foo"), "one", None),
             ("warn", re.compile(r"foo"), "two", None)]
    assert wording.lint_text("foo", rules) == [(1, "flag", "foo", "one")]


def test_table_separators_and_code_spans_are_not_prose() -> None:
    rules = _rules()
    assert wording.lint_text("| --- | --- | --- |", rules) == []
    assert wording.lint_text("Run `pipeline.py slides --session 2`", rules) == []


def test_the_cli_flags_and_warns(tmp_path) -> None:
    p = tmp_path / "draft.md"
    p.write_text("It's not just time.\n## Run of show\n", encoding="utf-8")
    assert wording.main([str(p)]) == 2


def test_the_cli_returns_zero_on_a_clean_file(tmp_path) -> None:
    p = tmp_path / "clean.md"
    p.write_text("The filters cost you more on Wednesday.\n", encoding="utf-8")
    assert wording.main([str(p)]) == 0
