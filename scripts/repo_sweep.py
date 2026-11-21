#!/usr/bin/env python3
"""One Markdown table of uncommitted files, unpushed commits and stale worktrees per repository.

    python3 scripts/repo_sweep.py ~/Software/Prototypes/agentkit ~/Software/Prototypes/socrates \\
        --out "$HOME/Software/Prototypes/socrates/docs/2026-11-21 repository sweep.md" --days 7

One row per worktree, written under one line that names the date and the number of repositories:

    | Repository | Worktree | Branch | Last commit | Age (days) | Uncommitted files | Unpushed commits | State |

State is the list of what holds, in this order: `uncommitted`, `unpushed`, `no upstream`, `stale`
(the last commit is older than `--days`), or `clean` when none holds. A worktree path is relative to
its repository and the main checkout is `.`.

The script deletes nothing. It runs only git commands that read: `worktree list --porcelain`,
`status --porcelain`, `rev-list --count`, `log -1`, `rev-parse` and `for-each-ref`. It never fetches,
pushes, prunes, removes a worktree, moves a branch or checks anything out.
"""
import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

HEADER = (
    "| Repository | Worktree | Branch | Last commit | Age (days) "
    "| Uncommitted files | Unpushed commits | State |\n"
    "|---|---|---|---|---|---|---|---|"
)


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a read-only git command and return the finished process."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    )


def is_repository(path: Path) -> bool:
    return git(path, "rev-parse", "--git-dir").returncode == 0


def worktrees(repo: Path) -> list[dict]:
    """Each worktree of the repository: its path, its branch and whether it is detached."""
    out = git(repo, "worktree", "list", "--porcelain")
    if out.returncode != 0:
        return []
    found: list[dict] = []
    current: dict = {}
    for line in out.stdout.splitlines():
        if line.startswith("worktree "):
            if current:
                found.append(current)
            current = {"path": Path(line[len("worktree "):]), "branch": None, "detached": False}
        elif line.startswith("branch refs/heads/"):
            current["branch"] = line[len("branch refs/heads/"):]
        elif line == "detached":
            current["detached"] = True
    if current:
        found.append(current)
    return found


def upstream(where: Path) -> str | None:
    out = git(where, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def row(repo: Path, tree: dict, days: int, today: date) -> list[str]:
    where = tree["path"]
    relative = Path(os.path.relpath(where, repo)).as_posix()
    branch = tree["branch"] or ("(detached)" if tree["detached"] else "(bare)")

    commit = git(where, "log", "-1", "--format=%cs").stdout.strip()
    age = (today - date.fromisoformat(commit)).days if commit else None

    status = git(where, "status", "--porcelain")
    uncommitted = len([line for line in status.stdout.splitlines() if line.strip()]) \
        if status.returncode == 0 else 0

    track = upstream(where)
    unpushed = 0
    if track:
        counted = git(where, "rev-list", "--count", f"{track}..HEAD")
        unpushed = int(counted.stdout.strip()) if counted.returncode == 0 else 0

    holds = []
    if uncommitted:
        holds.append("uncommitted")
    if unpushed:
        holds.append("unpushed")
    if not track:
        holds.append("no upstream")
    if age is not None and age > days:
        holds.append("stale")
    state = ", ".join(holds) if holds else "clean"

    return [
        repo.name,
        relative,
        branch,
        commit or "none",
        "" if age is None else str(age),
        str(uncommitted),
        str(unpushed),
        state,
    ]


def render(rows: list[list[str]], today: date, repositories: int) -> str:
    count = f"{repositories} repositor{'y' if repositories == 1 else 'ies'}"
    lines = [
        f"{today.isoformat()}: one row per worktree of {count}, nothing changed.",
        "",
        HEADER,
    ]
    lines += ["| " + " | ".join(cells) + " |" for cells in rows]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="One Markdown table of uncommitted files, unpushed commits and stale "
        "worktrees across repositories. It reads and deletes nothing."
    )
    parser.add_argument(
        "repositories",
        nargs="+",
        metavar="REPOSITORY",
        help="a folder of a git repository to read; a folder that is not a repository is skipped",
    )
    parser.add_argument(
        "--out", required=True, metavar="FILE", help="the Markdown file to write the table to"
    )
    parser.add_argument(
        "--days", type=int, default=7, metavar="DAYS",
        help="a worktree is stale when its last commit is older than this many days (default 7)",
    )
    args = parser.parse_args(argv)

    today = date.today()
    rows: list[list[str]] = []
    swept = 0
    for name in args.repositories:
        repo = Path(name).expanduser().resolve()
        if not is_repository(repo):
            print(f"skip {repo}: not a git repository", file=sys.stderr)
            continue
        swept += 1
        for tree in worktrees(repo):
            rows.append(row(repo, tree, args.days, today))

    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(rows, today, swept))
    print(f"{len(rows)} worktrees of {swept} repositories written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
