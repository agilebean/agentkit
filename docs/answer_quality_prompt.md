# Make the agent answer from the reader's seat

A self-contained prompt for a high-end model that will change a personal agent's writing behavior. Read it end to end, then work. In this brief, the reader is Chaehan. The agent's rules live in `agentkit/`. Its user-specific prompt is `socrates/.opencode/agents/socrates.md`, and the failure register is `socrates/memory/agentic_ai.md`.

## 0. The task

You are improving one personal agent's writing. The agent works for Chaehan, and Chaehan reads everything it writes: chat answers, Evernote notes, memory files, reports, plans. The agent is accurate and complete, and its answers still fail. It reports the world in the order it researched it, shortens the list when asked to summarize, and leaves Chaehan to work out what the material means.

The example Chaehan gave on 2026-11-05. Chaehan asked whether the sperm frozen in 2020 is a better choice than a fresh sample at 56. The note names about twenty studies, each with its design and its effect, and the answer is at the end of the opening summary and again in the last section. Chaehan's verdict: "it cannot summarize yet studies in their gist but shows all details."

Your job is to change the instructions and the workflow so the next answer is selected from the reader's decision, not from the source. Deliver the change, not a commentary on it. Do not solve this with more rules about tone. The wording standard exists; the defect this brief targets is selection.

## 1. The test every answer must pass

After one pass, the reader can answer four questions.

1. What is true now?
2. What does it mean for me: what it costs, what it forecloses, what it makes possible?
3. What will I do, and what will I not do?
4. What would change my mind?

A text that answers only the first is a list of facts, however short. A summary is a new object, built backward from the answer. Its length is set by the number of decisions it changes, not by the number of facts read. Its last sentence states a consequence the reader could not have deduced from the facts alone.

A focused question still gets two sentences: the conclusion with its decisive number, then what follows. The four questions are the test of a summary, not a license to write four paragraphs.

Two words in Chaehan's complaints need definitions you can test.

**Human.** Read the draft aloud. A friend would say it in that many sentences, with those words, in that order. Report scaffolding is the main tell: a heading per part of the question, a bolded lead-in in front of a paragraph, a verdict label ("moderate confidence"), a premise announced as a noun ("The hole:", "The promising part:"), a closing formula, a sentence about the message or the analysis. Every one of those can be struck and the text improves.

**Intelligent.** The text does work the reader cannot do in the head: it ranks, computes, connects a cause to its consequence, and names the one fact that would reverse the conclusion. A summary that only restates what the source says is not intelligent, however accurate.

## 2. Who reads it

Chaehan is 55, Korean-German, a psychologist and AI researcher, and a professor. Chaehan is precise, impatient with filler, and checks claims against the record.

What Chaehan is trying to make true, as of 2026-11-05:

- **A family.** Chaehan is looking for a partner to have children with: warm, emotionally intelligent, inside a 15-year age gap. Two earlier relationships ended over children. The search runs through Korean matchmaking agencies, with a signed contract at J Noble and one failed first date.
- **A base.** Korea is home. A US green card is in the Frankfurt queue for a 2027 interview, and Melbourne is a winter block, not a migration.
- **Health.** Gluten is out since 2026-10-19 (barley, wheat including 파로 and emmer, rye, malt). Lactose is a standing intolerance, and lactose-free dairy is acceptable. LDL fell from 143 to 67 on a daily tablet. The right shoulder pulls on fast reps. A root-canal tooth waits for an X-ray.
- **Money.** US and Korean tax threads are open. CRWV and IREN must be sold this tax year to keep the ORACLE loss. A Seoul apartment in the 1.5 to 2.5 million dollar range is the next large purchase.
- **Work.** The KUBS design-thinking course closed at 150 hours. A spring 2027 Applied AI course is booked, and more Seoul workshops are the plan.

Standing constraints for any option: gluten-free, lactose-free, access, proximity, affordability, usability, and the terms Chaehan actually has to sign. An option that fails one is not an option, and its other virtues do not put it back in the running.

