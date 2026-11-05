import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills/life-overview/scripts/overview_gate.py"
_spec = importlib.util.spec_from_file_location("overview_gate", _p)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

LINK = "[Seoul Mapo storage locker](evernote:///view/39d2f74/s365/g/g/)"

GOOD = f"""## Takeaway

- Your clothes and papers have no home after 2026-12-04, and the unit that fits had one left.

## Seoul storage

- The unit fits the clothes.
  - It costs 72090 won a month.
- {LINK}

## Open tasks

| Thread | Next move |
| --- | --- |
| Seoul storage | book the 72090 won unit through the monthly link |
"""

BAD = """## Takeaway

- Seoul storage: book the 72090 won unit through the monthly link.

## Seoul storage

- The unit costs 72090 won a month.

## Open tasks

| Thread | Next move |
| --- | --- |
| Seoul storage | book the 72090 won unit through the monthly link |
"""


def test_good_draft_passes():
    assert gate.check(GOOD) == []


def test_bad_draft_names_each_failure():
    fails = gate.check(BAD)
    kinds = {f.split()[0] for f in fails}
    assert kinds == {"T3", "T4", "T5"}
    assert any("book the 72090 won unit" in f for f in fails if f.startswith("T3"))
    assert any("'Seoul storage'" in f for f in fails if f.startswith("T4"))


def test_fact_loss_detected_and_linked_note_counts():
    original = "Storage paid to 2023-11-06, 0.575 cbm."
    assert gate.check(GOOD, original) == ["T6 fact lost: 0.575", "T6 fact lost: 2023-11-06"]
    assert gate.check(GOOD, original, ["0.575 cbm, paid to 2023-11-06"]) == []


def test_cli_exit_code(tmp_path, capsys):
    f = tmp_path / "d.md"
    f.write_text(BAD)
    assert gate.main([str(f)]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_section_may_declare_no_detail_note():
    draft = GOOD.replace("## Open tasks", "## Health\n\n- Gluten is out since 2026-10-19 (no detail note).\n\n## Open tasks")
    assert gate.check(draft) == []


def test_facts_only_skips_overview_checks():
    original = "Storage paid to 2023-11-06."
    note = "## Takeaway\nThe 2020 sample is better. Storage was paid to 2023-11-06."
    assert gate.check(note, original, facts_only=True) == []
    assert gate.check("## Takeaway\nThe 2020 sample is better.", original, facts_only=True) == ["T6 fact lost: 2023-11-06"]


def test_note_mode_flags_prose_sections_and_passes_lists():
    prose = "## How it is made\nThe vesicles go first. The prostate follows. The sperm come last. Then it is pumped out.\n"
    listed = "## How it is made\n1. The vesicles go first.\n   - 60 to 70% of the volume.\n2. The prostate follows.\n"
    assert gate.check(prose, note=True) == ["T5 section is prose of 4 sentences, write it as a list: 'How it is made'"]
    assert gate.check(listed, note=True) == []


ORIG = """## Assembly
- Arousal comes first.
- Emission follows.

| Source | Reads as |
| --- | --- |
| Prostate | Sour and sharp |

## Words
- Acceptance leaves the owner unstated.
"""


def test_note_mode_fails_on_lost_table_row_and_empty_bullet():
    draft = "## Assembly\n- Arousal comes first.\n- \n- Emission follows.\n\n## Words\n- Reception is her side.\n"
    fails = gate.check(draft, ORIG, note=True)
    assert "T7 table row lost: | Prostate | Sour and sharp |" in fails
    assert "T8 empty list item at line 3" in fails


def test_note_mode_passes_a_reworded_line() -> None:
    draft = ORIG.replace("- Acceptance leaves the owner unstated.", "- Reception is her side.")
    assert gate.check(draft, ORIG, note=True) == []


def test_a_cut_list_lets_a_fact_leave_with_its_destination() -> None:
    original = "## Buying\n- Swanson 100 mg, 30 capsules, 39647 won.\n- Prelox, 62118 won.\n"
    draft = "## Buying\n- Pycnogenol 100 mg from any brand.\n"
    assert "T6 fact lost: 39647" in gate.check(draft, original, note=True)
    cuts = "- 39647, 62118, 30: brand prices, any brand at 100 mg works\n"
    assert gate.check(draft, original, note=True, cuts=cuts) == []


def test_a_cut_without_its_reason_fails() -> None:
    original = "## Buying\n- Prelox, 62118 won.\n"
    fails = gate.check("## Buying\n- Pycnogenol.\n", original, note=True, cuts="- 62118\n")
    assert any(f.startswith("T9") for f in fails)


SUMMARY = "## Summary\n\n" + "".join(f"- Decision {i} is short.\n" for i in range(6)) + "\n## Body\n- Detail.\n"


def test_a_summary_over_five_lines_fails() -> None:
    assert any(f.startswith("T10") for f in gate.check(SUMMARY, note=True))


def test_a_long_summary_line_fails() -> None:
    draft = "## Summary\n- " + " ".join(["word"] * 31) + ".\n\n## Body\n- Detail.\n"
    assert any(f.startswith("T10") for f in gate.check(draft, note=True))


def test_a_summary_line_that_repeats_a_body_line_fails() -> None:
    line = "Pycnogenol raises the erection score 9.2 points across 23 trials in 1583 men"
    draft = f"## Summary\n- {line}.\n\n## Evidence\n- {line}, Ramasamy 2024.\n"
    assert any(f.startswith("T11") for f in gate.check(draft, note=True))


def test_more_than_seven_siblings_fail() -> None:
    flat = "## Buying\n" + "".join(f"- Item {i}.\n" for i in range(8))
    grouped = "## Buying\n" + "".join(f"- Group {g}.\n" + "".join(f"  - Item {i}.\n" for i in range(4)) for g in range(2))
    assert any(f.startswith("T12") for f in gate.check(flat, note=True))
    assert not any(f.startswith("T12") for f in gate.check(grouped, note=True))
