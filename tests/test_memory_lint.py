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
