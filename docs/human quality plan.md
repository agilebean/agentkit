# Human quality plan

**Plan, not implemented yet.** This file plans how the notes DeepSeek writes into Evernote and Hanji become knowledge you can act on, and it is the one place where that work is tracked: the status board holds each task's state, and the log at the foot of this file holds the dated reason for every change. Its tasks are written for the session that takes them up, most of them for a frontier model such as Claude Opus 5.5 or Claude Fable 5.2. The dated analyses it builds on stay as written, in socrates under `docs/human quality/`: the 2026-11-05 agent writing summary, the note wording analyses of 2026-11-15 and 2026-11-17, and the 2026-11-17 build spec.

agentkit is a public repository. Nothing from Chaehan's notes or memory (names, health, money, dates with people) goes into this file or any other agentkit file: test notes, gold lists and measured builds live in socrates, which is private, under `docs/human quality/`, with the data the scripts read in its `data/` folder. This file holds task states and aggregate numbers.

## Summary

- Your notes now come out true and plain, and the step that makes them smart is still missing: of the 15 failures since 2026-11-05 about what a note chose to say, 6 missed what the facts mean for you, and each fix built its step inside one skill only.
- The fact-card path won your blind read on 2026-11-20 on wording alone, since both versions held the facts the old path had chosen; choosing its own facts the same day, its Takeaway left out the note's soonest decision (A4), then named its deadline as a bare date with the action left in the body (A5).
- Your 257 rules run to 89427 words, 13 of them added since 2026-11-03, and on 2026-11-20 a Claude Opus 5.5 session wrote a stock review that failed quality over quantity twice, the first time without having opened rule 19.
- On 2026-11-16 an open question found the idea of a conversation in 4 of 4 DeepSeek runs and the full instruction in 0 of 4, so understanding has to come before any rule of form.
- If notes built from your live decisions still miss them in your blind read, DeepSeek's judgment is the limit, and the step that finds the point moves to a stronger model (~$0.05 a note by the 2026-11-15 estimate).
- So the next gain is one missing layer, your live decisions held as data with a test that a note conveys them; every check of form added so far has been met with a new robotic form.

## What your corrections have in common

Your corrections since 2026-11-03 ask for six things, and under them lies one wish: to read a note once and act on it, without checking it and without correcting the agent again.

| What you asked for | Your words | How the system answered |
|---|---|---|
| 1. Only what changes a decision | "I'm repeating for the tenth time I want quality over quantity so no clutter" (2026-11-07) | the parsimony principle, rule 19, the cut list and gate checks T9 to T12, the overlap step, card selection |
| 2. Your seat and your order | "every response must be written for the human user perspective" (2026-11-07) | the seat test, sections in your life's priority order, What went well |
| 3. Only what the record says | "most plausible-sounding is not enough" (2026-11-08) | rule 17, the empty case of rule 245, copied record lines with gate check T19, cards with their source line |
| 4. Plain speech | "the constant second person wording sounds repetitive and unnatural" (2026-11-14) | rule 2 and its 79 markers, `common_sense.md`, the card writer |
| 5. What it means for you | "now i just have a technical document which doesn't tell me anything of the dilemmas i'm facing" (2026-11-07) | goal sections in life challenges, `idea.md` in date analysis, the pattern sentence and decisions in the stock review |
| 6. Fix the cause at its earliest step | "not to fix issues on the symptomatic level but strategically as early and high as possible" (2026-11-06) | rule 11's causal order, rule 245, build specs, the 60 labelled lines |

Read together, the six are two demands and one way of meeting them. You act on a note without opening its sources, so it must be true: an invented or misread fact does more harm than a missing one (rows 3 and 4). You want the note to do the choosing, connecting and ranking you would otherwise do yourself (rows 1, 2 and 5). And you want DeepSeek, at $0.01 to $0.08 a note, taught so that each correction you give is the last of its kind (row 6). The time you spend correcting is what the present system costs you, and this plan succeeds when that time falls.

The register's entries since failure 150 use "robotic" 15 times, "clutter" 14 times and "quality over quantity" 12 times, and your sharpest words, "underwhelming" and "no clear train of thought", fall on the notes that missed what the facts mean (failures 178, 182, 184 and 213).

## Symptom or structure: the state on 2026-11-20

