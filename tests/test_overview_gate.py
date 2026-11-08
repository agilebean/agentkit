import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills/life-overview/scripts/overview_gate.py"
_spec = importlib.util.spec_from_file_location("overview_gate", _p)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

LINK = "[Seoul Mapo storage locker](evernote:///view/39d2f74/s365/g/g/)"
CHALLENGES_LINK = "[2026-11-07 Life Challenges](evernote:///view/39d2f74/s365/c/c/)"

GOOD = f"""## Takeaway

- Your clothes and papers have no home after 2026-12-04, and the unit that fits had one left.

## Seoul storage

- The unit fits the clothes.
  - It costs 72090 won a month.
- {LINK}

## Your decisions

Your open decisions and the steps you can hand to me are in {CHALLENGES_LINK}.
"""

CHALLENGES = """## Takeaway

- You book storage before 2026-12-04.

## Your decisions

### Storage

Do you book the Gongdeok storage unit, or keep the clothes and papers somewhere free?

1. Book the Gongdeok unit: 72090 won a month.
2. Ask the family to keep one box: free.

## Hand to me

| Issue | I do | You decide | Command |
| --- | --- | --- | --- |
| Seoul storage | book the 72090 won unit through the monthly link | approve | /life storage |
"""

BAD = """## Takeaway

- Seoul storage: book the 72090 won unit through the monthly link.

## Seoul storage

- The unit costs 72090 won a month.

## Open tasks

| Thread | Next move |
| --- | --- |
| Seoul storage | book the 72090 won unit through the monthly link |
"""


def test_good_draft_passes():
    assert gate.check(GOOD) == []


def test_bad_draft_names_each_failure():
    fails = gate.check(BAD)
    kinds = {f.split()[0] for f in fails}
    assert kinds == {"T3", "T4", "T5"}
    assert any("Open tasks section" in f for f in fails if f.startswith("T3"))
    assert any("no link to the current Life Challenges note" in f for f in fails)
    assert any("'Seoul storage'" in f for f in fails if f.startswith("T4"))


def test_takeaway_repeating_the_challenges_note_fails():
    fails = gate.check(BAD, challenges=CHALLENGES)
    assert any("repeats the Life Challenges note" in f and "book the 72090 won unit" in f for f in fails)
    assert not any("repeats the Life Challenges note" in f for f in gate.check(GOOD, challenges=CHALLENGES))


def test_contact_in_overview_fails():
    draft = GOOD.replace("- The unit fits the clothes.", "- The unit fits the clothes; call 02-705-7361 or kej0313@korea.ac.kr.")
    hits = [f for f in gate.check(draft) if f.startswith("T3 a contact")]
    assert len(hits) == 2


def test_dates_are_not_phone_numbers():
    assert gate.PHONE.findall("2026-11-05 and 2026-12-04, 72090 won, 0.575 cbm") == []


def test_overview_runs_t5_but_not_t6():
    original = "Bond AUD 2740 due 2026-12-12."
    assert gate.check(GOOD, original) == []
    flat = GOOD.replace("  - It costs 72090 won a month.", "- It costs 72090 won a month.")
    assert gate.check(flat, original) == ["T5 no indented bullet: every point is a sibling"]


def test_legacy_life_problems_link_counts():
    draft = GOOD.replace("2026-11-07 Life Challenges", "2026-11-06 Life Problems")
    assert gate.check(draft) == []


def test_fact_loss_detected_and_linked_note_counts():
    original = "Storage paid to 2023-11-06, 0.575 cbm."
    assert gate.check(GOOD, original, facts_only=True) == ["T6 fact lost: 0.575", "T6 fact lost: 2023-11-06"]
    assert gate.check(GOOD, original, ["0.575 cbm, paid to 2023-11-06"], facts_only=True) == []


