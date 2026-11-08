import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills/life-challenges/scripts/challenges_gate.py"
_spec = importlib.util.spec_from_file_location("challenges_gate", _p)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

GOOD = """## Summary

- You choose between staying longer in Seoul and dating by video over the winter.
- Your four planned dates will show which way fits.
- You can send the IRS follow-up in five minutes.

## Two ways through the winter

You can meet your J Noble dates only in Seoul, and from 2026-12-04 you are away for 102 days.

- You stay in Seoul longer, so that a second meeting can happen in person.
  - You would lose the Osaka hotel week of ¥141000.
- You leave on 2026-12-04 and meet women by video in between.
  - You would ask Ms. Hyejin Kong for something J Noble does not advertise.

## What decides between them

You can have both answers before you leave Seoul.

- Does one of your four dates lead to a second meeting you want?
  - If yes, staying into December is worth its cost.
  - If no, you keep the winter as booked.

## Your money

You can do the follow-up in five minutes.

- Your refund behind the 2025 return is USD 371250.
  - You email the Form 911 address with the subject "No Response".
"""


def codes(fails):
    return {f.split()[0] for f in fails}


def test_good_note_passes():
    assert gate.check(GOOD) == []


def test_layout_order_and_two_ways():
    assert any("open with" in f for f in gate.check(GOOD.replace("## Summary", "## Takeaway")))
    assert any("second section" in f for f in gate.check(GOOD.replace("## Two ways through", "## Options for")))
    one_way = GOOD.replace("- You leave on 2026-12-04 and meet women by video in between.\n  - You would ask Ms. Hyejin Kong for something J Noble does not advertise.\n", "")
    assert any("1 ways" in f for f in gate.check(one_way))
    assert any("third section" in f for f in gate.check(GOOD.replace("## What decides between them", "## Questions")))
    assert any("no area section" in f for f in gate.check(GOOD[:GOOD.index("## Your money")]))


def test_question_needs_if_yes_and_if_no():
    fails = gate.check(GOOD.replace("  - If no, you keep the winter as booked.\n", "  - Otherwise you keep the winter.\n"))
    assert any(f.startswith("C5") and "If no" in f for f in fails)
    four = GOOD.replace("- Does one of your four dates", "- Q2?\n  - If yes, a.\n  - If no, b.\n- Q3?\n  - If yes, a.\n  - If no, b.\n- Q4?\n  - If yes, a.\n  - If no, b.\n- Does one of your four dates")
    assert any("4 questions" in f for f in gate.check(four))


def test_label_word_fails_unless_quoted():
    assert any("avoidance" in f for f in gate.check(GOOD.replace("You can do the follow-up", "Your avoidance shows. You can do the follow-up")))
    assert not any(f.startswith("C5") for f in gate.check(GOOD.replace("You can do the follow-up", "You called it \"my fear of calls\". You can do the follow-up")))


def test_no_tooling_in_the_note():
    assert "C6" in codes(gate.check(GOOD + "\n- Run `/life tas` for the draft.\n"))
    assert "C6" in codes(gate.check(GOOD + "\n## Hand to me\n\nYou can hand these to me.\n\n- The TAS email.\n"))


def test_summary_bullets_only_and_at_most_five():
    extra = "".join(f"- You sell share {n} before 2026-12-31.\n" for n in range(3))
    six = GOOD.replace("- You can send the IRS follow-up", extra + "- You can send the IRS follow-up")
    assert any(f.startswith("C7") and "6 bullets" in f for f in gate.check(six))
    assert "C7" in codes(gate.check(GOOD.replace("## Summary\n\n", "## Summary\n\nYou have a lot going on.\n\n")))


def test_wording_classes_rejected_on_2026_11_07_fail():
    for bad in ("You can buy your Seoul dates in December.", "2027 spends all nine days.", "The refund lands around February.",
                "What tips it is the date.", "The trip loses that errand.", "1372 has a clock."):
        fails = gate.check(GOOD.replace("You would lose the Osaka hotel week of ¥141000.", bad))
        assert any(f.startswith("T16") for f in fails), bad


def test_empty_heading_pronoun_separator_ssn():
    assert "C1" in codes(gate.check(GOOD + "\n## Your health\n"))
    assert "C2" in codes(gate.check(GOOD.replace("hotel week of", "hotel week of his")))
    assert "C3" in codes(gate.check(GOOD.replace("USD 371250", "USD 371,250")))
    assert "C8" in codes(gate.check(GOOD.replace("Form 911 address", "Form 911 address, SSN 605-98-1744")))


def test_lost_fact_and_issue_need_the_cut_list():
    original = "## Storage\n\n- The unit costs 88000 won a month.\n"
    assert any(f.startswith("T6 a note built") for f in gate.check(GOOD, original))
    assert gate.check(GOOD, original, "- 88000: the old price, replaced by 72090\n") == []
    old = "## Problems\n\n| Problem | Kind |\n| --- | --- |\n| Furniture shipment | deadline |\n"
    assert any(f.startswith("C9") and "Furniture shipment" in f for f in gate.check(GOOD, old, "- 1: n/a\n"))
    note_d = "## Two ways to handle the 102 days\n\n### Stay close to the search\n\n- You stay.\n\n## Your money\n\n### Storage\n\n- The unit.\n"
    assert gate.previous_issues(note_d) == ["Storage"]


def test_pass_leaves_the_stamp_to_note_build(tmp_path, monkeypatch, capsys):
    stamps = tmp_path / "stamps"
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(stamps))
    draft = tmp_path / "draft.md"
    draft.write_text(GOOD, encoding="utf-8")
    assert gate.main([str(draft)]) == 0
    out = capsys.readouterr().out
    assert "PASS" in out and "note-gate:" not in out
    assert not stamps.exists() or not any(stamps.iterdir())
