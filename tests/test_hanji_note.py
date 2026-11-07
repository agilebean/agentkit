import importlib.util
import json
import os
import shutil
import struct
import zlib
from pathlib import Path

import pytest

_p = Path(__file__).resolve().parents[1] / "skills/hanji/scripts/hanji_note.py"
_spec = importlib.util.spec_from_file_location("hanji_note", _p)
hn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hn)

HANJI = os.environ.get("HANJI_BIN") or shutil.which("hanji") or hn.APP_BIN
needs_hanji = pytest.mark.skipif(not Path(HANJI).is_file(), reason="Hanji.app is not installed")

NOTE = """# 2026-11-07 Swim log

## Takeaway

CSS is 1:52 per 100 m.

## Plan

- Monday
  - 400 m warmup
- Tuesday rest

## Log

| Date | Distance | Notes |
| --- | --- | --- |
| 2026-11-05 | 2000 m | easy |

```
## not a heading
| not | a table |
```
"""


# ---------------------------------------------------------------- pure functions

def test_headings_skip_code_blocks() -> None:
    assert [t for _, _, t in hn.headings(NOTE)] == ["2026-11-07 Swim log", "Takeaway", "Plan", "Log"]


def test_section_span_runs_to_the_next_heading_of_the_same_level() -> None:
    s, e = hn.section_span(NOTE, "Plan")
    body = NOTE.split("\n")[s:e]
    assert "- Monday" in body and "## Log" not in body


def test_splice_touches_only_the_joints() -> None:
    md = "# T\n\n## A\n\nold\n\n## B\n\n```\nx\n\n\n\ny\n```\n"
    s, e = hn.section_span(md, "A")
    out = hn.splice(md, s, e, "new line")
    assert out == "# T\n\n## A\n\nnew line\n\n## B\n\n```\nx\n\n\n\ny\n```\n"


def test_tables_skip_code_blocks_and_cells_split_on_unescaped_bars() -> None:
    assert len(hn.tables(NOTE)) == 1
    assert hn.split_cells("| a \\| b | c |") == ["a \\| b", "c"]


def test_ambiguous_heading_is_refused() -> None:
    with pytest.raises(hn.Fail) as e:
        hn.find_heading("# T\n\n## Log\n\n## Log\n", "Log")
    assert e.value.code == 5


def test_web_links_are_not_attachments(tmp_path) -> None:
    f = tmp_path / "chart.png"
    f.write_bytes(b"x")
    md = f"# T\n\n[site](https://example.com)\n\n![chart]({f})\n\n[x](blobs/abc)\n"
    kinds = [k for k, _ in hn.segments(md)]
    assert kinds == ["text", "att", "att"]


# ---------------------------------------------------------------- against a scratch database

def png(path: Path, w: int, h: int, rgb: bytes) -> Path:
    raw = b"".join(b"\x00" + rgb * w for _ in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return path


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    (tmp_path / "tmp").mkdir()
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "tmp"))
    d = str(tmp_path / "notes.db")
    hn.Hanji(db=d)("notebook", "create", "Swimming")
    return d


def run(db, capsys, *args, stdin=None, monkeypatch=None):
    code = hn.main(["--db", db, *args])
    out, err = capsys.readouterr()
    return code, out, err


def md_of(db, ref):
    h = hn.Hanji(db=db)
    nid, _ = hn.resolve(h, ref)
    return h.markdown(nid), h.attachments(nid)


@needs_hanji
def test_create_puts_a_local_image_where_its_line_stands(db, tmp_path, capsys) -> None:
    img = png(tmp_path / "chart.png", 4, 2, b"\xff\x00\x00")
    src = tmp_path / "in.md"
    src.write_text(f"# 2026-11-07 Swim log\n\n![chart.png]({img})\n\n## Takeaway\n\nCSS is 1:52.\n")
    code, out, err = run(db, capsys, "create", "--notebook", "Swimming", "--file", str(src))
    assert code == 0, err
    assert json.loads(out)["verified"] is True
    md, atts = md_of(db, "2026-11-07 Swim log")
    lines = [ln for ln in md.split("\n") if ln.strip()]
    assert lines[0] == "# 2026-11-07 Swim log"
    assert lines[1].startswith("![chart.png](blobs/") and lines[2] == "## Takeaway"
    assert len(atts) == 1


