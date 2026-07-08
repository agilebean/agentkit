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

## How to update a note (read-modify-write)

`update-by-title` REPLACES the entire note content. It does NOT merge or
patch. To add a row to a table, insert a line in a list, or change one
field, you must:

1. **Read** the note first:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title "<title>"
   ```
   Returns `{"title": "...", "content": "..."}`. Content is plain text:
   tables come back as rows separated by newlines, cells within a row
   separated by a single space.

2. **Modify** the content in memory. Reconstruct the full text with the
   change applied. Examples:
   - Add a table row: append a new line with cells joined by spaces.
   - Add a list item: append a new line.
   - Change a value: find the line, replace it, keep everything else intact.

3. **Write back** the FULL content:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api update-by-title "<title>" "<full_new_content>"
   ```
   Newlines in content are preserved (converted to div / br in ENML).

**Never** call `update-by-title` without first reading the note. You would
destroy existing content.

## Append (add to end only)

If the user just wants to add text at the bottom with no structured edit:
```
mamba run -n socrates python -m projects.evernote.src.evernote_api append-by-title "<title>" "<text>"
```
This reads, appends, and writes back in one call. Use for log entries,
notes, or anything where order does not matter.

## Read a note

```
mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title "<title>"
```

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
mamba run -n socrates python -m projects.evernote.src.evernote_api get <guid>
mamba run -n socrates python -m projects.evernote.src.evernote_api update <guid> <content>
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
