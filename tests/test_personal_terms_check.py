"""The check that searches a tree for Chaehan's personal terms (DD-03, step 3).

The list of terms lives in socrates and reaches this check through a file on the command line or
through an environment variable in the workflow, so the terms themselves never enter agentkit
and never reach a log: a hit is printed as `path:line: term N`, where N is the term's 1-based
position among the list's terms.

The fixtures below use invented terms, so this file can stand inside the tree the check searches.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

AGENTKIT = Path(__file__).resolve().parents[1]
SCRIPT = AGENTKIT / "scripts" / "personal_terms_check.py"

TERMS = "# a comment line\n\nzorblat\nquibbleflux\n"


def run(tree: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--tree", str(tree), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_a_term_in_the_tree_exits_1_and_names_the_file_and_line(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("one line\ncurse of the zorblat\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    terms.write_text(TERMS, encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(terms))

    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.strip().splitlines() == ["notes.md:2: term 1"], result.stdout


def test_the_hit_names_the_terms_position_in_the_list(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("a quibbleflux here\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    terms.write_text(TERMS, encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(terms))

    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.strip().splitlines() == ["notes.md:1: term 2"], result.stdout


def test_the_list_inside_the_tree_is_not_searched(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("nothing personal here\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    terms.write_text(TERMS, encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(terms))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "", result.stdout


def test_a_clean_tree_exits_0_with_no_hit(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("nothing personal here\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    terms.write_text(TERMS, encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(terms))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "", result.stdout


def test_a_missing_list_exits_0_and_says_it_skipped(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("curse of the zorblat\n", encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(tmp_path / "absent.txt"))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "personal_terms_check: no terms list, check skipped", result.stdout


def test_an_empty_list_exits_0_and_says_it_skipped(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("curse of the zorblat\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    terms.write_text("# only a comment\n\n", encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(terms))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "personal_terms_check: no terms list, check skipped", result.stdout


def test_a_binary_file_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01zorblat\x00\x02")
    (tmp_path / "notes.md").write_text("nothing personal here\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    terms.write_text(TERMS, encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(terms))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "", result.stdout


def test_git_and_pycache_are_skipped(tmp_path: Path) -> None:
    for name in (".git", "__pycache__"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "notes.md").write_text("curse of the zorblat\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    terms.write_text(TERMS, encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(terms))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "", result.stdout


def test_the_list_can_arrive_in_an_environment_variable(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("curse of the zorblat\n", encoding="utf-8")
    env = dict(os.environ)
    env["PERSONAL_TERMS_FOR_TEST"] = TERMS

    result = run(tmp_path, "--from-env", "PERSONAL_TERMS_FOR_TEST", env=env)

    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.strip().splitlines() == ["notes.md:1: term 1"], result.stdout


def test_an_absent_environment_variable_says_it_skipped(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("curse of the zorblat\n", encoding="utf-8")
    env = {key: value for key, value in os.environ.items() if key != "PERSONAL_TERMS_ABSENT"}

    result = run(tmp_path, "--from-env", "PERSONAL_TERMS_ABSENT", env=env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "personal_terms_check: no terms list, check skipped", result.stdout


def test_the_term_itself_is_never_printed(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("curse of the zorblat\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    terms.write_text(TERMS, encoding="utf-8")

    result = run(tmp_path, "--terms-file", str(terms))

    assert result.returncode == 1, result.stdout + result.stderr
    assert "zorblat" not in result.stdout, result.stdout
    assert "zorblat" not in result.stderr, result.stderr
