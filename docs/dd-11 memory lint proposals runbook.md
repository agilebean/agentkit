# DD-11 memory lint backlog as proposed fixes, run as a test-first delivery

Task DD-11 of the [DeepSeek delegation plan](<deepseek delegation plan.md>): every line of socrates' memory that `memory_lint.py` flags gets a proposed fix in one table per file, and a script checks that no proposal changes a fact. Proposals only: nothing in `memory/` changes until Chaehan approves a file. Written 2026-11-21 by Claude Opus 5.5; DeepSeek V4.1 Flash runs it in opencode under the runbook skill (`skills/runbook/SKILL.md`).

Board: `docs/deepseek delegation plan.md`, task DD-11. Report: `docs/2026-11-21 dd-11 memory lint proposals report.md`. The proposals quote memory, so they go to socrates: `~/Software/Prototypes/socrates/docs/2026-11-21 memory lint proposals.md`.

State: not started.
Resume: run the *Resume checks* below and continue at the first test whose row in the *Test log* is not `pass`.

## Delivery rules

- You create `scripts/memory_fix_check.py` and `tests/test_memory_fix_check.py` in agentkit, the proposals file in socrates, this runbook's *State* line and *Test log*, the DD-11 row of the board (the claim only), and the report. You never write to `socrates/memory/`.
- Python is `mamba run -n socrates python`; the tests run with `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q tests/test_memory_fix_check.py`.
- The report names files and counts and never quotes a memory line, since agentkit is public.
- Stage each file by its name, in agentkit and in socrates, and leave every other file that `git status --short` shows.

## What exists today (measured 2026-11-21)

| Item | Value |
|---|---|
| The lint | `python3 scripts/memory_lint.py <file> ...` prints `<file>:<line>: <check> <message>`; its function `lint(text)` returns `(line, check, message)` |
| Flags | 329 hits on 313 lines in 20 files of `socrates/memory/`: M1 24 (relative time outside a quote), M2 198 (an old value beside its replacement), M3 21 (an inference stated as fact), M5 86 (a quote addressed to the agent) |
| Files | `agentic_ai.md` 194, `kubs.md` 54, `health.md` 10, `travel.md` 8, `swim.md` 7, `agentic_ai.index.md` 7, `spanish.md` 5, `dating.md` 5, `furniture-relocation.md` 4, `_psych_obs.md` 4, `polyboard.md` 3, `optimization_cost.md` 3, `improv.md` 3, `talks.md` 2, `psychological-insight-extraction.md` 2, `macbook.md` 2, `legal.md` 2, `_psych_obs.index.md` 2, `virtualfriend.md` 1, `virtualfriend-marketing.md` 1 |
| The failure register | `agentic_ai.md` records each failure with Chaehan's correction verbatim and the wrong value beside its fix (AGENTS.md core 0 and core 8), so its M2 and M5 lines and the M5 lines of `_psych_obs.md` are proposed as `keep` |

## The proposals file

One section per memory file, `## memory/<file>`, ordered by the table above read from the bottom up, so the small topic files come first and `agentic_ai.md` last. Each section is one table:

```
| Line | Check | Line now | Proposed line |
|---|---|---|---|
| 41 | M1 | ...the line as it stands, with every pipe written \| ... | ...the fix... |
```

- One row per flagged line; a line with two checks names both, `M1, M3`.
- `Line now` is the line exactly as the file holds it, with each `|` written `\|`.
- `Proposed line` is the line as it would stand after the fix, and for M2 the line in force followed by ` / History: ` and the old value as a dated line for a History section. A proposal is `keep: <reason>` only where the rule above says so.
- A fix states only what the line already holds. M1: the date replaces the relative phrase, taken from the line's own date or its section's date; when neither gives one, the phrase moves inside a quote with the date it was said, or the proposal is `keep: no date in the record`. M3: `the agent reads` marks the inference, or the inference is cut. M5: the fact or rule the quote states, with Chaehan's key words kept in quotes.

## Story 1: the checker, test first

- [ ] T1.1 Given no `tests/test_memory_fix_check.py`, when it is written first, then it builds in `tmp_path` a memory file with one line for each of M1, M2, M3 and M5 and one table row holding pipes, a proposals file that fixes them, and one broken proposals file per rule below, and asserts that the good file passes and each broken one is refused by its rule; `pytest -q tests/test_memory_fix_check.py` fails before the script exists.
- [ ] T1.2 Given T1.1, when `scripts/memory_fix_check.py PROPOSALS --root <socrates folder>` is written, then the tests pass. It refuses, naming the section and line:
  - C1 a flagged line of a section's file without a row, or a row for a line the lint does not flag
  - C2 a `Line now` that differs from the file's line
  - C3 a proposed line on which `memory_lint.lint` still finds a check (for M2, the part before ` / History: `)
  - C4 a proposed line, History part included, that drops a number, a date, a quoted text or a backtick span of the line now
  - C5 a `keep` outside the rule of *What exists today*, or without its reason

## Story 2: the proposals

- [ ] T2.1 Given T1.2, when the proposals file holds a section for each of the 20 files, then `python3 scripts/memory_fix_check.py "$HOME/Software/Prototypes/socrates/docs/2026-11-21 memory lint proposals.md" --root "$HOME/Software/Prototypes/socrates"` prints a pass for 313 rows, one per flagged line. Write the sections in the order of the file, and run the checker after each section; a section it refuses twice in a row without fewer refusals stops the run.
- [ ] T2.2 Given T2.1, when `git -C ~/Software/Prototypes/socrates log --oneline -5 -- memory/` and `git -C ~/Software/Prototypes/socrates status --short memory/` are read, then no commit or change of this run touches `memory/`.

## Story 3: commits and the report

- [ ] T3.1 Given Stories 1 and 2, when agentkit commits the checker and its test (`DD-11: memory_fix_check.py, a proposed memory fix keeps every fact`) and socrates commits the proposals (`DD-11: proposed fixes for the 313 lines memory_lint flags`), each pushed, then agentkit's workflow run for its commit shows `success` (waited for in the foreground).
- [ ] T3.2 Given T3.1, when the report is written in the form of the runbook skill, then `python3 scripts/report_check.py "docs/2026-11-21 dd-11 memory lint proposals report.md"` prints `report_check: PASS`. Its table of changes counts the rows per check and the `keep` rows; its open items name Chaehan's approval, one row per file with proposals.

## When to stop

- A test or section that fails twice in a row without fewer failures.
- A step that would write to `socrates/memory/`, or change a file that the delivery rules do not list.

## Resume checks

| Check | Reads | Means |
|---|---|---|
| `ls scripts/memory_fix_check.py tests/test_memory_fix_check.py` | the files that exist | Story 1 begun |
| `grep -c '^## memory/' "$HOME/Software/Prototypes/socrates/docs/2026-11-21 memory lint proposals.md"` | the sections written | Story 2 progress, out of 20 |
| `git log --oneline -3 --grep DD-11` | the checker's commit | T3.1 begun |

## Test log

| ID | Date | Result | Evidence |
|---|---|---|---|
