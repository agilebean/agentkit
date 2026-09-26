---
name: evernote
description: Read, update, create, delete, or search Evernote notes by title via the evernote_api Thrift CLI. Use when told to read, update, append, create, delete, or search Evernote notes. Calls shell commands; do NOT import evernote_api in-process.
---

# Evernote CLI

All commands run from the socrates repo root via the `socrates` mamba env.

Run prefix: `mamba run -n socrates python -m projects.evernote.src.evernote_api`

## Which path to use

The **Evernote MCP server is the only path.** It is configured in `~/.config/opencode/opencode.jsonc` under `mcp.evernote` (`type: remote`, `url: https://mcp.evernote.com/mcp`); opencode itself is the MCP client, and the tools reach the session's catalog as `tools.evernote.*` (27 tools: `search_notes`, `get_note`, `edit_note`, `create_note`, `delete_note`, attachments and tags). Use them through `execute` only. The shell CLI is not a fallback — Chaehan, 2026-09-26: "you never use the cli fallback that is too slow."

**When the tools are absent, it is a connection-state problem, not auth.** Read the opencode log (`~/.local/share/opencode/log/opencode.log`); never run the `opencode` CLI to diagnose it (it blocks while it starts or attaches to the service). The evernote MCP connects once per project directory when the service starts; if that first connect fails — on 2026-09-26 the Surfshark VPN blackholed `mcp.evernote.com` and the log showed `mcp connect failed ... ConnectionRefused` at 10:31 — that directory stays without the tools for the life of the service while others reconnect. Read `mcp connect failed` / `mcp connected ... directory=<dir>` for the session's directory. Fix: restart the service (the fresh connect at 12:57:25 restored all 27 tools the same day); with a VPN in play, turn it off first. Re-check availability with `search({ query: "evernote", namespace: "evernote" })`. While it is down, report the outage instead of writing through the CLI.

The shell CLI below is the fallback, and the only path outside an opencode session.

**Batch MCP work into one visible call.** Fetch the note once inside a single `execute` call, apply every edit in that same call (await them in a loop), and read the note back once at the end for the report. Never read-modify-verify per edit: each MCP call is a remote round trip, and on 2026-09-25 thirteen edits became twenty calls while Chaehan watched it hang ("is that absolutely necessary? if yes, timeout early!!!!!"). One call for the changes, one for the verification; the execute runtime has no timers, so the only lever is fewer calls.

**Verify every write by re-reading, on both paths.** A write can report success and not persist. Observed 2026-09-25 on the note "2026-09-11 KUBS DT Course Design - Sprint and JTBD": `replace-section` and `insert-after-heading` returned `updated: true` six times in a row while a by-guid read kept returning byte-identical content, and a scratch note in the same notebook accepted a write in the same minute. After any `update-by-title`, `replace-section`, `insert-after-heading` or `update`, read the note back by guid and confirm the new text is in it; if it is not, report that instead of reporting the note as updated.

## Prerequisites

Token saved at `~/.local/share/socrates/evernote_token` (chmod 600).
Extract: Chrome DevTools > Application > Cookies > www.evernote.com > clipper-sso.
Alternatively: set `EVERNOTE_TOKEN` env var.

## Note structure rules

- Any graphic (chart, screenshot, image) must be placed at the very top of the note, ABOVE the TL;DR section. Never embed graphics below the TL;DR, at the bottom, or in the middle of a note.
- Order: graphic first, then TL;DR, then the body sections.
- The TL;DR is an H2 heading (`## TL;DR`), never plain text or a bolded line. Its text follows on the next line(s).
- Titles carry the date as the bare first word: `2026-08-16 Top Supplements`, never `Top Supplements (2026-08-16)`. Canonical rule: RULES.md rule 20.
- The body is written the way you would say it to Chaehan in chat, not as a reference entry: no label prefixes ("Status:", "Why:"), no telegraphic fragments, no analyst third person. Canonical rule: RULES.md rule 19.

## Notebook placement

Every note must be created in its topic's notebook, never the default.

| Topic | Notebook |
|-------|----------|
| Health | Health |
| Swimming | Swimming |
| Personal | Chaehan |

