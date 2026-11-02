# Agentic improvement

Status, 2026-11-03: Rounds 1 to 3 are complete, including the writing test (T6, section 3.4) and its balanced re-run (section 5). Changed and committed with this change: RULES.md rule 2, replaced with five classes and thirty-five kinds by name (examples in common_sense.md, section "Examples of rule 2's kinds"); RULES.md rules 2, 5, 9, 15, 21, 58, 61, 63, 67, 68, 69, 102 and 116 extended, and rules 244 to 251 added; rules.index.md (rows re-derived from the headings); one row in table two of common_sense.md; Failures 141 and 142, and the 2026-08-19 incident under Failure 19, in the register; the always-loaded core, installed in agentkit/AGENTS.md and socrates.md (section 7), and the skills and memory files named in 7.2. Not changed: the checker, scripts/wording_lint.py.

A new session starts here. Read section 0 for the question, 3.6 for the recommendation, 6 for what waits on Chaehan and 7 for the installed core. Sections 1 to 3 are the evidence; each figure names its source in its row or in Appendix B. The writing test's texts and judging record are in Appendix C.

Terms: the **checker** is `scripts/wording_lint.py` with its list `robot_markers.tsv` (agentkit). The **register** is `socrates/memory/agentic_ai.md`. The **chain** is the writing standard of RULES.md's opening section: a sentence states the observed effect, then its cause, then the consequence the reader could not deduce. **Robotic** is Chaehan's word for machine-sounding text.

## 0. The question

Chaehan's words, kept as fragments:
- "find improvement potentials for the agent rules to make them more effective and the linguistic understanding of robotic wording and common sense captured in memory files"
- "I feel that the fixes in the agent rules are too narrow and solving on the symptomatic level"
- "tell me if rephrasing or rearrangement would help"
- "do three rounds"
- "i don't want a lot of answer text or analysis, but instead in-depth understanding"

The two incidents he named:
- **The swim panel** (register Failure 139, 2026-10-31). A change to the 60% and 70% panel changed which sessions it plotted, widened the card so the row wrapped, and the pass reported the chart unchanged. His sentence: a change cannot alter what was displayed.
- **The essay grading.** The criterion Insight changed meaning across eleven commits to the essay skill on 2026-10-30 and 10-31, before a test-based definition held.

Judging standard for every proposal: does it change what the agent does at the moment it writes or changes something? A rule the agent does not read at that moment is not coverage.

## 1. Round 1: collection

### 1.1 Sources

| Source | What it holds | Size |
|---|---|---|
| `agentkit/RULES.md` | The rules. Opening standard lines 1-127; rule 2 (wording) 137-218; rule 11 (abstraction) 382-407; rule 213 (chain form) 3906-3925 | 4,535 lines, 76,339 words |
| `agentkit/rules.index.md` | Section index. Says the file is 199 KB | 260 lines |
| `agentkit/common_sense.md` | Table one: 126 wording cases, each with his words and the repair. Table two: 68 "not common sense" corrections. Standing instructions. Search procedure over the session database | 316 lines |
| `agentkit/robot_markers.tsv`, `scripts/wording_lint.py` | The checker: 33 rules. A flag fails the run; a warning does not | 154-line script |
| `agentkit/AGENTS.md` | Loaded in every session. Summary of the standards | 883 words |
| `socrates/.opencode/agents/socrates.md` | The always-loaded prompt of this agent | 9,613 words |
| `socrates/memory/agentic_ai.md` | The register: 149 entries, numbers 1 to 141 (Failure 141 added 2026-11-02), eight numbers used twice (71, 83, 84, 94, 98, 116, 117, 126). Each entry has four labelled parts: principle, instance, why it happened, fix | 4,506 lines |
| `agentkit/skills/kubs-essay-grading/SKILL.md` and its history | How Insight is defined and scored | 11 commits, 2026-10-30 and 10-31 |
| `~/.local/share/opencode/opencode.db` | Every session, message, model and variant | 1.6 GB |

### 1.2 The rule file is a log of incidents

Rule growth, from the git history of RULES.md (221 commits, 2026-07-16 to 2026-11-01):

| Date | Numbered rules | Words | Dated incident references |
|---|---|---|---|
| 2026-07-16 | 13 | 2,875 | 0 |
| 2026-09-08 | 32 | 7,361 | 18 |
| 2026-09-21 | 57 | 14,230 | 70 |
| 2026-10-02 | 106 | 29,934 | 94 |
| 2026-10-14 | 158 | 46,219 | 196 |
| 2026-10-26 | 216 | 68,707 | 296 |
| 2026-11-01 | 239 | 76,339 | 335 |
| 2026-11-02 | 246 headings (244 numbers, with rule 244; 205 and 221 used twice) | 77,832 | not counted |

- The opening section of RULES.md forbids incident narratives and dates in rules. Rule 11 says to abstract from the incident to the principle. The file `carries` 335 dated references.
- Rule numbers 205 and 221 each appear twice.
- Rule 2 holds 49 bullet classes, most with a quote and a date. Its own text says the list "is not the whole of the standard", and each correction adds one more quote.
- The chain standard is written in three places (RULES.md, AGENTS.md, socrates.md). The marker list is copied into rules 19, 37, 48, 54 and 85; common_sense.md records that the copies wait on Chaehan's word before they are trimmed.

### 1.3 The always-loaded prompt `carries` the same log

socrates.md is 9,613 words. Its "Self-correction" section is 6,968 words with its two subsections; the bullet list alone is 5,986 words (62%), holds 62 bullets and cites 24 dated references. The register (361 KB) is not loaded by default. The prompt sends the agent to RULES.md by section, and the agent decides which section to read.

### 1.4 The checker reaches a small part of the problem

Test set: the 126 cases in common_sense.md table one. The "Flagged" cell is what Chaehan rejected. The "Repair" cell is the agent's rewrite, not every repair was accepted as written. 115 rows parse; 11 hold a pipe character in a cell and were not run.

- The checker hits 18 of 115 flagged cases (16%).
- It hits 16 of 115 repair texts. Reading the 16: three reuse a banned word inside the repair; the other thirteen hit a quoted phrase, a semicolon list, a proper name, a pronoun inside a quotation, or Chaehan's own term (Insight, instance record, mechanism).
- Phrases Chaehan named as wrong are absent from the list: `covered` (2026-10-26), `buys` (2026-10-26), `lane` (2026-10-23), and the frame "What is now true is" (2026-10-23). A search of robot_markers.tsv finds none of them.
- Probe of 14 sentences (Appendix A): the checker flags 4 lines. Two are right (`carry`, `carries`). Two are wrong: `leg` for a body part in the rule 213 sentence, and `leg-up`, Chaehan's own training term. It also warns on `Insight`, the name of his grading criterion. It misses 7 of the 9 lines that should be flagged.

