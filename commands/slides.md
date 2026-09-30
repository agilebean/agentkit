---
description: Rebuild a KUBS DT keynote deck from the session's slides markdown
---

Rebuild the KUBS DT keynote deck for session $1.

From the socrates repo root:

```
python3 projects/kubs_dt/pipeline.py slides --session $1
```

The deck's text, slide by slide, lives in `KUBS DT Sn/KUBS DT session n - slides.md` in Google Drive — `## n · type · title` sections for the cover (`title`), the numbered content slides (`rows`), and the two-column comparison (`opposition`). The command takes a uniquely named copy of the deck, writes every slide's text and notes from the md, recomputes every row's colour bar against the rendered text, verifies bar and text line up within 2 px, and overwrites `KUBS DT Sn/KUBS DT WS2026 Enn.key`; the previous deck stays in the stage folder as a backup. Measured on E02, 7 slides: read 28 s, apply+save+export 20 s, measure 0.6 s, bars+save+export 12 s, verify 0.7 s.

- **The md is the only source of slide text.** Never rebuild a slide's text from the deck or from a render. If a deck has no md yet, write the md from the deck's current text once (byte-exact, including the cover's line-separator character), then edit only the md.
- **Homework slides take session 1's blue band** (#384894, the `blueband-3624.png` asset inside the E01 deck) instead of the session colour — the standing rule for every deck. The band swap is not wired into the command yet: a slide marked `· homework` makes the command stop and say so.
- **A deck open in Keynote refuses the run — close its window first.** Keynote autosave fails while its file is being rewritten ("the file has been changed by another application"), and the alert that follows hangs every further osascript call, `close` included (force-quit Keynote to recover; only then fix the cause).
- **Bar geometry comes from a render, not from the boxes.** The command renders the deck, measures each row's ink span, and places the bar to cover it exactly: bar box y = ink top + 3, height = ink span − 5; the drawn bar bleeds 3 px above and 2 px below its box at 1920x1080. Never hand-place a bar — re-run the command.
- **Structure changes are not the command's job.** If the md and the deck disagree on slide count, row count or pairs, it stops and names the slide; add or remove the row in Keynote first, then re-run.
- The command prints its measured seconds per step, the per-row bar/text offsets, and leaves a backup of the previous deck in the stage folder. Relay those numbers.
- If osascript times out, Keynote is showing a modal alert: look at its screen, dismiss it, close the stray `slides_build_*` document, and run again. Never overwrite a `.key` file while Keynote has it open.
