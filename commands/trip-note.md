---
description: Build an Evernote trip note for one city stay, sections in Chaehan's priority order
---

Trip: $ARGUMENTS

The argument names the city and the stay, e.g. `/trip-note Seoul 2027-03-16 to 2027-06-15`. The note follows the format Chaehan set on the Osaka note (2026-11-07 and 2026-11-08): read `~/Software/Prototypes/agentkit/skills/evernote/briefs/trip_note.md` end to end before the first tool call, and the evernote skill's section "Writing or rewriting a note's text".

1. Read the stay in `~/Software/Prototypes/socrates/memory/travel.md`: its dates, where he sleeps, and the bookings that have their own Evernote notes. Never take dates from anywhere else (point 5 of the brief).
2. Research only the kinds of section he has for this stay, in the brief's point 9 order: his life matters (meeting people, friends, partner search, health), then logistics (accommodation, and transport from where he sleeps with how he pays), then swimming, then eating, then the night. Check every place on its own page, and put each fact with its source URL into `$TMPDIR/<city-slug>/found.md` (point 6).
3. Write the findings as one markdown file with one `##` section per kind, in that order, and build the note from it:
   `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py init $TMPDIR/<city-slug> <findings.md> --title "<today> <City> trip" --notebook "<year of the stay> Travel & Logistics" --record ~/Software/Prototypes/socrates/memory/travel.md --chaehan ~/Software/Prototypes/agentkit/skills/evernote/briefs/trip_note.md`
   Then run `next` until it prints PASS: decisions in the point 9 order, labels, sentences, table titles, and each booking linked with `note_build.py link "<words>"` (point 1).
4. Run `note_build.py write` and the code it prints in ONE execute call: the note is created through the Evernote MCP, read back and verified. Never use the Evernote shell CLI. From Claude Code, which has no Evernote MCP, hand steps 3 and 4 to opencode with `note_test.py` (the evernote skill's section "Testing a note build with deepseek").
5. Report the note's title and guid, its sections in order, the cut list and the verify result.
