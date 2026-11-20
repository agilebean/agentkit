"""Sentences that follow each other (scripts/say_flow.py), human quality plan HQ-06.

No test calls a model: `complete` is a stub, and the section is invented.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("say_flow", ROOT / "scripts" / "say_flow.py")
flow = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(flow)

SECTION = """## Garden

Your pear tree at Mangwon 4 lost its leaves on 2026-10-02.

- Your pear tree at Mangwon 4 needs a cut before 2026-12-01.
- Your pear tree at Mangwon 4 was planted in 2019 by Oh Sumin.
  - The cut costs 30000 won.

| Plant | State |
| --- | --- |
| pear | bare |
"""
NOTE = "# 2026-11-01 Home\n\n" + SECTION + "\n## Kitchen\n\nThe tap was fixed on 2026-10-30.\n"
GOOD = ("L1\tYour pear tree at Mangwon 4 lost its leaves on 2026-10-02.\n"
        "L2,L3\tIt needs a cut before 2026-12-01, and Oh Sumin planted it in 2019.\n"
        "L4\tThe cut costs 30000 won.\n")


def _lines() -> list[str]:
    return SECTION.splitlines()


def test_only_leads_and_bullets_are_sent_with_their_place() -> None:
    items = flow.items_of(_lines())
    assert [i["id"] for i in items] == ["L1", "L2", "L3", "L4"]
    assert [flow.place(i) for i in items] == ["lead", "bullet", "bullet", "bullet under the bullet before"]
    assert flow.message(items).splitlines()[0] == "L1 (lead)\tYour pear tree at Mangwon 4 lost its leaves on 2026-10-02."


def test_a_good_answer_passes_and_is_written_at_the_first_line_of_each_group() -> None:
    items = flow.items_of(_lines())
    groups = flow.parse(GOOD)
    assert flow.check(items, groups, flow.PROMPT.read_text(encoding="utf-8")) == []
    out = flow.rewrite(_lines(), items, groups)
    assert "- It needs a cut before 2026-12-01, and Oh Sumin planted it in 2019." in out
    assert "  - The cut costs 30000 won." in out and "| pear | bare |" in out
    assert not any(l.startswith("- Your pear tree at Mangwon 4 was planted") for l in out)


def test_a_lost_number_an_added_name_a_lost_name_and_a_wrong_join_fail() -> None:
    items = flow.items_of(_lines())
    prompt = flow.PROMPT.read_text(encoding="utf-8")
    cases = {
        GOOD.replace("in 2019", "years ago"): "loses 2019",
        GOOD.replace("Oh Sumin planted", "Oh Sumin and Kang Mira planted"): "adds Kang, Mira",
        GOOD.replace("Your pear tree at Mangwon 4", "Your pear tree"): "loses Mangwon",
        "L1\tYour pear tree at Mangwon 4 lost its leaves on 2026-10-02.\nL2\tIt needs a cut before 2026-12-01.\n"
        "L3,L4\tOh Sumin planted it in 2019, and the cut costs 30000 won.\n": "not neighbours at one place",
        "L1\tx 2026-10-02 Mangwon\nL3\ty 2019 Oh Sumin\n": "every line id once",
    }
    for answer, reason in cases.items():
        fails = flow.check(items, flow.parse(answer), prompt)
        assert any(reason in f for f in fails), (reason, fails)


def test_a_failed_answer_is_asked_again_and_a_second_failure_keeps_the_section(monkeypatch) -> None:
    calls = []
    answers = iter(["L1\tnothing", GOOD])
    monkeypatch.setattr(flow, "complete", lambda messages, model=None: (calls.append(messages), next(answers))[1])
    r = flow.flow_section(_lines())
    assert r["how"] == "retry" and r["calls"] == 2 and "Your answer was refused" in calls[1][1]["content"]
    monkeypatch.setattr(flow, "complete", lambda messages, model=None: "L1\tnothing")
    r = flow.flow_section(_lines())
    assert r["how"] == "kept" and r["lines"] == _lines()


def test_the_note_keeps_its_title_and_a_section_of_one_line(monkeypatch) -> None:
    monkeypatch.setattr(flow, "complete", lambda messages, model=None: GOOD)
    text, report = flow.flow_note(NOTE, workers=1)
    assert text.startswith("# 2026-11-01 Home\n") and "The tap was fixed on 2026-10-30." in text
    assert report["Kitchen"]["how"] == "alone" and report["Garden"]["how"] == "model"


def test_the_measure_counts_a_name_said_again_in_the_next_sentence() -> None:
    before = flow.measure(NOTE)
    after = flow.measure("\n".join(flow.rewrite(_lines(), flow.items_of(_lines()), flow.parse(GOOD))))
    assert before["repeats"] == 2 and before["repeat_pairs"][0]["section"] == "Garden"
    assert after["repeats"] == 0 and after["median_words"] <= before["median_words"] + 5
    assert flow.sentences("It rained. Then 2026-10-02 came. ok") == ["It rained.", "Then 2026-10-02 came. ok"]
