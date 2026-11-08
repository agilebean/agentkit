---
name: life-overview
description: Create or refresh the user's dated Life Overview — whole-life status snapshot with a timeline graphic, what-went-well section, and one link to the Life Challenges note, which holds the open decisions and next moves. Use when the user says "create a life overview", "life overview", "refresh the life overview", or asks for a full status across life domains.
---

# Life Overview

A dated snapshot of the whole life state: what is fixed, what is moving, what
went well, and what waits on someone else. Every open decision and every next
move lives in the current Life Challenges note (the life-challenges skill),
and this note links it once and repeats none of it. The two notes run on
different clocks: this one is frozen on its date, while `/life` rewrites the
Challenges note in place, so a task list here goes stale the day a task
closes. On 2026-11-06 the Life Problems note repeated 11 of the 2026-11-05
overview's issues, and an agent's question listed in both was taken as
Chaehan's (`memory/agentic_ai.md` failure 166).

The current snapshot is the source of truth at
`socrates/docs/YYYY-MM-DD-life-overview.md`, with a twin in the Evernote
notebook "Chaehan's Life". Run everything from the socrates repo root
(`~/Software/Prototypes/socrates`).

## Trigger

"create a life overview" / "life overview". This creates a NEW dated snapshot.
Every earlier snapshot, note and local file, stays untouched: a dated snapshot
records what Chaehan believed on that date and is never superseded, folded,
trashed or renamed (RULES.md 31). A rework of today's draft keeps today's date;
a rework on a later day issues a new date. The local file and the note have
the same title stem (`docs/YYYY-MM-DD-life-overview.md` for "YYYY-MM-DD Life
Overview"); no `-NEW` or `v2` suffix.

## 1. Gather state

Read, in order — memory is ground truth (rule 35):

- `memory/travelitinerary.csv` — stay windows; travel days need the user's report (rule 18)
- `memory/_psych_obs.md` — emotional-drag patterns; feeds What went well
- `memory/travel.md` — stay, housing, exit decisions
- then the chapter files: `kubs.md`, `health.md`, `swim.md`, `partner-search.md`,
  `dating.md`, `furniture-relocation.md`, `src_shipping_ca2korea.md`, `finance.md`,
  `taxes_us.md`, `immigration.md`, `virtualfriend.md`, `virtualfriend-marketing.md`,
  `virtualfriend-architecture.md`, `startup.md`, `optimize-my-life.md`
- `git log --oneline -15` — what moved since the last overview
- from each chapter file, read its current state and your dated words; skip
  its research, evidence and study sections, which serve questions asked on
  demand and only crowd the reading
- the calendar, for the date of every event the note names (a date, a flight,
  a deadline):
  `mamba run -n socrates python projects/applecalendar/src/applecalendar_api.py events --past 14 --days 56`
  from the socrates root. It reads the macOS Calendar database read-only and
  returns one row per occurrence, so a recurring session already appears on
  each of its dates, and it drops the weather, birthday and suggestion
  calendars unless you pass `--all-calendars`. `--past 14` adds the fortnight
  behind today, so an appointment that has already happened is written as
  something you did and never as upcoming. The KUBS prep-hours ledger
  keeps its own raw sweep, `memory/kubs.md`. Every event in the note has one
  date, with or without the calendar: a relative or modal phrase in the record
  ("date after 5d", "soon") is never paraphrased or recomputed into a date;
  it is quoted with the date Chaehan said it, or the event goes without a
  date (RULES.md 17). Every fact comes from one record line about that event;
  two lines about different matters are never joined into a new fact, such as
  a helper, a cause or a payment.
- OmniFocus, for every dated task Chaehan has taken on:
  `mamba run -n socrates python projects/omnifocus/src/omnifocus_api.py due --days 56 --past 14`,
  the same command with `--overdue` for what is already late, and
  `... done --days 14` for what Chaehan finished. A task completed in that window
  is done even where a memory file still lists it open, and it never enters
  this note as an issue. A task with a due date that appears in no
  memory file is a commitment the note would otherwise miss, and it enters
  the section its project belongs to; one that fell due in the past fortnight
  and is still open is what slipped. A task with no due date has no date and
  never becomes one.
- the current Life Challenges note, read in Evernote and exported to a file
  (newest "YYYY-MM-DD Life Challenges"; before 2026-11-07 "YYYY-MM-DD Life
  Problems"), because `/life` writes its answers there: it names the issues
  this note states in one sentence and links, and its Settled bullets are
  candidates for What went well. An open action the memory files hold and the
  Challenges note does not is named in the report to Chaehan as missing there,
  never written into this note.
- the human side of the chapter, which the open items never show (RULES.md
  105): your academic CV (`~/Library/CloudStorage/GoogleDrive-chaehan.so@virtualfriend.chat/My Drive/1 Projects/KUBS/KUBS DT/KUBS DT S1/CV academic Chaehan So 2026.pdf`,
  read with `markitdown`) for what a step means against your career; the swim
  panels (`~/Software/Prototypes/swim/data/dashboard_payload.json`) and
  `memory/swim.md` for your measured progress; the accommodation prices in
  `memory/travel.md` against what you spent elsewhere; `memory/_psych_obs.md`
  and your own quoted words in the chapter files for what a step cost you. A
  measured gain is compared with your own baseline and with a published
  benchmark for a good performer when a study gives one, found by web search
  and cited by its source.

Then, for every item the memory files call open, search Evernote for the result
before it reaches the note (RULES.md 207): the test, the form, the booking. A
memory line can be older than the record, and publishing it as open is a false
statement about the user's life. The result moves the item to done with its date
and numbers, and the missing line goes into the topic's memory file in the same
pass.

Every cost and hour figure is recomputed in that pass from the record's own
parts, never copied with its label left behind (RULES.md 208). A total and its
parts are added up against each other, and the sentence says what the figure
contains (what the total covers, and per what), never an average whose scope
sits in another file. A cost or hour figure enters the note only where it is
the point of its sentence.

Each overview claim carries its file and date before a draft is shown.

## 2. Timeline graphic (required, top of the note)

1. Copy the spec shape from the previous run: `docs/assets/<date>-life-overview-timeline.json`.
2. Update the rows to the current chapter, for a phone screen, which is where
   Chaehan reads the note. The chart starts at the earliest item of What went
   well, so the past chapter shows: each achievement is a green done diamond
   on its date with a short label ("DPS 1.01 m", "J Noble signed", "KUBS
   course"), and a breakthrough is never left off. At most five lanes, in the
   order of the note: partner search, health (the frozen sample first), work,
   then logistics: where you are (the stay and travel blocks) and one "Dates"
   lane for single dates such as a filing or a sale. Every label says what and how
   long or what happened ("Melbourne 79 nights", never "Melbourne" alone);
   the title says in at most 40 characters what the chart shows; labels are at
   most 22 characters, with no booking detail and no abbreviation ("7 nights",
   never "7n"). Styles: solid = booked or fixed, open = conditional, diamond =
   milestone (green done, hollow open), red diamond = decision. The renderer
   picks the lane colours, shades neighbouring bars apart and places every
   label, so `color`, `text_pos` and `offset` are ignored.
3. Render:
   `mamba run -n socrates python ~/Software/Prototypes/agentkit/skills/life-overview/scripts/life_timeline.py <spec.json> docs/assets/YYYY-MM-DD-life-overview-timeline.png`
4. Inspect the PNG before embedding at phone width: read it at 390 px wide.
   A label you cannot read, a collision, or a lane that adds nothing a reader
   needs is cut from the spec, and the chart is rendered again.

## 3. Write the snapshot: four moves, in this order

Every element this skill asks for (a reason, a consequence, a reversing fact,
a helper, a benchmark) comes from a line of the record about that same
matter. When the record holds none, the element is left out, and the note is
right without it; an element made up to fill the place is the one way the
note can be wrong.

Relevance is impact on a goal Chaehan is pursuing or a decision Chaehan has
pending: the family, the base in Korea, health, money, work (the live goals
are listed in `memory/` and in the brief behind this skill,
`agentkit/docs/answer_quality_prompt.md` section 2), or something Chaehan
achieved in the chapter, in any domain, swimming included. A cost is a symptom of
that impact, not its definition. A fact that touches no live goal and no
pending decision is one line in its section or out. Do the moves in order and
write each product down before the next move. The What went well section is
written first, right after the gather and before Move 1, by its own rule
below, while the record is fresh; the Takeaway is written last.

Order is Chaehan's priority from Chaehan's own seat, highest first, and it is
obvious at a glance ("Life priorities" in `memory/optimize-my-life.md`):
partner search always first, then health (the frozen sample first in it),
then work, then logistics (the route and stays, storage, furniture, money and
filings). Every list in the note follows that order: the Takeaway bullets, the
What went well items, the sections and the chart's lanes. Within a block,
what bites sooner comes first.

**Move 1. One sentence per live goal: where it stands now.** For each goal
the record touches, write the sentence Chaehan would say to a friend: "The
search is signed with J Noble, and one date has not told you whether the age
gap is the problem." Its subject is Chaehan's decision, body, money or time,
never the agency, the contract or the file. A closed door is written as
Chaehan's decision and its consequence; a refusal as what remains open.

**Move 2. Under each sentence, the facts that change it.** At most three per
goal, each a fact that would move the sentence if it were different, plus the
fact that would reverse it when the record states one, written as a plain
fact among the others and never labelled ("What would reverse the sentence:
..."). When the record states none, the section has none. A fact that belongs
under another fact is indented under it as a sub-bullet, never set beside it,
so each section shows its facts with their details under them. An event the
section reports (a flare, a date, an injury) is written with its date.

**Move 3. Every remaining fact is detail, and gets its note.** For each
section, find its detail note (`find-note`, then the link form in the
`evernote` skill: `[<exact title>](evernote:///view/39d2f74/s365/<guid>/<guid>/)`).
The section shows the state in one sentence, its consequence when the record
or the dates make it plain, and that link. No figure that lives in the linked note appears above the link.
A booking shows what it fixes for you: where you are from when to when, and
what is still unbought. Its flight number, fare, seat fee, booking date and
cancellation terms live in its detail note.
A section with no detail note says "no detail note" and keeps its facts. Do
not compress Chaehan's facts: dates, numbers, decisions and constraints stay,
here or in the linked note. Only world detail (study design, vendor prose,
public rules) may leave the page.

An issue the Life Challenges note holds, an open decision or a step Chaehan
can take or hand over, takes that note as its detail note. Its section says
where the issue stands and what is still Chaehan's, one sentence each, and
links the Challenges note; the options, the contacts (phone numbers, email
addresses), the scripts and the steps themselves stay there. "You must still
book a locker for your winter clothes" belongs here; the unit, its price and
the booking link belong in the Challenges note. A thread that waits on someone
else (an office's reply, a queue, a registry) is state: it stays in its
section with the date it has waited since, and names no next move.

A decision the Challenges note holds appears here by its subject alone ("the
Osaka landing is still open"), never with its options, the dates of its
options, its costs or its if-then branches, and never through an earlier Life
Problems or Life Challenges note: the current one is the only home of a next
move.

**Move 4. The Takeaway, last, from moves 1 and 2.** Four to six bullets: what
Chaehan would say to a friend who asks "how is it going?", in priority order.
The bullets follow the order above: partner search first, then health (the
frozen sample first), work, then logistics, one bullet per block even when
nothing moved in it; each says where that block stands and what you achieved
in it when there is something. Between them they
cover what the next month depends on, what is settled, what changed (with its
reason when the record gives one),
and what gets worse if left alone. That list is the content, never the
wording: no bullet names its own function. Each bullet opens on Chaehan or
Chaehan's thing doing something, in the words Chaehan would say aloud, and
names every object it points at.

<!-- verbatim -->
- Accepted (2026-11-05): "You fly to Osaka on 2026-12-04, in 29 days, and every flight is booked except the return from Osaka to Seoul in March." Later the same day: "you must still book a locker for your winter clothes" and "it is unclear if Gayeon provides women of my target age or none like couple.net, so you didn't book it yet".
- Accepted (2026-11-08), a juxtaposition in plain words: "You don't buy a Seoul apartment until a marriage is decided, so the stay from 2027-03-16 is a rental." Chaehan: "this is exactly what i want, a juxtaposition with no robotic wording but still concise. mind: buy no... is unnatural, better: don't buy."
- Rejected (2026-11-08): "What you want in a partner has not changed" ("i never said i wanted or expected it to change, nor is change normal for romantic preferences"), "What would reverse the sentence: ..." ("terrible robotic!"), "nothing is left for you to do on them" (clutter), "the manager's blurb", and "off gluten since 2026-10-19" for a diet of 25 years.
- Rejected: "The next month turns on ...", "What changed since the last snapshot is ...", "The KUBS grade entry is the one deadline this week", "The route is fixed until Valencia ...", "Money keeps one clock", "the daily tablet" with no name for the tablet, "Your winter clothes and the green card papers have no home in Seoul", and "The question it cannot answer ... goes to the Gayeon free consult, which is not booked". `scripts/wording_lint.py` flags these shapes.
<!-- end verbatim -->

Each bullet names its objects so a stranger knows which: "the flat you leave
has to be emptied" does not say what goes where, and "you must still book a
locker for your winter clothes" does.

It is not a task list: a bullet that a decision or a Hand to me row of the
Life Challenges note could replace without losing its consequence is rewritten
or cut. The actions live in that note.

**Layout.** Image line first, then `## Takeaway`, `## What went well`, then
one `##` section per goal in priority order (the route and the stays
take their place in that order, never the top by default), and
`## Your decisions`: one sentence that links the current Life Challenges note
by its exact title, "Your open decisions and the steps you can hand to me are
in [<exact title>](evernote:///view/...)." The note has no task table. Rules that apply: 19,
20 (date first in title), 40 (anchor time claims to today: an event has one
date; a relative phrase stays inside its quote with the date it was said, and
a span such as "over three months" is computed from the dates of the cause it
names, or left out), 42 (bullets), 2
and `scripts/wording_lint.py`; no thousand separators. The note is written to
Chaehan as "you", which is necessary and not sufficient: the seat test in
`AGENTS.md` core 1 is the check. The previous snapshot is a reference for the
timeline spec only, never for voice, selection or section content: copying it
reintroduces its defects (`memory/agentic_ai.md` failure 104). A rework of
today's draft never reads the draft it replaces, because that draft holds the
defects the rework is for: it writes every section again from the record.

## 3a. The gate (runs on the finished draft, before the twin)

One command and one read. A failure goes back to the move that wrote the
sentence it names, never to the twin.

`python ~/Software/Prototypes/agentkit/skills/life-overview/scripts/overview_gate.py docs/YYYY-MM-DD-life-overview.md --challenges <exported Life Challenges note>`

- T3: no Open tasks section, no email address and no phone number; a link to
  the Life Challenges note; and no Takeaway bullet that repeats one of its
  decisions or Hand to me rows.
- T4: every section has a link to its detail note or says "no detail note".
- T5: at least one indented bullet; indent every fact that belongs under its
  neighbour.
- T18: no number with a thousand separator ("10000000 won").

Its PASS prints the `note-gate:` stamp the Evernote write needs. Then read the
draft once against Move 4 and the seat test in `AGENTS.md` core 1, and rewrite
any sentence whose subject is not you or your thing.

When this skill changes, run a fresh case in opencode on DeepSeek with this
skill only, time it, and read its note against the change.

## What went well — retell the record, add nothing

What went well retells what the record already says you did. It is built in
two steps, and the second step never adds what the first did not find.

1. **Find the lines.** In the memory files, find the lines where your own
   words call a step of this chapter an accomplishment, a breakthrough or
   something done ("my accomplishment to finish my first course at a top
   university Korea's after I retired from yonsei", "a huge breakthrough with
   partner search", "several breakthroughs in swimming"), and the lines that
   record a first or a measured gain dated after the previous overview. Copy them into
   `sources.md` beside the draft, one block per item: the file, the line
   number and the line itself. Every step you named yourself gets a block;
   three to five blocks in all, in priority order.
2. **Retell each block.** Write one or two sentences to you that say what the
   lines in its block say: what you did and what it took from you, in plain
   words, quoting you only for a word of yours that holds the point
   ("scarrend"). A person, a cause, a cost, a date or a number that is not in
   the block's lines is not in the item. Most items name no helper; an item
   names a person only when a line in its block names that person for this
   step. A measured gain may add one benchmark from a study you cite, in one
   clause with the shortest reference ("around the DPS of elite women
   swimmers (Staunton 2025)"), converted into your unit (DPS per single-arm
   stroke: a per-cycle value is halved) and given only in it.

An item that says only what its lines say is complete. Leaving something out
is never a failure; inventing it always is. Counts of students, sessions,
lectures or hours stay out. Each number keeps the term of its measure
("perceived effort 8, now 6", never "two-thirds of the effort"). Items already
claimed in a previous overview stay out unless their state changed. Record,
do not cheerlead.

## 4. Evernote twin

In-session, every Evernote operation goes through the MCP tools (the
`evernote` skill is authoritative): `create_note` in the "Chaehan's Life"
notebook; the body added with `edit_note` (`append`), converting the markdown
locally first with `markdown_to_enml` from `projects/evernote/src/enml.py`
(drop the image line and strip the `<en-note>` wrapper); the chart embedded
with the upload bridge documented in the `evernote` skill
(`start_attachment_upload`, GCS upload, `finalize_attachment`, then `edit_note`
`prepend`). The `execute` code that creates or appends the body carries the
line `// note-gate:<sha>` that the gate printed on its PASS, or the note-gate
plugin refuses the write. No earlier snapshot is deleted (section Trigger). The CLI
commands below are the outside-session fallback; in a session they are not
used (the user's "never use the cli fallback", 2026-09-26).

1. Create (or update) the note with the markdown WITHOUT the image line — the
   `![...]` line converts to a dead `<img src>`. With the image as the first
   line, `tail -n +3` strips it:
   `create --markdown "YYYY-MM-DD Life Overview" "$(tail -n +3 docs/YYYY-MM-DD-life-overview.md)" --notebook "Chaehan's Life"`
2. Embed the graphic above the Takeaway:
   `embed-image "YYYY-MM-DD Life Overview" docs/assets/YYYY-MM-DD-life-overview-timeline.png --top`
   Text updates orphan the attachment; re-running embed reuses it by hash
   (idempotent), so always re-embed after a text update.
3. Verify: read the note back; `en-media` appears before the first heading; one
   resource; its text matches the file by hash; the raw read shows one
   `evernote:///view/` per linked section. The twin is written from the text
   that passed the gate: the hash proves the copy, the gate proves the text, and
   neither replaces the other. New notes take minutes to appear in search — use
   the `create` guid with `get <guid>` for the immediate check.

## 5. Report and commit

Report at headline level only (rule 28): which artifact changed, plus the
headline changes against the previous snapshot, plus each open action the
Challenges note is missing (step 1), for the next `/life` or Challenges build. Commit the docs, asset, and any memory
changes once the user approves (rule 46), asking "commit and push?" when the
signal is ambiguous.
