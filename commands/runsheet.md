---
description: Rebuild a KUBS DT run sheet PNG from the "Run sheet cards" block at the foot of the session script
---

Rebuild the KUBS DT run sheet for session $1.

From the socrates repo root:

```
python3 projects/kubs_dt/pipeline.py runsheet --session $1            # render only, ~2.5 s
python3 projects/kubs_dt/pipeline.py runsheet --session $1 --checks   # render, then validate
```

**Run the command first — it is the verification.** Do not read the script, the block, the memory or an older render before it has run. Plain, the command renders the PNG to `KUBS DT Sn/KUBS DT session n - run sheet.png` in about 2.5 s and does nothing else. The checks are opt-in: **pass `--checks` whenever the edit touched the block, the script's minutes, the learning goal or the card text** — that is the state in which the three minute places can disagree. A re-render of unchanged content can go plain. Never spend a minute on checks the command does itself with `--checks`.

## What the command prints

- `png ready in Xs: <path> (WxH px; render Xs, save Xs)` — the PNG is on disk. Relay this line and the pixel size. The sheet is one A4-wide card grid (1900 CSS px wide at scale 2 = 3800 px, the A4 width; the PNG is cropped one margin below the last card row, so a two-row sheet is shorter than A4), four cards in every row, each card a fixed 400 px box - the box every shipped card's wording fits. The command parsed the block best-effort (a broken row still renders) and wrote the page to `projects/kubs_dt/run_sheets/rsn.html`, rendered it with headless Brave and saved the page. Plain runs then print `checks: skipped` and the timings: the render carries the command (measured 2026-10-06: render 1.7-3.3 s, save 0.2-0.3 s, checks 0.5 s).
- With `--checks`, one line per check, then a summary:
  - `block` — the block's irregularities, each with file and line: a row before the header, a wrong cell count, a missing `**Title.**` line, an `**Overrun.**` card with no row.
  - `learning goal` — read from the course design's `| **Sn** | Topic >> Learning goal |` row at render time, so the sheet and the design cannot disagree. Never copy it into the block.
  - `minutes` — rule 77's one set of minutes: the run-of-show rows, the section headers' block minutes and the block's chips must agree, per card.
  - `ink` — the drawn text read back for markup written as an HTML entity (`&gt;` draws literally; the block writes the plain character with a backslash, `\>`).
  - `fit` — every card row's border: each bottom border is paired with the next row's top border and the gap between them is read, plus the space under the last row, so a middle-row overflow is caught, not only the bottom row's. The border test is blue-family, so a run of cream chips cannot read as a border. A sheet taller than the render window is flagged as clipped; the PNG is cropped one margin (40 CSS px) below the last card row.
  - `wording` — the robot markers of RULES.md rule 2 in the script, as a note that never fails the sheet: `N flag(s), M warn(s)`, with `pipeline.py lint --session N` for the lines.
  - `budget` — free memory against the 3 GB floor (rule 75); informational once the render has run.

**Exit codes.** Plain: `0` when the PNG is written. With `--checks`: `0` when the PNG is written and all checks passed, `2` when checks flagged problems — report each failed check. Anything else: no PNG (the script or the block is missing) — report the error and stop.

The checks need only the script, the design and the rendered PNG; they can move to a command of their own if that is ever wanted. `printout` still re-renders with the checks when its PNG is stale, because that path is the gate before the TA prints.

**A failed check is fixed in the source, never in the render.** The block is the script's own wording (rule 77: a plan and its derived view are one artifact): sweep the run of show, the section headers, the chips and the design row together, then re-run the command. The sheet is never hand-edited — the next render overwrites it. The checks cover what a machine can see; a card's wording and content are still the user's.

## The block

The wording lives at the very bottom of `KUBS DT Sn/KUBS DT session n - script.md` in Google Drive, below a `---` line, as a "## Run sheet cards" block: a title line, a layout line (`**Layout.** A4 landscape, 4 columns, 400 px cards` — the one string for every sheet since the 2026-10-06 redesign; a line that still carries a column count, a px card height or `body N` renders anyway and flags in the block check, so sweep it), a shaded-cards line, an overrun line, then one table row per card (`#`, Card, Chip, Body, Source).

- **Nothing on the two header lines is prose.** The sub-line is composed from the data: `⚠ 3 Team formation` lists the cards named in `**Overrun.**` (the cards whose minutes can move; chip number plus the card's own keyword), `📖 5 The bad interview` lists the cards whose `Source` cell carries the pre-read mark (a card whose content needs a pre-read from the Kalbach book). No elastic card and no pre-read means no header line at all — never invent one.
- **A chip in the block holds the plain minutes** ("40 min"). The drawn sheet adds the running total in brackets ("40 (45) min") and prints the session total, so never write a total into the block: it is derived, and one edited minute renumbers every chip after it.
- **`Source`** names where a card's content comes from (a deck, an Evernote note, a book chapter), and it carries the sheet's one mark: `📖` for a card that needs a pre-read from the Kalbach book. The sheet lists those cards by chip number on the header line; a dash, or an empty cell, means no mark.
- The block is the only source of the sheet's wording. Never rebuild a card's text from the PNG, the deck, or a previous render — if the block is missing, report the error the command prints (it names the file) and stop.
- A script with no block yet: build the block from the current PNG or its `rsn.html`, then ask the user before writing it into the script — the block wording is the user's.