Your system has moved from bans to structure for truth and wording. Choice is structural in form and measured against the wrong reference, and for meaning, where knowledge for a decision lies, no step exists outside three skills.

| Layer | What you ask of it | Verdict | Why |
|---|---|---|---|
| Truth | every fact from your record, nothing invented | structural, one gap | Gate check T19 refuses a name or number that the copied record lines lack, and the card writer added an obligation the facts did not hold in 0 of 36 lines, against 8 of 36 before. A misread source reaches you unchecked: a photo measured by eye, a transcript line given to the wrong speaker (failures 216 and 217). |
| Wording | plain speech | moving to structural | The card writer came close to your accepted line on 11 of 11 cards. The 79 markers of rule 2 remain bans, and one sentence per card repeats a full name: three sentences in a row of A4 open on the same five words. |
| Choice | only what changes a decision, in your order | structural in form, measured against the wrong reference | `card_choose.py` was tuned against B, the old path's own choice: its prompt versions were scored by the share of B's cards they kept, and the version that let the soonest matter lead kept 59% against 66% and was reverted. Its prompt lets a section's latest event lead, so A4's Takeaway took that event and left the decision due in two days in the body. A5, built later that day with your order of priorities (commit 8315a26), names that decision's deadline in the Takeaway as a fact, keeps the action in the body, and is still scored by the share of B's cards it keeps (55% to 66%). |
| Meaning | what the facts force for your decisions | no general step | A card holds one source line and a consequence only when that line states it. So the path cannot write a line that computes from three record lines how far a prescription reaches into a winter abroad, the kind of line your 2026-11-16 Life Challenges note is built from. Life challenges, date analysis and the stock review each built their own step after a correction. |
| Measurement | proof that a change helps you | symptomatic | Every measure judges a line (60 labelled lines, 80% shared words with your line) or a check. Nothing tests whether a note tells you your decisions, so your blind read, run once, is the only measure of a whole note. |
| Rules | each correction the last of its kind | symptomatic, and slowing | Core 0 says a correction merges into its class, and 13 new numbered rules have come since 2026-11-03. RULES.md changed in 43 commits in the week from 2026-11-02, 15 in the next and 8 in this one, as the work moved into scripts. |

Three causes lie under the symptomatic rows.

1. The checks write the text. A model meets every check and drops every rule that has none (2026-11-05), and each new check of form has been met with the next robotic form: a check on a line's first word gave every line "You", and its fix gave every line an instruction (failure 207). The writing call should see cards and examples, never a rule.
2. Your decisions are not data. They stand as prose in the Life Challenges note, in skill briefs and in OmniFocus, so no step can ask which decision a fact serves, rank by deadline or test a note against them. Knowledge for action is a relation between facts and a decision, and the card path's unit is the single fact.
3. Understanding comes after form. Every skill except date analysis hands DeepSeek its rules before it asks what the material means, against the 4 of 4 and 0 of 4 of 2026-11-16.

You would call the meaning row solved when two notes of different kinds, built without a correction from you, name your live decisions with their deadlines in their first lines, each state one or more derived consequences, and win your blind read against the earlier build.

## What a note must do

A note gives you knowledge when, after one read, you can name your live decisions, their deadlines, what each depends on and what the facts force, and nothing in it is untrue.

| Measure | How it is taken | Baseline | Latest | Target |
|---|---|---|---|---|
| Decision recall | a fresh call reads only the note and lists the decisions it states with their deadlines; the list is matched to the gold list you confirmed (HQ-01) | not measured | 2026-11-21, judge, three runs, whole note (Takeaway): Life Challenges 2026-11-07 rebuild 11-12 of 16 (2-4), first build 9-10 (3); Stock Review 2026-11-20 final 2-3 of 4 (1-2), first 0-1 (1-2); A4 4 of 8 (0), B 3-4 (3) | every decision due within 30 days, in the Takeaway |
| Soonest decision | the Takeaway line on which the decision due soonest appears, with its action | A4: absent; A5: line 2, a date without the action | 2026-11-21, by the decision test: A4 in the body only, B line 2; Life Challenges 2026-11-07 rebuild line 3, first build line 2 | among the first three lines, with the action |
| Derived consequence | Takeaway lines that state what two or more record lines mean together, recomputed by a script (HQ-04) | A4 and A5: 0 of 6 | | one or more per decision |
| Invented facts | gate check T19 and the card check | 0 since 2026-11-09 | | 0 |
| Wording | flags of `wording_lint.py --strict`, and lines the literal question marks "cannot say" | A4: 0 and 1 | | 0 and 0 |
| Your corrections | corrections you give per note, counted in the failure register | not counted | | falling month on month |
| Your blind read | a new build against the last accepted build of its kind | A chosen over B, 2026-11-20 | | the new build |

