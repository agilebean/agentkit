"""The shared wording checker (scripts/wording_lint.py): RULES.md rule 2, checked.

The list lives in robot_markers.tsv at the repo root; the checker ships here so
every project runs one list. These tests hold the contract: flag hits fail the
command, warn hits report only, an exception keeps its line out (the feedback
grid's "my biggest insight" is the case), and a declared quoted excerpt is
skipped whole. The KUBS pipeline in the socrates repo consumes the same list
through this module.
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


def test_a_quoted_excerpt_is_left_alone() -> None:
    text = ("The job types, verbatim from Kalbach:\n"
            "<!-- verbatim -->\n"
            "It's an act that will be performed \u2014 the done part of jobs to be done.\n"
            "<!-- end verbatim -->\n"
            "The filters cost you more on Wednesday.\n")
    assert wording.lint_text(text, _rules()) == []


def test_the_excerpt_range_ends_at_its_marker() -> None:
    text = ("<!-- verbatim -->\nquoted\u2014theirs\n<!-- end verbatim -->\nmine\u2014not theirs\n")
    hits = wording.lint_text(text, _rules())
    assert [line for line, _l, _m, _f in hits] == [4]


def test_the_journey_map_name_is_exempt() -> None:
    hits = wording.lint_text("the riddle, the journey map, the service blueprint", _rules())
    assert not any("journey" in match for _line, _level, match, _fix in hits)


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


def test_a_title_naming_a_person_or_an_act_flags() -> None:
    # RULES.md rule 20: a title names its subject by a category noun, never by a
    # person or by what someone does or receives.
    assert wording.title_hits("2026-11-05 sample: what she gets, taste, consistency and production")
    assert wording.title_hits("2026-11-05 Oral sex and taste")
    assert wording.title_hits("2026-11-05 sample: nutritional intake, taste, consistency and production") == []
    assert wording.title_hits("2026-11-05 Paternal Age and the Frozen 2020 Sample Question") == []


def test_the_file_name_and_a_given_title_are_checked(tmp_path, capsys) -> None:
    bad = tmp_path / "2026-11-05 what she gets.md"
    bad.write_text("Plain text.\n")
    assert wording.main([str(bad)]) == 2
    good = tmp_path / "note.md"
    good.write_text("Plain text.\n")
    assert wording.main(["--title", "2026-11-05 sample: what she gets", str(good)]) == 2
    assert wording.main(["--title", "2026-11-05 sample: nutritional intake", str(good)]) == 0


def test_an_article_in_a_name_warns() -> None:
    # RULES.md rule 70, class 37 of the 2026-11-21 session harvest: "you use too
    # much the article "the"" about file names and slide rows.
    assert wording.title_articles("2026-11-21 The session lessons") == ["The"]
    assert wording.title_articles("Paternal Age and the Frozen 2020 Sample Question") == ["the"]
    assert wording.title_articles("2026-10-11_the_homework_slide") == ["the"]
    assert wording.title_articles("E06 Option A homework") == []
    assert wording.title_articles("2026-11-21 session lessons tier1") == []
    assert wording.title_articles("Theory of the firm") == ["the"]


def test_an_article_in_a_file_name_fails_only_strict(tmp_path) -> None:
    named = tmp_path / "2026-11-21 the plan.md"
    named.write_text("Plain text.\n")
    assert wording.main([str(named)]) == 0
    assert wording.main(["--strict", str(named)]) == 2


def test_a_bare_ordinal_date_warns_and_a_named_series_passes() -> None:
    """RULES.md 17: "A second meeting" in a note on a viewing with Minseo said Chaehan
    had met her before; the second of the four flat viewings was their first.
    A warning, not a flag: "a second meeting" in a Life Challenges note means
    meeting one woman again and is correct (Chaehan, 2026-11-08: "Warn only")."""
    rules = _rules()

    def flagged(text: str) -> bool:
        return any(level == "warn" and re.search(r"(?i)date|meeting", match)
                   for _line, level, match, _fix in wording.lint_text(text, rules))

    assert flagged("## A second meeting")
    assert flagged("Prepare for a second date with good questions")
    assert flagged("2026-11-08 Visit Minseo: second date tips")
    assert not flagged("The second of the four flat viewings, 2026-11-08: 민서")
    assert not flagged("Your second meeting with Minseo is on Sunday")
    assert not flagged("your first meeting with her")
    assert not flagged('Chaehan, 2026-11-08: "the second date is today not nov 11"')
    assert not flagged("If a second date with her comes")
    assert not flagged("It buys a second meeting in March with any woman from November")


# ---- --strict and stacked marker lists (2026-11-12) ----

def test_strict_makes_a_warn_fail(tmp_path) -> None:
    p = tmp_path / "note.md"
    p.write_text("You explained the mechanism rather than the taste.\n", encoding="utf-8")
    assert wording.main([str(p)]) == 0
    assert wording.main(["--strict", str(p)]) == 2


def test_markers_stack_and_the_shared_list_is_named(tmp_path) -> None:
    extra = tmp_path / "extra.tsv"
    extra.write_text("flag\t\\bexits?\\b\ta figure\n", encoding="utf-8")
    p = tmp_path / "note.md"
    p.write_text("You took no exit.\n", encoding="utf-8")
    assert wording.main([str(p)]) == 0
    assert wording.main(["--markers", str(extra), str(p)]) == 2
    both = ["--markers", wording.DEFAULT_MARKERS, "--markers", str(extra)]
    q = tmp_path / "dash.md"
    q.write_text("Plain — dashed.\n", encoding="utf-8")
    assert wording.main(both + [str(q)]) == 2
    assert wording.main(["--markers", str(extra), str(q)]) == 0


# The run-level checks (rhythm_hits): what a word list cannot see. Chaehan,
# 2026-11-14: "the constant second person wording sounds repetitive and
# unnatural" and "only instructions is also very unnatural". The colon frames
# and bold lead-ins are the forms the 2026-11-27 chat reply baseline found in
# replies that passed the marker list with 0 hits.

def _rhythm(text: str) -> list[tuple[int, str, str, str]]:
    return wording.rhythm_hits(text)


def test_three_sentences_opening_with_you_flag() -> None:
    text = ("You booked the clinic for Monday. You still need the referral. "
            "Your insurer pays 80% of it.")
    hits = _rhythm(text)
    assert [level for _l, level, _m, _f in hits] == ["flag"]
    assert "You" in hits[0][2]


def test_you_mixed_with_statements_passes() -> None:
    text = ("The clinic opens at 9 on Monday. You still need the referral. "
            "The insurer pays 80% of it, and the rest goes on your card.")
    assert _rhythm(text) == []


def test_a_reply_mostly_in_you_sentences_warns() -> None:
    text = ("You booked Monday. The clinic is near. You need the referral. You pay at the desk. "
            "It takes an hour. You claim it later. You keep the receipt.")
    levels = [level for _l, level, _m, _f in _rhythm(text)]
    assert "warn" in levels


def test_a_paragraph_of_only_instructions_warns() -> None:
    text = "Book the clinic for Monday. Bring the referral. Keep the receipt. Claim it within 30 days."
    hits = _rhythm(text)
    assert [level for _l, level, _m, _f in hits] == ["warn"]
    assert "instruction" in hits[0][3]


def test_instructions_mixed_with_facts_pass() -> None:
    text = "The clinic opens at 9. Bring the referral. The visit takes an hour."
    assert _rhythm(text) == []


def test_a_colon_frame_flags() -> None:
    for frame in ("So the shape is: two sessions, then one a year.",
                  "What would reverse this: a flare after the session.",
                  "One number decides it: the gap of ten weeks.",
                  "- **What would change this diagnosis:** a stronger model."):
        hits = _rhythm(frame)
        assert any(level == "flag" and "colon frame" in fix for _l, level, _m, fix in hits), frame


def test_a_list_label_with_no_verb_is_not_a_colon_frame() -> None:
    for line in ("Files changed:", "The suggested repairs, cheapest first:", "Fix: add the hook.",
                 "The visit is at 10:30 on Monday."):
        assert not any("colon frame" in fix for _l, _lv, _m, fix in _rhythm(line)), line


def test_a_bold_lead_in_flags_and_a_bold_line_alone_passes() -> None:
    hits = _rhythm("- **No gate on chat replies.** Neither harness checks a reply.")
    assert any("bold lead-in" in fix for _l, _lv, _m, fix in hits)
    assert not any("bold lead-in" in fix for _l, _lv, _m, fix in _rhythm("**Order.**"))
    assert not any("bold lead-in" in fix for _l, _lv, _m, fix in _rhythm("| **$2676** | 3 CBM |"))


def test_a_thousand_separator_flags() -> None:
    hits = _rhythm("The visit cost KRW 254,860.")
    assert any(level == "flag" and "254,860" in match for _l, level, match, _f in hits)
    assert _rhythm("Rules 2, 19 and 37 hold it, and the total is KRW 254860.") == []


def test_code_fences_quotes_and_inline_code_are_not_prose() -> None:
    text = ("```\nYou run it. You check it. You ship it. Cost: 1,000\n```\n"
            "> You said it. You meant it. You wrote it.\n"
            "The command `You do. You go. You see.` is quoted.")
    assert _rhythm(text) == []


def test_the_cli_reports_rhythm_hits(tmp_path) -> None:
    p = tmp_path / "reply.md"
    p.write_text("You booked it. You paid it. You claim it.\n")
    assert wording.main([str(p)]) == 2
