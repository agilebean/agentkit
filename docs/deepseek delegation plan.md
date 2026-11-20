# DeepSeek delegation plan

**Plan, not implemented yet.** This file plans which of your work goes to DeepSeek V4.1 Flash, and it tracks that work: the status board holds each task's state, and the log at its foot holds the dated reason for each change. Sessions take tasks as the section "How a session takes a task" of the [human quality plan](<human quality plan.md>) says: a frontier model (Claude Opus 5.5, Claude Fable 5.2 or a newer one) writes the runbook, and DeepSeek runs it. agentkit is public, so nothing personal goes into this file, and the data a task reads from your notes, mail or memory stays in socrates.

## Summary

- DeepSeek spends its time where it is weakest: of its 602 runs since 2026-10-01, 542 were in socrates, mostly notes and their test runs, and 45 were in your code repositories, where a test can check its work.
- It does what its checks reward (2026-11-05) and filled 26 cards from your records without inventing a consequence (2026-11-16); asked to skip facts that change nothing for you, it skipped none, so choosing what matters stays with a script, a frontier model or you.
- The VM move to a cheaper zone saved $313 a year, and every step except the two DNS records you own was agent work written as tests before the work, the form DeepSeek runs well.
- If DeepSeek fails the gates of the first two runbooks more than once each, the runbooks are too loose, and the frontier model writes the next ones in smaller steps before more work moves.
- So 16 tasks below take that form, and the first one fixes how all of them reach you: a report of tables and numbers that a script checks, so DeepSeek's prose never lands in front of you unchecked.

## Where your work goes, and what DeepSeek does there

| Area | Your activity, 60 days to 2026-11-20 | DeepSeek runs since 2026-10-01 | What DeepSeek can take |
|---|---|---|---|
| Notes and research in socrates | 660 commits | 542, among them 127 availability probes of the note harness since 2026-10-15 | fact-finding with sources, as cards or tables; the measure runs of the human quality plan |
| agentkit: rules, skills, scripts | 443 commits, 114 co-authored by Claude Opus | 8 | tests on every push, the privacy sweep, index and link checks |
| virtualfriend in production | 8 commits: the VM move, the log rotation | 2 | the bill audit, the nightly log digest, the key replacement |
| Your course at KUBS (Korea University Business School) | 245 socrates commits for the fall course | many of the socrates runs: grading tables, decks, run sheets | sources, readings and deck skeletons for the spring 2027 course; never a grade |
| swim dashboard | 47 commits | 24, the most outside socrates | already its work; it stays there |
| email-digest, invoice-admin, local-chat (public) | 23 commits | 11 | dependency and security upkeep; receipts into a cost register |
| Memory files | ~300 lines flagged by `memory_lint.py`, 193 of them in `agentic_ai.md` | none | fixes proposed file by file |

DeepSeek's recorded cost was $56.72 in October and $8.17 in November to the 20th, with most runs on the OpenCode Go subscription, so a further task costs nothing until the weekly quota runs out, as it did on 2026-11-06 (failure 165).

## What DeepSeek takes, and what stays with you and Claude

DeepSeek takes a task when all five of these hold.

1. A script or a test says whether the task is done.
2. The steps can be written before the work, as the tests of the VM move were.
3. Every change can be undone, or waits behind a gate.
4. What reaches you is a table, a number or a diff.
5. Nothing goes out in your name, no money moves, and no grade is set.

Choosing what matters to you, what facts mean for your decisions, your voice, grades, messages to other people, payments, and the runbooks and gold lists themselves stay with you and a frontier model.

## How a task goes to DeepSeek

1. A frontier session writes the runbook in the repository the task changes: the list of what exists today, the acceptance tests in Given/When/Then form, when to stop, how to resume, and the report form. The VM move runbook of 2026-11-18 is the model.
2. DeepSeek runs it in opencode, outside Claude Code's sandbox, with a time box: two rounds without a falling count stop the run (rule 74).
3. The gates decide: the tests, the wording lint and the report check of DD-01. A failed gate goes back to DeepSeek once with its reasons, then to the frontier session.
4. You read the report and answer its open items; the frontier session reads only the failed gates.

