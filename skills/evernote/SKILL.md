---
name: evernote
description: Read, update, create, delete, or search Evernote notes by title via the evernote_api Thrift CLI. Use when told to read, update, append, create, delete, or search Evernote notes. Calls shell commands; do NOT import evernote_api in-process.
---

# Evernote CLI

All commands run from the socrates repo root via the `socrates` mamba env.

Run prefix: `mamba run -n socrates python -m projects.evernote.src.evernote_api`

## Which path to use

The **Evernote MCP server is the only path.** It is configured in `~/.config/opencode/opencode.jsonc` under `mcp.evernote` (`type: remote`, `url: https://mcp.evernote.com/mcp`); opencode itself is the MCP client, and the tools reach the session's catalog as `tools.evernote.*` (27 tools: `search_notes`, `get_note`, `edit_note`, `create_note`, `delete_note`, attachments and tags). Use them through `execute` only. The shell CLI is not a fallback — the user, 2026-09-26: "you never use the cli fallback that is too slow."

**When the tools are absent, it is a connection-state problem, not auth.** Read the opencode log (`~/.local/share/opencode/log/opencode.log`); never run the `opencode` CLI to diagnose it (it blocks while it starts or attaches to the service). The evernote MCP connects when the service loads a project's location, and the service evicts and re-boots locations constantly (780 boots in the log by 2026-10-12), so each project reconnects many times a day. A connect that fails at that moment, with the Surfshark VPN blackholing `mcp.evernote.com` (2026-09-26, `ConnectionRefused` at 10:31) or the resolver mid-transition (2026-10-12 06:03, `getaddrinfo ENOTFOUND`), leaves that one directory `failed` for the life of the location while its neighbours reconnect. Read the log for the session's own directory with `rg 'mcp connect failed|mcp connected' ~/.local/share/opencode/log/opencode.log`; never run the `opencode` CLI to diagnose it (it blocks while it starts or attaches to the service). **Fix it yourself through the service's own API; do not restart the app, do not report the outage while a lever is untried.** The local OpenCode server manages MCP servers over HTTP: `GET /api/mcp?location[directory]=<dir>` gives every server's status (`connected`, `failed` with its error, `needs authentication`, `disabled`), and `POST /api/experimental/mcp/{server}/connect?location[directory]=<dir>` reconnects one. Both take the server's basic-auth password, and the session environment already carries it:

```
PORT=$(python3 -c "import json,glob;print(json.load(open(glob.glob('$HOME/.config/openchamber/managed-opencode/*.json')[0]))['port'])")
curl -s -u "opencode:$OPENCODE_PASSWORD" --get --data-urlencode "location[directory]=<the session's directory>" "http://127.0.0.1:$PORT/api/mcp"
curl -s -u "opencode:$OPENCODE_PASSWORD" -X POST --get --data-urlencode "location[directory]=<the session's directory>" "http://127.0.0.1:$PORT/api/experimental/mcp/evernote/connect"
```

Verified 2026-10-12: socrates read `failed` (`getaddrinfo ENOTFOUND mcp.evernote.com` from 06:03 that morning, sticky for the life of the location) while the same server read `connected` for another directory; one POST moved it to `connected` and the 27 tools appeared in the running session's catalog with no restart. Fixing it this way costs seconds. Restarting OpenChamber costs the user his sessions, so keep that for a service that is genuinely wedged. Re-check availability with `search({ query: "evernote", namespace: "evernote" })`. Report the outage only if the reconnect fails twice as well, and then name the failure class (DNS, connect timeout, socket reset).

A failed connect now heals on its own. The plugin `agentkit/plugins/mcp-reconnect` watches the MCP status of every location and forces a fresh connection attempt for a server sitting in `failed`, with a doubling backoff of 1 s to 30 s for the first ten attempts and a 5 minute ceiling after that; a server that is deliberately disconnected reads `disabled` and is left alone. It is registered in `~/.config/opencode/opencode.jsonc` under `plugins`, verified live on 2026-10-12 (a broken server read `failed`, was retried, and connected within seconds of its target becoming reachable). So when a tool is missing, check the status first and wait a moment before reaching for the manual call: the plugin may already be on it. Its predecessor, a V1 plugin at `~/.config/openchamber/mcp-reconnect/`, never ran (V1 plugin functions do not execute on opencode V2) and has been removed.