@needs_hanji
def test_replace_section_keeps_images_in_place(db, tmp_path, capsys) -> None:
    top = png(tmp_path / "top.png", 3, 3, b"\x00\xff\x00")
    low = png(tmp_path / "low.png", 5, 2, b"\x00\x00\xff")
    src = tmp_path / "in.md"
    src.write_text(f"# Note\n\n![top.png]({top})\n\n## Plan\n\nold plan\n\n## Photos\n\n![low.png]({low})\n")
    assert run(db, capsys, "create", "--notebook", "Swimming", "--file", str(src))[0] == 0
    before, atts_before = md_of(db, "Note")
    code, out, err = run(db, capsys, "replace-section", "Note", "Plan", "--text", "- new plan\n  - detail")
    assert code == 0, err
    after, atts_after = md_of(db, "Note")
    assert [a["hash"] for a in atts_after] == [a["hash"] for a in atts_before]
    assert "old plan" not in after and "  - detail" in after
    assert after.index("top.png") < after.index("## Plan") < after.index("## Photos") < after.index("low.png")


@needs_hanji
def test_a_write_that_leaves_out_an_attachment_is_refused(db, tmp_path, capsys) -> None:
    img = png(tmp_path / "a.png", 2, 2, b"\x10\x20\x30")
    src = tmp_path / "in.md"
    src.write_text(f"# Note\n\n![a.png]({img})\n\nbody\n")
    run(db, capsys, "create", "--notebook", "Swimming", "--file", str(src))
    code, _, err = run(db, capsys, "write", "Note", "--text", "# Note\n\nbody only\n")
    assert code == 2 and "a.png" in err
    assert len(md_of(db, "Note")[1]) == 1


@needs_hanji
def test_table_row_and_cell_edits(db, tmp_path, capsys) -> None:
    src = tmp_path / "in.md"
    src.write_text(NOTE)
    run(db, capsys, "create", "--notebook", "Swimming", "--file", str(src))
    t = "2026-11-07 Swim log"
    assert run(db, capsys, "add-row", t, "2026-11-06,2400 m,CSS set")[0] == 0
    assert run(db, capsys, "update-cell", t, "1", "2", "easy | aerobic")[0] == 0
    md, _ = md_of(db, t)
    assert "| 2026-11-06 | 2400 m | CSS set |" in md
    assert "| 2026-11-05 | 2000 m | easy \\| aerobic |" in md
    assert "## not a heading" in md  # the code block is untouched
    assert run(db, capsys, "add-row", t, "only,two")[0] == 2


@needs_hanji
def test_insert_after_heading_and_append(db, tmp_path, capsys) -> None:
    src = tmp_path / "in.md"
    src.write_text(NOTE)
    run(db, capsys, "create", "--notebook", "Swimming", "--file", str(src))
    t = "2026-11-07 Swim log"
    assert run(db, capsys, "insert-after-heading", t, "Takeaway", "--text", "**New first line.**")[0] == 0
    assert run(db, capsys, "append", t, "--text", "## 2026-11-08\n\nEasy 1500 m.")[0] == 0
    md, _ = md_of(db, t)
    assert md.index("**New first line.**") < md.index("CSS is 1:52")
    assert md.rstrip().endswith("Easy 1500 m.")


@needs_hanji
def test_embed_image_on_top_and_again_is_a_no_op(db, tmp_path, capsys) -> None:
    src = tmp_path / "in.md"
    src.write_text(NOTE)
    run(db, capsys, "create", "--notebook", "Swimming", "--file", str(src))
    t = "2026-11-07 Swim log"
    img = png(tmp_path / "chart.png", 6, 6, b"\x99\x99\x00")
    code, out, err = run(db, capsys, "embed-image", t, str(img), "--top")
    assert code == 0, err
    md, atts = md_of(db, t)
    assert [ln for ln in md.split("\n") if ln.strip()][1].startswith("![chart.png](blobs/")
    code, out, _ = run(db, capsys, "embed-image", t, str(img), "--top")
    assert json.loads(out)["already"] is True and len(md_of(db, t)[1]) == 1


@needs_hanji
def test_find_exact_ambiguous_and_missing(db, capsys) -> None:
    for _ in range(2):
        assert run(db, capsys, "create", "--notebook", "Swimming", "--text", "# Twin\n\nx\n")[0] == 0
    assert run(db, capsys, "create", "--notebook", "Swimming", "--text", "# Twin (2)\n\nx\n")[0] == 0
    code, _, err = run(db, capsys, "find", "Twin")
    assert code == 5 and len(json.loads(err)["candidates"]) == 2
    code, out, _ = run(db, capsys, "find", "Twin (2)")
    assert code == 0 and json.loads(out)["title"] == "Twin (2)"
    assert run(db, capsys, "find", "Nothing like it")[0] == 3
    assert run(db, capsys, "create", "--notebook", "Nope", "--text", "# X\n")[0] == 3


