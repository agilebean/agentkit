---
name: life-challenges
description: Build or walk through Chaehan's dated Life Challenges note in Evernote - his goals, where they pull against each other, the direction to move, the open decisions with their options, and the issues Chaehan can hand to the agent with /life. Use when the user says "life challenges", "my challenges", "untangle my issues", "what weighs on me", types /life, or asks how to tackle several life issues at once. A status snapshot of every domain is the life-overview skill.
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

This note is the one home of every open decision and every next move in
Chaehan's life. The Life Overview (the life-overview skill) says where each
goal stands, links this note once, and repeats none of it; this note never
reads the Overview, so the information runs one way.

**What the note is for.** Chaehan reads it to see what he is trying to
achieve, where his goals pull against each other, and which way to move. It
does the work he cannot do in his head (`agentkit/docs/answer_quality_prompt.md`
section 1, "intelligent"): it computes what can be computed, connects one
issue to another, and ranks. It is not a feed for `/life`: the walk-through
takes its questions from the note, the note is never written for the tool.
Quality over quantity: a bullet stays only if it changes what Chaehan decides,
each fact sits in one place, and what Chaehan already knows stays out. Drafts,
call scripts and research never sit in the note. Every sentence passes the
seat test in `agentkit/AGENTS.md` core 1 and is written to Chaehan as "you".

## The note

```
## Takeaway       three bullets: what you would tell a friend who asks how it is going
## Family         one section per live goal with something open, in this order
## Home
## Money
## Health
## Work
## Hand to me     one table
## Settled        only when something settled since the last note
```

Put each issue under the goal it serves, and test it in this order:

1. Done or decided since the last note: **Settled**, with its date.
2. Chaehan has not decided whether or how to do it: a decision under its
   goal. An issue the previous note listed as a task is a decision when
   Chaehan has not said to do it (booking the storage unit, when a friend
   could keep the clothes for free).
3. The next step is something you can prepare (a draft, a call script, a
   lookup, a form's values) and Chaehan only approves it: a row in **Hand to
   me**. Its goal section says what is at stake, once, and the row carries
   the action.
4. A decided step that only Chaehan can take (placing a sell order): one
   bullet under its goal, with its date.
5. Nothing for Chaehan or the agent to do until someone else moves (a queue,
   an office's reply, a registry's portal): out of this note. The Life
   Overview states it as a thread waiting since its date.

## Build
### 1. Gather

1. Read the previous `docs/*-life-challenges.md` (before 2026-11-07:
   `docs/*-life-problems.md`), `memory/travel.md`,
   `memory/travelitinerary.csv`, and every chapter file the life-overview
   skill lists in its step 1, and take each open action they hold as an issue
   to place. Never read the Life Overview: it links this note, and a line read
   back from it looks confirmed twice (`memory/agentic_ai.md` failure 166).
   An issue the Overview's report named as missing here is placed like any
   other.
2. Ask Chaehan which issues of the previous note are done since it, with the
   question tool: one multiSelect question per four issues. Never decide that
   an issue is done or open from a missing record (core 5). Write what Chaehan
   reports into the domain memory file, dated.
3. Keep an open question only when a message of Chaehan's asks it or it
   decides an action Chaehan named; ask Chaehan about any other (RULES.md 83).

### 2. The goal sections

The live goals, as of 2026-11-07: a family, a home base in Korea, money,
health, work (`agentkit/docs/answer_quality_prompt.md` section 2, and the
memory files). A goal with nothing open gets no section. Each section holds:

1. An opening sentence: what Chaehan wants, in the record's words ("You want
   a partner to have children with: warm, emotionally intelligent ...").
2. The facts that pull against it, each with the number that measures it
   (days, money, a date) and what it costs or forecloses. Compute what the
   record lets you compute: "from 2026-12-04 you are away for 102 days", "the
   183-day line leaves ~9 days of slack, so 2027-03-07 is your earliest
   return".
3. The link to another goal when the record shows one: "the 2027-03-09
   arrival gives your search 7 more days and fits the medicine run".
4. The direction, as if-then from Chaehan's own priorities: "If a November
   date goes well, move your return toward 2027-03-07; if none does, keep
   2027-03-16."
5. Each open decision as a bullet ending with "?", with its two to four
   options indented under it, one line each with what the option costs or
   gives you. Add the option the record does not name when one exists, such
   as the family keeping a box. The walk-through asks exactly these.

What makes a decision heavy is written only when it changes which option
fits, and only from a fact on record (a date, a sum, a person you dealt with)
or Chaehan's quoted words. Never a label such as "anxiety" or "avoidance", and
never a pattern from `_psych_obs.md` stated as present.

The deciding question, when the record states that one open question changes
other decisions (RULES.md 83: name the message), is a decision bullet in the
goal it belongs to, worded "Your deciding question: ...?", with one sub-bullet
per answer saying what follows.

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

### 4. Takeaway, last

Three bullets, each at most 30 words, with you or your thing as the subject:
what you would tell a friend who asks "how is it going?". The state of the
goal that matters most this month and what it costs, the largest sum or the
nearest date and the move that settles it, and the deciding question with what
follows from it. Never a list of tasks.

### 5. Gate and write

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
2. Go through the issues: the decision bullets (ending with "?") by the date
   that closes them, then the Hand to me rows in their order. With a keyword, take only that issue.
3. For a decision, ask the question tool with the bullet's question and its
   options. One question per issue.
4. For a Hand to me row, do the "I do" part: write the draft or the script by
   the drafting rules (RULES.md 37, 85, 103, 111, 250) from the issue's own
   record, and show it in the chat as plain text. A social security number
   appears as its last four digits; the full number goes in when Chaehan
   sends. Then ask with the question tool: approve, correct, or skip.
5. After each answer, write it back: a decision becomes a Settled bullet with
   Chaehan's words (its goal section keeps what follows from it), or a Hand
   to me row for its next step; an approved draft
   becomes "approved YYYY-MM-DD, you send it" in its row until Chaehan says it
   went out. Record the decision in the domain memory file, dated. Run the
   gate and write the note.
6. Stop when Chaehan says stop, or when every issue has had its question.
   Report what moved, in one line per issue.
