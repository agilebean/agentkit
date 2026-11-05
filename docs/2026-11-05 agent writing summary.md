## Summary

- Deepseek did what the checks rewarded, and every check rewarded keeping: no number, row or word lost. Nothing measured what was cut.
- So its citrulline rewrite kept all 64 numbers and grew from 1488 to 1553 words, with 16 flat bullets under Buying.
- The gate now accepts a cut list, caps the summary at 5 lines of 30 words, and fails more than 7 items at one level.
- Rewritten through the new steps, the citrulline note has 774 words, 5 summary lines and 12 cuts, each with its reason.

## Why deepseek writes this way

Each section names one thing the model cannot do, the mistakes it produced in your notes, and the check that replaces the missing judgment.

### It follows the check, not the goal

- In your notes: the citrulline note got longer, the semen note kept the trivial pregnancy line, and the blind judge passed a Takeaway you found robotic.
- The cause: a rule with a test that exits 1 wins every conflict with a rule that has none. The note gate fails a draft that drops any number of the original, so "compress the world" lost to it every time. Deepseek even noted that the number check "is lenient" and planned around it.
- The replacement: the gate counts a fact as accounted for when it is in the draft or in a cut list with its destination ("moved to the linked study note", "dropped: single study, pooled estimate covers it"). A summary longer than one line per decision fails.

### It rewrites sentence by sentence and never selects

<!-- verbatim -->
- In your notes: "carrying the effect" (a phrase the checker flags) became "produces the effect", every section survived, and a list of products became more bullets.
<!-- end verbatim -->
- The cause: a weak model does a rewrite as translation, one sentence in and one out. Ranking sentences against your decision is a judgment over the whole note, and it has no step for it.
- The replacement: a labelling table before the draft, one row per source sentence: decides, supports, world detail, or already known to you. Sorting items one at a time is a task a weak model does well. Only "decides" enters the summary; world detail is cut or linked.

### It copies the instruction's words into the note

<!-- verbatim -->
- In your notes: "the next month turns on", "what changed since the last snapshot", "the one deadline", "is fixed until", "money keeps one clock".
<!-- end verbatim -->
- The cause: the four questions ("what is true now", "what would change your mind") are written in words about text, and the model cannot keep the language of the instruction apart from the language of the answer.
- The replacement: the four questions are answered in a scratch file and never pasted. The checker flags each leaked phrase. The skill shows each answer in content words beside the rejected form.

### It writes from its own context, not yours

<!-- verbatim -->
- In your notes: "the daily tablet", "the panel", "the act", "it ends without a towel", "the clothes have no home", "the question goes to the Gayeon consult".
<!-- end verbatim -->
- The cause: the model holds the whole conversation and does not picture a reader who lacks it. Its sources describe objects, so its sentences describe the state of objects instead of your action.
- The replacement: the seat test as a subject check (the subject of each summary sentence is you or your thing), the referent warnings for unnamed nouns, and the absence and travelling-question forms as checker rows.

### It reads a rule for what it allows

<!-- verbatim -->
- In your notes: "this is a research note, not a meeting summary, so a Takeaway is not added", and "the gate's note mode doesn't check heading names". It also took "every citation stays" from the brief over the core.
<!-- end verbatim -->
- The cause: the model reasons about which text applies and what a check accepts, not about what the rule is for. A brief written by another agent counts as a closer instruction than the standard.
- The replacement: every rule it must obey has one accepted and one rejected example; a brief may only narrow the standard, and the evernote skill's brief template states what may be cut.

## What I built that worked against it

- The note gate's fact check (T6) was written to stop deepseek dropping your dates and numbers. It cannot tell your numbers from a study's, so it also forbids cutting the world, which the core requires.
- The "CHECK words gone" list asked the model to account for each lost word. Deepseek read it as a list of things to put back, and it is now removed.
- The rewrite brief from the orchestrating session said "every dose, timing, half-life, study size, effect size and citation stays". That sentence alone forbids quality over quantity.

## Titles and file names

