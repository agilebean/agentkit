#!/usr/bin/env python3
"""One month of DeepSeek's runs and cost by repository and kind, the commits Claude co-authored, and the share of the board it finished.

The database is opened read-only and only the table session_v2 is read, never written and never
copied. A run is a top-level row (parent_id null) whose model names DeepSeek; its kind is a probe
when the title is "availability probe", a test when the title holds "test" in any case, and work
otherwise. A repository is the one whose folder is the longest prefix of the run's directory, and
`other` when none holds it. Cost sums every DeepSeek row of the window, a child session's included,
since the child's cost is spent in the same folder. Git is read with `git -C <repo> log` only.
"""
import argparse
import os
import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = Path.home() / ".local/share/opencode/opencode.db"
DEFAULT_PLAN = ROOT / "docs" / "deepseek delegation plan.md"
PROTOTYPES = Path.home() / "Software" / "Prototypes"
SOFTWARE = Path.home() / "Software"

REPOSITORIES = {
    "agentkit": PROTOTYPES / "agentkit",
    "email-digest": PROTOTYPES / "email-digest",
    "evernote-replacement": PROTOTYPES / "evernote-replacement",
    "invoice-admin": PROTOTYPES / "invoice-admin",
    "local-chat": PROTOTYPES / "local-chat",
    "markitdown": PROTOTYPES / "markitdown",
    "socrates": PROTOTYPES / "socrates",
    "swim": PROTOTYPES / "swim",
    "machinelearningtools": SOFTWARE / "machinelearningtools",
    "virtualfriend": SOFTWARE / "virtualfriend",
}
KINDS = ("work", "test", "probe")


def parse_when(text):
    """A moment in Korean time, from YYYY-MM-DD, YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS."""
    for form in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), form)
        except ValueError:
            pass
    raise SystemExit(f"a time takes YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, not {text!r}")


def month_window(month):
    """A calendar month in Korean time: its first moment and the first moment after it."""
    year, number = (int(part) for part in month.split("-"))
    if not 1 <= number <= 12:
        raise SystemExit(f"a month takes YYYY-MM, not {month!r}")
    start = datetime(year, number, 1)
    end = datetime(year + (number == 12), 1 if number == 12 else number + 1, 1)
    return start, end


def to_ms(moment):
    return int(moment.replace(tzinfo=KST).timestamp() * 1000)


def as_iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%S") + "+09:00"


def repository_of(directory, repositories):
    best = None
    for name, path in repositories.items():
        folder = str(path)
        if directory == folder or directory.startswith(folder + os.sep):
            if best is None or len(folder) > len(str(repositories[best])):
                best = name
    return best or "other"


def kind_of(title):
    title = title or ""
    if title == "availability probe":
        return "probe"
    if "test" in title.lower():
        return "test"
    return "work"


def collect_runs(db_path, since, until, repositories=REPOSITORIES):
    con = sqlite3.connect("file:" + str(Path(db_path).expanduser()) + "?mode=ro", uri=True)
    try:
        rows = con.execute(
            "select parent_id, directory, title, model, cost from session_v2"
            " where time_created >= ? and time_created < ?",
            (to_ms(since), to_ms(until)),
        ).fetchall()
    finally:
        con.close()
    runs = {}
    for parent, directory, title, model, cost in rows:
        if "deepseek" not in (model or "").lower():
            continue
        stats = runs.setdefault(
            repository_of(directory, repositories), {kind: 0 for kind in KINDS} | {"cost": 0.0}
        )
        stats["cost"] += cost or 0.0
        if not parent:
            stats[kind_of(title)] += 1
    return runs


def _git_count(path, since, until, extra=()):
    done = subprocess.run(
        ["git", "-C", str(path), "log", *extra, "--since=" + as_iso(since),
         "--until=" + as_iso(until), "--format=%H"],
        capture_output=True, text=True,
    )
    if done.returncode != 0:
        return 0
    return len(done.stdout.split())


