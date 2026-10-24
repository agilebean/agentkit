---
name: kubs-grading
description: Build and maintain the KUBS DT solo presentation grading: the table and its rendered grade curve in the Drive folder "KUBS DT Grading". Use when the user asks to regenerate or update the KUBS DT grade curve, change grading scores or bands, or work on the grading table.
---

# KUBS DT grading: the table and the curve

Everything lives in the Drive folder "1 Projects/KUBS/KUBS DT/KUBS DT Grading":

- the LMS export csv (registered names, student IDs, section; Olesia Forkulitsa and Deepti Gupta sit in it but are off the course),
- "KUBS DT solo presentations grading.md" - the table: scheme on top, criteria scores (Skill, Insight, Method; 1-5, 5 best), weighted averages with class SDs, cluster column (A to E, legend in the file), grade column (A+ to C+), one evidence line per student,
- "KUBS DT solo presentations grading curve.png" - the rendered curve,
- "2026-10-19 KUBS DT S7 presentations grading.md" - the calibration file of 2026-10-19: S3 Solo, S6 Habits and S7 Jobs in one place, with the criteria, weights and bands the later reads use,
- "2026-10-22 KUBS DT S8 final presentations grading.md" - the final of 2026-10-22: the five teams in the E08 agenda slide's order with the members' registered names and student numbers, and the per-team read table. This is the graded team project, 65 percent of the course grade.
- "2026-10-22 KUBS DT S8 final presentations - transcript.md" - the session recording (`~/Desktop/229-332.mp4`, 47 min 8 s) transcribed: teams 3, 4 and 5 only, timestamped, speaker labels left out because the app's diarization is unusable.
- "2026-10-22 KUBS DT S8 final presentations - full read.md" - the evidence behind the S8 numbers: a section per team with what the room saw, the slides as they appeared, the four criteria with their reasons, and a member table that states how certain each attribution is.
- the mirror in the socrates repo: `projects/kubs_dt/grading/` holds the five grading documents, `_log.md` and the LMS export as versioned copies. Drive stays the working copy; a pass that edits one of them copies it there in the same turn, and the renders, the recordings and the submitted PDFs stay in Drive.

The grading files carry a date in the name, the day the presentations happened (solo 2026-10-05, S7 2026-10-19, the S8 final 2026-10-22); the earlier half of this skill's "no date in file names" guard is superseded for this folder on Chaehan's word of 2026-10-19.

The spoken forms of the names and the speaker-segmented transcript live in "KUBS DT S3/KUBS DT session 3 - solo presentations.md". The S8 script names the five teams after their S7 presenter (Alex, Mojmir, Malea, Bea, Maiko), which is the same order the E08 agenda slide carries.

## Regenerate the curve (the usual job)

From the socrates repo:

    cd ~/Software/Prototypes/socrates
    mamba run -n socrates python3 projects/kubs_dt/grade_curve.py

It writes `projects/kubs_dt/grade_curve.html`, screenshots it with headless Brave at 1900 px (device scale 2, about 2.5 s), crops the ink plus 80 px, and overwrites the PNG in the Drive folder. Measured 2026-10-05: 2.8 s total. Read the PNG and check the layout before reporting.

## Keep the two in sync

The scores live in two places: the md table and the `ROWS` list at the top of `grade_curve.py` (name, cluster, grade, weighted average; sorted by score). A score change edits both in the same pass. The curve colors follow the cluster letters: A amber, B navy, C teal, D light grey, E slate.

## The scheme (set 2026-10-05)

- A family 60 percent (15 of 25 students), B family 40 percent, C seat reserved for clear negative outliers (empty in the first class).
- Granular: A+ is 3.3 and up, A is 3.0, A- is 2.3 to 2.7. The flat 2.0 band splits by what the result rests on: B+ the person's response, B a design or a decision, B- the student's own effort.
- Communication is scored only where the session was recorded: 10 percent, the fourth criterion, on the 30/30/30/10 weights Chaehan set on 2026-10-23. It reads what the room saw - a scenario acted out where an explanation would have taken longer, narration that holds the audience, how the time was spent. In S3, S6 and S7 it stays unscored, because visualization and delivery leave no trace in a transcript. The solo sprint stays ungraded; the table is calibration for the course grade.
- **The two deductions of the 2026-10-23 final, both in Communication only.** The time rule comes from his format note "2026-10-19 KUBS DT - Final Presentation Format": "9-10 min presentation (downgrade if less or more time or many pauses)". Read as a quarter point per 15 seconds outside the window with the first 15 seconds free, it reproduces the Communication 2 he had already given team 2 for 5 min 45 s exactly (195 s - 15 s = 12 steps of 15 s, three points). A shortfall on a mandatory slide takes half a point, and the two add. Measured against it: team 1 8 min 14 s gave 4.5, team 2 5 min 45 s gave 1.5, team 4 7 min 33 s gave 1.3, team 5 8 min 57 s stayed at 4 inside the tolerance, and team 3 cannot be measured because `229-332.mp4` opens inside their talk.
- **What counts as a page in a submitted PDF.** A title or a thank-you page is formatting, a description page is one of the two A4 pages and not a slide, and only the rest are content slides. Count the three apart: conflating them produced "five pages" and "six pages" for PDFs of seven and eight, and the confusion put "inside the window" beside an 8 min 14 s talk.
- **A mandatory-slide deviation is read against the note, not against the course template.** The note asks for "job statements (including emotional/social jobs, needs)", so a job statement plus the emotional and social jobs and the needs meets it whether or not a functional job is labelled separately; the missed element is the one the note names and the submission lacks.

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

## Guards

- An edit to `grade_curve.py` is a .py edit and triggers the full test suite (RULES.md rule 6): run `mamba run -n socrates python3 -m pytest -q` from the repo root before reporting.
- Dates in file names: the grading files are named after the day their presentations happened ("2026-10-05 KUBS DT solo presentations grading.md", "2026-10-19 KUBS DT S7 presentations grading.md", "2026-10-22 KUBS DT S8 final presentations grading.md") - Chaehan's word, 2026-10-19, after the S7 rebuild first landed undated. A document change is logged in the folder's `_log.md` in the same pass.
- Text the user will read goes through the robot-marker check: `mamba run -n socrates python3 ~/Software/Prototypes/agentkit/scripts/wording_lint.py FILE`. The word "Insight" as the criterion's own name is a known warn.

## Report

Name the files changed, the measured render seconds, and the counts per grade band.
