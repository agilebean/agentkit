---
name: life-challenges
description: Build or walk through Chaehan's dated Life Challenges note in Evernote - the deciding question, the decisions with their options, and the issues Chaehan can hand to the agent with /life. Use when the user says "life challenges", "my challenges", "untangle my issues", "what weighs on me", types /life, or asks how to tackle several life issues at once. A status snapshot of every domain is the life-overview skill.
---

# Life Challenges

One dated note, "YYYY-MM-DD Life Challenges" in the Evernote notebook
"Chaehan's Life", with its source `socrates/docs/YYYY-MM-DD-life-challenges.md`.
It is made in two passes:

1. **Build.** Write the note from the record. Chaehan reads it in Evernote.
2. **Walk-through.** `/life` takes Chaehan through the note's decisions and
   issues one at a time with the question tool and writes each answer back
   into the same note. `/life <keyword>` runs one issue.

The walk-through refines the note in place. A new build on a later day gets a
new date and leaves every earlier note untouched (RULES.md 31).

**Quality over quantity is the first rule here.** The note has the five
sections below and nothing else, and each issue appears in exactly one of
them. Drafts, call scripts and research never sit in the note: the
walk-through makes them when Chaehan asks for the issue. Every sentence passes
the seat test in `agentkit/AGENTS.md` core 1 and is written to Chaehan as
"you".

## The note

```
## Takeaway                 at most 3 bullets
## The deciding question    only when an open question changes other decisions
## Your decisions           one ### per decision
## Hand to me               one table
## Settled                  one bullet per issue settled since the last note
```

Put each issue in one section, testing in this order:

1. Done or decided since the last note: **Settled**, with its date.
2. Chaehan has not decided whether or how to do it: **Your decisions**. An
   issue the previous note listed as a task is a decision when Chaehan has not
   said to do it (booking the storage unit, when a friend could keep the
   clothes for free).
3. The next step is something you can prepare (a draft, a call script, a
   lookup, a form's values) and Chaehan only approves it: **Hand to me**.
4. A decided step that only Chaehan can take (placing a sell order): one
   Takeaway bullet with its date.

## Build

### 1. Gather

1. Read the latest `docs/*-life-overview.md`, the previous
   `docs/*-life-challenges.md` (before 2026-11-07: `docs/*-life-problems.md`),
   `memory/travel.md`, `memory/travelitinerary.csv`, and the memory file of
   each issue's domain.
2. Ask Chaehan which issues of the previous note are done since it, with the
   question tool: one multiSelect question per four issues. Never decide that
   an issue is done or open from a missing record (core 5). Write what Chaehan
   reports into the domain memory file, dated.
3. Keep an open question only when a message of Chaehan's asks it or it
   decides an action Chaehan named; ask Chaehan about any other (RULES.md 83).

### 2. Your decisions

One `###` per decision, titled by its subject ("Storage"). Under it, in order:

1. The question in your words, ending with "?": "Do you book the Gongdeok
   storage unit, or keep the clothes and papers somewhere free?"
2. A numbered list of two to four options, one line each, with what the option
   costs or gives you (money, days, effort). Add the option the record does
   not name when one exists, such as a friend or the family keeping a box.
3. One sentence starting "Your choice depends on": the fact that tips the
   choice. When the decision waits on the deciding question, this sentence
   says so.
4. At most one sentence on what makes it heavy for you, and only when that
   changes which option fits: built from a fact on record (a date, a sum, a
   person you dealt with) or your quoted words. Never a label such as
   "anxiety" or "avoidance", and never a pattern from `_psych_obs.md` stated
   as present.

The walk-through puts exactly these options into the question tool, so each
option must read as an answer Chaehan can click.

### 3. Hand to me

One table, ranked by what each issue takes off you for the effort of
starting it (`memory/optimize-my-life.md`, the scarrends principle):

`Issue | I do | You decide | Command`

- I do: what you prepare, in one line ("draft the No Response email to the
  Form 911 address").
- You decide: what Chaehan must do with it ("approve or correct the draft,
  then you send it"). Nothing goes out before Chaehan has read the final text
  (RULES.md 84).
- Command: `/life <keyword>`, one short lowercase word that names the issue
  and is unique in the note.

### 4. The deciding question

Only when the record states that one open question changes other decisions
(RULES.md 83: name the message). The section opens with the question, ending
with "?", and one bullet per answer says what follows from it.

### 5. Takeaway, last

At most three bullets, each at most 30 words, with you or an action as the
subject: the deciding question when there is one, the decision closest to its
date, and the issues you can hand over or the decided step only Chaehan can
take.

### 6. Gate and write

Write the cut list `$TMPDIR/life-challenges_cuts.md`: one line per number or
date of the previous note that this one drops, and one per issue that left,
`- <numbers or issue name>: <why it left>`. A number that belongs to an issue
still open is never world detail. Then run:

```
python ~/Software/Prototypes/agentkit/skills/life-challenges/scripts/challenges_gate.py docs/YYYY-MM-DD-life-challenges.md --original <previous note .md> --cuts $TMPDIR/life-challenges_cuts.md
```

A failure goes back to the step that made the sentence it names. A PASS
prints the `note-gate:` stamp the Evernote write needs; it proves the form,
not the content. Then read the draft once for the seat test and for any
sentence that repeats another. Write the note with the evernote skill from the
file that passed, read it back, and confirm the headings and the table.

## Walk-through (`/life`)

1. Read the latest `docs/*-life-challenges.md` and its Evernote note. When the
   note differs from the file, Chaehan edited it: carry the edit into the file
   first.
2. Go through the issues: the decisions by the date that closes them, then the
   Hand to me rows in their order. With a keyword, take only that issue.
3. For a decision, ask the question tool with the note's question and its
   options. One question per issue.
4. For a Hand to me row, do the "I do" part: write the draft or the script by
   the drafting rules (RULES.md 37, 85, 103, 111, 250) from the issue's own
   record, and show it in the chat as plain text. A social security number
   appears as its last four digits; the full number goes in when Chaehan
   sends. Then ask with the question tool: approve, correct, or skip.
5. After each answer, write it back: a decision becomes a Settled bullet with
   Chaehan's words, or a Hand to me row for its next step; an approved draft
   becomes "approved YYYY-MM-DD, you send it" in its row until Chaehan says it
   went out. Record the decision in the domain memory file, dated. Run the
   gate and write the note.
6. Stop when Chaehan says stop, or when every issue has had its question.
   Report what moved, in one line per issue.
