---
name: kubs-grading
description: Grade and maintain the KUBS DT team and solo assessment in the Drive folder "KUBS DT Grading" - the 65 percent team round read from the submitted PDFs and the session recordings, the comparison against Chaehan's own read, the solo presentation table and its rendered curve. The essay round and the course gradebook are kubs-essay-grading. Use when the user asks to grade or reproduce the team presentations, to compare his read with the agent's, to change team or solo scores and bands, or to rebuild the curve.
---

# KUBS DT grading: the team round, the table and the curve

## The folder

Everything lives in the Drive folder "1 Projects/KUBS/KUBS DT/KUBS DT Grading":

- the LMS export csv (registered names, student IDs, section; Olesia Forkulitsa and Deepti Gupta sit in it but are off the course),
- "KUBS DT solo presentations grading.md" - the table: scheme on top, criteria scores (Skill, Insight, Method; 1-5, 5 best), weighted averages with class SDs, cluster column (A to E, legend in the file), grade column (A+ to C+), one evidence line per student,
- "KUBS DT solo presentations grading curve.png" - the rendered curve,
- "2026-10-19 KUBS DT S7 presentations grading.md" - the calibration file of 2026-10-19: S3 Solo, S6 Habits and S7 Jobs in one place, with the criteria, weights and bands the later reads use,
- "KUBS DT final presentations grading.md" - the final of 2026-10-22: the five teams in the E08 agenda slide's order with the members' registered names and student numbers, the per-team read, the criteria table, the mandatory-slide table, and the two comparison tables. This is the graded team project, 65 percent of the course grade,
- "2026-10-22 KUBS DT S8 final presentations - transcript.md" - both session recordings (`142.mp4`, 42 min, the intro and teams 1-2; `229-332.mp4`, 47 min, teams 3-5) transcribed and merged in time order, timestamped, speaker labels left out because the app's diarization is unusable,
- "2026-10-22 KUBS DT S8 final presentations - full read.md" - a section per team with what the room saw, the slides as they appeared, the four criteria with their reasons, and a member table that states how certain each attribution is. It is a reading, not a source: it carried three claims its own evidence contradicted,
- "KUBS DT grading insights.md" - the traps and lessons written through both rounds; this skill reads its team sections only, named in the boundary below,
- the mirror in the socrates repo: `projects/kubs_dt/grading/` holds the grading documents, `_log.md` and the LMS export as versioned copies. Drive stays the working copy; a pass that edits one of them copies it there in the same turn, and the renders, the recordings and the submitted PDFs stay in Drive.

The grading files are named after the day the presentations happened (solo 2026-10-05, S7 2026-10-19, the S8 final 2026-10-22); the earlier half of this skill's "no date in file names" guard is superseded for this folder on Chaehan's word of 2026-10-19.

The spoken forms of the names and the speaker-segmented transcript live in "KUBS DT S3/KUBS DT session 3 - solo presentations.md". The S8 script names the five teams after their S7 presenter (Alex, Mojmir, Malea, Bea, Maiko), which is the same order as the E08 agenda slide.

## Boundary with the essay round

Two grading skills exist, one per round. **Load exactly one per pass.**

- This skill owns the 65 percent team round and the solo presentation table. The 35 percent essays and the course gradebook are `kubs-essay-grading`: do not load it, and do not open its sheet, its anchors or its reading model while a team is being scored.
- The rounds share the folder, the letter scale and the record discipline. They share no criterion, no anchor and no deduction. An essay's length charge, AI downgrade and signposting rule have no meaning here; this round's half point for a mandatory slide and its room-reception test have none there.
- One file both rounds read: "KUBS DT grading insights.md". This skill reads only the team sections - "What the team round taught about grading" and the team reproduction prompt - and stops at the essay lessons below them.
- Nothing crosses in either direction: a rule learned on an essay never changes a team score, and a team lesson never changes an essay score. When a correction arrives that seems to apply to both, it belongs to the round it was taught on, and the other round waits for its own.
- A task that needs both rounds - rebuilding the gradebook - belongs to `kubs-essay-grading`, which quotes this round's settled means as data. A team mean is never re-derived there, and an essay score is never re-derived here.

## What a score is about

One rule runs under all four criteria: **a score reads what the room received.** The artefacts are only the evidence for that, never a score of their own. A well-designed device earns nothing on paper; it earns through whether the room could hear it, read it, follow it and stay at ease.

