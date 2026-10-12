# Rebuild defects inventory

The instances behind RULES.md rules 104 and 133 to 137, in one file. Compiled 2026-10-10 from the KUBS DT folder logs (Course Design, S1 to S5), the session record of 2026-10-09 and 2026-10-10, and the deck backups in the stage.

The user, 2026-10-10: "i'm sick and tired of soo many mistakes you repeat despite instructions. investigate each where i complained that it happened repeatedly. i want a stronger, deeper, more thorough and clear analysis what the root causes were and improvement of the agent instructions which seemed to handle the specs superficially or too narrowly or not clearly."

"The user corrects a sentence to kill a class of mistake, not the sentence." Every class below is why a defect returned after it had already been fixed once. The classes are the standard, not the list of instances.

## The system

- `RULES.md` 104 and 133 to 137: the standing classes, each with the plain rule. 104 an element the user edits is never flattened: a living original stays editable, and a new element he will edit or animate is built from the artifact's native objects; 133 the page is white and full-page; 134 a rebuild copies the deck's own reference geometry and reuses finished assets; 135 a standing requirement survives every new instruction; 136 a specification applies to its class; 137 verification must be differential and able to fail.
- This file: one section per class: the trigger, the instances with the user's own words, why the guard failed, and where it is enforced now.
- The values, machine-readable: `projects/kubs_dt/deck_reference.json` (the deck's measured geometry and asset locations). The single source of truth; nothing rebuilds from memory.
- The checks, executable: `projects/kubs_dt/deckcheck.py`, wrapped by `pipeline.py deckcheck --session N`. Differential against the reference; exits 2 on a flag. Each check has been run against the export of the exact defect it exists for (the stage keeps them) and shown to flag.
- The procedure, ordered with gates: the `kubs-deck` skill (`agentkit/skills/kubs-deck/SKILL.md`).

Maintenance: a new defect is classified against these classes in the same turn. An instance is a row under its class with the date, the place, and the user's words; a new class is a section here, a rule in RULES.md, and, where a machine can catch it, a check in `deckcheck.py` run against the defect before it is trusted.

---

## Class 1. Reference geometry re-derived per instance

**Trigger.** Any element created or replaced that already exists in the artifact: a band title, a divider box, a figure slot, a chart mark, a page construction.

**The rule was already paid for once.** The S5 log, 2026-10-02: the Yes-and titles were "re-anchored to ink x44 (a +14 box shift on the blue- and red-band slides)". The anchor was known, fixed, and written down. Seven days later three slides carried titles at ink x 26 and y 28, and the user had to say it again:

- 2026-10-09, divider subtext: "all the divider slides have a subtext which is not left aligned. you must look for the master in s01 and don't deviate".
- 2026-10-09, band titles on slides 10, 12, 21: "many title slides have the title not middle aligned, take it from the tip slide or four forces", then "why is this still these issues even though we repeated that 100s times??"
- 2026-10-09, the chart's week-row ring: hand-drawn at a 9 px inset where the chart's own marks use 2 px.
- 2026-10-12, the E06 terminology page: built from the user's layout spec with the figure's *type sizes* copied, but the deck's box format not read - loose shapes with separate text items, left-aligned citations, wide strip boxes, one colour family, no groups. The format had been measured a year's-week earlier and pointed at by the skill (`memory/kubs.md`, Tooling). The user: "you forgot many design elements i specified in that slide of e05, like all middle aligned. i corrected all manually. read it and compare with the specs you remembered."
- 2026-10-12, the E06 band pages: pages 5 ("Homework") and 6 ("Tips") carry the band as two objects - the image over a band SHAPE at the same (0,12) 1920x112 rect whose 2 px outline is the band red - and the outline's outer half shows as a full-width hairline at y 11 and y 124-125. Both pages got their band by duplicating an older page (slide 5 was rebuilt from the blue Yes-and slide on 2026-10-11; the Tips page duplicated slide 5's frame on 2026-10-12), so the construction came from an instance instead of the reference, and the shape also shades the page around the band. The class is the whole family: 17 pages carry the hairline - E01 4,5,6,7,11,20; E02 3,4,5,6; E03 61; E06 5,6; E07 3,4; E08 3,4 - and 4 more carry the object with nothing visible (E01 9,10 under a band image with an outline that is not the band red; E03 62,63 under a full-page canvas). E05's nine shapes were deleted on 2026-10-09 under an instruction the record kept as E05's slide numbers, so the class was never swept; E04 is clean. The user: "KUBS DT WS2026 E06.key has two title bars which have a red line border - how is that possible and why don't you get the reference from the deck preferences?" Swept the same day: 10 pages fixed by deleting the leftover shape (E02 3-5, E03 61, E06 5-6, E07 3-4, E08 3-4), each verified by export (only rows 0-148 of the page changed; every other page byte-identical) and by the `stroke` check. Closed on 2026-10-13, both by a build: E01's six pages rebuilt - shape deleted, band image placed, the title re-created above it, read back from the export and nudged to its old ink (recipe and measured numbers in `band.build_recipe`) - and E02's page 6 patched at the media level (`band.render_patch`). The second case taught its own lesson: a base render cannot be replaced by adding an image, because the new image lands on top of the composition and hides the group's four boxes - adding it, replacing the wrong source file (the deck holds a plain rules render beside the composed page), and dropping the ICC profile each showed up in the export diff, and the deck was restored from its byte-identical backup the moment the boxes were found missing.

