"""The fact card (build spec step 2): card_fill.py, card_check.py, card_select.py.

The fixture is the pilot of 2026-11-16: six record lines from memory/health.md
and memory/travel.md, and the 13 cards DeepSeek V4.1 Flash filled from them in
its first run (docs/2026-11-17 wording build/pilot/card_fill.txt).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fill = _load("card_fill")
check = _load("card_check")
select = _load("card_select")

SOURCES = """# Sources

## Health

memory/health.md:96 | Sleep: magnesium before bed is 4-6 g, about 1 h before (Chaehan, 2026-11-03). Ibuprofen is in use, not daily (Chaehan, 2026-11-03); on-demand dose 30 mg (Chaehan, 2026-11-04).
memory/health.md:12 | Gluten intolerance (standing constraint): Chaehan has kept gluten out of his diet for about 25 years, so it is his permanent diet (Chaehan, 2026-11-08); the agent first recorded it on 2026-10-19, when it ruled out a barley product.
memory/health.md:13 | Lactose intolerance (standing constraint): Chaehan has kept lactose out of his diet for about 25 years, so it is his permanent diet (Chaehan, 2026-11-08); the agent first recorded it on 2026-11-03. Excluded: milk and dairy that contain lactose. Lactose-free dairy is acceptable (Chaehan, 2026-11-04). The 2026-09-21 entry below weighs A1 beta-casein over lactose for the bloating; the two are not yet reconciled.
memory/health.md:140 | Dental cleanings received June 3, 2026 at Bom Clinic (Seoul): 2 cleanings + x-rays = 190,000 KRW, not covered by worldwide insurance. A trusted Apgujeong clinic (doctor knows surgical history) is available but more expensive.
memory/health.md:151 | Clinic invoices filed (stated by Chaehan 2026-11-06, "i filed the health invoices"): the blood test and knee injection receipts that the 2026-11-03 Life Problems note listed as a quick win.
memory/travel.md:88 | Airbnb Sep 14-18 at 80k KRW/day; Chaehan leaves one day early (the final night is paid either way).
"""

FILLED = """measure | your magnesium dose before bed | is 4-6 g, about 1 h before |  |  | 2026-11-03 | 1
state | your ibuprofen use | is in use, not daily |  |  | 2026-11-03 | 1
measure | your ibuprofen on-demand dose | is 30 mg |  |  | 2026-11-04 | 1
state | your gluten-free diet | has been kept for about 25 years and is permanent |  |  | 2026-11-08 | 2
state | your lactose-free diet | has been kept for about 25 years and is permanent |  |  | 2026-11-08 | 3
instr | you |  |  | exclude milk and dairy that contain lactose |  | 3
state | your lactose-free dairy intake | is acceptable | you can eat lactose-free dairy |  | 2026-11-04 | 3
open | the cause of your bloating | remains unreconciled between A1 beta-casein and lactose, with the 2026-09-21 entry weighing A1 beta-casein over lactose |  |  |  | 3
act | you | received 2 dental cleanings plus x-rays on 2026-06-03 at Bom Clinic, Seoul | paid 190,000 KRW, not covered by worldwide insurance |  |  | 4
state | the trusted Apgujeong clinic | is available, its doctor knows your surgical history, and it is more expensive |  |  |  | 4
act | you | filed the health invoices, the blood test and knee injection receipts |  |  | 2026-11-06 | 5
state | your Airbnb stay on Sep 14-18 | costs 80k KRW/day |  |  |  | 6
act | you | leave the Airbnb one day early | the final night is paid either way |  |  | 6
"""


def _pilot(tmp_path) -> Path:
    (tmp_path / "sources.md").write_text(SOURCES, encoding="utf-8")
    block = fill.section_lines(SOURCES, "Health")
    cards, bad = fill.parse_cards(FILLED, "Health", block)
    assert not bad
    path = tmp_path / "cards.tsv"
    fill.write_cards(path, cards)
    return path


# ---- card_fill: the call's answer becomes rows of cards.tsv ------------------

def test_the_section_block_is_numbered_with_its_locations() -> None:
    block = fill.section_lines(SOURCES, "Health")
    assert [loc for loc, _ in block][:2] == ["memory/health.md:96", "memory/health.md:12"]
    assert block[5][1].startswith("Airbnb Sep 14-18")
    assert fill.user_message(block).splitlines()[1].startswith("1  Sleep:")


def test_the_filled_cards_become_13_rows_with_their_record_line_as_src(tmp_path) -> None:
    rows = check.read_cards(_pilot(tmp_path))
    assert len(rows) == 13
    assert rows[0]["id"] == "C01" and rows[0]["section"] == "Health"
    assert rows[0]["src"] == "memory/health.md:96"
    assert rows[12]["src"] == "memory/travel.md:88"
    assert rows[5]["do"] == "exclude milk and dairy that contain lactose"


def test_a_line_that_is_not_a_card_is_reported_not_kept() -> None:
    block = fill.section_lines(SOURCES, "Health")
    cards, bad = fill.parse_cards("Here are the cards:\nstate | your gym | runs until 2027 |  |  |  | 9\n"
                                  "state | your ibuprofen use | is on demand |  |  |  | 1\n", "Health", block)
    assert len(cards) == 1
    assert len(bad) == 2  # the preamble, and a src line the block does not have


# ---- card_check on the pilot -------------------------------------------------

def test_card_check_fixes_the_separator_and_each_about(tmp_path) -> None:
    path = _pilot(tmp_path)
    refusals, emptied, fixed = check.check_file(path, sources=tmp_path / "sources.md")
    assert refusals == []
    assert sorted(" ".join(f.split()[:2]) for f in fixed) == ["C01 fact:", "C04 fact:", "C05 fact:", "C09 so:"]
    rows = check.read_cards(path)
    assert rows[8]["so"] == "paid 190000 KRW, not covered by worldwide insurance"
    assert rows[0]["fact"] == "is 4-6 g, ~1 h before"
    assert rows[7]["kind"] == "open"  # "remains unreconciled" states an unknown


def test_card_check_empties_a_so_that_repeats_the_fact(tmp_path) -> None:
    path = _pilot(tmp_path)
    _, emptied, _ = check.check_file(path, sources=tmp_path / "sources.md")
    assert emptied == ["C07"]
    rows = check.read_cards(path)
    assert rows[6]["so"] == ""
    assert rows[12]["so"] == "the final night is paid either way"  # new words: kept


def test_a_date_converted_from_month_words_is_grounded(tmp_path) -> None:
    path = _pilot(tmp_path)
    refusals, *_ = check.check_file(path, sources=tmp_path / "sources.md")
    assert not any("2026-06-03" in r.text for r in refusals)


def test_card_select_cuts_7_known_cards_and_keeps_6(tmp_path) -> None:
    path = _pilot(tmp_path)
    check.check_file(path, sources=tmp_path / "sources.md")
    kept, cut = select.select_file(path)
    assert len(cut) == 7 and len(kept) == 6
    assert [c["id"] for c in cut] == ["C01", "C02", "C03", "C04", "C05", "C07", "C11"]
    assert all(c["reason"] == "known" for c in cut)
    assert len(check.read_cards(path)) == 6
    assert len(check.read_cards(tmp_path / "cut.tsv")) == 7


# ---- each rule of the card table ---------------------------------------------

def _card(**kw) -> dict:
    base = {"section": "Health", "id": "C01", "kind": "state", "thing": "your Mapo gym membership",
            "fact": "runs until 2027-01-31", "so": "", "do": "", "said": "", "src": "memory/health.md:1"}
    base.update(kw)
    return base


SRC = "Mapo gym membership runs until 2027-01-31; Chaehan paid 330000 won on 2026-10-02 (Chaehan, 2026-10-02)."


def _fields(card: dict, src: str = SRC) -> set[str]:
    refusals, _ = check.check_card(card, src, check.lint_rules())
    return {r.field for r in refusals}


def test_a_good_card_passes() -> None:
    assert _fields(_card()) == set()


def test_kind_must_be_one_of_seven() -> None:
    assert _fields(_card(kind="fact")) == {"kind"}


def test_thing_must_name_which_one() -> None:
    assert _fields(_card(thing="the membership")) == {"thing"}
    assert _fields(_card(thing="Mapo gym")) == set()
    assert _fields(_card(thing="the 2026-10-02 payment")) == set()


def test_fact_must_continue_the_thing() -> None:
    assert _fields(_card(fact="it runs until 2027-01-31")) == {"fact"}
    assert _fields(_card(fact="")) == {"fact"}
    assert _fields(_card(kind="todo", thing="you", fact="", do="renew the Mapo gym membership")) == set()


def test_do_belongs_to_todo_and_instr_and_starts_with_a_verb() -> None:
    assert _fields(_card(kind="todo", thing="you", fact="", do="the membership renewal")) == {"do"}
    assert _fields(_card(kind="todo", thing="you", fact="", do="you must renew it")) == {"do"}
    assert _fields(_card(kind="todo", thing="you", fact="")) == {"do"}
    assert _fields(_card(do="renew it")) == {"do"}


def test_a_card_has_so_or_do_never_both() -> None:
    card = _card(kind="todo", thing="you", fact="", so="you keep the pool lane", do="renew the Mapo gym membership")
    assert "so" in _fields(card)


def test_said_must_be_a_date_of_the_source_line() -> None:
    assert _fields(_card(said="2026-10-02")) == set()
    assert _fields(_card(said="2026-11-03")) == {"said"}


def test_numbers_and_names_must_be_in_the_source_line() -> None:
    assert _fields(_card(fact="runs until 2027-02-28")) == {"fact"}
    assert _fields(_card(thing="your Hapjeong gym membership")) == {"thing"}


def test_a_missing_source_line_is_refused(tmp_path) -> None:
    path = tmp_path / "cards.tsv"
    check.write_cards(path, [_card(src="memory/health.md:99999")])
    refusals, *_ = check.check_file(path, sources=None, root=tmp_path)
    assert [r.field for r in refusals] == ["src"]


def test_what_went_well_is_never_cut(tmp_path) -> None:
    path = tmp_path / "cards.tsv"
    check.write_cards(path, [_card(section="What went well", said="2026-10-02"), _card(id="C02", said="2026-10-02")])
    kept, cut = select.select_file(path)
    assert [c["id"] for c in kept] == ["C01"] and [c["id"] for c in cut] == ["C02"]


def test_a_thousand_written_with_k_grounds_its_written_out_form() -> None:
    card = _card(thing="your Airbnb stay on Sep 14-18", fact="costs 80000 KRW per day")
    assert _fields(card, "Airbnb Sep 14-18 at 80k KRW/day; Chaehan leaves one day early.") == set()


def test_an_instruction_chaehan_stated_himself_is_known_and_a_todo_stays(tmp_path) -> None:
    path = tmp_path / "cards.tsv"
    check.write_cards(path, [_card(kind="instr", thing="you", fact="", do="take ibuprofen 30 mg on demand",
                                   said="2026-11-04"),
                             _card(id="C02", kind="todo", thing="you", fact="", do="book the Mapo locker",
                                   said="2026-11-04")])
    kept, cut = select.select_file(path)
    assert [c["id"] for c in cut] == ["C01"] and [c["id"] for c in kept] == ["C02"]


def test_a_record_line_copied_under_two_sections_keeps_both_copies(tmp_path) -> None:
    src = tmp_path / "sources.md"
    src.write_text("## What went well\n\nmemory/kubs.md:13 | The course is your first; you count it as done (2026-11-07).\n\n"
                   "## Work\n\nmemory/kubs.md:13 | The course is your first.\n", encoding="utf-8")
    assert "2026-11-07" in check.read_sources(src)["memory/kubs.md:13"]


def test_a_long_section_is_filled_in_pieces_and_a_failed_piece_stops_nothing(monkeypatch) -> None:
    lines = "\n".join(f"memory/health.md:{n} | Your Mapo gym membership runs until 2027-01-{n:02d}." for n in range(1, 10))
    sources = f"## Health\n\n{lines}\n"
    sent = []

    def fake(messages, model=None, **kw):
        sent.append(messages[-1]["content"])
        if "2027-01-07" in messages[-1]["content"]:
            raise RuntimeError("finish_reason='length'")
        return "state | your Mapo gym membership | runs until 2027-01-01 |  |  |  | 1"

    monkeypatch.setattr(fill, "complete", fake)
    cards, bad, _secs = fill.fill_section(sources, "Health")
    assert len(sent) == 2 and sent[0].count("\n") == 6 and sent[1].count("\n") == 3
    assert len(cards) == 1 and cards[0]["src"] == "memory/health.md:1"
    assert len(bad) == 1 and "memory/health.md:7" in bad[0] and "length" in bad[0]


def test_a_name_may_come_from_the_section_and_a_number_only_from_the_line(tmp_path) -> None:
    src = tmp_path / "sources.md"
    src.write_text("## Storage and furniture\n\n"
                   "memory/furniture.md:30 | LA execution complete (2026-09-30): the shipment is in transit.\n"
                   "Evernote 2026-11-07 Life Challenges | Ask whether the furniture that left Los Angeles has arrived.\n"
                   "memory/travel.md:35 | i will rent again, starting from sep 2028 longterm, 2027-03-16.\n", encoding="utf-8")
    path = tmp_path / "cards.tsv"
    check.write_cards(path, [
        _card(section="Storage and furniture", thing="your furniture from Los Angeles",
              fact="left on 2026-09-30 and is in transit", src="memory/furniture.md:30"),
        _card(id="C02", section="Storage and furniture", thing="your rental in Seoul from Sep 2028",
              fact="is long term", src="memory/travel.md:35"),
        _card(id="C03", section="Storage and furniture", thing="your furniture",
              fact="left on 2026-03-16", src="memory/furniture.md:30"),
    ])
    refusals, *_ = check.check_file(path, sources=src)
    assert [(r.card, r.field) for r in refusals] == [("C02", "thing"), ("C03", "fact")]
    assert "Seoul" in refusals[0].text and "2026-03-16" in refusals[1].text


def test_a_quote_survives_any_number_of_writes(tmp_path) -> None:
    path = tmp_path / "cards.tsv"
    card = _card(fact='counts as "a huge breakthrough" in the search')
    for _ in range(3):
        check.write_cards(path, [card])
        card = check.read_cards(path)[0]
    assert card["fact"] == 'counts as "a huge breakthrough" in the search'


# ---- the fixes and refusals step 8 called for (2026-11-19) ------------------------

def test_a_date_in_words_chaehans_and_an_open_card_without_an_unknown_are_fixed() -> None:
    card = _card(kind="open", thing="your storage locker fee", fact="expires on November 11, 2026",
                 so="Chaehan's 2020 sample is kept")
    changes = check.fix_card(card)
    assert card["fact"] == "expires on 2026-11-11" and card["so"] == "your 2020 sample is kept"
    assert card["kind"] == "state" and len(changes) == 3


def test_an_open_card_that_states_an_unknown_stays_open() -> None:
    for fact in ("could be 2027-03-15 or 2027-03-16", "may have women of your target age", "is not yet decided"):
        card = _card(kind="open", fact=fact)
        check.fix_card(card)
        assert card["kind"] == "open", fact


def test_a_bare_chaehan_is_refused() -> None:
    assert _fields(_card(fact="runs until 2027-01-31, as Chaehan said on 2026-10-02")) == {"fact"}


def test_a_todo_whose_record_line_shows_it_done_is_refused() -> None:
    done = "2026-10-31 16:27 send CT-TR-1 + RRF-1 Forms + pay fee [Nonprofit Admin]"
    card = _card(kind="todo", thing="you", fact="", do="send CT-TR-1 + RRF-1 Forms", src="omnifocus_done.txt:2")
    refusals, _ = check.check_card(card, done, check.lint_rules())
    assert [r.rule for r in refusals] == ["done"]
    card["src"] = "memory/taxes.md:3"
    assert check.check_card(card, "- [x] send CT-TR-1 + RRF-1 Forms", check.lint_rules())[0]
    assert not check.check_card(card, "send CT-TR-1 + RRF-1 Forms by 2027-02-15", check.lint_rules())[0]
    due = _card(thing="your Nonprofit Admin task", fact="is due on 2026-10-31", src="omnifocus_done.txt:2")
    assert [r.rule for r in check.check_card(due, done, check.lint_rules())[0]] == ["done"]
    sent = _card(kind="act", thing="you", fact="sent the CT-TR-1 forms on 2026-10-31", src="omnifocus_done.txt:2")
    assert check.check_card(sent, done, check.lint_rules())[0] == []


def test_repair_fills_a_refused_card_again_and_the_facts_a_line_lacks(tmp_path, monkeypatch) -> None:
    src = tmp_path / "sources.md"
    src.write_text("## What went well\n\n"
                   "memory/sport.md:24 | The gym registration as a breakthrough (Chaehan, 2026-11-07): he set "
                   "up a phone call with Junho to run the registration in Korean.\n"
                   "omnifocus_done.txt:2 | 2026-10-31 16:27 send CT-TR-1 + RRF-1 Forms + pay fee\n", encoding="utf-8")
    path = tmp_path / "cards.tsv"
    check.write_cards(path, [
        _card(section="What went well", kind="state", thing="your gym registration",
              fact="counts as a breakthrough for Chaehan", said="2026-11-07", src="memory/sport.md:24"),
        _card(id="C02", section="What went well", kind="todo", thing="you", fact="", do="send CT-TR-1 + RRF-1 Forms",
              src="omnifocus_done.txt:2"),
    ])
    asked = []

    def fake(messages, model=None, **kw):
        msg = messages[-1]["content"]
        asked.append(msg)
        if "was refused" in msg and "CT-TR-1" in msg:
            return "act | you | sent the CT-TR-1 and RRF-1 forms and paid the fee on 2026-10-31 |  |  |  | 1"
        if "was refused" in msg:
            return "state | your gym registration | counts as a breakthrough |  |  | 2026-11-07 | 1"
        if "stand in no card: Junho" in msg:
            return "act | you | set up a phone call with Junho to run the registration in Korean |  |  |  | 1"
        return ""

    monkeypatch.setattr(fill, "complete", fake)
    report = fill.repair(path, src, tmp_path)
    cards = {c["id"]: c for c in check.read_cards(path)}
    assert cards["C01"]["fact"] == "counts as a breakthrough"
    assert cards["C02"]["kind"] == "act" and "2026-10-31" in cards["C02"]["fact"]
    assert any("Junho" in c["fact"] for c in cards.values())
    assert report["refilled"] == {"C01": ["C01"], "C02": ["C02"]} and report["cut as refused"] == []
    assert report["covered"]["memory/sport.md:24"]["missing"] == ["Junho", "Korean"]


def test_a_card_refused_twice_is_cut(tmp_path, monkeypatch) -> None:
    src = tmp_path / "sources.md"
    src.write_text("## Health\n\nmemory/health.md:1 | Mapo gym membership runs until 2027-01-31.\n", encoding="utf-8")
    path = tmp_path / "cards.tsv"
    check.write_cards(path, [_card(fact="runs until 2027-02-28", src="memory/health.md:1")])
    monkeypatch.setattr(fill, "complete", lambda m, **kw: "state | your Mapo gym membership | runs until 2027-03-31 |  |  |  | 1"
                        if "was refused" in m[-1]["content"] else "")
    report = fill.repair(path, src, tmp_path)
    assert report["cut as refused"] == ["C01"] and check.read_cards(path) == []
    assert "refused" in check.read_cards(tmp_path / "cut.tsv")[0]["reason"]


def test_a_year_that_a_date_of_the_line_holds_is_in_the_line() -> None:
    line = "The lease covers 120 days (2031-02-01 to 05-31) plus ~60 in the autumn"
    card = {"section": "Home", "id": "C1", "kind": "measure", "thing": "your lease days in 2031",
            "fact": "are ~180", "so": "", "do": "", "said": "", "src": "memory/home.md:3"}
    line = line.replace("autumn", "autumn, ~180 in all")
    assert check.check_card(card, line, check.lint_rules())[0] == []
    wrong = card | {"thing": "your lease days in 2032"}
    assert [r.rule for r in check.check_card(wrong, line, check.lint_rules())[0]] == ["in the record"]
