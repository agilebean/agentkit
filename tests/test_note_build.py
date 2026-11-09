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
