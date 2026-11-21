# DD-09 monthly usage report, run as a test-first delivery

Task DD-09 of the [DeepSeek delegation plan](<deepseek delegation plan.md>): one table a month of DeepSeek's runs and cost by repository and kind, the commits co-authored by Claude by repository, and the share of the board's tasks DeepSeek finished, made by a script that reads opencode's database without writing to it. Written 2026-11-21 by Claude Opus 5.5; DeepSeek V4.1 Flash runs it in opencode under the runbook skill (`skills/runbook/SKILL.md`).

Board: `docs/deepseek delegation plan.md`, task DD-09. Report: `docs/2026-11-21 dd-09 usage report report.md`. The month's table names Chaehan's costs and working folders, so it goes to socrates: `~/Software/Prototypes/socrates/docs/2026-11 deepseek usage.md`.

State: stopped at T2.1 on 2026-11-21. T1.1 and T1.2 pass (`scripts/usage_report.py` and its test are committed as `ca82a5d`). The database at the named path holds 400 sessions and none from 2026-11-12 to 2026-11-14, so the plan's window counts 225 socrates runs against the 542 measured when this runbook was written, and November counts 110 runs against 595.
Resume: run the *Resume checks* below and continue at the first test whose row in the *Test log* is not `pass`.

## Delivery rules

- You create `scripts/usage_report.py` and `tests/test_usage_report.py` in agentkit, the month's table in socrates, this runbook's *State* line and *Test log*, the DD-09 row of the board (the claim only), and the report. Nothing else changes.
- The database is opened read-only, always: `sqlite3.connect("file:" + path + "?mode=ro", uri=True)`. The script never writes to it, never copies it, and reads only the table `session_v2`.
- Git is read with `git -C <repo> log` only.
- Python is `mamba run -n socrates python`; the tests run with `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q tests/test_usage_report.py`.
- Stage each file by its name, in agentkit and in socrates, and leave every other file that `git status --short` shows.

## What exists today (measured 2026-11-21)

| Item | Value |
|---|---|
| Database | `~/.local/share/opencode/opencode.db`, 1.8 GB, table `session_v2`: `id`, `parent_id` (null for a top-level run), `directory`, `title`, `model` (JSON with `id`, `providerID`), `cost` (USD), `time_created` (ms since 1970, UTC) |
| A DeepSeek run | a top-level row (`parent_id is null`) whose `model` contains `deepseek` |
| Kind | `probe` when the title is `availability probe`; `test` when the title holds `test` in any case; `work` otherwise |
| Repository of a run | the repository whose folder is the longest prefix of `directory`, so a folder under `socrates/.claude/worktrees/` counts as socrates; `other` when no repository holds it |
| Repositories | `~/Software/Prototypes/` agentkit, email-digest, evernote-replacement, invoice-admin, local-chat, markitdown, socrates, swim; `~/Software/` machinelearningtools, virtualfriend |
| Month | a calendar month in Korean time (UTC+9); `--until` cuts it earlier |
| Commits co-authored by Claude | `git log -i --grep "Co-Authored-By: Claude"` in the window |
| The board's share | the rows of the status board in `docs/deepseek delegation plan.md` whose Runs on names DeepSeek, and among them those whose Status starts with `done` |
| The plan's window | 2026-10-01 00:00 to 2026-11-20 23:08:25 Korean time, when the plan was committed. Measured in it on 2026-11-21: 542 DeepSeek runs in socrates, 45 in the other repositories, $56.72 of DeepSeek cost in October; 47 commits in swim, 23 in email-digest, invoice-admin and local-chat together, 8 in virtualfriend. The plan's 602 runs, 127 probes and $8.17 for November came from a query that was not saved, and today's count of the same window gives 595, 128 and $7.77. |

## Story 1: the script, test first

- [ ] T1.1 Given no `tests/test_usage_report.py`, when it is written first, then it builds in `tmp_path` a database file with a `session_v2` table holding six rows (two months, a child row, a probe, a test, a non-DeepSeek model, a folder under `.claude/worktrees/`) and a git repository with two commits, one co-authored by Claude, and asserts the counts of each table; `pytest -q tests/test_usage_report.py` fails before the script exists.
- [ ] T1.2 Given T1.1, when `scripts/usage_report.py` is written, then the tests pass, and `python3 scripts/usage_report.py --help` names its arguments: `--month YYYY-MM`, `--since`, `--until`, `--db`, `--plan`, `--out`.

  Its output is three Markdown tables under one line that names the window:

  ```
  | Repository | Work runs | Test runs | Probes | Cost USD |
  | Repository | Commits | Co-authored by Claude |
  | Board rows DeepSeek runs | Done | Share |
  ```

## Story 2: the plan's window reproduced

- [ ] T2.1 Given T1.2, when the script runs with `--since 2026-10-01 --until "2026-11-20 23:08:25"`, then its tables show 542 runs in socrates, 45 runs summed over the other repositories, $56.72 of cost in October when run with `--month 2026-10`, and 47, 23 and 8 commits for swim, the three public repositories and virtualfriend. The report's open items name the plan's 602 runs, 127 probes and $8.17 against the script's numbers.

## Story 3: November

- [ ] T3.1 Given T2.1, when the script runs with `--month 2026-11 --out "$HOME/Software/Prototypes/socrates/docs/2026-11 deepseek usage.md"`, then the file holds the three tables, and its run count for socrates equals `sqlite3` run by hand on the same window.

## Story 4: commits and the report

- [ ] T4.1 Given Stories 1 to 3, when agentkit commits the script and its test (`DD-09: usage_report.py, the month's DeepSeek runs, commits and board share`) and socrates commits the month's table (`DD-09: DeepSeek usage of 2026-11`), each pushed, then agentkit's workflow run for its commit shows `success` (waited for in the foreground).
- [ ] T4.2 Given T4.1, when the report is written in the form of the runbook skill, then `python3 scripts/report_check.py "docs/2026-11-21 dd-09 usage report report.md"` prints `report_check: PASS`, and its open items name the monthly schedule, which only Chaehan can set up.

## When to stop

- A test that fails twice in a row without fewer failures.
- A step that would write to the database, read a table other than `session_v2`, or change a file that the delivery rules do not list.

## Resume checks

| Check | Reads | Means |
|---|---|---|
| `ls scripts/usage_report.py tests/test_usage_report.py` | the files that exist | Story 1 begun |
| `ls "$HOME/Software/Prototypes/socrates/docs/2026-11 deepseek usage.md"` | the file exists | T3.1 begun |
| `git log --oneline -3 --grep DD-09` | the script's commit | T4.1 begun |

## Test log

| ID | Date | Result | Evidence |
|---|---|---|---|
| T1.1 | 2026-11-21 | pass | `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q tests/test_usage_report.py` printed `5 passed in 0.55s` |
| T1.2 | 2026-11-21 | pass | `python3 scripts/usage_report.py --help` printed `--month`, `--since`, `--until`, `--db`, `--plan` and `--out` |
| T2.1 | 2026-11-21 | fail | `python3 scripts/usage_report.py --since 2026-10-01 --until "2026-11-20 23:08:25"` printed 225 runs for socrates, 37 for the others and `$56.72` was expected where `--month 2026-10` printed `| Total | 168 | 2 | 0 | 40.52 |` |
