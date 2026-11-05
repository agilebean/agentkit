---
name: life-overview
description: Create or refresh the user's dated Life Overview — whole-life status snapshot with a timeline graphic, what-went-well section, and open tasks. Use when the user says "create a life overview", "life overview", "refresh the life overview", or asks for a full status across life domains.
---

# Life Overview

A dated snapshot of the whole life state: what is fixed, what is moving, what
went well, what is open. The current snapshot is the source of truth at
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
- `memory/_misc.md` — parking lot; scan for promotion candidates (rule 34)
- `memory/travel.md` — stay, housing, exit decisions
- then the chapter files: `kubs.md`, `health.md`, `swim.md`, `partner-search.md`,
  `dating.md`, `furniture-relocation.md`, `src_shipping_ca2korea.md`, `finance.md`,
  `taxes_us.md`, `immigration.md`, `virtualfriend.md`, `virtualfriend-marketing.md`,
  `virtualfriend-architecture.md`, `startup.md`, `optimize-my-life.md`
- `git log --oneline -15` — what moved since the last overview

Then, for every item the memory files call open, search Evernote for the result
before it reaches the note (RULES.md 207): the test, the form, the booking. A
memory line can be older than the record, and publishing it as open is a false
statement about the user's life. The result moves the item to done with its date
and numbers, and the missing line goes into the topic's memory file in the same
pass.

Every cost and hour figure is recomputed in that pass from the record's own
parts, never copied with its label left behind (RULES.md 208). A total and its
parts are added up against each other, and the sentence says what the figure
contains: "15.78 hours for each of the eight lectures, the pre-course reading and
the course-level work included", not an average whose scope sits in another
file.

Each overview claim carries its file and date before a draft is shown.

## 2. Timeline graphic (required, top of the note)

1. Copy the spec shape from the previous run: `docs/assets/<date>-life-overview-timeline.json`.
2. Update the rows to the current chapter: stay/housing blocks, the fixed work
   course, the top open item with its target milestone, partner search, travel out.
   Styles: solid = booked/fixed, open = conditional, diamond = milestone,
   red diamond = decision.
3. Render:
   `mamba run -n socrates python ~/Software/Prototypes/agentkit/skills/life-overview/scripts/life_timeline.py <spec.json> docs/assets/YYYY-MM-DD-life-overview-timeline.png`
4. Inspect the PNG before embedding (dates line up, no overlapping labels).
   Per-item fixes: bar `text_pos` ("center"/"below"/"above"/"right"), milestone
   `offset` ("above"), narrow-bar short labels. Rerender until clean.

## 3. Write the snapshot: four moves, in this order

Relevance is impact on a goal Chaehan is pursuing or a decision Chaehan has
pending: the family, the base in Korea, health, money, work (the live goals
are listed in `memory/` and in the brief behind this skill,
`agentkit/docs/answer_quality_prompt.md` section 2). A cost is a symptom of
that impact, not its definition. A fact that touches no live goal and no
pending decision is one line in its section or out. Do the moves in order and
write each product down before the next move; the Takeaway is written last.

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
A section with no detail note says "no detail note" and keeps its facts. Do
not compress Chaehan's facts: dates, numbers, decisions and constraints stay,
here or in the linked note. Only world detail (study design, vendor prose,
public rules) may leave the page.

**Move 4. The Takeaway, last, from moves 1 and 2.** Four to six bullets: what
Chaehan would say to a friend who asks "how is it going?". Between them they
cover what the next month depends on, what is settled, what changed and why,
and what gets worse if left alone. That list is the content, never the
wording: no bullet names its own function. Each bullet opens on Chaehan or
Chaehan's thing doing something, in the words Chaehan would say aloud, and
names every object it points at.