## 3. The seat test

The question "is this written from the user's perspective?" has five observable signals. Use them as tests, not as advice.

1. **The subject of the sentence is Chaehan's decision, body, money or time.** Not the agency's process, the study's design, the document's structure, or the agent's research path.
2. **A closed door is written as the reader's decision and its consequence.** "The Australian visa is closed" is the visa system's output. "You decided on 2026-10-14 to stop pursuing residence in Australia, so Melbourne is now a winter block and Korea is the base" is the state that matters.
3. **A refusal is written as what remains open.** "Duo answered the question by refusing you" calls a refusal an answer. Duo would not take a foreign passport, so that pool is closed; the question it was meant to answer, how many women aged 32 to 38 would meet a 55-year-old, is still open and moves to the next agency.
4. **A state is written with its consequence.** A contract with no decision after it is not a fact about the contract; it is the absence of a decision in Chaehan's file, and the reader needs to know what the next date can and cannot settle.
5. **Detail is admitted only if it changes one of the four questions.** If a sentence can move to a linked note without changing what Chaehan decides, it belongs in the note.

A scope is part of the fact. "Tadalafil is in use, not daily" is not "not in use". An absolute the record does not support is a false statement, and it costs more than the detail it saves.

Two send-time checks.

- **The stranger test.** If the paragraph could be sent unchanged to someone else, it is a report about the world, not an answer to Chaehan.
- **The Monday test.** If the reader cannot say what will happen on Monday after reading it, the summary is not finished.

Second person is necessary and not sufficient. The 2026-11-03 life overview says "you" throughout and still fails the seat test, because moving the pronoun did not move the subject.

## 4. What a gist is

A gist is the conclusion, the two or three facts that make it credible, and the one fact that would reverse it. Everything else is detail.

Seven rules follow.

- **Compress the world, not the user.** Published studies, vendor terms and public rules are the world: they can leave the page, one search away. Chaehan's dates, numbers, decisions, constraints and history are the user: every one survives, in the text or in the linked note. A mechanism that explains Chaehan's own experience stays; a paper's mechanism chain that a search returns stays out. Chaehan's own formulation: "you should just remove the details of studies, not my health details."
- **A study enters a personal note only as a meta-analysis, with its effect size and sample size.** Name a single study only when it decides the verdict or contradicts the pooled estimate. This is Chaehan's instruction verbatim: "in studies look only for meta-analysis, and report only effect size and sample size of meta-analysis."
- **Say what the evidence shows as a whole, not one finding at a time.** What agrees, what disagrees, which studies are larger and newer, and what that does to the decision. Twenty rows of design and effect are a literature log, not a synthesis.
- **Say what the evidence cannot say.** If every study splits at 45 or 50 and the comparison is 49 against 56, the per-year increment is unpublished and the decision rests on the direction. That sentence is worth more than the twenty rows.
- **Detail goes behind one link.** The section gives the state in one sentence, the consequence in one sentence, and a link titled with the note's exact name. No figure that lives in the linked note appears above it.
- **A subsumable point is indented under its parent, never a sibling.** Chaehan's words: "if a section contains a point that can be subsumed it must be indented as bullet point."
- **An unchecked candidate is labeled unchecked.** When there are more candidates than can be checked in the time available, the text reports how many are unverified, states none of them as a finding, and offers to check more. A checked finding outranks ten plausible ones.

The Takeaway of a state document is not a task list. Define it by its function: the paragraph Chaehan would say to a friend who asks "how is it going?". Four to six sentences with the one thing that decides the next month, what is now fixed, what changed since the last snapshot and why, and the risk that grows if untouched. The task table holds the actions. A Takeaway bullet that repeats a task row is a task, not a takeaway.

## 5. Three failures, with a plain form for each

These are the test cases. The current text is real. The forms below show the target, not text to copy: the model that implements this writes its own, and a form that keeps the source's metaphors, its invented mechanisms or a forbidden word has failed.

