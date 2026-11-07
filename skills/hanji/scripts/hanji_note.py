#!/usr/bin/env python3
"""Hanji notes by title: find, read, create, section and table edits, images in place.

Wraps the `hanji` command line of Hanji.app. The CLI itself writes a note's whole
text (`note set`) or adds at its end (`note append`, `note attach`); a whole-text
write turns every image into its name. This script edits a note's Markdown and
writes it back as text segments with each attachment re-attached where its line
stands, so a section edit keeps the note's images and files in place.

Every write backs the note up first (its Markdown and attachment files, under
$TMPDIR/hanji-backups/<id>/<time>/), writes, reads the note back and compares it
with the intended text after passing both through Hanji's own Markdown converter
on a scratch database. Output is JSON on stdout; `get` prints Markdown.

Exit codes: 0 done, 1 failed, 2 bad usage, 3 note or notebook not found,
4 the write did not verify (the note is as the read-back shows; the backup
restores it), 5 the title matches several notes, 6 the note changed since it
was read (a second writer).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import filecmp
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

APP_BIN = "/Applications/Hanji.app/Contents/MacOS/hanji"
ID_RE = re.compile(r"^[0-9a-f]{32}$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
ATT_RE = re.compile(r"^\s*(!?)\[([^\]]*)\]\(([^)\s]+)\)\s*$")
SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


class Fail(Exception):
    def __init__(self, code: int, message: str, **extra):
        super().__init__(message)
        self.code = code
        self.extra = extra


# ---------------------------------------------------------------- hanji calls

class Hanji:
    def __init__(self, db: str | None = None, profile: str | None = None):
        self.bin = os.environ.get("HANJI_BIN") or shutil.which("hanji") or APP_BIN
        self.sel = ["--db", db] if db else (["--profile", profile] if profile else [])

    def __call__(self, *args: str, stdin: str | None = None, sel: list[str] | None = None):
        cmd = [self.bin, *(self.sel if sel is None else sel), "--json", *args]
        try:
            p = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            raise Fail(1, f"no hanji binary at {self.bin}: install Hanji.app or set HANJI_BIN")
        out = p.stdout.strip()
        err = p.stderr.strip()
        if p.returncode != 0 or (out.startswith('{"error"')):
            msg = err or out
            try:
                msg = json.loads(msg)["error"]["message"]
            except (ValueError, KeyError, TypeError):
                pass
            raise Fail(p.returncode if p.returncode in (1, 2, 3) else 1, f"hanji {' '.join(args[:2])}: {msg}")
        return json.loads(out) if out else None

    def markdown(self, nid: str) -> str:
        return self("note", "get", nid, "--format", "md")["markdown"]

    def attachments(self, nid: str) -> list[dict]:
        return self("note", "attachments", nid)

    def live_notes(self) -> list[dict]:
        return self("note", "list", "--limit", "0")


def canonical(md: str) -> str:
    """md as Hanji itself writes it back: created on a scratch database, read, purged."""
    d = Path(tempfile.gettempdir()) / "hanji-canon"
    d.mkdir(parents=True, exist_ok=True)
    h = Hanji(db=str(d / "notes.db"))
    args = ("note", "create", "--notebook", "canon", "--stdin", "--format", "md")
    try:
        nid = h(*args, stdin=md)["id"]
    except Fail as e:
        if e.code != 3:
            raise
        h("notebook", "create", "canon")
        nid = h(*args, stdin=md)["id"]
    try:
        return h.markdown(nid)
    finally:
        h("note", "delete", nid)
        h("note", "purge", nid)


# ---------------------------------------------------------------- markdown model

def sha(md: str) -> str:
    return hashlib.sha256(md.encode()).hexdigest()[:12]


def code_mask(lines: list[str]) -> list[bool]:
    """True for each line inside (or opening/closing) a fenced code block."""
    mask, inside = [], False
    for ln in lines:
        if FENCE_RE.match(ln):
            mask.append(True)
            inside = not inside
            continue
        mask.append(inside)
    return mask


def headings(md: str) -> list[tuple[int, int, str]]:
    """(line index, level, text) of every heading outside code blocks."""
    lines = md.split("\n")
    mask = code_mask(lines)
    out = []
    for i, ln in enumerate(lines):
        m = HEADING_RE.match(ln)
        if m and not mask[i]:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def find_heading(md: str, text: str) -> tuple[int, int, str]:
    hs = headings(md)
    for exact in (True, False):
        norm = (lambda s: s) if exact else (lambda s: re.sub(r"[*_`]", "", s).strip().casefold())
        hits = [h for h in hs if norm(h[2]) == norm(text)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise Fail(5, f"heading {text!r} occurs {len(hits)} times", candidates=[h[2] for h in hits])
    raise Fail(3, f"no heading {text!r}", headings=[h[2] for h in hs])


def section_span(md: str, heading: str, to_heading: str | None = None) -> tuple[int, int]:
    """Line range (start, end) of the body under a heading: after it, up to the next
    heading of the same or a higher level, or up to --to-heading."""
    lines = md.split("\n")
    i, level, _ = find_heading(md, heading)
    end = len(lines)
    if to_heading:
        j, _, _ = find_heading(md, to_heading)
        if j <= i:
            raise Fail(2, f"--to-heading {to_heading!r} comes before {heading!r}")
        end = j
    else:
        for j, lv, _ in headings(md):
            if j > i and lv <= level:
                end = j
                break
    return i + 1, end


def splice(md: str, start: int, end: int, block: str) -> str:
    """Lines start..end replaced by block, one blank line at each joint, nothing else touched."""
    lines = md.split("\n")
    head, tail = lines[:start], lines[end:]
    while head and not head[-1].strip():
        head.pop()
    while tail and not tail[0].strip():
        tail.pop(0)
    mid = block.strip("\n").split("\n") if block.strip() else []
    out = head + [""] + mid + ([""] if mid and tail else []) + tail
    return "\n".join(out).rstrip("\n") + "\n"


def tables(md: str) -> list[tuple[int, int]]:
    """(first line, last line + 1) of each Markdown table outside code blocks."""
    lines = md.split("\n")
    mask = code_mask(lines)
    out, i = [], 0
    while i < len(lines):
        if not mask[i] and lines[i].lstrip().startswith("|") and i + 1 < len(lines) and SEP_RE.match(lines[i + 1]):
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|") and not mask[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def split_cells(row: str) -> list[str]:
    s = row.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def join_cells(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def esc_cell(v: str) -> str:
    return re.sub(r"(?<!\\)\|", r"\\|", v.replace("\n", " ")).strip()


# ---------------------------------------------------------------- attachments

def is_att_line(line: str) -> re.Match | None:
    m = ATT_RE.match(line)
    if not m:
        return None
    target = m.group(3)
    if target.startswith("blobs/"):
        return m
    if re.match(r"^[a-z]+:", target):  # http, https, mailto: a link, not a file
        return None
    return m if Path(os.path.expanduser(target)).is_file() else None


def segments(md: str) -> list[tuple[str, object]]:
    """The text split at attachment lines: ("text", str) and ("att", {name, target})."""
    out, buf = [], []
    lines = md.split("\n")
    mask = code_mask(lines)
    for i, ln in enumerate(lines):
        m = None if mask[i] else is_att_line(ln)
        if m:
            if "\n".join(buf).strip():
                out.append(("text", "\n".join(buf).strip("\n") + "\n"))
            buf = []
            out.append(("att", {"name": m.group(2), "target": m.group(3), "image": bool(m.group(1))}))
        else:
            buf.append(ln)
    if "\n".join(buf).strip():
        out.append(("text", "\n".join(buf).strip("\n") + "\n"))
    return out


def resolve_atts(md: str, attached: list[tuple[str, str]]) -> str:
    """md with its attachment lines, in order, written as the blobs they became."""
    it = iter(attached)
    lines = md.split("\n")
    mask = code_mask(lines)
    out = []
    for i, ln in enumerate(lines):
        m = None if mask[i] else is_att_line(ln)
        if m:
            name, hsh = next(it)
            out.append(f"{m.group(1)}[{name}](blobs/{hsh})")
        else:
            out.append(ln)
    return "\n".join(out)


def placeholder_view(md: str) -> tuple[str, list[tuple[str, str]]]:
    """The text with each attachment line as a numbered placeholder, and the attachments."""
    lines = md.split("\n")
    mask = code_mask(lines)
    atts, out = [], []
    for i, ln in enumerate(lines):
        m = None if mask[i] else ATT_RE.match(ln)
        if m and m.group(3).startswith("blobs/"):
            atts.append((m.group(2), m.group(3)[len("blobs/"):]))
            out.append(f"HANJIATTACHMENT{len(atts)}")
        else:
            out.append(ln)
    return "\n".join(out), atts


# ---------------------------------------------------------------- the write path

class Note:
    def __init__(self, h: Hanji, ref: str):
        self.h = h
        self.id, self.title = resolve(h, ref)
        self.md = h.markdown(self.id)
        self.atts = h.attachments(self.id)
        self.backup: Path | None = None

    def make_backup(self) -> Path:
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        d = Path(tempfile.gettempdir()) / "hanji-backups" / self.id / stamp
        (d / "blobs").mkdir(parents=True, exist_ok=True)
        (d / "note.md").write_text(self.md)
        for a in self.atts:
            if a.get("path") and Path(a["path"]).is_file():
                shutil.copy2(a["path"], d / "blobs" / a["hash"])
        (d / "attachments.json").write_text(json.dumps(self.atts, indent=1))
        self.backup = d
        return d

    def source_for(self, target: str) -> tuple[str, str | None]:
        """A local file for an attachment line's target, and its mime when known."""
        if target.startswith("blobs/"):
            hsh = target[len("blobs/"):]
            meta = next((a for a in self.atts if a["hash"] == hsh), None)
            if self.backup and (self.backup / "blobs" / hsh).is_file():
                return str(self.backup / "blobs" / hsh), meta["mime"] if meta else None
            if meta and meta.get("path") and Path(meta["path"]).is_file():
                return meta["path"], meta["mime"]
            raise Fail(2, f"{target} is not an attachment of this note (note attachments lists them)")
        return os.path.expanduser(target), None

    def guard(self, base: str | None) -> None:
        now = self.h.markdown(self.id)
        if base and sha(now) != base:
            raise Fail(6, f"the note changed since it was read (sha {base}, now {sha(now)}): a second writer; "
                          f"read it again and redo the edit on the current text")
        if now != self.md:
            raise Fail(6, "the note changed while this edit ran: a second writer; read it again")

    def write(self, new_md: str, *, base: str | None = None, allow_drop: bool = False,
              dry_run: bool = False, append_only: str | None = None) -> dict:
        """Write new_md as the note's whole text (or, append_only, add that text at the end)."""
        segs = segments(append_only if append_only is not None else new_md)
        if append_only is None:
            if not segs or segs[0][0] != "text":
                raise Fail(2, "the note's first line is its title: put the title before any attachment")
            lost_h = list((Counter(t for _, _, t in headings(self.md)) - Counter(t for _, _, t in headings(new_md))).elements())
            lost_t = len(tables(self.md)) - len(tables(new_md))
            if (lost_h or lost_t > 0) and not allow_drop:
                what = " and ".join(([f"headings {lost_h}"] if lost_h else []) + ([f"{lost_t} table(s)"] if lost_t > 0 else []))
                raise Fail(2, f"the edit would remove {what} from the note; a section runs to the next "
                              f"heading of its level or higher, so check the span (skeleton shows the "
                              f"headings), or pass --allow-drop when that is intended",
                           lost_headings=lost_h, lost_tables=max(lost_t, 0))
            kept = {s[1]["target"][len("blobs/"):] for s in segs if s[0] == "att" and s[1]["target"].startswith("blobs/")}
            dropped = [a for a in self.atts if a["hash"] not in kept]
            inline = [a["name"] for a in dropped if f"blobs/{a['hash']}" in new_md]
            if inline and not allow_drop:
                raise Fail(2, f"attachments {inline} sit inside a table cell or a line with other text; "
                              f"the CLI places a file only on a line of its own, so rewriting this note "
                              f"would turn them into their names. Use append, or edit it in the app",
                           inline=inline)
            if dropped and not allow_drop:
                names = [a["name"] for a in dropped]
                raise Fail(2, f"the new text leaves out attachments {names}; keep their lines "
                              f"(as get prints them) or pass --allow-drop", dropped=names)
        plan = [("set" if append_only is None and k == 0 else ("attach" if s[0] == "att" else "append"),
                 s[1] if s[0] == "att" else s[1][:60]) for k, s in enumerate(segs)]
        if dry_run:
            return {"id": self.id, "title": self.title, "dry_run": True, "steps": plan,
                    "attachments_before": len(self.atts)}
        self.make_backup()
        self.guard(base)
        attached: list[tuple[str, str]] = []
        for k, (kind, val) in enumerate(segs):
            if kind == "text":
                if append_only is None and k == 0:
                    self.h("note", "set", self.id, "--stdin", "--format", "md", stdin=val)
                else:
                    self.h("note", "append", self.id, "--stdin", "--format", "md", stdin=val)
            else:
                src, mime = self.source_for(val["target"])
                name = val["name"] or Path(src).name
                args = ["note", "attach", self.id, src, "--name", name]
                if mime:
                    args += ["--mime", mime]
                r = self.h(*args)
                attached.append((name, r["hash"]))
        written = resolve_atts(append_only if append_only is not None else new_md, attached)
        intended = written if append_only is None else self.md.rstrip("\n") + "\n\n" + written
        return self.verify(intended)

    def verify(self, intended: str) -> dict:
        """The read-back equals intended (every attachment line as blobs/<hash>), compared
        after both pass through Hanji's own Markdown converter."""
        after = self.h.markdown(self.id)
        want_text, want_atts = placeholder_view(intended)
        got_text, got_atts = placeholder_view(after)
        want = canonical(want_text)
        ok = want.strip() == got_text.strip() and want_atts == got_atts
        res = {"id": self.id, "title": after.split("\n", 1)[0].lstrip("# ").strip(), "verified": ok,
               "sha": sha(after), "attachments": len(got_atts), "backup": str(self.backup)}
        if not ok:
            diff = "\n".join(difflib.unified_diff(want.strip().split("\n"), got_text.strip().split("\n"),
                                                  "intended", "read back", lineterm=""))
            if want_atts != got_atts:
                diff += f"\nattachments intended {want_atts}\nattachments read back {got_atts}"
            raise Fail(4, "the read-back differs from the intended text", diff=diff, backup=str(self.backup),
                       restore=f"hanji_note.py write {self.id} --file {self.backup}/note.md --allow-drop")
        return res


