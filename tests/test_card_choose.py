"""Choosing the cards a note says (scripts/card_choose.py).

The skill's Moves 1, 2 and 4 over fact cards: per section a lead, at most three bullets with their details
under them, and the cards left out; the Takeaway takes each section's lead. The call answers with card ids
only. No test here calls a model.
"""
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


choose = _load("card_choose")
check = _load("card_check")


def _card(cid: str, section: str = "Health", **kw) -> dict:
    base = {"section": section, "id": cid, "kind": "state", "thing": f"your thing {cid}", "fact": "is set",
            "so": "", "do": "", "said": "", "src": "memory/health.md:1"}
    return base | kw


HEALTH = [_card(f"C{n}") for n in range(1, 8)]
IDS = [c["id"] for c in HEALTH]


def test_the_prompt_example_is_answered_in_the_form_it_asks_for() -> None:
    text = choose.PROMPT.read_text(encoding="utf-8")
    answer = text.split("Answer:\n", 1)[1].split("\n\nReturn", 1)[0]
    rows, out, problems = choose.parse_answer(answer, ["E1", "E2", "E3", "E4", "E5", "E6", "E7"], "Apartment lease")
    assert problems == [] and out == ["E4", "E5", "E7"]
    assert [(r["kind"], r["indent"], r["cards"]) for r in rows] == [
        ("lead", 0, ["E1"]), ("bullet", 0, ["E2"]), ("bullet", 1, ["E3"]), ("bullet", 0, ["E6"])]


def test_the_user_message_holds_the_date_the_section_and_each_card_with_said() -> None:
    msg = choose.user_message("Health", [HEALTH[0], _card("C9", said="2026-11-08")], "2026-11-09")
    assert msg.splitlines()[0] == "Today is 2026-11-09. Section: Health"
    assert msg.splitlines()[2] == "C1\tkind=state | thing=your thing C1 | fact=is set"
    assert msg.splitlines()[3].endswith(" | said=2026-11-08")


def test_an_answer_breaking_a_rule_names_each_problem() -> None:
    cases = {
        "- C1\n- C2\nout: C3, C4, C5, C6, C7": "no lead",
        "lead: C1\n- C2\n- C3\n- C4\n- C5\nout: C6, C7": "more than three bullets",
        "lead: C1, C2, C3, C4\nout: C5, C6, C7": "more than three cards",
        "lead: C1\n- C9\nout: C2, C3, C4, C5, C6, C7": "C9",
        "lead: C1\n- C1\nout: C2, C3, C4, C5, C6, C7": "twice",
        "lead: C1\n  - C2\nout: C3, C4, C5, C6, C7": "indented",
    }
    for answer, word in cases.items():
        _rows, _out, problems = choose.parse_answer(answer, IDS, "Health")
        assert any(word in p for p in problems), (answer, problems)


def test_a_card_the_answer_forgets_goes_out_without_a_problem() -> None:
    rows, out, problems = choose.parse_answer("lead: C1\n- C2\nout: C3", IDS, "Health")
    assert problems == [] and out == ["C3", "C4", "C5", "C6", "C7"]


def test_what_went_well_has_no_lead_and_up_to_four_cards_a_line() -> None:
    wins = [_card(f"W{n}", "What went well") for n in range(1, 6)]
    ids = [c["id"] for c in wins]
    rows, out, problems = choose.parse_answer("- W1, W2, W3, W4\n- W5", ids, "What went well")
    assert problems == [] and [r["cards"] for r in rows] == [["W1", "W2", "W3", "W4"], ["W5"]]