| Criterion | What it reads | What lowers it | What never moves it |
| :-- | :-- | :-- | :-- |
| **Method** 30 | The team's chain of work, as the team explained it: each method element named as it is used, the reasoning for the next move | An artefact formulated wrongly (a how-might-we that names its own solution); the final prototype never tested, about half a point; content the method round needed and the talk never covered | A deck that arrives late; length by itself |
| **Skill** 30 | The team's own analytical work: analysis deepened by the data, a solution aspect improved across sprints, the emotional and social jobs found | A tool used wrongly (a tautology, push and pull swapped, a verbless how-might-we); a claim resting on one quote; the road from prototype to need never shown | An error in a tool the semester did not cover; how polished the presentation was |
| **Insight** 30 | What the team understood about the user, and whether the solution follows | The finding not shown to be the user's main problem; the population left unbounded; a trivial solution; alternatives never weighed | How counterintuitive a finding is, on its own |
| **Communication** 10 | Reception: legibility, audibility, rehearsal, comfort, who spoke, and the device only through those | Unreadable printouts, a prop in front of the slides, sound too low, visible discomfort, one or two voices where a team stood there, a device lifted after its own point was made | A deck that stays off screen while posters and films hold the room; the design of the device; whether a video was used at all |

The full table, with raises and lowers per criterion, is at the top of "KUBS DT final presentations grading.md" and is the authority; this one is its short form. Three consequences that were each learned from a wrong cell:

- **The brief decides what a deviation is.** The final asked for a talk that runs mostly without slides, the deck shown at the beginning or the end. A blank screen mid-talk is the requirement met, not a defect. Video was neither asked for nor forbidden, so it neither earns nor costs.
- **A score is defensible only in order.** Read each new team against the teams already recorded. Team 4's Method and Skill sat at Team 2's level while Team 4 had interviewed more people, rewritten its how-might-we questions and written two job statements against Team 2's one, and nothing in either submission makes them equal.
- **A defect is charged once**, under the criterion that owns it. An untested prototype is a Method, Skill and Insight fact; charging its absence from the screen again under Communication is the same point counted twice. Before a deduction, name the criterion that already pays for that fact: the watch that ignored its constraints repeats the concept Method already docked as untested, and a solution that does not follow from the finding repeats the Skill charge on the kit that never satisfied a need.
- **Who did how much is a team fact, not a reception fact.** A quiet member lowers Communication only when the room lost something because of it - a gap in the narration, a handover that stalls. Counting heads is an overall-comment observation, and two near-silent members in a talk that still flowed cost nothing.

Grades are absolute on the five-point scale, no minus grades: A+ 4.5 and up, A 4.0 to 4.49, B+ 3.5 to 3.99, B 3.0 to 3.49, C+ 2.5 to 2.99. The cutoffs used before 2026-10-27 (A+ 3.3 and up, A 2.8 to 3.2) were set to land a 60/40 family split and are retired: a grading percentage is not a scheme, and a 1-5 mean is never mapped onto a finer 0-100 band.

## Grading the team round

The round is reproduced from the folder alone: six submitted PDFs for five teams, two recordings, the merged transcript, and the format note "2026-10-19 KUBS DT - Final Presentation Format".

**0. Cost line.** State the number of teams and files and the expected cost in one line before starting. Measured on the 2026-10-30 reproduction of five teams: 164 frames, 14 contact sheets, 35 tool calls to the first score; 40 to 60 calls for the full round.

**1. Read the deliverables.**
- Every submitted page, in order, and record which slide sits on which page. A page whose text layer is empty is a picture, not a blank page: render it and look before writing a word about what a team did not submit. This one trap produced a retracted claim about Team 4 and another about Team 5's job slide.
- The harness cannot take a PDF as input. Extract the text layer first (`pypdf`, one line per page with its character count); a page that comes back near-empty is the picture page, and only that page needs rendering (`pymupdf`, `get_pixmap(dpi=110)`), then reading as an image.
- The transcript of the team's talk and its questions, in full. A finding said in the Q&A is evidence (Team 4's "not making them feel like they're accepting charity"; Team 5's "simplify by using data" when asked for the underlying idea).
- Frames for what only the eye can settle: who stands at the front, what they hold, whether the deck is on screen and in which view, whether a device was lifted after its point. Measured recipe: `fps=1/15, scale=480:-1` over each team's own window, then tiles of four by four with the timestamp drawn on each cell; about 2 minutes for the two recordings and legible for stage action, never for slide text.

