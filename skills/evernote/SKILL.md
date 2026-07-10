---
name: evernote
description: Read and update Evernote notes by title via the evernote_api Thrift CLI. Use when told to read, update, append, create, or search Evernote notes. Calls shell commands; do NOT import evernote_api in-process.
---

# Evernote CLI

All commands run from the socrates repo root via the `socrates` mamba env.

Run prefix: `mamba run -n socrates python -m projects.evernote.src.evernote_api`

## Prerequisites

Token saved at `~/.local/share/socrates/evernote_token` (chmod 600).
Extract: Chrome DevTools > Application > Cookies > www.evernote.com > clipper-sso.
Alternatively: set `EVERNOTE_TOKEN` env var.

## Read-modify-write (use --raw by default)

Almost every Evernote note has tables, links, or formatting. **Always use
`--raw`** unless you are certain the note is plain text only.

With `--raw`, get-by-title returns raw ENML (HTML-like): `<table><tr><td>`,
`<div>`, `<a href="...">`, `<h3>` — full structure preserved. Without
`--raw`, tables become newline-separated cells with no row boundaries and
are impossible to edit.

1. **Read** the raw ENML:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title --raw "<title>"
   ```
   Returns `{"title": "", "content": "<en-note>...</en-note>"}`.

2. **Modify** the ENML in memory. Parse the structure, make changes, keep
    everything else intact. Content must stay valid ENML (wrapped in
    `<en-note>`).

   **After every edit**, validate the HTML structure of every `<table>`:
   - Count `<tr>` and `</tr>` in each table. They must match.
   - No row may have a missing `</tr>` — the next `<tr>` must not appear
     before the previous row's `</tr>`. Missing `</tr>` merges two rows
     into one, and the merged rows will not render in the Evernote app.
   - No row may have a duplicate `</tr>` (two consecutive `</tr>`).
   - Fix any violations before proceeding to write.

   **Table row ordering**: when a table column contains dates, rows must be
   in descending date order (newest first). After any insert, reorder rows
   to maintain this invariant.

3. **Write back** the full ENML:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api update-by-title --raw "<title>" "<full_enml>"
   ```
   With `--raw`, content is sent to Evernote as-is with no wrapping.

4. **Verify** the write took effect by re-reading:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title --raw "<title>"
   ```
   **Never trust** `{"updated": true}` alone. The Evernote API can return
   success even when cloud-side sync fails silently. Always grep the
   re-read output for the specific values you changed and confirm they
   appear.

**Never** call `update-by-title` without first reading the note. You would
destroy existing content.

## Append (add to end only)

```
mamba run -n socrates python -m projects.evernote.src.evernote_api append-by-title "<title>" "<text>"
```
Reads, appends, and writes back in one call. For log entries or notes where
order does not matter.

## Find a note

```
mamba run -n socrates python -m projects.evernote.src.evernote_api find-note "<title>"
```
Exact title match: returns `{"guid": "...", "title": "..."}`, exit 0.
Multiple or partial matches: candidate list on stdout, exit 5.
No results: stderr message, exit 6.

## Building blocks (by guid)

```
mamba run -n socrates python -m projects.evernote.src.evernote_api notebooks
mamba run -n socrates python -m projects.evernote.src.evernote_api search <query> [--notebook <name>] [--max <n>]
mamba run -n socrates python -m projects.evernote.src.evernote_api get <guid> [--raw]
mamba run -n socrates python -m projects.evernote.src.evernote_api update <guid> <content> [--raw]
mamba run -n socrates python -m projects.evernote.src.evernote_api append <guid> <text>
mamba run -n socrates python -m projects.evernote.src.evernote_api create <title> <content> [--notebook <name>]
```

## Output

All output is JSON to stdout. Errors to stderr. Exit codes:
- 0: success
- 2: auth error (token invalid/expired)
- 3: permission denied
- 4: network error or retries exhausted
- 5: ambiguous title (multiple matches or partial matches, stdout lists candidates)
- 6: title not found (search returned nothing)

## Disambiguation

If find-note or get-by-title exits 5, read the candidate list from stdout,
present it to the user, and ask which note to use. Then use the guid from
the selected candidate with the by-guid commands.
