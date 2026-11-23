# Evernote troubleshooting

Missing MCP tools, a locked note, and a table cell whose markup a write destroyed (`SKILL.md`, "Reference files").

## The Evernote MCP tools are absent

**When the tools are absent, it is a connection-state problem, not auth.** Read the opencode log (`~/.local/share/opencode/log/opencode.log`); never run the `opencode` CLI to diagnose it (it blocks while it starts or attaches to the service). The evernote MCP connects when the service loads a project's location, and the service evicts and re-boots locations constantly (780 boots in the log by 2026-10-12), so each project reconnects many times a day. A connect that fails at that moment, with the Surfshark VPN blackholing `mcp.evernote.com` (2026-09-26, `ConnectionRefused` at 10:31) or the resolver mid-transition (2026-10-12 06:03, `getaddrinfo ENOTFOUND`), leaves that one directory `failed` for the life of the location while its neighbours reconnect. Read the log for the session's own directory with `rg 'mcp connect failed|mcp connected' ~/.local/share/opencode/log/opencode.log`; never run the `opencode` CLI to diagnose it (it blocks while it starts or attaches to the service). **Fix it yourself through the service's own API; do not restart the app, do not report the outage while a lever is untried.** The local OpenCode server manages MCP servers over HTTP: `GET /api/mcp?location[directory]=<dir>` gives every server's status (`connected`, `failed` with its error, `needs authentication`, `disabled`), and `POST /api/experimental/mcp/{server}/connect?location[directory]=<dir>` reconnects one. Both take the server's basic-auth password, and the session environment already carries it:

```
PORT=$(python3 -c "import json,glob;print(json.load(open(glob.glob('$HOME/.config/openchamber/managed-opencode/*.json')[0]))['port'])")
curl -s -u "opencode:$OPENCODE_PASSWORD" --get --data-urlencode "location[directory]=<the session's directory>" "http://127.0.0.1:$PORT/api/mcp"
curl -s -u "opencode:$OPENCODE_PASSWORD" -X POST --get --data-urlencode "location[directory]=<the session's directory>" "http://127.0.0.1:$PORT/api/experimental/mcp/evernote/connect"
```

Verified 2026-10-12: socrates read `failed` (`getaddrinfo ENOTFOUND mcp.evernote.com` from 06:03 that morning, sticky for the life of the location) while the same server read `connected` for another directory; one POST moved it to `connected` and the 27 tools appeared in the running session's catalog with no restart. Fixing it this way costs seconds. Restarting OpenChamber costs the user his sessions, so keep that for a service that is genuinely wedged. Re-check availability with `search({ query: "evernote", namespace: "evernote" })`. Report the outage only if the reconnect fails twice as well, and then name the failure class (DNS, connect timeout, socket reset).

A failed connect now heals on its own. The plugin `agentkit/plugins/mcp-reconnect` watches the MCP status of every location and forces a fresh connection attempt for a server sitting in `failed`, with a doubling backoff of 1 s to 30 s for the first ten attempts and a 5 minute ceiling after that; a server that is deliberately disconnected reads `disabled` and is left alone. It is registered in `~/.config/opencode/opencode.jsonc` under `plugins`, verified live on 2026-10-12 (a broken server read `failed`, was retried, and connected within seconds of its target becoming reachable). So when a tool is missing, check the status first and wait a moment before reaching for the manual call: the plugin may already be on it. Its predecessor, a V1 plugin at `~/.config/openchamber/mcp-reconnect/`, never ran (V1 plugin functions do not execute on opencode V2) and has been removed.

## Cell edits must preserve the cell's markup; recover lost markup from note history

Replacing a table cell's inner content with a rebuilt plain string destroys
everything the cell's ENML carries beyond its words: richlinks to other notes
(`<a type="inline-richlink" href="evernote:///…">`, share links), stacked
`<div>` lines, coloured `<span>` runs, right-aligned number divs. A text read
cannot see any of it — the stripped text looks the same before and after the
loss — so it surfaces only when the user opens the note, and by then the
markup is gone.

- A label the cell already carries keeps its place: append the value after it,
  never before. A cell reading `400m 2:05/2:04 DPS` is finished as
  `400m 2:05/2:04 DPS 0.99/0.97`, not `400m 2:05/2:04 0.99/0.97 DPS` —
  inserting text ahead of the token reinterprets it as a trailing unit and
  rewrites wording the user typed. The row being edited is the authority on
  the order; the note's older rows are not (2026-10-13, "Swim Training Times":
  "no i wanted the DPS before the values!"; rule 157, agent/failures.md failure 46).
- Before changing a cell, fetch the raw ENML (`get_note`) and treat the
  existing inner markup as part of the content: substitute only the specific
  words and numbers that were approved, keeping every tag around them.
- When markup was already flattened, recover it from note history — Evernote
  keeps per-sync versions (2026-10-04: 186 of them on "2026 Travel Itinerary
  €20274"): `listNoteVersions(token, guid)`, pick the newest version from
  before the loss, `getNoteVersion(token, guid, usn, False, False, False)`
  via `projects/evernote/src/thrift_client.py`, transplant the cell's raw
  inner, re-apply the approved text changes inside it, then write with the
  MCP `edit_note` (surgical, keeps the note's resources).
- Verify by markup markers (`href` fragments, `style=` runs), never by the
  stripped text: the text check passes on both the rich and the flattened cell.

Failure it prevents: on 2026-10-04 the Seoul row's details cell was rebuilt
as plain text during a cost edit; four note links and the line and colour
formatting vanished, and only the version history could bring them back.

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
