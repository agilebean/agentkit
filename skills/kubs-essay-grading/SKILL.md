---
name: kubs-essay-grading
description: Grade the KUBS DT final essays - the 35 percent individual round - on the five-point scale, regrade a single student, sweep the essay sheet, and build the course gradebook from the settled scores. Use when the user asks to grade or regrade essays, check an essay score, or rebuild the gradebook and its PDF. The team presentations round is kubs-grading, not this.
---

# KUBS DT essay round

Everything lives in the Drive folder "1 Projects/KUBS/KUBS DT/KUBS DT Grading"; the mirror
is `projects/kubs_dt/grading/` in the socrates repo, and it is never the deliverable.

- "final essays/" - 26 PDFs named by student number only, plus "backup 2026-10-26" and "top8"
- "KUBS DT final essays grading - anonymous.md" - the essay sheet: the reading model, the
  fixed rules, one row per student number, the computed distribution. **This is the only essay
  sheet.** A named twin and a dated twin were both retired; do not recreate either.
- "KUBS DT final presentations grading.md" - the team round's roster and settled team means. **Data only, and only at the gradebook step**, after every essay score is fixed; never open it while scoring
- "KUBS DT gradebook.md" + "KUBS DT gradebook - anonymous.md" + "KUBS DT gradebook.pdf" -
  the course grade, built from the two rounds
- "KUBS DT grade disclosure prompt.md", "KUBS DT grading insights.md", `_log.md`

The criteria, the weight of each and the word target come from the syllabus and "KUBS DT
session 2 - assessment.md", never from a previous round's summary row.

## Boundary with the team round

Two grading skills exist, one per round. **Load exactly one per pass.**

- This skill owns the 35 percent essay round and the course gradebook. The team presentations are `kubs-grading`: do not load it, and do not open its criteria table, its comparison rows, its full read or its recordings while an essay is being scored.
- The rounds share the folder, the letter scale and the record discipline. They share no criterion, no anchor and no deduction. This round's length charge, AI downgrade and signposting rule have no counterpart there; that round's half point for a mandatory slide and its room-reception test have none here.
- One file both rounds read: "KUBS DT grading insights.md". This skill reads the essay lessons - the traps list, the transferable-lesson rows and the essay reproduction prompt - and does not apply a lesson written for the team round.
- Nothing crosses in either direction. A team lesson never moves an essay score, and an essay rule never moves a team score. A correction taught on one round belongs to it; the other round waits for its own.
- The gradebook is this skill's job and it consumes the team round as **data**: the settled team means, quoted as they stand in the team file. A team score is never re-derived here, and an essay score is never re-derived there.

**Two entry points, one skill.** `/grade-essay` runs the scoring pass and never opens the team file;
`/gradebook` runs the gradebook step alone from settled scores and re-scores nothing. A scoring pass
never ends by building the gradebook, and a gradebook run never changes a number. `/grade-team` is
the other round's entry point, and it loads the other skill.

## What is being graded

A 1500-word personal learning journey, built from the learning journal, assessed on how personal
it is and on being the student's own writing. English quality is **not** scored - the syllabus
says so - and clumsy English that stays comprehensible is therefore never a defect.

| Criterion | Weight | The question it asks |
| :-- | :-- | :-- |
| Method | 30 | Did the student keep a learning journal and review their own progress and struggles across the four weeks? |
| Skill | 30 | Is the student's own analysis differentiated and non-trivial? |
| Insight | 30 | What did they come to understand that they did not before, and did it change anything? |
| Communication | 10 | Structure and clarity only: can a reader follow it, and is the reader shown the learning or told the plan? |

## The grader's model

Eight tests decide almost every point. They are statements about what a sentence *does*, so they
apply to an essay nobody has written yet.

**Every score is a quarter point.** 1.00, 1.25, 1.50 and so on to 5.00 and nothing between - the
settled sheet holds no other value, and a score like 4.10 is not a finer judgment, it is a number
nobody chose.


