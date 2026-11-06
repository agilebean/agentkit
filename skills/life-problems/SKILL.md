---
name: life-problems
description: Build Chaehan's dated Life Problems map - the problems that weigh on Chaehan now, each typed by the kind of stuck it is, the one decision others hang on, what Chaehan can put down, quick wins with their message or script ready, and the open decisions written as dilemmas. Use when the user says "life problems", "my problems", "untangle my problems", "what weighs on me", or asks how to tackle several life problems at once. A status snapshot of every life domain is the life-overview skill, not this.
---

# Life Problems

A dated map of what weighs on Chaehan and the next move on each. The source of
truth is `socrates/docs/YYYY-MM-DD-life-problems.md`; its twin is the Evernote
note "YYYY-MM-DD Life Problems" in the notebook "Chaehan's Life". Run
everything from the socrates repo root. The life overview links here for its
decisions.

A dated map is never superseded (RULES.md 31): a new map gets a new date, and
every earlier map, note and file stays untouched.

The note is written to Chaehan as "you" (RULES.md 195), and every sentence
passes the seat test in `agentkit/AGENTS.md` core 1: its subject is your
decision, your body, your money or your time.

Do the steps in order, and write each step's product into the draft before the
next one. The Takeaway is written last.

## 1. Gather

1. Read the latest `docs/*-life-overview.md`, the previous
   `docs/*-life-problems.md` (or the previous Life Problems note, read with the
   evernote skill), `memory/_psych_obs.md`, `memory/_misc.md`,
   `memory/travel.md`, `memory/travelitinerary.csv`, and the memory file of
   each problem's domain.
2. List every item the previous map or the overview calls open. Ask Chaehan
   which are done, with the question tool: one multiSelect question per four
   items. Never decide that an item is done or open from a missing record
   (core 5). Write what Chaehan reports into the domain memory file, dated.
3. Check every open question before it enters the map. A question is
   Chaehan's only if a message of Chaehan's asks it, or it decides an action
   Chaehan named. A question that only an agent's record carries ("ask J Noble
   how many dates a week") is asked of Chaehan before it frames anything
   (RULES.md 83). Name the message for each question you keep.
4. Each claim carries its file and date in your working notes before the draft.

## 2. Type every problem

Write the table `## Problems` with four columns:
`Problem | Kind of stuck | What weighs on you | Next move`.

Kind of stuck is exactly one of five, and the kind decides the move:

- **deadline**: it expires on a date. The move is to do it. Write the date
  after the kind: "deadline 2026-12-04".
- **one missing fact**: one fact decides it. The move is one probe: who you
  ask and what you ask. Then you decide.
- **waits on another decision**: its answer changes with a decision you have
  not made yet. The move is the default you can undo until then.
- **someone else's move**: after one message or call of yours, the next step
  is another person's. The move is that message, and then you put it down.
- **settled**: decided or done since the last map, with its date.

Row order: the knot and what hangs on it first, then deadlines by date, then
the rest. The Next move cell names the person, the place or the link.

Every problem of the previous map comes forward: it gets a row here, as
"settled" when it is done, or a line in the cut list, `- <its name>: <why it
left>`. A decision Chaehan still has to make never leaves as world detail; the
gate (P13) names each one that went missing.

## 3. Find the knot

For each pair of open decisions, ask: if this one's answer changed, would that
one's change? Use only links the record states; ask Chaehan about a link you
only infer. The decision with the most dependents is the knot.

Only decisions count. A fact you still need (a fee, a count, a date someone
owes you) or an errand is never a dependent and never the knot: it is the
missing fact of the decision it serves.

Write `## The knot`:

1. One opening sentence: the knot and what hangs on it.
2. One bullet per dependent decision: how the knot's answer changes it.
3. Under each, indented: the undoable default while the knot is open.

When no decision has a dependent, the section says so in one sentence.

## 4. What weighs on you

Write one line per problem, in the table's third column. Build it from facts
the record shows about this problem:

- how long it has been open ("open since 2026-09-29");
- whether it was settled and then reopened (both dates);
- whether the next step escalates against a person you dealt with
  personally (the name and the date);
- whether it is a call to an authority that cannot be scripted;
- the money or the days at stake;
- your own words about it, quoted.

Three limits:

- Never write a pattern from `_psych_obs.md` as present ("you avoid calls",
  "you frame it as a binary"). The file holds one-time snapshots, and its bias
  guard forbids reading new facts through them. A pattern may shape a question
  you ask; it never becomes a sentence about Chaehan.
- When the facts are on record but what makes the problem heavy is not, and
  the answer would change the move, ask Chaehan with the question tool: one
  question, options built from the facts. Write the answer quoted.
- When the felt burden and the real risk differ, say both as two plain
  statements: "Your position is settled on paper. What is missing is the
  receipt."

The gate fails a cell with no date, number or quotation in it, and a cell
with a label word such as "anxiety", "avoidance" or "bias" outside quotation
marks.

## 5. Decisions as dilemmas

