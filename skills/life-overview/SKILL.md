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
- `memory/_psych_obs.md` — emotional-drag patterns; feeds What you achieved
- `memory/_misc.md` — parking lot; scan for promotion candidates (rule 34)
- `memory/travel.md` — stay, housing, exit decisions
- then the chapter files: `kubs.md`, `health.md`, `swim.md`, `partner-search.md`,
  `dating.md`, `furniture-relocation.md`, `src_shipping_ca2korea.md`, `finance.md`,
  `taxes_us.md`, `immigration.md`, `virtualfriend.md`, `virtualfriend-marketing.md`,
  `virtualfriend-architecture.md`, `startup.md`, `optimize-my-life.md`
- `git log --oneline -15` — what moved since the last overview
- the current Life Challenges note, read in Evernote and exported to a file
  (newest "YYYY-MM-DD Life Challenges"; before 2026-11-07 "YYYY-MM-DD Life
  Problems"), because `/life` writes its answers there: it names the issues
  this note states in one sentence and links, and its Settled bullets are
  candidates for What you achieved. An open action the memory files hold and the
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
  benchmark for a good performer, found by web search and cited by its source.

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
   Chaehan reads the note. At most five lanes: where you are (the stay and
   travel blocks), the goals with a dated item (partner search, work), and one
   "Dates" lane for single dates such as a filing, a sale or a decision. The
   title says in at most 40 characters what the chart shows ("Your winter away
   and the March return"); lane labels and item texts are at most 18
   characters (place names, "4 dates", "Applied AI starts"), with no booking
   detail and no abbreviation ("7 nights", never "7n"). Styles: solid = booked or fixed, open = conditional, diamond =
   milestone (green done, hollow open), red diamond = decision. The renderer
   picks the lane colours and places every label, so `color`, `text_pos` and
   `offset` are ignored.
3. Render:
   `mamba run -n socrates python ~/Software/Prototypes/agentkit/skills/life-overview/scripts/life_timeline.py <spec.json> docs/assets/YYYY-MM-DD-life-overview-timeline.png`
4. Inspect the PNG before embedding at phone width: read it at 390 px wide.
   A label you cannot read, a collision, or a lane that adds nothing a reader
   needs is cut from the spec, and the chart is rendered again.

## 3. Write the snapshot: four moves, in this order

Relevance is impact on a goal Chaehan is pursuing or a decision Chaehan has
pending: the family, the base in Korea, health, money, work (the live goals
are listed in `memory/` and in the brief behind this skill,
`agentkit/docs/answer_quality_prompt.md` section 2), or something Chaehan
achieved in the chapter, in any domain, swimming included. A cost is a symptom of
that impact, not its definition. A fact that touches no live goal and no
pending decision is one line in its section or out. Do the moves in order and
write each product down before the next move; the Takeaway is written last.

Order is Chaehan's priority, highest first, and it is obvious at a glance:
Chaehan's stated order in `memory/optimize-my-life.md` ("Life priorities") leads,
and the rest follows by how soon it bites and what it costs if left alone.
Every list in the note follows that order: the Takeaway bullets, the What you
achieved items and the sections.

**Move 1. One sentence per live goal: where it stands now.** For each goal
the record touches, write the sentence Chaehan would say to a friend: "The
search is signed with J Noble, and one date has not told you whether the age
gap is the problem." Its subject is Chaehan's decision, body, money or time,
never the agency, the contract or the file. A closed door is written as
Chaehan's decision and its consequence; a refusal as what remains open.

**Move 2. Under each sentence, the facts that change it.** At most three per
goal, each a fact that would move the sentence if it were different, plus the
one fact that would reverse it. A fact that belongs under another fact is
indented under it as a sub-bullet, never set beside it.

**Move 3. Every remaining fact is detail, and gets its note.** For each
section, find its detail note (`find-note`, then the link form in the
`evernote` skill: `[<exact title>](evernote:///view/39d2f74/s365/<guid>/<guid>/)`).
The section shows the state in one sentence, the consequence in one sentence,
and that link. No figure that lives in the linked note appears above the link.
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
The first bullets are the "Life priorities" in `memory/optimize-my-life.md`,
one bullet each and in that order, even when nothing moved in one; each says
where that priority stands and what you achieved in it when there is
something. Between them they
cover what the next month depends on, what is settled, what changed and why,
and what gets worse if left alone. That list is the content, never the
wording: no bullet names its own function. Each bullet opens on Chaehan or
Chaehan's thing doing something, in the words Chaehan would say aloud, and
names every object it points at.

<!-- verbatim -->
- Accepted (2026-11-05): "You fly to Osaka on 2026-12-04, in 29 days, and every flight is booked except the return from Osaka to Seoul in March." / "What you want in a partner has not changed." Later the same day: "you must still book a locker for your winter clothes" and "it is unclear if Gayeon provides women of my target age or none like couple.net, so you didn't book it yet".
- Rejected: "The next month turns on ...", "What changed since the last snapshot is ...", "The KUBS grade entry is the one deadline this week", "The route is fixed until Valencia ...", "Money keeps one clock", "the daily tablet" with no name for the tablet, "Your winter clothes and the green card papers have no home in Seoul", and "The question it cannot answer ... goes to the Gayeon free consult, which is not booked". `scripts/wording_lint.py` flags these shapes.
<!-- end verbatim -->

Each bullet names its objects so a stranger knows which: "the flat you leave
has to be emptied" does not say what goes where, and "you must still book a
locker for your winter clothes" does.

It is not a task list: a bullet that a decision or a Hand to me row of the
Life Challenges note could replace without losing its consequence is rewritten
or cut. The actions live in that note.

**Layout.** Image line first, then `## Takeaway`, `## What you achieved`,
then one `##` section per goal in priority order (the route and the stays
take their place in that order, never the top by default), and
`## Your decisions`: one sentence that links the current Life Challenges note
by its exact title, "Your open decisions and the steps you can hand to me are
in [<exact title>](evernote:///view/...)." The note has no task table. Rules that apply: 19,
20 (date first in title), 40 (anchor time claims to today: a relative time in
the record, such as "in five days" written on 2026-11-06, becomes its date or
is recomputed from today, and a span such as "over three months" is computed
from the dates of the cause it names, or left out), 42 (bullets), 2
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

Its PASS prints the `note-gate:` stamp the Evernote write needs. Then read the
draft once against Move 4 and the seat test in `AGENTS.md` core 1, and rewrite
any sentence whose subject is not you or your thing.

When this skill changes, run a fresh case in opencode on DeepSeek with this
skill only, time it, and read its note against the change.

## What you achieved — selection rule

Three to five items, found in the whole record of the chapter, never in the
open items, in priority order. An achievement Chaehan named himself in the
record during the chapter (Chaehan's words calling it an accomplishment or a
breakthrough, in the memory files) is always one of them; the others are
chosen around it. Each is one of three kinds:

- a first: something you had not done before, or not since a break your
  record names (your CV and the chapter files show it);
- a plateau broken: a measured value that moved after a flat stretch, given as
  the number before and after, against your own baseline and against a
  published benchmark for a good performer, with its source. The comparison
  is made in your unit, never in the study's: the swim panels give DPS per
  single-arm stroke (`swim/src/swim/dashboard/payload.py`, counted cycles
  times two), so a published value per arm cycle is halved before it is
  compared (a study's 1.95 m per cycle is 0.98 m per stroke), and your own
  number is never converted. The sentence gives only the converted value,
  never the study's own unit;
- a drag overcome: a step your record shows was hard for you (a failure
  behind it, a fear, a habit such as frugality, a scarrend), with what it took
  from you. Name the earlier failure that made the step a risk. Name the
  habit the step went against, in the record's own terms: your low-price
  accommodation choices in `memory/travel.md` show frugality, so the step is
  one you took against your frugality; never set the example's price against
  the step's. Name who helped and how, in your own words from the chapter
  file, never in an earlier overview's.

For each item: what you did, what it took from you, and what it makes
possible now, in two or three sentences addressed to you, with its detail
note linked. Counts of students, sessions, lectures or hours stay out: they
say how big the job was, never what it meant to you. Each number keeps the
term of its measure: "perceived effort 8,
now 6", never "two-thirds of the effort"; DPS, stroke rate and CSS by their
names. Each phrase makes a claim. A claim the reader cannot picture gets its
facts: "your 400 m went from 8:08 on 2026-09-07 to 8:04 on 2026-10-16", never
"you hold the same 400 m time". A phrase that makes no claim leaves: "across
eight sessions and graded the course to a close" says nothing about what the
course means to you. Items already claimed in a previous overview stay out
unless their state changed. Record, do not cheerlead.

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