- A title and a file name name the subject by a category noun, never by a person or by what someone does or receives: "Semen: nutritional intake", never "what she gets".
- "Embarrassing" is a judgment deepseek cannot make, so the checker now tests it lexically: a pronoun or an explicit word in a file's own name or in `--title "<note title>"` is a flag. Rule 20, rule 70 and the evernote skill point to it.
- No existing markdown file name in agentkit or socrates fails the check.

## What was built on 2026-11-05

1. The note gate takes a cut list (`--cuts <file>`): a number of the original passes when the draft or the cut list names it, and a cut line without a reason fails (T9). The "CHECK words gone" list is removed.
2. Summary checks: more than 5 lines or a line over 30 words fails (T10), and a summary line that shares most of its words with a body line fails as a repeat (T11).
3. A list check: more than 7 items at one level under one parent fails (T12). This is the check that would have stopped the 16 flat bullets in the citrulline buying section.
4. The evernote skill's step 1 now has the labelling step: Chaehan's decisions first, then every old sentence labelled decides, supports, world detail or known, and every cut written into the cut list. A new section gives the brief text for another agent and forbids "every citation stays".

## Next round

1. Rerun deepseek on another research note with the new skill and gate, and compare its cut list with the one written for citrulline.
2. Build the plugin that refuses an Evernote write whose text fails the checks.

## Technical details

### Where each standard lives

| Standard | Home | Points to it |
| --- | --- | --- |
| Selection: four questions, three moves, seat test, gist | `agentkit/AGENTS.md` core 1 | RULES 19, 195, 244; life-overview skill; `socrates/.opencode/agents/socrates.md` |
| The chain (effect, cause, consequence) | `agentkit/RULES.md` opening section | `AGENTS.md` core 2; socrates.md |
| Robotic kinds (38) and their fixes | `RULES.md` rule 2 | `AGENTS.md` core 4; `common_sense.md` rows |
| Note rewrite, six steps | `agentkit/skills/evernote/SKILL.md`, "Writing or rewriting a note's text" | `AGENTS.md` core 1 |
| Life overview, four moves and gate | `agentkit/skills/life-overview/SKILL.md` sections 3 and 3a | none |
| Dated snapshots are never superseded | `RULES.md` 31 | `AGENTS.md` core 7; both skills |
| Neutral titles | `RULES.md` 20 | evernote skill, note structure rules |
| Lock is not a second writer | `RULES.md` 216 | evernote skill, verify section and step 6 |

`AGENTS.md` is loaded in every opencode session and is at its 1200-word ceiling: a new line there replaces one. `RULES.md` is not loaded by the harness; agents read it by section through `rules.index.md`, regenerated with `python3 tools/rules_index.py`.

### Commands

- Wording checker: `python3 ~/Software/Prototypes/agentkit/scripts/wording_lint.py <file>`. Marker list: `agentkit/robot_markers.tsv` (level, regex, fix).
- Note gate for any note: `python3 ~/Software/Prototypes/agentkit/skills/life-overview/scripts/overview_gate.py <draft.md> --original <before.md> --cuts <cuts.md> --note`.
  - T5: a section of 3 or more sentences with no list in it.
  - T6: a date or number of the original that is gone (thousand separators ignored).
  - T7: a table row of the original that is gone.
  - T8: an empty list item.
  - T9 to T12: a cut without a reason, a summary over 5 lines or 30 words a line, a summary line that repeats a body line, more than 7 items at one level.
  - `--cuts <file>`: one line per removal, `- <numbers>: <destination or reason>`.
- Life overview gate: same script without `--note`, with `--linked <exported detail notes>`.
  - T3: a Takeaway bullet that shares at least half of a task row's words, the row making up at least 30% of the bullet. It catches literal repeats only, so the agent also reads each bullet against the table.
  - T4: a body section with no `evernote:///` link, unless it says "no detail note".
- Tests: `~/Software/miniforge3/envs/socrates/bin/python -m pytest -q` in agentkit, 246 passing. Inside Claude Code's sandbox, two browser tests fail because they cannot bind a local port; run outside the sandbox.

### Marker rows added on 2026-11-05

