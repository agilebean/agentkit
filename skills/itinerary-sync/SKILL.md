---
name: itinerary-sync
description: Write Chaehan's travel dates and his flight, train, hotel, apartment and rental-car bookings into travel.md, travelitinerary.csv and the year's Evernote itinerary note in one pass, inferring the itinerary rows from a booking's own dates. Runs in opencode on DeepSeek with the Evernote MCP. Use when Chaehan states travel dates or moves one in chat, mentions or forwards a booking, or right after the receipt-note skill has made a booking note.
---

# itinerary-sync

Three records hold Chaehan's travel and must show the same rows: `memory/travelitinerary.csv`
(one row per place, rule 18 reads it), the schedule table in `memory/travel.md` (`## 2027 schedule`)
and the Evernote note "<year> Travel Itinerary". The script `scripts/itinerary_sync.py` is their one
writer. You read the input and write the facts as JSON; the script finds the rows, moves or adds
them, links the booking notes, adds the € and $ figures, keeps his header formula and verifies the
notes. Never edit those tables, the CSV or the itinerary notes by hand for a date or a booking.

Chaehan's rules, 2026-11-07, which the script applies:

- A row starts on the day he is in the place: the hotel check-in day. A flight note's title names
  the departure day; the next place starts on the landing day, the day after for an overnight flight.
- Dates he gives in chat go to all three records at once. A booking alone moves or adds the rows
  from its own dates. A row whose date already comes from a booking (✅ in its date cell) is never
  moved by a later date; the script reports the conflict instead.
- A December row that both years' notes show gets the link in both; its € counts only in the
  note of the year the stay starts.
- The header is his 2026 formula: `<€/month>€/m [12m] -> €a+b+... = total | $/€=1.17`.
- A return ticket's price is split over its two flights (`"split": 2`), as his 2026 note does (€2092/2).

## Steps

1. **Read the input.** A chat message: his words. A booking note: fetch it with `get_note` in
   `execute` and read its title and text. Name each place by the itinerary's city name, as the
   CSV writes it: Osaka for KIX, UKB and ITM, Seoul for ICN and GMP, Melbourne for MEL.
2. **Write `events.json`** in a new folder under `$TMPDIR`, one event per landing or stay:

   ```json
   {"events": [
    {"kind": "flight", "from": "Melbourne", "to": "Osaka", "depart": "2027-03-01", "arrive": "2027-03-02",
     "price": 2092, "currency": "EUR", "split": 2, "provider": "China Eastern", "ref": "MZ33K4",
     "note_guid": "0549d1c1-96f4-9a5c-b648-e95ad424f7ab",
     "note_title": "2026-12-11 ~ 2027-03-01 Flug Osaka-Melbourne 2092€ MZ33K4"},
    {"kind": "hotel", "city": "Osaka", "checkin": "2027-03-02", "checkout": "2027-03-04",
     "price": 60000, "currency": "JPY", "provider": "Imperial Hotel Osaka", "ref": "5143123603",
     "note_guid": null, "note_title": null, "text": "Imperial Hotel Osaka 03-02~04 ¥60000"},
    {"kind": "dates", "city": "Seoul", "date": "2027-03-16", "text": "Seoul from 2027-03-16"}
   ]}
   ```

   Kinds: `flight`, `train`, `bus`, `ferry` (from, to, depart, arrive); `hotel`, `apartment`
   (city, checkin, checkout); `car` (city, checkin = pickup, checkout = return). `dates` (city,
   date). `arrive` is the local landing day. A connection is not a place: one event runs from the
   origin to the final destination, and a return ticket is two events with `"split": 2`. `price` is
   the whole ticket's or stay's total as a bare number, with its `currency`. Leave a field `null`
   when the input does not give it; a missing landing day or check-in day is asked with the
   question tool, never guessed (rule 18). A booking without a note gets `text`, the line the row
   will show.
3. **Start the run** from the socrates folder:
   `python3 ~/Software/Prototypes/agentkit/skills/itinerary-sync/scripts/itinerary_sync.py start <events.json>`.
   `--repo <folder>` names the socrates checkout when the session works in another one, and
   `--dry-run` plans without writing. Exit 2 lists what to fix in `events.json`; fix it and start
   again.
4. **Run the printed code in ONE `execute` call, exactly as printed.** It reads the notes, fetches
   the planned `edit_note` replacements from the script on 127.0.0.1, applies them, reads the notes
   back and returns the report. The script writes travel.md and the CSV only after every note
   verified. If the call fails (a refused fetch, a locked note), report the error as it reads and
   stop: no hand edits.
5. **Report to Chaehan** from the returned report (also `report.md` beside `events.json`): what
   changed in each record. Ask each line under "Ask Chaehan" with the question tool. Pass on each
   line under "Notes", such as row prose that still names an old date; that prose is his to change.
6. **Commit and push** `memory/travel.md` and `memory/travelitinerary.csv` by filename (rule 3).

## Outside opencode

Claude Code has no Evernote MCP, so it runs this skill in opencode on DeepSeek, with a brief that
names the input ("Run the itinerary-sync skill (read
~/Software/Prototypes/agentkit/skills/itinerary-sync/SKILL.md) for: <his words or the booking
notes' titles and guids>"):

```
python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_test.py --brief <brief.md> --out <folder> --cwd <socrates folder> --title "itinerary sync"
```

`<folder>/report.md` names the provider and model, the steps and cost, and the agent's last
message, which holds the sync report.

## Test without Evernote

`itinerary_sync.py plan <events.json> --enml <guid>=<file> ... --out <folder>` applies the plan to
saved ENML (a `get_note` result or the raw ENML) and prints the report: no note and no local file
is touched.