The agent never runs the shell CLI below for Evernote work, inside an opencode session or outside one. Chaehan, 2026-11-07: "only use the evernote mcp not cli! the cli is buggy". Outside opencode (a Claude Code session), the MCP is reached through an opencode run in the socrates folder, as `note_test.py` and the hanji skill's `hanji_test.py` launch it. The commands below stay as the engine `note_build.py` calls and as its reference. A whole-body write through MCP carries the `// note-gate:<sha>` line from the note gate's PASS, or the note-gate plugin refuses it ("Writing or rewriting a note's text").

**Batch MCP work into one visible call.** Fetch the note once inside a single `execute` call, apply every edit in that same call (await them in a loop), and read the note back once at the end for the report. Never read-modify-verify per edit: each MCP call is a remote round trip, and on 2026-09-25 thirteen edits became twenty calls while the user watched it hang ("is that absolutely necessary? if yes, timeout early!!!!!"). One call for the changes, one for the verification; the execute runtime has no timers, so the only lever is fewer calls.

**Verify every write by re-reading, on both paths.** A write can report success and not persist. Observed 2026-09-25 on the note "2026-09-11 KUBS DT Course Design - Sprint and JTBD": `replace-section` and `insert-after-heading` returned `updated: true` six times in a row while a by-guid read kept returning byte-identical content, and a scratch note in the same notebook accepted a write in the same minute. After any `update-by-title`, `replace-section`, `insert-after-heading` or `update`, read the note back by guid and confirm the new text is in it; if it is not, report that instead of reporting the note as updated.

**For its first minute or two, a new note is reached by its guid.** Keep the guid `create_note` returns and read the note by it. On 2026-11-07 three title searches (`intitle:"<title>"`, the bare words, the quoted title) returned 0 hits right after `create_note`, while `notebook:"Computer"` listed the note first; the same title search found it two minutes later in 353 ms. A trash likewise shows only in `get_note` (`active: false` and its `deleted` time): `intrash:true` listed the trashed note once, and a minute later listed nothing.

**Verify the whole skeleton, not only the edited cell.** Before the write, record the note's headings, table count and length; after it, read the note back and confirm each heading and table is still there. A cell-level read proves the cell and says nothing about a section the write did not intend to touch. On 2026-10-26 the 2026-10-25 row verified clean while the Training Plan table had vanished and the note had dropped from 18465 to 11057 characters.

A note open in the app (the thrift update answers `RTE room has already been open`) is a lock: "Note lock recovery (RTE room)" below releases it. When the note's text changed since you read it, or the version list shows a version the agent did not write, a second writer is present. Stop the pass: read the current content, restore any missing section from the last version that had it (`listNoteVersions` then `getNoteVersion`, both on the note store), verify the skeleton again, and report the second writer. Never write over it.

## Prerequisites

Token saved at `~/.local/share/socrates/evernote_token` (chmod 600).
Extract: Chrome DevTools > Application > Cookies > www.evernote.com > clipper-sso.
Alternatively: set `EVERNOTE_TOKEN` env var.

## Note structure rules

