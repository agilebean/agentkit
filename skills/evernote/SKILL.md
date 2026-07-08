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

## How to update a note with tables (read-modify-write, --raw)

Notes with tables, links, or formatting CANNOT be edited using plain text
mode. The plain text output strips all structure (tables become
newline-separated rows with space-separated cells, losing boundaries).

For any note that contains tables or structured formatting, use `--raw`:

1. **Read** the raw ENML:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title "<title>" --raw
   ```
   Returns `{"title": "", "content": "<en-note>...</en-note>"}`. Content is
   raw ENML (HTML-like): tables are `<table><tr><td>...</td></tr></table>`,
   text is in `<div>` tags, line breaks are `<br/>`.

2. **Modify** the ENML in memory. Parse the table structure, add or change
   `<tr>`/`<td>` elements, keep everything else intact. The content must
   stay valid ENML (wrapped in `<en-note>...</en-note>`).

3. **Write back** the full ENML:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api update-by-title "<title>" "<full_enml>" --raw
   ```
   With `--raw`, the content is sent to Evernote as-is, no wrapping or
   escaping applied. You are responsible for valid ENML.

**Never** call `update-by-title` without first reading the note. You would
destroy existing content.

## How to update a plain text note (no tables)

For notes that are plain text only (no tables, no links, no formatting):

1. **Read**:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title "<title>"
   ```
   Content is plain text. Newlines separate lines.

2. **Write back** the full text:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api update-by-title "<title>" "<full_new_content>"
   ```
   Without `--raw`, content is wrapped in ENML automatically (plain text to
   div/br tags, XML-escaped).

## Append (add to end only)

If the user just wants to add text at the bottom with no structured edit:
```
mamba run -n socrates python -m projects.evernote.src.evernote_api append-by-title "<title>" "<text>"
```
This reads, appends, and writes back in one call. Use for log entries,
notes, or anything where order does not matter.

## Find a note (check title exists)

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