def resolve(h: Hanji, ref: str) -> tuple[str, str]:
    if ID_RE.match(ref):
        row = h("note", "get", ref)
        return row["id"], row["title"]
    notes = h.live_notes()
    for exact in (True, False):
        norm = (lambda s: s) if exact else (lambda s: " ".join(s.split()).casefold())
        hits = [n for n in notes if norm(n["title"]) == norm(ref)]
        if len(hits) == 1:
            return hits[0]["id"], hits[0]["title"]
        if len(hits) > 1:
            raise Fail(5, f"{len(hits)} notes are titled {ref!r}",
                       candidates=[{"id": n["id"], "title": n["title"], "notebook": n["notebook_name"],
                                    "updated": n["updated"]} for n in hits])
    words = [n for n in notes if all(w.casefold() in n["title"].casefold() for w in ref.split())]
    raise Fail(3, f"no note titled {ref!r}",
               candidates=[{"id": n["id"], "title": n["title"], "notebook": n["notebook_name"]} for n in words[:20]])


def read_text(a) -> str:
    if getattr(a, "file", None):
        return Path(a.file).read_text()
    if getattr(a, "stdin", False):
        return sys.stdin.read()
    if getattr(a, "text", None) is not None:
        return a.text
    raise Fail(2, "give the text with --file, --stdin or --text")