def test_cli_exit_code(tmp_path, capsys):
    f = tmp_path / "d.md"
    f.write_text(BAD)
    assert gate.main([str(f)]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_section_may_declare_no_detail_note():
    draft = GOOD.replace("## Your decisions", "## Health\n\n- Gluten is out since 2026-10-19 (no detail note).\n\n## Your decisions")
    assert gate.check(draft) == []


def test_facts_only_skips_overview_checks():
    original = "Storage paid to 2023-11-06."
    note = "## Takeaway\nThe 2020 sample is better. Storage was paid to 2023-11-06."
    assert gate.check(note, original, facts_only=True) == []
    assert gate.check("## Takeaway\nThe 2020 sample is better.", original, facts_only=True) == ["T6 fact lost: 2023-11-06"]


def test_note_mode_flags_prose_sections_and_passes_lists():
    prose = "## How it is made\nThe vesicles go first. The prostate follows. The sperm come last. Then it is pumped out.\n"
    listed = "## How it is made\nYou can see it in three stages.\n1. The vesicles go first.\n   - 60 to 70% of the volume.\n2. The prostate follows.\n"
    assert "T5 section is prose of 4 sentences, write it as a list: 'How it is made'" in gate.check(prose, note=True)
    assert gate.check(listed, note=True) == []


ORIG = """## Assembly
Your body runs it in two stages.
- Arousal comes first.
- Emission follows.

### Taste by source

| Source | Reads as |
| --- | --- |
| Prostate | Sour and sharp |

## Words
You choose the word for each side.
- Acceptance leaves the owner unstated.
"""


def test_note_mode_fails_on_lost_table_row_and_empty_bullet():
    draft = "## Assembly\n- Arousal comes first.\n- \n- Emission follows.\n\n## Words\n- Reception is her side.\n"
    fails = gate.check(draft, ORIG, note=True)
    assert "T7 table row lost: | Prostate | Sour and sharp |" in fails
    assert "T8 empty list item at line 3" in fails


def test_note_mode_passes_a_reworded_line() -> None:
    draft = ORIG.replace("- Acceptance leaves the owner unstated.", "- Reception is her side.")
    assert gate.check(draft, ORIG, note=True) == []


def test_a_cut_list_lets_a_fact_leave_with_its_destination() -> None:
    original = "## Buying\n- Swanson 100 mg, 30 capsules, 39647 won.\n- Prelox, 62118 won.\n"
    draft = "## Buying\nYou buy pycnogenol by its dose.\n- Pycnogenol 100 mg from any brand.\n"
    assert "T6 fact lost: 39647" in gate.check(draft, original, note=True)
    cuts = "- 39647, 62118, 30: brand prices, any brand at 100 mg works\n"
    assert gate.check(draft, original, note=True, cuts=cuts) == []


def test_a_cut_without_its_reason_fails() -> None:
    original = "## Buying\n- Prelox, 62118 won.\n"
    fails = gate.check("## Buying\n- Pycnogenol.\n", original, note=True, cuts="- 62118\n")
    assert any(f.startswith("T9") for f in fails)


SUMMARY = "## Summary\n\n" + "".join(f"- Decision {i} is short.\n" for i in range(6)) + "\n## Body\n- Detail.\n"


def test_a_summary_over_five_lines_fails() -> None:
    assert any(f.startswith("T10") for f in gate.check(SUMMARY, note=True))


def test_a_long_summary_line_fails() -> None:
    draft = "## Summary\n- " + " ".join(["word"] * 31) + ".\n\n## Body\n- Detail.\n"
    assert any(f.startswith("T10") for f in gate.check(draft, note=True))


def test_a_summary_line_that_repeats_a_body_line_fails() -> None:
    line = "Pycnogenol raises the erection score 9.2 points across 23 trials in 1583 men"
    draft = f"## Summary\n- {line}.\n\n## Evidence\n- {line}, Ramasamy 2024.\n"
    assert any(f.startswith("T11") for f in gate.check(draft, note=True))


def test_more_than_seven_siblings_fail() -> None:
    flat = "## Buying\n" + "".join(f"- Item {i}.\n" for i in range(8))
    grouped = "## Buying\n" + "".join(f"- Group {g}.\n" + "".join(f"  - Item {i}.\n" for i in range(4)) for g in range(2))
    assert any(f.startswith("T12") for f in gate.check(flat, note=True))
    assert not any(f.startswith("T12") for f in gate.check(grouped, note=True))


# The shape checks a weaker model cannot meet by rewording: a section opens with
# one sentence about you (T13), a summary sentence has you or an action as its
# subject and no "X, not Y" frame (T15), and the labelled cut is really cut (T14).

def test_a_section_that_opens_with_a_list_fails() -> None:
    draft = "## Getting around\n- Walk six minutes to Sakuranomiya.\n"
    assert any(f.startswith("T13") for f in gate.check(draft, note=True))


def test_a_section_that_opens_on_an_object_fails() -> None:
    draft = "## Soaplands\nOsaka city has no soapland district.\n- Tobita Shinchi is the Osaka option.\n"
    assert any(f.startswith("T13") for f in gate.check(draft, note=True))


def test_a_section_that_opens_with_you_passes() -> None:
    draft = "## Soaplands\nYou will find no soapland district in Osaka city.\n- Tobita Shinchi is the Osaka option.\n"
    assert not any(f.startswith("T13") for f in gate.check(draft, note=True))


ROBOT = "March has a quote and a band, not a booking, so the flat and a good hotel still land close on price."
PLAIN = "You must still book the March flat. For the 20 nights you need, Atinn's quote comes to ¥208333, close to a good hotel's ¥220000."


def test_a_summary_sentence_about_an_object_fails() -> None:
    fails = gate.check(f"## Summary\n- {ROBOT}\n", note=True)
    assert any(f.startswith("T15") and "subject" in f for f in fails)
    assert any(f.startswith("T15") and "not" in f for f in fails)


def test_summary_subjects_that_pass_and_fail() -> None:
    ok = [PLAIN, "Buy the city pool pass.", "On 2026-12-04 you fly to Kobe.", "If the flat costs more, take the hotel."]
    bad = ["Leaving before the cherry blossoms also keeps you out of the price peak.",
           "ICOCA in Apple Wallet covers the rest.", "Minamisenba and Shimanouchi is the district to search."]
    for line in ok:
        assert not [f for f in gate.check(f"## Summary\n- {line}\n", note=True) if f.startswith("T15")], line
    for line in bad:
        assert [f for f in gate.check(f"## Summary\n- {line}\n", note=True) if f.startswith("T15")], line


LABELS = "1\tD\tD1\tYou land at Kobe Airport at 14:00.\n2\tW\t\tExpo 2025 pulled a demand spike into the city.\n3\t\t\tThe tram stops are the closest.\n"


def test_a_labelled_cut_still_in_the_draft_fails_and_every_item_needs_a_label() -> None:
    draft = "## Arrival\nYou arrive by plane.\n- You land at Kobe Airport at 14:00.\n- Expo 2025 pulled a demand spike into the city.\n"
    fails = gate.check(draft, note=True, labels=LABELS)
    assert any(f.startswith("T14") and "Expo 2025" in f for f in fails)
    assert any(f.startswith("T14") and "item 3" in f for f in fails)


def test_the_cli_refuses_a_rewrite_without_labels_and_cuts(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(tmp_path / "stamps"))
    d = tmp_path / "d.md"
    o = tmp_path / "o.md"
    d.write_text("## Arrival\nYou arrive by plane.\n- You land at 14:00.\n")
    o.write_text("## Arrival\n- Land at 14:00.\n")
    assert gate.main([str(d), "--original", str(o), "--note"]) == 1
    assert "T14" in capsys.readouterr().out


def test_a_pass_stamps_the_exact_text_and_a_fail_does_not(tmp_path, monkeypatch) -> None:
    import hashlib
    stamps = tmp_path / "stamps"
    monkeypatch.setenv("NOTE_GATE_STAMPS", str(stamps))
    good = tmp_path / "good.md"
    good.write_text("## Arrival\nYou arrive by plane.\n- You land at 14:00.\n")
    bad = tmp_path / "bad.md"
    bad.write_text("## Arrival\n- Land at 14:00.\n")
    assert gate.main([str(good), "--note"]) == 0
    assert gate.main([str(bad), "--note"]) == 1
    digest = lambda p: hashlib.sha256(p.read_text().strip().encode()).hexdigest()
    assert (stamps / digest(good)).exists()
    assert not (stamps / digest(bad)).exists()


def test_a_link_title_in_a_summary_line_is_not_read_as_a_sentence() -> None:
    line = "You fly to Osaka on 2026-12-04. [2026-10-04 Osaka trip](evernote:///view/a/s/g/g/)"
    assert not [f for f in gate.check(f"## Summary\n- {line}\n", note=True) if f.startswith("T15")]


def test_a_wording_flag_outside_a_table_fails_and_japanese_in_parentheses_passes() -> None:
    robot = "## Bookings\nYou booked the week.\n- The booking carries the pool fee.\n"
    named = "## Pools\nYou swim at two pools.\n- Chuo Indoor Pool (中央屋内プール) is the daily base.\n"
    leading = "## Pools\nYou swim at two pools.\n- 中央屋内プール is the daily base.\n"
    assert any(f.startswith("T16") for f in gate.check(robot, note=True))
    assert not any(f.startswith("T16") for f in gate.check(named, note=True))
    assert any(f.startswith("T16") for f in gate.check(leading, note=True))


def test_a_table_can_leave_through_the_cut_list() -> None:
    original = "## Market\nYou read the market here.\n\n| Year | Rate |\n| --- | --- |\n| 2024 | 19569 |\n"
    draft = "## Market\nYou pay less in early March.\n- The rate fell in 2026.\n"
    cuts = "- 2024, 19569: market table, world detail\n  | Year | Rate |\n  | 2024 | 19569 |\n"
    assert any(f.startswith("T7") for f in gate.check(draft, original, note=True))
    assert not [f for f in gate.check(draft, original, note=True, cuts=cuts) if f.startswith(("T7", "T9"))]


def test_the_stamp_key_ignores_image_lines_and_outer_whitespace() -> None:
    # The same key as socrates projects/evernote/src/evernote_api.py note_gate_key:
    # the life overview passes its file to the gate and writes it without the image line.
    a = "![Timeline](docs/assets/t.png)\n\n## Takeaway\n- You fly on 2026-12-04.\n"
    b = "## Takeaway\n- You fly on 2026-12-04."
    assert gate.stamp_key(a) == gate.stamp_key(b)
    assert gate.stamp_key(b) == "8841e5e77c030090a9e033ee40d5c674fd9c95a4ee15d6e57dc5e763baa4c70f"


CONTRASTS = [
    "You have a quote for the flat, not a booking.",
    "You book not the flat but the hotel.",
    "Your pass is not a saving; it is a convenience.",
    "You take the hotel rather than the flat.",
    "You take the hotel instead of the flat.",
    "You get not just a room but daily service.",
    "Unlike the flat, your hotel cleans daily.",
    "You pay ¥11000 at the hotel versus ¥10417 at the flat.",
    "Your choice is less about price than about space.",
    "You have no booking, only a quote.",
    "You book the tail but not the first ten days.",
    "Even though March has a quote, you still pay the deposit.",
    "You pay the deposit, though the flat is cheaper.",
    "You booked the flat, yet the hotel costs the same.",
    "You do not even get a towel for the March week.",
    "Your flat costs surprisingly little, as the March quote showed.",
    "Despite your effort, the flat is not booked.",
    "You spent a week on it only to land at the same price.",
    "The catch is that the flat has no cleaning.",
    "You actually save ¥583 a night.",
    "It turns out the hotel is cheaper.",
    "You have only a quote for the Atinn flat, so the March bed still costs ¥250000.",
    "You have no indoor 50 m pool inside Osaka city, so the long course sits at Higashiosaka.",
]

NATURAL = [
    "You must still book a locker for your winter clothes.",
    "You stay at least 3 nights in Kobe.",
    "You swim while the pool is quiet.",
    "You land at 14:00 and take the Port Liner to Sannomiya for ¥340.",
]


def test_everyday_sentences_without_a_contrast_pass() -> None:
    for line in NATURAL:
        assert not gate.contrast(line), line


def test_every_contrast_frame_fails_in_a_summary_line() -> None:
    for line in CONTRASTS:
        fails = [f for f in gate.check(f"## Summary\n- {line}\n", note=True) if "contrast" in f]
        assert fails, line


def test_a_plain_summary_line_has_no_contrast() -> None:
    assert not [f for f in gate.check(f"## Summary\n- {PLAIN}\n", note=True) if "contrast" in f]


def test_a_contrast_in_a_section_opening_fails() -> None:
    draft = "## March stay\nYou take the hotel rather than the flat.\n- The hotel costs ¥11000 a night.\n"
    assert any(f.startswith("T13") and "contrast" in f for f in gate.check(draft, note=True))


def test_a_table_without_an_h3_title_fails() -> None:
    draft = "## Stay\nYou book the hotel.\n- The hotel costs ¥11000.\n\n| Hotel | Price |\n| --- | --- |\n| A | 1 |\n"
    assert any(f.startswith("T17") for f in gate.check(draft, note=True, table_titles=True))
    titled = draft.replace("\n\n| Hotel", "\n\n### Hotels by price\n\n| Hotel")
    assert not any(f.startswith("T17") for f in gate.check(titled, note=True, table_titles=True))


GOAL_LAYOUT = """## Takeaway

- You decide where you live.

## Home

You want Korea as your home base.

- Your deciding question: is your marriage decided in the first half of 2027?
  - If yes, you would consider buying an apartment in the second half of 2027.
  - If not, you rent again from September 2028.
- Where do your winter clothes stay from 2026-12-04?
  - The Gongdeok unit: 72090 won a month.
  - A friend in Seoul: free, for one favour.

## Hand to me

| Issue | I do | You decide | Command |
| --- | --- | --- | --- |
| TAS email | draft the No Response email | approve it, then you send it | `/life tas` |
"""


def test_goal_layout_items_include_questions_options_and_answers():
    items = gate.challenges_items(GOAL_LAYOUT)
    assert "Your deciding question: is your marriage decided in the first half of 2027?" in items
    assert "If yes, you would consider buying an apartment in the second half of 2027." in items
    assert "A friend in Seoul: free, for one favour." in items
    assert any(i.startswith("TAS email") for i in items)
    assert "You decide where you live." not in items and "You want Korea as your home base." not in items


def test_takeaway_restating_the_deciding_question_fails():
    draft = GOOD.replace("- Your clothes and papers",
                         "- If your marriage is decided in the first half of 2027, you would consider buying an apartment.\n- Your clothes and papers")
    assert any("repeats the Life Challenges note" in f for f in gate.check(draft, challenges=GOAL_LAYOUT))


def test_link_address_digits_are_not_facts():
    original = "Book it in [Seoul Mapo storage locker](evernote:///view/39d2f74/s365/431a56de-0a63/431a56de-0a63/), 0.575 cbm."
    assert gate.check(GOOD, original, ["0.575 cbm"], facts_only=True) == []


def test_thousand_separator_fails_and_plain_numbers_pass():
    draft = GOOD.replace("- The unit fits the clothes.", "- You paid 10,000,000 won at signing.")
    assert any(f.startswith("T18") and "10,000,000" in f for f in gate.check(draft))
    assert not any(f.startswith("T18") for f in gate.check(GOOD.replace("- The unit fits the clothes.", "- You paid 10000000 won, 1.5 to 2.5 times.")))