**1. The chain: prior belief, then the moment that broke it, then what changed.**
A stated lesson is worth nothing on its own. Method is satisfied by the student's own state at
each stage of the four weeks - "we were like, What? Why are we doing this?", "I kind of liked the
silent voting because we just had to put a sticker" - so a chronological walk through the course
is Method evidence, not a lack of structure. It fails only when the elements are listed with
nothing of the student attached, or when classmates' portraits displace the student's own review.
Skill is satisfied by a decision reported with its cause ("the button to call a family member has
made them feel a burden, so we shifted to seek a helper outside"). Insight is satisfied only when
the understanding arrives and something follows it.

**Method does not require a week-by-week form.** A review ordered by cause, by theme or by stage is
just as systematic as a calendar; headings, numbers and dates are formatting and earn nothing. What
Method asks is that the review covers the four weeks and that the student's *struggles* appear in it.
Separate the two things a walk can be made of:

- **A state** - what they found hard, got wrong, or did not expect ("the first homework was the
  hardest for me"; "I felt a lot of impostor syndrome for two reasons: energy loss and habit").
  A walk built of states is Method 4.50 and above, even when it lists every session in order.
- **A preference** - what they liked, enjoyed, or took away as a habit with no resistance ("more
  time with my child", "jogging", "new music"). A walk built of preferences, with no struggle
  anywhere, is Method 3.50 to 4.00 however complete its coverage.

Nothing in between counts as a flaw of organisation: an essay that recounts the course thematically
and names its struggles is not "a report", and one that names the weeks without naming a struggle
is not "systematic".

**A defence of one's share is not a review.** A student who missed a sprint and then spends the
essay establishing who wrote what ("I got in touch with my team members to find out what had
happened during Sprint 2", appendices offered so a grader can tell the student's work apart) has
documented an absence, not reviewed a progress: Method 3.00, and the same section costs
Communication under the band table below.



**2. An insight is what the method bought, not what the student felt.**
Method and Skill are read on how the student worked differently from their earlier approach - a
contrast the essay shows. Insight is read on what the new way of working let them understand: the
understanding they would not have reached without the interview, the reframe, the score, the sketch
test. Three questions, in this order:

- **Provenance.** Which step of the method produced this? Name it. If the understanding could have
  come from ordinary reflection, it is a changed approach (Method) and not an Insight.
- **Counterfactual.** What did the student believe before, and what would they have done without
  that step? An insight with no prior belief beside it is a remark, not a finding.
- **Ownership.** Whose is it? A team finding restated, or a teammate's or the professor's line
  quoted, is not the student's: 4.25 at most when restated, 4.00 when quoted.
- **Depth.** An insight that states what is true and stops is description. It needs the mechanism
  behind it and why it matters to this person; without either it sits in the 3.00 to 3.50 band,
  however true it is - and where in that band depends on how specific the description is (001 3.50,
  020 3.25, 022 3.00, set 2026-10-31).

**The removal test.** Take the method out of the essay and read what is left. If the insights stand
unchanged without it, the method did not produce them and **Insight is 4.00 at most**, whatever
their quality. This is the test that separates an essay that learned the method from an essay that
learned through it.

Count the insights next, then place the essay on the ladder:

| Rung | Trigger |
| :-- | :-- |
| 5.00 | three or more, each traceable to a method step, each with the prior belief and the decision it changed, each carried to what the student now does (064, 021) |
| 4.75 | the same with one finding fewer, or the reasoning shorter on one |
| 4.50 | two or three traceable findings, the reasoning behind each brief (013) |
| 4.25 | one traceable finding carried all the way, or a team finding the student turns on their own conduct (018) |
| 4.00 | a genuine understanding the method did not produce (a life lesson), a principle naming no action, or a quoted insight (019, 038) |
| 3.00 to 3.50 | a descriptive insight - true, with no mechanism and no personal relevance: 3.50 when the description is specific (001), 3.25 when it is thinner (020), 3.00 when it is a generic principle about the user group (022) |
| 2.50 | disclosure with no understanding, or one finding stated and then left (004, 007) |
| 1.50 | nothing understood: a maxim, or a defence of the writer's own contribution (034) |



**3. A maxim is not analysis.**
"It is important to listen before judging", "using a structured approach does not guarantee
reliable evidence", "observing what people do is one thing and making conclusions is another" -
each reads like a finding and asserts nothing about a specific decision. The test: could the
sentence be moved into another student's essay unchanged? If yes it is not differentiation.
A balanced abstraction that weighs two considerations and names no decision, no person and no
direction ("placing those considerations in relation to the user instead of allowing them to
replace the user's perspective") says nothing either.

**A confession is not analysis either.** Choosing to write about an awkwardness, a guilt or a
difficulty is a topic; Skill appears only when the student draws a distinction between two ideas
and says which one held. "I chose the awkwardness topic and named it avoidance" is the topic.
"I needed to question whether my ideas addressed a meaningful need, before showing their strength"
is the distinction - only someone who sat through that sprint could draw it.


**4. A tool named is not a tool used, and an intention is not a change.**
Method scores the application: an opportunity score computed at 12 and 7 and then checked against
other interviewees is Method; a list of Opportunity Score, Value Proposition Canvas and HMW that
"helped me think" is vocabulary and buys Method only, never Skill or Insight. Likewise a rewritten
interview question is proof the lesson landed; "I could do a mini Design Sprint... I haven't done
this yet" is a plan and scores as Insight below 4.00. Volume - 1600 words, nine numbered sections,
the most method references in the set - buys nothing on the other three criteria. Put ceilings on
it so it cannot creep back:

- The essay's analysis is mostly method vocabulary, restated steps or tool names: **Skill 4.00 and
  Insight 3.50 at most**, whatever Method earned.
- A tool is computed and then critiqued (an opportunity score worked out at 15 and questioned):
  that is Skill 4.50 and above, and it is the difference between the two essays above.


**5. Two things cost Communication, and grammar does not.**
Signposting: an essay that narrates its own architecture ("in the following, I will describe my
learning journey", "I have divided this section into two parts. First..., Second...", "Firstly,
Secondly, In conclusion", "in this essay, I wanted to talk about") tells the reader the plan
instead of showing the learning. Enumeration of content ("First, I will try to understand a
situation before making a judgment") is not signposting and costs nothing. And a gratitude
formula or compliments to the professor are an influence attempt, not a close. What also costs:
a close that restates the course, and a section spent defending one's share of the work
("I got in touch with my team members to find out what had happened during Sprint 2", appendices
offered so a grader can tell the student's work apart) - documentation of absence reads as
diligence and is neither Method nor Skill.

Place the essay in a band rather than subtracting ad hoc. The bands are the settled set's own:

| Band | What puts an essay there |
| :-- | :-- |
| 1.00 to 1.50 | the essay is addressed to the grader: a contribution defence, appendices offered as proof of authorship, a list of what the writer alone wrote, and writing that argues nothing |
| 3.00 to 3.50 | the reader is told the plan (signposting in most sections), or the essay closes on thanks, or a single thank-you line sits where the finding should be |
| 3.75 to 4.00 | readable throughout with one cost: classmates' portraits taking the middle, a section that repeats the course, the student's own sprint evidence left in an appendix |
| 4.25 to 4.75 | the learning is shown in order, the sections follow the argument, no plan is announced and nothing is addressed to the grader |

Charges are small and named; a single thank-you line costs half a point, not a band. A page given
to three classmates costs 0.75, and so does a section that restates the course. The student's own
sprint evidence left in an appendix is the same charge: the essay routes the reader away from the
proof it claims.


**6. Which of the book's ideas the student kept says how deep the reading went.**
Choosing long-term goal and HMWs - the first elements in the book, in the order they appear - as
the life takeaway is shallow. A habit change with no threshold crossed (more time with the child,
jogging, new music) cost nothing and is self-serving; a learning episode meets resistance.
Retrospective nostalgia - a digital detox taken years ago - describes a past, not a shift. Personal
disclosure is material, not a finding: a wife's pregnancy, a difficult father, "I was hurt too by
the interview. Not because of the interview but because of our past and our relationship" points at
a problem and stops.

**7. An insight quoted is not an insight arrived at.**
Kathi's "we usually jump right into solutions, but we should focus on what others really need",
the professor's "we shouldn't be biased by our own judgment": whoever says it, the student has
borrowed the authority instead of doing the work, and the criterion scores the doing. **Insight
4.00 at most** when the findings are quotations, however good the quotations. The same holds for an
essay that lists what the student liked - "I liked the warm-ups", "the lecture was helpful" - with a
professor's line under each: **Skill and Insight 4.00 at most**.
Disagreeing with the professor is not that, and costs nothing: the one essay in the set that says
the one-minute meditations did not help *is* showing its own judgment, and scores on it.

**8. An A needs one criterion at 4.25 or above.**
Every essay at A or A+ in the settled set has at least one criterion at 4.25 or higher, and no
essay whose best criterion is 4.00 sits at A. That single check settles most boundary calls: an
essay at 4.00 / 3.75 / 4.00 / 3.75 is 3.90 B+ and stays there, because the cheapest way to lift it
would push it above essays doing more. When a colleague asks whether an essay can be upgraded,
answer with that arithmetic and name the criterion that would have to clear 4.25 to do it honestly.

A score can also be **held for a reason that is not its reading** - a correction withdrawn because
of the seats it moved, a number kept to match a published state. The row's note says so. Do not
move such a number on a re-read, and do not re-propose a correction the record has already
withdrawn: say what the reading produces and that the record holds it for the other reason.


## The anchor set

Rules alone cannot place a number; these rows can. Read them before the first essay and compare
every new essay to them, saying in one line which anchor it sits above or below. They are the
settled 2026-10-28 read (001 and 004 re-read 2026-10-30), in the sheet's own order of quality.

| Anchor: criteria = score | What decided it |
| :-- | :-- |
| 2026972064 · 4.75/4.75/5.00/4.75 = 4.82 A+ | the most reasoning per insight in the set: observation, what it implies, what she does differently - every one taken that far |
| 2026417027 · 4.75/4.75/4.75/4.50 = 4.73 A+ | "the first homework was the hardest for me. I chose to interview my father... because it is hard to remove yourself from a problem that actively involves you"; impostor syndrome named as energy loss and habit |
| 2026417040 · 4.50/4.75/4.25/4.50 = 4.50 A+ | the clearest single depiction of Skill in the set; good insights with less reasoning behind each and fewer in total than 013 |
| 2026417017 · 4.50/4.50/4.50/4.25 = 4.40 A | the walk with her own state at each step ("by first developing a sense of affinity... I could speak in front of others without feeling self-conscious"), the silent-voting analysis, and an application specified to the day; 272 words short and still A |
| 2026417031 · 4.50/4.25/4.25/4.50 = 4.35 A | the opportunity score computed at 12 and 7 and checked against other interviewees - a tool used, not named |
| 2026417013 · 4.00/4.50/4.00/4.00 = 4.15 A | the sketching analysis is worth 4.50 Skill, but every change she names is still an intention and her own sprint sits in an appendix |
| 2026417039 · 4.00/4.25/4.00/3.50 = 4.02 A | opportunity score computed at 15 and then critiqued - real work - but the applications are plans ("I haven't done this yet") and the close is thanks |
| 2026417038 · 4.25/3.75/4.00/3.25 = 3.92 B+ | insights quoted rather than arrived at; "in this essay, I wanted to talk about" |
| 2026972164 · 4.00/3.75/4.00/3.75 = 3.90 B+ | the strongest single insight below the A line (the mother sprint) inside a list of what he liked, quotes from the professor, and a method half that contradicts itself |
| 2026417007 · 3.75/3.25/2.50/3.50 = 3.20 B | disclosure with no finding: the hurt reported, never explained; the record holds this number for a seating reason, not a reading one |
| 2026417012 · 3.50/3.75/3.50/4.00 - 0.73 = 2.89 C+ | handwritten, 674 body words, a reconstructed record with no dated entry; the length charge is arithmetic, not judgment |
| 2026417034 · 3.00/3.00/1.50/1.00 = 2.35 C | the essay's subject is the writer's share of a sprint he missed; a maxim is not Skill, a contribution defence is not Insight, and addressing the grader is Communication 1.00 |

2026417008 sits at 3.83 B+ on its four criteria with the two-grade AI downgrade charged on the
Total only, and 2026972154 at 5.00/4.00/3.50/3.75 = 4.12 A: the most method references in the set
buy Method 5.00 and nothing else.


## Writing: authorship, not detection

The syllabus's rule is a **two-grade downgrade**, and it is charged on the **Total** in the
gradebook, once. The essay keeps the score its text earned. No detector output is evidence.

- The tells are uniform, balanced, complex syntax with no awkward construction, and a concept that
  appears in neither the course nor its books ("The gift analogy had opened a door"; gift and
  empathy are not course material). Formulations that could be moved between essays count with them.
- The reverse is evidence of authorship: "This was of thinking is very important to me", ligature-
  broken characters, a complaint about the course's own logistics. A grader prefers these to a
  polished surface, so never mark down clumsiness - it is neither Communication nor authorship doubt.
- Handwriting is not an AI signal either way. A reconstructed record with no dated journal entries
  caps Method at 4.50, which is a Method finding, not an authorship one.

## Order: a score is only defensible in order

Score one file at a time, and before each new essay read it against the rows already recorded.
A number that contradicts its own evidence line is the miss this rule exists for: the essay whose
evidence said "the life takeaway is the book's first three elements" sat at Insight 3.75 while two
essays with the same defect sat at 2.50. When two essays are close, say in one line what puts one
above the other and leave the number where the evidence puts it - never move it to match a letter,
a curve, or a colleague's read.

**Rank continuously, not every tenth.** From the fifth essay on, every new essay is placed against
the batch already scored, and a number may move - the older one - when the new essay is clearly
better or worse than it. A pass that scores each essay on its own and checks only every tenth file
lets the first five set the centre, and everything after it clusters there.

## Use the whole scale

The settled set ranges 1.00 to 5.00, and most criteria are used to both ends: Insight reaches 5.00
three times and 1.50 once, Communication reaches 4.75 and 1.00. A batch whose four criteria all sit
between 3.25 and 4.50 has not been read; it has been averaged. Place each criterion on its rungs,
and let an essay take a low rung when it earns one.

**Method, six rungs.** The rung is set by whether a struggle the student names is acted on.

| Rung | Trigger |
| :-- | :-- |
| 5.00 | the journal kept across the four weeks, the struggle named at each stage, and the change carried into an application specified to the day (017) |
| 4.50 | the same walk with the struggle named and the application either specified or honestly absent; the student's own position at each step (021, 040) |
| 4.25 | a walk of states with the review of progress thin, or one section given to classmates (026, 038) |
| 4.00 | a thematic review made of states but with no account of progress, or a walk whose takeaway is the book's first elements with habit changes that cross no threshold (001, 020, 024) |
| 3.50 | preferences rather than states: what they liked, what they took away, with no resistance named (004) |
| 3.00 | a sprint missed and the essay spent proving who wrote what, or method vocabulary with no application (034) |

**Skill, five rungs.** The rung is set by whether a distinction is drawn, and how far it is carried.

| Rung | Trigger |
| :-- | :-- |
| 4.75 | a distinction only someone who did the work could draw, stated as a test: "sketching felt less like a drawing activity and more like a way to check how well I understood the problem" (013) |
| 4.50 | a distinction plus the decision it changed, or a tool computed and then checked against other interviewees (031, 017) |
| 4.25 | one clear distinction carried through a section (021, 038) |
| 3.75 to 4.00 | description of what happened with the analysis thin; a real observation that names no decision (001, 004, 020, 026) |
| 3.25 to 3.50 | maxim-shaped analysis, a sentence that could move into another essay (007, 022) |
| 3.00 | maxims as the body of the analysis, or tools named and not used (034) |

**Insight, seven rungs.** The rung is set by how far the best finding travels, then the count.

| Rung | Trigger |
| :-- | :-- |
| 5.00 | every finding carried observation → implication → what the student now does; the reasoning is there for each (064, 021) |
| 4.75 | the same chain but shorter on one finding, or one finding fewer |
| 4.50 | two or three findings carried, the reasoning present but brief (013) |
| 4.25 | one finding carried all the way, or good findings with less reasoning behind each (040) |
| 4.00 | a principle naming no action, a quoted insight, or a group observation with nothing turned on the student (019, 038, 040's lesser rows) |
| 3.50 | an observation about groups only, or a team finding restated as the essay's main point |
| 2.50 | one finding stated and left; disclosure with no finding (004, 007) |
| 1.50 | a maxim, or a defence of the writer's own contribution (034) |

**One verdict, three criteria.** Some essays are one thing wearing four columns. A contribution
defence is not a Method finding with an Insight question beside it: it scores Method 3.00, Insight
1.50 **and** Communication 1.00 together, because the same section is what costs all three. Read the
essay's subject first, and when it is the writer's share rather than the writer's learning, place
all three low in the same pass.

The 5.00 rung asks you to name the findings, not count them: if you cannot write down three
findings and the action each one changed, the essay is not there.

**Communication, five rungs.** The rung is set by the largest thing the reader meets.

| Rung | Trigger |
| :-- | :-- |
| 4.75 | clear and unhurried, every section showing learning, nothing announced and nothing addressed to the grader (021, 064) |
| 4.50 | the same with one soft spot (031, 040) |
| 4.25 | clean, with one charge: a short thank-you line, one section restating the course (017, 028) |
| 3.75 | one real cost: portraits taking the middle, the student's sprint in an appendix, a habit list with no thread (001, 004, 013, 020, 022, 024, 026, 029, 164) |
| 3.25 to 3.50 | thanks through the close, or signposting in most sections (007, 038, 039) |
| 1.00 to 1.50 | the essay is addressed to the grader: a contribution defence, appendices as proof of authorship (034) |

**Method and Skill are the crowded pair.** Most essays land on 4.00 or 4.25, which is why these two
produce the most inversions. Separate them with two questions, in this order: does the student name a
struggle in the review (yes → 4.50 and above, no → 3.75 and below)? and is the analysis a
distinction between two ideas or a description of what happened (distinction → 4.25 and above,
description → 4.00 and below)? Between two essays a quarter point apart, the one that names its
struggle earlier wins Method, and the one whose distinction could not be made by someone who did
not do the work wins Skill.

**The four criteria must differ.** In the settled set the best and worst criterion of an essay sit
0.68 apart on average, and 17 of 26 differ by 0.75 or more. A pass that gives one essay 4.25/4.25/
4.25/4.25 has stopped reading. Two criteria may share a value only when each has its own passage
that decided it.


## The arithmetic

| Item | Value |
| :-- | :-- |
| Essay score | weighted mean of the four at 30/30/30/10, then the length charge, floored at 1 |
| Essay letter | absolute, no curve: A+ 4.50+, A 4.00-4.49, B+ 3.50-3.99, B 3.00-3.49, C+ 2.50-2.99, C 2.00-2.49 |
| Length target | **1,401 body words**, not 1,500: the 99 free words come off the bottom, so the comparison is body against 1,401. Comparing body minus 99 against 1,500 is the bug that made the target 1,599 |
| Length charge | **0.001 per word short - 0.10 per 100 - off the essay score, floored at 1**: 674 words loses 0.73, 1029 loses 0.37. A closing remark about the journal is not essay text |
| Over-run | **no charge, ever.** The rules table names one and the settled rows never apply it: 15 essays sit above 1,500 words and not one is docked. Charge nothing, and if you were about to write a deduction for length above the target, delete it |
| Body words | title block, running headers, page numbers, a reference list and an appendix excluded; a closing remark about the journal is a remark, not essay text; a handwritten page is counted line by line from the image; text that prints without spaces is counted on its letters at 4.93 per word |
| Team | one value per team, the settled weighted mean on the same 1-5 scale; **Chaehan's row governs** over the AI read |
| Total | 0.65 x Team + 0.35 x Essay, less the AI penalty where one applies |
| Total letter | the top 16 rows of the Total ranking are the A family - A+ at Total 4.08 and up, A the remaining seats; below the family the absolute scale, so a Total under 3.00 reads C+ however few rows sit beneath it; a row with the AI penalty reads C+ |
| AI penalty | -2.00 on Total only, shown as "(-2 AI)" inside the Total cell |

Two rules that were corrected and must not drift back:

- **A shortfall comes off the essay score, an over-run off Communication.** An essay is judged as a
  whole, so missing words are missing content; running over shows the points were not brought
  across in the space the brief set.
- **The essay and the team are already on one scale**, so nothing is converted. A 1-5 mean stretched
  across a 0-100 band invents resolution the score does not have; that mapping was retired.

## The pass

1. **Say the cost before starting**: the number of files and the batch plan, one line. Work in
   batches of nine.
2. **Read blind.** Essays are keyed by student number. Do not open the gradebook, the roster's name
   column or any number-to-name map while scoring; the name goes on at the writing stage.
3. **Per file, before scoring**: extract the text, count the body words, and look at the pages -
   downscaled to a few hundred KB, never full size. A page that renders blank stops the file and is
   reported with its name and page number before any score; it is a question to ask, never a fact to
   record, and no substituted copy is scored in its place. The instrument is
   `python3 projects/kubs_dt/essay_pass.py --pdf PATH`: it prints the body count, the net count and
   the pages with no text layer. Use its count; a count typed by hand is the one that drifts.
4. **Score Method, then Skill, then Insight, then Communication**, each with the page and the words
   that decided it. Write the four before opening the next file.
5. **Charge a defect once**: length is the rule deduction and nothing else; a thin method is Method
   and not also Insight; an unclear structure is Communication and not also Method.
6. **From the fifth file on, place every new essay against the batch already scored** and move an
   older number when the new one is clearly above or below it, with one line on what separates
   them. Do not score the whole set file by file and sort it afterwards.
7. **Write the artefacts from a script**, never by typing rows by hand: the essay sheet, then the
   gradebook, its anonymous twin and the PDF. Every distribution table is computed on each build -
   a hand-kept count drifted three times in one round.

## The sheet and the gradebook

Essay sheet, one row per student number, no names:

| Student no. | Essay | Letter | Method | Skill | Insight | Comm. | Mean | Length | AI | Body words | Evidence |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |

The evidence cell names the page and quotes the words. For A and above, one thing that earns it;
below A, the element the essay lacks. An absence claim names the search that established it
("searched all 8 pages for 'journal': zero hits", RULES 222). A page that renders blank was reported
in the pass that found it (RULES 223).

Gradebook, one row per student, **roster order** (student number ascending, the LMS sheet's order),
each score cell reading criteria = score and letter:

| # | Student no. | Student | Essay | Team | Total |
| :-- | :-- | :-- | :-- | :-- | :-- |

- `3.75/3.75/3.25/3.75=3.60 B+` - the four criteria in Method / Skill / Insight / Comm order.
- Metric beside every letter, always. A table of letters without the number is rejected.
- No separate "absolute letter" column and no Why column: the Why lives in the essay sheet.
- The student number column repeats at the right edge if the table scrolls.
- Letters are plain text in the `.md`. Colour belongs to the PDF (RULES 228), and there are four
  tones: A+ and A green, B+ blue, B amber, C+ and C red, below C grey. The PDF is a render of the
  sheet, so a PDF one revision behind it is a defect.

## Guards

- **A grading file exists nowhere for the user until it is in the Drive folder.** Copy every write
  there in the same turn and match the two by checksum; the repo folder is the versioned mirror.
  The gradebook PDF lives in Drive only.
- **An accepted table's shape is frozen** (RULES 224). Change a value in it, never its columns;
  when he asks for a column back, restore the shape from his own earlier table, not from git history
  of your last output.
- **Never re-type a repeated row; copy it from the generator** (RULES 225), and read a modified
  tracked file before writing to it (RULES 226) - a second session may hold the same document.
- **A lesson he teaches in chat goes into the essay sheet's model section in the turn he teaches it**,
  with the essay it was taught on; a correction that lives only in the conversation is re-derived
  wrong on the next file.
- Text he will read goes through the robot-marker check:
  `mamba run -n socrates python3 ~/Software/Prototypes/agentkit/scripts/wording_lint.py FILE`
  ("Insight" as the criterion's own name is a known warn).
- An edit to `build_course_grades.py` or any `.py` triggers the full test suite (RULES 6):
  `mamba run -n socrates python3 -m pytest -q`.

## What this instrument can and cannot do

Measured by reading all 26 settled essays blind, in five passes, and comparing cell by cell. The
arithmetic reproduces exactly every time (both length charges to the point, every word count). The
four criteria, on the last two passes, which differ only in which fresh session read the batch:

| | Method | Skill | Insight | Communication | Essay |
| :-- | :-- | :-- | :-- | :-- | :-- |
| correlation (pass 5 / pass 6) | 0.91 / 0.97 | 0.87 / 0.91 | 0.85 / 0.95 | 0.95 / 0.98 | 0.94 / 0.98 |
| mean absolute error | 0.11 / 0.05 | 0.14 / 0.12 | 0.22 / 0.12 | 0.12 / 0.04 | 0.11 / 0.08 |
| values exactly on the sheet | 18 / 21 | 16 / 16 | 16 / 18 | 19 / 24 | 13 / 14 |
| letters right | | | | | 21 / 23 of 26 |

The jump came from reading Insight as **what the method bought** - the removal test - and not from
more prose: the passes before that rewrite sat at 0.41 to 0.54 on Insight and 0.45 to 0.51 on Skill.

What still moves between two readers: the essays whose settled score is itself contested in the
record (a disclosure held at 2.50 for a seating reason, a method-heavy essay held at 3.50). Expect a
row or two to swing 0.5 there, and treat the skill's number as the draft and the sheet as the record.



## Report

The table keyed by student number with the four criteria, the essay score and the letter; the bands
and the mean; every deviation from a settled score with the one line that explains it; and the
decisions that are his. Lean and specific, no filler, no names unless he asks to issue grades.
