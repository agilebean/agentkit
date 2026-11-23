# RULES.md redesign plan, 2026-11-23

RULES.md loses ~19% of its words when each rule keeps its principle sentences word for word, one quote and its failure numbers: the first batch of phase 2 took rules 2, 10, 17, 73 and 104 from 7727 to 6275 words on 2026-11-24, and at that share the file ends near ~75000 of its 92666 words. A smaller file needs phase 3, where rules merge and their wording changes on your yes. The order makes it safe: phase 1 copied every incident into the failure register on 2026-11-24, so all 783 distinct long quotes of RULES.md stand there, against 281 the day before, and no cut loses your words.

Three measurements make the plan necessary and safe:
- 35% of RULES.md (~32600 of 92666 words) is in sentences with a date, a quote or a failure number, and the file's own writing standard (its line 9) says a rule tells no incident. That share is an upper bound: the first batch cut 48% of those words, and the rest are quoted examples, such as the kinds of rule 2, or rules that state a date.
- Of the 783 distinct quotes of 25 characters or more, 281 (36%) stood verbatim in socrates `agent/failures.md` on 2026-11-23, matched across line breaks by the ledger of phase 0. 223 rules tell a dated incident, and 195 of them cite no failure number.
- 79 files in agentkit and socrates cite 180 rules by number, 634 times. Numbers therefore never change.

The copy came to 42970 words, against the ~8000 words of quotes this plan first estimated: phase 2 can only cut a sentence the register holds whole, and an instance runs on in sentences with no date or quote of their own. The register grew from 91952 to 134996 words and its index from 275 to 517 lines, and it is still read by section. If the longer index makes looking up a failure too costly, the section "Evidence for the rules" moves into its own file in socrates `agent/`, a move of one section.

## What it costs you now

What every session loads stays small: `AGENTS.md` is ~2700 tokens. The cost is in following the rules. An agent picks rules from the 261 headlines in `rules.index.md` (~7600 tokens). The instruction it then reads sits between the incidents that produced it: the median rule has 276 words, and rule 2 has 2275. Each correction is also merged into the rule's body (`AGENTS.md` core 0), so a rule grows with every incident. One level-2 section, "Invariants, coupling, and avoiding narrow rules", holds 219 of the 261 rules, and the section on the shell aliases holds 32 more that have nothing to do with the shell, so the file has no grouping an agent can navigate by.

Incident quotes in RULES.md also keep private context in a public repository. Moving them to socrates serves the same goal as DD-03.

## The target: four layers

| Layer | File | Holds | Read |
|---|---|---|---|
| 1 | `AGENTS.md` | the core standards | every session, unchanged |
| 2 | `rules.index.md` | rules grouped by the moment they apply (before writing text, before a commit, before a memory write, before a deck install, shell and permissions), one line of principle per rule | when a task starts |
| 3 | `RULES.md` | one card per rule | by line range |
| 4 | socrates `agent/failures.md` | every incident: date, your words verbatim, cause, fix | by section, through its index |

Every card has the same shape:

```
### N. Title
Principle: one to three sentences, in the wording the rule has today.
Test: how to tell the rule is met, and the script or test that checks it, if one exists.
Neighbours: the rules it borders.
Evidence: failure numbers, plus one quote: the instance most representative of the rule's class and most discriminating against its neighbours.
```

Line 9 of RULES.md says which quote stays: the instance most representative of the rule's class and most discriminating against the neighbouring cases (Chaehan, 2026-11-23). A rule merged into another keeps its number as a one-line stub that names where it went. All 634 citations then still resolve.

## The migration, in four phases

**Phase 0, freeze and ledger.** Done on 2026-11-23. The agentkit tag `2026-11-23_rules` keeps the whole text. `tools/rules_ledger.py` splits RULES.md into 4091 units (a sentence, a heading, a table row or a code block), each with an identifier (`R17.004` is the fourth unit of rule 17) and a first-pass class, and `check` names any unit that stands in none of the files the text moved to. The split is lossless on the real file, all 261 rules are covered, and `check` against today's RULES.md finds 0 missing. The ledger quotes incidents, so it lives in socrates: `docs/2026-11-23 rules ledger.tsv`. The first-pass classes: principle 2728 units (56360 words), incident 897 (27713), heading 275, test 135, example 22, pointer 30, table 4. The incident class is a lower bound: a sentence that continues an incident without its own date or quote is classed principle, so phase 1 reviews each rule's units before copying.