# ---------------------------------------------------------------- commands

def cmd_find(h, a):
    nid, title = resolve(h, a.title)
    row = h("note", "get", nid)
    return {"id": nid, "title": title, "notebook": row["notebook_name"], "tags": row["tags"]}


def cmd_get(h, a):
    nid, title = resolve(h, a.note)
    if a.format != "md" or a.at:
        args = ["note", "get", nid, "--format", a.format] + (["--at", a.at] if a.at else [])
        r = h(*args)
        body = r.get("markdown") or r.get("html") or r.get("text", "")
    else:
        r = h("note", "get", nid, "--format", "md")
        body = r["markdown"]
    if a.json:
        return {"id": nid, "title": title, "notebook": r["notebook_name"], "tags": r["tags"],
                "updated": r["updated"], "sha": sha(body), a.format if a.format != "text" else "text": body}
    sys.stdout.write(body)
    print(f"sha: {sha(body)}  id: {nid}", file=sys.stderr)
    return None


def cmd_skeleton(h, a):
    n = Note(h, a.note)
    lines = n.md.split("\n")
    return {"id": n.id, "title": n.title, "sha": sha(n.md), "chars": len(n.md),
            "headings": [f"{'#' * lv} {t}" for _, lv, t in headings(n.md)],
            "tables": [{"index": k, "rows": e - s - 2, "cols": len(split_cells(lines[s])),
                        "header": split_cells(lines[s])} for k, (s, e) in enumerate(tables(n.md))],
            "attachments": [{"name": x["name"], "hash": x["hash"], "mime": x["mime"]} for x in n.atts]}


