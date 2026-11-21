"""Tests for `scripts/repo_sweep.py`, a read-only table of uncommitted work and stale worktrees.

The script only runs git commands that read, so the fixture builds a bare remote and a clone with
one pushed commit, one unpushed commit, one uncommitted file and a second worktree on another branch
whose last commit is dated ten days back through `GIT_COMMITTER_DATE`.
"""
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "repo_sweep.py"


def git(cwd: Path, *args: str, env: dict | None = None) -> str:
    merged = dict(os.environ, **(env or {}))
    done = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=merged
    )
    return done.stdout.strip()


def build_fixture(tmp_path: Path) -> tuple[Path, Path, date]:
    """A bare remote, a clone with one pushed and one unpushed commit, one uncommitted file,
    and a worktree on branch `side` whose last commit is ten days back."""
    remote = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "-q", "--bare", "--initial-branch=main", str(remote)], check=True
    )
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", "-q", str(remote), str(repo)], check=True)
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "Test")

    (repo / "a.txt").write_text("one\n")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-q", "-m", "first")
    git(repo, "push", "-q", "-u", "origin", "HEAD")

    (repo / "b.txt").write_text("two\n")
    git(repo, "add", "b.txt")
    git(repo, "commit", "-q", "-m", "unpushed")
    (repo / "c.txt").write_text("three\n")

    stale_day = date.today() - timedelta(days=10)
    stamp = {"GIT_AUTHOR_DATE": f"{stale_day} 12:00:00", "GIT_COMMITTER_DATE": f"{stale_day} 12:00:00"}
    side = tmp_path / "side"
    git(repo, "worktree", "add", "-q", "-b", "side", str(side))
    (side / "d.txt").write_text("four\n")
    git(side, "add", "d.txt")
    git(side, "commit", "-q", "-m", "side commit", env=stamp)
    return repo, side, stale_day


def sweep(tmp_path: Path, repos: list[Path], days: int = 7) -> str:
    out = tmp_path / "sweep.md"
    done = subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, repos), "--out", str(out), "--days", str(days)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0
    return out.read_text()


def rows_of(text: str) -> dict[str, list[str]]:
    """Map each worktree path to its cells after the repository name."""
    rows: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("| ") or "Repository" in line or set(line) <= set("|- "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows[cells[1]] = cells[1:]
    return rows


def test_a_table_row_per_worktree_with_its_state(tmp_path: Path) -> None:
    repo, side, stale_day = build_fixture(tmp_path)
    text = sweep(tmp_path, [repo])

    assert text.splitlines()[0].startswith(date.today().isoformat())
    assert "1 repository" in text.splitlines()[0]
    rows = rows_of(text)
    assert set(rows) == {".", "../side"}
    assert rows["."] == [
        ".", "main", date.today().isoformat(), "0", "1", "1", "uncommitted, unpushed"
    ]
    assert rows["../side"] == [
        "../side", "side", stale_day.isoformat(), "10", "0", "0", "no upstream, stale"
    ]


def test_a_pushed_worktree_is_clean_and_not_stale(tmp_path: Path) -> None:
    repo, _, _ = build_fixture(tmp_path)
    git(repo, "add", "c.txt")
    git(repo, "commit", "-q", "-m", "third")
    git(repo, "push", "-q")

    rows = rows_of(sweep(tmp_path, [repo]))
    assert rows["."] == [".", "main", date.today().isoformat(), "0", "0", "0", "clean"]


def test_help_names_its_arguments() -> None:
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True
    )
    assert done.returncode == 0
    for word in ("--out", "--days", "7"):
        assert word in done.stdout
