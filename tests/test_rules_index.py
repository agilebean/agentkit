"""tools/rules_index.py: every rule number in RULES.md heads exactly one rule.

A cited number ("RULES.md 221") must name one rule. On 2026-11-21 the numbers
205 and 221 each headed two rules, so a citation could not be resolved; the
second 205 became 260 and the first 221 became 261.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("rules_index", ROOT / "tools" / "rules_index.py")
assert _spec and _spec.loader
rules_index = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rules_index)


def test_a_reused_number_is_found() -> None:
    text = "### 5. One\n\nbody\n\n### 6. Two\n\n### 5. Three\n"
    assert rules_index.duplicate_numbers(text) == [5]


def test_every_rule_number_in_rules_md_is_unique() -> None:
    text = (ROOT / "RULES.md").read_text(encoding="utf-8")
    assert rules_index.duplicate_numbers(text) == []


def test_the_index_matches_rules_md() -> None:
    assert (ROOT / "rules.index.md").read_text(encoding="utf-8") == rules_index.build()