<!-- verbatim -->
- Accepted (2026-11-05): "You fly to Osaka on 2026-12-04, in 29 days, and every flight is booked except the return from Osaka to Seoul in March." / "What you want in a partner has not changed." Later the same day: "you must still book a locker for your winter clothes" and "it is unclear if Gayeon provides women of my target age or none like couple.net, so you didn't book it yet".
- Rejected: "The next month turns on ...", "What changed since the last snapshot is ...", "The KUBS grade entry is the one deadline this week", "The route is fixed until Valencia ...", "Money keeps one clock", "the daily tablet" with no name for the tablet, "Your winter clothes and the green card papers have no home in Seoul", and "The question it cannot answer ... goes to the Gayeon free consult, which is not booked". `scripts/wording_lint.py` flags these shapes.
<!-- end verbatim -->

It is not a task list: a bullet that an Open tasks row could replace without
losing its consequence is rewritten or cut. The actions live in the task table.

**Layout.** Image line first, then `## Takeaway`, the current chapter section,
`## Running in parallel` with one `###` per goal, `## What went well`, and
`## Open tasks` (Thread | When | Waiting on | Next move). Rules that apply: 19,
20 (date first in title), 40 (anchor time claims to today), 42 (bullets), 2
and `scripts/wording_lint.py`; no thousand separators. The note is written to
Chaehan as "you", which is necessary and not sufficient: the seat test in
`AGENTS.md` core 1 is the check. The previous snapshot is a reference for the
timeline spec only, never for voice, selection or section content: copying it
reintroduces its defects (`memory/agentic_ai.md` failure 104).

## 3a. The gate (runs on the finished draft, before the twin)

Seven checks. Each names the sentence it rejects; a check that cannot name one
has not run. A failing draft goes back to the move that produced the sentence,
never to the twin.

Mechanical, T3 to T6:

`python ~/Software/Prototypes/agentkit/skills/life-overview/scripts/overview_gate.py docs/YYYY-MM-DD-life-overview.md --original docs/<previous snapshot>.md --linked <exported detail notes>`

- T3 no Takeaway bullet repeats an Open tasks row. The script catches literal repeats only; a paraphrased task passes it. So also read each bullet against the table: a bullet that a row could replace without losing its consequence is rewritten. Then read the bullets aloud: a reader can tell what the month depends on, and no bullet says so in those words (Move 4).
- T4 every body section has its link or says "no detail note"; the note has at least one link.
- T5 at least one indented bullet; read each top-level bullet and indent any that belongs under its neighbour.
- T6 every date and number of the previous snapshot survives in the draft or in a linked note, unless the record shows it is done or replaced. List each one the script reports and say which it is.

Read by the agent, quoting the sentence:

- T1 seat: name every sentence whose subject is the agency, a study, a document or the research path, and every sentence that could be sent unchanged to a stranger. Rewrite each.
- T2 gist: for each section, name its conclusion, its two or three deciding facts and its reversing fact. A section where the reader has to work these out is rewritten.
- T7 weak reader: when this skill changes, run a fresh case through the installed model (`opencode run`, the socrates agent) with this skill only, and run the mechanical gate on its output.

## What went well — selection rule

Pick 3-5 items from the current chapter, prioritizing the ones that were
emotionally dragging: decision paralysis, scarrends (high-anxiety admin),
external dependencies, month-long loops. For each item: name the drag in plain
words, name what unstuck it (the specific decision or hand-off), and state what
is now true. Items already claimed in a previous overview stay out unless their
state changed. Record, do not cheerlead.

## 4. Evernote twin

In-session, every Evernote operation goes through the MCP tools (the
`evernote` skill is authoritative): `create_note` in the "Chaehan's Life"
notebook; the body added with `edit_note` (`append`), converting the markdown
locally first with `markdown_to_enml` from `projects/evernote/src/enml.py`
(drop the image line and strip the `<en-note>` wrapper); the chart embedded
with the upload bridge documented in the `evernote` skill
(`start_attachment_upload`, GCS upload, `finalize_attachment`, then `edit_note`
`prepend`). No earlier snapshot is deleted (section Trigger). The CLI
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
headline changes against the previous snapshot. Commit the docs, asset, and any memory
changes once the user approves (rule 46), asking "commit and push?" when the
signal is ambiguous.
