---
description: Build the KUBS DT printout files (session script PDF + run sheet PNG) for a session; send them to the TA over Signal only with the send option
---

Build the printout for KUBS DT session $1, and send it to Yeonju only when the arguments carry the send option. Arguments: `$ARGUMENTS`

From the socrates repo root:

```
python3 projects/kubs_dt/pipeline.py printout --session $1
```

It re-renders the run sheet first when the script is newer — the re-render writes the PNG before its checks run, so relay any failed check it prints — builds the script PDF in `out/`, and copies it into the session folder on the Drive. The `out/` build is what a send attaches; the Drive copy is the record beside the script. Stop here unless the send option was given or the user asked to send.

Send (only as `/printout $1 send`, or an explicit ask), as two messages — the announce line on its own, then both files in one:

```
signal-cli -a +14244420206 send -m "Yeonju, here are my files to printout for the next lecture. Thank you!" +821031917815
signal-cli -a +14244420206 send +821031917815 --attachment "<run sheet PNG>" "<script PDF>"
```

Both files ride under ONE `--attachment` flag (a second flag replaces the first and the sheet silently goes out nowhere), and the recipient goes before it (a positional after the `nargs='*'` option is swallowed: `No recipients given`, exit 1). After sending, read the newest `message_send_log_content` row's blob from `~/.local/share/signal-cli/data/755511.d/account.db` and check it carries `image/png` **and** `application/pdf` together with both file names — exit 0 plus a timestamp proves neither. (A send to the user's own number is not logged; a test to the user's account is read in the phone.)

Then report the session, the two files with sizes, the recipient when sent, and the measured build (and send) seconds.

- Never send without the send option or an explicit ask from the user; `/printout N` alone builds and stops.
- The message text is fixed; a different text is the user's to state.
- No session number given: ask which one.
- An error in a send is reported, never retried blindly.
- Account: the linked device "socrates" (+14244420206), revocable in the phone's Signal under Linked devices. Full procedure and guards: the `kubs-printout` skill in agentkit.