Four failures a rewrite of this material tends to keep. A metaphor where a physical event belongs is AI lingo ("the deadline lands on Friday"). A mechanism the source did not measure is invented ("the tablet flushes the artery"). A pronoun whose antecedent is not on the page is a defect ("it did the rest"). The marker list is binding. A verb the list marks as forbidden does not appear in a rewrite, even when it is the shortest word for "has".

### 5.1 The life overview: a Takeaway that is the task table

From the Evernote note "2026-11-03 Life Overview", written after the first relevance fix:

> No Seoul storage unit is booked, so the winter clothes and the green card documents have nowhere to stay from 2026-12-04 until you return: book the 공덕역 unit.

> The green card interview queue is in Frankfurt, for a February to May 2027 date that still fits the summer 2027 move.

**What fails.** Six Takeaway bullets correspond to six of the twelve rows in the Open tasks table. The Takeaway is the document compressed, and the document is a task list. The green card bullet is the tell: it states a condition, not an action, and reads as the odd line out. The skill defines relevance as "what it costs you if it is ignored", and a cost is always an unresolved action, so every item becomes a task. The one-sentence rule shortened the copies and did not change what they were.

**One plain form.**

> You fly in 29 days, and every flight is booked except the one back from Osaka in March.
> The KUBS grade entry is the one deadline this week: the appeal window closes tomorrow and nothing confirms the entry counted.
> Your clothes and papers have no home after 2026-12-04. The 공덕역 unit fits. One was left at the last check. The price and stock can only be confirmed at the payment step.
> What you want in a partner has not changed. A single date cannot tell you how many women aged 32 to 38 will accept the gap. The Gayeon consult is the next chance to answer it.
> The stock decision is made for this tax year: CRWV and IREN go, and ORACLE stays.

**What passes.** Each bullet says what the fact means. No bullet is a task row with its consequence stripped. The reader can say what the next month turns on.

### 5.2 The partner search: the agency's record instead of the search

From the same note:

> The J Noble contract was signed on 2026-10-24: 10 million won at signing and 30 million won at marriage, plus VAT (value-added tax). The one-year term is extended until marriage.

> The first date, on 2026-11-01, lasted 2 hours 50 minutes and was not worth pursuing. She had no interest of her own, gave verdicts without reasons, and asked nothing about what you are learning.

> No decision on the contract is recorded after that verdict.

**What fails.** The section reports a contract, a date and a licence, and never says what Chaehan is searching for, so it cannot say whether the search is on track. "No decision on the contract is recorded" is an absence in the file, not Chaehan's decision. The reader supplies the goal or leaves with a contract review.

**One plain form.**

> You are looking for a partner to have children with: warm, emotionally intelligent, and inside a 15-year age gap.
> The J Noble contract is signed. The first match had no interest of her own, which no profile can screen for.
> The agency described three traits and got all three wrong. Only the facts on the profile, such as birth year, school and job, can be trusted.
> One date does not tell you how many women aged 32 to 38 will accept the gap. The Gayeon consult is the next chance to answer it.

### 5.3 The paternal age note: twenty studies and the answer at the end

From the Evernote note "2026-11-05 Paternal Age and the Frozen 2020 Sperm Question":

<!-- verbatim -->
> Three findings, and one correction to what I said earlier.
>
> The paternal age effect on miscarriage is real, it travels in the sperm, and young donor eggs do not absorb it.
>
> My earlier claim that they did rested on one 2020 meta-analysis and one large Barcelona cohort.
>
> The DNA sequence is untouched, which is why the same vial still carries the genetic signature of the man at the age he banked it.
<!-- end verbatim -->

**What fails, sentence by sentence.**

- "Three findings, and one correction" describes the research, not the answer. The reader has to read on to learn what to do.
- "it travels in the sperm" is a metaphor. The physical fact is that the risk comes from the father's sperm, not from the egg.
- "young donor eggs do not absorb it" invents a mechanism. The studies compared miscarriage rates; none showed an egg absorbing anything.
- "My earlier claim that they did rested on" runs the pronoun and the verb together, so it reads as "they did rested". It also hides the correction: the earlier claim was wrong.
- The last sentence uses a verb the marker list forbids. Say "the sample still has the man's genetic profile from the age he banked it."
- The two tables give every study a row, so the three that decide the verdict look the same as the rest.

