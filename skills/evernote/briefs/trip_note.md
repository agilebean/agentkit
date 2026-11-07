Chaehan's standing instructions for a trip note: a note about one stay, its bookings and the decisions he makes for it. They come from his corrections of the note "2026-10-04 Osaka trip" on 2026-11-07, his words quoted. Pass this file to `note_build.py init` with `--chaehan`, and a second `--chaehan` file with what he said about the trip at hand.

1. Bookings link to their notes. Each booking the note names (the hotel stay, each flight, a train, a rental) links to its own Evernote note; find it with `note_build.py link "<words>"` and put the printed link into the item that names the booking (edits.tsv). "important info should be linked to other evernotes, eg for booking hotel there is clearly an evernote you must find".

2. Side plans leave. A day or night in another city, a day trip, and the flight onward after the stay are W, unless one of the note's decisions needs them. "kyoto and kobe days and melbourne end - this is clutter bec it is just side info".

3. Comparisons he will not act on leave. A place he will not book (a flat kept only to compare prices) and generic price tables are W. "atinn is purely for comparison purposes i don't intend to sleep there, so compress, so delete that info and table with atinn and generic hotels - clutter".

4. Getting around is short. Keep the default route from where he stays and how he pays at the gate; routes to other cities are W. "getting around: make concise, clutter is all after Back from either city to about ten minutes." Asked about the routes to Kyoto and Kobe: "Cut them".

5. Dates come from his record. The stay's dates and night counts come from his travel record (`socrates/memory/travel.md`), never from the old note, and every figure that depends on the stay's length (a monthly pass, the number of swims or nights) is worked out again for it, the arithmetic in found.md. "i already changed my leave from osaka to 15-16 march"; on the pool pass still counted over three and a half weeks: "Fix it".

6. One table per kind of place. Places of one kind (shops, restaurants) are one table of the best three or so, each row with its street address checked on the place's own page and the trip from where he stays; each address and trip goes into found.md with its source URL first. "merge the two shop tables, and condense to the very best, verify their address, as the second table contains useless locations far from osaka like kobe".

7. A topic that grows into its own subject moves out. It becomes its own note with `init --guid <trip note> --section "<heading>" --title "<date> <subject>" --notebook "<its domain's notebook>"`, its items in the trip note are M with that title as parent, and one item keeps a line with its link. "outsource swimming pools osaka as separate evernote".

8. The script holds the rest: every table has an H3 title ("the tables lack titles at H3"), no trade jargon such as "band" ("robotic: bands"), an approximate number is written ~N, and every sentence ends with a space before the next ("the interpunctuation is off, you forgot spaces between sentences: service.Photography").
