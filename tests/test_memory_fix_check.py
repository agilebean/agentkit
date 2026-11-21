"""The checker that refuses a memory fix which changes a fact (DD-11, rules C1 to C5).

A proposals file holds one table per memory file: the line, its check, the line as the file
holds it, and the line as it would stand after the fix. The checker reads the memory file, runs
`scripts/memory_lint.py`'s `lint` on it, and holds every row to four rules about the fix and one
about a `keep`.

C1  a flagged line of a section's file without a row, or a row for a line the lint does not
    flag. This run covers M1 and M3 only: a flagged line of M2 or M5 belongs to the other
    session and is neither a missing row nor an extra one.
C2  a `Line now` that differs from the file's line.
C3  a proposed line on which `memory_lint.lint` still finds a check.
C4  a proposed line that drops a number, a date, a quoted text or a backtick span of the line
    now.
C5  a `keep` without its reason, an M1 `keep` whose reason is not `no date in the record`, an M1
    `keep: no date in the record` on a line that carries a date, or a `keep` for a check that
    is not M1, M3 or M5.

The fixtures below build a memory folder in `tmp_path` and one broken proposals file per rule.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

AGENTKIT = Path(__file__).resolve().parents[1]
SCRIPT = AGENTKIT / "scripts" / "memory_fix_check.py"

# line 3 is M1, line 4 is M2, line 5 is M3, line 6 is M5, line 7 is M1 with a date of its own.
SAMPLE = r"""# sample

- Stock: 4 items today.
- This was superseded by 8 GB.
- the cause is likely the cache "the dark mode" | the disk.
- he wrote "you forgot the table" in the chat.
- On 2026-11-02 he wrote it today.
"""

HEADER = r"""# Proposed memory fixes

## memory/sample.md