The same defects run through the note. "The damage happens at both ends" is a metaphor for cooling and warming. "The test is clean" is a metaphor for a study with no confounder. "Comes back null" is statistics shorthand for "found no effect". "Both samples sit inside the same open-ended band" is jargon for "every study puts both men in the 45-and-over group". The rewrite removes these, not only the summary's first paragraph.

**One plain form.**

> The 2020 sample is the better choice, if the bank still has it. It would give your child about 20 fewer new mutations than a fresh sample would. That is about 0.3 percentage points of absolute risk. The risk of miscarriage also rises with the father's age, and eggs from women in their twenties do not remove it. I earlier said the donor's age removed it. That was based on one 2020 meta-analysis and one cohort in Barcelona. A larger 2022 meta-analysis and a 2025 cohort of 1,712 donor cycles found the opposite. Freezing keeps the sample at the age it was banked: the 2025 cohort used frozen sperm and still found more miscarriage in fathers over 45. Nobody has measured the difference between 49 and 56, because every study splits at 45 or 50. The first problem is practical: storage was paid to 2023-11-06 and no extension is on record. Confirm the vials exist before anything else.

**What passes.** The answer is the first sentence, the size, the correction and the limit are in plain words, no metaphor and no invented mechanism survive, the forbidden verb is gone, and the storage problem is the first caveat, not the last section. The tables stay below, for the record.

## 6. Why the last fix changed little

The 2026-11-04 change added four sentences to the life-overview skill: relevance by cost, one-sentence Takeaway bullets, a link per detail note, and indented sub-points. The document it produced still has zero links, zero indented bullets, and six Takeaway bullets that repeat six task rows. The link and indentation sentences produced no observable effect, the relevance sentence produced the task table, and the one-sentence rule shortened the bullets without changing what they said.

The measured writing test explains the rest. The revised wording module ranked first in 11 of 12 blind judgments, with fidelity 5.00 against 4.25 and decorative language 0.00 against 0.83. Plainness was 4.33 for both. The gain was in how a sentence is written. No test measured what was selected, so the selection stayed as it was.

What was changed before this brief, and what it did:

| Date | Change | Observed effect |
| --- | --- | --- |
| 2026-11-03 | Rule 2 replaced by five wording classes and 35 named kinds; rules 244 to 251 added; the always-loaded core installed in `AGENTS.md` and `socrates.md` | The writing test ranked the new module first in 11 of 12 judgments; the complaint rate stayed flat |
| 2026-11-03 | Rules 195 (address the reader as "you"), 207 (an open item is checked in the record), 208 (a derived figure is recomputed); "TL;DR" renamed "Takeaway" | The overview is in the second person and its figures reconcile; it still fails the seat test |
| 2026-11-04 | Life-overview skill: relevance by cost, one-sentence Takeaway bullets, one link per detail note, indented sub-points; source gate; twin hash check; parsimony per object; note titles name the subject | 0 links, 0 indented bullets and 6 task-row bullets in the next snapshot; the source gate held |

A mechanical gap remains. No step ran the new sentences against the draft. The twin hash proved the copy was faithful and the source gate proved the claims had files; nothing checked what was selected.

The record around it:

| Signal | Value | What it says |
| --- | --- | --- |
| RULES.md, 2026-11-05 | 268 headings, 78884 words, 458294 bytes | The rule file grows faster than the behavior changes |
| "Robotic" complaints | 5.2 per 100 of Chaehan's messages in September, 4.2 in October | The rate did not fall as the rules grew |
| Register fixes where the rule existed or was not applied | 37 percent | A rule present is not a rule at the decision |
| Checker reach on the flagged cases | 18 of 115, 16 percent | Word checks miss the class |
| Misses that were not word problems | 76 of 100 | Construction, content, voice and layout dominate |
| Life overview note | 17174 characters, 0 links, 0 nested bullets, 33 list items | The link and indentation rules never reached the draft |
| Paternal age note | 15363 characters, about 20 studies, 2 tables | The literature was logged, not synthesized |

