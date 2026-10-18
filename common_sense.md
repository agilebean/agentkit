# Common sense inventory

The instances his corrections are built on, in two tables. Table two holds what he had to call common sense: the miss, his words, and what should have been obvious, and it gives the file its name. Table one holds what he flagged as wording: the phrasing, why he rejected it, the repair, and why the repair is better. Compiled 2026-10-03 from the KUBS DT folder logs (Course Design, S1 to S4), the session record of 2026-08-06 to 2026-10-03, and the RULES.md history; table two compiled 2026-10-12 from the session record of 2026-09-28 to 2026-10-12. The record has a gap from 2026-09-10 to 2026-09-23 (cleaned up on 09-25); the folder logs cover that window.

His words arrive through two channels, and both are searched: his messages, and his answers to the `question` tool, which are stored inside the assistant's tool results and are not user messages. A search over messages alone misses the answers - the 2026-10-12 table-width correction came in as one. The procedure sits at the foot of this file.

The user, 2026-10-03: "i gave hundreds of examples the last 3 weeks of robotic wording ... i had instructed that you keep an inventory and not only for kubs so you learn what is robotic and how to improve it!" The same standing order now covers table two, 2026-10-12: "from now on everything I said was not common sense, put all of that together", and the same day: "make sure to find all occurences of common sense i mentioned in all sessions".

The standard behind every row of table one: anything the user will read or hear must be understood on the first pass, without a pause and without asking what it means (RULES.md rule 48's test). The markers are the failures seen so far, not the whole standard. The standard behind table two: what a competent person does without being told. Every row is a thing the agent had to be told, so each names the judgment that was missing and where it now lives as a rule.

## The system

- `RULES.md` rule 2: the standing classes, each with the plain fix. The reference for the word "robotic".
- This file, table one: one row per wording instance: location and date, the flagged wording, why the user rejected it, the repair, and why the repair is better.
- This file, table two: one row per "not common sense" correction: date, what he flagged, his words, what should have been obvious, and the rule or repair it produced.
- Checker: `robot_markers.tsv` (this folder) holds the machine-checkable subset; `scripts/wording_lint.py` runs it on any file, in any project. The KUBS pipeline wraps it (`pipeline.py lint --session N`).

Maintenance: every new correction is appended at the end of its table in the same turn as one row. Table one: location and date, the flagged words, why the user rejected them (the user's words where the record has them), the repair, and why the repair is better. Table two: date, the miss, the user's words, what should have been obvious, and the rule or repair. Keep cells short: quotes are trimmed to the carrier fragment, one or two sentences per cell. A correction without the reasoning is incomplete; when the exchange carries none and the reason is not evident, ask before appending. A new class becomes a bullet in rule 2; a class a machine can catch becomes a row in `robot_markers.tsv`, checked by `scripts/wording_lint.py`.

## The user's repair instructions (standing)

- The why is the teaching (2026-10-03): "so you learn what is robotic and how to improve it". The user corrects a sentence to kill a class of mistake, not the sentence.
- Cut clutter, never the details that instruct students (2026-10-03): "you cut clutter but even more important without cutting details which are extremely important as instructions for students".
- Conciseness that keeps every fact (2026-10-03): "look for conciseness of wordings which don't lose any semantics but are more precise and concise". Earlier: "be more concise yet don't suppress any details" (2026-08-17).
- Keep the user's verbatim wording, never reformulate it (2026-09-29): "keep this, don't reformulate. i gave it to you so you learn not only about less robotic wording, but also the order of saying things". The user's wording also wins over the agent's shortened version: "students will complain if it's not clear. use my wording" (2026-10-01).
- Answer first, reasoning after (2026-08-23): "after the decision, the tentative answer should already be given right after, not at the end. after that, you can explain all the reasoning."
- Plain short form: "team exercise", "the three filters", "how it works", "the drawing is not what counts".
- One voice, the user's: "tell us (i am the prof, not we)" (2026-10-01).
- The instructor script carries what the user will say and when; it is a reminder for the user, not a report. Rules already announced elsewhere are not reiterated (2026-10-02, 2026-10-03).
- Two corrections on one subject store the learning (2026-10-18): "now i want an automatic detection after i corrected 2x or more your response wording or your precision that you store automatically the learning from that using exactly the previous wording I found good ... so in the future i shouldn't tell you that any more". Wording goes to table one with the accepted version verbatim, a procedural miss to the socrates register, and the records commit in the same session (rule 174).

## The wording instances

The rows of Chaehan's wording corrections, and the corrections he had to call common sense, are in socrates `agent/wording cases.md`. They are private because they quote his notes; search them with grep.
