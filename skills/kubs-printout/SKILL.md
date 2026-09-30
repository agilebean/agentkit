---
name: kubs-printout
description: Build and send the KUBS lecture printout files (the session script as a PDF without its "Run sheet cards" block, and the run sheet PNG) to the TA Yeonju Lee over Signal. Use when Chaehan asks to send the lecture files or the printout for a session to Yeonju, or to get them out before a lecture.
---

# KUBS printout to the TA

Sends the two files Yeonju prints for a lecture:

- the session script as a PDF, with the "## Run sheet cards" block at its foot left out (that block is the run sheet's wording for the renderer, not lecture text)
- the run sheet PNG as it lies in the session folder

Chaehan's message, verbatim: "Yeonju, here are my files to printout for the next lecture. Thank you!"

Shortcut: the global command `/printout N` (source `agentkit/commands/printout.md`) runs these same steps for session N.

## Step 1 — resolve the session

Session dates, Fall 2026: S1 Mon 2026-09-28, S2 Thu 2026-10-01, S3 Mon 2026-10-05, S4 Thu 2026-10-08, S5 Mon 2026-10-12, S6 Thu 2026-10-15, S7 Mon 2026-10-19, S8 Thu 2026-10-22. Map "tomorrow / Monday / the next lecture" to a number against today's date; ask only when two remain possible.

## Step 2 — build the files

From the socrates repo (`~/Software/Prototypes/socrates`):

    python3 projects/kubs_dt/pipeline.py printout --session <N>

It re-renders the run sheet PNG first when the script is newer than the sheet (about 1.5 s fresh, about 4.5 s with the re-render), then prints three paths: the script PDF in the repo's `out/`, the run sheet PNG in the session folder, and the script PDF's copy in that same session folder on the Drive. The latter is the record a reader finds beside the script; the `out/` build is what Step 3 attaches. Read the output; stop and report on any error.

## Step 3 — send over Signal, as two messages

The announce line is a text message of its own; the two files follow as a second message.

    signal-cli -a +14244420206 send -m "Yeonju, here are my files to printout for the next lecture. Thank you!" +821031917815
    signal-cli -a +14244420206 send +821031917815 --attachment "<run sheet PNG>" "<script PDF>"

- Account: +14244420206, the device "socrates" linked 2026-09-30. Revocable from the phone: Signal, Settings, Linked devices.
- Recipient: +821031917815 (Yeonju Lee; verified registered, with an established identity in the linked account).
- **Both files go under ONE `--attachment` flag.** `--attachment`/`-a` is a `store` option with `nargs='*'`, so two flags do not add up: the second replaces the first, and the send still exits 0 with a timestamp. Measured 2026-09-30 - the S2 printout reached Yeonju as the PDF alone (its send-log body carries `application/pdf` once and `image/png` not at all) because the command carried `--attachment PNG --attachment PDF`.
- The text rides with the message it is sent in. Sent in the same message as the files it arrives as their caption, not as an announcement, so it goes on its own and first (Chaehan, 2026-09-30: "you sent the message as a comment to the pdf but it should be a text message to announce the files").
- The recipient goes **before** the attachments: a positional after a `nargs='*'` option is swallowed by it (`No recipients given`, exit 1, nothing sent).
- Success prints the message timestamp; anything else is an error to report, never to retry blindly.

## Step 4 — verify what actually went, then report

An exit code and a timestamp say nothing about the attachments. Read the record — for a send to someone else the CLI logs the message it handed to the server:

    db=~/.local/share/signal-cli/data/755511.d/account.db    # the +14244420206 account dir
    sqlite3 "$db" "select writefile('/tmp/sent.bin', content) from message_send_log_content order by timestamp desc limit 1;" >/dev/null
    strings -a /tmp/sent.bin | grep -E "image/png|application/pdf|\.pdf|\.png"

Both `image/png` and `application/pdf` must appear, one line each, together with the two file names. A send to Chaehan's own number leaves no entry there — a self-send is a sync message, not a delivery to retry — so a test to his account is read in the phone, not in the log.

## Report

Tell Chaehan: the session, the two files with sizes, the recipient, and the measured build and send seconds (one per message). Read Step 4's record before reporting a send as done — an exit code is not evidence. If the send failed, say what the error was and leave it there.

## Guards

- Send only when Chaehan asks in the conversation; never as a guessed or scheduled action.
- A test goes to Chaehan's own number (+14244420206) and nowhere else; the real send goes only to Yeonju (+821031917815).
- The run sheet goes as the PNG, never converted to a PDF (his call, 2026-09-30).
- The message text above is the fixed wording; a different text is his to state.
- Never reuse an older build silently: every send runs Step 2 first, so the PDF always matches the current script.
