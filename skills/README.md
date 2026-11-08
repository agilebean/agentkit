# Skills

A documentation map for every skill Chaehan owns. Two families exist, and only
the first is ours to edit.

| Family | Lives in | Edited |
|---|---|---|
| This repo, one folder per skill, symlinked to `~/.agents/skills/<name>` | `agentkit/skills/<name>/` | yes, here |
| An upstream collection (writing, TDD, triage, prototyping, handoff, grill-me, caveman, diagnose, find-skills, zoom-out and their kin) | plain folders in `~/.agents/skills/`, installed by `setup-matt-pocock-skills` | no, they carry their own docs |

## The rule

A skill is one folder. `SKILL.md` is the instruction, read end to end before
the first tool call; anything else in the folder supports it and is read only
when the instruction sends you there. Files beside a skill: `scripts/` for the
commands it runs, `briefs/` for Evernote note templates, `reference.md` for a
long lookup table.

Where a skill calls code that lives in another repo, that code keeps its own
README beside it and the skill names the command line only. Never restate the
code's design in the skill: the project README is the source and drifts first.

## The skills

| Skill | What it does | Detail and code |
|---|---|---|
| `brave-attach` | starts Brave with remote debugging and attaches a Selenium driver for browser automation | `scripts/` |
| `evernote` | reads, writes, searches and appends Evernote notes by title through the Thrift CLI; one label keeps its place, its value follows it | `briefs/`, `scripts/` |
| `gmail-setup` | sends and reads Gmail, including the KUBS mailbox `chaehanso@korea.ac.kr`; re-consents OAuth | `scripts/`; `README.md` at the repo root |
| `grill-instruct` | asks one question at a time to write agent instruction or skill files without prediction-as-prior wording | — |
| `hanji` | reads and writes Hanji notes through the local `hanji` CLI and `hanji_note.py`, with images, tags and versions | `scripts/` |
| `itinerary-sync` | writes a booking's dates into `memory/travel.md`, `travelitinerary.csv` and the year's itinerary note in one pass | `scripts/`, socrates `memory/travel.md` |
| `kubs-deck` | builds, fixes and verifies the E01-E08 Keynote decks; deckcheck runs before any install | socrates session folders |
| `kubs-essay-grading` | grades the 35 percent essay round, sweeps a single student, builds the course gradebook | socrates `docs/` |
| `kubs-grading` | team (65 percent) and solo assessment, the comparison against Chaehan's read, the rendered curve | Drive "KUBS DT Grading" |
| `kubs-mail` | reads the KUBS mailbox into a ranked list of what to attend, each row with its venue and registration link | `scripts/` |
| `kubs-printout` | session script PDF and run sheet PNG for the TA, sent over Signal | socrates printout files |
| `life-challenges` | the dated Life Challenges note: the dilemma as two ways, the questions that decide, research per issue | `scripts/`; socrates `projects/applecalendar`, `projects/omnifocus` |
| `life-overview` | the dated Life Overview: status per domain, timeline, what went well | `scripts/`; the same two adapters |
| `llm-smoke` | verifies LLM auth and connectivity end to end and reports which key source resolved | `scripts/` |
| `receipt-note` | a receipt or booking into an Evernote note with an itinerary card at the top | `email_shot.py`, `render_card.py` |
| `sourcing` | provider comparison tables in `memory/src_*.md`: vendors, quotes, reply checks | `README.md` (the routing rule for `src_` files) |
| `update-css` | a 200 m + 400 m swim test into CSS, its effort zones and `config/benchmark.yaml` | swim `config/benchmark.yaml`, `swim/AGENTS.md` |
| `vendor-bump` | rolls every consumer repo's pinned agentkit ref to a new tag | `scripts/` |

## Commands

`agentkit/commands/<name>.md` holds a step the user triggers on a fixed input
(`/life`, `/slides`, `/grade-essay`, `/trip-note`, `/printout`, `/runsheet`,
`/deckprep`, `/compare`, `/grade-team`, `/gradebook`, `/latency-report`). A
skill is recognised from a request; a command is invoked by name. A command
that grows a judgement goes in the skill it belongs to.

## Where a new document goes

- The instruction a skill follows: its `SKILL.md`.
- A script or template the skill runs: beside that skill, in its `scripts/` or a
  named file.
- A routing rule or a lookup table too long for `SKILL.md`: a `README.md` or
  `reference.md` in the skill's folder, as `sourcing` does.
- The design of code a skill calls: that project's own `README.md`, in the repo
  the code lives in.
- A fact about Chaehan: `memory/` in socrates, in the topic file it belongs to.
- A rule that binds every agent: `RULES.md` and `rules.index.md`, never a
  memory file and never a skill.
