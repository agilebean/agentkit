# DD-03 history purge, run as a test-first delivery

Task DD-03 of the [DeepSeek delegation plan](<deepseek delegation plan.md>), its history part: no commit of agentkit, old or new, holds the files moved to socrates on 2026-11-20 or a term of the private replacement list. Written 2026-11-21 by Claude Opus 5.5; DeepSeek V4.1 Flash runs it in opencode under the runbook skill (`skills/runbook/SKILL.md`).

Board: `docs/deepseek delegation plan.md`, task DD-19. Report: `docs/2026-11-21 dd-03 history purge report.md`.

State: stopped at T1.3 a second time on 2026-11-21, DeepSeek V4.1 Flash. The frontier session fixed the first five hits in commit `3687eef` (suite at 655 passed); the check now finds 5 hits in two transcript scripts and they wait for the same call. Chaehan gave the go on 2026-11-21 ("Yes, run it"), recorded in the DD-19 row of the board.
Resume: run the *Resume checks* below and continue at the first test whose row in the *Test log* is not `pass`.

## Delivery rules

- The replacement list is private and stays in socrates: `$HQ/history replacements.txt`, where `HQ="$HOME/Software/Prototypes/socrates/docs/human quality/data"`. Never copy it, quote it or name one of its terms in agentkit, in a commit message or in the report. The report counts hits; it never shows them.
- `AK="$HOME/Software/Prototypes/agentkit"` is the checkout other sessions share. In it you change only the files Story 1 names, this runbook's *State* line and *Test log*, the DD-19 row of the board (the claim only) and the report. Stage each file by its name.
- The rewrite of Story 2 happens in a fresh mirror clone under `$TMPDIR/dd03/`, never in `$AK`.
- A push that rewrites history uses `--force-with-lease` with the old SHA of each ref, as rule 193 allows. A bare `--force` is never used.
- Python is `mamba run -n socrates python`. The suite command is the one of DD-02: `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates env -u OPENCODE_SERVER_PASSWORD python -m pytest -q $(git ls-files 'tests/*test_*.py')`.
- Stop before a change that would touch a file this runbook does not list, and before any push while a local test fails.

## What exists today (measured 2026-11-21)

| Item | Value |
|---|---|
| Repository | `agilebean/agentkit`, public: an unauthenticated request for `raw.githubusercontent.com/agilebean/agentkit/main/AGENTS.md` answers 200 |
| Remote refs | `main` at `2d6b953` (579 commits) and the tags `v0.1.0`, `v0.2.0`, `v0.3.0`, `v0.3.1`, `v0.4.0`, `v0.4.1`; no other branch |
| Consumers | the workflows of socrates, email-digest and invoice-admin check agentkit out at `ref: v0.4.1` |
| An earlier rewrite | on 2026-11-21 at 01:09 the history was rewritten once with the token map of the socrates scrub record, and `$AK` was reset to it |
| Files still in the history | the 12 paths of Story 2, moved to socrates on 2026-11-20 |
| Terms still in the history | blobs and commit messages hold terms of the replacement list: in 5 to 14 commits per term, and in 11 commit messages |
| Terms in today's tree | 9 rules of the list hit 21 committed files: `.md` files, tests, `.tsv` data of skills and `.py` scripts |
| Tool | `git filter-repo` is not installed |
| The checker | `scripts/history_check.py` does not exist |

## Story 1: the current tree holds no term of the list

T1.1 Given `$AK` on `main`, when you write `scripts/history_check.py`, then it runs as below and its own test passes.

- `python3 scripts/history_check.py --rules "<file>" --tree <dir>` counts, for each rule of the file, its hits in every committed file of the folder. With `--repo <git dir>` it counts them in every blob of every commit and in every commit message. A rule is `literal==>replacement` or `regex:<python regex>==>replacement`; lines starting with `#` are comments.
- It prints one line per rule with hits, as `rule <line number>: <count> hits in <files or blobs>`, never the term, and a last line `history_check: <total> hits`. It exits 1 when the total is above 0.
- `tests/test_history_check.py` builds a two-commit repository in `tmp_path` with invented terms and checks the counts, the exit code and that no term is printed.
- Then: `mamba run -n socrates python -m pytest -q tests/test_history_check.py` prints `passed` with no failure.

