# Answer quality: test packet and results, 2026-11-05

The acceptance test of `answer_quality_prompt.md` section 9, run on the record. Every input below is the stored text of the note named; every rewrite was produced under the revised core (`AGENTS.md` core 1) and the revised life-overview skill. The blind judges were fresh model instances that read only the target definition (the brief's sections 1 to 4) and the texts, with the order of A and B randomized (seed 20261105) and the answer key kept out of their files. The mechanical checks are `skills/life-overview/scripts/overview_gate.py` and the fact diff in T6.

## Results

| Test | Result | What decided it |
| --- | --- | --- |
| T1 Seat | Pass, partial | The rewrite won. Deciding sentence: "The question it cannot answer, how many women aged 32 to 38 will meet you, goes to the Gayeon free consult, which is not booked." Two rewrite sentences still had the agency as subject; the licence line was rewritten after the judgment, the trait line was not |
| T2 Gist | Pass | The rewrite won at 196 words, with all three decisive facts and the storage lapse in its second sentence. It names four studies, all four part of the correction. Neither text gives the meta-analyses' effect size and sample size |
| T3 No task duplication | Pass on round 4, by Chaehan | The judge failed rounds 1 and 2 and passed round 3. Chaehan reversed it on tone: round 1 is the only conversational one, rounds 2 and 3 sound robotic. Round 4 keeps round 1's voice, rewrites its two robotic bullets, and passes the gate and the checker |
| T4 Detail routed | Pass after one fix | 6 links across the 4 sections that have detail notes; Money and admin and Virtual Friend have none and say so, as does the shoulder line under Health. The first draft showed 72090 won above the storage link, which the linked note holds; removed |
| T5 Subsumption | Pass | 8 indented sub-points where the original had 0 |
| T6 No fact loss | Pass after one fix | Gate run against the 2026-11-03 note: the 2025-11-09 immigration letter date was lost in the first draft and restored; every other date and number survives in the text or a linked note |
| T7 Weak reader | Partial | Deepseek v4.1 flash, revised skill only, no human correction: 7 links and 4 indented sub-points (pass); its Takeaway failed both "not a task list" and the seat test (fail) |

The mechanical gate was itself tested. On the 2026-11-03 note it reports 13 failures: 5 of the 6 Takeaway bullets that repeat task rows, zero links and every section unlinked, and zero indented bullets. Its T3 check catches literal repeats only. It flagged none of the three round-1 bullets the judge rejected, because they paraphrase their rows. The skill now says so, and the reading step stays the binding half of T3.

## T1: the partner-search section

Current (2026-11-03 Life Overview):

<!-- verbatim -->
### Partner search

- The J Noble contract was signed on 2026-10-24: 10 million won at signing and 30 million won at marriage, plus VAT (value-added tax). The one-year term is extended until marriage.
- The first date, on 2026-11-01, lasted 2 hours 50 minutes and was not worth pursuing. She had no interest of her own, gave verdicts without reasons, and asked nothing about what you are learning.
- The agency's profile blurb was wrong on all three traits it advertised. Only the structural fields count as verified: birth year, school, job, salary, family, height and address.
- No decision on the contract is recorded after that verdict.
- The Gayeon free consult is not recorded as booked. Its international marriage licence is listed on its signup page (recorded 2026-10-02).
<!-- end verbatim -->

Rewrite:

### Partner search

- You are looking for a partner to have children with: warm, emotionally intelligent, and inside a 15-year age gap.
- You signed with J Noble on 2026-10-24: 10 million won at signing and 30 million won at marriage, plus VAT (value-added tax), with the one-year term extended until marriage.
  - The first match, on 2026-11-01, met you for 2 hours 50 minutes and had no interest of her own, which no profile can screen for.
  - The agency described three traits and got all three wrong. Only the structural fields can be trusted: birth year, school, job, salary, family, height and address.
- You have not decided whether to stay with the contract after that date. The question it cannot answer, how many women aged 32 to 38 will meet you, goes to the Gayeon free consult, which is not booked; its international marriage licence is on its signup page (recorded 2026-10-02).
- [2026-10-23 J Noble registration w Chungshup](evernote:///view/39d2f74/s365/5083d582-d5f7-464a-c1f9-544d1e79c5e1/5083d582-d5f7-464a-c1f9-544d1e79c5e1/)
- [2026-09-19 Marriage Agency Benchmark](evernote:///view/39d2f74/s365/26357c1a-9b40-a7b4-60ae-f4e4372b3f0a/26357c1a-9b40-a7b4-60ae-f4e4372b3f0a/)

Judge, verbatim on the deciding point: "Text B never names the question at all. It reports the record instead ('No decision on the contract is recorded', 'The Gayeon free consult is not recorded as booked'), so the Gayeon line stands as a disconnected fact that would pass the stranger test, and B also drops the goal (children, a warm partner, the 15-year gap) that gives the section its point." Seat failures it found in the rewrite: "The agency described three traits and got all three wrong.", "Only the structural fields can be trusted: ...", and the licence clause. The licence clause was rewritten after the judgment with your decision as subject; the trait line still has the agency as subject.

## T2: the paternal note, summary against summary

Current ("Meta summary" of the 2026-11-05 note):

<!-- verbatim -->
Three findings, and one correction to what I said earlier.
The 2020 sample is genetically younger, measurably but small: about 20 fewer de novo mutations against a base of 70 to 100, which is roughly 0.3 percentage points of absolute risk on the outcomes paternal age drives.
The paternal age effect on miscarriage is real, it travels in the sperm, and young donor eggs do not absorb it. My earlier claim that they did rested on one 2020 meta-analysis and one large Barcelona cohort. The larger 2022 meta-analysis and the 2025 donor-oocyte cohort reverse it, and the check is set out below.
Freezing preserves the age of the sample rather than erasing it. The 2025 cohort used frozen sperm in all 1,712 cycles and still separated men over 45 from men under 45, which is direct evidence that a banked sample carries the man's age at banking, for better and for worse.
What stays unknown is the size of the 49-against-56 contrast. Every miscarriage analysis splits at 45 or 50, so both samples sit inside the same open-ended band. The only axis with a continuous per-year coefficient, the de novo mutation count, is the one where the absolute stakes are smallest.
What follows: the 2020 sample is better on both axes that carry a real coefficient, and the advantage is worth having but not worth planning around. Its first obstacle is not biology. Storage was paid to 2023-11-06 and no extension is on record, so whether the vials still exist comes before every other question.
<!-- end verbatim -->

Rewrite (196 words, judged; the note now carries a 115-word version written after your second correction, in the last appendix):

The 2020 sample is the better choice, if the bank still has it. Storage was paid to 2023-11-06 and no extension is on record, so confirm the vials exist before anything else.

- The 2020 sample gives your child about 20 fewer new mutations than a fresh one at 56, on a base of 70 to 100: about 0.3 percentage points of absolute risk on the conditions the father's age drives.
- The risk of miscarriage also rises with the father's age, and eggs from women in their twenties do not remove it.
  - I said earlier that young eggs removed it. That was wrong: one 2020 meta-analysis and one large Barcelona cohort said so, and the larger 2022 meta-analysis and the 2025 donor-egg cohort found the opposite.
- Freezing keeps the sample at the age it was banked: the 2025 cohort used frozen sperm in all 1712 cycles and still found more miscarriage over 45.
- Nobody has measured 49 against 56: every miscarriage study splits at 45 or 50. Only the mutation count is measured per year, and its absolute risk is the smallest.

The gain is worth having and not worth planning around.

The judge's only remark against the rewrite: "eggs from women in their twenties" is more specific than "young donor eggs". The note's donor-oocyte section states that donor eggs come from women in their twenties, so the phrase is the record's.

## T3: the Takeaway against the 12 task rows

Round 1 (failed):

- You fly to Osaka on 2026-12-04, in 29 days, and every flight is booked except the return from Osaka to Seoul in March.
- The KUBS grade entry is the one deadline this week: the appeal window closes on 2026-11-05 and nothing confirms the entry counted.
- Your winter clothes and the green card papers have no home in Seoul after 2026-12-04, and the only unit that fits had one left at the last check.
- What you want in a partner has not changed. One date cannot tell you how many women aged 32 to 38 will accept the age gap, and the Gayeon consult is the next chance to find out.
- The route is fixed until Valencia ends on 2027-06-30, and so is this year's share plan, which keeps the ORACLE loss on this year's return.

Round 2 (failed):

- The next month turns on leaving Seoul on 2026-12-04 with nothing loose. Your winter clothes and the green card papers need the one storage unit that fits, and if it is gone they have no place in Seoul until you return on 2027-03-25.
- Every booking through Valencia on 2027-06-30 is made but one: the March flight back to Seoul, whose business fare rises the later you buy it.
- The partner search is signed and still has no answer to the question that decides it: how many women aged 32 to 38 will accept the age gap. One date could not answer it, so the answer has to come from another agency's numbers.
- This year's share plan is fixed and keeps the ORACLE loss on this year's return.

Round 3 (passed by the judge, rejected by Chaehan):

- The next month turns on leaving Seoul on 2026-12-04 with nothing loose. Your winter clothes and the green card papers need the one storage unit that fits, and if it is gone they have no place in Seoul until you return in March.
- Every booking through Valencia on 2027-06-30 is made but one: the March flight back to Seoul, whose business fare rises the later you buy it.
- The partner search is signed and still has no answer to the question that decides it: how many women aged 32 to 38 will accept the age gap. One date could not answer it, so the answer has to come from another agency's numbers.
- What changed since the last snapshot is the share plan. On 2026-11-04 you chose to sell CRWV and IREN and keep ORACLE, because the 2026-10-03 plan would have bought ORACLE back within 30 days and voided its loss for this tax year.

Tensions the round-3 judge named and that remain: "made but one" sits beside the unpaid Melbourne bond, and "nothing loose" names only the storage unit.

Chaehan's verdict, 2026-11-05: round 1 "is the only one that has a conversational tone like you fly, your winter clothes, what you want, and only two robotic ones (grade entry is the one deadline, the route is fixed until valencia), the others sound more robotic." The judge checked function only, so it rewarded rounds 2 and 3 for writing the function into the sentence ("The next month turns on", "What changed since the last snapshot is"). The cause was the skill's own wording of Move 4, now fixed; the five shapes are marker rows.

Round 4 (gate pass, checker pass, accepted by Chaehan 2026-11-05: "Yes, it reads right"):

- You fly to Osaka on 2026-12-04, in 29 days, and every flight is booked except the return from Osaka to Seoul in March. That return costs more the longer you wait to buy it.
- Your KUBS grades may not have counted: nothing confirms the entry, and students can appeal only until 2026-11-05.
- Your winter clothes and the green card papers have no home in Seoul after 2026-12-04, and the only unit that fits had one left at the last check.
- What you want in a partner has not changed. One date cannot tell you how many women aged 32 to 38 will accept the age gap, and the Gayeon consult is the next chance to find out.
- You decided on 2026-11-04 to sell CRWV and IREN this year and keep ORACLE, so its loss still counts. The old plan would have bought ORACLE back within 30 days and lost it.

## T7: the installed model on a fresh case

Input: the facts of the 2026-10-23 Life Overview, the revised skill, and the list of detail notes, given to `opencode run -m opencode-go/deepseek-v4.1-flash#high` with the instruction to use no tool. Its Takeaway:

<!-- verbatim -->
- From 2026-10-23 the only hard date in the next five weeks is grading: the essay closed today, the five team reads must be in the S8 file by 2026-10-30, and appeals open on 2026-11-02, so a late file hands students a fight you have to answer.
- The winter is booked through 2027-03-01, and the one leg you left open, Osaka to Seoul on 2027-03-27, stays open because a business one-way gets cheaper nearer the date.
- Three questions closed since the last snapshot on rules you cannot argue with: Duo refused a foreign passport on 2026-10-11, every written Australian visa route failed its age limit on 2026-10-14, and the 2026-10-20 panel showed the daily tablet working.
- The risk that grows if untouched is the base you leave behind: with no locker chosen by 2026-12-04, the winter clothes and the green card documents have nowhere to sit, and the interview can be called from December.
- Money keeps one clock: the ORACLE loss only touches this year's gains if the sale lands in 2026, and the Anthropic window opens in November.
<!-- end verbatim -->

Gate: 7 links, 4 indented sub-points, and 2 T3 candidates (bullets 2 and 4). Blind judge: non-task Takeaway fail (bullets 1, 2, 4 and 5 map onto rows with a reason added), seat test fail on bullet 3, whose Duo refusal and visa line are written as the agency's and the visa system's acts, the two cases the brief opens with. Two of the judge's remarks are noise and do not change the verdict: it dated the case to 2026-11-05 instead of the case's 2026-10-23, and it read the 2026-10-23 share plan as an error.

Chaehan's read of the same Takeaway differs from the judge's on bullet 3: "this summary is good except the last point on panel is unclear bec it has no semantic info what tablet is it referencing". "Money keeps one clock" and "the next month turns" are "totally robotic".

What T7 leaves open is the brief's section 6 question: the model was not allowed to run the gate, so this run cannot say whether it ignores a failing gate or never reaches it. The next run gives it the gate script as a step.

## Appendix: the rewritten 2026-11-03 overview (input to T3 to T6), round 4

## Takeaway

- You fly to Osaka on 2026-12-04, in 29 days, and every flight is booked except the return from Osaka to Seoul in March. That return costs more the longer you wait to buy it.
- Your KUBS grades may not have counted: nothing confirms the entry, and students can appeal only until 2026-11-05.
- Your winter clothes and the green card papers have no home in Seoul after 2026-12-04, and the only unit that fits had one left at the last check.
- What you want in a partner has not changed. One date cannot tell you how many women aged 32 to 38 will accept the age gap, and the Gayeon consult is the next chance to find out.
- You decided on 2026-11-04 to sell CRWV and IREN this year and keep ORACLE, so its loss still counts. The old plan would have bought ORACLE back within 30 days and lost it.

## The route

| Place | Dates | Note |
| --- | --- | --- |
| Seoul | until 2026-12-04 | flight to Kobe, sold as Osaka, on 2026-12-04 |
| Osaka | 2026-12-04 to 2026-12-11 | Imperial Hotel, non-refundable, ¥141000 paid, 14:00 to 15:00 check-in agreed at no charge, booked 2026-10-07 |
| Melbourne | 2026-12-12 to 2027-03-01 | UKO Melbourne Central, unit 1102, 79 nights, lease signed 2026-10-07 |
| Osaka | 2027-03-01 to 2027-03-25 | lands 2027-03-02 at 12:10; return to Seoul not ticketed |
| Seoul | 2027-03-25 to 2027-06-15 | 83 days, the record's count |
| Valencia | 2027-06-15 to 2027-06-30 | two-week apartment; 2027-07-01 to 2027-08-30 is open |

Korea days in 2027 total about 165 against the 183-day line: 83 in this block and about 82 from mid-September to early December. The Applied AI course starts 2027-03-29, four days after the planned Seoul landing on 2027-03-25.

## Seoul storage

- From 2026-12-04 until you return on 2027-03-25, your winter clothes and the green card documents need a place in Seoul, and none is booked.
  - The 공덕역 slim unit fits them on a one-month minimum. Book it through the monthly link, because the branch page opens on the 12-month contract.
- [Seoul Mapo storage locker](evernote:///view/39d2f74/s365/431a56de-0a63-dcf4-a7fa-0e457c70b30a/431a56de-0a63-dcf4-a7fa-0e457c70b30a/)

## Running in parallel

### Partner search

- You are looking for a partner to have children with: warm, emotionally intelligent, and inside a 15-year age gap.
- You signed with J Noble on 2026-10-24: 10 million won at signing and 30 million won at marriage, plus VAT (value-added tax), with the one-year term extended until marriage.
  - The first match, on 2026-11-01, met you for 2 hours 50 minutes and had no interest of her own, which no profile can screen for.
  - The agency described three traits and got all three wrong. Only the structural fields can be trusted: birth year, school, job, salary, family, height and address.
- You have not decided whether to stay with the contract after that date. The question it cannot answer, how many women aged 32 to 38 will meet you, goes to the Gayeon free consult, which is not booked.
  - Gayeon lists an international marriage licence on its signup page (recorded 2026-10-02), so your foreign passport does not close that pool the way it closed Duo's.
- [2026-10-23 J Noble registration w Chungshup](evernote:///view/39d2f74/s365/5083d582-d5f7-464a-c1f9-544d1e79c5e1/5083d582-d5f7-464a-c1f9-544d1e79c5e1/)
- [2026-09-19 Marriage Agency Benchmark](evernote:///view/39d2f74/s365/26357c1a-9b40-a7b4-60ae-f4e4372b3f0a/26357c1a-9b40-a7b4-60ae-f4e4372b3f0a/)

### Health

- Your LDL (the "bad" cholesterol) is down to 67 on the daily Atobamib tablet, so the cholesterol question is settled for now.
  - [Cholesterol Blood Test Summary](evernote:///view/39d2f74/s365/01717603-9461-19c2-a468-9fa2c6b5797d/01717603-9461-19c2-a468-9fa2c6b5797d/)
- Gluten is out since 2026-10-19: barley, wheat including 파로 (emmer), rye and malt. Whether it is coeliac disease or a sensitivity decides how strictly you avoid traces, and that is still open.
- The green card medical exam still needs your hepatitis B and 2026-27 flu shots before the interview; the panel physician in Germany gives the polio dose at the exam.
  - [2026-10-14 Green card immunization records and what remains](evernote:///view/39d2f74/s365/9f180c40-d936-45c9-81b7-ccf4852399ca/9f180c40-d936-45c9-81b7-ccf4852399ca/)
- Your right shoulder still pulls mildly on fast reps, and the left has been quiet since 2026-08-20 (no detail note).

### Money and admin

- Your 2025 US tax return is still not posted. The Taxpayer Advocate Service (TAS, which takes cases the tax agency has stalled) has your Form 911 from 2026-09-30 and has not replied since its 30-day wait ended on 2026-10-30, so the next move is one email, not a second form.
- You decided on 2026-11-04 to sell CRWV and IREN before 2026-12-31 and keep ORACLE, because its loss counts only if sold this tax year. This replaces the 2026-10-03 queue (ORACLE, then IREN), where buying ORACLE back within 30 days would have voided the loss.
- In Korea, your 비거주자 (non-resident) confirmation request went by fax to 마포세무서 (Mapo tax office) on 2026-09-29 and its receipt is not confirmed. The immigration letter of 2025-11-09 set a response date of 2026-11-09, and it is met, since your case was complete on 2026-07-14.
- Anthropic's initial public offering (IPO) roadshow is expected from 2026-11-09, with the listing targeted before 2026-11-26. You have placed no order (no detail note).

### Furniture

- Your furniture left Los Angeles on 2026-09-30 and should reach Seoul between 2026-10-25 and 2026-11-09, at 25 to 40 days door to door; no arrival is recorded.
  - It clears customs under your ARC (foreign resident registration card), valid to 2029-11-29.
  - Whether the family can take in the marble table and the chandeliers at arrival is still to be asked.
- [2026-10-02 Move and Storage Record - Evernote Links](evernote:///view/39d2f74/s365/73caa3ff-6871-464c-a832-184219c226ce/73caa3ff-6871-464c-a832-184219c226ce/)

### Virtual Friend

- You cannot file the California charity renewal yet, and it is due 2027-02-15. The California Registry of Charities and Fundraisers withdrew its 30 September notice on 2026-10-09 as sent in error, its online service lists no renewal, and your web-form query of 2026-10-01 was still unanswered on 2026-10-31.
- The WhatsApp Business account stays blocked at Meta's business verification, which Meta Verified does not get around (no detail note).

## What went well

- The June exit stopped moving. It had gone from 2027-06-14 to 2027-06-17, then to 2027-06-15. On 2026-10-26 it was set from the central-region monsoon onset (Korea Meteorological Administration, 2015 to 2026, median 26 June), sized to the Valencia fortnight. The route above is the one you book against.
- The course ledger closed at 150 hours on 2026-11-02, grading included. Grading had been missing from the total until it got its own row of 21.5 hours (16.5 reading, 5 entry), which makes 18.75 hours per lecture across the eight lectures.

## Open tasks

| Thread | When | Waiting on | Next move |
| --- | --- | --- | --- |
| Seoul storage | before 2026-12-04 | you | book the 72090 won unit through the monthly link; confirm stock and price at the payment step |
| KUBS grades | appeals to 2026-11-05; confirmed 2026-11-09 | KUBS MBA office, minwoonam@korea.ac.kr | confirm the entry counted |
| CRWV and IREN | by 2026-12-31 | you | sell CRWV and IREN; ORACLE stays |
| TAS case | overdue since 2026-10-30 | US Taxpayer Advocate Service | email tas.form.911.request.for.assistance@irs.gov, subject "No Response", if no contact has arrived |
| Korea tax letter | while in Seoul | 마포세무서 | confirm the 2026-09-29 fax receipt; call +82-126 |
| Dental | next free Seoul day | you | X-ray and bite check for the root-canal tooth |
| Partner search | November | you | book the Gayeon consult and ask how many women aged 32 to 38 they hold for you first; sign nothing that day; upload the clean-shaven photos to J Noble |
| Furniture | by 2026-11-09 | forwarder and family, 조영일 (012780625@hanmail.net) | confirm arrival; ask about the marble table and chandeliers |
| Green card | from December | Frankfurt queue | watch the scheduling tool; ask for a postponement if a date lands before February 2027 |
| Virtual Friend charity | by 2027-02-15 | California Registry | file when the portal lists the renewal |
| Melbourne bond | 2026-12-12 | you | pay the first fortnight and the AUD 2740 bond |
| March flight | undecided | you | decide the March arrival, 2027-03-11 or 2027-03-25; the Osaka to Seoul business one-way is not ticketed |

## Appendix: the paternal note as written to Evernote, 2026-11-05

Written after the second wording correction (summary cut to the deciding facts, the correction of the earlier answer taken out of the note). Both tables are byte-identical to the stored note, and no date or number of the stored note is missing; read back from Evernote.

## Takeaway
The 2020 sample is the better choice, if the bank still has it. You must still call CHA Gangnam to confirm the vials are stored, because the storage was paid only to 2023-11-06.

- It gives your child about 20 fewer new mutations than a fresh sample at 56, about 0.3 percentage points of absolute risk.
- Young donor eggs do not remove the higher miscarriage risk of an older father, and a frozen sample keeps the risk of the age it was banked at.
- No study compares 49 with 56, so how much the seven years add to the miscarriage risk is unknown.

The gain is worth having, but not worth planning around.

## What a freeze-thaw is
The sperm is mixed one to one with a glycerol-based cryoprotectant, cooled at about one degree per minute to minus 80 C, and stored in liquid nitrogen at minus 196 C. On the day of use it is warmed to 37 C and washed free of the cryoprotectant. A freeze-thaw is that one complete cycle.
Cooling forms ice crystals and shrinks the cells as water leaves them. Warming exposes them to oxygen again, which releases a burst of oxidants. The measured costs are about half of the progressive motility, some breaks in the DNA strands, and fewer usable sperm per vial. That is why a thawed sample is injected into the egg rather than treated as equal to fresh for natural conception.
The DNA sequence does not change, so the sample still has your genetic profile from the age you banked it.

## The donor-oocyte check
Donor eggs come from women in their twenties, so the mother's age is the same across cycles and only the father's age varies. One cohort and one meta-analysis found no effect even above 50. Larger and later work replaces both.

| Study | Cycles | Result |
| --- | --- | --- |
| Begueria 2014, Hum Reprod, EUGIN Barcelona | 4,887 donor-ICSI cycles, donor under 36, 75% frozen sperm | No link between male age and miscarriage, pregnancy or live birth; miscarriage OR 1.06 per 5 years with the interval crossing 1 |
| Frattarelli 2008 | 1,023 anonymous donor cycles | Live birth down and pregnancy loss up above 50 |
| Luna 2009 | 672 donor cycles | Blastocyst formation and implantation down; miscarriage trend up above 60 |
| Sagi-Dain 2019, Clin Res Trials | 746 donor cycles | 50 and over vs under 40: clinical pregnancy OR 0.62 (0.39-0.95), live birth OR 0.59 (0.37-0.96); early miscarriage 22.8% vs 18.9%, not significant |
| Guglielmo 2025, ESHRE abstract, six centres in Italy and Spain | 1,712 first donor cycles, frozen sperm, single blastocyst transfer | Over 45: miscarriage 23.8% vs 16.3%, live birth 35.1% vs 41% |

Taken together, the father's age raises miscarriage and young eggs do not remove it. The no-effect result comes from one centre's 4887 cycles in 2014 and from the 2020 meta-analysis. The 2022 meta-analysis of 12 donor-oocyte studies and the 2025 cohort of 1712 cycles both find the effect, and the 2025 numbers are large enough to matter: men over 45 miscarried at 23.8% against 16.3%, and reached a live birth at 35.1% against 41%.
None of this gives a number for 49 against 56. Every study splits at 45 or 50, so both ages fall in the same group, and none can say what seven more years above 45 cost. The 2025 cohort is a conference abstract that looked back at records and reports no adjusted estimate, so the live birth gap could come partly from the recipient's age or the state of her uterus.

## The meta-analyses and systematic reviews

| Source | What it pooled | Effect and bearing |
| --- | --- | --- |
| Kong 2012, Nature (sequencing, not pooled) | 78 father-mother-child trios | 2.01 new mutations per paternal year; count doubles every 16.5 years. The 2020 sample carries about 20 fewer. |
| Wu 2017, Acta Psychiatr Scand | 27 studies | Autism plus 21% per 10 paternal years; seven years is about 14% relative, roughly 0.3 points absolute. |
| Miller 2011, Schizophr Bull | 3.0 million subjects, 14,568 cases | Schizophrenia RR 1.66 at 50 and over vs 25-29; 1.22 at 40-44. |
| Oldereid 2018, Hum Reprod Update | GRADE review of paternal factors | Small rise in birth defects, moderate certainty of evidence. |
| Bu 2023, congenital anomalies meta-analysis | Cohort studies | aOR 1.17 (1.12-1.21) above paternal age 44. |
| du Fosse 2020, Hum Reprod Update | 9 studies, adjusted for maternal age | Miscarriage RR 1.23 at 40-44 and 1.43 at 45 and over, reference 25-29. Both samples sit in the 45 and over bucket. |
| Murugesu 2022, Reprod Biomed Online | 28 studies, 32,484 cycles, 12 of them donor oocyte | In donor cycles, paternal age under 50 cut miscarriage (OR 0.68, 0.54-0.86). Reverses the 2020 null. |
| Morris 2020, F&S Reviews | Autologous and donor oocyte ART studies | Autologous: miscarriage up above 40. Donor: no increase even above 50. The donor arm is superseded. |
| Morris 2021, AOGS (single centre, not pooled) | 4,833 fresh autologous cycles | Paternal age over 50 lowered live birth (OR 0.67) but did not independently predict miscarriage (OR 0.68, 0.37-1.25). |
| Johnson 2015, semen quality meta-analysis | Studies across the male age range | Volume, motility and morphology fall with age; concentration differs between reviews. |
| Gonzalez 2021 review and Evenson 2020 | 19 studies, 40,668 men; 25,262 men | DNA fragmentation 19.5% at 40-49 and 26.8% at 50-59. |
| Petrushko 2023, cryopreservation meta-analysis | 52 studies | One freeze-thaw adds about 9 fragmentation points in normozoospermia. |
| Journal of Assisted Reproduction and Genetics 2026 | Storage cohorts | Up to 30 years of storage, no meaningful loss of motility. |
| Jenkins 2019, Epigenetics and Chromatin | Sperm methylome | Age-linked methylation patterns do not persist into the child. |

## What this does to the question
On the number of new mutations in your child, the 2020 sample wins by about 20, out of 70 to 100 in total. On miscarriage it also wins, because the risk comes from the sperm and survives freezing, but how much seven years add is unpublished. On telomere length the fresh sample wins, since older fathers pass on longer telomeres. On epigenetics neither wins: the methylation marks that change with age are erased after fertilisation and do not reach the child.
One freeze-thaw does not cancel the age advantage in pregnancy outcomes: the 2025 cohort saw the age effect through frozen sperm. It does cancel it in DNA fragmentation, where seven years of ageing and one freeze-thaw each add about seven to nine points. The two readings differ because fragmentation stands in for the outcome, and miscarriage and live birth are the outcome.

## The 2020 sample on file

- Frozen November 2020 at CHA Gangnam; semen analysis dated 2020-11-13.
- Storage paid to 2023-11-06; extension quoted at 30 for one year and 100 for three years in the 2020 note.
- No extension payment is on file after 2023-11-22.
- The analysis values (count, motility, morphology) sit in the receipt photographs, not in note text.
- First action: call the bank on +82 2-3468-3461 or 3462 and confirm the vials are still stored, before weighing which sample is better.