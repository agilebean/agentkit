#!/usr/bin/env python3
"""Write Chaehan's travel dates and bookings into travel.md, travelitinerary.csv and the yearly
Evernote itinerary notes, so the three records carry the same rows.

The agent (DeepSeek in opencode) reads the message or the booking note and writes events.json.
This script plans every change. The two local files are written by the script itself; each
Evernote note is changed by `edit_note` replacements that the agent's one `execute` call fetches
from this script over localhost, so the notes' markup never passes through the model.

    itinerary_sync.py start EVENTS.json [--repo DIR] [--dry-run]   # validate, serve, print the execute code
    itinerary_sync.py plan EVENTS.json --enml GUID=FILE ... [--repo DIR] [--out DIR]   # offline test
    itinerary_sync.py serve EVENTS.json --port N [--repo DIR] [--dry-run]   # started by `start`

Standard library only. Exit 2 on invalid events (the errors say what to fix).
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import socket
import subprocess
import sys
import unicodedata
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path.home() / "Software" / "Prototypes" / "socrates"
TRANSPORT = {"flight": "Flight ✅", "train": "Zug ✅", "bus": "Bus ✅", "ferry": "Ferry ✅"}
STAY = {"hotel": "Hotel ✅", "apartment": "Apt ✅"}
KINDS = set(TRANSPORT) | set(STAY) | {"car", "dates"}
DEFAULT_RATE = 1.17  # $/€, the rate in Chaehan's 2026 itinerary header
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
GREEN = "color:rgb(24, 168, 65);--inversion-type-color:simple;"
MARK_DIV = '<div><b><span style="' + GREEN + '">{}</span></b></div>'
LINK_DIV = ('<div><a type="inline-richlink" rev="{{&quot;isCached&quot;:false}}" '
            'href="evernote:///view/60632948/s365/{g}/{g}/">{t}</a></div>')
NUM_DIV = '<div style="text-align:right;">{}</div>'
GENERIC = {"hotel", "the", "le", "la", "el", "apartment", "apartments", "hostal", "hostel", "casa", "air"}


# ---------------------------------------------------------------- events

def day(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def norm(city: str) -> str:
    s = unicodedata.normalize("NFKD", city or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def same_city(a: str, b: str) -> bool:
    a, b = norm(a), norm(b)
    if not a or not b:
        return False
    return a == b or (min(len(a), len(b)) >= 3 and (a.startswith(b) or b.startswith(a)))


def validate(data: dict) -> list[str]:
    errs: list[str] = []
    evs = data.get("events") if isinstance(data, dict) else None
    if not isinstance(evs, list) or not evs:
        return ['events.json must be {"events": [ ... ]} with at least one event']
    today = dt.date.today()
    for i, e in enumerate(evs):
        p = f"event {i + 1}"
        k = e.get("kind")
        if k not in KINDS:
            errs.append(f"{p}: kind must be one of {sorted(KINDS)}, not {k!r}")
            continue
        need = {"dates": ["city", "date"], "car": ["city", "checkin"]}.get(k)
        if need is None:
            need = ["from", "to", "depart", "arrive"] if k in TRANSPORT else ["city", "checkin", "checkout"]
        for f in need:
            if not e.get(f):
                errs.append(f"{p} ({k}): '{f}' is missing; a transport needs from, to, depart and arrive "
                            "(arrive is the local landing day, the day after depart for an overnight flight); "
                            "if the source does not give it, ask Chaehan")
        for f in ("date", "depart", "arrive", "checkin", "checkout"):
            if e.get(f):
                try:
                    d = day(e[f])
                    if not (today - dt.timedelta(days=500) <= d <= today + dt.timedelta(days=900)):
                        errs.append(f"{p}: {f} {e[f]} is outside the planning window")
                except ValueError:
                    errs.append(f"{p}: {f} must be YYYY-MM-DD, not {e[f]!r}")
        if e.get("depart") and e.get("arrive") and DATE.fullmatch(e["depart"]) and DATE.fullmatch(e["arrive"]) \
                and day(e["arrive"]) < day(e["depart"]):
            errs.append(f"{p}: arrive {e['arrive']} is before depart {e['depart']}")
        if e.get("price") is not None and not isinstance(e["price"], (int, float)):
            errs.append(f"{p}: price must be a number (no currency sign, no separators)")
        if e.get("price") is not None and not e.get("currency"):
            errs.append(f"{p}: price needs currency (EUR, KRW, JPY, AUD, ...)")
        if e.get("note_guid") and not UUID.match(e["note_guid"]):
            errs.append(f"{p}: note_guid must be the booking note's guid")
        if e.get("note_guid") and not e.get("note_title"):
            errs.append(f"{p}: note_title (the booking note's exact title) is missing")
        if "legs" in e and "split" not in e:
            e["split"] = e.pop("legs")  # the key's first name, 2026-11-07
        if not isinstance(e.get("split", 1), int) or e.get("split", 1) < 1:
            errs.append(f"{p}: split is the number of flights on one ticket, an integer >= 1")
    return errs


@dataclass
class Target:
    date: dt.date
    city: str
    kind: str
    marker: str | None
    guid: str | None
    title: str | None
    text: str | None
    eur: int | None
    orig: str | None
    provider: str | None
    ref: str | None
    price_words: list[str] = field(default_factory=list)
    nights: int | None = None


def fx_to_eur(amount: float, cur: str) -> float | None:
    cur = cur.upper()
    if cur in ("EUR", "€"):
        return amount
    try:
        url = f"https://api.frankfurter.dev/v1/latest?base={cur}&symbols=EUR"
        with urllib.request.urlopen(url, timeout=10) as r:
            return amount * json.load(r)["rates"]["EUR"]
    except Exception:
        return None


def targets(events: list[dict], warn: list[str]) -> list[Target]:
    out: list[Target] = []
    for e in events:
        k = e["kind"]
        share = None
        if e.get("price") is not None:
            share = e["price"] / e.get("split", 1)
        eur = None
        if share is not None:
            v = fx_to_eur(share, e["currency"])
            if v is None:
                warn.append(f"{e.get('note_title') or k}: no € rate for {e['currency']}, so its € cell stays empty")
            else:
                eur = round(v)
        orig = None
        if share is not None and e["currency"].upper() not in ("EUR", "€"):
            orig = f"{e['currency'].upper()} {round(share)}"
        words = [w for w in (str(round(e["price"])) if e.get("price") is not None else "", e.get("ref") or "") if w]
        common = dict(kind=k, guid=e.get("note_guid"), title=e.get("note_title"), text=e.get("text"),
                      eur=eur, orig=orig, provider=e.get("provider"), ref=e.get("ref"), price_words=words)
        if k in TRANSPORT:
            out.append(Target(date=day(e["arrive"]), city=e["to"], marker=TRANSPORT[k], **common))
        elif k in STAY:
            t = Target(date=day(e["checkin"]), city=e["city"], marker=STAY[k], **common)
            t.nights = (day(e["checkout"]) - day(e["checkin"])).days
            out.append(t)
        elif k == "car":
            out.append(Target(date=day(e["checkin"]), city=e["city"], marker="RentalCar ✅", **common))
        else:
            out.append(Target(date=day(e["date"]), city=e["city"], marker=None, **common))
    out.sort(key=lambda t: t.date)
    return out


# ---------------------------------------------------------------- generic rows

@dataclass
class Row:
    date: dt.date
    city: str
    ref: object  # the record's own handle
    orig_date: dt.date | None = None
    new: bool = False
    changed: bool = False
    nights: int | None = None  # a stay's own length, kept when it ends before the next row


def match(rows: list[Row], t: Target) -> Row | None:
    rows = sorted(rows, key=lambda r: r.date)
    same = [r for r in rows if same_city(r.city, t.city)]
    for r in same:
        nxt = next((x.date for x in rows if x.date > r.date), dt.date.max)
        if r.date <= t.date < nxt:
            return r
    if t.kind == "car" or not same:
        return None
    best = min(same, key=lambda r: abs((r.date - t.date).days))
    return best if abs((best.date - t.date).days) <= 31 else None


# ---------------------------------------------------------------- CSV

def load_csv(path: Path) -> list[Row]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            d, c = line.split(",", 1)
            rows.append(Row(day(d.strip()), c.strip(), None))
    return rows


def dump_csv(rows: list[Row]) -> str:
    return "date,city\n" + "".join(f"{r.date},{r.city}\n" for r in sorted(rows, key=lambda r: r.date))


# ---------------------------------------------------------------- travel.md schedule tables

SECTION = re.compile(r"^## (\d{4}) schedule.*$", re.M)
GUIDS = re.compile(r"(\d{4}) Travel Itinerary `([0-9a-f-]{36})`")


@dataclass
class MdTable:
    year: int
    start: int  # index of the first table line in the file's line list
    end: int
    header: list[str]
    rows: list[Row]


def load_md(lines: list[str]) -> list[MdTable]:
    tables = []
    for i, line in enumerate(lines):
        m = SECTION.match(line)
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].startswith("|"):
            if lines[j].startswith("## "):
                break
            j += 1
        if j >= len(lines) or not lines[j].startswith("|"):
            continue
        k = j
        while k < len(lines) and lines[k].startswith("|"):
            k += 1
        rows = []
        for n in range(j + 2, k):
            cells = [c.strip() for c in lines[n].strip().strip("|").split("|")]
            cells += [""] * (3 - len(cells))
            if cells and DATE.fullmatch(cells[0]):
                rows.append(Row(day(cells[0]), cells[1].split("→")[-1].strip(), cells))
        tables.append(MdTable(int(m.group(1)), j, k, lines[j:j + 2], rows))
    return tables


def pick_md(tables: list[MdTable], d: dt.date) -> MdTable | None:
    fits = [t for t in tables if t.year >= d.year and t.rows and min(r.date for r in t.rows) <= d]
    if fits:
        return max(fits, key=lambda t: t.year)
    return next((t for t in tables if t.year == d.year), None)


# ---------------------------------------------------------------- Evernote ENML

TABLE = re.compile(r"<table\b.*?</table>", re.S)
TR = re.compile(r"<tr\b[^>]*>.*?</tr>", re.S)
CELL = re.compile(r"(<t[dh]\b[^>]*>)(.*?)(</t[dh]>)", re.S)
H2 = re.compile(r"<h2\b[^>]*>.*?</h2>", re.S)
FORMULA = re.compile(r"€\s*(\d+(?:\s*\+\s*\d+)*)\s*=\s*(\d+)")


def text(inner: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", inner))).strip()


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
    if isinstance(obj, dict):
        for v in obj.values():
            r = find_enml(v)
            if r:
                return r
    if isinstance(obj, list):
        for v in obj:
            r = find_enml(v)
            if r:
                return r
    return None


@dataclass
class NoteRow:
    tr: str
    cells: list[list[str]]  # [open, inner, close]

    def build(self) -> str:
        head = re.match(r"<tr\b[^>]*>", self.tr).group(0)
        return head + "".join("".join(c) for c in self.cells) + "</tr>"


class Note:
    def __init__(self, guid: str, year: int, enml: str):
        self.guid, self.year, self.enml = guid, year, enml
        tables = [t for t in TABLE.findall(enml) if "Details" in text(t)]
        if not tables:
            raise ValueError(f"note {guid}: no itinerary table (a table with a Details column)")
        self.table = tables[0]
        trs = TR.findall(self.table)
        self.header = [text(c[1]) for c in CELL.findall(trs[0])]
        self.col = {}
        for name in ("Date", "City", "Temp", "Details", "Orig", "€", "$"):
            self.col[name] = next((i for i, h in enumerate(self.header) if name.lower() in h.lower()), None)
        self.rows: list[Row] = []
        for tr in trs[1:]:
            cells = [list(c) for c in CELL.findall(tr)]
            if not cells:
                continue
            m = DATE.search(text(cells[0][1]))
            if not m:
                continue
            city_cell = text(cells[self.col["City"]][1]) if self.col["City"] is not None else ""
            city = re.match(r"\s*([^\d(✅/€$]*)", city_cell).group(1).strip(" ,") or city_cell
            self.rows.append(Row(day(m.group(0)), city, NoteRow(tr, cells), orig_date=day(m.group(0))))
        self.inserted: list[tuple[Row, Row | None]] = []  # (new row, anchor row it follows)
        self.added_eur: list[int] = []
        h2 = H2.search(enml)
        self.h2 = h2.group(0) if h2 else None
        rate = re.search(r"\$/€\s*=\s*([\d.]+)", text(self.h2 or ""))
        self.rate = float(rate.group(1)) if rate else DEFAULT_RATE

    def booked(self, r: Row) -> bool:
        return "✅" in text(r.ref.cells[0][1])

    def cell(self, r: Row, name: str) -> list[str] | None:
        i = self.col.get(name)
        return r.ref.cells[i] if i is not None and i < len(r.ref.cells) else None


def divs(inner: str) -> str:
    """The cell's content as div lines, a placeholder '/' or emptiness dropped."""
    if text(inner) in ("", "/"):
        return ""
    return inner if "<div" in inner else f"<div>{inner}</div>"