Three definitions were wrong, and each produced one family of defects.

1. **Relevance was defined as cost.** A cost is always an unresolved action, so the Takeaway became the task table and every workstream got a bullet.
2. **A summary was defined as coverage.** The skill listed what the Takeaway must mention (most urgent action, fixed commitments, one line per workstream), so the summary became the whole document compressed.
3. **User perspective was defined as the pronoun.** Rule 195 changed the third-person pronoun to "you" and the subject of every sentence stayed the agency, the study or the file.

Fix the definitions, not the sentences. The deployed reader is deepseek v4.1 flash, and the model may also be a limit. The test separates the two: give the installed model the finished draft and the gate. If it can run the gate and still ships a failing draft, the gate is in the wrong place. If it cannot run the gate, the gate must be mechanical. A rule that a strong model can follow by inference is no evidence that the installed reader can.

## 7. What to change in the architecture

1. **Put each standard at the step where the text is made.** A paragraph of guidance above a procedure is not read while the draft is assembled. In the life-overview skill, section 3 becomes four ordered moves: write the one-sentence answer, list the facts that change it, mark every remaining fact as detail with its note, then write the Takeaway last from the first two. The link, the indentation and the gist are products of those moves, not reminders beside them.
2. **Add one gate that fails on the finished draft.** Seven checks, each able to name the sentence it rejects: seat (T1), gist (T2), no task duplication (T3), one link per detail item (T4), no sibling that belongs under another (T5), no fact of Chaehan's lost (T6), the installed model reproduces it (T7). A gate that cannot name the rejected sentence is decoration.
3. **Give each standard one home.** The chain standard appears in `RULES.md`, in the `AGENTS.md` core and in `socrates.md`. Merge to one home and point from the others. A standard written twice is read as two standards and followed as neither.
4. **Redefine the three terms in place.** Relevance is impact on a live goal or a pending decision; cost is a symptom of it. A summary is the four questions of section 1, not a shortened list. User perspective is the seat test, not the pronoun.
5. **A dated record is not superseded.** `RULES.md` 31 and three lines in the life-overview skill order the deletion of the earlier snapshot. That is why the 2026-10-23 note was deleted and had to be restored. Write the exception: a dated snapshot records what Chaehan believed on that date; a rework issues a new date and leaves the earlier note and file untouched.
6. **The twin is written from the approved text.** The hash check proves the copy is faithful, not that the text obeys the skill. Both checks stay; neither replaces the gate.
7. **Stop adding numbered incident rules.** A correction becomes a class, a test and a gate. If a rule must be added, it replaces one. The file is 78884 words; the next correction adds no word to it.
8. **Design for a weak reader.** Steps, not principles. Few words in the always-loaded core. Mechanical where possible. Test on the installed model, not on yourself.
9. **Ask when the definition belongs to Chaehan.** What counts as important, what Chaehan is looking for, what a record must keep: these belong to Chaehan. Ask one question with options, and do not invent the answer. Chaehan's instruction: "ask in doubt with the question tool to narrow down what i mean."

The evernote skill needs the authoring step for a note link. It documents how a link is preserved and not how one is created, which is why a note with five detail items has zero links.

## 8. What not to do

- Do not add a rule per incident. The register holds 163 failure entries and the complaints did not fall.
- Do not restate formatting rules in the agent's prompt. It already holds them; the problem is that they are not at the decision point.
- Do not define importance as cost. It turns every fact into a task.
- Do not define a summary as coverage. It turns every workstream into a bullet.
- Do not move the pronoun and call it user perspective.
- Do not copy the previous snapshot for voice or content. It reintroduces the defect the last fix removed.
- Do not compress Chaehan's facts. The studies may leave; the dates, numbers, decisions and constraints stay.
- Do not claim a fix from a hash, a lint pass, or a field comparison. Those check the copy, the words and the fields, not what the reader sees.
- Do not write the change as a longer explanation of the change. The change is the revised instructions and the test result.

