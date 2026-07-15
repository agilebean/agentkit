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

## Reading notes

Three read modes with different token costs and fidelity:

| Mode | Flag | Token reduction | When to use |
|------|------|----------------|-------------|
| Raw ENML | `--raw` | baseline (~406 tokens for 3-row table) | Pixel-perfect edits on complex notes |
| Clean HTML | `--clean` | 54% less (~185 tokens) | Need exact structure (tables, links) without conversion risk |
| Markdown | `--markdown` | 74% less (~104 tokens) | Most reads, understanding content, search snippets |

`--raw`, `--markdown`, and `--clean` are mutually exclusive. Passing two or more exits with error 1.

```
mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title --markdown "<title>"
mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title --clean "<title>"
mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title --raw "<title>"
```

## Write modes (update, update-by-title, create)

`--markdown` and `--clean` flags are available on `update`, `update-by-title`, and
`create`. When writing with `--markdown`, the input is GitHub-flavored markdown
converted to ENML. With `--clean`, the input is clean HTML wrapped in `<en-note>`.

```
mamba run -n socrates python -m projects.evernote.src.evernote_api create --markdown "<title>" "<markdown_content>"
mamba run -n socrates python -m projects.evernote.src.evernote_api update-by-title --markdown "<title>" "<markdown_content>"
```

Full read-modify-write with `--raw` (preserved for backward compat):

