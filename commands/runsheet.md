---
description: Rebuild a KUBS DT run sheet PNG from the "Run sheet cards" block at the foot of the session script
---

Rebuild the KUBS DT run sheet for session $1.

From the socrates repo root:

```
python3 projects/kubs_dt/pipeline.py runsheet --session $1
```

The run sheet's wording lives at the very bottom of `KUBS DT Sn/KUBS DT session n - script.md` in Google Drive, below a `---` line, as a "## Run sheet cards" block: a title line, a sub-line, a layout line, a shaded-cards line, then one table row per card (`#`, Card, Chip, Body). The command reads that block, writes the HTML page to `projects/kubs_dt/run_sheets/rsn.html`, renders it with the headless Brave browser, crops the ink, and overwrites `KUBS DT Sn/KUBS DT session n - run sheet.png`.

- The block is the only source of the sheet's wording. Never rebuild a card's text from the PNG, the deck, or a previous render — if the block is missing or a row breaks the table, report the error the command prints (it names the file and line) and stop.
- Relay the measured seconds it prints (parse+html, render, crop) and the PNG's pixel size.
- A script with no block yet: build the block from the current PNG or its `rsn.html`, then ask Chaehan before writing it into the script — the block wording is his.
- The markdown sibling of the sheet: a change to either the block or the script's body still has to be swept into the other, and the run sheet is re-rendered in the same pass (the script and the sheet stay in sync, memory/kubs.md).
