#!/usr/bin/env python3
"""Copy Evernote notes into Hanji: read through the Evernote MCP, written through the hanji helper.

The Evernote MCP is reached only from opencode's `execute` sandbox, which can
neither write a file nor download bytes. So `start` prints one `execute` call
that finds each title (search_notes), reads the note (get_note) and a download
link for each of its files (get_attachment), and posts all of it to a receiver
this script starts on 127.0.0.1. The receiver converts each note's ENML to
Markdown with socrates's converter, downloads its files and checks each against
its Evernote MD5, creates the note in Hanji with hanji_note.py, and compares the
Hanji note with the Evernote original: every word, every file byte for byte,
checkboxes, tables and web links. The execute call returns that report, which
is also written to <out>/report.md.

    en_to_hanji.py start "<title>" ["<title>" ...] [--notebook NB] [--out DIR] [--dry-run] [--db DB]
    en_to_hanji.py serve --port N --out DIR [...]      # started by start
    en_to_hanji.py convert NOTE.json [--files DIR]     # a saved get_note result as Markdown, offline

The Evernote note is only read, never changed or deleted. A note goes into the
Hanji notebook named by --notebook, else the one named like its Evernote
notebook, else Inbox. A title already in Hanji is skipped.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import socket
import subprocess
import sys
import unicodedata
import urllib.request
from collections import Counter
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
HELPER = HERE / "hanji_note.py"
SOCRATES = Path(os.environ.get("NOTE_BUILD_SOCRATES") or Path.home() / "Software" / "Prototypes" / "socrates")
APP_BIN = os.environ.get("HANJI_BIN") or "/Applications/Hanji.app/Contents/MacOS/hanji"
FALLBACK_NOTEBOOK = "Inbox"

EXT = {"image/png": "png", "image/jpeg": "jpg", "image/gif": "gif", "image/webp": "webp", "image/heic": "heic",
       "image/svg+xml": "svg", "application/pdf": "pdf", "text/plain": "txt", "audio/mpeg": "mp3",
       "audio/x-m4a": "m4a", "video/mp4": "mp4"}

MEDIA_RE = re.compile(r"<en-media\b[^>]*?>(?:\s*</en-media>)?", re.I)
HASH_RE = re.compile(r'\bhash="([0-9a-fA-F]+)"')
TODO_RE = re.compile(r"<en-todo\b([^>]*?)/?>(?:\s*</en-todo>)?", re.I)
CELL_RE = re.compile(r"<(td|th)\b[^>]*>.*?</\1\s*>", re.S | re.I)
ENLINK_RE = re.compile(r"<a\b[^>]*\bhref=\"evernote:[^\"]*\"[^>]*>(.*?)</a\s*>", re.S | re.I)
CRYPT_RE = re.compile(r"<en-crypt\b.*?</en-crypt\s*>", re.S | re.I)
WEB_RE = re.compile(r"""href=["'](https?://[^"']+)["']""", re.I)
SPAN_RE = re.compile(r'<span\b[^>]*\bstyle="([^"]*)"[^>]*>([^<]*)</span\s*>', re.I)
RGB_RE = re.compile(r"(?<![-\w])color\s*:\s*rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", re.I)
HEX_RE = re.compile(r"(?<![-\w])color\s*:\s*#([0-9a-f]{6})\b", re.I)
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")

EXECUTE = """const B = "http://127.0.0.1:{port}", titles = {titles};
const norm = s => String(s || "").normalize("NFC").replace(/[\\u2018\\u2019]/g, "'").replace(/\\s+/g, " ").trim().toLowerCase();
const notes = [];
for (const title of titles) {{
  const r = {{ title }};
  try {{
    const s = await tools.evernote.search_notes({{ query: 'intitle:"' + title.replace(/"/g, "") + '"', maxResults: 50 }});
    const hits = (s.hits || []).map(h => ({{ title: h.title, id: h.noteId }}));
    let exact = hits.filter(h => norm(h.title) === norm(title));
    if (!exact.length) {{
      const pre = hits.filter(h => norm(h.title).startsWith(norm(title)));
      if (pre.length === 1) {{ exact = pre; r.byBeginning = true; }}
    }}
    r.matches = exact;
    if (exact.length === 1) {{
      const n = await tools.evernote.get_note({{ noteId: exact[0].id }});
      r.note = n;
      const sc = (n.structuredContent && n.structuredContent.resources) ? n.structuredContent : n;
      r.files = [];
      for (const x of (sc.resources || [])) r.files.push({{ hash: x.hash, got: await tools.evernote.get_attachment({{ noteId: exact[0].id, hash: x.hash }}) }});
    }} else if (!exact.length) {{
      const s2 = await tools.evernote.search_notes({{ query: title, maxResults: 8 }});
      r.near = (s2.hits || []).map(h => h.title);
    }}
  }} catch (e) {{ r.error = String((e && e.message) || e); }}
  notes.push(r);
}}
let notebooks = null;
try {{ notebooks = await tools.evernote.search_notebooks({{ query: "", maxResults: 100 }}); }} catch (e) {{ notebooks = {{ error: String((e && e.message) || e) }}; }}
return await (await fetch(B + "/import", {{ method: "POST", body: JSON.stringify({{ notes, notebooks }}) }})).text();"""


# ---------------------------------------------------------------- reading the MCP results

def find_enml(obj) -> str | None:
    """The ENML string inside a get_note result, whatever its wrapping."""
    if isinstance(obj, str):
        if "<en-note" in obj:
            if obj.lstrip().startswith("{"):
                try:
                    return find_enml(json.loads(obj)) or obj
                except ValueError:
                    pass
            return obj
        return None
    vals = obj.values() if isinstance(obj, dict) else obj if isinstance(obj, list) else []
    for v in vals:
        r = find_enml(v)
        if r:
            return r
    return None


def find_key(obj, key: str):
    """The first value stored under `key` anywhere inside obj (JSON strings are opened)."""
    if isinstance(obj, str) and obj.lstrip().startswith(("{", "[")):
        try:
            obj = json.loads(obj)
        except ValueError:
            return None
    if isinstance(obj, dict):
        if key in obj and obj[key] not in (None, "", []):
            return obj[key]
        obj = list(obj.values())
    if isinstance(obj, list):
        for v in obj:
            r = find_key(v, key)
            if r not in (None, "", []):
                return r
    return None


def resources(note) -> list[dict]:
    res = find_key(note, "resources") or []
    if isinstance(res, str):
        res = json.loads(res)
    return [r for r in res if isinstance(r, dict) and r.get("hash")]


def tag_names(note) -> list[str]:
    tags = find_key(note, "tags") or find_key(note, "tagNames") or []
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except ValueError:
            tags = []
    out = []
    for t in tags:
        name = t if isinstance(t, str) else (t.get("name") or t.get("label")) if isinstance(t, dict) else None
        if name and not re.fullmatch(r"[0-9a-f-]{36}", name):
            out.append(name)
    return out


# ---------------------------------------------------------------- ENML to Hanji Markdown

def _enml():
    sys.path.insert(0, str(SOCRATES))
    from projects.evernote.src import enml  # noqa: PLC0415
    return enml


def file_line(f: dict) -> str:
    return f"{'!' if f['mime'].startswith('image/') else ''}[{f['name']}]({f['path']})"


def marked(style: str) -> bool:
    """Whether a span's style marks its words: a highlight, or a text colour that is not grey."""
    if re.search(r"--en-highlight|background(-color)?\s*:\s*(?!\s*(transparent|#fff|white|rgb\(\s*255))", style, re.I):
        return True
    m = RGB_RE.search(style)
    rgb = [int(x) for x in m.groups()] if m else None
    if not rgb and (h := HEX_RE.search(style)):
        rgb = [int(h.group(1)[i:i + 2], 16) for i in (0, 2, 4)]
    return bool(rgb) and max(rgb) - min(rgb) > 60


def esc_md(text: str, line_start: bool) -> str:
    """Literal text as Markdown: the characters Hanji would read as formatting, escaped."""
    t = text.replace("\\", "\\\\")
    t = re.sub(r"([*`~\[\]<|])", r"\\\1", t)
    t = t.replace("==", "\\=\\=")
    t = re.sub(r"(?<![^\W_])_|_(?![^\W_])", r"\\_", t)
    if line_start:
        t = re.sub(r"^(\s*)([-+#>])(\s)", r"\1\\\2\3", t)
        t = re.sub(r"^(\s*\d+)\.(\s)", r"\1\\.\2", t)
    return t


def escape_text(s: str) -> str:
    """Escape every text node of the ENML, outside code, for the Markdown it becomes."""
    out, pos, in_code = [], 0, 0
    for m in re.finditer(r"<[^>]+>", s):
        txt = s[pos:m.start()]
        if txt:
            if in_code:
                out.append(txt)
            else:
                prev = out[-1] if out else ""
                start = bool(re.match(r"<(div|p|li|br|h\d|td|th)\b", prev, re.I)) or not out
                out.append(html.escape(esc_md(html.unescape(txt), start), quote=False))
        tag = m.group(0)
        if re.match(r"<(pre|code)\b", tag, re.I):
            in_code += 1
        elif re.match(r"</(pre|code)\s*>", tag, re.I):
            in_code = max(0, in_code - 1)
        out.append(tag)
        pos = m.end()
    out.append(s[pos:])
    return "".join(out)


def convert(enml_text: str, files: dict[str, dict]) -> tuple[str, list[str]]:
    """Hanji Markdown for an Evernote note, and the changes Hanji forces, in words.

    files maps an Evernote hash to {name, mime, path}; a hash without a file is an error.
    """
    changes: list[str] = []
    s = CRYPT_RE.sub("", enml_text)
    if s != enml_text:
        changes.append("an encrypted block was left out: Hanji cannot decrypt Evernote's")
    links = ENLINK_RE.findall(s)
    if links:
        s = ENLINK_RE.sub(lambda m: m.group(1), s)
        changes.append(f"{len(links)} link(s) to other Evernote notes became their text: Hanji has no note links")
    s = TODO_RE.sub(lambda m: "HJTODOX " if re.search(r'checked\s*=\s*"true"', m.group(1), re.I)
                    else "HJTODOO ", s)
    marks = [0]

    def span(m: re.Match) -> str:
        if marked(m.group(1)) and m.group(2).strip():
            marks[0] += 1
            return f"HJHLO{m.group(2)}HJHLC"
        return m.group(2)
    s = SPAN_RE.sub(span, s)
    if marks[0]:
        changes.append(f"{marks[0]} coloured or highlighted run(s) became Hanji's one highlight: Hanji 0.8.1 has "
                       "no text colours, so green, red and orange read the same")
    bare = sum(1 for t in re.findall(r"<table\b.*?</table\s*>", s, re.S | re.I) if not re.search(r"<th\b", t, re.I))
    if bare:
        changes.append(f"the first row of {bare} table(s) without a header row reads as their header: a Markdown "
                       "table always has one")
    in_cell: list[str] = []

    def cell(m: re.Match) -> str:
        c = m.group(0)

        def med(x: re.Match) -> str:
            h = HASH_RE.search(x.group(0))
            if h:
                in_cell.append(h.group(1).lower())
                return f" HJCELLMEDIA{h.group(1).lower()} "
            return ""
        c = MEDIA_RE.sub(med, c)
        c = re.sub(r"<li\b[^>]*>", " HJBR HJBULLET ", c, flags=re.I)
        c = re.sub(r"</?(ul|ol|li)\b[^>]*>", " ", c, flags=re.I)
        c = re.sub(r"</(div|p)\s*>\s*<(div|p)\b[^>]*>", " HJBR ", c, flags=re.I)
        return re.sub(r"<br\s*/?>", " HJBR ", c, flags=re.I)
    for _ in range(3):  # "<b> City</b>" as " <b>City</b>": Markdown bold cannot open or close on a space
        s = re.sub(r"(<(b|strong|i|em|u|s|strike)\b[^>]*>)(\s+)", r"\3\1", s, flags=re.I)
        s = re.sub(r"(\s+)(</(b|strong|i|em|u|s|strike)\s*>)", r"\2\1", s, flags=re.I)
    s = escape_text(s)
    s = CELL_RE.sub(cell, s)
    s = MEDIA_RE.sub(lambda x: (f"<div>HJMEDIA{HASH_RE.search(x.group(0)).group(1).lower()}</div>"
                                if HASH_RE.search(x.group(0)) else ""), s)
    md = _enml().enml_to_markdown(s)

    def fl(h: str) -> str:
        if h not in files:
            raise KeyError(f"no downloaded file for Evernote hash {h}")
        return file_line(files[h])

    out: list[str] = []
    pending: list[str] = []
    for ln in md.split("\n"):
        is_row = ln.lstrip().startswith("|")
        if pending and not is_row:
            out += ["", *pending, ""]
            pending = []
        m = re.match(r"^(\s*)(?:[-*] )?HJTODO([XO])\s*(.*)$", ln)
        if m:
            ln = f"{m.group(1)}- [{'x' if m.group(2) == 'X' else ' '}] {m.group(3)}"
        ln = ln.replace("HJTODOX", "[x]").replace("HJTODOO", "[ ]")
        ln = re.sub(r"HJHLO(\s*)", r"\1==", ln)
        ln = re.sub(r"(\s*)HJHLC", r"==\1", ln)
        ln = re.sub(r"HJBULLET\s*", "• ", ln)
        if is_row:
            for h in re.findall(r"HJCELLMEDIA([0-9a-f]+)", ln):
                pending.append(fl(h))
                ln = ln.replace(f"HJCELLMEDIA{h}", esc_md(files[h]["name"], False))
            cells = [re.sub(r"^(\s*<br>\s*)+|(\s*<br>\s*)+$", "", re.sub(r"\s*HJBR\s*", "<br>", c))
                     for c in ln.split("|")]
            ln = "|".join(f" {c.strip()} " if c.strip() else c for c in cells).strip()
            out.append(ln)
            continue
        ln = re.sub(r"\s*HJBR\s*", "\n", ln)
        parts = re.split(r"HJMEDIA([0-9a-f]+)", ln)
        if len(parts) == 1:
            out.append(ln)
            continue
        for i, p in enumerate(parts):
            if i % 2:
                out += ["", fl(p), ""]
            elif p.strip() and p.strip() not in ("-", "*"):
                out.append(p.rstrip())
    if pending:
        out += ["", *pending]
    if in_cell:
        changes.append(f"{len(in_cell)} file(s) inside table cells moved below their table, the cell keeping the "
                       "file's name: Hanji 0.8.1 holds a file only on a line of its own")
    deep = sum(1 for ln in out if re.match(r"^#{4,6}\s", ln))
    if deep:
        changes.append(f"{deep} heading(s) below ### come back as ###: Hanji has three heading levels")
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(separate_blocks("\n".join(out).split("\n")))).strip() + "\n"
    return text, changes


def _kind(ln: str) -> str:
    if not ln.strip():
        return "blank"
    if ln.lstrip().startswith("|"):
        return "row"
    if re.match(r"^\s*([-*+]|\d+[.)])\s", ln):
        return "list"
    if ln.startswith((" ", "\t")):
        return "indent"
    return "para"


def separate_blocks(lines: list[str]) -> list[str]:
    """A blank line where a list or a table meets other text.

    Evernote writes one <div> per line, which the converter gives as lines with no
    blank between them. Hanji reads each as its own paragraph, except a line right
    after a list item (Markdown folds it into the item) or after a table row (it
    becomes a row).
    """
    out: list[str] = []
    prev = "blank"
    for ln in lines:
        k = _kind(ln)
        if (prev == "list" and k == "para") or (prev == "row" and k not in ("row", "blank")) or \
                (k == "row" and prev not in ("row", "blank")):
            out.append("")
        out.append(ln)
        prev = k
    return out


# ---------------------------------------------------------------- checks

def words(text: str) -> Counter:
    return Counter(re.findall(r"\w+", unicodedata.normalize("NFC", text).lower()))


def enml_words(enml_text: str) -> Counter:
    s = CRYPT_RE.sub(" ", enml_text)
    s = re.sub(r"<!DOCTYPE[^>]*>", " ", s)
    s = re.sub(r"</?(span|a|b|strong|i|em|u|s|strike|font|sup|sub|code)\b[^>]*>", "", s, flags=re.I)  # no word break
    s = re.sub(r"<[^>]+>", " ", s)
    return words(html.unescape(s))


def md_tables(md: str) -> int:
    return sum(1 for ln in md.split("\n") if TABLE_SEP.match(ln) and "|" in ln)


def hanji(db: str | None, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([APP_BIN, *(["--db", db] if db else []), *args], capture_output=True, text=True,
                          timeout=60)


def helper(db: str | None, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HELPER), *(["--db", db] if db else []), *args],
                          capture_output=True, text=True, timeout=300)


def check(enml_text: str, nid: str, db: str | None, hashes: list[str]) -> list[str]:
    """What the Hanji note lost against the Evernote original, as report lines."""
    lines = []
    text = hanji(db, "note", "get", nid, "--format", "text").stdout
    md = hanji(db, "note", "get", nid, "--format", "md").stdout
    ev, hj = enml_words(enml_text), words(text)
    lost = ev - hj
    n = sum(ev.values())
    if lost:
        sample = ", ".join(f"{w}" + (f" ×{c}" if c > 1 else "") for w, c in lost.most_common(15))
        lines.append(f"- Words: {sum(lost.values())} of {n} missing: {sample}")
    else:
        lines.append(f"- Words: all {n} kept.")
    atts = json.loads(hanji(db, "--json", "note", "attachments", nid).stdout or "[]")
    got = Counter(hashlib.md5(Path(a["path"]).read_bytes()).hexdigest() for a in atts if a.get("path"))
    want = Counter(hashes)
    if want or got:
        ok = sum((want & got).values())
        tail = "byte-identical" if ok == sum(want.values()) == sum(got.values()) else \
            f"{sum((want - got).values())} missing, {sum((got - want).values())} extra"
        lines.append(f"- Files: {ok} of {sum(want.values())}, {tail}.")
    todos = TODO_RE.findall(enml_text)
    if todos:
        ticked = sum(1 for t in todos if re.search(r'checked\s*=\s*"true"', t, re.I))
        h_all = len(re.findall(r"^\s*- \[[ xX]\] ", md, re.M))
        h_tick = len(re.findall(r"^\s*- \[[xX]\] ", md, re.M))
        lines.append(f"- Checkboxes: {h_all} of {len(todos)}, {h_tick} of {ticked} ticked.")
    t_ev = len(re.findall(r"<table\b", enml_text, re.I))
    if t_ev:
        lines.append(f"- Tables: {md_tables(md)} of {t_ev}.")
    web = set(WEB_RE.findall(enml_text))
    if web:
        kept = {u for u in web if html.unescape(u) in md or u in md}
        miss = sorted(web - kept)
        lines.append(f"- Web links: {len(kept)} of {len(web)}" + (f"; missing: {', '.join(miss[:5])}." if miss else "."))
    return lines


# ---------------------------------------------------------------- the import

def slug(s: str) -> str:
    return re.sub(r"[^\w.-]+", "-", s, flags=re.UNICODE).strip("-")[:60] or "note"


def download(url: str, dest: Path) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as r:  # noqa: S310 - Evernote's signed link
        data = r.read()
    dest.write_bytes(data)
    return data


def notebook_for(name: str | None, hanji_books: list[str], forced: str | None) -> str:
    if forced:
        return forced
    if name and name in hanji_books:
        return name
    return FALLBACK_NOTEBOOK


def run_import(payload: dict, out: Path, db: str | None, forced_nb: str | None, dry: bool) -> str:
    out.mkdir(parents=True, exist_ok=True)
    (out / "received.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    nb_names = {}
    for h in (find_key(payload.get("notebooks"), "hits") or []):
        if isinstance(h, dict) and h.get("notebookId"):
            nb_names[h["notebookId"]] = h.get("label") or h.get("name")
    books = [b["name"] for b in json.loads(hanji(db, "--json", "notebook", "list").stdout or "[]")]
    blocks, moved = [], 0
    for i, r in enumerate(payload.get("notes", []), 1):
        title = r.get("title", "?")
        b = [f"## {title}"]
        blocks.append(b)
        if r.get("error"):
            b.append(f"Not moved: the Evernote MCP failed: {r['error']}")
            continue
        matches = r.get("matches") or []
        if len(matches) != 1:
            if matches:
                b.append(f"Not moved: {len(matches)} Evernote notes carry this title; name one by its guid.")
            else:
                near = "; ".join(r.get("near") or []) or "none"
                b.append(f"Not moved: no Evernote note has this exact title. Nearest titles: {near}.")
            continue
        note = r.get("note")
        if r.get("byBeginning"):
            title = find_key(note, "title") or matches[0]["title"]
            b[0] = f"## {title}"
            b.append(f"No exact title {r['title']!r}; one Evernote note begins with it, and its title is kept.")
        enml_text = find_enml(note)
        if not enml_text:
            b.append("Not moved: get_note returned no ENML.")
            continue
        if "</en-note>" not in enml_text:
            b.append("Not moved: the ENML has no closing </en-note>, so get_note may have cut it short.")
            continue
        folder = out / f"{i:02d}-{slug(title)}"
        (folder / "files").mkdir(parents=True, exist_ok=True)
        (folder / "evernote.enml").write_text(enml_text, encoding="utf-8")
        links = {f["hash"].lower(): find_key(f.get("got"), "downloadUrl") for f in r.get("files") or []}
        files, bad = {}, []
        for k, res in enumerate(resources(note), 1):
            h = res["hash"].lower()
            mime = res.get("mime") or res.get("mimeType") or "application/octet-stream"
            name = unicodedata.normalize("NFC", re.sub(r"[\[\]\n\r]", "", res.get("name") or res.get("filename") or "")) or \
                f"file-{k}.{EXT.get(mime, 'bin')}"
            ext = EXT.get(mime) or (Path(name).suffix.lstrip(".") or "bin")
            dest = folder / "files" / f"{k:02d}-{h[:8]}.{ext}"
            url = links.get(h)
            if not url:
                bad.append(f"{name}: get_attachment gave no download link")
                continue
            try:
                data = download(url, dest)
            except Exception as exc:  # noqa: BLE001 - reported, the note is not written
                bad.append(f"{name}: download failed ({exc})")
                continue
            if hashlib.md5(data).hexdigest() != h:
                bad.append(f"{name}: the downloaded bytes do not match Evernote's MD5")
                continue
            files[h] = {"name": name, "mime": mime, "path": str(dest)}
        if bad:
            b.append("Not moved: " + "; ".join(bad) + ".")
            continue
        try:
            md, changes = convert(enml_text, files)
        except KeyError as exc:
            b.append(f"Not moved: {exc.args[0]}.")
            continue
        md_path = folder / "note.md"
        md_path.write_text(md, encoding="utf-8")
        ev_nb = nb_names.get(find_key(note, "notebookId"))
        nb = notebook_for(ev_nb, books, forced_nb)
        where = f"Evernote notebook {ev_nb or 'unknown'}, {len(files)} file(s); Hanji notebook {nb}"
        if nb not in books:
            b.append(f"Not moved: Hanji has no notebook {nb!r} (it has {', '.join(books)}).")
            continue
        found = helper(db, "find", title)
        if found.returncode in (0, 5):
            b.append(f"Not moved: Hanji already has a note with this title ({found.stdout.strip()[:120]}).")
            continue
        if dry:
            b.append(f"Dry run: would create it; {where}. Markdown: {md_path}")
            b += [f"- Changes: {c}." for c in changes]
            continue
        args = ["create", "--notebook", nb, "--title", title, "--file", str(md_path)]
        for t in tag_names(note):
            args += ["--tag", t]
        res = helper(db, *args)
        try:
            made = json.loads(res.stdout or res.stderr)
        except ValueError:
            made = {}
        if res.returncode != 0 or not made.get("id"):
            why = (made.get("error") or res.stderr or res.stdout).strip()[:300]
            if res.returncode == 4:  # written, but the read-back differs: no unverified copy stays behind
                gone = helper(db, "delete", title)
                where_now = "moved to Hanji's trash" if gone.returncode == 0 else \
                    f"left in Hanji, and trashing it failed: {gone.stderr.strip()[:120]}"
                why = f"the copy did not read back as written, so it was {where_now}. {why}. " \
                      f"Diff: {str(made.get('diff', ''))[:600]}"
            b.append(f"Not moved: hanji_note.py create exited {res.returncode}: {why}")
            continue
        moved += 1
        b.append(f"Moved: {where}, id {made['id']}, write verified {made.get('verified')}.")
        b += check(enml_text, made["id"], db, [res_["hash"].lower() for res_ in resources(note)])
        b += [f"- Changed: {c}." for c in changes]
    head = [f"# Evernote to Hanji, {dt.datetime.now():%Y-%m-%d %H:%M}", "",
            f"{'Dry run, nothing written' if dry else f'Moved {moved} of {len(blocks)} notes'}. "
            "The Evernote notes are unchanged.", ""]
    rep = "\n".join(head + ["\n".join(b) + "\n" for b in blocks])
    (out / "report.md").write_text(rep, encoding="utf-8")
    return rep


# ---------------------------------------------------------------- commands

def cmd_start(a) -> int:
    out = Path(a.out or Path(os.environ.get("TMPDIR", "/tmp")) / "en-to-hanji" / f"{dt.datetime.now():%Y%m%dT%H%M%S}")
    out.mkdir(parents=True, exist_ok=True)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    cmd = [sys.executable, __file__, "serve", "--port", str(port), "--out", str(out)]
    for flag, val in (("--notebook", a.notebook), ("--db", a.db)):
        if val:
            cmd += [flag, val]
    if a.dry_run:
        cmd.append("--dry-run")
    log = open(out / "serve.log", "w")
    subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=True)
    print(f"Receiver on port {port}, waiting 15 minutes. Run this code in ONE execute call, exactly as printed. "
          f"It reads the notes through the Evernote MCP and returns the report, also written to {out}/report.md "
          "(read it there if the call errors or times out).\n")
    print(EXECUTE.format(port=port, titles=json.dumps(a.titles, ensure_ascii=False)))
    return 0


def cmd_serve(a) -> int:
    out = Path(a.out)
    state: dict = {}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *args):  # noqa: D401
            pass

        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
            try:
                rep = run_import(json.loads(raw), out, a.db, a.notebook, a.dry_run)
            except Exception as exc:  # noqa: BLE001 - the agent sees the reason in the execute result
                rep = f"en_to_hanji failed: {type(exc).__name__}: {exc}"
                (out / "report.md").write_text(rep + "\n", encoding="utf-8")
            data = rep.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            state["done"] = True

    srv = HTTPServer(("127.0.0.1", a.port), H)
    srv.timeout = 5
    deadline = dt.datetime.now() + dt.timedelta(minutes=15)
    while not state.get("done") and dt.datetime.now() < deadline:
        srv.handle_request()
    if not state.get("done"):
        (out / "report.md").write_text("# Evernote to Hanji\n\nThe execute call never reached the receiver; "
                                       "nothing was written.\n", encoding="utf-8")
    return 0


def cmd_convert(a) -> int:
    note = json.loads(Path(a.note).read_text(encoding="utf-8"))
    enml_text = find_enml(note) or ""
    files = {}
    for k, res in enumerate(resources(note), 1):
        h = res["hash"].lower()
        mime = res.get("mime") or "application/octet-stream"
        p = next(Path(a.files).glob(f"*{h[:8]}*"), None) if a.files else None
        files[h] = {"name": res.get("name") or f"file-{k}", "mime": mime, "path": str(p or f"missing-{h[:8]}")}
    md, changes = convert(enml_text, files)
    sys.stdout.write(md)
    for c in changes:
        print(f"change: {c}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("start", "serve"):
        p = sub.add_parser(name)
        if name == "start":
            p.add_argument("titles", nargs="+", help="exact Evernote titles")
        else:
            p.add_argument("--port", type=int, required=True)
        p.add_argument("--out")
        p.add_argument("--notebook", help="the Hanji notebook for every note")
        p.add_argument("--db", help="a Hanji database other than the app's (tests)")
        p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("convert")
    p.add_argument("note")
    p.add_argument("--files")
    a = ap.parse_args(argv)
    return {"start": cmd_start, "serve": cmd_serve, "convert": cmd_convert}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
