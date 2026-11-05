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


def test_note_mode_lists_lost_words_without_failing():
    draft = ORIG.replace("- Acceptance leaves the owner unstated.", "- Reception is her side.")
    assert gate.check(draft, ORIG, note=True) == []
    assert "acceptance" in gate.lost_words(draft, ORIG)
