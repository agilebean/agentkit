---
description: Build and send the KUBS DT printout files (session script PDF + run sheet PNG) for a session to the TA over Signal
---

Send Yeonju the printout files for KUBS DT session $1.

Step 1, build the two files (the script as a PDF without its "Run sheet cards" block, and the run sheet PNG; the sheet is re-rendered first when the script is newer — the re-render writes the PNG before its checks run, so relay any failed check it prints). From the socrates repo root:

```
python3 projects/kubs_dt/pipeline.py printout --session $1
```

It builds the PDF in the repo's `out/` and copies it into the session folder on the Drive, so the session folder always holds the current script PDF beside its script. Attach the `out/` PDF and the run sheet PNG from the session folder; the Drive copy is the record, not a second attachment.

Step 2, send them over Signal — the announce line as its own text message, then the two files as a second message (the two file paths are the ones step 1 printed):

```
signal-cli -a +14244420206 send -m "Yeonju, here are my files to printout for the next lecture. Thank you!" +821031917815
signal-cli -a +14244420206 send +821031917815 --attachment "<run sheet PNG>" "<script PDF>"
```

Step 3, read the record before reporting: dump the newest `message_send_log_content` row's blob from `~/.local/share/signal-cli/data/755511.d/account.db` and check it carries `image/png` **and** `application/pdf`. Exit 0 plus a timestamp proves neither file. (A send to Chaehan's own number is not logged; a test to his account is read in the phone.)

Then report the session, the two files with sizes, the recipient, and the measured build and send seconds.

- The message text is fixed; a different text is Chaehan's to state.
- Both files go under ONE `--attachment` flag: it is a `store` option with `nargs='*'`, so a second `--attachment` replaces the first and the files silently go out short.
- The recipient goes before the attachments: a positional after that option is swallowed by it (`No recipients given`, exit 1).
- The run sheet goes as the PNG, never as a PDF.
- No session number given: ask which one.
- Success is a printed timestamp; anything else is an error to report, never to retry blindly.
- Account: the linked device "socrates" (+14244420206), revocable in the phone's Signal under Linked devices. Full procedure and guards: the `kubs-printout` skill in agentkit.