## The report you get

Every DeepSeek run ends in this form, and nothing else from it reaches you (DD-01):

- First line: the outcome as a state and a number, such as "done: 14 of 14 tests pass" or "stopped at T3: no Spot capacity in the zone".
- A table of changes: what changed, its value before, its value after, and the evidence (a command, a file or an output line).
- A table of open items: what is open, who decides, by when.
- Text only inside cells, one clause each, with no flag of `wording_lint.py --strict`.

`report_check.py` refuses a report with text outside those three parts, an empty evidence cell, a number without its unit, or a lint flag. A note for you still goes through the card path of the human quality plan.

## Status board

This table is where progress is tracked: a session sets a task's status here before it starts, and every change of status gets an entry in the log at the foot of this file. Tasks are numbered DD, for DeepSeek delegation, in the order to take them. Your decisions E1 to E6 follow the board.

| ID | Task | Area | What it gives you | Runs on | Waits on | Status |
|---|---|---|---|---|---|---|
| DD-01 | The report form and its check | all | every later task reaches you as a table you can trust | frontier designs, any model builds | E1 for the rule line | in progress, 2026-11-20, Claude Opus 5.5 |
| DD-02 | agentkit tests on every push, and the red test fixed | agentkit | a broken commit shows within minutes | DeepSeek | none | in progress, 2026-11-20, DeepSeek V4.1 Flash |
| DD-03 | Personal data out of agentkit | agentkit | what the move of 2026-11-20 left public is gone | DeepSeek | E2 for skills, rules and history | ready for tests and scripts |
| DD-04 | Google Cloud bill audit each month | virtualfriend | the next saving after the VM move | DeepSeek, read-only | your yes per change | ready |
| DD-05 | Nightly log digest | virtualfriend | errors and response times on one page a day | DeepSeek | none | ready |
| DD-06 | The service-account key replaced by the VM's own identity | virtualfriend | the key file the VM runbook flagged is gone | DeepSeek | E3 | blocked: E3 |
| DD-07 | Dependency and security upkeep of the public repositories | four public repositories | known advisories closed with tests green | DeepSeek | none | ready |
| DD-08 | Uncommitted work and stale worktree sweep | all | no lost edits, no forgotten branches | DeepSeek reports, deletes nothing | none | ready |
| DD-09 | Monthly usage report | all | whether work moves the way this plan wants | DeepSeek | none | ready |
| DD-10 | Docs: one naming rule, the right repository, an index | all | agents find any document through its index | DeepSeek | E5 | blocked: E5 |
| DD-11 | Memory lint backlog as proposed fixes | socrates memory | the lines notes are built from in a form a model reads right | DeepSeek proposes | your yes per file | ready |
| DD-12 | Recurring-cost register | money | every subscription with its renewal date and last use | DeepSeek, data in socrates | E4 | blocked: E4 |
| DD-13 | Evernote to Hanji copy in batches | notes | the move to Hanji finished and checked word for word | DeepSeek | the notebooks you name | ready to count |
| DD-14 | Spring 2027 course preparation | course | checked sources and deck skeletons per session | frontier plans, DeepSeek builds | E6 | blocked: E6 |
| DD-15 | The human quality plan's measure runs | notes | the decision test run on every build | DeepSeek | HQ-01 | blocked: HQ-01 |
| DD-16 | Stock scores refreshed each week | money | the score table without a Claude session | DeepSeek, data in socrates | none | ready |

Statuses are ready, blocked (by a task or a decision), in progress (date and model), done (date and result), proposed and dropped.

## Decisions only you can make

The session that reaches a decision asks it with the question tool, quoting this section.