Length is reported beside recall with no target, since a word count read as the goal produced failure 205. A session writes each new value into Latest with its date and the note it was taken on.

## The path from facts to knowledge

After this plan, every note goes through seven steps; three exist today and one exists in date analysis alone.

1. Understand (new; date analysis has it as `idea.md`). One call on the sources alone, with high reasoning and no rule of form, answers which of your live decisions the material bears on, what it changes for each, and the one idea that ties it together. It writes `point.md`.
2. Ground (exists: `card_fill.py`, `card_check.py`). Every fact becomes a card with its source line.
3. Derive (new). A derived card states what two or more record lines on one matter mean together, names its premises and writes out its arithmetic, which a script recomputes. A reading card states a link the record does not, written as the agent's reading or as open with the possibilities named (failure 202).
4. Choose (exists as `card_choose.py`, to be changed). Each card names the decision it serves; the Takeaway ranks decisions across sections by deadline and cost, and a section's live decision leads before its latest event.
5. Say (exists: `say.py`), with a pass that names a thing in full once and briefly after.
6. Check (exists: check T19, the card check, the wording lint), plus the decision test.
7. Learn (new). A correction from you becomes a case of the layer that failed before it becomes a rule, and a change is kept only when the measures improve.

Rule 17 keeps its force inside this path: a person, a cause, a payment or a date is attached to an event only when one record line names both. A derived card adds no such link; it computes what the cited lines already hold.

## Status board

This table is where progress is tracked. A session that takes a task sets its status here before it starts, and every change of status gets a dated entry in the log at the foot of this file, with its reason and numbers. Tasks are numbered HQ, for human quality, in causal order: the measure first, then the layers from meaning down to wording, then the rules and the spread to every skill. The decisions D0 to D5 are yours and are listed after the board.

| ID | Task | Layer | Model | Waits on | Status |
|---|---|---|---|---|---|
| HQ-00 | Personal test data out of the public repository | privacy | any | D0, decided | done in part on 2026-11-20; the rest is DD-03 of the delegation plan |
| HQ-01 | Decision test for a whole note | measurement | frontier | D1, decided | blocked, 2026-11-21: Takeaway recall ranks the build you preferred above in 4 of 9 pair-runs by shared words and 1 of 9 by the judge |
| HQ-02 | Your live decisions as data | choice, meaning | frontier | D2, decided | ready |
| HQ-03 | Understand before form | meaning | frontier designs; DeepSeek and a frontier model run | none | ready |
| HQ-04 | Derived and reading cards | meaning | frontier | D3, decided | ready |
| HQ-05 | Choose by decision and deadline | choice | frontier | HQ-02 | blocked: HQ-02 |
| HQ-06 | Sentences that follow each other | wording | any | none | ready |
| HQ-07 | A correction becomes a case first | learning | any | D4, decided | ready |
| HQ-08 | Retire rules and checks that write form | rules | frontier | D5 per batch | ready |
| HQ-09 | One builder for every note skill | all | frontier | HQ-03 to HQ-06 | blocked |
| HQ-10 | Memory index and dated fact lines | truth | any | HQ-02 for part b | ready for part a |

Frontier means Claude Opus 5.5, Claude Fable 5.2 or a newer model; any means a model that writes and tests code well, DeepSeek included.

## Decisions only you can make

The session that reaches a decision asks it with the question tool, quoting this section.