def test_a_section_is_asked_again_once_then_written_by_the_script(monkeypatch) -> None:
    answers = iter(["- C1\n- C2", "lead: C1\n- C2\n  - C3\nout: C4, C5, C6, C7"])
    sent = []

    def fake(messages, model=None, **kw):
        sent.append(messages[-1]["content"])
        return next(answers)

    monkeypatch.setattr(choose, "complete", fake)
    r = choose.choose_section("Health", HEALTH, "2026-11-09")
    assert r["how"] == "retry" and len(sent) == 2 and "no lead" in sent[1]
    assert [x["cards"] for x in r["rows"]] == [["C1"], ["C2"], ["C3"]]
    monkeypatch.setattr(choose, "complete", lambda m, **kw: "nothing useful")
    r = choose.choose_section("Health", HEALTH, "2026-11-09")
    assert r["how"] == "script"
    assert [(x["kind"], x["cards"]) for x in r["rows"]] == [("lead", ["C1"]), ("bullet", ["C2"]), ("bullet", ["C3"]),
                                                           ("bullet", ["C4"])]


def test_the_script_choice_leaves_out_cards_he_stated_himself(monkeypatch) -> None:
    cards = [_card("C1", said="2026-11-01"), _card("C2"), _card("C3", said="2026-11-02"), _card("C4")]
    monkeypatch.setattr(choose, "complete", lambda m, **kw: "")
    r = choose.choose_section("Health", cards, "2026-11-09")
    assert [x["cards"] for x in r["rows"]] == [["C2"], ["C4"]]


def test_the_plan_puts_each_sections_lead_in_the_takeaway_and_writes_map_columns(tmp_path, monkeypatch) -> None:
    cards = [_card("W1", "What went well"), _card("C1", "Travel"), _card("C2", "Travel"),
             _card("C3", "Health"), _card("C4", "Health")]
    path = tmp_path / "cards.tsv"
    check.write_cards(path, cards)

    def fake(messages, model=None, **kw):
        msg = messages[-1]["content"]
        if "Section: What went well" in msg:
            return "- W1"
        if "Section: Travel" in msg:
            return "lead: C2\n- C1"
        return "lead: C3\nout: C4"

    monkeypatch.setattr(choose, "complete", fake)
    report = choose.plan(path, tmp_path / "plan.tsv", "2026-11-09")
    with open(tmp_path / "plan.tsv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))
    assert list(rows[0]) == ["section", "kind", "indent", "cards", "today"]
    assert [(r["section"], r["cards"]) for r in rows[:2]] == [("Takeaway", "C2"), ("Takeaway", "C3")]
    assert [(r["section"], r["kind"], r["cards"]) for r in rows[2:]] == [
        ("What went well", "bullet", "W1"), ("Travel", "lead", "C2"), ("Travel", "bullet", "C1"),
        ("Health", "lead", "C3")]
    assert report["out"] == {"Health": ["C4"]} and report["calls"] == 3


def test_the_date_is_read_from_the_sources_heading(tmp_path) -> None:
    src = tmp_path / "sources.md"
    src.write_text("# Sources for 2026-11-09 Life Overview\n\n## Health\n", encoding="utf-8")
    assert choose.date_of(src) == "2026-11-09"


def test_a_call_that_fails_twice_leaves_the_section_to_the_script(monkeypatch) -> None:
    def broken(messages, model=None, **kw):
        raise RuntimeError("finish_reason='length'")

    monkeypatch.setattr(choose, "complete", broken)
    r = choose.choose_section("Health", HEALTH, "2026-11-09")
    assert r["how"] == "script" and r["calls"] == 2 and "no answer" in r["problems"][0]


def test_his_order_of_priorities_stands_above_the_cards_when_given(tmp_path) -> None:
    memory = tmp_path / "optimize-my-life.md"
    memory.write_text("# Me\n\n## Life priorities\n\nOrder (2026-11-08): 1. travel; 2. health, the knee "
                      "first in it.\n\n## Purpose\nOther text.\n", encoding="utf-8")
    order = choose.priorities_of(memory)
    assert order == "Order (2026-11-08): 1. travel; 2. health, the knee first in it."
    lines = choose.user_message("Health", HEALTH[:1], "2026-11-09", order).splitlines()
    assert lines[1] == "His order of priorities: " + order and lines[2] == "Cards:"
    memory.write_text("# Me\n\n## Purpose\nOther text.\n", encoding="utf-8")
    assert choose.priorities_of(memory) is None
