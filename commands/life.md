---
description: Walk through the latest Life Challenges note with questions; /life <keyword> runs one issue
---

Load the life-challenges skill and run its walk-through on the latest
`docs/*-life-challenges.md` in the socrates repo and its Evernote note.

- `$ARGUMENTS` empty: go through every open decision and Hand to me issue, one
  question at a time, and write each answer back into the note.
- `$ARGUMENTS` set: run only the issue whose command is `/life $ARGUMENTS`.
- `$ARGUMENTS` is `build`: build a new dated note instead (the skill's Build
  pass).
