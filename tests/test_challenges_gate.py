import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills/life-challenges/scripts/challenges_gate.py"
_spec = importlib.util.spec_from_file_location("challenges_gate", _p)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

GOOD = """## Takeaway

- Your deciding question is whether your marriage is decided in the first half of 2027.
- You decide the storage first: the Gongdeok unit had one left on 2026-10-30.
- You can hand two issues to me with /life.

## The deciding question

Is your marriage decided in the first half of 2027?

- If yes, you would consider buying an apartment in the second half of 2027.
- If not, you rent again.

## Your decisions

You have one decision open.

### Storage

Do you book the Gongdeok storage unit, or keep the clothes and papers somewhere free?

1. Book the unit: 72090 won a month, one month minimum.
2. Ask the family that receives your furniture to keep one box: free.

Your choice depends on whether the family has space for one box until 2027-03-16.

## Hand to me

You can hand these issues to me, and each command prepares one for your approval.

| Issue | I do | You decide | Command |
| --- | --- | --- | --- |
| TAS email | draft the No Response email to the Form 911 address | approve or correct it, then you send it | `/life tas` |
| Tax office call | write the Korean call script for 소득세과 | approve it, then you call before 2026-12-04 | `/life tax` |

## Settled

You have settled one issue since the last note.

- The clinic invoices: filed on 2026-11-06.
"""


def codes(fails):
    return {f.split()[0] for f in fails}


def test_good_note_passes():
    assert gate.check(GOOD) == []


def test_extra_section_fails():
    fails = gate.check(GOOD + "\n## Ready to use\n\nYou can send this.\n")
    assert any(f.startswith("C4") and "ready to use" in f for f in fails)


def test_missing_settled_fails():
    fails = gate.check(GOOD[:GOOD.index("## Settled")])
    assert any(f.startswith("C4 section missing") and "Settled" in f for f in fails)


def test_section_order_fails():
    hand = GOOD[GOOD.index("## Hand to me"):GOOD.index("## Settled")]
    moved = GOOD.replace(hand, "").replace("## Your decisions", hand + "## Your decisions")
    assert any(f.startswith("C4 sections out of order") for f in gate.check(moved))


def test_decision_needs_question_options_and_tipping_fact():
    fails = gate.check(GOOD.replace("or keep the clothes and papers somewhere free?", "or keep them somewhere free."))
    assert any(f.startswith("C5") and "question" in f for f in fails)
    fails = gate.check(GOOD.replace("2. Ask the family that receives your furniture to keep one box: free.\n", ""))
    assert any(f.startswith("C5") and "1 numbered options" in f for f in fails)
    fails = gate.check(GOOD.replace("Your choice depends on whether", "Whether"))
    assert any(f.startswith("C5") and "depends on" in f for f in fails)


def test_decision_label_word_fails_unless_quoted():
    fails = gate.check(GOOD.replace("Your choice depends on whether the family", "Your avoidance of asking matters. Your choice depends on whether the family"))
    assert any(f.startswith("C5") and "avoidance" in f for f in fails)
    ok = GOOD.replace("Your choice depends on whether the family", "You called it \"my fear of asking\". Your choice depends on whether the family")
    assert not any(f.startswith("C5") for f in gate.check(ok))


def test_hand_to_me_command_and_cells():
    assert "C6" in codes(gate.check(GOOD.replace("`/life tas`", "`/lc tas`")))
    assert any("used by" in f for f in gate.check(GOOD.replace("`/life tax`", "`/life tas`")))
    assert any("empty cell" in f for f in gate.check(GOOD.replace("| approve or correct it, then you send it |", "|  |")))
    fails = gate.check(GOOD.replace("## Settled", "### TAS draft\n\nYou send this.\n\n## Settled"))
    assert any(f.startswith("C6") and "on demand" in f for f in fails)


def test_takeaway_bullets_only_and_at_most_three():
    fails = gate.check(GOOD.replace("- You can hand two issues to me with /life.",
                                    "- You can hand two issues to me with /life.\n- You place the sell orders by 2026-12-31."))
    assert any(f.startswith("C7") and "4 bullets" in f for f in fails)
    fails = gate.check(GOOD.replace("## Takeaway\n\n", "## Takeaway\n\nYou have a lot going on.\n\n"))
    assert "C7" in codes(fails)


def test_empty_heading_pronoun_separator_ssn():
    assert "C1" in codes(gate.check(GOOD.replace("## Settled", "### Spare\n\n## Settled")))
    assert "C2" in codes(gate.check(GOOD.replace("one month minimum", "his one month minimum")))
    assert "C3" in codes(gate.check(GOOD.replace("72090 won", "72,090 won")))
    assert "C8" in codes(gate.check(GOOD.replace("Form 911 address", "Form 911 address, SSN 605-98-1744")))


def test_deciding_question_form():
    fails = gate.check(GOOD.replace("Is your marriage decided in the first half of 2027?",
                                    "Your marriage may be decided in the first half of 2027."))
    assert any(f.startswith("C10") and "'?'" in f for f in fails)
    fails = gate.check(GOOD.replace("- Your deciding question is whether your marriage is decided in the first half of 2027.",
                                    "- You fly to Osaka on 2026-12-04 with every flight booked."))
    assert any(f.startswith("C10") and "Takeaway" in f for f in fails)


def test_previous_issues_carried_in_either_format():
    old = "## Problems\n\n| Problem | Kind |\n| --- | --- |\n| Gayeon consult | one missing fact |\n| Storage | deadline |\n"
    fails = gate.check(GOOD, old, "- 1: n/a\n")
    assert any(f.startswith("C9") and "Gayeon consult" in f for f in fails)
    assert not any("'Storage'" in f for f in fails if f.startswith("C9"))
    assert gate.check(GOOD, old, "- Gayeon consult: you dropped the second agency\n") == []
    fails = gate.check(GOOD.replace("Tax office call", "Tax call"), GOOD, "- x: y\n")
    assert any(f.startswith("C9") and "Tax office call" in f for f in fails)
    assert not any("'Storage'" in f or "'TAS email'" in f for f in fails if f.startswith("C9"))


def test_lost_fact_needs_the_cut_list():
    original = "## Storage\n\n- The unit costs 88000 won a month.\n"
    assert any(f.startswith("T6 a note built") for f in gate.check(GOOD, original))
    assert any("88000" in f for f in gate.check(GOOD, original, "- Storage: kept\n"))
    assert gate.check(GOOD, original, "- 88000: the old price, replaced by 72090\n") == []


def test_pass_prints_the_note_gate_marker(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path))
    draft = tmp_path / "note.md"
    draft.write_text(GOOD, encoding="utf-8")
    assert gate.main([str(draft)]) == 0
    out = capsys.readouterr().out
    assert "note-gate:" in out and out.strip().endswith("PASS")
