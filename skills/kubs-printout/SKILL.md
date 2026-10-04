---
name: kubs-printout
description: Build the KUBS lecture printout files (the session script as a PDF without its "Run sheet cards" block, and the run sheet PNG) for the TA Yeonju Lee, sending them over Signal only with the send option. Use when the user asks for the printout, asks to send the lecture files, or wants them out before a lecture.
---

# KUBS printout to the TA

Builds the two files Yeonju prints for a lecture (the send is opt-in — Step 3):

- the session script as a PDF, with the "## Run sheet cards" block at its foot left out (that block is the run sheet's wording for the renderer, not lecture text)
- the run sheet PNG as it lies in the session folder

The user's message, verbatim: "Yeonju, here are my files to printout for the next lecture. Thank you!"

Shortcut: the global command `/printout N` (source `agentkit/commands/printout.md`) runs the build for session N; `/printout N send` (its send option) runs build and send.

## Step 1 — resolve the session

Session dates, Fall 2026: S1 Mon 2026-09-28, S2 Thu 2026-10-01, S3 Mon 2026-10-05, S4 Thu 2026-10-08, S5 Mon 2026-10-12, S6 Thu 2026-10-15, S7 Mon 2026-10-19, S8 Thu 2026-10-22. Map "tomorrow / Monday / the next lecture" to a number against today's date; ask only when two remain possible.

## Step 2 — build the files

From the socrates repo (`~/Software/Prototypes/socrates`):

    python3 projects/kubs_dt/pipeline.py printout --session <N>

It re-renders the run sheet PNG first when the script is newer than the sheet (about 2.7 s measured 2026-10-02; the PNG is written before its checks run — relay any failed check it prints), builds the script PDF into the repo's `out/`, and copies it into the session folder beside the script on the Drive. The `out/` build is what a send attaches; the Drive copy is the record a reader finds beside the script. Read its output; stop and report on any error — and stop here: the send is opt-in and is Step 3.

## Step 3 — send over Signal, only with the send option

Send only when the user passes the send option (`/printout N send`) or asks for the send in the conversation. The announce line goes as a text message of its own; each file follows as its own message, the sheet first, the script second:

    signal-cli -a +14244420206 send -m "Yeonju, here are my files to printout for the next lecture. Thank you!" +821031917815
    signal-cli -a +14244420206 send +821031917815 --attachment "<run sheet PNG>"
    signal-cli -a +14244420206 send +821031917815 --attachment "<script PDF>"

- Account: +14244420206, the device "socrates" linked 2026-09-30 (revocable from the phone: Signal, Settings, Linked devices). Recipient: +821031917815 (Yeonju Lee; verified registered, with an established identity in the linked account).
- **One file per message.** A message carrying two files delivers only the first: measured 2026-10-04, the S3 printout's two-file message carried both pointers in its record (both uploaded) and reached Yeonju as the run sheet alone; the script arrived when re-sent as its own single-file message. Two flags are no better: `--attachment`/`-a` is a `store` option with `nargs='*'`, so the second replaces the first and the send still exits 0 with a timestamp (measured 2026-09-30: the S2 printout reached Yeonju as the PDF alone). Each file goes as its own message.
- The text rides with the message it is sent in. Sent in the same message as the files it arrives as their caption, not as an announcement, so it goes on its own and first (the user, 2026-09-30: "you sent the message as a comment to the pdf but it should be a text message to announce the files").
- The recipient goes **before** the attachments: a positional after a `nargs='*'` option is swallowed by it (`No recipients given`, exit 1, nothing sent).
- Success prints the message timestamp; anything else is an error to report, never to retry blindly.

## Step 4 — the record is the handoff evidence

An exit code and a timestamp say nothing about the attachments, and the record proves the handoff, not the delivery: a row carrying both files still delivered one (2026-10-04). After sending, read the two newest `message_send_log_content` rows — the script's message and the sheet's — and require the sheet's row to carry `image/png` plus its file name and the script's row `application/pdf` plus its file name; for a send to someone else the CLI logs the message it handed the server:

    db=~/.local/share/signal-cli/data/755511.d/account.db    # the +14244420206 account dir
    sqlite3 "$db" "select writefile('/tmp/sent_pdf.bin', content) from message_send_log_content order by timestamp desc limit 1;" >/dev/null
    sqlite3 "$db" "select writefile('/tmp/sent_png.bin', content) from message_send_log_content order by timestamp desc limit 1 offset 1;" >/dev/null
    strings -a /tmp/sent_pdf.bin | grep -E "application/pdf|\.pdf"
    strings -a /tmp/sent_png.bin | grep -E "image/png|\.png"

A send to the user's own number leaves no entry there — a self-send is a sync message, not a delivery to retry — so a test to the user's account is read in the phone, not in the log.

## Report

Tell the user: the session, the two files with sizes, the recipient when sent, and the measured build (and send) seconds. Read Step 4's record before reporting a send as done — an exit code is not evidence, and the record covers the handoff, not the recipient's screen. If the send failed, say what the error was and leave it there.

## Guards

- Send only when the user asks in the conversation or passes the send option; never as a guessed or scheduled action. A plain `/printout N` builds and stops — never send from it, and the python command does not send at all.
- A test goes to the user's own number (+14244420206) and nowhere else; the real send goes only to Yeonju (+821031917815).
- The run sheet goes as the PNG, never converted to a PDF (the user's call, 2026-09-30).
- The message text is fixed; a different text is the user's to state.
- Never reuse an older build silently: every send runs the build first, so the PDF always matches the current script.