| Line | Check | Line now | Proposed line |
|---|---|---|---|
"""

ROW_3 = r"| 3 | M1 | - Stock: 4 items today. | - Stock: 4 items on 2026-11-21. |" + "\n"
ROW_5 = r'| 5 | M3 | - the cause is likely the cache "the dark mode" \| the disk. | - the agent reads the cause as the cache "the dark mode" \| the disk. |' + "\n"
ROW_7 = r"| 7 | M1 | - On 2026-11-02 he wrote it today. | - On 2026-11-02 he wrote it. |" + "\n"
ROW_4 = r"| 4 | M1 | - This was superseded by 8 GB. | - This was set to 8 GB on 2026-11-21. |" + "\n"


def build(tmp_path: Path, rows: str) -> Path:
    (tmp_path / "memory").mkdir(exist_ok=True)
    (tmp_path / "memory" / "sample.md").write_text(SAMPLE, encoding="utf-8")
    proposals = tmp_path / "proposals.md"
    proposals.write_text(HEADER + rows, encoding="utf-8")
    return proposals


def run(proposals: Path, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(proposals), "--root", str(root)],
        cwd=str(AGENTKIT), capture_output=True, text=True,
    )


def test_the_good_file_passes(tmp_path: Path) -> None:
    """The M2 and M5 lines carry no row and are not missing rows; every M1 and M3 row passes."""
    done = run(build(tmp_path, ROW_3 + ROW_5 + ROW_7), tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "PASS" in done.stdout
    assert "3 row(s)" in done.stdout
    assert "M1 2" in done.stdout and "M3 1" in done.stdout


def test_c1_a_missing_row_is_refused(tmp_path: Path) -> None:
    done = run(build(tmp_path, ROW_3 + ROW_7), tmp_path)
    assert done.returncode == 1
    assert "C1" in done.stdout and "memory/sample.md:5" in done.stdout and "M3" in done.stdout


def test_c1_an_extra_row_is_refused(tmp_path: Path) -> None:
    """A row for a line the lint does not flag M1 or M3 on: line 4 is M2 only."""
    done = run(build(tmp_path, ROW_3 + ROW_5 + ROW_7 + ROW_4), tmp_path)
    assert done.returncode == 1
    assert "C1" in done.stdout and "memory/sample.md:4" in done.stdout


def test_c1_a_section_missing_for_a_flagged_file_is_refused(tmp_path: Path) -> None:
    (tmp_path / "memory").mkdir(exist_ok=True)
    (tmp_path / "memory" / "sample.md").write_text(SAMPLE, encoding="utf-8")
    (tmp_path / "memory" / "other.md").write_text("# other\n\n- he wrote it today.\n", encoding="utf-8")
    proposals = tmp_path / "proposals.md"
    proposals.write_text(HEADER + ROW_3 + ROW_5 + ROW_7, encoding="utf-8")
    done = run(proposals, tmp_path)
    assert done.returncode == 1
    assert "C1" in done.stdout and "memory/other.md" in done.stdout


def test_c2_a_changed_line_now_is_refused(tmp_path: Path) -> None:
    row = r"| 5 | M3 | - the cause is likely the cache | - the agent reads the cause as the cache |" + "\n"
    done = run(build(tmp_path, ROW_3 + row + ROW_7), tmp_path)
    assert done.returncode == 1
    assert "C2" in done.stdout and "memory/sample.md:5" in done.stdout


def test_c3_a_proposal_the_lint_still_flags_is_refused(tmp_path: Path) -> None:
    row = r"| 5 | M3 | - the cause is likely the cache \"the dark mode\" \| the disk. | - the cause is likely the disk. |" + "\n"
    done = run(build(tmp_path, ROW_3 + row + ROW_7), tmp_path)
    assert done.returncode == 1
    assert "C3" in done.stdout and "memory/sample.md:5" in done.stdout


def test_c4_a_dropped_number_is_refused(tmp_path: Path) -> None:
    row = r"| 3 | M1 | - Stock: 4 items today. | - Stock: items on 2026-11-21. |" + "\n"
    done = run(build(tmp_path, row + ROW_5 + ROW_7), tmp_path)
    assert done.returncode == 1
    assert "C4" in done.stdout and "memory/sample.md:3" in done.stdout and "4" in done.stdout


def test_c4_a_dropped_quote_is_refused(tmp_path: Path) -> None:
    row = r'| 5 | M3 | - the cause is likely the cache "the dark mode" \| the disk. | - the agent reads the cause as the cache \| the disk. |' + "\n"
    done = run(build(tmp_path, ROW_3 + row + ROW_7), tmp_path)
    assert done.returncode == 1
    assert "C4" in done.stdout and "memory/sample.md:5" in done.stdout and "the dark mode" in done.stdout


def test_c4_a_dropped_date_is_refused(tmp_path: Path) -> None:
    row = r"| 7 | M1 | - On 2026-11-02 he wrote it today. | - He wrote it. |" + "\n"
    done = run(build(tmp_path, ROW_3 + ROW_5 + row), tmp_path)
    assert done.returncode == 1
    assert "C4" in done.stdout and "memory/sample.md:7" in done.stdout and "2026-11-02" in done.stdout


def test_c5_a_keep_without_its_reason_is_refused(tmp_path: Path) -> None:
    row = r"| 5 | M3 | - the cause is likely the cache \"the dark mode\" \| the disk. | keep: |" + "\n"
    done = run(build(tmp_path, ROW_3 + row + ROW_7), tmp_path)
    assert done.returncode == 1
    assert "C5" in done.stdout and "memory/sample.md:5" in done.stdout


def test_c5_an_m1_keep_with_another_reason_is_refused(tmp_path: Path) -> None:
    row = r"| 3 | M1 | - Stock: 4 items today. | keep: the word is unimportant |" + "\n"
    done = run(build(tmp_path, row + ROW_5 + ROW_7), tmp_path)
    assert done.returncode == 1
    assert "C5" in done.stdout and "memory/sample.md:3" in done.stdout


def test_c5_an_m1_keep_on_a_dated_line_is_refused(tmp_path: Path) -> None:
    row = r"| 7 | M1 | - On 2026-11-02 he wrote it today. | keep: no date in the record |" + "\n"
    done = run(build(tmp_path, ROW_3 + ROW_5 + row), tmp_path)
    assert done.returncode == 1
    assert "C5" in done.stdout and "memory/sample.md:7" in done.stdout


def test_c5_an_m1_keep_with_no_date_in_the_line_passes(tmp_path: Path) -> None:
    row = r"| 3 | M1 | - Stock: 4 items today. | keep: no date in the record |" + "\n"
    done = run(build(tmp_path, row + ROW_5 + ROW_7), tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr


def test_an_m5_line_needs_no_row(tmp_path: Path) -> None:
    """Line 6 holds a quote addressed to the agent: M5 is out of scope, so it is not a C1 miss."""
    done = run(build(tmp_path, ROW_3 + ROW_5 + ROW_7), tmp_path)
    assert done.returncode == 0
    assert "you forgot" not in done.stdout
