# Answer quality: report, 2026-11-05

## What is now true for you

The agent now chooses what goes into a text from your decision before it writes a sentence. The always-loaded core (`AGENTS.md`, 1044 words, down from 1772) opens its answer standard with the four questions: what is true, what it means for you, what you will do, what would change your mind. Three moves follow: the answer, the facts that decide it, and the detail behind one link. The seat test checks the finished draft for sentences whose subject is the agency, the study or the file instead of you.

The life-overview skill no longer defines relevance as cost. It defines it as impact on a goal you are pursuing or a decision you have pending. The Takeaway is written last, from the answers, and it cannot repeat a task row. A gate script rejects a draft with no note links, no indented sub-points, a Takeaway bullet that copies a task row, or a lost date or number, and it names the sentence or section it rejects. On the 2026-11-03 overview it reports 13 failures.

No dated snapshot is deleted any more. The three lines that ordered the deletion are gone from the skill, and rule 31 and the evernote skill now say that a rework issues a new date and leaves the earlier note untouched. That rule is why the 2026-10-23 note had to be restored.

The paternal note is rewritten and written to Evernote: the summary keeps the answer, the call to the bank and three deciding facts, and no sentence about the agent's earlier answer. On the record, the rewrite of the 2026-11-03 overview passed T1, T2, T4, T5 and T6. On T3 you reversed the blind judge: its passing round 3 sounds robotic, because the skill listed the Takeaway's functions and the rewrites wrote them into the sentences. The skill now forbids naming a bullet's function, the checker flags the five shapes, and round 4 keeps round 1's voice; you accepted it. T7, the installed deepseek model on a fresh case, is partial. It produced links and sub-points without help, but its Takeaway still read as tasks, and it wrote the Duo refusal and the visa as the agency's and the visa system's acts. The packet holds every failure.

## What waits on you

- Commit and push the changes in agentkit and socrates?
- T7 could not show whether deepseek ignores a failing gate or never reaches it, because the run gave it no tools. The next run gives it the gate script as a step.
- `RULES.md` grew by 444 words (78903 to 79347). The words are pointers to each standard's home, the dated-snapshot exception, and the two paragraphs moved out of `AGENTS.md`. The brief asks that a correction add none.
- The local file `socrates/docs/2026-11-03-life-overview-NEW.md` still disagrees with its note's title. The skill now forbids the suffix. The rename is yours to approve.




## Files changed

- `agentkit/AGENTS.md`: the core rewritten (relocations below)
- `agentkit/skills/life-overview/SKILL.md`: four moves, the gate, the dated-snapshot exception, three deletion lines removed
- `agentkit/skills/life-overview/scripts/overview_gate.py` and `agentkit/tests/test_overview_gate.py`: new; full suite 234 passed
- `agentkit/skills/evernote/SKILL.md`: dated-snapshot exception, how to author a note link
- `agentkit/RULES.md` (preamble, writing standard, 19, 31, 141, 195, 244) and `rules.index.md` (regenerated)
- `socrates/.opencode/agents/socrates.md`: its copy of the chain standard and of rule 21's format replaced by pointers
- `agentkit/robot_markers.tsv` and `agentkit/common_sense.md`: five marker rows, three wording rows
- `socrates/memory/agentic_ai.md`: failure 156
- `agentkit/docs/answer_quality_test_packet.md` and this report: new

## Appendix: one home per standard

| Standard | Home | Points to it |
| --- | --- | --- |
| Selection: four questions, three moves, seat test, gist | `AGENTS.md` core 1 | RULES 19, 195, 244; life-overview skill; socrates.md |
| The chain | `RULES.md` opening | `AGENTS.md` core 2; socrates.md |
| Two-sentence focused answer | `RULES.md` 21 | `AGENTS.md` core 1; socrates.md Phase 3 |
| Studies as meta-analyses in notes | `RULES.md` 244 | `AGENTS.md` core 1 |
| Dated snapshots are not superseded | `RULES.md` 31 | `AGENTS.md` core 7; evernote and life-overview skills |
| Wording classes | `RULES.md` 2 | `AGENTS.md` core 4 |
| Note link authoring, twin hash | evernote skill | life-overview skill |

## Appendix: where the removed `AGENTS.md` sentences went

| Removed | Now lives in |
| --- | --- |
| The opencode v2.0.16 probe on why RULES.md is pointed to | `RULES.md` preamble |
| The E05 compaction measurement; "context compacts at ~300k" | `RULES.md` 141; the harness figure deleted |
| Parsimony, the gist of a structure, the chain (long forms) | `RULES.md` opening sections; one line each in core 2 |
| "Do not duplicate the numbered rules here" | Deleted; the Rules paragraph states one home per standard |
| Core 2 "(5) for prose, state the event"; "a removal fix matches the identity" | `RULES.md` chain section; "Never change the gist of a structure" |
| "A stale figure is re-measured"; "a workaround through the failed gate is dropped" | `RULES.md` 208 and 63; 248 |
| "X should have Y is a directive"; "a pending action runs when the channel returns"; "a preference is not a filter" | `RULES.md` 102; 176; 5 |
| "A complaint that names an act is a revert"; "settled content propagates"; "edits merge"; "git status after the last edit" | `RULES.md` 148; 69 and 72; 93; 10 |
| "Every quote, provider or contact entry holds its email address" | socrates.md, Names and identifiers |
| "A bias label needs his endorsement"; "event reports are not prescriptions"; "an episode is filed under its topic" | `RULES.md` 22; 15; 69 |
| "No changed subject line, no abbreviated name", "check the sent history before any resend" | Kept in core 8: no other home exists |