The 100 phrase-level misses, coded by class (first pass, one coder, from the flagged phrase and its "why" cell; a phrase can fit two classes, so the counts rank rather than measure):

| Class | Count | What it is | Example, flagged phrase |
|---|---|---|---|
| Construction | 28 | Sentence shape: a contrast, a stand-in subject, an announcing frame | "knows where bias enters an interview" |
| Vocabulary | 24 | A word or term that is wrong here | "progress"; "evidence trail"; "get-it-done-ness" |
| Content or fidelity | 21 | Invented procedure, a claim not in the record, clutter | "How we do it: everyone writes their name on a card" |
| Voice or register | 14 | Who speaks, commands, refers to itself, the tone | "Please arrive at 13:25 and do this" |
| Layout or format | 13 | Headings, numbered lists, labels, table cells | "Confidence: high on rejecting heavier; moderate overall" |

Reading: a string list reaches only the vocabulary class, and only the exact form. 76 of the 100 misses are not word problems (construction 28, content 21, voice 14, layout 13).

### 1.5 The complaints did not fall as the rules grew

Chaehan's messages per month (session database, type user). Rate per 100 of his messages.

| Month | His messages | "robotic" | "common sense" | "can't you see" or "can't you understand" or "why is this still not" |
|---|---|---|---|---|
| 2026-08 | 306 | 1.0 | 0.0 | 0.3 |
| 2026-09 | 383 | 5.2 | 0.5 | 0.5 |
| 2026-10 | 978 | 4.2 | 5.9 | 2.7 |

Read with care. The rule count rose from 57 to 239 between September and October. Message volume rose about 2.5 times. Chaehan began using "common sense" as a standing label on 2026-10-03, which inflates that column. The "robotic" column is the cleaner signal, and it did not fall.

### 1.6 What the agent's replies contain

Assistant text parts from the session database: 1,585 messages in September, 4,886 in October. Tool narration is included, so the rates are upper bounds for replies.

| Pattern | Sep | Oct | Note |
|---|---|---|---|
| Em dash, en dash, or spaced double hyphen | 37.7% | 54.2% | Rule 2 forbids the em dash |
| Any checker hit | 50% | 62% | All rules, including warnings |
| "rather than" | 3.5% | 5.3% | Normal English; precision not measured |
| Past participle, then "not" (watched, not switched off) | 1.1% | 1.3% | Precision not measured |
| "not X, it is Y" or "not X but Y" | 0.3% | 0.4% | |
| "What is now true is" | 0.1% | 0.1% | 5 messages in October |
| "but costs you none" or "nothing" | 0 | 0 | The strict form of the construction Chaehan named does not occur |

Reading: the most frequent visible tell is the dash. Rule 2 has forbidden it for months, and half of October's messages still contain one. The contrast-for-effect family is present at roughly 1 to 5 messages per 100.

### 1.7 The register: what the fixes were

138 entries have a readable fix field.
- 117 of 138 fixes cite a rule number (85%).
- 61 of 138 mention a check, test, script, lint or gate by keyword (44%).
- In 55 of 148 entries (37%) the entry itself says the rule, the record or the skill already existed, or was not applied when it mattered. This is a keyword match; seven of the 55 were read and hold.

### 1.8 The grave failures

Failures that damaged a record, a send or a decision. Titles from the register; the number is the entry.

| Entry | Date | What happened |
|---|---|---|
| 1 | 2026-05 | Code edits with no test run; drill distances corrupted in W6S1 and W8S3 |
| 11 | 2026-09-29 | IRS escalation email, first version sent: headings, colon blocks, rubric labels, self-reference |
| 24 | 2026-10-11 | Health advice built on the generic habit, not on Chaehan's recorded one |
| 49, 50, 51 | 2026-10-14 | Eligibility inferred from a neighbouring tax concept; a procedure presented as available; a served-country list read as a signup gate |
| 53 | 2026-10-15 | An amend aimed at HEAD, in a checkout a concurrent session commits to |
| 57 | 2026-10-15 | A complaint about invented content answered by keeping it |
| 62 | 2026-10-17 | An install deleted a page of the deck |
| 98 | 2026-10-21 | A verification run overwrote the deck Chaehan presents from |
| 110 | 2026-10-25 | Availability asserted from a price |
| 116 | 2026-10-26 | An invented limit and an invented procedure around Chaehan's own material |
| 121, 123 | 2026-10-26 | A backup copied into the folder it protected; the backup deleted |
| 139 | 2026-10-31 | The swim panel (1.9) |

### 1.9 Smaller inconsistencies

- `rules.index.md` says 199 KB (actual 444 KB). `common_sense.md` says 28 machine checks (actual 33).
- Rule 213's worked sentence reads "prevented to setup", and its word "`leg`" trips the checker. The model sentence teaches the structure through a broken phrase.
- Rule 2's list is "not the whole of the standard" and still grows by one quote per correction.

### 1.10 The model

The register never names the model. The session database (`session_v2.model`) shows deepseek-v4.1-flash through opencode-go in 203 of the 209 sessions opened in October, and in 33 of 46 in September. This session runs claude-haiku-5-5. The premise holds for October, but the register cannot show it. Each entry should name its model and variant.

### 1.11 The two incidents, from the record

**Swim panel (Failure 139).** The pass added a series filter that moved the 60% and 70% reps across all dates. The 90% reps stayed right. It widened the card and the row wrapped. It ran "583 passed, 1 skipped" four times. The axis band moved from 2:02 to 2:32 while `y_range` stayed byte-identical, so it reported the axis untouched. The register's causes: it modelled the request and not the chart; it read the display code and not the code that decides which reps belong to a panel; it learned the layout by breaking it; the first crowding changed the layout, and Chaehan's phrase "exactly like panel 1" was taken as permission; the correction was stored as the act, not the class; the checks compared fields that do not `carry` the population; the written spec was rewritten to match the build. The register's root line: "the pass had no model of the structure, so 'do not change it' had no referent."

**Essay grading (skill history).** In the passes before the rewrite, the agreement on Insight with Chaehan's scores was 0.41 to 0.54, and on Skill 0.45 to 0.51, after repeated passes that added prose. After Insight became a test, the removal test (take the method out of the essay; if the insights stand unchanged, the method did not produce them, so Insight is 4.00 at most), agreement on Insight reached 0.85 and 0.95 in the last two passes over the 26 settled essays.

## 2. Round 2: strategies

### 2.1 What Round 1 says

1. The rules are a log of instances. Each rule binds to one quote and one word, so a new complaint adds a word and the class returns in another form. The `carry` family shows it: "`carries`" was flagged on 2026-10-11; "Wall posters `carry` the presentation" passed on 2026-10-12, because the list held only the forms it named; then `buys`, then `covered`.
2. Most failures are not word failures. Modelling the object (the swim panel, Insight), reading the state at the point of change (the chart, the screen), keeping Chaehan's own terms and content (the handout, the invented procedure), and scope (a consolidation that left the source in place) account for most of the register.
3. A rule is often present and not applied (37% of entries). Adding a rule does not place it in the decision.
4. One concept-level fix has a measured effect in the record: a definition written as a test, checked against a labelled set (the essay sheet).

