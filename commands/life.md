---
description: Build the Life Challenges note, or with a topic a note on that one challenge; Hanji as the last word writes it to Hanji
---

Arguments: $ARGUMENTS

Load the life-challenges skill and read the arguments this way:

- When the last word is "Hanji" (any case), this run writes its note to Hanji,
  and the word is not part of the topic. Otherwise the note goes to the
  skill's default note app, Evernote ("Evernote" as the last word says the
  same).
- With no other words, build the Life Challenges note of all challenges (the
  skill's Build pass).
- With other words, they name one challenge: build the skill's topic note on
  it.

Every build ends by offering the walk-through. The four forms, Chaehan,
2026-11-08: `/life`, `/life Hanji`, `/life <topic>`, `/life <topic> Hanji`.
