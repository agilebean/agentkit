import json
import pytest
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



def _no_overlaps(d) -> None:
    """For a test about something else: judge every listed overlap different."""
    items = json.loads((d / "items.json").read_text())["items"]
    lines = []
    for a, b, ta, tb in nb.overlap_pairs(d, items):
        x, y = sorted((a, b))
        tx, ty = (ta, tb) if x == a else (tb, ta)
        own = [w for w in sorted(nb.content_words(ty) - nb.content_words(tx)) if w in ty.lower() and w not in tx.lower()]
        lines.append(f"{x}\t{y}\tdifferent\t{own[0]}\n")
    (d / "overlaps.tsv").write_text("".join(lines))


def _run(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    d = tmp_path / "w"
    old = tmp_path / "old.md"
    old.write_text(OLD)
    assert nb.main(["init", str(d), str(old), "--guid", "g-1"]) == 0
    return d


def test_each_step_is_asked_for_in_turn_and_bad_labels_are_refused(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    assert nb.main(["next", str(d)]) == 2 and "Step 1 of 4" in capsys.readouterr().out
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    assert nb.main(["next", str(d)]) == 2 and "Step 2 of 4" in capsys.readouterr().out
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


def test_a_given_summary_replaces_the_line_per_section(tmp_path, monkeypatch, capsys) -> None:
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\t-\tYou find the landing time and the train here.\n")
    (d / "summary.md").write_text("- " + "\n- ".join(["Q?"] * 4) + "\n")
    out = (nb.main(["next", str(d)]), capsys.readouterr().out)
    assert out[0] == 2 and "summary.md has 4 lines" in out[1]
    (d / "summary.md").write_text("- The Port Liner decides your first hour in Kobe.\n")
    out = (nb.main(["next", str(d)]), capsys.readouterr().out)
    assert out[0] == 2 and "summary.md line 1 must start with You" in out[1]
    (d / "summary.md").write_text("- You reach Sannomiya 18 minutes after you leave Kobe Airport.\n"
                                  "- Do you take the Port Liner at ¥340 when you land at 14:00?\n")
    rc = nb.main(["next", str(d)])
    out = capsys.readouterr().out
    assert rc == 0, out
    draft = (d / "draft.md").read_text()
    assert draft.startswith("## Summary\n\n- You reach Sannomiya 18 minutes after you leave Kobe Airport.\n"
                            "- Do you take the Port Liner at ¥340 when you land at 14:00?\n\n## Kobe Airport")


HANJI = "/Applications/Hanji.app/Contents/MacOS/hanji"


def test_init_for_hanji_takes_only_a_new_note(tmp_path, capsys) -> None:
    old = tmp_path / "old.md"
    old.write_text(OLD)
    assert nb.main(["init", str(tmp_path / "w"), "--guid", "g-1", "--dest", "hanji"]) == 1
    assert "builds a new note from a file" in capsys.readouterr().err


@pytest.mark.skipif(not Path(HANJI).is_file(), reason="Hanji.app is not installed")
def test_a_hanji_build_creates_reads_back_and_verifies(tmp_path, monkeypatch, capsys) -> None:
    import sys
    sys.path.insert(0, str(_p.parents[2] / "hanji" / "scripts"))
    import hanji_note as hn
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    db = str(tmp_path / "notes.db")
    hn.Hanji(db=db)("notebook", "create", "Travel")
    monkeypatch.setenv("NOTE_BUILD_HANJI_DB", db)
    d = tmp_path / "w"
    old = tmp_path / "old.md"
    old.write_text(OLD)
    assert nb.main(["init", str(d), str(old), "--title", "Kobe arrival", "--notebook", "Travel", "--dest", "hanji"]) == 0
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You find the landing time and the train here.\n")
    assert nb.main(["next", str(d)]) == 0, capsys.readouterr().out
    capsys.readouterr()
    rc = nb.main(["write", str(d)])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert '"dest": "hanji"' in out and "PASS" in out
    md = hn.Hanji(db=db).markdown(json.loads((d / "written.json").read_text())["id"])
    assert md.startswith("# Kobe arrival") and "  - The Port Liner takes 18 minutes" in md


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
                               "You find the landing time and the train here.\n")
    _no_overlaps(d)
    assert nb.main(["next", str(d)]) == 0, capsys.readouterr().out


def test_the_old_summary_is_cut_by_the_script(tmp_path, monkeypatch, capsys) -> None:
    # A weaker model kept the old summary's lines as body items although the
    # step calls them known; the new summary replaces them, so the script cuts them.
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tS\t2\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You find the landing time and the train here.\n")
    _no_overlaps(d)
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
                               "You find the landing time and the train here.\n")
    _no_overlaps(d)
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