Write `## Decisions`, one `###` for the knot and one for every other decision
that is still open and is Chaehan's to make (not settled, not someone else's
move). Each holds, in order:

1. The opening sentence: "You want A and B, and C makes you choose." A and B
   are two things the record shows Chaehan wanting, and you can name the file
   and date of each; C is the constraint that forces the choice. When you
   cannot name two such wants, it is not a dilemma: give it no `###` and
   write it as the missing fact of the decision it serves, or as a deadline.
2. A bullet with the rule that settles it, as if-then: "If ..., ...; if ...,
   ...".
3. A bullet with the fact still missing and the one probe that gets it, or
   "You know enough to decide."
4. A bullet starting "While you wait": the default you can undo.
5. A bullet with the option neither A nor B names, when one exists: a
   choice Chaehan could make instead of A or B, never a probe or an errand.
   Find it by asking "which option is not on the table?". Write it as an
   option, never as a remark on how Chaehan frames things. When there is
   none, leave the bullet out.

## 6. Quick wins, ready to use

A quick win is something you can finish in one sitting of under 30 minutes
that takes something off you: a deadline risk, or a thread you keep open. Write
`## Quick wins` as a table:
`Task | Effort | What it takes off you | Ready to use`.

1. Rank the rows by what each takes off you for the effort of starting it, not
   by minutes (`memory/optimize-my-life.md`, the scarrends principle: stress
   removed is the value).
2. Effort is minutes. For a call to an authority, or a step that escalates
   against a person you know, add the word "call" or "escalation": these cost
   more than their minutes, so their instrument carries a script with one
   branch for each answer you can get.
3. Ready to use is the instrument you prepare, so that what is left for
   Chaehan is the click: the draft message, the call script in the call's
   language, the link, the exact form values. The cell holds the link, or
   the exact title of its subsection under `## Ready to use`.
4. Write each draft by the drafting rules (RULES.md 37, 85, 103, 250) and the
   thread's constraints. Nothing is sent: sending waits for Chaehan's yes on
   the final text (RULES.md 84).
5. A draft says only what the record shows. It never calls a document
   ready, states a plan, or takes a stance Chaehan has not stated (RULES.md
   111). Read the problem's own record before you draft: who the message
   goes to, and what Chaehan asks of them.
6. Your drafts are your own text: never put them inside verbatim markers,
   which are for another author's words and would hide the drafts from the
   checks (gate P11).
7. A social security number appears as its last four digits ("SSN ending
   1744"); the full number goes in when Chaehan sends (gate P12).

Write `## Ready to use` last in the note: one `###` per instrument, titled as
its table cell names it. Each opens with one sentence saying where it goes
("You send this to ..."), then the text. A call script has one `- If ...`
bullet per answer.

## 7. What you can put down

Write `## What you can put down` as bullets:

- each "someone else's move" problem: the one message, then whose move it is;
- each problem settled since the last map, with its date.

## 8. The Takeaway, last

At most five bullets and nothing else, each at most 30 words, each with you or
an action as its subject. The first names the knot and what hangs on it. Then what you can put
down, the quick wins' total minutes, and the decision closest to its date. No
bullet repeats a table row.

## Layout

The title line, then `## Takeaway`, `## The knot`, `## What you can put down`,
`## Quick wins`, `## Decisions`, `## Problems`, `## Ready to use`. Every
section opens with one sentence whose subject is you, before any list or
table. No empty heading, no "he" or "his", no thousand separators.

## 9. The gate

Write the cut list `$TMPDIR/life-problems_cuts.md`: one line per number or
date of the previous map that the new map drops,
`- <the numbers>: <where it went, or why it left>` (done, superseded, or world
detail Chaehan does not decide on), and one line per problem that left (step
2). A number that belongs to a decision still open is never world detail.
Then run:

```
python ~/Software/Prototypes/agentkit/skills/life-problems/scripts/problems_gate.py docs/YYYY-MM-DD-life-problems.md --original <previous map .md> --cuts $TMPDIR/life-problems_cuts.md
```

It runs the note checks of the life-overview gate (T5, T8, T10 to T13, T15,
T16), the lost-fact check T6 against the previous map, and the checks P1 to P9
of this skill (P1 to P14). A failing draft goes back to the step that made the
sentence it names. A PASS proves the form, not the content: the read below is
not optional. A PASS prints `note-gate:<sha>`, the stamp the Evernote write needs.

Then read the draft once yourself, quoting each sentence you fix:

- seat: a sentence whose subject is the agency, a study, a document or the
  research path is rewritten;
- burden: every "What weighs on you" line rests on a fact you can name, or on
  Chaehan's quoted words;
- questions: every open question names the message of Chaehan's that asks it.

## 10. The twin

Write the note with the evernote skill: "YYYY-MM-DD Life Problems" in
"Chaehan's Life", from the file that passed the gate, carrying its
`note-gate:` marker. Read it back and confirm every heading and both tables
are there. Report what is now true, what waits on Chaehan, and the files
changed.