def cmd_search(h, a):
    rows = h("search", a.query, "--limit", str(a.limit))
    if a.notebook:
        nb = {n["id"]: n["notebook_name"] for n in h.live_notes()}
        rows = [r for r in rows if nb.get(r["id"]) == a.notebook]
    return rows


def cmd_create(h, a):
    md = read_text(a)
    if a.title:
        first = md.lstrip("\n").split("\n", 1)[0]
        m = HEADING_RE.match(first)
        if not (m and m.group(2) == a.title):
            md = f"# {a.title}\n\n{md.lstrip()}"
    nbs = h("notebook", "list")
    if not any(a.notebook in (nb["name"], nb["id"]) for nb in nbs):
        raise Fail(3, f"no notebook {a.notebook!r}", notebooks=[nb["name"] for nb in nbs])
    segs = segments(md)
    if not segs or segs[0][0] != "text":
        raise Fail(2, "the note's first line is its title: put the title before any attachment")
    for kind, val in segs:
        if kind == "att" and val["target"].startswith("blobs/"):
            raise Fail(2, f"{val['target']}: a new note takes files by their local path")
    if a.dry_run:
        return {"dry_run": True, "notebook": a.notebook, "steps": [s[0] for s in segs]}
    lines = md.split("\n")
    mask = code_mask(lines)
    cut = next((i for i, ln in enumerate(lines) if not mask[i] and is_att_line(ln)), len(lines))
    head, rest = "\n".join(lines[:cut]).strip("\n") + "\n", "\n".join(lines[cut:]).strip("\n")
    args = ["note", "create", "--notebook", a.notebook, "--stdin", "--format", "md"]
    for t in a.tag or []:
        args += ["--tag", t]
    nid = h(*args, stdin=head)["id"]
    n = Note(h, nid)
    n.backup = None
    res = n.write(None, append_only=rest + "\n") if rest else n.verify(head)
    res["created"] = True
    return res


