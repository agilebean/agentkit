"""memory_lint.py on the line shapes of RULES.md 33: M3 a conclusion stated as fact, M6 the label.

A hedge inside the sentence marks an inference, so "likely" passes; the label "the agent's
reading" fails outside a quote (Chaehan, 2026-11-23).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import memory_lint  # noqa: E402


def codes(text: str) -> list[str]:
    return [code for _, code, _ in memory_lint.lint(text)]


def test_hedge_inside_the_sentence_passes():
    line = "After a long abstinence, the yellow sample color likely comes from sample vesicle fluid.\n"
    assert codes(line) == []


def test_the_label_fails_as_m6():
    line = "The agent's reading, highest probability: too little water.\n"
    assert codes(line) == ["M6"]


def test_the_label_inside_a_quote_passes():
    line = 'Chaehan, 2026-11-23: the wording "The agent\'s reading" leaves memory.\n'
    assert "M6" not in codes(line)


def test_a_conclusion_without_a_hedge_fails_as_m3():
    assert codes("- leading cause: the cache.\n") == ["M3"]


def test_a_conclusion_with_a_hedge_or_his_read_passes():
    assert codes("- leading cause: likely the cache.\n") == []
    assert codes("- best-fitting, his read: the cache.\n") == []


def test_m6_fails_the_run(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("The agent's reading: the cache.\n", encoding="utf-8")
    assert memory_lint.main([str(f)]) == 2


def test_a_sub_section_of_history_is_history_and_the_next_section_is_not():
    text = ("## History\n\n### Old tour (superseded 2026-10-04)\n\nSuperseded on 2026-10-04 by the Osaka exit.\n\n"
            "## Plan\n\nThe old plan was superseded.\n")
    assert [(n, c) for n, c, _ in memory_lint.lint(text)] == [(9, "M2")]


def test_old_value_flag_takes_correction_as_a_label_not_as_a_word():
    flagged = ["Correction (2026-09-15): the slot is at 08:00.", "Free swim 125000 KRW (corrects the earlier 115,000).",
               "Corrected 2026-10-09 on his repeat: the clean render.", "The 1:58 value is superseded."]
    clean = ["Spanish correction tools and inline corrections.", "Grade correction/appeal 2026-11-02 to 2026-11-05.",
             "Froth warning (test on the mid-2026 correction).", "His correction of the fix: the elbow."]
    assert all("M2" in [c for _, c, _ in memory_lint.lint(t)] for t in flagged)
    assert not any("M2" in [c for _, c, _ in memory_lint.lint(t)] for t in clean)
