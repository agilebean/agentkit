"""The check that counts a private list's terms in a tree or a history without printing them (DD-03).

The list itself stays in socrates, so this test builds a small repository of its own in `tmp_path`
and uses invented terms: `zorblat`, `quibbleflux` and the regex `zor[a-z]+t`. That way the test
can assert on the counts, the exit code and on the fact that no term reaches the output.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "history_check.py"
TERMS = {"zorblat", "quibbleflux", "zorblatium"}


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def repo_with_two_commits(tmp_path: Path) -> Path:
    """A repository whose first commit holds the terms and whose second commit deletes the file."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    (repo / "notes.md").write_text("a line with zorblat and zorblat again\n", encoding="utf-8")
    (repo / "data.bin").write_bytes(b"\x00zorblat")
    git(repo, "add", "notes.md", "data.bin")
    git(repo, "commit", "-q", "-m", "first, holding quibbleflux")
    git(repo, "rm", "-q", "notes.md", "data.bin")
    git(repo, "commit", "-q", "-m", "second, quibbleflux is gone")
    return repo


def assert_no_term(result: subprocess.CompletedProcess) -> None:
    shown = result.stdout + result.stderr
    for term in TERMS:
        assert term not in shown, shown


def test_a_tree_counts_literals_and_regex_and_names_the_rule_by_its_line(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "a.md").write_text("zorblat twice: zorblat\n", encoding="utf-8")
    (tree / "b.md").write_text("zorblatium once\n", encoding="utf-8")
    (tree / "c.bin").write_bytes(b"\x00zorblat")
    rules = tmp_path / "rules.txt"
    rules.write_text("# a comment\nzorblat==>one\nquibbleflux==>two\nregex:zor[a-z]+t==>three\n", encoding="utf-8")

    result = run("--rules", str(rules), "--tree", str(tree))

    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.strip().splitlines() == [
        "rule 2: 3 hits in files",
        "rule 4: 3 hits in files",
        "history_check: 6 hits",
    ], result.stdout
    assert_no_term(result)


def test_a_clean_tree_exits_0(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "a.md").write_text("nothing to see\n", encoding="utf-8")
    rules = tmp_path / "rules.txt"
    rules.write_text("zorblat==>one\nregex:zor[a-z]+t==>two\n", encoding="utf-8")

    result = run("--rules", str(rules), "--tree", str(tree))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip().splitlines() == ["history_check: 0 hits"], result.stdout


def test_a_history_counts_blobs_of_earlier_commits_and_commit_messages(tmp_path: Path) -> None:
    repo = repo_with_two_commits(tmp_path)
    rules = tmp_path / "rules.txt"
    rules.write_text("# a comment\nzorblat==>one\nquibbleflux==>two\n", encoding="utf-8")

    result = run("--rules", str(rules), "--repo", str(repo))

    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.strip().splitlines() == [
        "rule 2: 2 hits in blobs",
        "rule 3: 2 hits in blobs",
        "history_check: 4 hits",
    ], result.stdout
    assert_no_term(result)


def test_a_tree_reads_committed_files_only(tmp_path: Path) -> None:
    repo = repo_with_two_commits(tmp_path)
    rules = tmp_path / "rules.txt"
    rules.write_text("zorblat==>one\n", encoding="utf-8")

    result = run("--rules", str(rules), "--tree", str(repo))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip().splitlines() == ["history_check: 0 hits"], result.stdout


def test_a_missing_rules_file_exits_2(tmp_path: Path) -> None:
    result = run("--rules", str(tmp_path / "none.txt"), "--tree", str(tmp_path))

    assert result.returncode == 2, result.stdout + result.stderr
    assert "no rules file" in result.stderr
