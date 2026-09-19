---
name: life-overview
description: Create or refresh Chaehan's dated Life Overview — whole-life status snapshot with a timeline graphic, what-went-well section, and open tasks. Use when the user says "create a life overview", "life overview", "refresh the life overview", or asks for a full status across life domains.
---

# Life Overview

A dated snapshot of the whole life state: what is fixed, what is moving, what
went well, what is open. The current snapshot is the source of truth at
`socrates/docs/YYYY-MM-DD-life-overview.md`, with a twin in the Evernote
notebook "Chaehan's Life". Run everything from the socrates repo root
(`~/Software/Prototypes/socrates`).

## Trigger

"create a life overview" / "life overview". This creates a NEW dated snapshot
and supersedes the previous one (delete the old note — rules 28 and 31).

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

## 3. Write the snapshot (structure)

- Image reference first, above the TL;DR: `![timeline](assets/YYYY-MM-DD-life-overview-timeline.png)`
- `## TL;DR` — 4-6 bullets: ⚠️ most urgent action, the chapter's fixed
  commitments, one line each for parallel workstreams and long-horizon items.
  Icons sparingly (rule 42).
- Current chapter section (e.g. "Seoul window: dates") with bold sub-labels per thread.
- `## Running in parallel` — company, health, money/admin, side work.
- `## What went well` — selection rule below.
- `## Open tasks` — table: Thread | Waiting on | Next move.

Style rules that apply: RULES.md 19 (answer first, plain words), 20 (date first
in title), 40 (anchor every time claim to today), 42 (bullets everywhere),
2 (no em dashes). No thousand separators in numbers.

## What went well — selection rule

Pick 3-5 items from the current chapter, prioritizing the ones that were
emotionally dragging: decision paralysis, scarrends (high-anxiety admin),
external dependencies, month-long loops. For each item: name the drag in plain
words, name what unstuck it (the specific decision or hand-off), and state what
is now true. Items already claimed in a previous overview stay out unless their
state changed. Record, do not cheerlead.

## 4. Evernote twin

1. Create (or update) the note with the markdown WITHOUT the image line — the
   `![...]` line converts to a dead `<img src>`. With the image as the first
   line, `tail -n +3` strips it:
   `create --markdown "YYYY-MM-DD Life Overview" "$(tail -n +3 docs/YYYY-MM-DD-life-overview.md)" --notebook "Chaehan's Life"`
2. Embed the graphic above the TL;DR:
   `embed-image "YYYY-MM-DD Life Overview" docs/assets/YYYY-MM-DD-life-overview-timeline.png --top`
   Text updates orphan the attachment; re-running embed reuses it by hash
   (idempotent), so always re-embed after a text update.
3. Verify: read the note back; `en-media` appears before the first heading; one
   resource. New notes take minutes to appear in search — use the `create`
   guid with `get <guid>` for the immediate check.
4. Supersede: search the notebook for older "Life Overview" notes and delete
   each (to trash). Only the current snapshot remains.

## 5. Report and commit

Report at headline level only (rule 28): which artifact changed, plus the
headline deltas since the last snapshot. Commit the docs, asset, and any memory
changes once the user approves (rule 46), asking "commit and push?" when the
signal is ambiguous.
