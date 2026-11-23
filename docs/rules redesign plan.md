# RULES.md redesign plan, 2026-11-23

RULES.md can shrink by about a third without losing a sentence, but only in this order: first every incident is copied into the failure register, then each rule is cut to its principle, its test and the failure numbers. Today 78% of the long quotes in RULES.md exist nowhere else, so cutting first would lose your words.

Three measurements make the plan necessary and safe:
- 35% of RULES.md (~32600 of 92666 words) is in sentences with a date, a quote or a failure number. That is incident text, and the file's own writing standard (its line 9) already says a rule carries no incident narrative.
- Of the 549 quotes of 25 characters or more, 122 (22%) stand verbatim in socrates `agent/failures.md`. 223 rules tell a dated incident, and 195 of them cite no failure number.
- 79 files in agentkit and socrates cite 180 rules by number, 634 times. Numbers therefore never change.

The plan would change if the failure register turned out to be the wrong home for ~8000 more words of quotes. The alternative would then be one evidence file per rule group in socrates.

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
Evidence: failure numbers, plus at most one quote where your wording fixes the standard.
```

The quote exception is the one line 9 already makes ("quote the shortest fragment that carries it"). A rule merged into another keeps its number as a one-line stub that names where it went. All 634 citations then still resolve.

## The migration, in four phases

**Phase 0, freeze and ledger.** Tag agentkit `rules-2026-11-23`, so the whole text stays retrievable. A script, `tools/rules_ledger.py`, splits RULES.md into sentences, each with an identifier (rule number and position) and a class: principle, test, scope, example, incident or pointer. The ledger quotes incidents, so it lives in socrates.

**Phase 1, copy, delete nothing.** Every incident sentence that the register lacks goes into it: into the matching failure entry where the date and quote match, otherwise into one evidence entry per rule ("Evidence for rule 17") that lists the dated instances verbatim. Done when all 549 quotes stand verbatim in the register, against 122 today.

**Phase 2, trim to cards, 20 rules per batch, longest first.** Incident sentences give way to their failure numbers. Principle sentences stay word for word: nothing is reworded in this phase. You review the first batch's before and after (rules 2, 17, 73, 10 and 104) before the rest runs. Each batch is one commit, with the checks below green.

**Phase 3, merge and route, each merge on your yes.** Rules on one theme merge into one card: wording (2, 19, 37, 48, 54, 57, 85, whose duplicated markers `common_sense.md` already lists as waiting on your word) and commits (3, 10, 46, 119) are the first candidates. Then `rules.index.md` is regrouped by the moment of use.

## The checks that prove nothing is lost

Each check runs in `tests/` on every push:
- **Quote ledger:** every quote in the tagged RULES.md stands in the register or in the new RULES.md.
- **Sentence ledger:** every sentence identifier has a destination where the sentence stands verbatim.
- **Principle diff:** in phase 2, each rule's principle sentences are identical before and after; wording changes only in phase 3, on your yes.
- **Citations:** every "RULES.md N" and "rule N" in agentkit, socrates, the skills, the commands and the opencode agents points to a rule or a stub.

## What you get

After phase 2, RULES.md drops from 92666 to ~60000 words, and every rule fits on a screen: principle, test, evidence numbers. After phase 3 the index routes by task, and the size depends on how many merges you accept. The register grows by ~8000 words of quotes, read only by section.

## What you decide before phase 0

1. A rule keeps one quote where your wording fixes the standard, or none. Proposal: one.
2. A merged rule keeps its number as a stub. Proposal: yes.
3. The evidence lives in the socrates failure register. Proposal: yes, since it is private, indexed and already in the incident format.
4. The first batch is the five longest rules, and you review it before the rest. Proposal: yes.