1. **Read** the raw ENML:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api get-by-title --raw "<title>"
   ```
2. **Modify** the ENML in memory. Validate table structure (matching `<tr>`/`</tr>` counts).
3. **Write back**:
   ```
   mamba run -n socrates python -m projects.evernote.src.evernote_api update-by-title --raw "<title>" "<full_enml>"
   ```
4. **Verify** by re-reading.

## Surgical update commands (delta only, no read needed)

These commands modify ENML server-side so the LLM sends only the delta.
Token cost is ~94% less than full round-trip.

| Command | What it does | Token cost |
|---------|-------------|------------|
| `add-row` | Add a row to the Nth table | ~26 tokens |
| `update-cell` | Update a single cell at (row, col) | ~20 tokens |
| `insert-after-heading` | Insert text after a heading | ~40 tokens |
| `replace-section` | Replace content between headings | ~100 tokens |

```
mamba run -n socrates python -m projects.evernote.src.evernote_api add-row "<title>" "date,value,notes" [--table N]
mamba run -n socrates python -m projects.evernote.src.evernote_api update-cell "<title>" <row> <col> "<value>" [--table N]
mamba run -n socrates python -m projects.evernote.src.evernote_api insert-after-heading "<title>" "<heading>" "<text>" [--markdown] [--batch]
mamba run -n socrates python -m projects.evernote.src.evernote_api replace-section "<title>" "<from_heading>" "<content>" [--to-heading "<heading>"] [--markdown]
```

`insert-after-heading` supports `--batch`: the title argument is a comma-separated list of note titles. Applies the same insertion to all notes.

`add-row` supports `--photo <file>` and `--photo-col <N>`: uploads an image file as an Evernote resource and embeds it in the specified column. If `--photo-col` is omitted, the last column is used.

```
mamba run -n socrates python -m projects.evernote.src.evernote_api add-row "<title>" "date,$1500,photo" --photo /path/to/receipt.jpg --photo-col 2
```

## Append (add to end)

**WARNING: Plain append (no flag) flattens ALL structure to plain text and DESTROYS tables, links, and formatting. Never use plain append on structured notes.**

Use `--raw` or `--markdown` to preserve structure:

```
mamba run -n socrates python -m projects.evernote.src.evernote_api append-by-title --raw "<title>" "<enml_fragment>"
mamba run -n socrates python -m projects.evernote.src.evernote_api append-by-title --markdown "<title>" "<markdown_content>"
```

## Image embedding

Embed images from files or directly from macOS Photos:

```
mamba run -n socrates python -m projects.evernote.src.evernote_api embed-image "<title>" /path/to/image.jpg [--after-heading "<heading>"]
mamba run -n socrates python -m projects.evernote.src.evernote_api photos-embed "<title>" [--count N] [--after-heading "<heading>"]
```

## Log entry (heading + fields + optional photo)

```
mamba run -n socrates python -m projects.evernote.src.evernote_api log-entry "<title>" "<heading>" --fields "key1=val1,key2=val2" [--photo] [--after-heading "<heading>"]
```

## Table creation

```
mamba run -n socrates python -m projects.evernote.src.evernote_api create-table "<title>" --headers "Col1,Col2" --rows "a,b;c,d" [--after-heading "<heading>"]
```

## Cross-reference links between notes

```
mamba run -n socrates python -m projects.evernote.src.evernote_api link-note "<source_title>" "<target_title>" [--after-heading "<heading>"]
```

## Memory sync

Sync local `memory/*.md` files with Evernote notes:

```
mamba run -n socrates python -m projects.evernote.src.evernote_api sync-memory --from-evernote [--topics health,finance]
mamba run -n socrates python -m projects.evernote.src.evernote_api sync-memory --to-evernote [--topics health,finance]
```

The memory file → Evernote note title mapping is in `projects/evernote/src/memory_map.py`.

## Search with content snippets

```
mamba run -n socrates python -m projects.evernote.src.evernote_api search "<query>" --content [--markdown] [--max N]
```

Returns title, guid, and a text snippet with the search term in context.

## Token cost comparison

| Mode | Operation | ~Tokens (3-row table note) |
|------|-----------|---------------------------|
| `--raw` read | get-by-title --raw | ~406 |
| `--clean` read | get-by-title --clean | ~185 |
| `--markdown` read | get-by-title --markdown | ~104 |
| surgical add-row | add-row --title X --row "a,b,c" | ~26 |
| surgical update-cell | update-cell --title X 0 0 "val" | ~20 |
| `--markdown` write | update-by-title --markdown X "md" | ~104 |
| `--clean` write | update-by-title --clean X "html" | ~185 |

## Append (add to end)

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
mamba run -n socrates python -m projects.evernote.src.evernote_api search <query> [--notebook <name>] [--max <n>] [--content] [--markdown]
mamba run -n socrates python -m projects.evernote.src.evernote_api get <guid> [--raw] [--markdown] [--clean]
mamba run -n socrates python -m projects.evernote.src.evernote_api update <guid> <content> [--raw] [--markdown] [--clean]
mamba run -n socrates python -m projects.evernote.src.evernote_api append <guid> <text> [--raw] [--markdown]
mamba run -n socrates python -m projects.evernote.src.evernote_api create <title> <content> [--notebook <name>] [--markdown] [--clean]
mamba run -n socrates python -m projects.evernote.src.evernote_api add-row <title> <row> [--table N] [--photo <file>] [--photo-col N]
mamba run -n socrates python -m projects.evernote.src.evernote_api update-cell <title> <row> <col> <value> [--table N]
mamba run -n socrates python -m projects.evernote.src.evernote_api insert-after-heading <title> <heading> <text> [--markdown] [--batch]
mamba run -n socrates python -m projects.evernote.src.evernote_api replace-section <title> <from_heading> <content> [--to-heading <heading>] [--markdown]
mamba run -n socrates python -m projects.evernote.src.evernote_api create-table <title> --headers "A,B" --rows "1,2;3,4" [--after-heading <heading>]
mamba run -n socrates python -m projects.evernote.src.evernote_api link-note <source_title> <target_title> [--after-heading <heading>]
mamba run -n socrates python -m projects.evernote.src.evernote_api embed-image <title> <file> [--after-heading <heading>]
mamba run -n socrates python -m projects.evernote.src.evernote_api photos-embed <title> [--count N] [--after-heading <heading>]
mamba run -n socrates python -m projects.evernote.src.evernote_api log-entry <title> <heading> --fields "k=v" [--photo] [--after-heading <heading>]
mamba run -n socrates python -m projects.evernote.src.evernote_api sync-memory --from-evernote|--to-evernote [--topics a,b]
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