**Why the guard failed.** The values existed only as narrative in past log entries and in the user's head. Every pass that re-created an element invented its box, because nothing in the working path carried the value to copy and no check could contradict it. A prose rule ("look for the master") depends on the agent remembering it at the exact moment it writes a box; a file the pass must read and a check that runs on the export do not. The 2026-10-12 repeat is the same shape one level up: the box format was written in memory and pointed at by the skill, and the pass still built the page without opening either - so the format moved into the values file the pass reads first, and the measurement it must report. The band instance is the same failure by the opposite road: the pass did not invent the geometry, it inherited it from a page it duplicated, and the reference described where the band sits but not what it is made of, so nothing in the pass could see the shape and `deckcheck`'s band check sampled the band's interior, where the shape is hidden.

**Enforced now.** `deck_reference.json` holds the values (`figure_box_format`: the box construction, the both-axes centring rule, the line-break rule, the grouping rule, the E05 spec and the E06 page as the newest instance, with its tolerances; `band.construction`, `band.defect_signature` and `band.leftover_shape_instances_2026_10_12`: the band is the image alone, the leftover shape's measured signature, and the pages that carry it); the `band` check measures every banded page's title ink against the deck's measured column and the 10 px spread rule on every pass (E05 measures x 38-40; the E02-E04 lineage anchors at x 44, so the check spans both and the spread rule carries the class); the `stroke` check flags any full-width row outside the band image's rect that matches the band red, and was run against the 17 defective pages and the clean decks before being trusted; the skill's build step requires a box-format page's texts' ink centres to be measured against their box centres from the export (8 px / 12 px) and names the band's image-only construction and the object dump a duplicated page is checked against; rule 134 names the class, 155 the copied-page case.

---

## Class 2. A standing requirement dropped when a new instruction arrived

**Trigger.** An instruction that names one thing for an artifact that carries several requirements.

**The instance.** The deck was created on 2026-10-02 carrying "the course chart with the week 3 row and the S5 chip circled"; the 2026-10-05 refresh kept them ("the week 3 row and the S5 chip stay marked in green"). On 2026-10-09, acting on "the course overview - i said it 100 times - should not be an image including the green circles. it should be on a white background", the pass replaced the marked chart with a clean render and a single hand-made ring. The standing requirement was dropped silently, and it cost three further reports:

- "why is the course overview missing the circle around the session?"
- "why can't you just do what you did for the other sessions?"
- "the rectangle on the session has two horizontal lines sticking out of the rounded rectangle."

**Why the guard failed.** The instruction was read as a replacement of the construction, not as a constraint on it. Nothing in the pass listed what the artifact must keep, and the sibling decks (E06 to E08), which carried the finished construction, were never opened. The ambiguous half of the instruction ("not an image including the green circles") was resolved silently and narrowly instead of being surfaced.

**Enforced now.** Rule 135 (state what must stay; the siblings are the reference for a valid instance); the `chart` check compares the page's green pixels against the session's own chart file and flags both a missing mark (884 px on the phantom build) and green outside the marks (565 px on the overhang build); the skill's preflight asks for the requirements before any write.

---

## Class 3. A specification about a class applied to one instance

**Trigger.** A spec stated with a scope word: "all", "every", "always", or a spec whose scope is a class the user can see and the agent cannot.

**Instances.**
- 2026-10-09: "why didn't you register that all pasted slides should be on a white background?" The lesson had been learned for the slide that was named (the chicken page rebuilt on a full white canvas) and not for the class; slide 2 stayed transparent until the next report.
- 2026-10-09: the reading's Part 1 Annex marked optional - correct on the carrier he named, swept to the other four carriers only after he insisted it belongs everywhere.

**Why the guard failed.** Every report was patched at the location that was named. No step asked what class the instruction governs, so the class got the fix only when the user walked the instances himself.

**Enforced now.** Rule 136 (enumerate the class, act on all of it, name the sweep in the report); the `pages` check fails on any non-opaque page, so the class cannot be half-done silently.

---

## Class 4. Verification that cannot fail

**Trigger.** Any claim that a change is correct.

**Instances.**
- The overhang: three passing numeric measurements, and the user still saw "two horizontal lines sticking out of the rounded rectangle". The measurements compared the result against the numbers the pass had computed, not against the reference chart.
- The phantom ring: a fitted-view read of a render reported a defect that was not in the pixels, and the same read missed the one that was. Two rounds were spent chasing a spectre.
- The transparent margins: found only by the export, after the complaint.

**Why the guard failed.** Self-consistency is the default mode: the agent checks that what it meant to do happened. That check cannot detect a wrong intention. And a fitted render is not evidence for defects at the 6 px scale the class lives at.

**Enforced now.** Rule 137; `deckcheck.py` is differential by construction and has been run against the defect exports (`look_b6`, `look_b7`) and shown to flag them; the skill requires a magnified read of every changed region before installing.

---

## Class 5. The source's structure treated as the deliverable's spec

**Trigger.** Building a figure, table or page from a source document (a book, a paper, an earlier deck) that also appears in the artifact.

**Instance.** 2026-10-09, the tip figure: built from the book's own table grouping, with one INTERPRETATIONS header over jobs and needs, while the slide's own title taught the chain Observations, Jobs, Needs. The user: "the tip slide should show the Observations to Jobs to Needs in the headers, not summarize jobs and needs."

**Why the guard failed.** The source was at hand and authoritative-looking; the deliverable's own spec (its title, its teaching chain, its sibling pages) was not read as the spec. The same shape appeared with the needs page ("the two opposing definitions side by side like the boxes on the formulate the job slide") and the chicken page: the deck had a construction, and the pass used the source's.

**Enforced now.** Rule 134's second sentence: the source material supplies content only; geometry, grouping and construction come from the deck. The skill's preflight asks which existing page the new element copies.

---

## Class 6. A live element installed as a flattening

**Trigger.** A new element the user must edit or animate later — a diagram, a row of boxes, a table — composed directly as an image.

**The instances.** The complaint recurs; the user's words when it does:
- 2026-10-02, the S3/S4 post-it and dot-vote slides: "the new slides for postit and dot vote are images that is terrible!!! why would you do that not as an editable slide like everywhere else?"
- 2026-10-03, the S3 "Design Challenge" divider: "you did it again the same mistake the divider slide is an image which i cannot edit! how many times do i have to say it again so you remember??"
- 2026-10-10, E05 "Formulate the Job": "i said this so many times but you still didn't get it: i need every slide in elements that are editable! you did again just one image which i cannot edit nor make animation effects! why didn't you get this still not?"

**Why the guard failed.** RULES.md 104 framed the choice around content *moving between containers*; here nothing moved — a brand-new diagram was drawn straight to a render, so the move question never fired. The deck's accepted drawn figures read as house style, and the deck's own box construction was not opened as the model.

**Enforced now.** Rule 104's drawn-element bullet; the skill's build step: a new element is native objects first (shapes, text items), a render only for content that is itself a render, and the styling the script cannot reach (fill, stroke, corner radius — `background color` fails at runtime, probed 2026-10-10) is a hand pass named in the report. No deckcheck check: the difference between a book facsimile (right as a render) and drawn content (wrong as a render) lives in the source, not in the pixels.
