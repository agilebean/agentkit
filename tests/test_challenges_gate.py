import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills/life-challenges/scripts/challenges_gate.py"
_spec = importlib.util.spec_from_file_location("challenges_gate", _p)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

GOOD = """## Takeaway

- Your family search is moving, and from 2026-12-04 you are away for 102 days.
- Your largest sum, the USD 371250 refund, waits on one email of ~5 minutes.
- Your housing waits on the marriage, so until then you rent and decide only small things.

## Family

You want a partner to have children with.

- From 2026-12-04 you are away for 102 days, so a woman you like in November waits until 2027-03-16.
  - The 183-day line leaves ~9 days of slack, so 2027-03-07 is your earliest return.
- Do you still want a second agency next to J Noble?
  - Book the Gayeon free consult now.
  - Wait until the four J Noble dates have happened.

## Home

You want Korea as your home base.

- Your deciding question: is your marriage decided in the first half of 2027?
  - If yes, you would consider buying an apartment in the second half of 2027.
  - If not, you rent again.
- Where do your winter clothes stay from 2026-12-04?
  - The Gongdeok unit: 72090 won a month.
  - The family that receives your furniture: free.

## Hand to me

You can hand these issues to me, and each command prepares one for your approval.

| Issue | I do | You decide | Command |
| --- | --- | --- | --- |
| TAS email | draft the No Response email to the Form 911 address | approve or correct it, then you send it | `/life tas` |
| Tax office call | write the Korean call script for 소득세과 | approve it, then you call before 2026-12-04 | `/life tax` |
"""


def codes(fails):
    return {f.split()[0] for f in fails}


def test_good_note_passes():
    assert gate.check(GOOD) == []


def test_settled_is_optional_and_last():
    assert gate.check(GOOD + "\n## Settled\n\nYou have filed the clinic invoices.\n\n- Filed on 2026-11-06.\n") == []
    moved = GOOD.replace("## Hand to me", "## Settled\n\nYou have filed the clinic invoices.\n\n- Filed on 2026-11-06.\n\n## Hand to me")
    assert any(f.startswith("C4") and "Settled" in f for f in gate.check(moved))


def test_takeaway_first_hand_to_me_required_goal_between():
    assert any("open with" in f for f in gate.check(GOOD.replace("## Takeaway", "## Summary")))
    assert any("Hand to me" in f for f in gate.check(GOOD[:GOOD.index("## Hand to me")]))
    no_goal = GOOD[:GOOD.index("## Family")] + GOOD[GOOD.index("## Hand to me"):]
    assert any("no goal section" in f for f in gate.check(no_goal))


def test_decision_needs_two_to_four_options():
    one = GOOD.replace("  - Wait until the four J Noble dates have happened.\n", "")
    assert any(f.startswith("C5") and "1 options" in f for f in gate.check(one))
    five = GOOD.replace("  - Wait until the four J Noble dates have happened.\n",
                        "  - Wait.\n  - Drop it.\n  - Ask J Noble.\n  - Ask a friend.\n")
    assert any(f.startswith("C5") and "5 options" in f for f in gate.check(five))


def test_label_word_fails_unless_quoted():
    bad = GOOD.replace("You want Korea as your home base.", "You want Korea as your home base, and your avoidance shows.")
    assert any(f.startswith("C5") and "avoidance" in f for f in gate.check(bad))
    ok = GOOD.replace("You want Korea as your home base.", "You want Korea as your home base, \"without my fear of renting\".")
    assert not any(f.startswith("C5") for f in gate.check(ok))


def test_hand_to_me_command_and_cells():
    assert "C6" in codes(gate.check(GOOD.replace("`/life tas`", "`/lc tas`")))
    assert any("used by" in f for f in gate.check(GOOD.replace("`/life tax`", "`/life tas`")))
    assert any("empty cell" in f for f in gate.check(GOOD.replace("| approve or correct it, then you send it |", "|  |")))
    assert any(f.startswith("C6") and "on demand" in f for f in gate.check(GOOD + "\n### TAS draft\n\nYou send this.\n"))


def test_takeaway_bullets_only_and_at_most_three():
    four = GOOD.replace("- Your housing waits", "- You sell CRWV before 2026-12-31.\n- Your housing waits")
    assert any(f.startswith("C7") and "4 bullets" in f for f in gate.check(four))
    assert "C7" in codes(gate.check(GOOD.replace("## Takeaway\n\n", "## Takeaway\n\nYou have a lot going on.\n\n")))


def test_empty_heading_pronoun_separator_ssn():
    assert "C1" in codes(gate.check(GOOD.replace("## Hand to me", "## Work\n\n## Hand to me")))
    assert "C2" in codes(gate.check(GOOD.replace("72090 won a month", "his 72090 won a month")))
    assert "C3" in codes(gate.check(GOOD.replace("72090 won", "72,090 won")))
    assert "C8" in codes(gate.check(GOOD.replace("Form 911 address", "Form 911 address, SSN 605-98-1744")))


def test_previous_issues_carried_in_any_format():
    old = "## Problems\n\n| Problem | Kind |\n| --- | --- |\n| Gayeon free consult | one missing fact |\n| Furniture shipment | deadline |\n"
    fails = gate.check(GOOD, old, "- 1: n/a\n")
    assert any(f.startswith("C9") and "Furniture shipment" in f for f in fails)
    assert gate.check(GOOD, old, "- Furniture shipment: the arrival is confirmed\n") == []
    fails = gate.check(GOOD.replace("Tax office call", "Tax call"), GOOD, "- x: y\n")
    assert any(f.startswith("C9") and "Tax office call" in f for f in fails)


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
    assert "note-gate:" in capsys.readouterr().out
