import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills/evernote/scripts/note_build.py"
_spec = importlib.util.spec_from_file_location("note_build", _p)
nb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nb)

OLD = """## Summary

- The week has a quote and a band, not a booking.

## Getting there

- Land at [Kobe Airport](https://maps.google.com/?q=Kobe) at 14:00. The Port Liner takes 18 minutes to Sannomiya for ¥340.
- The airport opened in 2006 and handles 3.2 million passengers.

## Market

| Year | Rate |
| --- | --- |
| 2024 | 19569 |
"""


def test_items_keep_links_whole_and_a_table_is_one_item() -> None:
    items, headings = nb.split_items(OLD)
    texts = [it["text"] for it in items]
    assert "Land at [Kobe Airport](https://maps.google.com/?q=Kobe) at 14:00." in texts
    assert sum(it["kind"] == "table" for it in items) == 1
    assert headings == ["Summary", "Getting there", "Market"]


def _run(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    d = tmp_path / "w"
    old = tmp_path / "old.md"
    old.write_text(OLD)
    assert nb.main(["init", str(d), str(old), "--guid", "g-1"]) == 0
    return d


def test_each_step_is_asked_for_in_turn_and_bad_labels_are_refused(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    assert nb.main(["next", str(d)]) == 2 and "Step 1 of 3" in capsys.readouterr().out
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    assert nb.main(["next", str(d)]) == 2 and "Step 2 of 3" in capsys.readouterr().out
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD9\n")
    out = (nb.main(["next", str(d)]), capsys.readouterr().out)
    assert out[0] == 2 and "have no label" in out[1] and "parent is a decision" in out[1]


def test_a_full_build_cuts_nests_opens_each_section_and_stamps(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    # items: 1 old summary, 2 land, 3 port liner, 4 opened in 2006, 5 the table
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You find the landing time and the train here.\n")
    rc = nb.main(["next", str(d)])
    out = capsys.readouterr().out
    assert rc == 0, out
    draft = (d / "draft.md").read_text()
    assert "## Kobe Airport to Sannomiya\n\nYou find the landing time" in draft
    assert "- Land at [Kobe Airport](https://maps.google.com/?q=Kobe) at 14:00.\n  - The Port Liner takes 18 minutes" in draft
    assert "2006" not in draft and "19569" not in draft and "not a booking" not in draft
    assert "2006" in (d / "cuts.md").read_text()
    assert "note_build.py write" in out
    assert list((tmp_path / "stamps").iterdir())


def test_a_new_sentence_about_an_object_is_refused(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tThe week has a quote and a band, not a booking.\t"
                               "You find the landing time and the train here.\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "must start with You" in out and "X, not Y" in out


def test_a_supporting_item_can_carry_its_own_sub_items(tmp_path, monkeypatch, capsys) -> None:
    # Grouping a flat list means hanging details under a detail: the model's own
    # move, which the first deepseek run made 12 times and the script refused.
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tS\t3\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You find the landing time and the train here.\n")
    assert nb.main(["next", str(d)]) == 0, capsys.readouterr().out
    draft = (d / "draft.md").read_text()
    assert "  - The Port Liner takes 18 minutes to Sannomiya for ¥340.\n    - The airport opened in 2006" in draft


def test_an_item_deeper_than_three_levels_is_placed_at_the_third(tmp_path, monkeypatch, capsys) -> None:
    # deepseek grouped into ever deeper chains when a limit refused them; the
    # script places such items itself instead of refusing.
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tS\t3\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You land at 14:00 and reach Sannomiya in 18 minutes.\n")
    assert nb.main(["next", str(d)]) == 0, capsys.readouterr().out


def test_the_old_summary_is_cut_by_the_script(tmp_path, monkeypatch, capsys) -> None:
    # A weaker model kept the old summary's lines as body items although the
    # step calls them known; the new summary replaces them, so the script cuts them.
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tS\t2\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You land at 14:00 and reach Sannomiya in 18 minutes.\n")
    assert nb.main(["next", str(d)]) == 0, capsys.readouterr().out
    assert "not a booking" not in (d / "draft.md").read_text()


def test_every_old_section_needs_a_decision_or_chaehans_word(tmp_path, monkeypatch, capsys) -> None:
    # What matters is Chaehan's to say: a section leaves only through his answer.
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\n")
    assert nb.main(["next", str(d)]) == 2
    assert "Market" in capsys.readouterr().out
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> ask\n")
    assert nb.main(["next", str(d)]) == 3
    assert "Ask Chaehan" in capsys.readouterr().out


def test_a_mapped_section_that_keeps_nothing_is_refused(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> D1\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You land at 14:00 and reach Sannomiya in 18 minutes.\n")
    assert nb.main(["next", str(d)]) == 2
    assert "Market" in capsys.readouterr().out


def test_a_decision_no_section_stands_behind_is_refused(tmp_path, monkeypatch, capsys) -> None:
    # deepseek invented "Do you buy the Osaka Amazing Pass?" for a note that never names it.
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text(
        "D1: How do you get from Kobe Airport to Sannomiya?\nD2: Do you buy the Osaka Amazing Pass?\n"
        "Getting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "D2" in out and ("Amazing" in out or "no section" in out)


def test_a_copied_example_and_an_invented_number_are_refused(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 25 minutes for ¥340.\t"
                               "You swim three mornings a week at the Mapo pool, which opens at 06:00.\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "25" in out and "not in the note" in out
    assert "copies" in out


def test_a_first_line_that_talks_about_the_note_is_refused(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "Your arrival runs on the Port Liner, and the section below lists the times.\n")
    assert nb.main(["next", str(d)]) == 2
    assert "talks about the note" in capsys.readouterr().out


def _kept_table(tmp_path, monkeypatch, capsys):
    """A build that keeps the Market table, so the table needs a title."""
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> D1\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tS\t2\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You find the landing time and the train here.\n")
    return d


def test_a_kept_table_needs_a_title_and_gets_an_h3(tmp_path, monkeypatch, capsys) -> None:
    d = _kept_table(tmp_path, monkeypatch, capsys)
    assert nb.main(["next", str(d)]) == 2 and "table 5 has no title" in capsys.readouterr().out
    (d / "titles.tsv").write_text("5\tRates by year\n")
    rc = nb.main(["next", str(d)])
    assert rc == 0, capsys.readouterr().out
    assert "### Rates by year\n\n| Year | Rate |" in (d / "draft.md").read_text()


def test_an_edit_with_an_invented_number_or_a_separator_is_refused(tmp_path, monkeypatch, capsys) -> None:
    d = _kept_table(tmp_path, monkeypatch, capsys)
    (d / "titles.tsv").write_text("5\tRates by year\n")
    (d / "edits.tsv").write_text("3\tThe Port Liner takes about 25 minutes for ¥1,340.\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "25" in out and "thousand separator" in out and "~N" in out
    (d / "chaehan.md").write_text("Chaehan, 2026-11-07: the Port Liner now takes 25 minutes.\n")
    (d / "edits.tsv").write_text("3\tThe Port Liner takes 25 minutes for ¥340.\n")
    assert nb.main(["next", str(d)]) == 0, capsys.readouterr().out


def test_an_evernote_link_must_name_a_real_note_by_its_exact_title(tmp_path, monkeypatch, capsys) -> None:
    d = _kept_table(tmp_path, monkeypatch, capsys)
    (d / "titles.tsv").write_text("5\tRates by year\n")
    g = "f760aa60-eb40-444d-91bc-6b6656415bb1"
    (d / "links.json").write_text('{"%s": "2026-12-04~11 Hotel: Imperial Hotel Osaka 7n ¥141000"}' % g)
    link = f"evernote:///view/39d2f74/s365/{g}/{g}/"
    (d / "edits.tsv").write_text(f"2\tLand at Kobe Airport at 14:00, [the hotel]({link}).\n")
    assert nb.main(["next", str(d)]) == 2 and "exact title" in capsys.readouterr().out
    (d / "edits.tsv").write_text(f"2\tLand at Kobe Airport at 14:00, [2026-12-04~11 Hotel: Imperial Hotel Osaka 7n ¥141000]({link}).\n")
    assert nb.main(["next", str(d)]) == 0, capsys.readouterr().out


def test_extract_copies_one_section_word_for_word(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    out = tmp_path / "found.md"
    assert nb.main(["extract", str(d), "Getting there", str(out)]) == 0
    assert out.read_text().startswith("- Land at [Kobe Airport]") and "Market" not in out.read_text()


def test_a_created_note_is_updated_on_the_next_write(tmp_path, monkeypatch, capsys) -> None:
    import json
    import types
    d = tmp_path / "w"
    d.mkdir()
    (d / "meta.json").write_text(json.dumps({"guid": None, "title": "2026-11-07 Pools", "notebook": "Swimming"}))
    (d / "draft.md").write_text("## Summary\n")
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        out = '{"guid": "g-new", "title": "2026-11-07 Pools"}' if "create" in cmd else '{"content": ""}'
        return types.SimpleNamespace(returncode=0, stdout=out, stderr="")

    monkeypatch.setattr(nb.subprocess, "run", run)
    monkeypatch.setattr(nb, "cmd_verify", lambda a: 0)
    assert nb.main(["write", str(d)]) == 0
    assert json.loads((d / "meta.json").read_text())["guid"] == "g-new"
    assert nb.main(["write", str(d)]) == 0
    assert "update" in calls[-2] and "create" not in calls[-2]
