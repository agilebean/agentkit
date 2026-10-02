---
description: Rebuild a KUBS DT run sheet PNG from the "Run sheet cards" block at the foot of the session script
---

Rebuild the KUBS DT run sheet for session $1.

From the socrates repo root:

```
python3 projects/kubs_dt/pipeline.py runsheet --session $1
```

**Run the command first — it is the verification.** Do not read the script, the block, the memory or an older render before it has run. The command renders first and checks second: the PNG is written to `KUBS DT Sn/KUBS DT session n - run sheet.png` in seconds, and only then does it validate. Never spend a minute on checks the command does itself.

## What the command prints

- `png ready in Xs: <path> (WxH px; render Xs, crop Xs)` — the PNG is on disk. Relay this line and the pixel size. The command parsed the block best-effort (a broken row still renders), wrote the page to `projects/kubs_dt/run_sheets/rsn.html`, rendered it with headless Brave and cropped the ink.
- One line per check, then a summary:
  - `block` — the block's irregularities, each with file and line: a row before the header, a wrong cell count, a missing `**Title.**` line, an `**Overrun.**` card with no row.
  - `learning goal` — read from the course design's `| **Sn** | Topic >> Learning goal |` row at render time, so the sheet and the design cannot disagree. Never copy it into the block.
  - `minutes` — rule 77's one set of minutes: the run-of-show rows, the section headers' block minutes and the block's chips must agree, per card.
  - `ink` — the drawn text read back for markup written as an HTML entity (`&gt;` draws literally; the block writes the plain character with a backslash, `\>`).
  - `fit` — every card row's border: each bottom border is paired with the next row's top border and the gap between them is read, plus the space under the last row, so a middle-row overflow is caught, not only the bottom row's. The border test is blue-family, so a run of cream chips cannot read as a border.
  - `wording` — the robot markers of RULES.md rule 2 in the script, as a note that never fails the sheet: `N flag(s), M warn(s)`, with `pipeline.py lint --session N` for the lines.
  - `budget` — free memory against the 3 GB floor (rule 75); informational once the render has run.

**Exit codes.** `0`: the PNG is written, all checks passed. `2`: the PNG is written and checks flagged problems — report each failed check. Anything else: no PNG (the script or the block is missing) — report the error and stop.

**A failed check is fixed in the source, never in the render.** The block is the script's own wording (rule 77: a plan and its derived view are one artifact): sweep the run of show, the section headers, the chips and the design row together, then re-run the command. The sheet is never hand-edited — the next render overwrites it. The checks cover what a machine can see; a card's wording and content are still Chaehan's.

## The block

The wording lives at the very bottom of `KUBS DT Sn/KUBS DT session n - script.md` in Google Drive, below a `---` line, as a "## Run sheet cards" block: a title line, a layout line, a shaded-cards line, an overrun line, then one table row per card (`#`, Card, Chip, Body, Source).

- **Nothing on the two header lines is prose.** The sub-line is composed from the data: `⚠ 3 Team formation` lists the cards named in `**Overrun.**` (the cards whose minutes can move; chip number plus the card's own keyword), `📖 5 The bad interview` lists the cards whose `Source` cell carries the pre-read mark (a card whose content needs a pre-read from the Kalbach book). No elastic card and no pre-read means no header line at all — never invent one.
- **A chip in the block holds the plain minutes** ("40 min"). The drawn sheet adds the running total in brackets ("40 (45) min") and prints the session total, so never write a total into the block: it is derived, and one edited minute renumbers every chip after it.
- **`Source`** names where a card's content comes from (a deck, an Evernote note, a book chapter), and it carries the sheet's one mark: `📖` for a card that needs a pre-read from the Kalbach book. The sheet lists those cards by chip number on the header line; a dash, or an empty cell, means no mark.
- The block is the only source of the sheet's wording. Never rebuild a card's text from the PNG, the deck, or a previous render — if the block is missing, report the error the command prints (it names the file) and stop.
- A script with no block yet: build the block from the current PNG or its `rsn.html`, then ask Chaehan before writing it into the script — the block wording is his.
