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
   *whole* message: the price lines, the reference numbers, the cancellation
   terms and the room or fare class usually sit in different blocks.

2. **Collect the fields the user searches by later.** At minimum the date, the
   provider, the price, and the reference or booking number. Then the fields
   that decide the stay: room type, nights, timing, baggage, seat, address,
   phone, cancellation deadline. Keep the confirmation's own wording for the
   room or fare name.

3. **Build the card.**
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
   Look at the PNG before uploading it (the read tool renders images): a
   wrong figure on the card is the one error the user cannot miss.

   **A real screenshot of the email** is only for when it is already open and
   readable — the browser panel reports whether it can drive the page, and
   Gmail in that panel is usually signed out. Rendering from the message's own
   text is the reliable path, and it must be labelled honestly: the subtitle
   names the confirmation it came from. Never present a card as the email.

4. **Write the note.**
   - Title: date first, then the entity and the number that matters
     (`2026-12-04~11 Hotel: Imperial Hotel Osaka 7n Y141000`;
     `2026-12-04 Flugticket ICN-UKB Asiana OZ1163 KRW154344`).
   - Notebook: the topic's notebook (travel → that year's `... Travel & Logistics`;
     health → Health; finance → Chaehan Financials). Ask when no notebook matches.
   - Body: no TL;DR, no label prefixes. Say it the way it would be said in chat.
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
