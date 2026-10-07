---
name: receipt-note
description: Turn a receipt or booking confirmation into an Evernote note: an itinerary card PNG at the top, the booking facts below, no TL;DR. Use when the user books a flight, hotel, apartment or ticket and forwards or mentions the confirmation, or asks to put a confirmation into Evernote.
---

# receipt-note

A receipt or confirmation becomes a note the user can read at a glance months
later: one card image with the name, the dates and the price, and the facts
underneath in the words he would use. The source is the confirmation itself —
the email, the PDF, the booking page — never a summary of it.

## The rule that governs the shape

**No TL;DR on a note made from a receipt or confirmation.** A TL;DR belongs to
a meeting summary or to an analysis of the user's results. A confirmation note
opens with the card and then states the facts; nothing restates them above.
(Stated 2026-10-07; the evernote skill carries the same rule.)

Order: the card image first, above everything (the evernote skill's graphic
rule), then the facts.

## Steps

1. **Get the source.** Find the confirmation email or document. The Gmail read
   path is the OAuth CLI (`agentkit.gmail.cli`) or, when the token is expired,
   IMAP with the app password (`~/.gmail/gmail-smtp-app-password`). Read the
   *whole* message, to its last line, and read the property's own messages
   too: Booking.com confirmations end with an **Important details** block, and
   the hotel or airline often writes again separately. The shuttle timetable,
   the facility fees, the accommodation tax, the breakfast price, the
   maintenance closures and the check-in conditions all live in those blocks,
   and a dump cut at the first screen misses them.
   (2026-10-07: the Imperial Hotel Osaka's pool fee, its COMPLIMENTARY shuttle
   timetable and the Osaka accommodation tax were all missed because the email
   body was truncated; the hotel's own message to the guest carried the exact
   fees. Read to the end, and read every message in the thread.)

2. **Collect the fields the user searches by later.** At minimum the date, the
   provider, the price, and the reference or booking number. Then the fields
   that decide the stay: room type, nights, timing, baggage, seat, address,
   phone, cancellation deadline. Keep the confirmation's own wording for the
   room or fare name. Then the terms that cost money or change the plan: what
   the price excludes (taxes), what closes and when, and what the property
   offers free.

3. **Make the image the source itself, not a rebuild.** When the confirmation
   is an HTML email, screenshot the email:
   ```
   python3 ~/.agents/skills/receipt-note/email_shot.py --eml mail.eml --out shot.png --width 760
   ```
   The PNG then carries everything the email carries: the airline card, the
   seat, the baggage table, the price breakdown. `--html page.html` does the
   same for a saved web page. The browser panel is not the way in — it is
   usually signed out of Gmail — so pull the message over IMAP into an `.eml`
   file first. A note whose card summarised an email the user could have seen
   in full will be sent back (2026-10-07: the flight card lacked the seat and
   baggage detail that sat in the confirmation, and the note was rebuilt around
   the email itself).

   Use the card renderer where there is no renderable source: a PDF, a
   plain-text confirmation, a receipt photo.
   ```
   python3 ~/.agents/skills/receipt-note/render_card.py --spec card.json --out card.png
   ```
   `card.json`:
   ```
   {"title": "Imperial Hotel Osaka",
    "subtitle": "Booking.com confirmation 5143123603 - booked 2026-10-07",
    "rows": [["Check-in", "Fri, Dec 4, 2026 (14:00-24:00)"],
             ["Check-out", "Fri, Dec 11, 2026 (until 12:00)"],
             ["Room", "Standard Double Room, Non-Smoking"],
             ["Nights", "7"]],
    "footer": "Total Y141,000 paid"}
   ```
   Every row is `[label, value]`; a row with an empty label runs full width.
   The card is tight-cropped, so the PNG is the card and nothing else.

   Never present a card as the email. Look at the PNG before uploading it (the
   read tool renders images): a wrong figure on the image is the one error the
   user cannot miss.

4. **Write the note.**
   - Title: date first, then the entity and the number that matters
     (`2026-12-04~11 Hotel: Imperial Hotel Osaka 7n Y141000`;
     `2026-12-04 Flugticket ICN-UKB Asiana OZ1163 KRW154344`).
   - Notebook: the topic's notebook (travel → that year's `... Travel & Logistics`;
     health → Health; finance → Chaehan Financials). Ask when no notebook matches.
   - Body: no TL;DR, no label prefixes. Write it as a **bulleted hierarchy** with the
     sub-facts indented under their parent, so the shape is visible at a glance:
     the entity, then its dates, its price, its references as sub-bullets. Say it
     the way it would be said in chat.
   - The card goes in at the top, and the facts sit below with the exact
     references (booking reference, e-ticket, PIN only when the user needs it).

5. **Embed the card and verify.** `embed-image "<note title>" <card.png> --top`
   (the CLI is right here: it uploads the resource and rewrites the ENML in one
   call, where the MCP path needs the GCS bridge for binary bytes). Then read the
   note back and confirm one `<en-media type="image/png" hash="...">` with the
   local file's MD5, no `<img src=` left behind, and the facts present.
   A freshly created note is not searchable for a minute or two — a "Title not
   found" from a title lookup right after `create` is index lag, not a failure;
   retry, or hold the note's GUID.

6. **Link it from where the trip lives.** Add the note as an inline richlink in
   the itinerary note's row (or the ledger the booking belongs to), so the plan
   and the confirmation point at each other.

## Sweep superseded copies

Before creating, search the notebook for the same booking. An earlier version
of the same reservation, or a placeholder note created while the booking was
still open, is folded in and deleted (evernote skill, RULES.md rule 31). A note
that only says "booking details to be added" is replaced by the real note, not
kept beside it.
