import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

_p = Path(__file__).resolve().parents[1] / "skills/hanji/scripts/en_to_hanji.py"
_spec = importlib.util.spec_from_file_location("en_to_hanji", _p)
eh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eh)

HANJI = os.environ.get("HANJI_BIN") or shutil.which("hanji") or eh.APP_BIN
needs_hanji = pytest.mark.skipif(not Path(HANJI).is_file(), reason="Hanji.app is not installed")
needs_socrates = pytest.mark.skipif(not (eh.SOCRATES / "projects/evernote/src/enml.py").is_file(),
                                    reason="socrates's ENML converter is not checked out")


def png(seed: int) -> bytes:
    raw = b"\x00" + bytes([seed % 256, 80, 160]) * 2
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def fixture(tmp: Path):
    top, cellimg, pdf = png(1), png(2), b"%PDF-1.4 test file\n"
    files = []
    for i, (data, mime, name) in enumerate([(top, "image/png", "chart.png"), (cellimg, "image/png", "jan.png"),
                                             (pdf, "application/pdf", "ticket.pdf")]):
        p = tmp / f"src{i}"
        p.write_bytes(data)
        files.append({"hash": hashlib.md5(data).hexdigest(), "mime": mime, "name": name, "path": p})
    h = [f["hash"] for f in files]
    enml = (
        '<?xml version="1.0"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note>'
        f'<div><en-media hash="{h[0]}" type="image/png"/></div>'
        "<h2>Plan</h2>"
        '<div><en-todo checked="true"/>Book the Osaka flight</div>'
        '<div><en-todo checked="false"/>Pack the winter coat</div>'
        '<div>See <a href="evernote:///view/1/s1/abc/abc/">2026 Packing List</a> and '
        '<a href="https://maps.google.com/?q=Umeda">Umeda</a>.</div>'
        "<table><tr><th><div>Month</div></th><th><div>Picture</div></th></tr>"
        f'<tr><td><div>January</div><div>first week</div></td><td><en-media hash="{h[1]}" type="image/png"/></td></tr>'
        "</table>"
        "<h4>Deep detail</h4><div>Gate 34 at 서울역.</div>"
        f'<div><en-media hash="{h[2]}" type="application/pdf"/></div>'
        "</en-note>")
    note = {"id": "g-1", "title": "2026-11-07 Move test", "notebookId": "nb-1", "content": enml,
            "tags": [], "resources": [{"hash": f["hash"], "mime": f["mime"], "name": f["name"]} for f in files]}
    payload = {"notes": [{"title": note["title"], "matches": [{"title": note["title"], "id": "g-1"}], "note": note,
                          "files": [{"hash": f["hash"], "got": {"downloadUrl": f["path"].as_uri()}} for f in files]},
                         {"title": "No such note", "matches": [], "near": ["Something close"]}],
               "notebooks": {"hits": [{"notebookId": "nb-1", "label": "Travel"}]}}
    return enml, files, payload


@needs_socrates
def test_convert_keeps_checkboxes_cell_lines_and_places_files(tmp_path) -> None:
    enml, files, _ = fixture(tmp_path)
    fmap = {f["hash"]: {"name": f["name"], "mime": f["mime"], "path": str(f["path"])} for f in files}
    md, changes = eh.convert(enml, fmap)
    lines = md.split("\n")
    assert lines[0] == f"![chart.png]({files[0]['path']})"
    assert "- [x] Book the Osaka flight" in lines and "- [ ] Pack the winter coat" in lines
    see = lines.index("See 2026 Packing List and [Umeda](https://maps.google.com/?q=Umeda).")
    assert lines[see - 1] == ""  # not folded into the checkbox above it
    row = next(ln for ln in lines if ln.startswith("| January"))
    assert row == "| January<br>first week | jan.png |"
    after = lines[lines.index(row) + 1:]
    assert f"![jan.png]({files[1]['path']})" in after[:3]
    assert f"[ticket.pdf]({files[2]['path']})" in lines
    assert any("other Evernote notes" in c for c in changes)
    assert any("inside table cells" in c for c in changes)
    assert any("below ###" in c for c in changes)