T1.2 Given the list, when you run `python3 scripts/history_check.py --rules "$HQ/history replacements.txt" --tree "$AK"`, then the printout names the files with hits. Write their names and counts into the *Test log*. This is the baseline; it is expected to fail.

T1.3 Given the files of T1.2, when a hit sits in a `.py` file outside `tests/` or in a `.tsv` file under `skills/`, then stop: write the report `stopped at T1.3: <n> hits in scripts or skill data` and list each file and rule number in the table of open items. A name there may be read at run time, and changing it is the frontier session's call.

T1.4 Given T1.3 found no such hit, when you apply every rule of the list to the `.md` files and the files under `tests/` that T1.2 named (the replacement of each rule, in the list's order, with Python `re.sub` for regex rules and `str.replace` for literal ones), then `history_check.py --tree "$AK"` prints `history_check: 0 hits`, and the suite passes with the same number of passed tests as before the change.

T1.5 Commit the changed files by name with the message `DD-03 S1: today's tree holds no term of the private list` and push to `main`. Then `gh run list --commit <sha> --json conclusion` reads `success`, watched in the foreground as the runbook skill says.

## Story 2: the rewrite, in a fresh mirror clone

T2.1 Given no session has unpushed work, when you run `git -C "$AK" log origin/main..main --oneline`, then it prints nothing. Record `OLD_MAIN=$(git ls-remote https://github.com/agilebean/agentkit.git refs/heads/main | cut -f1)` and each tag's SHA from `git ls-remote --tags` in the *Test log*.

T2.2 Given `~/Software/archive/` exists, when you run `git clone --mirror https://github.com/agilebean/agentkit.git "$HOME/Software/archive/agentkit-mirror-2026-11-21.git"`, then `git -C <that mirror> rev-parse main` equals `OLD_MAIN`. The backup holds the old history and never leaves this machine.

T2.3 Given `mamba run -n socrates pip install git-filter-repo` has run, when `mamba run -n socrates git filter-repo --version` runs, then it prints a version. Write it in the *Test log*.

T2.4 Given a fresh `git clone --mirror https://github.com/agilebean/agentkit.git "$TMPDIR/dd03/agentkit.git"` and the file `$TMPDIR/dd03/paths.txt` holding these 12 lines, one path a line:

```
docs/2026-11-05 agent writing summary.md
docs/2026-11-15 note wording analysis.md
docs/2026-11-15 wording test/
docs/2026-11-16 wording build/
docs/2026-11-17 note wording analysis.md
docs/2026-11-17 note wording build spec.md
docs/2026-11-17 wording build/
docs/answer_quality_prompt.md
docs/answer_quality_report.md
docs/answer_quality_test_packet.md
wording_cases.tsv
wording_pairs.tsv
```

when you run, inside `$TMPDIR/dd03/agentkit.git`, `mamba run -n socrates git filter-repo --invert-paths --paths-from-file "$TMPDIR/dd03/paths.txt" --replace-text "$HQ/history replacements.txt" --replace-message "$HQ/history replacements.txt"`, then it ends without an error.

T2.5 Then, in the rewritten mirror: for each of the 12 paths, `git log --all --oneline -- "<path>"` prints nothing, and `python3 "$AK/scripts/history_check.py" --rules "$HQ/history replacements.txt" --repo "$TMPDIR/dd03/agentkit.git"` prints `history_check: 0 hits`.

T2.6 Then `git -C "$TMPDIR/dd03/agentkit.git" rev-parse 'main^{tree}'` equals `git -C "$HOME/Software/Prototypes/agentkit" rev-parse 'origin/main^{tree}'`, so the newest files are unchanged, and the six tag names exist. Write the commit counts before and after in the *Test log*.

## Story 3: the push

T3.1 Given T2.6 passed, when you add the remote with `git -C "$TMPDIR/dd03/agentkit.git" remote add origin https://github.com/agilebean/agentkit.git` and push `main` with `--force-with-lease=refs/heads/main:$OLD_MAIN`, then each tag with `--force-with-lease=refs/tags/<tag>:<its old SHA>`, then `git ls-remote origin` shows for `main` and each tag the SHA of the rewritten mirror.

When a lease is refused because `main` moved, stop pushing: write the refusal in the *Test log* and resume at T2.1 with a new fresh clone.

T3.2 Then the tests workflow on the new `main` reads `success`, watched in the foreground.

## Story 4: the shared checkout follows without losing anyone's edits

T4.1 Given `git -C "$AK" status --short > "$TMPDIR/dd03/status.before"`, when you run `git -C "$AK" fetch origin --tags --force` and then `git -C "$AK" reset --mixed origin/main`, then `git -C "$AK" status --short` equals `status.before` line for line, and `git -C "$AK" rev-parse HEAD` equals the new `main`.

T4.2 Then `git -C "$AK" log --oneline -- "docs/2026-11-17 wording build/"` prints nothing.

## Story 5: what stays outside your reach, and the report

T5.1 Given the old `main` SHA, when you run `curl -s -o /dev/null -w '%{http_code}' https://github.com/agilebean/agentkit/commit/$OLD_MAIN`, then write the code in the *Test log*. A 200 means GitHub still serves the old commit by its SHA until it collects it; that goes into the table of open items for Chaehan (GitHub Support can purge cached views, and making the repository private closes them at once).

T5.2 Write the report in the form of the runbook skill. The table of changes holds the commit counts before and after, the hits before and after (counts only), the SHAs of `main` before and after, the workflow results, the backup path and the shared checkout's status. The table of open items holds T5.1's result and any file T1.3 stopped at. Then `python3 scripts/report_check.py "docs/2026-11-21 dd-03 history purge report.md"` prints `report_check: PASS`.

## When to stop

- At a test whose check fails twice without the number of failures falling (rule 74).
- At T1.3 when a script or a skill's data file holds a hit.
- When a lease is refused: go back to T2.1, never to `--force`.
- When `status.before` and the status after T4.1 differ: run `git -C "$AK" reset --mixed <the old HEAD from the reflog>` at once, then stop and report.

## Resume checks

- `git -C "$AK" log --oneline -1` and `git ls-remote origin refs/heads/main`: when they differ, finish T4.1 before anything else.
- `ls "$HOME/Software/archive/agentkit-mirror-2026-11-21.git"` exists before any push.
- The *Test log* names the last test that passed; continue at the next one.

## Test log

| Test | Date | Result | Evidence |
|---|---|---|---|
| T1.1 | 2026-11-21 | pass | `mamba run -n socrates python -m pytest -q tests/test_history_check.py` printed `5 passed` |
| T1.2 | 2026-11-21 | fail | `python3 scripts/history_check.py --rules "$HQ/history replacements.txt" --tree "$PWD"` printed `history_check: 90 hits`; RULES.md 12, commands/date.md 2, common_sense.md 14, scripts/instruction_lint.py 1, scripts/memory_lint.py 1, skills/date-analysis/SKILL.md 5, skills/date-analysis/date_markers.tsv 2, skills/date-analysis/scripts/md_turns.py 1, skills/date-analysis/scripts/mw_transcript.py 4, skills/date-analysis/traits.md 2, skills/evernote/SKILL.md 1, skills/life-overview/SKILL.md 1, skills/life-overview/scripts/overview_gate.py 1, tests/test_cards.py 5, tests/test_date_analysis.py 16, tests/test_note_build.py 3, tests/test_overview_gate.py 15, tests/test_wording_lint.py 4 |
| T1.3 | 2026-11-21 | fail | 5 hits in scripts or skill data: `scripts/instruction_lint.py` rule 26, `scripts/memory_lint.py` rule 26, `skills/life-overview/scripts/overview_gate.py` rule 26, `skills/date-analysis/date_markers.tsv` rules 21 and 22 |
| T1.3 | 2026-11-21 | fail | rerun after `3687eef`: 5 hits in scripts or skill data, `skills/date-analysis/scripts/md_turns.py` rule 22, `skills/date-analysis/scripts/mw_transcript.py` rules 21 and 22 |
