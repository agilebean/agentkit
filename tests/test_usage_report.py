"""Tests of scripts/usage_report.py: the month's DeepSeek runs, the commits Claude co-authored, and the board's share.

The database is built in tmp_path, never opencode's own. A run counts one row whose parent is
null; cost counts every DeepSeek row of the window, child sessions included, since a child
session's cost is spent in the same folder.
"""
import importlib.util
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "usage_report.py"


def _load():
    spec = importlib.util.spec_from_file_location("usage_report", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ur = _load()


def _ms(text):
    """The wall time is KST: a naive timestamp() reads the host's zone, which is UTC on the runner."""
    return int(datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ur.KST).timestamp() * 1000)


def _commit(repo, message, when, coauthor=False):
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": when,
        "GIT_COMMITTER_DATE": when,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    body = message
    if coauthor:
        body += "\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "--allow-empty", "-m", body],
        check=True,
        env=env,
        capture_output=True,
    )


@pytest.fixture
def world(tmp_path):
    """A database of six rows across two months, and a socrates folder with two commits."""
    db = tmp_path / "opencode.db"
    con = sqlite3.connect(db)
    con.execute(
        "create table session_v2 (id text primary key, parent_id text, directory text,"
        " title text, model text, cost real, time_created integer)"
    )
    deepseek = '{"id":"deepseek-v4-flash","providerID":"opencode-go"}'
    claude = '{"id":"claude-opus-5-5","providerID":"anthropic"}'
    socrates = str(tmp_path / "socrates")
    rows = [
        ("ses_1", None, socrates, "Refactor the note builder", deepseek, 1.00, "2026-10-05 10:00:00"),
        ("ses_2", None, socrates, "Run the build test", deepseek, 0.50, "2026-10-06 10:00:00"),
        ("ses_3", None, socrates, "availability probe", deepseek, 0.25, "2026-10-07 10:00:00"),
        ("ses_4", None, socrates + "/.claude/worktrees/w1", "Note fix in the worktree", deepseek, 0.75, "2026-10-08 10:00:00"),
        ("ses_5", "ses_1", socrates, "Child session", deepseek, 2.00, "2026-10-09 10:00:00"),
        ("ses_6", None, socrates, "Claude session", claude, 3.00, "2026-11-05 10:00:00"),
    ]
    con.executemany(
        "insert into session_v2 values (?, ?, ?, ?, ?, ?, ?)",
        [(i, p, d, t, m, c, _ms(w)) for i, p, d, t, m, c, w in rows],
    )
    con.commit()
    con.close()

    repo = tmp_path / "socrates"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, capture_output=True)
    _commit(repo, "The first note", "2026-10-10T10:00:00+09:00")
    _commit(repo, "The second note", "2026-10-20T10:00:00+09:00", coauthor=True)

    plan = tmp_path / "plan.md"
    plan.write_text(
        "# Plan\n\n## Status board\n\n"
        "| ID | Task | Area | What it gives you | Runs on | Waits on | Status |\n"
        "|---|---|---|---|---|---|---|\n"
        "| DD-01 | a | b | c | any | none | done, 2026-11-01: ok |\n"
        "| DD-02 | a | b | c | DeepSeek | none | done, 2026-11-01: ok |\n"
        "| DD-03 | a | b | c | DeepSeek, read-only | none | open |\n"
    )
    return {"db": db, "repos": {"socrates": str(repo)}, "plan": plan}


def test_runs_count_four_in_october_with_the_child_cost(world):
    since, until = ur.month_window("2026-10")
    runs = ur.collect_runs(world["db"], since, until, world["repos"])
    assert list(runs) == ["socrates"]
    assert runs["socrates"]["work"] == 2
    assert runs["socrates"]["test"] == 1
    assert runs["socrates"]["probe"] == 1
    assert runs["socrates"]["cost"] == pytest.approx(4.50)


def test_commits_count_both_and_the_claude_one(world):
    since, until = ur.month_window("2026-10")
    commits = ur.collect_commits(world["repos"], since, until)
    assert commits["socrates"]["commits"] == 2
    assert commits["socrates"]["coauthored"] == 1


def test_board_counts_only_deepseek_rows(world):
    assert ur.collect_board(world["plan"]) == {"rows": 2, "done": 1}


def test_rendered_tables_hold_the_runbook_headers(world):
    since, until = ur.month_window("2026-10")
    runs = ur.collect_runs(world["db"], since, until, world["repos"])
    commits = ur.collect_commits(world["repos"], since, until)
    board = ur.collect_board(world["plan"])
    text = ur.render(ur.window_label(since, until, "2026-10"), runs, commits, board)
    assert "the month 2026-10" in text
    assert "| Repository | Work runs | Test runs | Probes | Cost USD |" in text
    assert "| Repository | Commits | Co-authored by Claude |" in text
    assert "| Board rows DeepSeek runs | Done | Share |" in text
    assert "| socrates | 2 | 1 | 1 | 4.50 |" in text
    assert "| socrates | 2 | 1 |" in text
    assert "| 2 | 1 | 50% |" in text


def test_help_names_the_arguments():
    out = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"], capture_output=True, text=True, check=True
    )
    for name in ("--month", "--since", "--until", "--db", "--plan", "--out"):
        assert name in out.stdout



def test_export_writes_the_windows_rows_to_a_dated_csv(tmp_path):
    db = tmp_path / "opencode.db"
    con = sqlite3.connect(db)
    con.execute(
        "create table session_v2 (id text, parent_id text, directory text, title text,"
        " model text, cost real, time_created integer)"
    )
    con.executemany(
        "insert into session_v2 values (?,?,?,?,?,?,?)",
        [
            ("a", None, "/w/socrates", "note work", "deepseek-v4.1-flash", 0.25, _ms("2026-11-02 09:00:00")),
            ("b", "a", "/w/socrates", "child", "deepseek-v4.1-flash", 0.05, _ms("2026-11-02 09:05:00")),
            ("c", None, "/w/swim", "outside", "deepseek-v4.1-flash", 0.10, _ms("2026-12-01 09:00:00")),
        ],
    )
    con.commit()
    con.close()

    since = datetime(2026, 11, 1, 0, 0, 0)
    until = datetime(2026, 12, 1, 0, 0, 0)
    target = tmp_path / "2026-11 sessions.csv"
    assert ur.export_sessions(db, since, until, target) == 2

    lines = target.read_text(encoding="utf-8").strip().split("\n")
    assert lines[0].startswith("time_created_kst,parent_id,directory,title,model,cost_usd")
    assert len(lines) == 3
    assert "2026-11-02 09:00:00" in lines[1] and "0.250000" in lines[1]
    assert "child" in lines[2] and "2026-12-01" not in target.read_text(encoding="utf-8")