- Any graphic (chart, screenshot, image) must be placed at the very top of the note, ABOVE the Takeaway section. Never embed graphics below the Takeaway, at the bottom, or in the middle of a note. **A graphic's home is the note's own layout, not the position its line happens to hold in the markdown twin.** When a note is fed from a markdown document, the document's image lines sit where the note's graphics go — the two read in the same order — because a markdown write turns each image line into an `<img>` tag at that spot and a recovery re-embeds the resource "after the heading the graphic sat under" (the nearest one, which can be a body heading three sections below the graphic's place). 2026-10-13, "2026-09-11 KUBS DT Course Design": the JTBD integration diagram's markdown line sat at the end of the Reading section, the note consequently carried the diagram under the "Reading" heading — below the Takeaway — and the note's own line "the conceptual diagram above marks the added tools" pointed at nothing. Chaehan: "missing the image above 'One process, two perspectives, three sprints.' ... find and put it back in". The diagram moved to the top, directly above the tagline (raw offset 288, after the course chart at 74), and the markdown line moved to line 5; both images are verified on the raw read (one `<en-media>` per graphic with its recorded hash, no `<img>`).
- Order: graphic first, then the body sections. A Takeaway is added only for a meeting summary or an analysis of the user's results — for those, it sits after the graphic. **A note made from a receipt or confirmation has no Takeaway at all** (stated 2026-10-07): it opens with the card image and states the facts, and nothing restates them above. The same note-making workflow is in the `receipt-note` skill.
- The Takeaway is an H2 heading (`## Takeaway`), never plain text or a bolded line. Its text follows on the next line(s).
- Titles carry the date as the bare first word: `2026-08-16 Top Supplements`, never `Top Supplements (2026-08-16)`. Canonical rule: RULES.md rule 20.
- **Every note about a booking is a bulleted hierarchy, not prose.** Flight and hotel details go into bullet points, with the sub-facts indented under their parent so the shape of the record is visible at a glance: the entity, then its dates, its price, its references as sub-bullets. Stated 2026-10-07: "just put all the info for flights and hotel into bullet points and tab them to see the hierarchy". A paragraph that runs the same facts together hides the hierarchy and is the wrong shape.
- **Options with attributes become a table below the bullets.** When a note compares named options — restaurants, hotels, vendors, pools — the bullets above the table carry the rules of the search and the finding as sentences, the table carries the comparable fields (distance, rating, hours, price, and a Verdict column saying why the row is in the list), and one bullet below the table carries the rejected names, each with the reason it was dropped. A nested bullet blob of attributes is not readable: the reader cannot scan a column. Stated 2026-10-07 on the Kobe beef picks: "the info is horribly formatted! you must understand this is not humanly readable ... for info structured like restaurants make a table below the bullet points". Canonical rule: RULES.md rule 67. ENML to copy: `<table width="Npx" style="border-collapse:collapse;width:Npx;">` with a `<colgroup>`, and every `<th>`/`<td>` styled `border-color:#d4d4d4;border-width:1.5px;border-style:solid;padding:10px;` with its content wrapped in `<div>`; N is the table's own width, from the rule below.
- **A table is as wide as its content needs, and never stretched to the pane.** Every table leaves with an explicit width and a colgroup. `projects/evernote/src/enml.py`'s `fit_table_widths` computes it on every markdown write; `fit-tables "<title>"` applies it to a note already written and `--refit` replaces a fitting that was wrong. The model: a column's natural width is its longest line (headers counted, bold counted at 1.06) at 16 px plus 24 px of padding and air, so that a header cannot break mid-word; where the columns' sum fits under the ceiling they are used as they are, and where it does not they are compressed together, each column's width following its content raised to 0.75 and never dropping below its longest word. Then the wrapping column gives its width back: it is trimmed to the point where its content stops saving the table a line, so the table ends narrower than the ceiling. Width past that point buys nothing - a second or third line in a column costs nothing when a neighbouring column already carries three (rule 149) - and a table with four columns does not reach the width a six-column one needs. The ceiling is **939 px**, the widest table of his own in the account (his hand-dragged Osaka table at 937/938.88, a 939 px table of 2025-02-26, the client's own fits at 923, 817, 774, 700, 632, 623). The 1108.64 px of 2026-10-09 was the agent's own output measured back: every 1108-1128 px table in the account is agent-written, and a table that wide runs past his pane. A table whose columns all carry the same width is a default, not a layout, and is refitted; a table whose columns differ is his own (he drags borders and the client writes fractional widths such as 938.88) and is left alone. Stated 2026-10-12, three times: "i said to optimize the vertical space, but that doesn't mean by extend all tables to max. width"; of the first fitting, which cut the widest column until the total fit: "you broke 'Mandatory, 10% of the grade; more than 30% of sessions missed = F' across 5 rows!!" and a header broken after "Hour"; and of the second, which filled the S6 table to the ceiling: "can't you apply common sense? it doesn't matter if there is a second or third line if another column already has 3 lines!!!! ... keep 130 but shorten the text line bec the goal is not to use max width with so few cols!" The reference is his hand-dragged Osaka table (938.88: 188/116/79/132/85/339); the anti-shape is the same table at 1128 px with six equal 188 px columns.
- **Every place name is a link to Google Maps.** Restaurants, bars and hotels carry a Google Maps link on the name itself, wherever the name appears in the note — not only in a links section at the foot: `<a href="https://maps.google.com/?q=<url-encoded name>">name</a>`. The Japanese name is what resolves in Maps, so it travels in the query while the English name stays as the visible text. Stated 2026-10-07: "always link the location names (restaurants, bars, hotels) with the google maps link".
- **A sub-list is written after its parent item, the form Evernote's own editor writes.** `markdown_to_enml` writes a child list as `<li>parent</li><ul>child</ul>`; written inside its parent item (`<li>parent<ul>child</ul></li>`) the app draws it as an ordinary bullet at the parent's level. On 2026-11-08 the Osaka trip note showed flat sub-bullets while every read-back through our converter showed them nested (failure 192), so a verify of list rendering never rests on the converter alone.
- The body is written the way you would say it to the user in chat, not as a reference entry: no label prefixes ("Status:", "Why:"), no telegraphic fragments, no analyst third person. Canonical rule: RULES.md rule 19.
- **A title names its subject in neutral words.** It reads as something Chaehan could show anyone: "2026-11-05 Semen: nutritional intake, taste, consistency and production", never "what she gets". A title names the subject by a category noun, never by a person or by what someone does or receives; the same holds for the twin's file name. Run `wording_lint.py --title "<title>" <file>` before create or rename: it flags a pronoun or an explicit word. The body can stay precise. The same holds for a heading and a summary line: an intimate or red-light matter stays inside its section under a neutral heading such as "Nightlife" and never reaches the summary (Chaehan, 2026-11-08: "you bring embarrasing hints to the redlight with the paid night which not appear in the summary, and the section was better named as Nightlife").
- **Every note is written in the life overview's style.** Its section "3. Write the snapshot" in `agentkit/skills/life-overview/SKILL.md` (Moves 1 to 3 and the accepted and rejected lines) is the writing standard for any note Chaehan reads; only the Takeaway's life order, the Life Challenges link and the overview's gate belong to the overview alone. Chaehan, 2026-11-09: "you should have inferred that the writing style of life overview should be used as general style".
- **A note keeps only the relevant points, and the overlaps go first.** Chaehan, 2026-11-09: "only relevant points not clutter (more of the same) or unnecessary detail (obscuring the point). most important cut the overlaps". The cuts run in that order: a fact said twice, a second fact that says more of the same, then detail that obscures the point. note_build's step 4 lists the overlapping pairs and has each one judged and cut. Chaehan's facts that no point needs stay in the memory record or the linked note; a booking keeps its own dates, price and references.
- **Before adding a table or section, read the note's existing structure for the slot.** A plan already has a warmup column and a cooldown column: the drills go in the warmup cell, the scull in the cooldown cell, and no second table is created. A label that no longer names the function is renamed to the function, never bypassed with a new section.

## Writing or rewriting a note's text: run note_build.py

A request to reorder a note is not a rewrite: move its sections and items as they stand, change only the words Chaehan named, and never rebuild it with note_build, whose step 3 writes a new summary and new headings (RULES.md, "Never change the gist of a structure").

Every note whose prose is written or rewritten is built with `~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py`, whatever the topic and however short. Do not draft the note yourself, unless Chaehan asked you to write it: then the section "A text you wrote, from Claude Code" below applies. A rewrite done as a run of find-and-replace edits, a section at a time, is still a rewrite: the note-gate plugin refuses any edit whose code carries more than 200 characters of text outside a table without the gate's marker, so a correction of more than one sentence goes through note_build. The write keeps the note's images where they stand, at the top or at the foot. The script asks for three things, one at a time, builds the note from them, runs the note gate, and writes the note through the Evernote MCP. The gate's PASS stamps the text, and the write refuses a draft without that stamp; the note-gate plugin refuses an MCP whole-body write without its marker. A life overview runs the life-overview skill's gate instead, whose PASS stamps the same way.

1. Run `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py init $TMPDIR/<slug> --guid <guid> --record ~/Software/Prototypes/socrates/memory/<topic>.md`. It prints code for ONE execute call, which reads the note with `get_note` and starts the build; the script never runs the Evernote CLI. For a new note, write your findings into a file and pass it in place of `--guid`, with `--title "<title>" --notebook "<notebook>"`. The record is Chaehan's memory file for the topic: what matters in the note comes from there and from the sections he asked for, never from an old summary. When the brief names his decisions, write them to a file as `D1: ...` lines and add `--decisions <file>`. When the brief has his instructions or new facts, pass them in his words with `--chaehan <file>`: the script then accepts their numbers and names. An update brings facts the note does not hold yet (what he found, measured or decided since, and your research for it): write them into a file, one plain sentence per line, and add `--new <file>`. They become items under "New facts", labelled like the old ones, and a decision may rest on them alone; every number and name in a kept new fact must stand in the record, `chaehan.md` or `found.md`, or the script refuses it. Lines Chaehan wrote out for a section go into the `--new` file as he wrote them, bullets and indents kept, and the section is those lines (core standard 6: the specified text lands first). Every text of Chaehan's that stands in the note as written (his lines, his feedback copied from another note) also goes into a file passed with `--verbatim <file>`: the gate then leaves its form alone (no list, no lead line, no item count) and fails (T20) when one of those paragraphs is not one unbroken run of the original words (RULES.md 93). Without `--new` an update has no place for its new facts, and that gap is what sent a build around the gate (failure 201). To move a section into a new note, add `--section "<heading words>" --title "<title>" --notebook "<notebook>"` to `--guid`: the section becomes the new note's old text. A trip note (one stay, its bookings, its decisions) also takes `--chaehan ~/Software/Prototypes/agentkit/skills/evernote/briefs/trip_note.md`: Chaehan's standing corrections for that format, before the file with what he said about this trip.
2. Run `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py next $TMPDIR/<slug>` and do what it prints. Run it again after each file you write, until it prints PASS. It asks, in this order:
   a) the decisions Chaehan makes with the note, at most five, and for every old section the decision it serves;
   b) a label for every item of the old text: decides, supports, world detail or known;
   c) per decision, a heading, a summary line and the section's first line, and a title of 2 to 6 words for every table you keep (`titles.tsv`), which the note shows as an H3 above the table.

   Labels are D (decides), S (supports), W (world detail), K (known) and M (moved: the item now lives in another note, whose exact title is its parent). An item's new wording goes into `edits.tsv` as `id<TAB>text`, a table's rows joined by `\n`; the script refuses an edit that copies its instructions, a number or name it cannot find in the note, the record, `chaehan.md` or `found.md`, a thousand separator and "about" before a number. Research for an edit goes into `found.md` in the build folder, each fact with its source URL. A link to another note comes from `note_build.py link "<words>"`, which prints the exact link; the script checks that every Evernote link names a real note by its exact title. A note whose Summary is not one line per section (the life-challenges topic note) writes its one to three Summary lines into `summary.md` in the build folder and puts "-" in new.tsv's summary cells; the script checks each line as a summary line.