- Pass `--notebook <name>` to `create` with the exact notebook name.
- For topics not in the table, pick the obviously matching existing notebook (finance → "Chaehan Financials", travel → the current year's travel notebook). If none matches, ask.
- The CLI has no move command and `update` cannot change a note's notebook. To move a note, set `notebookGuid` directly via the thrift client.
- Exact-title search (`find-note`, `get-by-title`) fails on titles containing parentheses; Evernote parses them as search operators. Use a partial query or the guid.

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

## Creating or reworking a note: sweep superseded copies first (RULES.md rule 31)

Before a `create`, search the target notebook for the topic
(`search "<title stem>" --notebook "<notebook>"`) and resolve what the new
note supersedes: fold any unique content into the new note, then delete
the superseded note. The same sweep runs when an existing artifact is
reworked, renamed, or declared superseded. The sweep is automatic; ask
the user only when the content cannot tell you which note is canonical.

Delete moves a note to the trash (recoverable); `--permanent` expunges —
only when the user says so:

```
mamba run -n socrates python -m projects.evernote.src.evernote_api delete "<title>"
mamba run -n socrates python -m projects.evernote.src.evernote_api delete "<guid>" --guid
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

## Embedded graphics do not survive a full-body replacement

A full-body write (`--markdown`, `--clean`, or `--raw`) replaces the whole note
body, and the conversion cannot upload a local image path. The rewrite also does
not carry the note's existing resources, so every embedded image must be
re-uploaded in the same operation or it is lost.

- A markdown line such as `![Course overview, week grid v6](<Diagram evolution/week grid v6.png>)`
  becomes `<img src="Diagram%20evolution/...png">`: a path Evernote cannot
  resolve. The note's embedded resource is gone and the reader sees a broken
  image. An `evernote:` image URI in the input fails the same way.
- Symptom to check for after any body replacement: raw content containing
  `<img src="...">` instead of `<en-media type="image/png" hash="..."/>`.

Procedure when the note carries (or should carry) a graphic:

1. Before the write, read the note with resources and record each hash
   (`projects/evernote/src`, `thrift_client.make_user_store` /
   `resolve_note_store_url` / `make_note_store`, then
   `getNote(token, guid, True, True, False, False)`).
2. Do the body replacement.
3. Re-upload each image:
   `embed-image "<title>" "<file>" --after-heading "<heading the graphic sat under>"`
   or `--top` when it sits above everything. The returned hash must equal the
   hash recorded in step 1; a different hash means the wrong file.
4. Verify: the raw content holds one `<en-media>` per graphic with the recorded
   hash and no relative-path `<img>` tag.

Risk set: notes whose markdown twin references images by path. In KUBS DT those
are the course design overview (week grid at the top), the opener story (the BigP
retrospective photo) and the diagram evolution document.

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
mamba run -n socrates python -m projects.evernote.src.evernote_api embed-image "<title>" /path/to/image.jpg [--top | --after-heading "<heading>"]
mamba run -n socrates python -m projects.evernote.src.evernote_api photos-embed "<title>" [--count N] [--after-heading "<heading>"]
```

Re-embedding the same file reuses the existing attachment (same-hash check),
so re-runs do not duplicate resources.

**Full-content writes drop embedded images.** `create`, `update`, and
`update-by-title` replace the note together with its resource list, so
after such a write the note has no images; a markdown local-path
reference is left as a broken `<img>` element. Re-embed the note's images
in the same turn; when the source markdown points at local files, strip
those image lines before the write, then embed the files with `--top` or
`--after-heading`.

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
mamba run -n socrates python -m projects.evernote.src.evernote_api delete <title> [--guid] [--permanent]
mamba run -n socrates python -m projects.evernote.src.evernote_api close-note "<title>"
```

## Output

All output is JSON to stdout. Errors to stderr. Exit codes:
- 0: success
- 2: auth error (token invalid/expired)
- 3: permission denied
- 4: network error or retries exhausted
- 5: ambiguous title (multiple matches or partial matches, stdout lists candidates)
- 6: title not found (search returned nothing)

## Note lock recovery (RTE room)

Write commands auto-release the "RTE room" lock (exit 4, stderr contains
"locked"). The lock exists only while Evernote has the note in an active
edit session (the note open in a tab with the editor used). Clicking
another note in the sidebar switches the tab away from the locked note,
and the lock then releases on Evernote's own timing, observed at 15s in
one live run and ~59s in another. View > Reload does NOT speed this up.
The CLI clicks, verifies via AX that the tab actually switched (clicking
further down the list if not), then retries the write every 20s for up to
~2 minutes before giving up. Tabs are never closed.

The helper activates Evernote (brings it to the front) before clicking,
and only runs when Evernote's window is on the current macOS Space. The
first sidebar row is usually the locked note itself (most recently updated
sorts to the top), so the helper clicks further down too.

If a write still exits 4 with the lock message:

1. Run `close-note "<title>"`. It returns `{"closed": true, ...}` on
   success or `{"closed": false, "error": "..."}` on failure.
2. If closed, wait about a minute, then retry the original write once.
   If the result includes `"switched": false`, the tab still shows the
   locked note (the sidebar list likely holds only that note); ask the
   user to switch the note themselves.
3. If the close returns `{"closed": false, "error": "evernote window not
   visible on current Space"}`, Evernote's window is on another macOS
   Space. Ask the user to click the Evernote Dock icon so the window is
   visible, then retry the close once.
4. If the close returns a release-helper error, the helper failed to build
   or run. Report the error; do not retry in a loop.

Do not retry a locked write more than twice in total. Never close the
user's note tabs yourself; the click mechanism already avoids this.

## Disambiguation

If find-note or get-by-title exits 5, read the candidate list from stdout,
present it to the user, and ask which note to use. Then use the guid from
the selected candidate with the by-guid commands.
