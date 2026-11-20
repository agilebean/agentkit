---
description: Analyze a date recording and write the note (date-analysis skill); Hanji as the last word writes it to Hanji
---

Arguments: $ARGUMENTS

Load the date-analysis skill and read the arguments this way:

- The words name the recording as Whisper Transcription holds it, for example
  "2026-11-19 Sunrise Date 지원"; the note takes the same name. With no words,
  take the newest recording in Whisper Transcription.
- When the last word is "Hanji" (any case), this run writes its note to Hanji,
  and the word is not part of the name. Otherwise the note goes to Evernote,
  notebook Affinity.
- When a note of that name exists, rebuild it in place by its guid (the
  evernote skill's `--guid --base` path); never make a second note.