def _stamped_build(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NOTE_BUILD_SOCRATES", str(Path.home() / "Software/Prototypes/socrates/.claude/worktrees/evernote-osaka-trip-quality-b1df3d"))
    d = _kept_table(tmp_path, monkeypatch, capsys)
    (d / "titles.tsv").write_text("5\tRates by year\n")
    assert nb.main(["next", str(d)]) == 0
    return d


def test_a_write_replaces_the_whole_body_and_a_created_note_keeps_its_guid(tmp_path, monkeypatch, capsys) -> None:
    import json
    d = _stamped_build(tmp_path, monkeypatch, capsys)
    before = {"structuredContent": {"title": "Old", "content": "<en-note><div>old body</div></en-note>"}}
    plan = nb.plan_write(d, {}, before)
    assert plan["find"] == "<div>old body</div>" and "<h2>Kobe Airport to Sannomiya</h2>" in plan["content"]
    assert "<li><div>" in plan["content"]
    after = {"structuredContent": {"title": "T", "content": "<en-note>" + plan["content"] + "</en-note>"}}
    out = nb.done_write(d, "g-new", after)
    assert '"written": true' in out and "PASS" in out
    assert json.loads((d / "meta.json").read_text())["guid"] == "g-new"


def test_a_write_is_refused_for_a_wrong_link_title_or_an_unstamped_draft(tmp_path, monkeypatch, capsys) -> None:
    d = _stamped_build(tmp_path, monkeypatch, capsys)
    g = "f760aa60-eb40-444d-91bc-6b6656415bb1"
    link = f"evernote:///view/39d2f74/s365/{g}/{g}/"
    (d / "edits.tsv").write_text(f"2\tLand at Kobe Airport at 14:00, [Hotel booking]({link}).\n")
    assert nb.main(["next", str(d)]) == 0
    real = {g: {"structuredContent": {"title": "2026-12-04~11 Hotel: Imperial Hotel Osaka 7n ¥141000"}}}
    assert "exact title" in nb.plan_write(d, real, None)["error"]
    (d / "draft.md").write_text((d / "draft.md").read_text() + "\nhand edit\n")
    assert "changed after its PASS" in nb.plan_write(d, real, None)["error"]


def test_link_and_write_print_execute_code_for_the_mcp(tmp_path, monkeypatch, capsys) -> None:
    assert nb.main(["link", "Imperial Hotel Osaka"]) == 0
    out = capsys.readouterr().out
    assert "tools.evernote.search_notes" in out and '"Imperial Hotel Osaka"' in out
    d = _stamped_build(tmp_path, monkeypatch, capsys)
    capsys.readouterr()
    monkeypatch.setattr(nb, "start_bridge", lambda d, mode: 41234)
    assert nb.main(["write", str(d)]) == 0
    code = capsys.readouterr().out
    assert "// note-gate:" in code and "127.0.0.1:41234" in code and "tools.evernote.edit_note" in code
    assert "evernote_api" not in code


def test_a_sentence_opening_on_a_verb_or_a_number_word_is_no_invented_name() -> None:
    assert nb.invented("Eat Kobe beef at obiobi.", "Kobe beef at obiobi") == []
    assert nb.invented("Six swims cost ¥4200.", "swims ¥4200") == []
    assert nb.invented("Buy the Osaka Amazing Pass.", "Osaka") == ["Amazing", "Pass"]


def test_sentences_run_together_get_their_space_back_outside_links() -> None:
    assert nb.space_sentences("Port Liner, ¥340.At JR Sannomiya.") == "Port Liner, ¥340. At JR Sannomiya."
    assert nb.space_sentences("no shower.Photography is not welcome.") == "no shower. Photography is not welcome."
    link = "[Kansai Mini Pass](https://www.westjr.co.jp/travel.Info/x)"
    assert nb.space_sentences(link) == link
    assert nb.space_sentences("Tabelog 3.5 or better.") == "Tabelog 3.5 or better."


def test_a_top_image_stays_and_a_note_edited_since_the_read_is_refused(tmp_path, monkeypatch, capsys) -> None:
    import json
    d = _stamped_build(tmp_path, monkeypatch, capsys)
    tag = '<en-media hash="606720675162a39fe5181774b33c33d9" type="image/png" width="509px" />'
    before = {"content": f"<en-note>{tag}<h2>Old</h2><div>old body</div></en-note>"}
    plan = nb.plan_write(d, {}, before)
    assert plan["find"] == "<h2>Old</h2><div>old body</div>" and tag not in plan["content"]
    inside = {"content": f"<en-note><h2>Old</h2>{tag}<div>old body</div></en-note>"}
    assert "inside its text" in nb.plan_write(d, {}, inside)["error"]
    meta = json.loads((d / "meta.json").read_text())
    meta["body_key"] = nb.body_key("<h2>Old</h2><div>an earlier body</div>")
    (d / "meta.json").write_text(json.dumps(meta))
    assert "edited since the build read it" in nb.plan_write(d, {}, before)["error"]
    meta["body_key"] = nb.body_key(f"{tag}<h2>Old</h2><div>old body</div>")
    (d / "meta.json").write_text(json.dumps(meta))
    assert "error" not in nb.plan_write(d, {}, before)


def _run_new(tmp_path, monkeypatch, facts: str, found: str = ""):
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    d = tmp_path / "w"
    old, new = tmp_path / "old.md", tmp_path / "new.md"
    old.write_text(OLD)
    new.write_text(facts)
    assert nb.main(["init", str(d), str(old), "--guid", "g-1", "--new", str(new)]) == 0
    if found:
        (d / "found.md").write_text(found)
    return d


def test_new_facts_become_items_and_carry_a_decision_no_old_section_holds(tmp_path, monkeypatch, capsys) -> None:
    # 2026-11-08: a note update with facts the old note did not hold had no slot, so deepseek left the build
    # ("D2 has no section of the old note behind it") and rewrote the note in small edits (failure 201).
    d = _run_new(tmp_path, monkeypatch, "The Port Liner runs every 6 minutes from 05:30.\n",
                 found="Port Liner timetable: every 6 minutes from 05:30. https://www.knkcorp.co.jp\n")
    items = json.loads((d / "items.json").read_text())["items"]
    assert items[-1]["section"] == nb.NEW_HEAD and "every 6 minutes" in items[-1]["text"]
    assert "every 6 minutes" not in (d / "original.md").read_text()
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\n"
                                    "D2: Which Port Liner do you take after landing at 14:00?\n"
                                    "Getting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n6\tD\tD2\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You find the landing time and the train here.\n"
                               "D2\tThe first train\tYou catch a Port Liner within 6 minutes of landing.\t"
                               "Take the next train after 14:00 without a timetable.\n")
    _no_overlaps(d)
    rc = nb.main(["next", str(d)])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "every 6 minutes from 05:30" in (d / "draft.md").read_text()