- E1, for DD-01. One line in the core of `AGENTS.md`: a run made from a runbook reports in the form above and passes `report_check.py`. It binds every opencode session, DeepSeek's included.
- E2, for DD-03. Whether the examples in the skills and RULES.md that come from your life are rewritten with invented ones, which changes text DeepSeek reads and is measured like any prompt change, and whether agentkit's history is rewritten with a force push or the repository is made private. Without the second, every line moved out on 2026-11-20 stays readable in the history.
- E3, for DD-06. Whether virtualfriend stops using a key file and calls Google services as the VM's own service account, a change to production that the runbook tests on the live endpoints.
- E4, for DD-12. Which mailbox and folders hold your receipts. The register reads vendors, amounts and dates, never card numbers, and every cancellation stays your act.
- E5, for DD-10. The four rules of the docs section below.
- E6, for DD-14. Your session plan for the spring course, since the course design is yours.

## Tasks

Each task names its goal, why it stands where it does, its steps and the result that accepts it. The frontier session that takes one writes its runbook first.

### DD-01 The report form and its check

Goal: every DeepSeek run reports in the form of "The report you get", and a script checks it.

Steps:

1. A skill, `agentkit/skills/runbook/SKILL.md`, that DeepSeek loads to run a runbook: read it whole, claim the task on its board, run the acceptance tests in order, stop at a failed test, write the report.
2. `agentkit/scripts/report_check.py`, with tests on three good and three bad reports.
3. On E1, the line in the core of `AGENTS.md`.

Acceptance: `report_check.py` passes DeepSeek's report of DD-02 within two tries and refuses the three bad reports.

### DD-02 agentkit tests on every push, and the red test fixed

Goal: every push to agentkit runs its test suite on GitHub's runners.

Why here: 443 commits in 60 days came from many sessions, agentkit has no automated test run, and on 2026-11-20 one test failed unseen, in `tests/test_en_to_hanji.py`, whose converter changed on 2026-11-16 (failure 214).

Steps:

1. Bring the test in line with the 2026-11-16 behaviour, under which colour is dropped and counted.
2. `.github/workflows/tests.yml`: the Python of the socrates environment, the install, `pytest -q`. Tests that need private data already skip without it; tests that need a local port get a marker.
3. The run's result enters each session's report.

Acceptance: the workflow passes on main, and a commit that breaks a test fails it.

### DD-03 Personal data out of agentkit

Goal: no line of agentkit names your health, money, people or dates.

Why here: on 2026-11-20 the test data and analyses moved to socrates, and 170 or more lines still matched a short list of personal terms: 85 in tests, ~40 in skills and their scripts, 25 in RULES.md and 22 in `common_sense.md`, plus the medicine name in `wording_fill_prompt.md`.

Steps:

1. Tests and scripts: each personal fixture becomes an invented one of the same shape, and the suite stays green.
2. On E2: the examples in skills and rules, each prompt change measured with `wording_eval.py` and the acceptance set of the card path; then the history, as E2 decides.
3. The list of terms stays in socrates; a check in DD-02's workflow searches agentkit for them through a secret, so the list is never public.

Acceptance: the search finds nothing in agentkit's tree, and the suite passes.

### DD-04 Google Cloud bill audit each month

Goal: each month a table of virtualfriend's Google Cloud costs by service, with a runbook for each saving worth doing.

Why here: the VM move saved $313 a year, and releasing an unused address $88 a year; the rest of the bill has not been read line by line, and test T8.2 of the VM runbook waits for the first bill after the move.

Steps:

1. Read-only: the last 30 days by service and by resource, and the idle resources: disks, addresses, snapshots, functions, buckets, log volume.
2. For each saving above the threshold you set, a test-first runbook in the VM move's form, run after your yes.
3. Close T8.2 when the bill shows compute at ~$15 to $18 a month.

Acceptance: the first report's rows sum to the bill within 1%.

### DD-05 Nightly log digest