def cmd_write(h, a):
    n = Note(h, a.note)
    return n.write(read_text(a), base=a.base, allow_drop=a.allow_drop, dry_run=a.dry_run)


def cmd_append(h, a):
    n = Note(h, a.note)
    return n.write(None, append_only=read_text(a).strip("\n") + "\n", dry_run=a.dry_run)


def cmd_replace_section(h, a):
    n = Note(h, a.note)
    s, e = section_span(n.md, a.heading, a.to_heading)
    return n.write(splice(n.md, s, e, read_text(a)), dry_run=a.dry_run, allow_drop=a.allow_drop)


def cmd_insert_after_heading(h, a):
    n = Note(h, a.note)
    i, _, _ = find_heading(n.md, a.heading)
    return n.write(splice(n.md, i + 1, i + 1, read_text(a)), dry_run=a.dry_run, allow_drop=a.allow_drop)


def _table(n: Note, k: int) -> tuple[list[str], int, int]:
    ts = tables(n.md)
    if k >= len(ts):
        raise Fail(3, f"the note has {len(ts)} tables; --table {k} is not one (0 is the first)")
    s, e = ts[k]
    return n.md.split("\n"), s, e


def cmd_add_row(h, a):
    n = Note(h, a.note)
    lines, s, e = _table(n, a.table)
    cols = len(split_cells(lines[s]))
    cells = [esc_cell(c) for c in a.row.split(a.sep)]
    if len(cells) != cols:
        raise Fail(2, f"the table has {cols} columns, the row {len(cells)}", header=split_cells(lines[s]))
    new = lines[:e] + [join_cells(cells)] + lines[e:]
    return n.write("\n".join(new), dry_run=a.dry_run, allow_drop=a.allow_drop)