## 9. Acceptance test

Build the packet from the record, not from your rewrite. For each test, a blind judge reads only the target definition (sections 1 to 4) and the two texts, with the order randomized, and names the sentence that decided the choice.

| Test | Input | Pass rule |
| --- | --- | --- |
| T1 Seat | The partner-search section, current against rewritten | The rewrite wins, and the judge's reason names a sentence whose subject is the reader's decision |
| T2 Gist | The paternal note, current against a rewrite of 200 words or less | The rewrite keeps all three decisive facts (size of the mutation advantage, miscarriage effect survives freezing, storage lapse first) and names only the studies that decide the verdict or correct the earlier claim |
| T3 No task duplication | The rewritten Takeaway against the 12 task rows | No bullet can be replaced by a task row without losing the consequence; the judge can say what the month turns on |
| T4 Detail routed | The rewritten overview | Every detail-bearing item has one link; no figure that lives in the linked note appears above it |
| T5 Subsumption | The rewritten overview | At least one indented bullet where the record has a sub-point; no sibling that belongs under another |
| T6 No fact loss | Original and rewrite, diffed | Every date, number, decision and constraint of Chaehan's survives in the text or the linked note; only world detail may leave |
| T7 Weak reader | A fresh case given to deepseek v4.1 flash with the revised skill only | It produces a link, an indented sub-point and a non-task Takeaway without a human correction |

Report every failure. A partial pass is reported as partial. A test that cannot fail is removed, not kept as encouragement.

The blind judge may be a strong model or Chaehan. If it is a strong model, it must not see which text is new.

## 10. What to hand over

1. The revised always-loaded core in `agentkit/AGENTS.md`, target 1200 words or less, with the relocation of every removed sentence named.
2. The revised `agentkit/skills/life-overview/SKILL.md`: the four moves, the gate, the dated-record exception, and the three deletion lines removed.
3. The dated-record exception in `RULES.md` 31 and in `agentkit/skills/evernote/SKILL.md`.
4. The merge of the duplicated standards, with the home of each named.
5. The test packet and the T1 to T7 results, including failures.
6. A one-page report: what is now true for the reader, what waits on Chaehan, then the files changed.
7. The 2026-11-05 paternal note is the worked case: the implementing model rewrites its prose in the same pass, keeps both tables and every fact, and reads the note back to verify it.

Do not change a definition that belongs to Chaehan without asking. Do not change what an existing document or chart displays. Read the state before you edit: the 2026-11-03 note and its local file, the 2026-10-23 note, the paternal note, the two skills, rules 19, 21, 31, 54, 195 and 244, the core, and the socrates prompt.

## Appendix A. Chaehan's words

<!-- verbatim -->
Quality over quantity:

- "did you prioritize quality over quantity in every response so you rethink your answer including tables and charts not only in avoiding robotic wording but also what is the most straightforward way to answer the human, and what is the gist (rename the TL;DR title to Takeaway) as opposed to details that can be delivered after? You should understand that less is more."
- "you must get that your understanding about quality over quantity is not enough and not prioritized high enough, so reflect why and suggest changes which are not symptomatic."

Research:

- "for research questions, it doesn't help the human at all if you bring up lots of answers, but it bears 100x more weight that you doublecheck findings so you return a few but most robust findings."
- "the user perspective of access proximity, affordability, usability etc weighs 100x more than any uncorroborated finding."
- "it would be best if you report first findings as unverified if there are too many to research so your task finishes timely but can offer to search more."
- "highest priority to make the gist of knowledge very salient (in studies look only for meta-analysis, and report only effect size and sample size of meta-analysis), by putting the details (like studies etc.) as subordinate info which can be reduced to a min."
- "i feel you summarized too much the details of my health history. you should just remove the details of studies, not my health details."
- "why did you remove the key learnings and mechanisms? these are key to retain!"
- "too much clutter ... too little info: right shoulder and gluten bear almost no info!"
- "why did you not subsume the female orgasm timeline under sexual health where it belongs semantically?"