Goal: one page a day in `logs/summary/` on the VM: error count, sessions, the response times of speech and model calls, banned addresses.

Why here: the VM move runbook proposed it and it is not built, so reading a month of logs means opening files of ~24 MB.

Steps: a script run by cron on the VM, its output a table, tested on one day of real logs before it is scheduled.

Acceptance: seven days of pages whose error counts match a direct count on the same logs.

### DD-06 The service-account key replaced by the VM's own identity

Goal: no key file on the VM or in the repository; the app calls Google services as the VM's attached service account.

Why here: the VM move runbook names the key in `src/config/` as the real exposure of the server.

Steps, after E3: find every reader of the key file, switch each one to the attached identity, test the features that call Google services, then delete the key in Google Cloud.

Acceptance: both health endpoints answer 200, the features that call Google services pass their checks, and the key no longer exists in Google Cloud.

### DD-07 Dependency and security upkeep of the public repositories

Goal: each month, agentkit, email-digest, invoice-admin and local-chat upgrade every dependency an advisory names, with their tests green.

Steps: an audit per repository (`pip-audit`, or `npm audit` where it applies), the upgrade, the tests, the commit, and a table of advisories closed and left open.

Acceptance: no advisory with a released fix is left open without its reason in the table.

### DD-08 Uncommitted work and stale worktree sweep

Goal: each week, a table of uncommitted files, unpushed commits and worktrees older than 7 days across your repositories. It deletes nothing.

Why here: on 2026-11-20 four sessions held uncommitted edits in agentkit and socrates at once, and failure number 227 was taken twice that day.

Acceptance: the first table lists every worktree under `socrates/.claude/worktrees/` with its branch, age and state.

### DD-09 Monthly usage report

Goal: one table a month: DeepSeek runs and cost by repository and kind (work, test, probe), commits co-authored by Claude by repository, and the share of this board's tasks DeepSeek finished.

Why here: it shows whether work moves the way this plan wants. The counts in this file came from that query, run read-only on opencode's database on 2026-11-20.

Acceptance: the report for November reproduces this file's counts.

### DD-10 Docs: one naming rule, the right repository, an index

Goal: the four rules of the section below hold in every docs folder, and every move or rename leaves no broken pointer.

Steps, after E5: build `agentkit/tools/docs_index.py`, then move and rename by the table below and sweep every pointer in every repository (rule 71). Write each `index.md` and add the line to `AGENTS.md`.

Acceptance: a link check over every repository finds no pointer to an old name, and each docs folder's `index.md` lists every file in it.

### DD-11 Memory lint backlog as proposed fixes

Goal: the ~300 lines that `memory_lint.py` flags become proposed fixes, one table per file, applied on your yes.

Why here: the lint guards the lines notes are built from; an old value beside its replacement (check M2) alone flags 100 lines in `agentic_ai.md`.

Steps: per file, a table of line, check, the line now and the proposed line; no fix changes a fact.

Acceptance: per approved file, `memory_lint.py` reports 0 flags and the diff touches only flagged lines.

### DD-12 Recurring-cost register

Goal: a table in socrates of every subscription and recurring charge: vendor, amount, cycle, next renewal, last use, the receipt it came from.

Why here: the VM move found $401 a year in one bill, and no memory file lists your other recurring costs.

Steps, after E4: read the receipts with the gmail and invoice tools, one row per vendor with its source message, then you mark each row keep or cancel.

Acceptance: every row has a source message, and a run a month later adds only new charges.

### DD-13 Evernote to Hanji copy in batches

Goal: the notebooks you name move to Hanji in batches, each note checked word for word by `en_to_hanji.py`.

Steps: count what is left per notebook first, then copy in batches of the size you set. Each batch reports a table of notes copied, checked and failed, with the reason for each failure.

Acceptance: every note of a named notebook is copied and checked, or listed with its reason; the colour count of failure 214 stays in each table.

### DD-14 Spring 2027 course preparation