- D0, for HQ-00, decided on 2026-11-20: "move data to socrates". What moved and what stays public is under HQ-00.
- D1, for HQ-01. For each benchmark note, the decisions you faced on its date. The session drafts each list from the record and you confirm or correct it, since what matters to you is yours to define (core 6).
- D2, for HQ-02 and part b of HQ-10, decided on 2026-11-21: "the decisions from life challenges should be in the life folder as a dated file but only after i confirm their validity, so the life challenges skill should ask that by checkboxes after presenting the life challenges, and before creating the note". After the life-challenges skill presents the challenges and before it creates the note, it asks you with the question tool, one checkbox per decision, which are valid, and writes only those to a dated file in `socrates/life/`. HQ-05 and part b of HQ-10 read that file, and no register in `decisions/` is built.
- D3, for HQ-04, decided on 2026-11-21: "Derived and readings". A line may state what two or more record lines on one matter mean together, with its premises cited and its numbers recomputed by a script, and a link the record does not state appears only written as the agent's reading or as open. Whether "probably" and "may" may stand in a line about evidence, as the Cochrane Handbook uses them, stays open.
- D4, for HQ-07, decided on 2026-11-21: "Case first". A correction of yours about a note becomes a case of the layer it hit before it becomes a rule, and a new rule or check is kept only when the measures improve; core 0 of `AGENTS.md` changes with HQ-07.
- D5, for HQ-08. Each batch of rules to merge or retire, shown to you as a before and after.

## Tasks

Each task names its goal, why it stands where it does, its inputs, its steps, the number that accepts it and what it leaves alone. Data from Chaehan's notes goes to `socrates/docs/human quality/`, never into agentkit.

### HQ-00 Personal test data out of the public repository

Goal: nothing from your notes or memory is readable on GitHub.

Done on 2026-11-20 (agentkit 839ad31, socrates b01f084): the 2026-11-15 wording test, the 2026-11-17 wording build with its step 8 notes A to A5, `wording_cases.tsv`, `wording_pairs.tsv`, the 2026-11-05 to 2026-11-17 analyses and the answer quality packet moved to `socrates/docs/human quality/`. The writer prompt kept its rules in agentkit; its eight examples from your notes became `data/wording_writer_examples.md`, and `say.prompt_text()` joins the two into the same bytes as before, so no measured prompt changed. The 123 tests of the card path pass, and they skip where the data is absent.

Left public: 170 or more lines in tests, skills, RULES.md and `common_sense.md`, the medicine name in `wording_fill_prompt.md`, and the git history of every moved file. DD-03 of the [DeepSeek delegation plan](<deepseek delegation plan.md>) takes them, with your decision E2 on the history.

### HQ-01 Decision test for a whole note

Goal: one set of numbers per note that says whether it tells you your decisions, so every later task is judged by it.

Why first: every measure today judges a single line. The stranger check of 2026-11-15 failed because it judged lines out of context (it refused 20, then 10, of your 20 accepted lines); this test reads the whole note and compares what it states with a list you confirmed.

Inputs: pairs of builds on one date and one set of sources, one you rejected and one you accepted or preferred, all kept in socrates. Candidates:

- the first 2026-11-07 Life Challenges build (failure 178) and its rebuild of the same day, from socrates' git history
- the 2026-11-20 Stock Review, its first version (failure 226) and its final one, from Hanji's version history
- one date note before and after the rewrite of failure 213, from Evernote's version history
- B and A4 of the step 8 test (`socrates/docs/human quality/2026-11-17 wording build/step8/`), built from one source file (`socrates/life/2026-11-09-sources.md`), once you have read A4

Steps:

1. For each note, draft the gold list from the record as it stood on the note's date: each decision with its deadline, its options, what it depends on and its source line. Ask Chaehan to confirm each list (D1).
2. Write `agentkit/scripts/decision_eval.py <note.md> --gold <gold file>`. A fresh DeepSeek call with no other context reads the note and returns the decisions it states, one row each; a matching step pairs them with the gold rows, by shared content words or by a judge call that sees one pair at a time, whichever separates the pairs better. The script prints recall overall and within the Takeaway, the decisions it invented, the wrong deadlines, and the Takeaway line on which the decision due soonest first appears.
3. Tests in `agentkit/tests/test_decision_eval.py` with a stubbed model and invented gold rows.

Acceptance: in three runs, every build you preferred scores above the one you rejected on Takeaway recall. When the test cannot separate them, report the numbers and stop: your blind read stays the only measure of a whole note.

Leave alone: every gate, prompt and note.

### HQ-02 Your live decisions as data

