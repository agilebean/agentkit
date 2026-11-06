import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills/life-problems/scripts/problems_gate.py"
_spec = importlib.util.spec_from_file_location("problems_gate", _p)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

GOOD = """## Takeaway

- You have one knot: the order of the marriage and the green card decides whether you buy in Mapo.
- You can put two threads down after one message each.
- Your quick wins take about 15 minutes.

## The knot

You have one knot: the order of the marriage and the green card decides the Mapo purchase.

- The purchase decides what the stock money is for.
  - While the order is open, keep the money in cash.

## What you can put down

You can put these down after one message each.

- The Taxpayer Advocate: send the No Response email, and then it is their move.
- The clinic invoices: filed on 2026-11-06.

## Quick wins

You can finish each of these in one sitting.

| Task | Effort | What it takes off you | Ready to use |
| --- | --- | --- | --- |
| Email the Taxpayer Advocate | 5 min | a case silent since 2026-10-30 | TAS email |
| Call 소득세과 | 10 min, call | a fax unconfirmed since 2026-09-29 | Tax office call |

## Decisions

You have one decision open.

### The Mapo flat

You want a home in Seoul and you want to keep the green card open, and a purchase makes you choose.

- If the marriage comes first, buy in Mapo; if the green card comes first, rent for 12 months.
- You still need to know the order.
- While you wait, rent for 12 months.

## Problems

You have these problems open now.

| Problem | Kind of stuck | What weighs on you | Next move |
| --- | --- | --- | --- |
| Mapo flat | waits on another decision | a 21억 purchase with two inputs open | rent for 12 months |
| Korean tax letter | someone else's move | open since 2026-09-29 | call 소득세과 |

## Ready to use

You can send or say each of these as it stands.

### TAS email

You send this to the Form 911 address.

My case has had no response since 2026-10-30. Please tell me who holds it now. I can send any document you need.

### Tax office call

You say this to 소득세과 on 02-705-7361.

- If the fax is on file, ask for the review result in writing.
- If it is not on file, send the letter through 국민신문고.
"""


def codes(fails):
    return {f.split()[0] for f in fails}


def test_good_map_passes():
    assert gate.check(GOOD) == []


def test_empty_heading_fails():
    fails = gate.check(GOOD.replace("### Tax office call", "### Storage\n\n### Tax office call"))
    assert any(f.startswith("P1") and "Storage" in f for f in fails)


def test_third_person_fails():
    fails = gate.check(GOOD.replace("two inputs open", "his two inputs open"))
    assert "P2" in codes(fails)


def test_thousand_separator_fails():
    fails = gate.check(GOOD.replace("21억 purchase", "1,345 won purchase"))
    assert "P3" in codes(fails)
    fails = gate.check(GOOD.replace("21억 purchase", "$4,180, about 5.6M won, purchase"))
    assert any("4,180" in f for f in fails)


def test_missing_section_fails():
    start = GOOD.index("## What you can put down")
    end = GOOD.index("## Quick wins")
    fails = gate.check(GOOD[:start] + GOOD[end:])
    assert any(f.startswith("P4 section missing") for f in fails)


def test_unknown_kind_fails():
    fails = gate.check(GOOD.replace("| waits on another decision |", "| blocked |"))
    assert "P5" in codes(fails)


def test_burden_without_a_fact_fails():
    fails = gate.check(GOOD.replace("open since 2026-09-29", "the receipt is missing"))
    assert any(f.startswith("P6") and "no date" in f for f in fails)


def test_burden_with_a_label_word_fails():
    fails = gate.check(GOOD.replace("a 21억 purchase", "avoidance of a 21억 purchase"))
    assert any(f.startswith("P6") and "avoidance" in f for f in fails)


def test_quoted_label_word_passes():
    assert gate.check(GOOD.replace("a 21억 purchase", "\"my fear\" of a 21억 purchase")) == []


def test_quick_win_without_instrument_fails():
    fails = gate.check(GOOD.replace("| TAS email |", "| draft it |"))
    assert "P7" in codes(fails)


def test_call_without_branches_fails():
    fails = gate.check(GOOD.replace("- If the fax", "- When the fax").replace("- If it is not", "- When it is not"))
    assert "P8" in codes(fails)


def test_decision_without_dilemma_fails():
    fails = gate.check(GOOD.replace("- While you wait, rent", "- Meanwhile, rent"))
    assert any(f.startswith("P9") and "While you wait" in f for f in fails)
    fails = gate.check(GOOD.replace("You want a home in Seoul and you want", "You need a home in Seoul and"))
    assert any(f.startswith("P9") and "dilemma" in f for f in fails)


def test_takeaway_must_lead_with_the_knot():
    fails = gate.check(GOOD.replace(
        "You have one knot: the order of the marriage and the green card decides whether you buy in Mapo.",
        "You fly to Osaka on 2026-12-04 with every flight booked."))
    assert "P10" in codes(fails)


def test_lost_fact_needs_the_cut_list():
    original = "## Storage\n\n- The unit costs 72090 won a month.\n"
    assert any(f.startswith("T6 a map built") for f in gate.check(GOOD, original))
    assert any("72090" in f for f in gate.check(GOOD, original, "- 2026-11-06: filed\n"))
    assert gate.check(GOOD, original, "- 72090: the storage unit is booked\n") == []


def test_pass_prints_the_note_gate_marker(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path))
    draft = tmp_path / "map.md"
    draft.write_text(GOOD, encoding="utf-8")
    assert gate.main([str(draft)]) == 0
    out = capsys.readouterr().out
    assert "note-gate:" in out and out.strip().endswith("PASS")
    assert len(list(tmp_path.glob("[0-9a-f]" * 8 + "*"))) == 1


def test_effort_needs_minutes():
    fails = gate.check(GOOD.replace("| 10 min, call |", "| 10 call |"))
    assert any(f.startswith("P7") and "minutes" in f for f in fails)


def test_verbatim_drafts_fail():
    fails = gate.check(GOOD.replace("My case has had", "<!-- verbatim -->\nMy case has had")
                       .replace("any document you need.", "any document you need.\n<!-- end verbatim -->"))
    assert "P11" in codes(fails)


def test_social_security_number_fails():
    fails = gate.check(GOOD.replace("My case has had", "SSN 605-98-1744. My case has had"))
    assert any(f.startswith("P12") and "ending 1744" in f for f in fails)


def test_dropped_problem_needs_a_cut_line():
    original = "## The three decisions\n\n### 1. Seoul housing\n\n- The flat.\n\n### 2. Korean tax letter\n\n- The fax.\n"
    fails = gate.check(GOOD, original, "- 1, 2: section numbers\n")
    assert any(f.startswith("P13") and "Seoul housing" in f for f in fails)
    assert not any("Korean tax letter" in f for f in fails)
    assert gate.check(GOOD, original, "- 1, 2: section numbers\n- Seoul housing: folded into the Mapo flat row\n") == []


def test_takeaway_prose_line_fails():
    fails = gate.check(GOOD.replace("## Takeaway\n\n", "## Takeaway\n\nYou have a lot going on.\n\n"))
    assert "P14" in codes(fails)