The life overview:

- "the takeaways contain too much detail which should be in the detail sections. if there is a detail evernote, it should show the link and only report the gist."
- "if a section contains a point that can be subsumed it must be indented as bullet point."
- "the writing still doesn't come from the user perspective - you must think what is most relevant for the human. ask in doubt with the question tool to narrow down what i mean."
- "Duo answered the question by refusing you - it just refused me, answered the question is non human. The Australian visa is closed - it means that i decided not to pursue living in Australia. the partner search: no user perspective at all. what is important for me?"
- "the 2026-11-03 is better but takeaway is the same as the tasks."
- "the sub bullets are not in."
<!-- end verbatim -->

## Appendix B. Evidence and files

| Source | What it holds | Date |
| --- | --- | --- |
| `socrates/memory/agentic_ai.md` failures 101 to 104, 152, 153 | Open items not checked, a plan reported as an event, a total not recomputed, third-person voice, claims without sources, single studies logged at length | 2026-10-23 to 2026-11-03 |
| `agentkit/docs/agentic_improvement.md` | The three rounds: rule growth, checker reach, the writing test, the strategies and the recommendation | 2026-11-03 |
| `agentkit/skills/life-overview/SKILL.md` | The four new sentences, the three deletion lines, the twin step | 2026-11-04 |
| Evernote "2026-10-23 Life Overview" | 6 long TL;DR paragraphs, prose sections, 13 task rows | 2026-10-23 |
| Evernote "2026-11-03 Life Overview" | 6 Takeaway bullets, 0 links, 0 nested bullets, 12 task rows | 2026-11-04 |
| Evernote "2026-11-05 Paternal Age and the Frozen 2020 Sperm Question" | About 20 studies, 2 tables, the answer at the end of the opening summary and in the last section | 2026-11-05 |
| `agentkit/RULES.md` | 268 headings, 78884 words, 458294 bytes | 2026-11-05 |
| `socrates/.opencode/agents/socrates.md` | The always-loaded user prompt | 2026-11-05 |
| Sessions "Life Overview Writing Rules" and "Life Overview Writing Rules 2" | What Chaehan asked for, the five defects, the introspection, and the changes made | 2026-11-04 |

The session records are in the OpenChamber session database at `~/.local/share/opencode/opencode.db`.

The 2026-10-23 note was deleted during the 2026-11-04 rework of the 2026-11-03 note, restored from the trash, and its body remains. The life-overview skill still orders the deletion in its trigger line and in step 4.4. The local document is still named `docs/2026-11-03-life-overview-NEW.md` while the note is "2026-11-03 Life Overview", so the twin and its source disagree on the title.

## Appendix C. Where the standards live now

| Standard | Current home | Problem |
| --- | --- | --- |
| The chain, effect then cause then consequence | `RULES.md` opening, `AGENTS.md` core 1, `socrates.md` | Three copies, none at the draft step |
| Five wording classes | `RULES.md` 2 | A list, not a gate |
| Answer first, two sentences | `RULES.md` 19 and 21 | Not applied to notes |
| Read-aloud reply test | `RULES.md` 54 | Chat only |
| Address the reader as "you" | `RULES.md` 195 | Pronoun, not seat |
| Checked findings, unverified labeled | `RULES.md` 244 | Research replies only |
| Relevance by cost | life-overview skill section 3 | Turns every item into a task |
| Takeaway coverage | life-overview skill section 3 | Turns the summary into the document |
| Link and indentation | life-overview skill section 3 | Never reached the draft |
| Dated notes are superseded | `RULES.md` 31, life-overview skill | False for a dated snapshot |
| Note link authoring | evernote skill | Documents how a link is preserved, not how one is created |
| Twin hash check | evernote skill | Proves the copy, not the compliance |
| Source gate | life-overview skill section 1 | Present and used |