def test_a_new_fact_without_a_source_line_is_refused(tmp_path, monkeypatch, capsys) -> None:
    d = _run_new(tmp_path, monkeypatch, "The Port Liner runs every 6 minutes from 05:30.\n")
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\n"
                                    "Getting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n6\tS\t3\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "Fix the new facts" in out and "05:30" in out


def test_more_than_three_supporting_items_under_one_item_are_refused(tmp_path, monkeypatch, capsys) -> None:
    facts = "".join(f"The Port Liner car {n} has {n} doors.\n" for n in (1, 2, 3, 4))
    d = _run_new(tmp_path, monkeypatch, facts, found=facts)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\n"
                                    "Getting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tK\t\n4\tW\t\n5\tW\t\n6\tS\t2\n7\tS\t2\n8\tS\t2\n9\tS\t2\n")
    assert nb.main(["next", str(d)]) == 2
    assert "item 2 carries 4 supporting items" in capsys.readouterr().out


def test_an_image_at_the_foot_stays_like_one_at_the_top(tmp_path, monkeypatch, capsys) -> None:
    d = _stamped_build(tmp_path, monkeypatch, capsys)
    tag = '<en-media type="image/png" hash="221100627706631fb4a4eda2b7f836d0" />'
    foot = {"content": f"<en-note><h2>Old</h2><div>old body</div>{tag}<div><br/></div></en-note>"}
    plan = nb.plan_write(d, {}, foot)
    assert "error" not in plan and plan["find"] == "<h2>Old</h2><div>old body</div>" and tag not in plan["content"]


def test_more_than_three_facts_at_the_top_of_a_section_are_refused(tmp_path, monkeypatch, capsys) -> None:
    # The life overview's Move 2: at most three facts under each point. DeepSeek's 2026-11-09 shoulder note kept
    # seven at the top of one section, a third of its items cut where Chaehan asked for quality over quantity.
    facts = "".join(f"The Port Liner car {n} has {n} doors.\n" for n in (1, 2, 3))
    d = _run_new(tmp_path, monkeypatch, facts, found=facts)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\n"
                                    "Getting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tK\t\n4\tW\t\n5\tW\t\n6\tD\tD1\n7\tD\tD1\n8\tS\tD1\n")
    assert nb.main(["next", str(d)]) == 2
    assert "D1 keeps 4 items at the top of its section" in capsys.readouterr().out


