/date <recording>

Load the date-analysis skill (~/.agents/skills/date-analysis/SKILL.md, with register.md and traits.md beside it) and follow it end to end. The note's title is "<title>"; she is <her name>.

- The build folder B is <B>, exactly as written (the letter B means this folder, never a folder named B).
- Step 1: the transcript is "<transcript path>".
- Step 4: Chaehan's words about this date are in B/his.md (empty when he gave none). His answer to the touch question, with its date: <his answer>. Ask nothing. The earlier notes on her are <their titles, or: none, this was the first meeting>. B/base.md, when it exists, is the current note of this date, for --base only: do not read it, and do not open that note in Evernote.
- Steps 1 to 9 as the skill says, until date_check.py prints PASS (with --verbatim B/his.md when it holds his words). Step 10 only as far as the gate: `note_build.py init B/note --as-is B/draft.md --title "<title>" --notebook "Affinity" --person "<her name>"` with --verbatim B/his.md when it holds his words<, and --guid <its guid> --base B/base.md when a note of that title exists>, then `next` until PASS. Do not run `note_build.py write`. Skip step 11. Ask nothing.

End with the date_check result, the note's word count, and the section "The turning point" as written.
