"""instruction_lint.py: I1 a slot with no empty case, I2 an empty case written as a sentence (RULES.md 245)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("instruction_lint", Path(__file__).parents[1] / "scripts" / "instruction_lint.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)


def test_an_empty_case_written_as_a_sentence_is_flagged() -> None:
    """The date skill's "When nothing changed how she treated you, one sentence that says so." kept a turning
    point section over "You felt no change in her" (failure 230, 2026-11-20)."""
    hits = lint.lint("3. The turning point. When nothing changed how she treated you, one sentence that says so.\n")
    assert [h for _n, h in hits if h.startswith("I2:")]


def test_an_empty_case_that_drops_the_section_passes() -> None:
    assert lint.lint("3. The turning point. Only when something changed; otherwise the note has none.\n") == []