def cmd_update_cell(h, a):
    n = Note(h, a.note)
    lines, s, e = _table(n, a.table)
    rows = [s] + list(range(s + 2, e))  # row 0 is the header; the separator line is not a row
    if a.row >= len(rows):
        raise Fail(3, f"the table has rows 0 to {len(rows) - 1} (0 is the header)")
    li = rows[a.row]
    cells = split_cells(lines[li])
    if a.col >= len(cells):
        raise Fail(3, f"the table has columns 0 to {len(cells) - 1}")
    cells[a.col] = esc_cell(a.value)
    lines[li] = join_cells(cells)
    return n.write("\n".join(lines), dry_run=a.dry_run, allow_drop=a.allow_drop)


def cmd_create_table(h, a):
    n = Note(h, a.note)
    head = [esc_cell(c) for c in a.headers.split(a.sep)]
    rows = [[esc_cell(c) for c in r.split(a.sep)] for r in a.rows.split(";")] if a.rows else []
    for r in rows:
        if len(r) != len(head):
            raise Fail(2, f"a row has {len(r)} cells, the header {len(head)}: {r}")
    block = "\n".join([join_cells(head), join_cells(["---"] * len(head))] + [join_cells(r) for r in rows])
    if a.after_heading:
        i, _, _ = find_heading(n.md, a.after_heading)
        return n.write(splice(n.md, i + 1, i + 1, block), dry_run=a.dry_run, allow_drop=a.allow_drop)
    return n.write(None, append_only=block + "\n", dry_run=a.dry_run)


def cmd_embed(h, a):
    n = Note(h, a.note)
    f = Path(os.path.expanduser(a.file))
    if not f.is_file():
        raise Fail(3, f"no file {f}")
    for x in n.atts:
        if x.get("path") and x["size"] == f.stat().st_size and filecmp.cmp(x["path"], f, shallow=False):
            return {"id": n.id, "title": n.title, "already": True, "name": x["name"], "hash": x["hash"]}
    name = a.name or f.name
    line = f"![{name}]({f})"
    if not a.top and not a.after_heading:
        return n.write(None, append_only=line + "\n", dry_run=a.dry_run)
    if a.top:
        at = 1  # directly under the title line, above every section
    else:
        at = find_heading(n.md, a.after_heading)[0] + 1
    return n.write(splice(n.md, at, at, line), dry_run=a.dry_run, allow_drop=a.allow_drop)


