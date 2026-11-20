---
name: runbook
description: Run a test-first runbook that a frontier model wrote (claim the task on its board, run the acceptance tests in order, stop at a failed test) and end in the one report Chaehan reads, a first line with the outcome and its number, a table of changes with evidence and a table of open items, which scripts/report_check.py must pass. Use when a message names a runbook to run, says "run DD-<n>", or says "run the runbook".
---

# runbook

A runbook is a task written before the work by a frontier model (Claude Opus 5.5, Claude Fable 5.2 or newer):
what exists today, the acceptance tests in Given/When/Then form, when to stop, how to resume, the files you may
change and the path of the report. You run it as written. The tests decide whether the work is done, and the
report is the only text of your run that Chaehan reads; `report_check.py` refuses it unless it has the form
below. The model runbook is `docs/2026-11-18 vm migration us-south1.md` in agentkit.

## Steps

1. **Read the runbook whole**, then every file it names, before the first change. When the runbook leaves a
   step open (a value, a path, a choice), make no guess: write the report `stopped at <the test's id>: the
   runbook leaves <what> open` and end the run.
2. **Claim the task on its board.** The runbook names the plan file and the task's id. Set the task's Status
   cell to `in progress, <today as YYYY-MM-DD>, DeepSeek V4.1 Flash`, change no other line, and commit that
   file alone: `git add "<plan file>"` and `git commit -m "<id> claimed, <date>, DeepSeek V4.1 Flash"`. Push.
3. **Run the resume checks** when the runbook has them, and start at the first acceptance test whose row in the
   runbook's test log is not `pass`.
4. **Run the acceptance tests in order.** For each test: do the work its Given and When describe, then run its
   Then check exactly as written and read the output. Add a row to the runbook's test log: the test's id, the
   date, `pass` or `fail`, and the evidence, which is the command in backticks and the output line that decides
   it. A test passes only on the output of its own check, never on your reading of the code.
5. **Stop at a failed test.** Fix it and rerun its check while the number of failures falls. After two rounds
   in which the number does not fall, stop (RULES.md rule 74): start no later test, and write the report
   `stopped at <id>: <what the last check printed>`. Stop as well, before the change, when the next step would
   change a file the runbook does not list, delete or weaken a test, skip a test that needs neither private
   data nor a local port, or push with a failing test.
6. **Commit and push** as the runbook says: stage each file by its name (never `git add -A` or `git add .`),
   one commit per test or per group the runbook names, and push after each commit. When the push is refused,
   run `git pull --rebase` and push again. When the repository has a test workflow, read its result for your
   last commit with `gh run list --commit <sha> --json conclusion,databaseId` once the run has finished, and
   put it in the report as a row of the table of changes.
   Every wait (a workflow run, a deploy, a queue) happens in the foreground, in a shell call with a timeout
   long enough for it, such as `gh run watch <id> --exit-status --interval 20` with 900000 ms. Never hand a
   wait to a background job and end your turn: in `opencode run` your run ends with your turn and nothing
   wakes you again (2026-11-20, the first DD-02 run stopped at T5.1 this way).
7. **Write the report** to the path the runbook names, then run
   `python3 ~/Software/Prototypes/agentkit/scripts/report_check.py "<report path>"`. When it prints FAIL, fix
   each line it names and run it once more. Commit and push the report after the check prints PASS, or after the
   second check either way, and end the run with the check's last line as your last message.

Leave the board's later statuses, the plan's log and every file the runbook does not list to the frontier
session that reads your report.

## The report

The report holds three parts and nothing else: no heading, no paragraph, no list, no summary.

```
done: 7 of 7 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the colour test in `tests/test_en_to_hanji.py` | 1 failed | 0 failed | `pytest -q tests/test_en_to_hanji.py` printed `8 passed` |
| the workflow on main | none | success in 3 min | `gh run view 19876543210` reads `success` |

| Open item | Who decides | By when |
|---|---|---|
| a check for the personal terms through a secret | Chaehan | 2026-11-27 |
```

- **First line.** `done: <number> of <number> acceptance tests pass` when every test passed, or
  `stopped at <test id>: <what stopped it>`.
- **Table of changes.** One row per thing that changed: what it is, its value before, its value after, and
  the evidence, which always holds a command, a file or an output line in backticks. A stopped run with no
  change keeps the header and the separator row and no row.
- **Table of open items.** One row per question your run could not settle: what is open, who decides
  (Chaehan, or the frontier session for a question about the runbook), and a date YYYY-MM-DD. With no open
  item it keeps the header and the separator row.
- **Cells.** One clause per cell, at most 20 words, no semicolon, no second sentence, no line break. Every
  number has its unit: `1 failed`, `0 flags`, `551 passed`, never `1` or `0` alone. A path, a command and an
  output line go in backticks. No word of the robot markers list (`robot_markers.tsv`, RULES.md rule 2) and no
  dash as punctuation.

`report_check.py` names each problem by its line and rule: R1 text outside the three parts, R2 the first line,
R3 a table's header or its number of cells, R4 an empty cell or evidence without backticks, R5 a number without
its unit, R6 more than one clause, R7 a robot marker, R8 a By when without a date.
