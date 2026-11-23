# Common sense inventory

The instances his corrections are built on, in two tables. Table two holds what he had to call common sense: the miss, his words, and what should have been obvious, and it gives the file its name. Table one holds what he flagged as wording: the phrasing, why he rejected it, the repair, and why the repair is better. Compiled 2026-10-03 from the KUBS DT folder logs (Course Design, S1 to S4), the session record of 2026-08-06 to 2026-10-03, and the RULES.md history; table two compiled 2026-10-12 from the session record of 2026-09-28 to 2026-10-12. The record has a gap from 2026-09-10 to 2026-09-23 (cleaned up on 09-25); the folder logs cover that window.

His words arrive through two channels, and both are searched: his messages, and his answers to the `question` tool, which are stored inside the assistant's tool results and are not user messages. A search over messages alone misses the answers - the 2026-10-12 table-width correction came in as one. The procedure sits at the foot of this file.

The user, 2026-10-03: "i gave hundreds of examples the last 3 weeks of robotic wording ... i had instructed that you keep an inventory and not only for kubs so you learn what is robotic and how to improve it!" The same standing order now covers table two, 2026-10-12: "from now on everything I said was not common sense, put all of that together", and the same day: "make sure to find all occurences of common sense i mentioned in all sessions".

The standard behind every row of table one: anything the user will read or hear must be understood on the first pass, without a pause and without asking what it means (RULES.md rule 48's test). The markers are the failures seen so far, not the whole standard. The standard behind table two: what a competent person does without being told. Every row is a thing the agent had to be told, so each names the judgment that was missing and where it now lives as a rule.

## The system

- `RULES.md` rule 2: the standing classes and the thirty-five kinds, each with its fix. The reference for the word "robotic". Their examples are in the section "Examples of rule 2's kinds".
- This file, table one: one row per wording instance: location and date, the flagged wording, why the user rejected it, the repair, and why the repair is better.
- This file, table two: one row per "not common sense" correction: date, what he flagged, his words, what should have been obvious, and the rule or repair it produced.
- Checker: `robot_markers.tsv` (this folder) holds the machine-checkable subset; `scripts/wording_lint.py` runs it on any file, in any project. The KUBS pipeline wraps it (`pipeline.py lint --session N`).
- Reading: a writer reads this file down to the heading "The wording instances": the standing repair instructions, the examples of rule 2's kinds, where the markers live and the search procedure. The two tables after it are searched for a precedent by a word or a date, and read whole only to append a row or to build a test set from them.

Maintenance: every new correction is appended at the end of its table in the same turn as one row. Table one: location and date, the flagged words, why the user rejected them (the user's words where the record has them), the repair, and why the repair is better. Table two: date, the miss, the user's words, what should have been obvious, and the rule or repair. Keep cells short: quotes are trimmed to the carrier fragment, one or two sentences per cell. A correction without the reasoning is incomplete; when the exchange carries none and the reason is not evident, ask before appending. A new class becomes a bullet in rule 2; a class a machine can catch becomes a row in `robot_markers.tsv`, checked by `scripts/wording_lint.py`.

## The user's repair instructions (standing)

- The why is the teaching (2026-10-03): "so you learn what is robotic and how to improve it". The user corrects a sentence to kill a class of mistake, not the sentence.
- Cut clutter, never the details that instruct students (2026-10-03): "you cut clutter but even more important without cutting details which are extremely important as instructions for students".
- Conciseness that keeps every fact (2026-10-03): "look for conciseness of wordings which don't lose any semantics but are more precise and concise". Earlier: "be more concise yet don't suppress any details" (2026-08-17).
- Keep the user's verbatim wording, never reformulate it (2026-09-29): "keep this, don't reformulate. i gave it to you so you learn not only about less robotic wording, but also the order of saying things". The user's wording also wins over the agent's shortened version: "students will complain if it's not clear. use my wording" (2026-10-01).
- Answer first, reasoning after (2026-08-23): "after the decision, the tentative answer should already be given right after, not at the end. after that, you can explain all the reasoning."
- Plain short form: "team exercise", "the three filters", "how it works", "the drawing is not what counts".
- One voice, the user's: "tell us (i am the prof, not we)" (2026-10-01).
- The instructor script carries what the user will say and when; it is a reminder for the user, not a report. Rules already announced elsewhere are not reiterated (2026-10-02, 2026-10-03).
- Two corrections on one subject store the learning (2026-10-18): "now i want an automatic detection after i corrected 2x or more your response wording or your precision that you store automatically the learning from that using exactly the previous wording I found good ... so in the future i shouldn't tell you that any more". Wording goes to table one with the accepted version verbatim, a procedural miss to the socrates register, and the records commit in the same session (rule 174).
- The verb is the tell (2026-10-26): "you still use the wording i hate: 'buys' is as terrible robotic as 'carries', give me 10 options for different cases to replace, and remember them". The class and its fix are in rule 2; the substitution by case is the table below. The same complaint also swept every instance already written in the session's artifacts, not only the sentence he quoted.

### Replacing buys and carries

Both verbs dress a plain gain, cost or transfer as a transaction or a shipment. Pick the row that matches what the sentence means, then write that verb.

| When the sentence means | Write | In a sentence |
|---|---|---|
| no gain from more of the same | adds nothing | "Past the hip, the extra push adds nothing." |
| a benefit one action returns | returns, is worth | "The drill returns a loaded left arm, not a faster 100." |
| what produced a result | did the work, drove it | "What did the work was the exhale, not the band session." |
| a cue that has to last into the next set | stays on, holds | "The roll cue stays on into the main set." |
| a cost that arrives later | shows up in, reaches | "Soreness shows up in the next day's threshold set." |
| time or distance won | gains, wins | "It gains two seconds per hundred." |
| a constraint that removes options | rules out | "The left shoulder rules out the swing this week." |
| relative importance | matters most, counts most | "The roll matters most. The catch follows it." |
| a claim that fails | does not hold, does not survive | "That reading does not hold after two sessions." |
| a load or a role | takes the load, puts the weight on | "The left arm takes the load in the drill." |

## Examples of rule 2's kinds

Moved from RULES.md rule 2 on 2026-11-02, in its own words: all 49 bullets of the old rule, so the text of every kind is kept. Rule 2 names each class and kind and its fix; the cases behind them are here.

### Introduction

- **Filler transition** ("through X and Y, students gain Z"): the introduction example of rule 2.

### Punctuation and rhythm

- **Three-item runs** ("faster, clearer, stronger"). Say the one thing that matters.
- **A comma followed by an "-ing" clause that carries a second action** (", magnesium relaxing the muscle and the stretch lengthening it"). Two sentences squeezed into one. Write them out in full.
- **Cleverness that needs decoding.** If a line is clever and needs a pause to parse, the cleverness is the wrong trade. Test: could the user ask "what does this mean?"
- **Em-dashes, and " --- " used as a substitute.** Write periods and short sentences.
- **Semicolon chains.** Split into sentences.
- **Long sentences with embedded clauses.** A stacked relative clause makes the hearer decode: "the routine of someone living alone who wants to keep one" forces "one" back to "routine". Write "the routine of someone living alone".

### Document scaffolding

- **Headings over paragraphs**, in a note, a reply or a letter ("What the account shows.", "Why this meets the criteria.").
- **A section per part of the question.** A balanced report where one answer was due.
- **Label prefixes** ("Status:", "Why:", "Context:", "The mechanism:", "The counter:", "Atmosphere:").
- **Bolded lead-ins in front of a paragraph.**
- **Colon-field blocks in prose** ("Taxpayer: ... SSN: ... Return: ..."), a form pasted into a narrative. In a text that stands alone as a submission, the labeled identifier line is the format, not the marker (rule 85).
- **Numbered or bulleted asks inside a letter.**
- **Telegraphic fragments instead of sentences.**
- **Vague readiness instructions** ("have the itinerary open", "keep that at hand"). Name the document, where it is kept, and the moment it is shown: "the e-ticket for the 11 December Osaka-Melbourne flight, saved as a screenshot on your phone, to show at the check-in counter if the return date is questioned." The user, 2026-10-07: "too robotic to use the word open, be specific."
- **Third-person summary voice** about the person being written for.

### Report and rubric language

- **Verdict labels** ("plausible, not established", "mixed evidence").
- **Confidence rituals** ("Confidence: moderate", "high confidence on X"). State the call; genuine uncertainty becomes the fact that would change it.
- **Premise labels** ("The hole:", "The promising part:").
- **Rubric labels taken from an institution's manual** ("Reason 5", "the criteria", "criteria 5 and 7").
- **Narration about the message itself** ("this message completes my earlier request").
- **Explanatory preambles** ("since we will book soon...") and **embedded justifications** ("the quote is two months old, so...").
- **Conditionals built from the analyst's logic** instead of the reader's.
- **Metaphor labels** ("the evidence trail"): name the thing - "what you found out".
- **Stand-in phrases that name no object** ("that ends it", "wording settles it", "a picture built on a file", "words the same failure", "the mechanism was retired"): name the object, the operation and the result - "the check that disproves each", "the file was not opened at startup". The user, 2026-10-18: "the wording is too imprecise, you use a clear technical and logical language, not vague and robotic wordings like 'that ends it', 'wrong paths', 'a picture built on a file'".
- **Rows built from the method's components** ("the interviews, the ratings, the score, the prototype"): a criterion names the quality being judged and the symptoms that show it, never the steps of the process.
- **Collective voice where one person acts** ("tell us why", "we grade"): write the one actor ("I grade"), or the direct imperative ("explain why"). The professor is one person, not a team.

### Vocabulary

- **Travel and transport words borrowed for ordinary work:** lane, leg, runway, track. A search for a partner is not a lane, a return flight is not a leg, a period of weeks is not a runway. Name the thing. The user, 2026-10-23: "still a lot of robotic wording ... the words lane and leg".
- **Abstractions where a person or an action fits:** artifact, deliverable, learnings, insight, alignment, journey, problem space, solution space, touchpoint, friction, granularity, altitude ("at the right altitude"), needs-first, end-to-end.
- **Consultant verbs:** leverage, utilize, facilitate, ideate, operationalize, socialize, surface (a need), unpack, double-click on, align on, drive (a change), enable, empower, front-load, back-load ("front-loads quality": say what comes first, "the hard sessions come first in the week").
- **Transaction and freight verbs where a gain, a cost or a transfer is meant:** buys, pays for, carries, carries over, carries weight. "Past the hip the extra push buys nothing" reads as a purchase and "the leg-up block carries into the next week" as freight. Say what the thing gains, costs, returns, stays on, or shows up in: "past the hip the extra push adds nothing". The substitution by case is the table in `common_sense.md`, "Replacing buys and carries". The user, 2026-10-26: "'buys' is as terrible robotic as 'carries'".
- **Nominalizations:** "the collection of", "the utilization of", "the implementation of", "an improvement in". Use the verb: "we collect", "you improve".
- **Empty intensifiers and hedges:** robust, holistic, seamless, comprehensive, cutting-edge, best-in-class, impactful, meaningful, significant, truly, deeply, arguably.
- **Domain shorthand outside its own trade:** SKU, COGS, BOM, SLA, arm (in a study, write "test group"), agent (of an illness, write "cause"). Exercise-physiology and coaching terms go the same way: concentric, eccentric, DOMS, supported or unsupported (of a stroke), muscle damage marker. Say what the body does and what the world does to it: "the arm muscles only shorten as they pull", "nothing lands on the body", "a blood test that rises when muscle is damaged". The user, 2026-10-26: "what do you mean with concentric swim and supported, again incomprehensibel".
- **A verb whose literal sense does not apply:** covered, handled, addressed, lives, sits, where nothing is physically covered, handled, sitting or living, and a fact is standing in for the picture. "The iron reason for the supplement is already covered" makes the reader rebuild which thing was covered by what, and it says nothing about the blood values. Write the fact: "your iron and ferritin are already normal, so there is nothing there for the supplement to fix". Test: can the verb's picture be drawn? If not, it is a stand-in. The user, 2026-10-26: "do not EVER use the word 'covered' if it doesn't mean covered!!! this is common sense".
- **Analyst jargon in user-facing prose:** benign, sub-clinical, protocol signal, fictional payoff, eliminated by error analysis, tail (of a dose or an effect: write "some of it is still in the blood later").
- **Trade slang kept out of speech:** "run of show" (write "the session plan"), "the block that stretches" (say what happens when it runs long), "shaded blocks" (say "after the break"), "in reading order", "on purpose" (write "deliberately").
- **A program's own names in a reply about it.** Say what the code does for the reader, not what it is called inside the file: "it draws every page in one pass and compares them with the last accepted run", not "one-launch stacked capture" and "the baseline gate". A file name, a flag or a function name appears only when the user has to type or open it. The user, 2026-10-20: "mind all the rules for non-robotic wording and responses in plain terms!"
- **Container words that name a list instead of being one:** catalogue, inventory, taxonomy, matrix, framework, pipeline, mechanism, protocol, lever, modality. Name the thing: "the three filters", "how it works".
- **Japanese and other non-Latin names without their reading:** give the romanized reading first (Kawaramachi), and keep the characters only so the name can be pasted into a map or a search (京都河原町). A name the user cannot read carries no information. The user, 2026-10-04: "i can't read the hotel names in japanese."

### Formulas

- **Fake-sentence patterns:** "It's not just X, it's Y"; "It's not about X, it's about Y"; "The key is..."; "At its core..."; "when it comes to"; "in order to" (write "to"); "the ability to" (write "you can").
- **Contrasts built for sound:** "bias is watched, not switched off"; "the filters cost you more on Wednesday"; "this week is the sprint, not the book". Write the plain fact: "you cannot switch bias off"; "you get one hour with a stranger and no second chance"; "the reading comes Thursday, in the sketch session".
- **Pointing back at the conversation** ("The second question is the subtle one you name", "the point you raise", "as you said"): state the content. The sentence's job is the subject, never the exchange it arrived in.
- **Formal greeting and closing formulas** in messages the user sends (매니저님, 안녕하세요 / 검토 부탁드립니다, 감사합니다). The body only.
- **Metaphors that give an abstraction agency, and absolutes about it:** "where bias enters an interview" claims one overall bias that is completely known. Write what the person does: "knows several biases in interviews". Same shape: "the session only reaches tomorrow's set" hides a harm behind a movement, and the reader inverts it; write "it would only hurt tomorrow's set" (2026-10-09).

### Voice in first-person text

- **Commentary on the writer's effort, frustration, willingness or hope, and the idioms that carry it:** "I have run out of ways to move it myself", "if that is what it takes to move it", "which puts me under real pressure to close this now", "I would rather resolve this with your office than anywhere else". The formal first person states facts, positions and requests: "I need a clean US tax record", "I prefer to resolve this with your office", "I reserve all rights and remedies".
- **Hedging and restatement.** One claim per sentence, each fact once, in the place where it does the most work.
- **Evidence compressed into parenthetical data capsules.**

### Content claims

- **Invented content.** A step, rule or procedure the user never set - the card-move team formation ("you made up a lot of clutter like how we do it", 2026-10-03), a peer-evaluation criterion ("why did you make these up?", 2026-10-01), the silent minute's invented "stand up, look at the wall" ("this is totally wrong", 2026-10-04), the S5 homework block's design-document machinery - the needs ratings, the switch story, the four forces - where only the prepare-to-run line and the reading list were set ("remove all shit you made up!!!!", 2026-10-06) - is not written into his artifacts, and never into his script, where it would be read and spoken as his. The script carries what he will say and the facts he set; what is missing is asked, not filled.
- **Goals a session cannot deliver:** a learning goal is a claim about what a student can do after the session, so it has to be possible and observable in that time. "can name every classmate's skill and strength" (27 people, one session) is neither; the honest version is "knows other classmates better for team building" (Bandura: an unattainable goal carries no signal). When a goal is corrected, sweep the same claim wherever the design states it, and re-render every artifact that reads it (rule 77).

## Where the markers live now

Rule 2 holds the classes and kinds with their fixes; this file holds the instances in two tables and the examples of the kinds; the shared marker list (`robot_markers.tsv`) holds the 28 machine checks, run by `scripts/wording_lint.py`; the KUBS pipeline wraps the checker. Note from the 2026-09-29 consolidation: rules 19, 37, 48, 54 and 85 still spell out their own copies of some markers, and that trim waits on the user's word ("Still duplicated, not trimmed ... Say the word and each becomes a pointer to rule 2"). Table two is new on 2026-10-12, on the user's order to keep every "not common sense" correction together; its rows are found by the search procedure below, and the search is repeated whenever the table is extended. The "can't you see" family is listed below the table for the same reason, searched with the same variants.

## The search procedure

His corrections live in two places in the session record, and the search reads both:

- His messages: `session_message` rows with `type = 'user'`, the message text in `data` → `text`.
- His answers to the `question` tool: stored inside an assistant row's tool part, under `state.metadata.answers` (a list of answers, each answer a list whose first element is his text) and `state.content`. A `LIKE` over the whole `data` column finds them; a query filtered to `type = 'user'` does not.

The phrases to search, case-insensitively, are his own markers: "common sense", "obvious", "of course", "basic", "isn't it clear", "why is this still not clear", "don't you get it", "can't you see", "can't you understand", "stupid", "you should know". A hit is a row here when it reprimands the agent for missing something ordinary; his own reasoning that happens to contain "of course", domain content he supplied, and fabrication complaints (table one) are not rows.

The one-liner over the database:

```
sqlite3 ~/.local/share/opencode/opencode.db \
  "SELECT datetime(time_created/1000,'unixepoch','localtime'), type, session_id, substr(data,1,300)
   FROM session_message
   WHERE lower(data) LIKE '%common sense%' OR lower(data) LIKE '%can''t you see%'
   ORDER BY time_created"
```

Then read the row: `type = 'user'` is a message, an assistant row whose tool part is named `question` carries an answer. Run it for the full phrase list before claiming the table is complete.

## The wording instances

The rows of Chaehan's wording corrections, and the corrections he had to call common sense, are in socrates `agent/wording cases.md`. They are private because they quote his notes; search them with grep.