def set_date(cell: list[str], new: dt.date) -> None:
    wd = WEEKDAYS[new.weekday()]
    inner = cell[1]
    pat = re.compile(r"\d{4}-\d{2}-\d{2}(?:\s*(?:MON|TUE|WED|THU|FRI|SAT|SUN)\b)?")
    inner = pat.sub(f"{new} {wd}", inner, count=1)
    cell[1] = inner


def add_marker(cell: list[str], marker: str, provider: str | None) -> bool:
    t = text(cell[1])
    word = (provider or "").split()[0].lower() if provider else ""
    if marker.split()[0].lower() in t.lower() or (word and re.search(rf"\b{re.escape(word)}\b[^✅]*✅", t.lower())):
        return False
    cell[1] = divs(cell[1]) + MARK_DIV.format(html.escape(marker, quote=False))
    return True


def nights_token(n: int) -> str:
    return f"{n}d" if n < 14 else f"{round(n / 7)}w"


# ---------------------------------------------------------------- the plan

class Plan:
    def __init__(self, events: list[dict], repo: Path, notes: dict[str, str] | None):
        self.repo = repo
        self.warn: list[str] = []
        self.asks: list[str] = []
        self.log: dict[str, list[str]] = {"travelitinerary.csv": [], "travel.md": []}
        self.csv_path = repo / "memory" / "travelitinerary.csv"
        self.md_path = repo / "memory" / "travel.md"
        self.csv_rows = load_csv(self.csv_path)
        self.md_lines = self.md_path.read_text(encoding="utf-8").split("\n")
        self.md_tables = load_md(self.md_lines)
        self.note_ids = {int(y): g for y, g in GUIDS.findall("\n".join(self.md_lines))}
        self.targets = targets(events, self.warn)
        self.notes: dict[int, Note] = {}
        for y, g in self.note_ids.items():
            if notes and g in notes:
                self.notes[y] = Note(g, y, notes[g])
                self.log[f"{y} itinerary note"] = []

    def needed_notes(self) -> dict[int, str]:
        years = set()
        for t in self.targets:
            years |= {t.date.year, t.date.year + 1}
        return {y: g for y, g in self.note_ids.items() if y in years}

    def notes_for(self, d: dt.date) -> list[Note]:
        out = []
        for y in (d.year, d.year + 1):
            n = self.notes.get(y)
            if n and (y == d.year or (n.rows and min(r.date for r in n.rows) <= d)):
                out.append(n)
        return out

    # one target across the records
    def run(self) -> None:
        for y in {t.date.year for t in self.targets} | {t.date.year + 1 for t in self.targets}:
            if y in self.needed_notes() and y not in self.notes:
                self.warn.append(f"the {y} itinerary note was not read")
        for t in self.targets:
            primary = self.notes.get(t.date.year)
            prow = match(primary.rows, t) if primary else None
            booked = bool(prow and primary.booked(prow))
            move = t.kind != "car" and not booked
            label = t.title or t.text or f"{t.kind} {t.city} {t.date}"
            if booked and prow.date != t.date and t.kind in TRANSPORT:
                self.asks.append(f"{label}: lands {t.date} in {t.city}, but the booked {prow.city} row starts "
                                 f"{prow.date}; the row keeps its date, ask Chaehan which is right")
            if t.kind == "dates" and booked and prow.date != t.date:
                self.asks.append(f"Chaehan's date {t.date} for {t.city} differs from the booked row {prow.date}; "
                                 "the row keeps its booked date, ask him")
            self.apply_csv(t, move)
            self.apply_md(t, move, label)
            for n in self.notes_for(t.date):
                self.apply_note(n, t, move, label)
        for n in self.notes.values():
            self.durations(n)
            self.header(n)

    def apply_csv(self, t: Target, move: bool) -> None:
        log = self.log["travelitinerary.csv"]
        r = match(self.csv_rows, t)
        if r is None:
            if t.kind == "car":
                return
            self.csv_rows.append(Row(t.date, t.city, None, new=True, changed=True))
            log.append(f"added {t.date},{t.city}")
            nxt = min((x.date for x in self.csv_rows if x.date > t.date), default=None)
            if t.nights and nxt and (t.date + dt.timedelta(days=t.nights)) < nxt:
                end = t.date + dt.timedelta(days=t.nights)
                self.asks.append(f"{t.title or t.text or t.city}: the stay ends {end}, before the next row "
                                 f"({nxt}); ask Chaehan where he is from {end}")
        elif move and r.date != t.date:
            log.append(f"{r.city} {r.date} -> {t.date}")
            r.date, r.changed = t.date, True

    def apply_md(self, t: Target, move: bool, label: str) -> None:
        log = self.log["travel.md"]
        tab = pick_md(self.md_tables, t.date)
        if tab is None:
            self.asks.append(f"travel.md has no '## {t.date.year} schedule' table for {label}; ask Chaehan "
                             "whether to start one")
            return
        r = match(tab.rows, t)
        if r is None:
            if t.kind == "car":
                self.warn.append(f"{label}: no travel.md row covers {t.date} in {t.city}")
                return
            prev = max((x for x in tab.rows if x.date < t.date), key=lambda x: x.date, default=None)
            nxt = min((x for x in tab.rows if x.date > t.date), key=lambda x: x.date, default=None)
            move_text = f"{prev.city} → {t.city}" if prev else f"→ {t.city}"
            note = f"Booked: {t.title}." if t.title else (t.text or "")
            tab.rows.append(Row(t.date, t.city, [str(t.date), move_text, note], new=True, changed=True))
            if nxt is not None and prev is not None and "→" in nxt.ref[1]:
                a, b = nxt.ref[1].split("→", 1)
                if same_city(a, prev.city):
                    nxt.ref[1] = f"{t.city} →{b}"
                    nxt.changed = True
            log.append(f"added {t.date} {move_text}")
            return
        if move and r.date != t.date:
            log.append(f"{r.city} {r.date} -> {t.date}")
            r.date, r.changed = t.date, True
            r.ref[0] = str(t.date)
        if t.title and t.title not in r.ref[2]:
            head = r.ref[2].rstrip()
            if head and not head.endswith((".", "!", "?")):
                head += "."
            r.ref[2] = (head + f" Booked: {t.title}.").strip()
            r.changed = True
            log.append(f"{r.city} {r.date}: noted {t.title}")

    def apply_note(self, n: Note, t: Target, move: bool, label: str) -> None:
        log = self.log[f"{n.year} itinerary note"]
        r = match(n.rows, t)
        if r is None:
            if t.kind == "car":
                self.warn.append(f"{label}: no row in the {n.year} note covers {t.date} in {t.city}")
                return
            anchor = max((x for x in n.rows if x.date < t.date), key=lambda x: x.date, default=None)
            r = self.new_note_row(n, t, anchor)
            log.append(f"added row {t.date} {t.city}")
        elif move and r.date != t.date:
            set_date(r.ref.cells[0], t.date)
            log.append(f"{r.city} {r.date} -> {t.date}")
            r.date, r.changed = t.date, True
            for row in (r, self.prev_row(n, r)):
                if row is not None:
                    det = n.cell(row, "Details")
                    prose = text(re.sub(r"<a\b.*?</a>", " ", det[1], flags=re.S)) if det else ""
                    old = r.orig_date
                    for s in sorted({str(old), old.strftime("%m-%d")}, key=len, reverse=True):
                        if s in prose:
                            self.warn.append(f"{n.year} note, {row.city} row: its Details text still says "
                                             f"'{s}'; the text is Chaehan's to change")
                            break
        cells = r.ref.cells
        if t.marker and add_marker(cells[0], t.marker, t.provider):
            r.changed = True
        det = n.cell(r, "Details")
        rowtext = text(r.ref.build())
        if t.guid and det is not None and t.guid not in r.ref.build():
            det[1] = divs(det[1]) + LINK_DIV.format(g=t.guid, t=html.escape(t.title, quote=False))
            r.changed = True
            log.append(f"{r.city} {r.date}: linked {t.title}")
        elif t.kind != "dates" and not t.guid and t.text and det is not None and t.text not in rowtext:
            det[1] = divs(det[1]) + f"<div>{html.escape(t.text, quote=False)}</div>"
            r.changed = True
            log.append(f"{r.city} {r.date}: noted {t.text}")
        word = (t.provider or "").split()[0] if t.provider else ""
        costed = any(w and w in rowtext for w in t.price_words) or bool(
            len(word) >= 3 and word.lower() not in GENERIC and re.search(rf"\b{re.escape(word)}\b", rowtext, re.I))
        if t.eur is not None and n.year == t.date.year and not costed and not (t.guid and t.guid in r.ref.tr):
            for name, val in (("€", t.eur), ("$", round(t.eur * n.rate)), ("Orig", t.orig)):
                c = n.cell(r, name)
                if c is not None and val is not None:
                    c[1] = divs(c[1]) + (NUM_DIV.format(val) if name != "Orig" else f"<div>{html.escape(val)}</div>")
            n.added_eur.append(t.eur)
            r.changed = True
            log.append(f"{r.city} {r.date}: €{t.eur}")
        elif t.eur is not None and costed and n.year == t.date.year:
            log.append(f"{r.city} {r.date}: € already in the row for {label}, not added again")
        if r.changed and not re.search(r"\b(?:MON|TUE|WED|THU|FRI|SAT|SUN)\b", text(cells[0][1])):
            set_date(cells[0], r.date)

    def prev_row(self, n: Note, r: Row) -> Row | None:
        return max((x for x in n.rows if x.date < r.date), key=lambda x: x.date, default=None)

    def new_note_row(self, n: Note, t: Target, anchor: Row | None) -> Row:
        model = (anchor or n.rows[0]).ref.cells
        cells = [[c[0], "", c[2]] for c in model]
        wd = WEEKDAYS[t.date.weekday()]
        cells[0][1] = f"<div>{t.date} {wd}</div>"
        if n.col["City"] is not None:
            tok = f" {nights_token(t.nights)}" if t.nights else ""
            cells[n.col["City"]][1] = f"<div>{html.escape(t.city)}{tok}</div>"
        head = re.match(r"<tr\b[^>]*>", model and (anchor or n.rows[0]).ref.tr).group(0)
        nr = NoteRow(head + "</tr>", cells)
        row = Row(t.date, t.city, nr, orig_date=None, new=True, changed=True, nights=t.nights)
        n.rows.append(row)
        n.inserted.append((row, anchor))
        return row

    def durations(self, n: Note) -> None:
        rows = sorted(n.rows, key=lambda r: r.date)
        for i, r in enumerate(rows[:-1]):
            nxt = rows[i + 1]
            if r.nights and r.date + dt.timedelta(days=r.nights) < nxt.date:
                continue  # a stay inside another city's span keeps its own length
            moved = r.changed and (r.new or r.orig_date != r.date)
            nxt_moved = nxt.new or (nxt.orig_date is not None and nxt.orig_date != nxt.date)
            if not (moved or nxt_moved):
                continue
            c = n.cell(r, "City")
            if c is None:
                continue
            tok = nights_token((nxt.date - r.date).days)
            m = re.search(r"(?<=[\s>])(\d+[dnwm])(?=[\s<✅€$]|$)", c[1])
            if m and m.group(1) != tok:
                c[1] = c[1][:m.start()] + tok + c[1][m.end():]
                r.changed = True
                self.log[f"{n.year} itinerary note"].append(f"{r.city} {r.date}: {m.group(1)} -> {tok}")

    def header(self, n: Note) -> None:
        if not n.added_eur or not n.h2:
            return
        inner = re.sub(r"^<h2\b[^>]*>|</h2>$", "", n.h2)
        m = FORMULA.search(inner)
        if m:
            terms = [int(x) for x in re.split(r"\s*\+\s*", m.group(1))] + n.added_eur
            total = sum(terms)
            new = inner[:m.start()] + "€" + "+".join(map(str, terms)) + f" = {total}" + inner[m.end():]
            new = re.sub(r"\d+€/m", f"{round(total / 12)}€/m", new, count=1)
        else:
            terms = []
            for r in sorted(n.rows, key=lambda r: r.date):
                c = n.cell(r, "€")
                if r.date.year == n.year and c is not None:
                    terms += [int(x) for x in re.findall(r">\s*(\d+)\s*<", c[1])]
            total = sum(terms)
            new = (f'<span style="{GREEN}">{round(total / 12)}€/m [12m]</span> -> '
                   f'€{"+".join(map(str, terms)) or "0"} = {total} | $/€={n.rate:g}')
        n.new_h2 = re.match(r"<h2\b[^>]*>", n.h2).group(0) + new + "</h2>"
        self.log[f"{n.year} itinerary note"].append(f"header: {text(n.new_h2)}")

    # outputs
    def ops(self, n: Note) -> list[dict]:
        ops = []
        old_rows = sorted([r for r in n.rows if not r.new], key=lambda r: r.orig_date)
        follow: dict[int, list[Row]] = {id(r): [] for r in old_rows}
        first: list[Row] = []
        for x in sorted((r for r in n.rows if r.new), key=lambda r: r.date):
            prev = [r for r in old_rows if r.date <= x.date]
            (follow[id(max(prev, key=lambda r: r.date))] if prev else first).append(x)
        sep = "\n" if "</tr>\n<tr" in n.table else ""
        for i, r in enumerate(old_rows):
            after = follow[id(r)]
            before = first if i == 0 else []
            if not (r.changed or after or before):
                continue
            content = "".join(x.ref.build() + sep for x in before) + r.ref.build() + "".join(
                sep + x.ref.build() for x in after)
            if n.enml.count(r.ref.tr) != 1:
                raise ValueError(f"{n.year} note: a row to change is not unique in the note")
            ops.append({"find": r.ref.tr, "content": content})
        if getattr(n, "new_h2", None):
            ops.append({"find": n.h2, "content": n.new_h2})
        return ops

    def write_local(self) -> None:
        if any(r.changed for r in self.csv_rows):
            self.csv_path.write_text(dump_csv(self.csv_rows), encoding="utf-8")
        lines = list(self.md_lines)
        for tab in sorted(self.md_tables, key=lambda t: t.start, reverse=True):
            if not any(r.changed for r in tab.rows):
                continue
            body = [f"| {' | '.join(r.ref)} |" for r in sorted(tab.rows, key=lambda r: r.date)]
            lines[tab.start:tab.end] = tab.header + body
        if lines != self.md_lines:
            self.md_path.write_text("\n".join(lines), encoding="utf-8")

    def report(self, verify: dict[str, list[str]] | None, written: bool, dry: bool) -> str:
        out = ["# itinerary-sync report", ""]
        if dry:
            out.append("Dry run: nothing was written.")
        elif not written:
            out.append("Nothing was written to travel.md or travelitinerary.csv, because a note write did not verify.")
        for rec, lines in self.log.items():
            out += ["", f"## {rec}", ""] + ([f"- {x}" for x in lines] or ["- no change"])
        if verify:
            out += ["", "## Verify", ""]
            for k, v in verify.items():
                out.append(f"- {k}: " + ("verified" if not v else "FAILED: " + "; ".join(v)))
        if self.asks:
            out += ["", "## Ask Chaehan", ""] + [f"- {x}" for x in self.asks]
        if self.warn:
            out += ["", "## Notes", ""] + [f"- {x}" for x in self.warn]
        return "\n".join(out) + "\n"


