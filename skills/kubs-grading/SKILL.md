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
- "2026-10-22 KUBS DT S8 final presentations grading.md" - the final of 2026-10-22: the five teams in the E08 agenda slide's order with the members' registered names and student numbers, and the per-team read table that is filled in after the session. This is the graded team project, 65 percent of the course grade.

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
- Communication is not scored from the transcript (visuals and delivery do not transcribe). The solo sprint stays ungraded; the table is calibration for the course grade.

## Guards

- An edit to `grade_curve.py` is a .py edit and triggers the full test suite (RULES.md rule 6): run `mamba run -n socrates python3 -m pytest -q` from the repo root before reporting.
- Dates in file names: the grading files are named after the day their presentations happened ("2026-10-05 KUBS DT solo presentations grading.md", "2026-10-19 KUBS DT S7 presentations grading.md", "2026-10-22 KUBS DT S8 final presentations grading.md") - Chaehan's word, 2026-10-19, after the S7 rebuild first landed undated. A document change is logged in the folder's `_log.md` in the same pass.
- Text the user will read goes through the robot-marker check: `mamba run -n socrates python3 ~/Software/Prototypes/agentkit/scripts/wording_lint.py FILE`. The word "Insight" as the criterion's own name is a known warn.

## Report

Name the files changed, the measured render seconds, and the counts per grade band.