**Phase 1, copy, delete nothing.** Done on 2026-11-24; RULES.md was unchanged since the tag, so the ledger of phase 0 was the input. `tools/rules_ledger.py evidence` decided every unit of a paragraph from its first incident on, and `apply` wrote the copies word for word:
- 1257 sentences (36506 words) copied: the 813 incident sentences the register lacked and the 444 sentences after them in their paragraphs, since the review found that an instance often continues in sentences the first pass classed principle. A principle sentence copied this way is a duplicate, and RULES.md keeps it.
- A paragraph that cites exactly one failure went into that failure's entry, under a line "From RULES.md rule N, tag, line": 45 paragraphs into 38 failures. Every other paragraph went into one entry per rule in the register's new section "Evidence for the rules", 237 rules and 4 sections without a rule.
- 70 sentences stood in the register already, and 15 only name a failure number ("Instance: `agent/failures.md` failure 49."); phase 2 turns those into the card's evidence numbers.
- All 783 quotes now stand verbatim in the register, no line of the register was lost or moved, and a second `apply` changes nothing. socrates `docs/2026-11-24 rules evidence map.tsv` records each unit's decision and destination, and socrates `tests/test_rules_evidence.py` fails if a copied sentence or a quote leaves the register.

Incidents keep reaching RULES.md through `AGENTS.md` core 0 until phase 2 runs, so phase 2 starts by building the ledger of its day and running `evidence` and `apply` again.

**Phase 2, trim to cards, 20 rules per batch, longest first.** Incident sentences give way to their failure numbers. Principle sentences stay word for word: nothing is reworded in this phase. You review the first batch's before and after (rules 2, 17, 73, 10 and 104) before the rest runs. Each batch is one commit, with the checks below green.

The first batch ran on 2026-11-24, on a RULES.md identical to the tag, so `evidence` and `apply` had nothing new to copy. Each unit was read by hand, because the first-pass class misleads both ways: a quoted example of a kind of rule 2 is classed incident and stays, and a sentence that only continues a case is classed principle and goes. The decisions are a file per batch in socrates, `docs/2026-11-24 rules trim batch 1.tsv`, one row per unit with its reason:
- "cut" removes a sentence that tells one dated case, or the user's reaction to it: 42 units.
- "strip" removes only a dated citation inside a sentence that states behaviour, such as the dated VPN case inside rule 73's sentence on hangs: 4 units.
- "append" adds the card's two lines at the rule's end: "Neighbours:", the rules it borders, and "Evidence:", its failure numbers and its entry "Evidence for rule N" in socrates `agent/failures.md`.
- Every unit the file does not name stays word for word, and each rule keeps one dated quote in place: rule 2 the one on "save", rule 10 the one on amending a correction, rule 17 the one on a constraint's age, rule 73 the one on 600-second timeouts, rule 104 the one on the E08 story pages.

`tools/rules_ledger.py trim` applies the file. It changes only the lines that lose text, copies into the register any cut sentence it lacks (one, from rule 10), and writes nothing when a kept sentence would stand in no line of RULES.md or a cut one in no line of the register. Rules 2 and 10 lost 1% and 4%, because they are mostly principle; rules 17, 73 and 104 lost 29%, 25% and 41%. A phase 2 card is therefore the rule's remaining text, then the two lines: a principle of one to three sentences and a separate Test line need rewording, so they come with phase 3.

**Phase 3, merge and route, each merge on your yes.** Rules on one theme merge into one card: wording (2, 19, 37, 48, 54, 57, 85, whose duplicated markers `common_sense.md` already lists as waiting on your word) and commits (3, 10, 46, 119) are the first candidates. Then `rules.index.md` is regrouped by the moment of use.

## The checks that prove nothing is lost

Each check runs in `tests/` on every push:
- **Quote ledger:** every quote in the tagged RULES.md stands in the register or in the new RULES.md; socrates `tests/test_rules_evidence.py` checks the register, which since phase 1 holds all of them.
- **Sentence ledger:** every sentence identifier has a destination where the sentence stands verbatim.
- **Principle diff:** in phase 2, every sentence a batch's decision file does not name stands word for word in the new RULES.md (`trim` checks it before writing), and socrates `tests/test_rules_evidence.py` fails if a cut sentence leaves the register; wording changes only in phase 3, on your yes.
- **Citations:** every "RULES.md N" and "rule N" in agentkit, socrates, the skills, the commands and the opencode agents points to a rule or a stub.

## What you get

After phase 2, RULES.md drops from 92666 to ~75000 words, and every rule ends in its neighbours and its evidence numbers. After phase 3 the index routes by task, each rule fits on a screen, and the size depends on how many merges and rewordings you accept. The register grew by 42970 words in phase 1 and is read only by section.

## Decisions, settled on 2026-11-23

1. A rule keeps one quote, the instance most representative of its class and most discriminating against its neighbours, never the shortest.
2. A merged rule keeps its number as a one-line stub (the three proposals approved, Chaehan, 2026-11-23: "yes").
3. The evidence lives in the socrates failure register.
4. The first batch of phase 2 is the five longest rules (2, 17, 73, 10, 104), and Chaehan reviews it before the rest runs.