def verify(before: str, after: str, ops: list[dict]) -> list[str]:
    bad = []
    for op in ops:
        if op["content"] not in after:
            bad.append("an edit is missing from the note")
    for h in set(re.findall(r'href="([^"]+)"', before)):
        if h not in after:
            bad.append(f"link lost: {h}")
    if after.count("<en-media") != before.count("<en-media"):
        bad.append("an image tag count changed")
    if len(after) < len(before) - 50:
        bad.append(f"the note shrank from {len(before)} to {len(after)} characters")
    return bad


# ---------------------------------------------------------------- commands

EXECUTE = """const B = "http://127.0.0.1:{port}", ids = {ids};
const before = {{}};
for (const id of ids) before[id] = await tools.evernote.get_note({{ noteId: id }});
const plan = await (await fetch(B + "/plan", {{ method: "POST", body: JSON.stringify(before) }})).json();
if (plan.error) return plan.error;
for (const id of ids) for (const op of plan.ops[id]) await tools.evernote.edit_note({{ noteId: id, mode: "replace", find: op.find, content: op.content }});
const after = {{}};
for (const id of ids) after[id] = await tools.evernote.get_note({{ noteId: id }});
return await (await fetch(B + "/done", {{ method: "POST", body: JSON.stringify(after) }})).text();"""