@needs_socrates
def test_convert_refuses_a_file_it_did_not_download(tmp_path) -> None:
    enml, files, _ = fixture(tmp_path)
    with pytest.raises(KeyError):
        eh.convert(enml, {})


def test_words_compare_evernote_text_with_hanji_text() -> None:
    ev = eh.enml_words("<en-note><div>Gate&nbsp;34 at 서울역</div><td>a1</td><td>a2</td></en-note>")
    assert ev == eh.words("gate 34 at 서울역 a1 a2")
    assert eh.words("a1a2") != eh.words("a1 a2")  # glued cell lines would count as lost words
    assert eh.enml_words('<div><span style="color:red">분</span>이십니다</div>') == eh.words("분이십니다")


@needs_hanji
@needs_socrates
def test_import_creates_the_note_and_checks_it_against_evernote(tmp_path) -> None:
    db = str(tmp_path / "notes.db")
    subprocess.run([HANJI, "--db", db, "--json", "notebook", "create", "Travel"], check=True, capture_output=True)
    subprocess.run([HANJI, "--db", db, "--json", "notebook", "create", "Inbox"], check=True, capture_output=True)
    _, files, payload = fixture(tmp_path)
    rep = eh.run_import(payload, tmp_path / "out", db, None, False)
    assert "Moved 1 of 2 notes" in rep
    assert "Hanji notebook Travel" in rep
    assert "- Words: all" in rep, rep
    assert "- Files: 3 of 3, byte-identical." in rep
    assert "- Checkboxes: 2 of 2, 1 of 1 ticked." in rep
    assert "- Tables: 1 of 1." in rep and "- Web links: 1 of 1." in rep
    assert "Nearest titles: Something close." in rep
    assert (tmp_path / "out/report.md").read_text() == rep
    again = eh.run_import(payload, tmp_path / "out2", db, None, False)
    assert "Hanji already has a note with this title" in again


@needs_hanji
@needs_socrates
def test_dry_run_writes_nothing(tmp_path) -> None:
    db = str(tmp_path / "notes.db")
    subprocess.run([HANJI, "--db", db, "--json", "notebook", "create", "Inbox"], check=True, capture_output=True)
    _, _, payload = fixture(tmp_path)
    rep = eh.run_import(payload, tmp_path / "out", db, None, True)
    assert "Dry run" in rep and "Hanji notebook Inbox" in rep
    notes = json.loads(subprocess.run([HANJI, "--db", db, "--json", "note", "list", "--limit", "0"],
                                      capture_output=True, text=True).stdout)
    assert notes == []


def test_execute_code_is_valid_template() -> None:
    code = eh.EXECUTE.format(port=1234, titles=json.dumps(["2026 New Year's Resolutions"]))
    assert "http://127.0.0.1:1234" in code and "New Year's Resolutions" in code
    assert code.count("{") == code.count("}")


@needs_socrates
def test_convert_escapes_masks_marks_colours_and_lists_cell_items() -> None:
    enml = ('<en-note><div>- not a list, 1. not either</div>'
            '<div>성함: 허다*님, 직업: 소프트**** 7~8천, a_b and _x_</div>'
            '<div><span style="color:rgb(24, 168, 65);">booked</span> and '
            '<span style="color:rgb(119, 119, 119);">grey</span></div>'
            '<table><tr><td><div>Profile</div><ul><li><div>밝고 따뜻하며</div></li><li><div>미국 유학</div></li></ul>'
            '</td><td><div>x</div></td></tr></table></en-note>')
    md, changes = eh.convert(enml, {})
    assert "\\- not a list, 1. not either" in md
    assert "허다\\*님" in md and "소프트\\*\\*\\*\\* 7\\~8천" in md and "a_b and \\_x\\_" in md
    assert "==booked== and grey" in md
    assert "| Profile<br>• 밝고 따뜻하며<br>• 미국 유학 | x |" in md
    assert any("highlight" in c for c in changes) and any("header" in c for c in changes)


@needs_socrates
def test_bold_with_a_space_inside_its_edge_stays_bold() -> None:
    md, _ = eh.convert('<en-note><table><tr><th><div><b>Date</b></div></th><th><div><b> City</b></div></th></tr>'
                       '<tr><td>a</td><td>b</td></tr></table></en-note>', {})
    assert "| **Date** | **City** |" in md