def cmd_delete(h, a):
    nid, title = resolve(h, a.note)
    if a.dry_run:
        return {"id": nid, "title": title, "dry_run": True, "permanent": a.permanent}
    h("note", "delete", nid)
    if a.permanent:
        h("note", "purge", nid)
    return {"id": nid, "title": title, "trashed": not a.permanent, "purged": a.permanent}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hanji_note.py", description=__doc__.split("\n\n")[0])
    p.add_argument("--db", help="database file (tests, a copy); default the desktop app's")
    p.add_argument("--profile", help="an isolated local store (hanji --profile)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def text_args(sp):
        g = sp.add_mutually_exclusive_group()
        g.add_argument("--file")
        g.add_argument("--stdin", action="store_true")
        g.add_argument("--text")

    def dry(sp):
        sp.add_argument("--dry-run", action="store_true")
        if not any(o.dest == "allow_drop" for o in sp._actions):
            sp.add_argument("--allow-drop", action="store_true",
                            help="let headings, tables or attachments the edit removes leave the note")

    sp = sub.add_parser("find", help="exact title -> id (exit 5 several, 3 none)")
    sp.add_argument("title")
    sp = sub.add_parser("get", help="a note's Markdown (title or id)")
    sp.add_argument("note")
    sp.add_argument("--format", choices=["md", "text", "html"], default="md")
    sp.add_argument("--at", help="the text as it was at VERSION (hanji note versions)")
    sp.add_argument("--json", action="store_true")
    sp = sub.add_parser("skeleton", help="headings, tables, attachments, length")
    sp.add_argument("note")
    sp = sub.add_parser("search", help="full-text search, best first")
    sp.add_argument("query")
    sp.add_argument("--notebook")
    sp.add_argument("--limit", type=int, default=20)
    sp = sub.add_parser("create", help="a new note from Markdown; local image paths are attached in place")
    sp.add_argument("--notebook", required=True)
    sp.add_argument("--title")
    sp.add_argument("--tag", action="append")
    text_args(sp), dry(sp)
    sp = sub.add_parser("write", help="replace the whole text, attachments kept where their lines stand")
    sp.add_argument("note")
    sp.add_argument("--base", help="sha the text was based on (get prints it); refuses if the note changed")
    text_args(sp), dry(sp)
    sp = sub.add_parser("append", help="add Markdown at the end")
    sp.add_argument("note")
    text_args(sp), dry(sp)
    sp = sub.add_parser("replace-section", help="replace the body under a heading")
    sp.add_argument("note")
    sp.add_argument("heading")
    sp.add_argument("--to-heading")
    text_args(sp), dry(sp)
    sp = sub.add_parser("insert-after-heading", help="insert Markdown directly under a heading")
    sp.add_argument("note")
    sp.add_argument("heading")
    text_args(sp), dry(sp)
    sp = sub.add_parser("add-row", help="add a row to the Nth table (0 is the first)")
    sp.add_argument("note")
    sp.add_argument("row", help="cells separated by --sep (,)")
    sp.add_argument("--table", type=int, default=0)
    sp.add_argument("--sep", default=",")
    dry(sp)
    sp = sub.add_parser("update-cell", help="set one cell; row 0 is the header, col 0 the first")
    sp.add_argument("note")
    sp.add_argument("row", type=int)
    sp.add_argument("col", type=int)
    sp.add_argument("value")
    sp.add_argument("--table", type=int, default=0)
    dry(sp)
    sp = sub.add_parser("create-table", help="a Markdown table under a heading or at the end")
    sp.add_argument("note")
    sp.add_argument("--headers", required=True)
    sp.add_argument("--rows", help="rows separated by ;, cells by --sep")
    sp.add_argument("--sep", default=",")
    sp.add_argument("--after-heading")
    dry(sp)
    sp = sub.add_parser("embed-image", help="attach a file at the end, under the title (--top) or a heading")
    sp.add_argument("note")
    sp.add_argument("file")
    sp.add_argument("--name")
    g = sp.add_mutually_exclusive_group()
    g.add_argument("--top", action="store_true")
    g.add_argument("--after-heading")
    dry(sp)
    sp = sub.add_parser("delete", help="move the note to the trash (--permanent: for good)")
    sp.add_argument("note")
    sp.add_argument("--permanent", action="store_true")
    dry(sp)
    return p


COMMANDS = {"find": cmd_find, "get": cmd_get, "skeleton": cmd_skeleton, "search": cmd_search,
            "create": cmd_create, "write": cmd_write, "append": cmd_append,
            "replace-section": cmd_replace_section, "insert-after-heading": cmd_insert_after_heading,
            "add-row": cmd_add_row, "update-cell": cmd_update_cell, "create-table": cmd_create_table,
            "embed-image": cmd_embed, "delete": cmd_delete}


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    h = Hanji(a.db, a.profile)
    try:
        res = COMMANDS[a.cmd](h, a)
    except Fail as e:
        print(json.dumps({"error": str(e), **e.extra}, ensure_ascii=False, indent=1), file=sys.stderr)
        return e.code
    if res is not None:
        print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