def load_events(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errs = validate(data)
    if errs:
        print("events.json is not valid; fix it and run start again:", *[f"- {e}" for e in errs], sep="\n")
        sys.exit(2)
    return data["events"]


def cmd_start(a) -> int:
    events = load_events(Path(a.events))
    plan = Plan(events, Path(a.repo), None)
    ids = list(plan.needed_notes().values())
    if not ids:
        print("travel.md names no itinerary note for these dates (line '<year> Travel Itinerary `<guid>`')")
        return 2
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    folder = Path(a.events).resolve().parent
    log = open(folder / "serve.log", "w")
    cmd = [sys.executable, __file__, "serve", str(Path(a.events).resolve()), "--port", str(port), "--repo", a.repo]
    if a.dry_run:
        cmd.append("--dry-run")
    subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=True)
    print("Run this code in ONE execute call, exactly as printed. It reads the notes, applies the planned "
          "edits and returns the report.\n")
    print(EXECUTE.format(port=port, ids=json.dumps(ids)))
    return 0


def cmd_serve(a) -> int:
    events = load_events(Path(a.events))
    folder = Path(a.events).resolve().parent
    state: dict = {}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *args):  # noqa: D401
            pass

        def reply(self, body: str, ctype="application/json"):
            data = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
            got = json.loads(raw)
            if self.path.startswith("/plan"):
                try:
                    notes = {g: find_enml(v) for g, v in got.items()}
                    missing = [g for g, e in notes.items() if not e]
                    if missing:
                        raise ValueError(f"get_note returned no ENML for {missing}")
                    plan = Plan(events, Path(a.repo), notes)
                    plan.run()
                    ops = {n.guid: ([] if a.dry_run else plan.ops(n)) for n in plan.notes.values()}
                    state.update(plan=plan, before=notes, ops=ops,
                                 planned={n.guid: plan.ops(n) for n in plan.notes.values()})
                    (folder / "plan.json").write_text(json.dumps(state["planned"], indent=1, ensure_ascii=False))
                    self.reply(json.dumps({"ops": ops}))
                except Exception as exc:  # the agent sees the reason in the execute result
                    self.reply(json.dumps({"error": f"itinerary-sync plan failed: {exc}"}))
                    state["done"] = True
            elif self.path.startswith("/done"):
                plan: Plan = state["plan"]
                checks = {}
                for n in plan.notes.values():
                    after = find_enml(got.get(n.guid)) or ""
                    checks[f"{n.year} itinerary note"] = verify(state["before"][n.guid], after, state["ops"][n.guid])
                ok = all(not v for v in checks.values())
                written = False
                if ok and not a.dry_run:
                    plan.write_local()
                    written = True
                rep = plan.report(checks, written, a.dry_run)
                (folder / "report.md").write_text(rep, encoding="utf-8")
                self.reply(rep, "text/plain; charset=utf-8")
                state["done"] = True

    srv = HTTPServer(("127.0.0.1", a.port), H)
    srv.timeout = 5
    deadline = dt.datetime.now() + dt.timedelta(minutes=15)
    while not state.get("done") and dt.datetime.now() < deadline:
        srv.handle_request()
    if not state.get("done"):
        (folder / "report.md").write_text("# itinerary-sync report\n\nThe execute call never finished; "
                                          "nothing was written.\n", encoding="utf-8")
    return 0