def test_a_pasted_phrase_with_a_small_letter_is_refused() -> None:
    errs = nb.new_text_errors("edit of item 41", "possible either the same cause or a strain", "")
    assert any("small letter" in e for e in errs)


def test_overlaps_are_listed_judged_and_cut_never_reworded(tmp_path, monkeypatch, capsys) -> None:
    # Chaehan, 2026-11-09: "most important cut the overlaps".
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tD\tD1\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You land at 14:00 and reach Sannomiya in 18 minutes.\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "Step 4 of 4: overlaps" in out and "D1  You land at 14:00" in out and "3  The Port Liner takes 18 minutes" in out
    (d / "overlaps.tsv").write_text("D1\t3\tsame\t3\nD1\t2\tdifferent\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "item 3 is still kept" in out and "name the words one line says" in out
    (d / "overlaps.tsv").write_text("D1\t3\tsame\tD1\n")
    assert nb.main(["next", str(d)]) == 2
    assert "cut the item" in capsys.readouterr().out
    (d / "overlaps.tsv").write_text("2\tD1\tdifferent\tsannomiya in 18 minutes\nD1\t3\tsame\t3\n")
    with open(d / "labels.tsv", "a") as f:
        f.write("3\tK\t\n")
    rc = nb.main(["next", str(d)])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "Port Liner takes 18 minutes" not in (d / "draft.md").read_text()


def test_a_different_verdict_quotes_what_one_line_adds_and_a_partial_one_is_measured_again(tmp_path, monkeypatch, capsys) -> None:
    # 2026-11-09: DeepSeek judged all 14 listed pairs "different" in two runs; the first line and an item of the
    # celecoxib section both repeated the 400 mg days while each added a fact of its own.
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tD\tD1\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You land at 14:00 and reach Sannomiya in 18 minutes.\n")
    (d / "overlaps.tsv").write_text("2\tD1\tdifferent\tyou land\n3\tD1\tdifferent\tthe moon\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "2 and D1: 'you land' adds nothing the other line lacks" in out
    assert "3 and D1: name the words one line says" in out
    (d / "overlaps.tsv").write_text("2\tD1\tdifferent\tkobe airport\n3\tD1\tpartial\t3\n")
    assert nb.main(["next", str(d)]) == 2
    assert "3 and D1 still share" in capsys.readouterr().out
    (d / "edits.tsv").write_text("3\tThe Port Liner costs ¥340.\n")
    nb.main(["next", str(d)])
    out = capsys.readouterr().out
    assert "still share" not in out and "Assembled" in out, out
    assert "The Port Liner costs ¥340." in (d / "draft.md").read_text()


def test_a_detail_hangs_under_the_line_it_supports(tmp_path, monkeypatch, capsys) -> None:
    # 2026-11-09, DeepSeek's sixth shoulder note: "Your bursa stays quiet" and the injection history hung under the
    # shot's timing, while they support the section's first line (the bursa or swim link left open).
    d = _run(tmp_path, monkeypatch, capsys)
    (d / "decisions.md").write_text("D1: How do you get from Kobe Airport to Sannomiya?\nGetting there -> D1\nMarket -> drop (Chaehan, 2026-11-06)\n")
    (d / "labels.tsv").write_text("1\tK\t\n2\tD\tD1\n3\tS\t2\n4\tW\t\n5\tW\t\n")
    (d / "new.tsv").write_text("D1\tKobe Airport to Sannomiya\tTake the Port Liner from Kobe Airport, 18 minutes for ¥340.\t"
                               "You reach Sannomiya in 18 minutes by the Port Liner.\n")
    assert nb.main(["next", str(d)]) == 2
    out = capsys.readouterr().out
    assert "item 3 hangs under item 2 but supports the first line of D1 more" in out and "label it D under D1" in out


# ---- a text written elsewhere (init --as-is), photos at the top, the duplicate check, the stamp fallback ----

AS_IS = """## Takeaway

- You meet her on 2026-11-10 after your swim, on the Tuesday she offered herself.

## Her interest

You saw her invite you to her exhibition from 2026-11-21.

- She asked twice to attend your class.
"""


def _photo(tmp_path, name="photo of us.png", color=(200, 30, 30)):
    from PIL import Image
    p = tmp_path / name
    Image.new("RGB", (40, 30), color).save(p)
    return p


def _as_is(tmp_path, monkeypatch, text):
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    monkeypatch.setenv("NOTE_BUILD_SOCRATES", str(Path.home() / "Software/Prototypes/socrates/.claude/worktrees/evernote-osaka-trip-quality-b1df3d"))
    src = tmp_path / "mine.md"
    src.write_text(text)
    d = tmp_path / "w"
    rc = nb.main(["init", str(d), "--as-is", str(src), "--title", "2026-11-10 Test", "--notebook", "Affinity"])
    return d, rc


def test_a_text_written_elsewhere_is_gated_stamped_and_written_with_its_photos(tmp_path, monkeypatch, capsys) -> None:
    import hashlib
    img = _photo(tmp_path)
    d, rc = _as_is(tmp_path, monkeypatch, f"![us](<{img}>)\n\n" + AS_IS)
    out = capsys.readouterr().out
    assert rc == 0 and "PASS" in out and "note-gate:" in out
    plan = nb.plan_write(d, {}, None)
    assert "error" not in plan and "<img" not in plan["content"] and "<h2>Her interest</h2>" in plan["content"]
    md5 = hashlib.md5(img.read_bytes()).hexdigest()
    assert plan["images"] == [{"name": img.name, "hash": md5, "size": img.stat().st_size, "mime": "image/png",
                               "width": 40, "height": 30}]
    tag = f'<div><en-media hash="{md5}" type="image/png"/></div>'
    after = {"structuredContent": {"title": "2026-11-10 Test", "content": "<en-note>" + tag + plan["content"] + "</en-note>"}}
    done = nb.done_write(d, "g-new", after, {md5: {"downloadUrl": img.as_uri()}}, {md5: "PUT 200"})
    assert "PASS" in done and "1 at the top, 1 of 1 downloads match" in done and "VERIFY FAILED" not in done
    plain = {"structuredContent": {"content": "<en-note>" + plan["content"] + "</en-note>"}}
    assert "IMAGES FAILED" in nb.done_write(d, "g-new", plain, {}) and "VERIFY FAILED" in nb.done_write(d, "g-new", plain, {})


def test_a_photo_below_the_text_is_refused_and_an_edit_of_the_draft_reruns_the_gate(tmp_path, monkeypatch, capsys) -> None:
    img = _photo(tmp_path)
    d, rc = _as_is(tmp_path, monkeypatch, AS_IS + f"\n![us](<{img}>)\n")
    assert rc == 1 and "stands below the text" in capsys.readouterr().out
    (d / "draft.md").write_text(f"![us](<{img}>)\n\n" + AS_IS)
    assert nb.main(["next", str(d)]) == 0 and "PASS" in capsys.readouterr().out


def test_the_bridge_uploads_a_photo_with_a_resumable_start_and_one_put(tmp_path) -> None:
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    img = _photo(tmp_path)
    seen = {}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            seen["start"] = self.headers.get("x-goog-resumable"), self.headers.get("x-upload-content-length")
            self.send_response(200)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/session")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_PUT(self):
            seen["body"] = self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=lambda: [srv.handle_request() for _ in range(2)], daemon=True).start()
    assert nb.gcs_upload(f"http://127.0.0.1:{srv.server_port}/signed?x=1", img) == "PUT 200"
    assert seen["start"] == ("start", str(img.stat().st_size)) and seen["body"] == img.read_bytes()


def test_a_new_note_whose_title_evernote_holds_already_is_refused() -> None:
    code = nb.EXECUTE_WRITE
    assert code.index("search_notes") < code.index("create_note") and "exists already" in code
    assert code.index("start_attachment_upload") < code.index('mode: "prepend"') < code.index("finalize_attachment")


def test_the_gate_stamps_into_the_cache_folder_where_the_main_one_cannot_be_written(tmp_path, monkeypatch) -> None:
    g = nb.gate()
    monkeypatch.delenv("NOTE_GATE_STAMPS", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".local").mkdir()
    (tmp_path / ".local/state").write_text("a file where the folder would go, as a refused write")
    f = g.stamp("You meet her today.")
    assert f.parent == tmp_path / ".cache/agentkit/note-gate" and g.stamped("You meet her today.")
    assert not g.stamped("You meet her tomorrow.")


def test_a_second_write_does_not_put_in_again_a_photo_the_note_holds(tmp_path, monkeypatch, capsys) -> None:
    import hashlib
    img, other = _photo(tmp_path), _photo(tmp_path, "second.png", (10, 200, 10))
    d, rc = _as_is(tmp_path, monkeypatch, f"![us](<{img}>)\n\n![two](<{other}>)\n\n" + AS_IS)
    assert rc == 0
    held = hashlib.md5(img.read_bytes()).hexdigest()
    before = {"structuredContent": {"content": f'<en-note><en-media hash="{held}" type="image/png"/><div>old</div></en-note>'}}
    plan = nb.plan_write(d, {}, before)
    assert [im["name"] for im in plan["images"]] == ["second.png"]


def test_the_write_run_takes_its_folder_from_the_environment_and_its_verdict_from_the_folder(tmp_path, monkeypatch) -> None:
    import importlib.util as u
    spec = u.spec_from_file_location("note_test", Path(nb.__file__).with_name("note_test.py"))
    nt = u.module_from_spec(spec)
    spec.loader.exec_module(nt)
    assert '"$NOTE_BUILD_WRITE"' in nt.WRITE_BRIEF and "do not read the script" in nt.WRITE_BRIEF
    seen = {}
    monkeypatch.setattr(nt.Run, "go", lambda self: seen.update(a=self.a) or 0)
    assert nt.main(["--write", str(tmp_path), "--out", str(tmp_path / "run")]) == 0
    assert seen["a"].build == str(tmp_path)
    with pytest.raises(SystemExit):
        nt.main(["--out", str(tmp_path / "run")])
    r = nt.Run(seen["a"])
    r.say = lambda *x: None
    (tmp_path / "write_result.txt").write_text('{"guid": "g", "written": true}\nPASS\nimages: 2 at the top, 2 of 2 downloads match their MD5\n')
    r.check_build()
    assert r.written and r.verified
    (tmp_path / "write_result.txt").write_text('{"guid": "g", "written": true}\nPASS\nIMAGES FAILED: x\nVERIFY FAILED\n')
    r.check_build()
    assert r.written and not r.verified


def test_photos_the_write_put_at_the_top_in_divs_stay_at_the_top_on_the_next_write(tmp_path, monkeypatch, capsys) -> None:
    import hashlib
    img = _photo(tmp_path)
    d, rc = _as_is(tmp_path, monkeypatch, f"![us](<{img}>)\n\n" + AS_IS)
    h = hashlib.md5(img.read_bytes()).hexdigest()
    top = f'<div><en-media hash="{h}" type="image/png"/></div><div><en-media hash="{"1" * 32}" type="image/png"/></div>'
    before = {"structuredContent": {"content": f"<en-note>{top}<h2>Takeaway</h2><div>old</div></en-note>"}}
    plan = nb.plan_write(d, {}, before)
    assert "error" not in plan and plan["find"] == "<h2>Takeaway</h2><div>old</div>" and plan["images"] == []


def test_the_printed_execute_code_parses_as_javascript(tmp_path) -> None:
    """2026-11-10: two lines lost their escaped quotes when Python printed them, and the execute call failed to parse."""
    import shutil
    import subprocess
    if not shutil.which("node"):
        pytest.skip("node is not installed")
    for name in ("EXECUTE_WRITE", "EXECUTE_INIT", "EXECUTE_LINK"):
        code = getattr(nb, name).replace("PORT", "41234").replace("STAMP", "0" * 64).replace("GUID", "g")
        code = code.replace("WORDS", '"x"').replace("N }", "5 }")
        f = tmp_path / f"{name}.mjs"
        f.write_text("export default async function run(tools, fetch) {\n" + code + "\n}\n")
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, (name, r.stderr[-400:])


def test_a_text_written_elsewhere_goes_to_hanji_with_a_photo_whose_path_has_a_space(tmp_path, monkeypatch, capsys) -> None:
    import importlib.util as u
    import shutil
    if not Path("/Applications/Hanji.app/Contents/MacOS/hanji").exists():
        pytest.skip("Hanji.app is not installed")
    spec = u.spec_from_file_location("hanji_note", nb.HANJI_NOTE)
    hn = u.module_from_spec(spec)
    spec.loader.exec_module(hn)
    (tmp_path / "tmp").mkdir()
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    db = str(tmp_path / "notes.db")
    hn.Hanji(db=db)("notebook", "create", "Affinity")
    monkeypatch.setenv("NOTE_BUILD_HANJI_DB", db)
    img = _photo(tmp_path, "photo of us.png")
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    src = tmp_path / "mine.md"
    src.write_text(f"![us](<{img}>)\n\n" + AS_IS)
    d = tmp_path / "w"
    assert nb.main(["init", str(d), "--as-is", str(src), "--title", "2026-11-10 Test", "--notebook", "Affinity",
                    "--dest", "hanji"]) == 0
    capsys.readouterr()
    rc = nb.main(["write", str(d)])
    out = capsys.readouterr().out
    assert rc == 0, out[-600:]
    h = hn.Hanji(db=db)
    nid, _ = hn.resolve(h, "2026-11-10 Test")
    atts = h.attachments(nid)
    assert [(x["name"], x["mime"]) for x in atts] == [("photo of us.png", "image/png")]
    assert [l for l in h.markdown(nid).split("\n") if l.strip()][1].startswith("![photo of us.png](blobs/")


# ---- Chaehan's own words stand as he wrote them (--verbatim) ----

HIS = """**2026-11-08** the second swim test, 400 m in 6:58. Went better than expected. My legs were tired from pilates, although the pace held. I felt the last 100 m were the strongest.

The pool was cold; the lane was crowded after 13:00."""

WITH_HIS = """## Takeaway

- You swam the 400 m in 6:58 on 2026-11-08, your best this month.

## Your feedback

""" + HIS + """

## Next test

You test again on 2026-11-15, in the 13:00 slot.

- Book the lane before you go.
"""


def test_his_own_words_keep_their_form_and_are_checked_for_loss_only(tmp_path) -> None:
    g = nb.gate()
    plain = g.check(WITH_HIS, None, note=True, table_titles=True)
    assert any(f.startswith("T5") for f in plain) and any(f.startswith("T13") and "Your feedback" in f for f in plain)
    assert g.check(WITH_HIS, None, note=True, table_titles=True, verbatim=HIS) == []
    changed = WITH_HIS.replace("Went better than expected.", "It went better than expected.")
    fails = g.check(changed, None, note=True, table_titles=True, verbatim=HIS)
    assert [f for f in fails if f.startswith("T20")] == ["T20 your words are missing or changed: 'Went better than "
                                                         "expected.'; keep them as you wrote them"]
    import re
    bulleted = WITH_HIS.replace(HIS, "\n".join("- " + s for s in re.split(r"(?<=[.;])\s+", HIS.replace("\n\n", " "))))
    assert not [f for f in g.check(bulleted, None, note=True, table_titles=True, verbatim=HIS) if f.startswith("T20")]


def test_his_own_list_of_more_than_seven_items_stands(tmp_path) -> None:
    g = nb.gate()
    items = "\n".join(f"- Lap {i} felt slower than lap {i - 1} by a second" for i in range(2, 11))
    md = WITH_HIS.replace(HIS, "You wrote this list after the test.\n\n" + items)
    assert any(f.startswith("T12") for f in g.check(md, None, note=True, table_titles=True))
    assert not [f for f in g.check(md, None, note=True, table_titles=True, verbatim=items) if f.startswith("T12")]


def test_init_as_is_with_his_words_passes_and_its_read_back_verifies(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    monkeypatch.setenv("NOTE_BUILD_SOCRATES", str(Path.home() / "Software/Prototypes/socrates/.claude/worktrees/evernote-osaka-trip-quality-b1df3d"))
    (tmp_path / "his.md").write_text(HIS)
    (tmp_path / "mine.md").write_text(WITH_HIS)
    d = tmp_path / "w"
    args = ["init", str(d), "--as-is", str(tmp_path / "mine.md"), "--title", "2026-11-08 Swim", "--notebook", "Swimming"]
    assert nb.main(args) == 1  # without his words named, the gate reshapes them
    capsys.readouterr()
    assert nb.main(args + ["--verbatim", str(tmp_path / "his.md")]) == 0 and "PASS" in capsys.readouterr().out
    plan = nb.plan_write(d, {}, None)
    after = {"structuredContent": {"content": "<en-note><div><br/></div>" + plan["content"] + "</en-note>"}}
    assert "PASS" in nb.done_write(d, "g", after, {})


def test_photos_after_an_empty_first_line_still_stand_at_the_top() -> None:
    body = '<div><br/></div><div><en-media hash="' + "a" * 32 + '" type="image/png"/></div><h2>Takeaway</h2>'
    m = nb.LEADING_MEDIA.match(body)
    assert m and body[m.end():] == "<h2>Takeaway</h2>"


def test_a_rewrite_by_guid_needs_the_text_it_started_from_and_refuses_an_edit_since(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    monkeypatch.setenv("NOTE_BUILD_SOCRATES", str(Path.home() / "Software/Prototypes/socrates/.claude/worktrees/evernote-osaka-trip-quality-b1df3d"))
    (tmp_path / "his.md").write_text(HIS)
    (tmp_path / "mine.md").write_text(WITH_HIS)
    base = WITH_HIS.replace(HIS, "- Went better than expected.")
    (tmp_path / "base.md").write_text(base)
    d = tmp_path / "w"
    args = ["init", str(d), "--as-is", str(tmp_path / "mine.md"), "--guid", "g-1", "--verbatim", str(tmp_path / "his.md")]
    assert nb.main(args) == 1 and "--base" in capsys.readouterr().err
    assert nb.main(args + ["--base", str(tmp_path / "base.md")]) == 0
    enml = nb.enml_module().markdown_to_enml(base)
    photo = '<div><en-media hash="' + "b" * 32 + '" type="image/png"/></div>'
    before = {"structuredContent": {"content": enml.replace("<en-note>", "<en-note>" + photo, 1)}}
    plan = nb.plan_write(d, {}, before)
    assert "error" not in plan and photo not in plan["find"]
    edited = {"structuredContent": {"content": before["structuredContent"]["content"].replace("Book the lane", "Book a lane")}}
    assert "edited since" in nb.plan_write(d, {}, edited)["error"]


def _section_build(tmp_path, monkeypatch, base_md):
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    monkeypatch.setenv("NOTE_BUILD_SOCRATES", str(Path.home() / "Software/Prototypes/socrates/.claude/worktrees/evernote-osaka-trip-quality-b1df3d"))
    (tmp_path / "his.md").write_text(HIS)
    (tmp_path / "sec.md").write_text("## Your feedback\n\n" + HIS)
    (tmp_path / "base.md").write_text(base_md)
    d = tmp_path / "w"
    assert nb.main(["init", str(d), "--as-is", str(tmp_path / "sec.md"), "--guid", "g-1", "--base", str(tmp_path / "base.md"),
                    "--verbatim", str(tmp_path / "his.md"), "--replace-section", "Your feedback"]) == 0
    return d


def test_a_section_write_replaces_one_section_and_keeps_his_edits_and_photos_around_it(tmp_path, monkeypatch, capsys) -> None:
    base = WITH_HIS.replace(HIS, "You wrote this after the test.\n\n- Went better than expected.")
    d = _section_build(tmp_path, monkeypatch, base)
    enml = nb.enml_module().markdown_to_enml(base)
    photos = '<table><tr><td><en-media hash="' + "c" * 32 + '" type="image/png"/></td></tr></table>'
    his_edit = "<ol><li><div>his own list</div></li></ol>" + photos
    raw = enml.replace("<en-note>", "<en-note>" + his_edit, 1).replace("<h2>Your feedback</h2>",
                                                                        '<h2 style="--en-nodeId:x;">Your feedback</h2>')
    plan = nb.plan_write(d, {}, {"structuredContent": {"content": raw}})
    assert "error" not in plan and plan["find"].startswith('<h2 style="--en-nodeId:x;">Your feedback</h2>')
    assert "Next test" not in plan["find"] and "his own list" not in plan["find"] and "Went better" in plan["content"]
    after = {"structuredContent": {"content": raw.replace(plan["find"], plan["content"])}}
    assert "PASS: the section reads back" in nb.done_write(d, "g-1", after)
    broken = {"structuredContent": {"content": after["structuredContent"]["content"].replace("his own list", "a list")}}
    out = nb.done_write(d, "g-1", broken)
    assert "the rest of the note changed" in out and "VERIFY FAILED" in out


def test_a_section_edited_since_or_holding_an_image_is_refused(tmp_path, monkeypatch, capsys) -> None:
    base = WITH_HIS.replace(HIS, "You wrote this after the test.\n\n- Went better than expected.")
    d = _section_build(tmp_path, monkeypatch, base)
    enml = nb.enml_module().markdown_to_enml(base)
    edited = enml.replace("Went better than expected.", "Went much better than expected.")
    assert "edited since" in nb.plan_write(d, {}, {"structuredContent": {"content": edited}})["error"]
    img = enml.replace("<h2>Your feedback</h2>", '<h2>Your feedback</h2><en-media hash="' + "d" * 32 + '" type="image/png"/>')
    assert "holds an image" in nb.plan_write(d, {}, {"structuredContent": {"content": img}})["error"]


def test_a_date_note_keeps_her_as_subject_through_the_read_back(tmp_path, monkeypatch) -> None:
    """--person reaches the gate at init and again when the read-back is verified (2026-11-12, Jiyoung date 3)."""
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    import importlib.util as _u
    spec = _u.spec_from_file_location("nb_person", Path(__file__).resolve().parents[1] / "skills" / "evernote" / "scripts" / "note_build.py")
    nb = _u.module_from_spec(spec); spec.loader.exec_module(nb)
    text = ("## Takeaway\n\n- You met her for ten hours and she asked about your parents.\n\n"
            "## Her humor\n\nShe makes dry jokes about herself.\n\n"
            + "".join(f"- She laughed at line {i} of your story.\n" for i in range(5)))
    src = tmp_path / "draft.md"; src.write_text(text, encoding="utf-8")
    d = tmp_path / "build"
    assert nb.main(["init", str(d), "--as-is", str(src), "--title", "2026-11-11 Test: Date 3",
                    "--notebook", "Affinity", "--person", "Jiyoung Kim"]) == 0
    back = tmp_path / "back.md"; back.write_text(text, encoding="utf-8")
    assert nb.main(["verify", str(d), str(back)]) == 0
