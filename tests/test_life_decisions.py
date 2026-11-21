"""Confirmed live decisions as data (skills/life-challenges/scripts/decisions.py), human quality plan HQ-02.

The rows are invented; no test reads Chaehan's record.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("decisions", ROOT / "skills" / "life-challenges" / "scripts" / "decisions.py")
dec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dec)

HEAD = "# confirmed by checkbox\nid\tdecision\tdeadline\toptions\tdepends\tsource\n"
ROWS = ("D01\tRenew the boat licence\t2026-03-10\trenew / let it lapse\tthe sailing plan\tmemory/boat.md:12\n"
        "D02\tPick a school\tnone\tvillage / city\tthe move\tmemory/family.md:4\n"
        "D03\tPay the water bill\t2026-02-20\tnone\tnone\tmemory/home.md:9\n")


def _file(tmp_path: Path, name: str = "2026-03-01-decisions.tsv", text: str = HEAD + ROWS) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_a_well_formed_file_passes(tmp_path) -> None:
    assert dec.check(_file(tmp_path)) == []


def test_each_broken_form_names_its_row(tmp_path) -> None:
    bad = HEAD + ROWS.replace("2026-03-10", "March").replace("memory/home.md:9", "my notes").replace("D02", "D01")
    fails = dec.check(_file(tmp_path, "decisions.tsv", bad))
    assert any("YYYY-MM-DD-decisions.tsv" in f for f in fails)
    assert any("not 'March'" in f for f in fails)
    assert any("source names the record line" in f for f in fails)
    assert any("its own id" in f for f in fails)
    assert dec.check(_file(tmp_path, text="id\tdecision\n")) == ["the header must be id decision deadline options depends source, tab-separated"]


def test_the_list_takes_the_latest_file_overdue_first_then_by_deadline(tmp_path, capsys) -> None:
    _file(tmp_path, "2026-02-01-decisions.tsv", HEAD + "D09\tOld\tnone\tnone\tnone\tx.md:1\n")
    _file(tmp_path)
    assert dec.latest(tmp_path).name == "2026-03-01-decisions.tsv"
    order = [r["id"] for r in dec.by_deadline(dec.read(dec.latest(tmp_path)), dt.date(2026, 3, 1))]
    assert order == ["D03", "D01", "D02"]
    assert dec.main(["list", "--life", str(tmp_path), "--today", "2026-03-01"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[1].startswith("D03\t2026-02-20 (overdue)") and out[2].endswith("[renew / let it lapse]")