def cmd_plan(a) -> int:
    events = load_events(Path(a.events))
    notes = {}
    for spec in a.enml or []:
        g, f = spec.split("=", 1)
        notes[g] = find_enml(json.loads(Path(f).read_text())) if f.endswith(".json") else Path(f).read_text()
    plan = Plan(events, Path(a.repo), notes)
    plan.run()
    out = Path(a.out) if a.out else None
    for n in plan.notes.values():
        ops = plan.ops(n)
        after = n.enml
        for op in ops:
            assert after.count(op["find"]) == 1
            after = after.replace(op["find"], op["content"])
        problems = verify(n.enml, after, ops)
        print(f"{n.year} note: {len(ops)} edits, verify: {problems or 'ok'}")
        if out:
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{n.year}.enml").write_text(after)
    if out:
        (out / "travelitinerary.csv").write_text(dump_csv(plan.csv_rows))
    print(plan.report(None, False, True))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("start", "serve", "plan"):
        p = sub.add_parser(name)
        p.add_argument("events")
        p.add_argument("--repo", default=str(REPO))
        if name in ("start", "serve"):
            p.add_argument("--dry-run", action="store_true")
        if name == "serve":
            p.add_argument("--port", type=int, required=True)
        if name == "plan":
            p.add_argument("--enml", action="append", help="GUID=FILE, a get_note result or ENML file")
            p.add_argument("--out")
    a = ap.parse_args(argv)
    return {"start": cmd_start, "serve": cmd_serve, "plan": cmd_plan}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