Goal: for each session of the spring course, the sources and readings with links checked on the day, and a deck skeleton built by the kubs-deck skill that passes its deckcheck gate.

Steps, after E6: DeepSeek lists candidates per session in a table (title, link, why it fits, length). You choose, and DeepSeek builds the skeletons and runs the gate.

Acceptance: every link opens on the day of the report, and every deck passes deckcheck.

### DD-15 The human quality plan's measure runs

Goal: DeepSeek runs `decision_eval.py` on every note build and prepares the blind-read packets, once HQ-01 has built the test.

### DD-16 Stock scores refreshed each week

Goal: each week, the stock-analysis skill's data pull and its 0 to 10 scores, written as a table in socrates, with the skill's grouping and no call of its own; a note for you still goes through the card path.

Acceptance: each score in the table is reproduced from its Yahoo Finance values by the skill's script.

## Docs: where they go and how agents find them

Your documents are spread over six docs folders and five naming styles (dated with spaces, dated with dashes, capitals with underscores, plain words, and the prefix "implementation plan"), and four of your repositories are public. After DD-10, four rules hold.

1. Home. A document lives in the repository whose code or data it describes. Plans that change agentkit's rules, skills or scripts stay in agentkit; virtualfriend's VM and log documents move to virtualfriend, which is private.
2. Privacy. A document that quotes your notes, mail, memory, health, money or people, or that names a production machine's address, lives in a private repository: socrates for your life, the project's own repository for its machines.
3. Names. Lowercase words with spaces. A living document is named `<topic> <kind>.md`, with the kind plan, spec, runbook, reference or brief; a dated snapshot is `YYYY-MM-DD <topic> <kind>.md`, with the kind analysis, report, decision or letter. Three or more files of one work share a folder named for it, with its data in `data/`.
4. Index. Each docs folder has an `index.md` written by `agentkit/tools/docs_index.py`: one row per document with its kind, its status (living, snapshot, done, retired) and its first sentence. `AGENTS.md`, which every session loads, says to read the index of the repository you work in, and agentkit's for plans that span projects.

| Now in agentkit/docs | After DD-10 | Why |
|---|---|---|
| `2026-11-18 vm migration us-south1.md` and its `config` file | virtualfriend `docs/2026-11-18 vm migration runbook.md` and `docs/2026-11-18 vm migration config.md` | virtualfriend's machine, named with its address |
| `2026-11-18 log rotation prompt.md`, `2026-11-19 log rotation code/` | virtualfriend `docs/` | virtualfriend's logs |
| `agentic_improvement.md` | `2026-11-02 agentic improvement analysis.md` | a dated snapshot |
| `implementation plan agentkit.md`, `implementation plan claude code.md`, `IMPLEMENTATION PLAN module extraction.md`, `implementation plan streamline.md` | `agentkit plan.md`, `claude code plan.md`, `module extraction plan.md`, `streamline plan.md` | one naming style; each one's status read from its own text into the index |
| `lessons_learned.md` | `lessons learned.md` | one naming style |
| `human quality plan.md`, `deepseek delegation plan.md` | unchanged | living plans |

The other folders follow the same rules. In socrates, `IMPLEMENTATION_PLAN_socrates.md`, `PROJECT_BRIEF_socrates.md` and `implementation plan merge socrates.md` take plan and brief names, and the dated letters and positions keep their dates with spaces; swim, email-digest and invoice-admin rename their capitalised files.

Suggestion: a frontier-model session writes the runbook of DD-01 and DeepSeek runs DD-02 under it, which changes no rule and no document of yours and tests the report form on a task whose result a test decides; E1 to E6 wait for your word.

## Log

- 2026-11-20: created from the opencode session database (602 top-level runs since 2026-10-01), the commit logs of the last 60 days, the memory lint counts and the VM move runbook of 2026-11-18, in answer to Chaehan's question of what else DeepSeek can take, with the docs question answered in its last section.
