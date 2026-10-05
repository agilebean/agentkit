---
name: kubs-grading
description: Build and maintain the KUBS DT solo presentation grading: the table and its rendered grade curve in the Drive folder "KUBS DT Grading". Use when the user asks to regenerate or update the KUBS DT grade curve, change grading scores or bands, or work on the grading table.
---

# KUBS DT grading: the table and the curve

Everything lives in the Drive folder "1 Projects/KUBS/KUBS DT/KUBS DT Grading":

- the LMS export csv (registered names, student IDs, section; Olesia Forkulitsa and Deepti Gupta sit in it but are off the course),
- "KUBS DT solo presentations grading.md" - the table: scheme on top, criteria scores (Skill, Insight, Method; 1-5, 5 best), weighted averages with class SDs, cluster column (A to E, legend in the file), grade column (A+ to C+), one evidence line per student,
- "KUBS DT solo presentations grading curve.png" - the rendered curve.

The spoken forms of the names and the speaker-segmented transcript live in "KUBS DT S3/KUBS DT session 3 - solo presentations.md".

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
- No date in file names (Chaehan's rule). A document change is logged in the folder's `_log.md` in the same pass.
- Text the user will read goes through the robot-marker check: `mamba run -n socrates python3 ~/Software/Prototypes/agentkit/scripts/wording_lint.py FILE`. The word "Insight" as the criterion's own name is a known warn.

## Report

Name the files changed, the measured render seconds, and the counts per grade band.