def collect_commits(repositories, since, until):
    return {
        name: {
            "commits": _git_count(path, since, until),
            "coauthored": _git_count(path, since, until, ("-i", "--grep", "Co-Authored-By: Claude")),
        }
        for name, path in repositories.items()
    }


def collect_board(plan_path):
    rows = done = 0
    in_board = False
    for line in Path(plan_path).expanduser().read_text().splitlines():
        if line.startswith("|") and "Runs on" in line and "Status" in line:
            in_board = True
            continue
        if not in_board:
            continue
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7 or all(set(cell) <= set("-: ") for cell in cells):
            continue
        if "deepseek" in cells[4].lower():
            rows += 1
            if cells[6].lower().startswith("done"):
                done += 1
    return {"rows": rows, "done": done}


def window_label(since, until, month=None):
    if month:
        return f"DeepSeek usage, the month {month}, Korean time (UTC+9)"
    return (
        f"DeepSeek usage, {since:%Y-%m-%d %H:%M} to {until:%Y-%m-%d %H:%M}, "
        "Korean time (UTC+9)"
    )


def render(label, runs, commits, board):
    lines = [label, ""]

    lines += ["| Repository | Work runs | Test runs | Probes | Cost USD |", "|---|---|---|---|---|"]
    total = {kind: 0 for kind in KINDS} | {"cost": 0.0}
    for name in sorted(runs, key=lambda n: (-sum(runs[n][kind] for kind in KINDS), n)):
        stats = runs[name]
        lines.append(
            f"| {name} | {stats['work']} | {stats['test']} | {stats['probe']} | {stats['cost']:.2f} |"
        )
        for kind in KINDS:
            total[kind] += stats[kind]
        total["cost"] += stats["cost"]
    lines.append(
        f"| Total | {total['work']} | {total['test']} | {total['probe']} | {total['cost']:.2f} |"
    )

    lines += ["", "| Repository | Commits | Co-authored by Claude |", "|---|---|---|"]
    totals = [0, 0]
    for name in sorted(commits, key=lambda n: (-commits[n]["commits"], n)):
        if not commits[name]["commits"]:
            continue
        lines.append(f"| {name} | {commits[name]['commits']} | {commits[name]['coauthored']} |")
        totals[0] += commits[name]["commits"]
        totals[1] += commits[name]["coauthored"]
    lines.append(f"| Total | {totals[0]} | {totals[1]} |")

    share = f"{100 * board['done'] / board['rows']:.0f}%" if board["rows"] else "0%"
    lines += [
        "",
        "| Board rows DeepSeek runs | Done | Share |",
        "|---|---|---|",
        f"| {board['rows']} | {board['done']} | {share} |",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="One month of DeepSeek's runs and cost, the commits Claude co-authored,"
        " and the share of the board's tasks DeepSeek finished. Reads opencode's database"
        " read-only, and only the table session_v2."
    )
    parser.add_argument("--month", help="a calendar month in Korean time, YYYY-MM")
    parser.add_argument("--since", help="the window's first moment, YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, Korean time")
    parser.add_argument("--until", help="the window's end, same form, exclusive")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"opencode's database (default {DEFAULT_DB})")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN, help="the plan whose board holds the tasks")
    parser.add_argument("--out", type=Path, help="write the tables here instead of printing them")
    args = parser.parse_args(argv)

    if not args.month and not args.since:
        parser.error("one of --month or --since is required")
    month = args.month
    since = parse_when(args.since) if args.since else month_window(month)[0]
    if args.until:
        until = parse_when(args.until)
    elif month:
        until = month_window(month)[1]
    else:
        until = datetime.now(KST).replace(tzinfo=None)
    if until <= since:
        parser.error("--until must come after --since")

    label = window_label(since, until, month if (month and not args.since and not args.until) else None)
    text = render(
        label,
        collect_runs(args.db, since, until),
        collect_commits(REPOSITORIES, since, until),
        collect_board(args.plan),
    )
    if args.out:
        Path(args.out).expanduser().write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