**2. The mandatory six.** The brief asks for three mandatory slides and at most two optional ones of the team's own choice, plus the two A4 pages: sprint 1 with its retrospective, sprint 2 with its retrospective, and the job statements with the emotional and social jobs and the needs. Check the submission against the note, not against the course template, and write one compliance row per team with the page that settles it: present, partial, or missing. A shortfall on a mandatory slide takes **half a point off Communication**; nothing else is deducted, and "more than five slides loses points" was never a rule.

A page count separates three things a PDF page can be: a content slide, a formatting page (a title or a thank-you, no content of the brief), and a description page (the two A4 pages, not slides). Count them apart.

**3. Score the team, blind.** Set the four criteria from step 1 and 2 alone. Chaehan's row and his wording stay out of view: a cell that reuses his nouns is a check-list, not a reading, and a pass that moved his numbers into the agent's cells was called cheating twice, on 2026-10-28. His row sits in the same file as the criteria, so read the criteria block only - the top of "KUBS DT final presentations grading.md" down to the "Teams" heading - and open the comparison tables after the score is written. Agreement is a coincidence to notice, not a target.

Write one evidence line per criterion, naming the timestamp or the page. Every number needs its sentence; a number whose cell does not explain it is the rule applied to the prose only.

**4. His row.** Elicit it in ONE question-tool pass with all nine fields - the four grades, the four comments, the overall comment - after stating the team name and every member in parentheses. Never one pass per criterion, and never show the AI grade while he answers. His grade governs where the two differ, and where they differ one line says what the difference rests on.

**5. Record.** His row sits directly under the AI row in the same columns, his wording verbatim with his `+` and `-` markers kept, in two tables that keep the same columns: one of grades, one of comments. Then sweep every file that has the number (the course-grade sheets, the gradebook, the renders), add the line to `_log.md`, copy to Drive and commit.

## Evidence rules

These four decide whether a row can be defended to a student.

- **Never invent a claim about a team's work.** "Remember not to make up things, especially when grading - this is utmost priority in grading." An absence claim ("never tested", "no needs", "no cost or distance") needs the whole file searched first and the search named; two versions of such claims were retracted in one round. If the record cannot settle it, write unknown.
- **A missing method element is a downgrade, once it is certain.** A test can hide in a paragraph, and an interview list can sit on a page that renders as a picture. Verify, then charge: an untested final prototype costs about half a point.
- **A method step is credited when it is used, not when it is named.** Naming the Opportunity Score and the Value Proposition Canvas is not a method step; applying the score to two named jobs and checking the pattern in other interviewees is.
- **Read the primary source, not the intermediate record.** The full read, a previous summary row, or an earlier pass of the same table can contradict the PDF in front of you. Three claims in the S8 full read were contradicted by its own evidence.

## Reading a session recording

Measured on the S8 final, 2026-10-23, 47 minutes of 720p video:

    ffmpeg -y -i VIDEO -vn -ac 1 -ar 16000 -c:a pcm_s16le audio16k.wav          # 1.5 s
    open -a "Whisper Transcription.app" "2026-10-22 ... teams.wav"               # the app's default model is parakeetKitPro / nvidia_parakeet-v3

The app transcribes in about 24 s for 47 minutes of audio. Read the result out of its database, not the UI: `~/Library/Containers/com.goodsnooze.MacWhisper/Data/Library/Application Support/MacWhisper/Database/main.sqlite`, tables `session` (title, modelIdentifer, playbackDuration, timeTakenToTranscribe) and `transcriptline` (orderIndex, start, end in ms, speakerId, text). Open it read-only (`sqlite3 "file:PATH?mode=ro"`) while the app runs.

For a silence check - the break between blocks, a cut in the file - run it on the audio track, never on the video:

    ffmpeg -hide_banner -nostats -i VIDEO -vn -af silencedetect=noise=-35dB:d=20 -f null -

Measured 2026-10-23 on the two S8 files: 36 s for 73 minutes of audio, against 316 MB of 720p the same scan decodes without `-vn`. A foreground shell call is capped at 20 s and a larger timeout does not raise the cap, so the first cap means move it to the background; two foreground attempts in a row spend a minute to learn what one taught.

Two limits to state in any file that leans on it: the diarization merges the professor, the guests and several students into one cluster, so drop the speaker labels and keep turn changes; and no recording holds a name-to-face key unless a team introduces itself or its title slide lists the members.