@needs_hanji
def test_write_refuses_when_the_note_changed_since_it_was_read(db, capsys) -> None:
    run(db, capsys, "create", "--notebook", "Swimming", "--text", "# Note\n\nfirst\n")
    code, out, err = run(db, capsys, "get", "Note")
    base = err.split("sha: ")[1].split()[0]
    hn.Hanji(db=db)("note", "append", hn.resolve(hn.Hanji(db=db), "Note")[0], "--text", "the app's edit")
    code, _, err = run(db, capsys, "write", "Note", "--base", base, "--text", "# Note\n\nmine\n")
    assert code == 6
    assert "the app's edit" in md_of(db, "Note")[0]


@needs_hanji
def test_delete_moves_to_the_trash(db, capsys) -> None:
    run(db, capsys, "create", "--notebook", "Swimming", "--text", "# Gone\n\nx\n")
    code, out, _ = run(db, capsys, "delete", "Gone")
    assert code == 0 and json.loads(out)["trashed"] is True
    assert run(db, capsys, "find", "Gone")[0] == 3


@needs_hanji
def test_a_read_back_that_differs_fails_with_the_restore_command(db, capsys, monkeypatch) -> None:
    run(db, capsys, "create", "--notebook", "Swimming", "--text", "# Note\n\n## A\n\nold\n")
    real = hn.Hanji.__call__

    def lossy(self, *args, stdin=None, sel=None):
        if args[:2] == ("note", "set") and stdin:
            stdin = stdin.replace("new", "ne")  # the store keeps something else than was sent
        return real(self, *args, stdin=stdin, sel=sel)

    monkeypatch.setattr(hn.Hanji, "__call__", lossy)
    code, _, err = run(db, capsys, "replace-section", "Note", "A", "--text", "new")
    assert code == 4
    e = json.loads(err)
    assert "-new" in e["diff"] and "+ne" in e["diff"]
    assert Path(e["backup"], "note.md").read_text().endswith("old\n")
    assert e["restore"].startswith("hanji_note.py write ")


@needs_hanji
def test_an_image_inside_a_table_cell_blocks_a_rewrite(db, tmp_path, capsys) -> None:
    img = png(tmp_path / "cell.png", 2, 2, b"\x01\x02\x03")
    src = tmp_path / "in.md"
    src.write_text(f"# Note\n\n![cell.png]({img})\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n")
    run(db, capsys, "create", "--notebook", "Swimming", "--file", str(src))
    md, atts = md_of(db, "Note")
    blob = f"![cell.png](blobs/{atts[0]['hash']})"
    moved = md.replace(blob + "\n", "").replace("| 1 | 2 |", f"| 1 | {blob} |")
    code, _, err = run(db, capsys, "write", "Note", "--text", moved)
    assert code == 2 and "table cell" in json.loads(err)["error"]
    assert md_of(db, "Note")[0] == md


@needs_hanji
def test_a_section_edit_that_would_swallow_a_table_is_refused(db, capsys) -> None:
    body = "# Budget\n\nIntro line.\n\n| Item | KRW |\n| --- | --- |\n| Hotel | 840000 |\n\nClosing line.\n"
    run(db, capsys, "create", "--notebook", "Swimming", "--text", body)
    assert run(db, capsys, "insert-after-heading", "Budget", "Budget", "--text", "## Total\n\n1200000")[0] == 0
    before = md_of(db, "Budget")[0]
    code, _, err = run(db, capsys, "replace-section", "Budget", "Total", "--text", "1245000")
    assert code == 2 and json.loads(err)["lost_tables"] == 1
    assert md_of(db, "Budget")[0] == before
    assert run(db, capsys, "replace-section", "Budget", "Total", "--text", "1245000", "--allow-drop")[0] == 0
    assert "| Hotel |" not in md_of(db, "Budget")[0]


@needs_hanji
def test_skeleton_counts_data_rows(db, tmp_path, capsys) -> None:
    src = tmp_path / "in.md"
    src.write_text(NOTE)
    run(db, capsys, "create", "--notebook", "Swimming", "--file", str(src))
    code, out, _ = run(db, capsys, "skeleton", "2026-11-07 Swim log")
    t = json.loads(out)["tables"]
    assert code == 0 and len(t) == 1 and t[0]["rows"] == 1 and t[0]["cols"] == 3
