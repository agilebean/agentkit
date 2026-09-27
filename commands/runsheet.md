---
description: Rebuild a KUBS DT run sheet PNG from the "Run sheet cards" block at the foot of the session script
---

Rebuild the KUBS DT run sheet for session $1.

From the socrates repo root:

```
python3 projects/kubs_dt/pipeline.py runsheet --session $1
```

The run sheet's wording lives at the very bottom of `KUBS DT Sn/KUBS DT session n - script.md` in Google Drive, below a `---` line, as a "## Run sheet cards" block: a title line, a layout line, a shaded-cards line, an overrun line, then one table row per card (`#`, Card, Chip, Body, Source). The command reads that block, writes the HTML page to `projects/kubs_dt/run_sheets/rsn.html`, renders it with the headless Brave browser, crops the ink, and overwrites `KUBS DT Sn/KUBS DT session n - run sheet.png`.

- **Nothing on the two header lines is prose.** The sub-line is composed from the data: `⚠ 3 Team formation` lists the cards named in `**Overrun.**` (the cards whose minutes can move; chip number plus the card's own keyword), `□ 5 The bad interview` lists the cards whose `Source` cell is empty. No elastic card and no gap means no header line at all — never invent one.
- **The learning goal is read, not written.** It comes from the `| **Sn** | Topic >> Learning goal |` row of `KUBS DT Course Design/KUBS DT Course Design.md` at render time, so the sheet and the design cannot disagree. Never copy it into the block.
- **A chip in the block holds the plain minutes** ("40 min"). The drawn sheet adds the running total in brackets ("40 (45) min") and prints the session total, so never write a total into the block: it is derived, and one edited minute renumbers every chip after it.
- **`Source`** names where a card's content comes from (a deck, an Evernote note, a book chapter). A dash means nothing to refine; an empty cell is a gap, and the sheet reports it by chip number.
- **agentkit rule 77 governs this pair**: a change to the block or to the script body lands in the other in the same turn, and the render follows. The sheet is never hand-edited — the next render overwrites it.
- The block is the only source of the sheet's wording. Never rebuild a card's text from the PNG, the deck, or a previous render — if the block is missing, a row breaks the table, or an Overrun card has no row, report the error the command prints (it names the file and line) and stop.
- Relay the measured seconds it prints (parse+html, render, crop) and the PNG's pixel size.
- A script with no block yet: build the block from the current PNG or its `rsn.html`, then ask Chaehan before writing it into the script — the block wording is his.