### 2.2 The strategies

Each strategy states what it changes, the mechanism that should make it work, its pros and cons, and what it does to a weak reader (the deepseek sessions).

**S0. Keep the current practice (control).**
- Change: one rule or one word per correction, appended to RULES.md and the list.
- Mechanism: a rule read at the moment of writing blocks the exact instance next time.
- Pros: no design cost; every correction recorded; the owner sees a response.
- Cons: 13 rules to 239 in three and a half months; complaints flat; the rules contradict their own standard; each instance adds to the load the reader must hold; the class is never reached.
- Weak reader: the more text, the less of it is applied. The register already shows rules present and unapplied in 37% of entries.

**S1. Extend the word list with the words Chaehan named.**
- Change: add `covered`, `buys`, `lane`, `sprint` and the frame "What is now true is" to `robot_markers.tsv`.
- Mechanism: a machine check fails the run on the exact word.
- Pros: cheap; the only mechanical gain in the record; blocks exact recurrences.
- Cons: measured gain of four labelled cases (16% to 19%) against three new hits in repair texts. `sprint` is the course's own term, and `lane` is pool vocabulary. `leg` already misfires on body parts. Each word becomes a ban, and no construction or content class is reached.
- Weak reader: it obeys the list, and the false hits teach it to rename Chaehan's own terms, which he has said he does not want.

**S2. Split "robotic" into five classes, each with a test that can fail.**
- Change: replace the 49-class instance record in rule 2 with five classes: construction, stand-in vocabulary, invented content, voice, layout. Each has its form, one test, three accepted and three rejected examples from the labelled set, and its enforcement.
- The construction test is a deletion test, the same pattern as the removal test. Delete the clause. If the sentence still says the same thing, the clause was decoration: delete it. If the sentence now says less, the clause holds a claim: write the claim as its own sentence with a plain verb. Example: "bias is watched, not switched off" becomes "you cannot switch bias off", the repair rule 2 already gives.
- The stand-in test: can the verb's picture be drawn? Rule 2 already states it for `covered`. The word `buys` passes a word list when rewritten as "adds nothing"; the test asks which gain or cost is meant.
- Mechanism: each class is checked by the instrument that can see it: a word list for vocabulary, the deletion test for constructions, a source check for invented content, a voice specification for register, a layout template for format.
- Pros: matches the data (1.4); the 126 labelled cases and the probe become a regression set; the accepted repairs become the negative set that prevents collisions like `sprint`.
- Cons: the deletion test is judgment, and a weak reader may delete the wrong clause. Word swaps survive when the test is skipped. Each class needs Chaehan's approval of its examples.
- Weak reader: short tests work when they are short enough to run in the head.

**S3. An object-first procedure before any change or claim (root cause).**
- Change: a five-line procedure that runs before the first edit and before any sentence about a thing. (1) Name the object as Chaehan sees it: the chart, the page, the sentence, the grade. (2) Name what the change touches, and what must stay identical as seen: the marks, the words he quoted, the criterion's test. (3) Read the state at the point of change: the rendered output and the code that decides what it shows, not only the code that draws it. (4) For a graded concept, state the test that separates it from its neighbour. (5) For prose, state the event: who or what did what, and what it changed.
- Mechanism: the register's modelling failures (139, 18, 34, 43, 49, 52, 110, 112 and the Insight loop) are failures to name the object, not failures to know a rule. The procedure puts the object into the decision.
- Pros: attacks the largest class in the register; works across domains; step 4 is the mechanism behind the one measured fix; step 2 would have stopped the swim change, because the population is part of what the chart shows.
- Cons: a checklist can be filled in without reading. The swim pass named the chart and still changed the population. It needs a check that can fail (S6). It adds one step to each turn. It matters only where the reader meets it at the decision (S4).
- Weak reader: five lines can be held; 4,500 lines cannot.