Goal: each live decision of yours is one line a script can read: what you decide, by when, the options, what it depends on, its source line, and whether it is open.

Why here: choosing by what is due (HQ-05), the understand step (HQ-03) and the decision test all need the list, and today it exists only as prose.

Inputs: the latest Life Challenges note in `socrates/life/`, the Current state and On the horizon sections of the memory files, step 7b of the 2026-11-17 build spec.

Steps:

1. Propose the line form and its home (D2) with three filled examples from the record.
2. On your yes, fill the decisions live on the day, each from a record line; nothing inferred becomes a decision (rule 245's empty case).
3. `memory_lint.py` gains a check of the form.
4. A script lists the open decisions by deadline, and the life-overview and life-challenges skills read that list in their gather step.

Acceptance: the list holds every open decision of the latest Life Challenges note and of the latest stock review, each traced to its record line, and you confirm it.

Leave alone: no fact moves between memory files without your yes.

### HQ-03 Understand before form

Goal: every note build starts with `point.md`, written from the sources alone in answer to one open question, and the note is built around it.

Aim: on 2026-11-21 you chose A4 over B for its fuller body: its sections hold more of the record, such as the "You must still..." lines, and not for its Takeaway, which names none of the eight decisions. A build keeps every live matter of a section with the step you still have to take, and nothing the understand step adds may cost that body.

Why here: the 4 of 4 against 0 of 4 of 2026-11-16, and three skills that each built this step by hand after a correction.

Steps:

1. Write the question once for every note kind: which of your live decisions the material bears on, what it changes for each, and the one idea that ties it together. Date analysis keeps its own question.
2. Run it on the sources of the benchmark notes with DeepSeek at high reasoning and with a frontier model, three runs each, timing every call. The runner's 120 s idle cut stopped long silent reasoning in failure 213, so the cut rises for this step alone.
3. Build each note through the card path from `point.md`, measure it with HQ-01, and give Chaehan the best build of each model blind.

Acceptance: you prefer the new build in a blind read against the same build without `point.md`, on three of every four benchmark notes, with no invented fact; the judge's whole-note recall from `decision_eval.py` is reported beside it as a signal, never as a gate. The model that wins your blind read is written into the skills, with its cost per note.

### HQ-04 Derived and reading cards

Goal: the card path can state what facts mean together, and only what they hold.

Why here: knowledge for a decision is mostly a relation between facts, and a card holds one source line.

Steps, after D3:

1. Two card kinds. A derived card lists two or more source lines and a `calc` field with its arithmetic: a date difference, a count, a sum, a conversion into your unit. A reading card states a link the record does not.
2. `card_check.py` recomputes every `calc` and refuses a number it cannot reproduce, a derived card that attaches a person, cause, payment or date to an event, and a reading not written as a reading or as open.
3. The fill prompt asks for derived cards after the fact cards, from the consequences in `point.md`; the writer prompt gets one example of each kind, from an invented record.

Acceptance: from the record lines behind the 2026-11-16 Life Challenges note, copied into a sources file in socrates, the path writes that note's two computed lines (the prescription supply and the spare days) with numbers the script recomputes. The joined fact of failure 189 is refused as a test case, and the numbers of `wording_eval.py` do not fall.

### HQ-05 Choose by decision and deadline

Goal: the Takeaway opens with the decisions due soonest and costing most, and a section's live decision leads before its latest event.

Aim: on 2026-11-21 you chose A4 over B for its fuller body: its sections hold more of the record, such as the "You must still..." lines, and not for its Takeaway, which names none of the eight decisions. A build keeps every live matter of a section with the step you still have to take, and nothing the Takeaway's choice adds may cost that body.

Why here: the Takeaway takes each section's lead, so in A4 a section's latest event stood there, and in A5 your order of priorities brought the soonest deadline in as a date while its action stayed in the body.

Coordination: commit 8315a26 gives every choose call your order of priorities from `memory/optimize-my-life.md`, and uncommitted edits to `wording_choose_prompt.md` and `wording_fill_prompt.md` in the agentkit checkout on 2026-11-20 continue it. The session that made them owns those files until it commits, and this task starts from that commit.

Steps:

1. Each card names the id of the decision it serves, from `point.md` and HQ-02.
2. The Takeaway is chosen across sections: open decisions by deadline and cost first, then one state per section that changes what you expect. An event enters only when it changes a decision.
3. Choice is measured against the gold lists of HQ-01, no longer against B.

Acceptance: rebuilt from the cards of 2026-11-09, you prefer the new build to A4 in a blind read; the judge's whole-note recall from `decision_eval.py` is reported beside it as a signal, never as a gate, with the Takeaway line on which the decision due soonest appears.

### HQ-06 Sentences that follow each other

Goal: a section reads as speech: a thing is named in full once and briefly after, and each sentence opens on what you already know from the one before.

Why here: the 2026-11-17 analysis left this gap untested (its fourth gap). One sentence per card (A3) repeats a full name, and joining cards (A2) gave a median of 30 words a sentence.

Steps:

1. A pass in `say.py` over each section's lines: the first mention keeps the full name and later ones take a short form of it, and two cards on one thing may share a sentence.
2. Every number, name and verb of each card stays, held by the existing checks.
3. Rebuild the sections of A4.

Acceptance: no thing is named in full in two sentences in a row, and the median sentence has ~18 words or fewer. The acceptance set of `pairs.tsv` stays at 11 of 11 with no new lint flag, and you prefer the rebuild to A4 in a blind read.

### HQ-07 A correction becomes a case first

Goal: a correction you give about a note changes a measure before it changes a rule, so you never give the same correction twice.

Why here: 13 numbered rules have come since 2026-11-03 against core 0's merge rule, and step 6 of the 2026-11-17 build spec waits on D4.

Steps, after D4:

1. Core 0 in `AGENTS.md`: a correction about a note is classed by the layer it hit (truth, wording, choice, meaning, structure) and stored as a case: a rejected or accepted line for `wording_eval.py`, a missed decision for HQ-01, or a record line. Core 0 also names this plan, so the task of that layer receives the case.
2. A new rule, marker or check is kept only when `wording_eval.py` and `decision_eval.py` improve and neither falls, and both numbers go into the reply.
3. The failure register entry names the case it added and the task it belongs to. Part c of step 7 of the build spec, a step at a session's end that lists your accepted and rejected lines, is built here.

Acceptance: your next three corrections each add a case, and a rebuild of the note that drew each one passes it.

### HQ-08 Retire rules and checks that write form

Goal: writing calls see cards and examples, never rules, and the rules shrink to what the agent repairing the system needs.

Why here: a check of form gets that form back (failures 163 and 207), and rules read by line range are missed (failure 226).

Steps:

1. Map every rule and check that touches note writing to its layer and to the script that now enforces it, if any.
2. Propose batches. A rule a script fully enforces becomes a one-line pointer to the script, and incident rules merge into their class. A check that forces a form (the gate's seat check on a line's first two words, and the sentence "Both sentences start with You or Your" in step 3 of `note_build.py`, step 5 of the build spec) is kept only if the measures fall without it.
3. Each batch goes to you as a before and after (D5), and the index is regenerated with `tools/rules_index.py`.

Acceptance: per batch, you prefer the new build in a blind read or rate the two equal, `wording_eval.py` does not fall on the benchmark, and the test of every removed rule is kept in its class or in a script; the judge's whole-note recall from `decision_eval.py` is reported beside it as a signal, never as a gate.

### HQ-09 One builder for every note skill

Goal: life overview, life challenges, trip note, stock review, date analysis and the evernote skill's research and health notes go through one path.

Why here: each skill built meaning by hand, so a new skill starts without it, as the stock-analysis skill did on the day it was written (failure 226).

Steps:

1. Each skill's note spec shrinks to its sources, its sections and its own question for the understand step; the shared builder does the rest.
2. Port one skill at a time, in the order of how often its notes drew a correction in the failure register, each measured by HQ-01 on its benchmark note.
3. Delete a skill's old steps once its port passes (rule 203).

Acceptance: per skill, in a blind read you prefer the port or rate the two equal; the judge's whole-note recall from `decision_eval.py` is reported beside it as a signal, never as a gate.

### HQ-10 Memory index and dated fact lines

Goal: a build reads only the lines it needs, each with its date and who stated it.

Steps: part a of step 7 of the 2026-11-17 build spec as written (an index in three levels); part b (one fact a line under Now, Events, History and Research, plus the Decisions heading of HQ-02) after D2. Part c is built in HQ-07, and part d holds once every note goes through the card path (HQ-09).

Acceptance: as the build spec states for each part.

## How a session takes a task

1. Read the Summary, the board and the task, then every file the task names, and check `git status` in agentkit and socrates for another session's edits on those files (core 7).
2. Set the task's status to "in progress, <date>, <model>" and commit that line alone, so a parallel session sees the claim.
3. Run the task's measure before any change and write the baseline into the measures table.
4. Do the steps. When the acceptance number is not reached, stop, record the number, set the status to blocked with the reason, and change nothing else.
5. Put every decision the task waits on to Chaehan with the question tool.
6. Record the result: the status with its date, the new values in Latest, an entry in the log at the foot of this file with the reason and the commits, and any correction Chaehan gave in the failure register.
7. Add a finding outside the task as a row with status proposed, and start nothing unasked.

## How this plan changes

- A correction about a note goes as a case to the task of the layer it hit (HQ-07); when no task covers that layer, it becomes a proposed task.
- When a task is done, its row of the assessment table is rewritten to the new state, and the earlier state stays in the log.
- The plan states what is true now, so a done task shrinks to one line with its result.
- When a measure stops moving over three builds, the layer above it is the limit, and the next task goes there.

Suggestion: a frontier-model session takes HQ-01 now, which changes no rule, gate or note and brings you the gold decision lists of its benchmark notes to confirm (D1).

## Technical details

- Failures since 2026-11-05 about what a note chose to say, from `socrates/memory/agentic_ai.md`:
  - kept what no decision needs: 163, 171, 174, 175, 202, 205 and 209
  - missed what the facts mean: 178, 182, 184, 210, 213 and 226
  - wrong order: 191 and 195
- The steps built for the second group: goal sections and researched answers in the life-challenges skill (178, 184), What went well in the life-overview skill (182), `idea.md` in the date-analysis skill (210, 213), the decisions grid in the stock-analysis skill (226).
- Phrase counts: `sed -n '4851,$p' memory/agentic_ai.md | grep -oi '<phrase>' | wc -l` in socrates on 2026-11-20; line 4851 opens failure 150.
- Rule counts: `grep -c '^### [0-9]' RULES.md` gives 259 headings, since the numbers 205 and 221 are each used twice; `wc -w RULES.md` gives 89427. Rules 245 to 251 were added on 2026-11-03 (commit 4050835) and 252 to 257 after.
- Commits on RULES.md per week: `git log --since=2026-10-01 --format=%ad --date=format:%G-W%V -- RULES.md | sort | uniq -c`.
- The card path: commits 1e6c3c4 to 5d123f8 (build spec steps 1 to 4), 8d0a543 (A and B), 6f53f0e (your choice of A), 8f95b3a (A2 and A3), 5aa6587 (A4 and `card_choose.py` with its three prompt versions), 8315a26 (A5); the notes and measures are in `socrates/docs/human quality/2026-11-17 wording build/step8/`. Steps 5, 6 and 7 of the build spec are not built.
- A4 against your standard: 1188 words, a median sentence of 14 words, no lint flag, no check T19 failure, one line the literal question marks "cannot say", and a Takeaway of six lines, none of which states a consequence.
- The 4 of 4 against 0 of 4: failure 213, DeepSeek V4.1 Flash at high reasoning, two runs per cell on two stretches of one transcript.

## Log

- 2026-11-21, fourth entry: you answered D2, D3 and D4 with the question tool. D2: the life-challenges skill asks, after it presents the challenges and before it creates the note, which decisions are valid, one checkbox each, and writes the confirmed ones to a dated file in `socrates/life/`, which HQ-05 and part b of HQ-10 read. The register in `decisions/` that the question proposed is dropped. D3: derived lines with cited premises and recomputed numbers, and readings marked as the agent's or as open. The Cochrane wording stays open. D4: case first. HQ-02, HQ-04 and HQ-07 are ready, and HQ-05 and part b of HQ-10 wait on HQ-02.
- 2026-11-21, third entry: you chose A4 over B for its fuller body (question tool, options fuller body, plainer wording, Takeaway doesn't matter). HQ-03 and HQ-05 now name that aim: a build keeps every live matter of a section with the step you still have to take, and the understand step or the Takeaway's choice may not cost that body. HQ-03 is ready; HQ-05 waits on D2.
- 2026-11-21, second entry: your blind read is the measure of a whole note, as HQ-01's acceptance says when the test cannot separate the builds. The acceptance of HQ-03, HQ-05, HQ-08 and HQ-09 now asks that you prefer the new build in a blind read, with the judge's whole-note recall of `decision_eval.py` reported beside it as a signal, never as a gate; HQ-08 and HQ-09 also pass when you rate the two equal, since a batch of retired rules or a port that changes nothing you see is the result they want. HQ-03 and HQ-08 no longer wait on HQ-01: HQ-08 is ready, and HQ-03 and HQ-05 wait on what made A4 better than B for you, since A4's Takeaway names none of the eight decisions of 2026-11-09 and B's names three. DD-15 of the delegation plan prepares the blind-read packets with the test as its signal. HQ-07's step 2 still keeps a rule only when `decision_eval.py` improves; it changes with D4, which another session is asking.

- 2026-11-21: HQ-01 is blocked, since the decision test does not rank every build you preferred above the one you rejected on Takeaway recall. `scripts/decision_eval.py` (agentkit acd07ef, 16 tests) has one fresh DeepSeek call read the whole note and another the Takeaway alone, and matches each call's rows to your gold list by shared words or by a judge call on one pair at a time. You confirmed four gold lists with the question tool (D1; socrates c4a9d00, `docs/human quality/data/decision_test/`): Life Challenges 2026-11-07 (16 decisions), Stock Review 2026-11-20 (4), Life Overview 2026-11-09 (8, A4 preferred over B) and date 3 (3), a control, since its two versions share one Takeaway word for word. In three runs with no failed call, the preferred build led on Takeaway recall in 4 of 9 pair-runs by shared words and 1 of 9 by the judge: Life Challenges 1 of 3 by both, Stock Review 3 of 3 by words and 0 of 3 by the judge (three ties), A4 against B 0 of 3, at 0 against 3 of 8 every run, and the control tied in all three runs. On whole-note recall the judge ranks the preferred build above in all three runs for Life Challenges and Stock Review, and for A4 in one run with two ties. Shared words paired rows on a common word ("follow up" with the Taxpayer Advocate follow-up), and the judge refused near matches ("buy Intel" against "buy Intel or AMD"). A4's Takeaway states none of the eight decisions, so your choice of A4 rests on what its body says, and B's Takeaway names three. Whole-note recall would not pass either, at 7 of 9 pair-runs by the judge, so your blind read stays the only measure of a whole note, as the task's acceptance says; the test still reports what a Takeaway leaves out. The first batch of 2026-11-20 was void after HTTP 429 refusals from the OpenCode Go route, so every call now passes one gate, six at a time in these runs, and a refusal waits and tries again. Correction recorded as failure 233 in socrates, with one sentence in rule 62.

- 2026-11-21: tasks DD-01 and DD-02 of the [DeepSeek delegation plan](<deepseek delegation plan.md>) were taken by the steps of "How a session takes a task" and are done: DeepSeek's runs now end in a report that `scripts/report_check.py` checks, and agentkit's suite runs on every push. Step 3 names a measures table, which the delegation plan does not have; the baseline (1 failed, 550 passed on 2026-11-20) went into the runbook's table of what exists. No HQ task changed status.
- 2026-11-20, second entry: renamed from "note quality plan", ids NQ, to "human quality plan", ids HQ, and this log moved here from `docs/_log.md`, which is deleted (Chaehan: "_log is too generic so put it in the same file to the bottom"; rule 79, failure 231). D0 decided, "move data to socrates": HQ-00 is done in part (agentkit 839ad31, socrates b01f084), and the rest went to DD-03 of the DeepSeek delegation plan, written the same day. D2 now names socrates' `decisions/` folder, which the first version missed. A5 was committed by its session as 8315a26.
- 2026-11-20, first entry: created from failures 156 to 226 of the socrates failure register, the analyses of 2026-11-05 to 2026-11-17 and the step 8 builds A to A5 of the card path. It states the assessment of that day and tasks HQ-00 to HQ-10: HQ-01, HQ-06 and part a of HQ-10 were ready, the rest waited on a task or on decisions D0 to D5.