For the screen: one frame every 4 s, cropped to the projection area, upscaled 2x, read with Apple's recogniser through a small Swift tool (`import Vision; VNRecognizeTextRequest`), then grouped into runs of similar text. That produces the slide timeline and the slide count. Verify the crop against one full frame first - the projection area is per camera position, not a constant. Full frames are still needed for what OCR cannot say: who stands at the front, what they wear and hold, and whether the deck was in slideshow or editing view.

## Regenerate the curve (the usual job)

From the socrates repo:

    cd ~/Software/Prototypes/socrates
    mamba run -n socrates python3 projects/kubs_dt/grade_curve.py

It writes `projects/kubs_dt/grade_curve.html`, screenshots it with headless Brave at 1900 px (device scale 2, about 2.5 s), crops the ink plus 80 px, and overwrites the PNG in the Drive folder. Measured 2026-10-05: 2.8 s total. Read the PNG and check the layout before reporting.

The scores live in two places: the md table and the `ROWS` list at the top of `grade_curve.py` (name, cluster, grade, weighted average; sorted by score). A score change edits both in the same pass. The curve colors follow the cluster letters: A amber, B navy, C teal, D light grey, E slate.

## The scheme (set 2026-10-05)

- A family 60 percent (15 of 25 students), B family 40 percent, C seat reserved for clear negative outliers (empty in the first class).
- Granular: A+ is 3.3 and up, A is 3.0, A- is 2.3 to 2.7. The flat 2.0 band splits by what the result rests on: B+ the person's response, B a design or a decision, B- the student's own effort.
- Communication is scored only where the session was recorded: 10 percent, the fourth criterion, on the 30/30/30/10 weights Chaehan set on 2026-10-23. In S3, S6 and S7 it stays unscored, because visualization and delivery leave no trace in a transcript. The solo sprint stays ungraded; the table is calibration for the course grade.
- **The one deduction of the 2026-10-23 final, in Communication only: a shortfall on a mandatory slide takes half a point.** The time rule of 2026-10-23 - a quarter point per 15 seconds outside the 9 to 10 minute window, after a 15-second tolerance - was **dropped on 2026-10-27** on Chaehan's word: a presentation that ends early is read on the content it left uncovered, and the loss shows up there rather than as a clock penalty. An unspent minute is therefore named where that content belongs - Team 2's 5:46 under Method as "missing a lot of detail", Team 1's spare 1:40 under Communication as differentiation that could have been added. Team 3's length is unmeasurable either way, because `229-332.mp4` opens inside their talk.
- **A mandatory-slide deviation is read against the note, not against the course template.** The note asks for "job statements (including emotional/social jobs, needs)", so a job statement plus the emotional and social jobs and the needs meets it whether or not a functional job is labelled separately; the missed element is the one the note names and the submission lacks.

## Guards

- **A grading file exists nowhere for him until it is in the Drive folder.**
  `projects/kubs_dt/grading/` in the socrates repo is the versioned mirror, never
  the deliverable. A pass that writes or edits any file of this set copies it to
  Drive in the same turn, before it reports, and matches the two by checksum.
  Writing only the mirror is the 2026-10-29 failure that produced "why did you
  not put this into the grading folder, isn't that common sense???" - the task
  arrived as a text transform and this skill was never loaded, so the folder
  that holds the work was never consulted.
- **Never move a score toward his read, and treat his wording as contamination too.** The two reads only test each other while one is set without the other in view. When his view arrives first, hold the score and report the difference instead of absorbing it.
- **A rule change must move the number, not only the prose.** A cell that says one item costs half a point while the score keeps the full point is the rule applied to the text only.
- An edit to `grade_curve.py` is a .py edit and triggers the full test suite (RULES.md rule 6): run `mamba run -n socrates python3 -m pytest -q` from the repo root before reporting.
- Dates in file names: the grading files are named after the day their presentations happened ("2026-10-05 KUBS DT solo presentations grading.md", "2026-10-19 KUBS DT S7 presentations grading.md", "KUBS DT final presentations grading.md") - Chaehan's word, 2026-10-19, after the S7 rebuild first landed undated. A document change is logged in the folder's `_log.md` in the same pass.
- Text the user will read goes through the robot-marker check: `mamba run -n socrates python3 ~/Software/Prototypes/agentkit/scripts/wording_lint.py FILE`. The word "Insight" as the criterion's own name is a known warn.

## Report

Name the files changed, the measured render seconds, and the counts per grade band. For a team round, the reply has the per-team table with the four criteria, the weighted mean and the letter, the two comparison tables, every deduction with its arithmetic, and one line per difference from his read saying what it rests on.
