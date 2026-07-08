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

## Primary flow (by title — use these)

```
# Find a note by exact title
mamba run -n socrates python -m projects.evernote.src.evernote_api find-note "<title>"

# Read a note
mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title "<title>"

# Update a note (replaces content)
mamba run -n socrates python -m projects.evernote.src.evernote_api update-by-title "<title>" "<new_content>"

# Append to a note
mamba run -n socrates python -m projects.evernote.src.evernote_api append-by-title "<title>" "<text>"
```

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
- 5: ambiguous title (multiple matches or partial matches — stdout lists candidates)
- 6: title not found (search returned nothing)

## Disambiguation

If find-note or get-by-title exits 5, read the candidate list from stdout,
present it to the user, and ask which note to use. Then use the guid from
the selected candidate with the by-guid commands.
