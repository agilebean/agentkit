# Evernote images

Read before any write to a note that holds an image, and before adding one (`SKILL.md`, "Reference files").

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