<!-- verbatim -->
- Flags: "the month turns on" (also week, year, search, plan, decision), "keeps one clock", "the one deadline/decision/question/risk", "since the last snapshot", "what changed is", "the risk that grows", "is fixed until", "what is fixed", a question that "goes/moves to" someone, "I said earlier", "my earlier claim", "That was wrong".
<!-- end verbatim -->
<!-- verbatim -->
- Warnings: "has no home", "none is booked", "is not booked", a refusal written as the agency's act ("refused a foreign", "refusing you"), an unnamed tablet, pill, drug, medication or panel ("panel physician" excluded).
<!-- end verbatim -->
- Each was probed on the rejected sentence and on the accepted one, and checked for false alarms across `RULES.md` and the socrates memory files.

### Evernote mechanics

- Note link form: `[<exact title>](evernote:///view/39d2f74/s365/<guid>/<guid>/)`; `markdown_to_enml` turns it into a link.
- In an opencode session the MCP tools are the only write path; the CLI is for outside a session.
- The CLI from Claude Code: call `~/Software/miniforge3/envs/socrates/bin/python -m projects.evernote.src.evernote_api` directly, because `mamba run` cannot take its lock file in the sandbox.
- Title lookups fail after a rename and on parentheses; read by guid with `get <guid> --markdown`.
- Version history: thrift `listNoteVersions(token, guid)` and `getNoteVersion(token, guid, usn, ...)` through `_build_note_store()`; this is how deepseek's 16:41 and 17:05 passes were told apart.
- Lock recovery clicks another note in Evernote's sidebar through Apple Events; Claude Code's sandbox blocks that, opencode does not.
- `replace-section "<title>" "<heading>" --to-heading "<next heading>" --markdown --file <file>` changes one section and leaves the rest of the note byte-identical.

### Tests run and results

- Packet and results: `agentkit/docs/answer_quality_test_packet.md`; short report: `agentkit/docs/answer_quality_report.md`.
- T1 (seat), T2 (gist, 200 words or less), T4, T5, T6 passed on the rewritten 2026-11-03 overview and the paternal note.
- T3 (Takeaway not a task list) passed on round 4, accepted by you; rounds 2 and 3 passed the blind judge and failed your reading.
- T7 (deepseek, skill only, no tools) partial: links and sub-points yes, Takeaway and seat test no.

### Plugin plan, not implemented yet

- Built like `agentkit/plugins/commit-discipline/index.ts`: `ctx.tool.hook("execute.before", event => ...)`, throwing an `Error` blocks the call.
- Evernote writes reach the hook as JavaScript passed to `execute`, so the note text has to be pulled out of that code, written to a file, and run through the checker and the gate; the refusal names each failing line.
- Needs a live test inside opencode with deepseek, which Claude Code's sandbox cannot run.

### Records

- Failure register `socrates/memory/agentic_ai.md`: failures 156, 157 and 160 to 162 from this work; 158 and 159 are another session's.
- `agentkit/common_sense.md`: 13 rows of accepted and rejected wording from 2026-11-05.
- Commits: agentkit `5893b00`, socrates `b273d95` (CI run 41994285364 passed).

### Citrulline evidence

- Note "2026-09-30 L-Citrulline - Doses, Timing, Tadalafil", guid `1053890a-c4cc-425b-9dc8-105128a3d480`; before is version 931387, saved with the current text in `$TMPDIR/aq/` as `cit_1053890a_v931387.md` and `cit_1053890a_now.md`.
- Deepseek session `ses_e550b5d25ffe8C2vCUbNiItZgT` in `~/.local/share/opencode/opencode.db` (deepseek-v4.1-flash, subagent "Rewrite Citrulline note"). Its reasoning maps every numeric token of the original to a place in the draft before writing.
- The rewrite's labels and cut list: `$TMPDIR/aq/cit_labels.md` and `cit_cuts.md`.
- Title check: `title_hits()` in `scripts/wording_lint.py`, tests in `tests/test_wording_lint.py`.

### Open questions

- The semen note says the seminal vesicles empty first and the prostate last, then that the prostatic fraction reaches the tongue first. The order needs a source before the note is corrected.