**S4. Rearrange by layer and by decision point (the rearrangement asked about).**
- Change: three layers. Layer 1, always loaded, target about 1,000 words: the chain standard once, the object-first procedure, the deletion test, a dozen invariants (never change what the user sees; no outside send without Chaehan's word; invented content is not written; a claim keeps its owner), and pointers. Layer 2, loaded by trigger (a skill or a class file): the five classes and the per-domain procedures (decks, swim dashboard, grading, Evernote, letters). Layer 3, searched and never loaded: the register and the instance record, with dates and quotes. Rules `carry` no dated quotes. Numbers are unique, and each standard has one home.
- Mechanism: the reader meets the principle in a short prompt. Instances leave the reading path but stay searchable. Duplication goes.
- Pros: the always-loaded surface drops from 9,613 words toward about 1,000. Each standard lives in one place. The load matches what a weak reader attends to. This is the direct answer to "rearrangement".
- Cons: a rule that is not loaded is not applied, so the trigger design decides the result, and the 37% pattern could move from the rule to the trigger. Relocation can lose content; the prompt itself says only the owner can confirm a faithful move. A reorganization of 4,500 lines is a large edit.
- Weak reader: the largest effect per token. It needs S2 and S3 to fill Layer 1.

**S5. Operational definitions for every criterion Chaehan judges work by.**
- Change: each term he uses to judge work (Insight, Skill, gist, cue, chain, common sense, robotic) gets a test that can fail, a rejected example from his record, and an agreement check on a labelled set. The essay sheet already does this for Insight.
- Mechanism: a test gives a yes or no on a case; a description gives a feeling about it.
- Pros: the only strategy with a measured effect in the record (Insight agreement 0.41 to 0.54 becomes 0.85 to 0.95). The test sits in the skill where the grading happens.
- Cons: the definition belongs to Chaehan, and the agent cannot write it alone. It fits concepts with cases, not voice or wording. Each agreement check needs a labelled set.
- Weak reader: a yes or no on a case is easier to apply than a description.

**S6. Mechanical checks at the moment of change or output.**
- Change: (a) a differential check on displays: capture the marks before and after any change to a chart or page, and fail on any difference not asked for. The deck check does this for decks; the swim dashboard has nothing equivalent. (b) An output gate on outgoing text: dashes and the word list, with exceptions for Chaehan's own terms, quotes and names, run before the text goes out. (c) A structure test for the rule file: unique numbers, no dates, a word budget, no standard written twice. (d) The labelled set run on every change to the list.
- Mechanism: the check does not depend on the reader. It fails the run.
- Pros: the swim population change shows up as changed marks, while the 583 field checks could not see it. Dashes sit in half of October's messages; an output gate does not depend on the model reading the rule. The labelled set would have caught S1's collisions.
- Cons: engineering cost per check. It catches only what can be measured. The output gate needs a hook in the reply path (not yet verified in the plugin system). Word checks still collide with vocabulary without an exception list.
- Weak reader: the most reliable of the six, because it needs no attention.

### 2.3 Rephrasing and rearrangement

- **Rearrangement helps, and it comes first.** The rules are ordered by incident. They should be ordered by the decision: the object, the state, the change, the claim, the words. The always-loaded prompt should hold the procedure, and the log belongs in the register.
- **Rephrasing helps in two places.** First, "robotic" is five failures, and rule 2 treats them as one list; each class needs its own test. Second, the standards say "never" next to a quote; replace each quote with the test it encodes.
- **Neither helps alone.** Rephrasing alone makes a longer file. Rearrangement alone leaves the wording as it is. They are one move.

## 3. Round 3: tests and recommendation

### 3.1 What was run and what was read

| Test | Kind | Tests |
|---|---|---|
| T1. Checker coverage on the labelled set (115 flagged, 115 repairs), current list and extended list | Run | S0, S1 |
| T2. Construction detectors on the labelled set, the probe and the replies | Run | S2 (the detector part) |
| T3. Ceiling of a string list: share of misses it can reach | Run (coding) | S1, S2 |
| T4. Replay of eight incidents against each strategy | Judged, not measured | S0 to S6 |
| T5. Measured record: Insight agreement before and after the test | Read from the skill's own measurement | S5 |
| T6. Writing test: four writing standards, three scenarios, two blind judges per scenario | Run, see 3.4 | S2, S3, S4 (S4 only by its reading) |

### 3.2 Checker and detector results

| Test | Result |
|---|---|
| T1, current list | 18 of 115 flagged cases hit (16%); 16 of 115 repair texts hit |
| T1, extended by `covered`, `buys`, `lane`, `sprint`, "What is now true is" | 22 of 115 flagged cases hit (19%); 3 new hits in repair texts |
| T2, six construction patterns on the labelled set | 3 of 115 flagged cases (rows 3, 31, 84); 0 repair texts |
| T2, the same six on the probe | 4 of 14 lines |
| T2, the same six on the replies | The strict "but costs you none" form: 0. The broader forms: 0.1% to 5.3% |

Reading: extending the list buys four cases and costs three false hits. Construction detectors reach a handful of the 28 construction cases. A string list is the wrong instrument for that class.

### 3.3 Decision-point replay

Judgment of one reader (this agent), not a measurement. **Yes**: the strategy would have changed the decision at the point it was made. **Partly**: it would have caught the instance or class only in part. **No**: it would not have changed the decision. S4 is a multiplier and has no column.

| Incident | S0 | S1 | S2 | S3 | S5 | S6 |
|---|---|---|---|---|---|---|
| I1. Swim panel: population changed (2026-10-31) | No | No | No | Yes | Partly | Yes |
| I2. Essay Insight, ten rewrites (2026-10-30 to 31) | No | No | Partly | Yes | Yes | Partly |
| I3. "buys" as bad as "`carries`" (2026-10-26) | No | Yes | Yes | Yes | n/a | Partly |
| I4. "covered" where nothing is covered (2026-10-26) | No | Yes | Partly | Partly | n/a | Partly |
| I5. IRS letter, headings and labels (2026-09-29) | No | No | Partly | Partly | n/a | Partly |
| I6. Swim WHY restating the WHAT (2026-10-25) | No | No | Yes | Yes | n/a | No |
| I7. "`carry`" in the base form passed the list (2026-10-12) | No | Partly | Yes | n/a | n/a | Partly |
| I8. "What is now true is" (2026-10-23) | No | Yes | Yes | Partly | n/a | Yes |
| **Yes count** | **0** | **3** | **4** | **4** | **1** | **2** |

Reading: the instance list (S0) prevents none of the eight. S3 and S2 cover the most incidents at the decision point. S6 covers the cases a machine can see. S5 is narrow but measured.

### 3.4 The measured record

Insight agreement with Chaehan's scores: 0.41 to 0.54 before the removal test; 0.85 and 0.95 in the last two passes, both blind readings of the 26 settled essays. Mean absolute error on Insight: 0.22 and 0.12. The passes before the rewrite added prose and did not move it. This supports S5, and through its mechanism S3's fourth step. It is one criterion in one course, so the evidence is strong for that case only.

The robotic-complaint rate (1.5) is evidence against S0.

**The writing test (T6).** Four writing standards, each writing one output per scenario. Six judgments per standard: three scenarios, two blind judges per scenario, four unlabelled outputs per judgment. Scores run 1 to 5, 5 best. Decorative counts the sentences a deletion test removes. Mean rank runs from 1 (best) to 4 (worst). Standards: C0, the current rule 2; C1, rule 2 plus the checker's flagged words and the four words it misses; C2, five classes with a deletion test; C3, five object-first steps. Scenarios: A, a chat reply to the swim charge; B, one memory line for the free-swim price correction; C, one grading sentence giving the Insight score and its reason. Texts and judging record: Appendix C.

| Standard | Plain | Chain | Fidelity | Common sense | Decorative | Mean rank | Checker flags |
|---|---|---|---|---|---|---|---|
| C0 current rule 2 | 4.67 | 3.67 | 4.17 | 3.83 | 0.33 | 3.17 | 0 |
| C1 rule 2 plus word list | 4.67 | 3.83 | 4.50 | 4.33 | 0.33 | 2.33 | 0 |
| C2 five classes | 4.17 | 4.17 | 4.83 | 4.33 | 0.17 | 2.00 | 0 |
| C3 object-first | 4.33 | 3.83 | 4.50 | 4.50 | 0.33 | 2.50 | 0 |

Reading. C2 ranked first in three of six judgments and was never last. Its weak point was one dense paragraph in scenario A, which one judge scored 3 for plainness. C3 gave the best common sense, but it repeated the object name eight times in scenario A, and one output cut the quoted charge short. C0 ranked last on average, and it was the only standard whose output dropped "at most" from the Insight score in scenario C. The order changes by scenario: C2 ranked first in B, C1 and C3 tied first in C, and C3 ranked last in A in both judgments. The decorative count was 0 or 1 in every output, so it cannot rank the standards. The pass rule set before the run was not met on both measures: C2 and C3 beat C0 on common sense in B and C, and C2 beat C0 on decorative only in A. All twelve outputs had zero checker flags, so the checker could not separate the standards. Each cell is one draw; read these as direction, not proof.

### 3.5 Comparison

| Strategy | Incidents at the decision (T4, Yes) | Measured effect | Cost | Main risk | Verdict |
|---|---|---|---|---|---|
| S0. Keep adding | 0 of 8 | Complaints flat | None now, growing | A file the reader cannot use | Stop |
| S1. Word list | 3 of 8 | +4 labelled cases; +3 false hits (T1); no effect in the writing test (T6) | Low | Collides with Chaehan's vocabulary | Keep only inside S6 |
| S2. Five classes | 4 of 8 | Writing test: best mean rank (2.00 of 4) and highest fidelity; detectors weak (3 of 115) | Medium: examples, tests | Judgment tests skipped; one dense paragraph (T6) | Adopt as the wording module after two changes and a re-run |
| S3. Object first | 4 of 8, the two that matter most | Writing test: best common sense (4.50); repeats the object name (eight times in scenario A) | Medium: one short procedure | Checklist filled without reading; repetition | Adopt steps 1 to 3 inside S2, not in every sentence |
| S4. Layers | Multiplier | Not measured | High: one reorganization | A rule not loaded is not applied | Adopt, first in order |
| S5. Operational tests | 1 of 8, narrow | Insight 0.41 to 0.95 | Medium per concept | Needs Chaehan's definition | Adopt for graded concepts |
| S6. Mechanical gates | 2 of 8 Yes, 5 Partly | Swim check would fail the change; dash gate not measured | Medium per gate | Catches only what can be measured | Adopt for displays and output |

### 3.6 Recommendation

Order of work. Each step is small enough to finish and measure.

1. **Rearrange first (S4).** Write the always-loaded core (section 7 is the draft): the object steps (S3), the five classes with their deletion test (S2), the invariants and pointers. Move the instance log into the register, searchable and dated. Keep every quote; you confirm nothing you rely on is gone before the old text is removed.
2. **Replace rule 2 with the revised module (C2R), with every kind of the old rule kept by name.** Done 2026-11-02 (section 6). The balanced re-run (section 5) ranked C2R first in 11 of 12 judgments. Its fidelity is 5.00 against 4.25, and its decorative count is 0.00 against 0.83. It missed the plainness floor (4.33 against 4.5; C0 scored the same). Chaehan chose the replacement after that result was reported.
3. **Build the gates that do not need the reader (S6).** A marks differential for any chart or page change, and an output gate for dashes and banned words with an exception list for your terms, quotes and names. Run the 126 labelled cases and the probe as the regression set before any list changes.
4. **Apply the operational-test pattern (S5) to the next graded concept.** Insight is done.
5. **Stop adding instance rules.** A correction becomes: name the class, check which of steps 1 to 3 it falls under, and record the case in the register.

Why this order: S4 decides whether S2 and S3 are read. S6 works without the reader. S5 is the only part with a measured effect.

### 3.7 The answer to rephrasing and rearrangement

Both help (2.3). The replay supports rearrangement: the two strategies that cover the most incidents sit at the decision point, and the instance list sits outside it. The labelled cases support rephrasing: "robotic" hides five failures that need five instruments (1.4).

## 4. Limits of this round

- T6 used general writer and judge subagents, not the deepseek reader that wrote the October replies, so it describes a stronger reader. Each cell is one draw: one output per standard per scenario, two judges per scenario.
- The replay (T4) is one reader's judgment.
- The coding of the 100 misses (1.4) is one coder's.
- The census counts tool narration with replies. The construction counts are regex matches, with precision unmeasured.
- The 37% figure (1.7) is a keyword match. Seven of the 55 entries were read and hold.
- The labelled set is Chaehan's flagged phrases paired with the agent's repairs. Not every repair was accepted as written.

## 5. The writing test: design, and the re-run

- **Scenarios** (packets in Appendix C, facts only): A, the chat reply to the swim charge of 2026-10-31; B, one memory line for the free-swim price correction; C, one grading sentence giving Insight and its reason.
- **Standards**: C0, the current rule 2; C1, C0 plus the checker's flagged words and the four words it misses; C2, five classes with a deletion test; C3, five object-first steps. Each writer read its standard and its packet only.
- **Scoring**: two blind judges per scenario, four unlabelled outputs each, the rubric in Appendix C. The checker runs on every output.
- **Pass rule, set before the run**: a standard beats C0 on the decorative count and on common sense in at least two of the three scenarios, with no more checker flags. Result: met on common sense for C2 and C3; not met on the decorative count (3.4).
- **Re-run after the module changes (3.6, step 2)**: C0 against the revised five-class module on the same three scenarios and the same rubric. Adopt if the module's mean rank beats C0's and its plain score is not below 4.5 (C0 scored 4.67).

**Result of the balanced re-run, 2026-11-02.** The first judging put C2R in position P in all six judgments, so I reversed the order for six more (A3, A4, B3, B4, C3, C4); the outputs are the same. Twelve judgments: four per scenario, two per position. Scores run 1 to 5; decorative is a count, lower is better; mean rank runs from 1 (first) to 2 (second). The judging record is in Appendix C.

| Standard | Plain | Chain | Fidelity | Common sense | Decorative | Mean rank | First place |
|---|---|---|---|---|---|---|---|
| C0 current rule 2 | 4.33 | 3.58 | 4.25 | 3.83 | 0.83 | 1.92 | 1 of 12 |
| C2R revised module | 4.33 | 3.75 | 5.00 | 4.00 | 0.00 | 1.08 | 11 of 12 |

- Position: C2R was first in 6 of 6 judgments when in position P, and in 5 of 6 when in position Q.
- Scenario: C2R was first in 4 of 4 for A (the swim reply), 3 of 4 for B (the memory line), 4 of 4 for C (the grading sentence). Plainness is lower for C2R in A (3.75 against 4.0) and B (4.25 against 5.0), higher in C (5.0 against 4.0).
- Adoption rule (plainness not below 4.5): not met, 4.33. C0 also scored 4.33 in this run. Its floor was set on the first run, where C0 scored 4.67.
- Pass rule (beat C0 on decorative and common sense in at least two of three scenarios): not met. In A, C2R loses on common sense (4.0 against 4.5). In B and C the decorative count is 0 for both, so neither can beat the other.
- Insight ceiling: C0 gave it as a value in both runs. The first run dropped "at most". The re-run reads "E-07 scores 4.00 on Insight, the most allowed", which both judges read as an exact score. C2R kept "4.00 at most".
- Scenario B: C0 wrote two sentences for a one-line brief and dropped the Shinseok pool name. Both B judges gave it fidelity 5 while their reasons name the drop.
- Limits: three scenarios are three comparisons, so a clean sweep gives p = 0.125 (one-sided). The writers and judges were general subagents, not the reader that wrote the October replies. The rubric scores none of the detector kinds the module lacks (section 6), so the test cannot show what losing them costs.

## 6. Status and what waits on Chaehan

- Done: Rounds 1 to 3, the writing test (3.4), its balanced re-run (5) and the checker runs (3.2).
- Done, committed with this change: rule 2 replaced, with thirty-five kinds by name; the 49 old bullets, verbatim, in the examples section of common_sense.md; rules 244 to 251; the scope sentences in rule 21; a count sentence in rule 58; the rules.index.md rows, re-derived from the headings; one row in table two of common_sense.md; Failures 141 and 142, and the 2026-08-19 incident under Failure 19, in the register; the core installed (section 7), with the 62 bullets relocated (7.2).
- Not done: the checker (scripts/wording_lint.py) is unchanged.
- Kinds: the first count was twenty-two, the kinds the five classes do not state. Mapping all 49 bullets of the old rule found thirteen more with no name in the new rule: cleverness that needs a pause; explanatory preambles; filler phrases; container words; travel, freight and transaction words; abstractions where a person fits; consultant verbs and empty intensifiers; domain shorthand; verbs whose literal sense does not apply; analyst jargon; pointing back at the conversation; numbered asks in a letter; goals a session cannot deliver. Rule 2 now names thirty-five, and the count sentence in rule 58 is the rule that would have caught the first count.
- Waiting on Chaehan: his check that nothing was dropped in the relocation. Section 7.2 gives each bullet's home, and the reply shows what left each core section and where it now lives. Push: only when told.
- Smaller fixes, independent of the decision: correct common_sense.md (33 checks, not 28), rules.index.md (444 KB, not 199 KB), the duplicate rule numbers 205 and 221, and the duplicate register numbers. Give each register entry a model field.

## 7. The always-loaded core (installed 2026-11-03)

The core replaced the self-correction section of socrates.md, which loaded on every turn: lines 62 to 582 before the install, 6,968 words. Sections 0 to 8 are cross-project standards and now sit at the end of agentkit/AGENTS.md, which every session loads. Sections 9 and 10 are Socrates workflow and stay in socrates.md, under "Procedures and output rules", above its Formatting and Drafting subsections.

### 7.1 Installed text

agentkit/AGENTS.md, section "Core standards (every session)", holds sections 0 to 8. socrates.md, section "Procedures and output rules", holds sections 9 and 10. The text is not repeated here, so the two copies cannot drift.

### 7.2 Where the 62 bullets went

The 62 bullets are numbered in their order in the self-correction list. Every quoted phrase and date in each bullet was checked against the homes below, with 0 missing after the install. Rule numbers are RULES.md.

| Core section | Bullets | Where each bullet's instruction now lives |
|---|---|---|
| 0 When corrected | 1, 2, 12 | 1: core 7 and socrates.md section 10; 2: core 0 and socrates.md section 10 (merge, never replace); 12: rule 245 |
| 1 Answers | 5, 25, 30, 46, 50 | 5: rule 59; 25: rules 21 and 244; 30: rule 251; 46: rule 65; 50: rule 139 |
| 2 The object | 36, 44, 57, 61 | 36: register Failure 19, and kubs-deck skill step 2; 44: rule 144; 57: rule 142; 61: rule 109 |
| 3 Wording | 15, 17, 18, 41, 60 | 15: sourcing skill, names spelled out; 17: rule 2 and common_sense.md; 18: rule 2 (checker before every reply) and common_sense.md; 41: rule 116; 60: rule 106 |
| 4 Verify | 4, 11, 20, 23, 28, 34, 43 | 4: rule 58; 11: rule 249; 20: rule 246; 23: rule 248; 28: rule 15; 34: rule 63; 43: rule 143 |
| 5 Ask and act | 13, 14, 16, 21, 29, 33, 56 | 13: rule 176; 14: rule 102; 16: rule 5; 21: rule 9; 29: rule 102; 33: rule 62; 56: rules 140 and 141 |
| 6 Scope and files | 3, 31, 47, 48, 53, 54, 55 | 3: rule 10; 31: rule 56; 47 and 53: rule 69; 48: rules 3, 46 and 119; 54 and 55: rule 148 |
| 7 Records | 8, 26, 27, 32, 35 | 8: sourcing skill (email address); 26: rule 22; 27: rule 15; 32: rule 61; 35: rule 69 and socrates.md section 9 (notebook map) |
| 8 Outgoing text | 6, 7, 9, 10 | 6: socrates.md drafting section and common_sense.md; 7: rule 250 and sourcing skill; 9 and 10: sourcing skill |
| 9 Trigger procedures | 19, 22, 24, 37, 38, 39, 40, 42, 45, 49, 51, 52, 58, 59, 62 | 19: socrates.md section 9 and rule 246; 22: rule 247; 24: socrates.md section 9; 37: rule 64 and memory/kubs.md; 38: rule 125; 39: memory/kubs.md and rule 88; 40: kubs-deck skill step 3; 42: rule 157; 45: rule 154; 49: rules 67 and 127; 51: rule 147; 52: rule 149; 58: rule 68; 59: rule 105; 62: rule 104 and agentkit rebuild_defects.md |

## Appendix A. Probe

Each line is a test case. Lines 2 to 9 and 14 should be flagged; the rest should not.

<!-- verbatim -->
1. The left arm did not roll down in the needle. Because the left roll never completed, the right leg and hip did not lift up.
2. Wall posters carry the presentation.
3. The lipid reason for fish oil is already covered.
4. Past the hip the extra push buys nothing.
5. The team picks a lane for the search.
6. What is now true is a booked chain from Seoul to Melbourne and back.
7. The bias is watched, not switched off.
8. It is not just the swim, it is the whole week.
9. The leg-up block carries into the next week.
10. Insight is the understanding the method bought.
11. The return flight stays open on purpose, because it costs less bought near the date.
12. Your triglycerides were 85 and your LDL 67, so there is nothing there for fish oil to fix.
13. After the left-side breath, the left arm did not roll down in the needle.
14. The new cue adds one step but costs you none.
<!-- end verbatim -->

Checker output, current list: line 1 `leg`; line 2 `carry`; line 9 `carries` and `leg`; line 10 `Insight` (warning). Lines 3 to 8 and 14 are missed.

## Appendix B. How to reproduce

- Checker: from agentkit, `python3 scripts/wording_lint.py FILE`.
- Labelled set: rows of `common_sense.md` between "## The wording instances" and "## What the user had to call common sense" with five cells; columns 2 (flagged) and 4 (repair).
- Complaint rates: `SELECT substr(datetime(time_created/1000,'unixepoch','localtime'),1,7), count(*), sum(lower(data) LIKE '%robotic%') FROM session_message WHERE type='user' GROUP BY 1;` The "common sense" and "can't you see" columns use the same form.
- Reply census: `session_message` rows with type `assistant`, expanded with `json_each(data,'$.content')` where the part type is `text`; grouped by message id. The model sits in `$.model.id`.
- Register: entries begin `### Failure N`. Fields are the bold labels `**The principle.**`, `**The instance.**`, `**Why it happened.**`, `**The fix.**`.

## Appendix C. The writing test (T6): texts and judging record

Every standard is the shared frame plus its own body. C0 is rule 2 itself: RULES.md lines 137 to 218 at commit c27fcee. C1 adds its list to C0. C2 and C3 replace rule 2. Each writer read its standard and one packet, and nothing else.

Shared frame (above every standard):

<!-- verbatim -->
```
# The task

You write one text for the task in your packet. The reader is Chaehan, who reads English closely and rejects machine-sounding text. Write only the text the task asks for, into the output file your instructions name. No preface, no closing line, no heading unless the task asks for one. Use only the facts in the packet.

# Your writing standard
```
<!-- end verbatim -->

C1 body, added to C0:

<!-- verbatim -->
```
## Words and frames the checker flags

Write the plain thing each one stands for. Do not write these:
- the dash character, and a spaced triple hyphen used as a dash
- "it's not just", "it's not about", "the key is", "at its core", "when it comes to", "in order to", "the ability to"
- catalogue, taxonomy, inventory, pipeline, lever, modality, protocol
- leverage, utilize, ideate, operationalize, socialize, unpack, double-click, front-load, back-load, align on
- a label at the start of a line: Status, Why, Context, The mechanism, The counter, Atmosphere, Confidence
- plausible, not established; mixed evidence; high confidence
- "this message completes / responds / follows / is"; evidence trail; learnings; at the right altitude
- robust, holistic, seamless, comprehensive, cutting-edge, best-in-class, impactful
- carry, carries, carrying; leg, legs, runway, swimlane
- "the question / point / thing / part you named / raised / mentioned / asked"
- covered, buys, lane, sprint; "what is now true is"
```
<!-- end verbatim -->

C2 body, replaces rule 2:

<!-- verbatim -->
```
Check every sentence against five classes of robotic text. For each class, the test says what to do with a sentence it catches.

1. Construction. The sentence frames its point instead of making it: a contrast ("it is not X, it is Y"), an announcement ("what matters here is", "the key point is"), or a restatement of the sentence before it. Test: delete the framing clause. If the sentence says the same thing, the clause was decoration and stays deleted. If the sentence now says less, the clause held a claim: write the claim as its own sentence with a plain verb.

2. Vocabulary. A word a person would not say aloud to a colleague about this material (leverage, robust, seamless, covered, buys, lane, facilitate). Test: say the sentence aloud. If the word needs explaining, replace it with the thing it names: the action, the number, the object.

3. Content. A claim, number, name or step that is not in the packet. Test: point at the packet fact that supports each sentence. A sentence with no fact behind it is deleted, not softened.

4. Voice. Hedging, enthusiasm, apology, talk about the writer or the message, a formula at the start or the end. Test: delete it. A fact it carried goes into a plain sentence. If it carried no fact, the sentence goes.

5. Layout. Headings, bold labels such as "Status:", bullet lists or tables where the content is one or two sentences, and dashes used as punctuation. Test: if the content reads as one plain paragraph without loss, write it as one plain paragraph.

Write the text as plain sentences, each stating what was seen, why it happened, or what it changes.
```
<!-- end verbatim -->

C3 body, replaces rule 2:

<!-- verbatim -->
```
Before you write, take these five steps, then write the text from them.

1. Name the object as Chaehan sees it: the chart, the page, the file line, the essay, the set, the grade.
2. Name what the text touches, and what must stay the same as it was seen: the marks, the words he quoted, the test the criterion uses.
3. State the state at the point of change: what the object showed before, and what it shows after.
4. For a graded concept, state the test that separates it from its neighbour.
5. For prose, state the event: who or what did what, and what it changed.

Write each sentence about the named object, with its number or name and one fact per sentence. A sentence that would read the same about any other object is deleted.
```
<!-- end verbatim -->

Packet A (scenario A):

<!-- verbatim -->
```
# Task

Write the chat reply to Chaehan that answers his charge about the swim dashboard change of 2026-10-31. Open with his charge in his words. Then say what the chart showed before the change, what the change did to it, why the checks reported no change, and what the fix is. About 200 words.

# Facts

His words in that session: "you broke all panels!!! can't you see that??? isn't that common sense??? revert!!!!" and "keep strictly not change anything the chart showed" and "i told you to revert so that means you must read what was before your changes stupid!"

Before the change, the threshold panel showed threshold sessions only: 60% had 4 reps over 3 dates, 70% had 21 reps over 8 dates, and 90% had 11 reps over 4 dates.

The change added a filter that selected the 60% and 70% reps from every date. The panel then showed 60% with 117 reps over 71 dates and 70% with 187 reps over 60 dates, including sessions outside the threshold block. The 90% reps were already right.

The axis band moved from 2:02 to 2:32. The card was widened to full width, so the interval panel and the threshold panel were no longer side by side. The checks compared the y-range and tick settings, which were identical, and the test suite reported "583 passed, 1 skipped" four times.

The fix: plot the core reps under the effort they were measured at, as the 90% reps already are, and leave the set of dates alone.
```
<!-- end verbatim -->

Packet B (scenario B):

<!-- verbatim -->
```
# Task

Write one line for the Shinseok pool entry of the swim memory that records the price correction below. The earlier line stays in the file, and the new line says what it replaces. One line only.

# Facts

- The earlier note, dated 2026-09-14, gives the free swim as 115,000 KRW a month.
- On 2026-09-19 Chaehan corrected it: the free swim is 125,000 KRW a month.
- Records in this file are dated and appended. An earlier figure is superseded, never deleted.
```
<!-- end verbatim -->

Packet C (scenario C):

<!-- verbatim -->
```
# Task

Write one sentence for the grading record of essay E-07 that gives its Insight score and the reason for it. Use plain words.

# Facts

- Insight asks whether the essay's insights come from its method. The test is removal: take the method out of the essay. If the insights stand unchanged, the method did not produce them, and Insight is 4.00 at most.
- E-07 names its method in the second paragraph: a three-step cue (observe, name, adjust).
- E-07 has three insights: recovery depends on sleep more than on the extra session; pace drift shows fatigue before the split does; the first set of a session predicts the last.
- With the method paragraph removed, all three insights stand unchanged.
```
<!-- end verbatim -->

Rubric:

<!-- verbatim -->
```
# Judging

You judge one task. You see four unlabelled outputs, P, Q, R and S, and the task packet. Judge each output on its own terms, then rank them. Score each criterion from 1 (poor) to 5 (excellent):

- plain: a reader like Chaehan understands every sentence on first reading. Five means no word or phrase would make him stop.
- chain: the text states what was seen or changed, then why, then what it changes for the reader, in that order. A stand-in phrase where the event belongs scores down.
- fidelity: every fact used is in the packet, nothing is added, and every fact the task asks for is present.
- common_sense: the text says what could change and what could not, names the object concretely, and for the grading task states the test that separates Insight from the method.

Then count, without scoring:
- decorative: the sentences a deletion test removes without losing a fact or a decision (a sentence that frames, announces, summarises or restates).
- robotic: the one phrase that most sounds machine-written, quoted, or the word none.

Rank the four outputs from best to worst by your overall judgement, and give one sentence of reason for the best and for the worst.

Write your result as JSON to the result file your instructions name, with the keys P, Q, R and S, each holding plain, chain, fidelity, common_sense, decorative, robotic; and the keys ranking (the four letters, best first), best_reason and worst_reason. Read only the files your instructions name.
```
<!-- end verbatim -->

Judging record: the standard behind each unlabelled output, and each judgment's ranking, best first.

| Judgment | P | Q | R | S | Ranking, best first |
|---|---|---|---|---|---|
| A1 | C2 | C3 | C1 | C0 | C1, C0, C2, C3 |
| A2 | C2 | C1 | C0 | C3 | C2, C1, C0, C3 |
| B1 | C3 | C0 | C2 | C1 | C2, C3, C0, C1 |
| B2 | C0 | C1 | C2 | C3 | C2, C3, C0, C1 |
| C1 | C1 | C3 | C0 | C2 | C3, C1, C2, C0 |
| C2 | C1 | C2 | C3 | C0 | C1, C3, C2, C0 |

### Re-run record (section 5)

C2R is C2 with two edits. The object sentence goes above the five classes: "Before the classes: each paragraph names its object once, with its number or name, in its first sentence. Later sentences in that paragraph refer back to it without repeating the full name." The layout test becomes: "Test: if the content is one step, write it as one plain paragraph. If it has several steps (what was seen, why it happened, what it changes), give each step its own paragraph, in that order." The rest is C2. The packets and rubric are as above, with two outputs, P and Q, and a ranking of two.

Outputs, verbatim. C0 is the current rule 2 (RULES.md lines 137 to 218).

**Scenario A (the swim reply), C0, current rule 2**

<!-- verbatim -->
```
You wrote: "you broke all panels!!! can't you see that??? isn't that common sense??? revert!!!!"

Before the change, the threshold panel showed only threshold sessions. At 60% it showed 4 reps over 3 dates. At 70% it showed 21 reps over 8 dates. At 90% it showed 11 reps over 4 dates.

The change selected the 60% and 70% reps from every date, not only the threshold sessions. The panel then showed 117 reps over 71 dates at 60%, and 187 reps over 60 dates at 70%. Those reps now include sessions outside the threshold block. The 90% reps were already right.

The axis band moved from 2:02 to 2:32. The card was widened to full width, so the interval panel and the threshold panel were no longer side by side.

The checks compared only the vertical range and the tick settings. They did not check which reps or dates were plotted. Those settings were identical, so the checks reported no change. The test suite reported "583 passed, 1 skipped" four times.

The fix is to plot the core reps under the effort they were measured at, as the 90% reps are. The dates stay as they were before the change: threshold sessions only.
```
<!-- end verbatim -->

**Scenario A (the swim reply), C2R, revised module**

<!-- verbatim -->
```
"you broke all panels!!! can't you see that??? isn't that common sense??? revert!!!!" is your charge against the swim dashboard change of 2026-10-31.

The threshold panel showed only threshold sessions before the change: 60% had 4 reps over 3 dates, 70% had 21 reps over 8 dates, and 90% had 11 reps over 4 dates.

The 2026-10-31 change added a filter that selected the 60% and 70% reps from every date. The threshold panel then showed 60% with 117 reps over 71 dates and 70% with 187 reps over 60 dates, including sessions outside the threshold block. The 90% reps were already right. The change moved the axis band from 2:02 to 2:32 and widened the card to full width, so the interval panel and the threshold panel were no longer side by side.

The checks reported no change because they compared the y-range and tick settings, which were identical. The test suite reported "583 passed, 1 skipped" four times.

The fix is to plot the core reps under the effort they were measured at, as the 90% reps already are, and to leave the set of dates alone.
```
<!-- end verbatim -->

**Scenario B (the memory line), C0, current rule 2**

<!-- verbatim -->
```
On 2026-09-19 the free swim was corrected to 125,000 KRW a month. This replaces the 2026-09-14 figure of 115,000 KRW a month.
```
<!-- end verbatim -->

**Scenario B (the memory line), C2R, revised module**

<!-- verbatim -->
```
On 2026-09-19 the Shinseok pool free swim was corrected to 125,000 KRW a month, replacing the 115,000 KRW a month in the earlier line dated 2026-09-14.
```
<!-- end verbatim -->

**Scenario C (the grading sentence), C0, current rule 2**

<!-- verbatim -->
```
E-07 scores 4.00 on Insight, the most allowed: when the method paragraph is removed, its three insights stay unchanged, so the method did not produce them.
```
<!-- end verbatim -->

**Scenario C (the grading sentence), C2R, revised module**

<!-- verbatim -->
```
E-07's Insight score is 4.00 at most: all three of its insights stay the same when the method paragraph is removed, so the insights do not come from the method.
```
<!-- end verbatim -->

Judging record: which standard was in position P and in position Q, the order of the ranking, and each output's scores as plain, chain, fidelity, common sense, decorative.

| Judgment | P | Q | Ranking | P scores | Q scores |
|---|---|---|---|---|---|
| A1 | C2R | C0 | P, Q | 3, 4, 5, 4, 0 | 4, 3, 4, 4, 3 |
| A2 | C2R | C0 | P, Q | 4, 4, 5, 4, 0 | 4, 3, 4, 5, 3 |
| A3 | C0 | C2R | Q, P | 4, 4, 4, 4, 2 | 4, 4, 5, 4, 0 |
| A4 | C0 | C2R | Q, P | 4, 4, 4, 5, 2 | 4, 4, 5, 4, 0 |
| B1 | C2R | C0 | P, Q | 5, 4, 5, 4, 0 | 5, 4, 5, 3, 0 |
| B2 | C2R | C0 | P, Q | 4, 4, 5, 4, 0 | 5, 4, 5, 3, 0 |
| B3 | C0 | C2R | Q, P | 5, 4, 5, 3, 0 | 4, 4, 5, 4, 0 |
| B4 | C0 | C2R | P, Q | 5, 5, 5, 4, 0 | 4, 5, 5, 4, 0 |
| C1 | C2R | C0 | P, Q | 5, 3, 5, 4, 0 | 4, 3, 3, 3, 0 |
| C2 | C2R | C0 | P, Q | 5, 3, 5, 4, 0 | 4, 3, 4, 4, 0 |
| C3 | C0 | C2R | Q, P | 4, 3, 4, 4, 0 | 5, 3, 5, 4, 0 |
| C4 | C0 | C2R | Q, P | 4, 3, 4, 4, 0 | 5, 3, 5, 4, 0 |
