# DD-08 uncommitted work and stale worktree sweep, run as a test-first delivery

Task DD-08 of the [DeepSeek delegation plan](<deepseek delegation plan.md>): one table of uncommitted files, unpushed commits and worktrees older than 7 days across Chaehan's repositories, made by a script that deletes nothing. Written 2026-11-21 by Claude Opus 5.5; DeepSeek V4.1 Flash runs it in opencode under the runbook skill (`skills/runbook/SKILL.md`).

Board: `docs/deepseek delegation plan.md`, task DD-08. Report: `docs/2026-11-21 dd-08 repository sweep report.md`. The sweep table itself names private branches and files, so it goes to socrates: `~/Software/Prototypes/socrates/docs/2026-11-21 repository sweep.md`.

State: not started.
Resume: run the *Resume checks* below and continue at the first test whose row in the *Test log* is not `pass`.

## Delivery rules

- You create `scripts/repo_sweep.py` and `tests/test_repo_sweep.py` in agentkit, the sweep table in socrates, this runbook's *State* line and *Test log*, the DD-08 row of the board (the claim only), and the report. Nothing else changes.
- The script runs only git commands that read: `worktree list --porcelain`, `status --porcelain`, `rev-list --count`, `log -1`, `rev-parse`, `for-each-ref`. It never runs `fetch`, `push`, `worktree remove`, `prune`, `branch -d`, `stash` or `checkout`.
- Python is `mamba run -n socrates python`; the tests run with `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q tests/test_repo_sweep.py`.
- Stage each file by its name, in agentkit and in socrates, and leave every other file that `git status --short` shows.

## What exists today (measured 2026-11-21)

| Item | Value |
|---|---|
| Repositories | `~/Software/Prototypes/` agentkit, email-digest, evernote-replacement, invoice-admin, local-chat, markitdown, socrates, swim; `~/Software/` machinelearningtools, virtualfriend |
| Worktrees | socrates: 6 (the main checkout and 5 under `.claude/worktrees/`); every other repository: 1 |
| A sweep script | none |

## Story 1: the script, test first

- [ ] T1.1 Given no `tests/test_repo_sweep.py`, when it is written first, then it builds in `tmp_path` a bare remote, a clone with one pushed commit, one unpushed commit, one uncommitted file and a second worktree on another branch whose last commit is dated 10 days back (`GIT_COMMITTER_DATE`), and asserts the rows below; `pytest -q tests/test_repo_sweep.py` fails before the script exists.
- [ ] T1.2 Given T1.1, when `scripts/repo_sweep.py` is written, then the tests pass, and `python3 scripts/repo_sweep.py --help` names its arguments: the repository folders, `--out <file>` and `--days 7`.

  One row per worktree, in this form, written as a Markdown table under one line that names the date and the number of repositories:

  ```
  | Repository | Worktree | Branch | Last commit | Age (days) | Uncommitted files | Unpushed commits | State |
  |---|---|---|---|---|---|---|---|
  | socrates | `.claude/worktrees/<name>` | `<branch>` | 2026-11-11 | 10 | 0 | 2 | stale, unpushed |
  ```

  State is the list of what holds, in this order: `uncommitted`, `unpushed`, `no upstream`, `stale` (last commit older than `--days`), or `clean` when none holds. A worktree path is relative to its repository; the main checkout is `.`.

## Story 2: the first sweep

- [ ] T2.1 Given T1.2, when the script runs over the ten repositories of the table above with `--out "$HOME/Software/Prototypes/socrates/docs/2026-11-21 repository sweep.md"`, then the file holds one row per line of `git -C <repo> worktree list` summed over the ten repositories, and every worktree under `socrates/.claude/worktrees/` has a row with its branch, age and state.
- [ ] T2.2 Given T2.1, when `git -C <repo> worktree list` and `git -C <repo> status --porcelain | wc -l` are run by hand for socrates, then they agree with its rows.

## Story 3: commits and the report

- [ ] T3.1 Given Stories 1 and 2, when agentkit commits the script and its test (`DD-08: repo_sweep.py, a read-only table of uncommitted work and stale worktrees`) and socrates commits the sweep table (`DD-08: the repository sweep of 2026-11-21`), each pushed, then agentkit's workflow run for its commit shows `success` (waited for in the foreground).
- [ ] T3.2 Given T3.1, when the report is written in the form of the runbook skill, then `python3 scripts/report_check.py "docs/2026-11-21 dd-08 repository sweep report.md"` prints `report_check: PASS`. The table of changes has a row for the script, one for the sweep with its counts (repositories, worktrees, stale, uncommitted, unpushed), and the open items name the weekly schedule, which only Chaehan can set up.

## When to stop

- A test that fails twice in a row without fewer failures.
- A step that would run a git command outside the list of the delivery rules, or change a file that the delivery rules do not list.

## Resume checks

| Check | Reads | Means |
|---|---|---|
| `ls scripts/repo_sweep.py tests/test_repo_sweep.py` | the files that exist | Story 1 begun |
| `ls "$HOME/Software/Prototypes/socrates/docs/2026-11-21 repository sweep.md"` | the file exists | T2.1 begun |
| `git log --oneline -3 --grep DD-08` | the script's commit | T3.1 begun |

## Test log

| ID | Date | Result | Evidence |
|---|---|---|---|