3. When `next` exits 3, it lists old sections that serve none of the decisions. Ask Chaehan with the question tool whether each one stays, and write his answer into `decisions.md`. A section leaves his note only with his word.
4. Run `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py write $TMPDIR/<slug>` and run the code it prints in ONE execute call, exactly as printed. The call creates the note or replaces its body with `edit_note`, reads it back with `get_note`, and returns the verify result; a line starting REFUSED (a link without the linked note's exact title, an image the rewrite would drop, a draft changed after its PASS) names what to fix before you write again; it is reported, never routed around: no other `edit_note` call on that note, and its image stays untouched (an image at the top is kept by the write itself). `link "<words>"` likewise prints one execute call that lists the exact links. A refusal because the note is open in the app is a lock: follow "Note lock recovery (RTE room)" below. Report the cut list (`cuts.md`) and the verify result.

The script delivers Chaehan's three imperatives by construction. Items labelled world detail or known go to the cut list, so the note gets shorter. Every section opens with its first line, which states its point. Supporting items sit indented under the item they support. It also refuses a decision or sentence that copies its instructions, and a number or name that neither the note nor the record contains. Never edit `draft.md` by hand: the stamp no longer matches, and the write is refused.

## A text you wrote, from Claude Code

Time every Evernote and Hanji create or write from its start to the verified read-back, and report the seconds with the result (Chaehan, 2026-11-14: "you should always time the evernote and hanji creations and report them"); `note_test.py` prints the run's clock and `report.md` its steps and cost, and a Hanji helper write is timed around the command.

When Chaehan asks Claude to write a note's text (an analysis, a summary) and the Evernote work to be done by the tools, the text skips note_build's selection steps and still passes the gate. Chaehan, 2026-11-10: "fix the evernote skill so it can be used by you as well". Claude Code cannot call the Evernote MCP, so the write runs in opencode, in one command:

1. Write the text to a file in the note's style (section 3 of the life-overview skill). Photos for the top go above the first heading as lines of their own with their local path, `![name](</path/with spaces.jpg>)`.
2. `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py init <folder> --as-is <file> --title "<title>" --notebook "<notebook>"`, with `--verbatim <file>` for Chaehan's own words in it. To change an existing note, pass `--guid <guid> --base <the note's text as read>` (the readback.md of its last write, or its markdown export): the write is refused when the note changed since. When the change is one section, add `--replace-section "<heading>"` with that section as the file: only the section is written, and Chaehan's edits elsewhere (an added list, photos placed in a table) stay byte for byte. A whole-text write by guid cannot keep a photo inside a table and refuses such a note. It runs the gate; on a failure, edit `<folder>/draft.md` and run `next <folder>` until it prints PASS. In Claude Code's sandbox the stamp lands in `~/.cache/agentkit/note-gate`, which the plugin and the CLI read as well, so no step needs the sandbox lifted.
3. `python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_test.py --write <folder> --out <run folder>`, outside the sandbox. The agent in opencode runs `write` and its one execute call, which refuses a new note whose exact title Evernote already holds, creates the note, uploads the photos and puts them above the text, reads the note back, and downloads each photo to match its MD5. `<run folder>/report.md` gives the time, the steps and the cost; `<folder>/write_result.txt` holds the verdict.

The same `init --as-is` with `--dest hanji` writes the note to Hanji instead, with no opencode run.

## Testing a note build with deepseek: run note_test.py

A test of how the installed model builds a note runs one command, outside the sandbox:

```
python3 ~/Software/Prototypes/agentkit/skills/evernote/scripts/note_test.py --brief <brief.md> --out <folder> [--session <id>]
```

It starts `opencode run --standalone --agent socrates` in the socrates folder with the brief, on the OpenCode Go API (`opencode-go/deepseek-v4.1-flash#high`) first and the direct DeepSeek API (`deepseek/deepseek-flash#high`) as the fallback: a spent quota, an unavailable model or a cut connection moves the same session to the fallback at once. Before the first step it pings the provider with a one-word request through the same path (2-4 s measured) and gives it 8 s, so a provider that is down is known in seconds (Chaehan, 2026-11-10: "fix the probe it costs just a few seconds as a ping"). It stops the run when two `next` rounds in a row neither lower the failure count nor change the first failure, after `--idle` seconds without an event (120), or past `--budget` seconds (1500). `<folder>/report.md` names each provider and model used with its steps, tokens and cost, every `note_build.py` call with its failures, why the run ended and the agent's last message, and splits the wall time into model steps and tool calls: measured 2026-11-10, about 5 s of model and 2.6 s of tool plumbing per step whatever the tool, 73 steps in 584 s and 38 in 312 s, so the step count is what a run's wall time follows and a 150 s run needs about 19 steps. `events.jsonl` holds the raw stream. Exit 0 means written and verified, 3 the agent asks Chaehan (continue with `--session` and his answers as the brief), 4 stuck, 5 idle or over budget, 6 every provider failed. A run that writes no note (a read, an export to files) names the files it must leave with `--expect <file> ...`, and those decide its outcome; without it such a run reads as a failure (2026-11-10: a read that saved every file still ended "exit 1, written False").

The loop: run it, read `report.md`, change one thing (the brief, a step text, a check) against the last run, and run again. A run that is stuck names the failure it repeats; fix the setup that produces it before another run (RULES.md rule 74).

## Briefing another agent to rewrite a note

A brief names the note, Chaehan's record of the topic and, when he gave them, his decisions. It says nothing about what to keep:

> Rewrite the Evernote note "<title>" (guid <guid>) with note_build.py, as the evernote skill's section "Writing or rewriting a note's text" says. Chaehan's record: `~/Software/Prototypes/socrates/memory/<topic>.md`. Report the cut list, the verify result, and each section Chaehan decided on.

Never add "every number stays", "every citation stays" or "keep all facts". The labels and the cut list already protect Chaehan's facts, and those words forbid the selection the rewrite is for.

## A note write is verified against the reader's view, not the stored bytes

Reading the ENML back proves storage; it does not prove the client renders the block or that the user can read it. Learned 2026-10-07, when the Kobe beef table was reported missing after two writes that each "verified" by re-reading the note:

1. **Build tables with the pipeline, never by hand-writing ENML `<table>` markup.** A markdown table through the converter, or `create-table`, is the shape this project's notes are known to render. Hand-assembling `<table width="…"><colgroup>…` copied out of another note is not a guarantee, and a storage read cannot tell the two apart.
2. **Verify the shape by converting the note back through the project's own converter** — `get <guid> --markdown` — and reading that output. A table that does not come back as a markdown table, or a bullet whose text comes back as a bare `-`, is a defect the byte check cannot see: the same day, a `<li>` containing a nested `<ul>` converted to an empty `-` with its parent's text gone. The converter keeps a parent's text since 2026-11-06, so a point and its sub-points read back as written.
3. **When the user says a note is unreadable or a block is missing, do not answer with the stored content.** Ask what he sees — a screenshot settles it — and check whether the note is open in the desktop app, where the client's own copy can be written back over an API write. Never claim a note is fixed on the strength of an API read: that is the claim he has to disprove.

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

**A dated snapshot is never superseded** (RULES.md 31). A note whose title starts
with a date and records a state is what Chaehan believed on that date. A rework
issues a new date and a new note; the earlier note and its local file stay
untouched, never folded, trashed or renamed. The sweep covers undated working
notes and same-date drafts only.

A twin is written from its approved file, and its text is checked against that file by hash before any old copy is trashed.

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
4. **Delete every leftover `<img src="...">` tag.** The re-upload restores the
   resource; it does not remove the tag the body replacement wrote, and that tag
   stays in the body pointing at a path Evernote cannot resolve, drawing a broken
   image beside the graphic it duplicates. Remove each one surgically
   (`edit_note`, `mode: "replace"`, the tag as `find`, empty `content`), one tag
   per picture. Verified 2026-10-12 on "2026-09-11 KUBS DT Course Design": two
   tags had survived the recovery since 2026-10-05 - the course chart's under the
   title, the JTBD diagram's under Reading - each next to the resource it
   duplicated, and the user reported it as "the second image is broken now".
5. Verify: the raw content holds one `<en-media>` per graphic with the recorded
   hash and **no relative-path `<img>` tag**. Read it with `get_note`, never with
   the markdown conversion: the converter drops an unknown `<img>` on the way
   out, so the markdown read shows the graphics and hides the broken tag - that
   check passes on a note the client draws as broken. A notebook sweep is one
   `get_note` per note counting `<img` against `<en-media` and `resources`
   (2026-10-12, 25 KUBS DT notes, all clean after this repair).

Risk set: notes whose markdown twin references images by path. In KUBS DT those
are the course design overview (week grid at the top), the opener story (the BigP
retrospective photo) and the diagram evolution document. The opener story's photo
was lost the same way and is recoverable from its note history
(`listNoteVersions` / `getNoteVersion`, the 2026-09-21 version carries it as
`31eb7c3deb7877e81a2d4569e00b3efb`, 1037895 bytes, image/jpeg).

## Uploading an image into a note via MCP (the binary bridge)

A photo at the top of a note written with note_build goes in with the write itself: an image line with a local path above the first heading, and `write` does steps 1 to 5 below in its one execute call, with the bridge doing the byte upload in Python (2026-11-10: four photos, two already in storage). The steps below are for an image anywhere else.

The MCP path for a new embedded image is `start_attachment_upload` then the
GCS upload then `finalize_attachment` then `edit_note`. The sandbox cannot do
the middle step itself: its `fetch` has no binary response (`arrayBuffer` is
absent) and no binary request body, so the file bytes cannot be PUT from
`execute`. Working bridge (verified 2026-10-06 on a 152227-byte PNG):

1. `start_attachment_upload` in `execute` (note GUID, lowercase MD5 and exact
   byte count of the file). The response carries `uploadUrl` and
   `alreadyUploaded`; when `alreadyUploaded` is true the bytes are already in
   storage, so skip the upload and go straight to `finalize_attachment`.
2. Start `python3 -m http.server <port> --bind 127.0.0.1` in any folder (kill
   it after), then emit the URL to the shell from `execute` with a GET:
   `fetch("http://127.0.0.1:<port>/bridge?u=" + encodeURIComponent(uploadUrl))`.
   A 404 response is expected; the request line lands in the server's access
   log, which is the hand-off. Each attempt takes a free port and a log file of
   its own. On 2026-11-07 a second server started on a port the first still
   held exited with `Address already in use`, and because both wrote to the same
   log path, the redirect emptied the log that held the signed URL: the hand-off
   then read as "no URL in the log". A fresh port and a fresh log worked at once.
3. In the shell, read the log line, `urllib.parse.unquote` the value, then the
   two curl calls: `POST` with `x-goog-resumable: start` and
   `x-upload-content-length: <size>` headers returns the session URI in the
   `Location` header; `PUT` with `Content-Length` and `x-upload-content-length`
   headers and `--data-binary @<file>` returns 200. Match the line with
   `/bridge\?k=(\w+)&u=(\S+) HTTP`: the access log writes ` HTTP/1.1` after the
   query, so a pattern ending in a quote matches nothing and the URL silently
   looks missing.
4. Put the `en-media` tag into the body FIRST, then finalize. Case the tag
   with `edit_note` (`prepend` for the top of the note, or `replace` against
   the old `<en-media ... />` for a swap; build `find` from the `get_note`
   string), then call `finalize_attachment` (same GUID, hash, size, mimeType;
   filename and width/height help the editor's first render). The binding
   takes only when the tag is already in the body: on 2026-10-07 both images
   were finalized before insertion, finalize returned a tag and a
   `resourceGuid` for each, and `get_attachment` still answered "No
   attachment with hash ... on note ..."; the same two files bound as soon as
   the tags were in the body and finalize ran again (`alreadyUploaded: true`,
   so no second PUT).
5. Verify by download, and re-verify later. `get_attachment` returns a
   pre-signed URL whose bucket is now `en-production-resources` (a
   `...-resources-temporary` URL means the bytes are still staging); curl it
   and MD5-compare against the local file. Then read the note again a few
   minutes later when the note is open in the desktop app: a client holding the note open saves its own copy and can
   revert the note to its own resource list, leaving the body tags pointing at
   nothing and the note carrying broken images. On 2026-10-07 the binding was
   intact at t0 and gone two minutes later, after which the desktop app's tab
   was switched away with `close-note` and the re-bound resources survived.
   A new note is open in no app, so its one read-back is the check. Never wait in a shell call: the shell stops
   a `sleep` at ~20 s (2026-11-10: two `sleep 150` calls ended after 41 s in all, before any change could show). A later read is a
   separate call made after other work.
   When the image has to survive a client that has the note open, prefer the
   Thrift CLI `embed-image`: it binds the resource in the same `updateNote`,
   but it fails with "Note is locked by another editing session (RTE room
   open)" while the app holds the note — `close-note` releases the app's tab
   (bring the Evernote window to the current Space first, or its helper
   reports "evernote window not visible on current Space").

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
  "no i wanted the DPS before the values!"; rule 157, agentic_ai failure 46).
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

**Authoring a link in a note written from markdown.** A section that has a detail
note carries the state in one sentence, its consequence when the record makes it
plain, and one link to that note. Build the link before the write:

1. Resolve the target: `find-note "<exact title>"` returns its guid.
2. Write it in the markdown as `[<exact title>](evernote:///view/39d2f74/s365/<guid>/<guid>/)`. The link text is the note's exact title; `39d2f74` and `s365` are this account's user id and shard, read from the token.
3. `markdown_to_enml` turns it into `<a href="evernote:///...">`. After the write, the raw read shows one `evernote:///view/` per detail note; zero links in a note with detail sections is a failed write.

For a note that already exists, `link-note` below appends the same link.

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
