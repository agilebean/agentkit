"""The writing call (scripts/say.py), build spec steps 3 and 4.

say.py turns the cards of one section into lines: one request with
wording_writer_prompt.md as the system message and the cards as the user
message, then a check of each line against its card, one retry, and a line
the script writes itself when the retry fails too. No test here calls a model.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("say", ROOT / "scripts" / "say.py")
say = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(say)

PAIRS = say.load_pairs()
BY_ID = {r["id"]: r for r in PAIRS}


def _card(**kw) -> dict:
    base = {"section": "Health", "id": "C01", "kind": "state", "thing": "", "fact": "", "so": "", "do": "",
            "said": "", "src": ""}
    return base | kw


# ---- the prompt ----------------------------------------------------------------

def test_the_prompt_rebuilt_from_pairs_p01_to_p08_is_the_tested_file() -> None:
    head, ids = say.split_prompt()
    assert ids == [f"P0{i}" for i in range(1, 9)]
    assert say.build_prompt(head, [BY_ID[i] for i in ids]) == say.PROMPT.read_text(encoding="utf-8")


def test_a_pair_that_shares_a_word_with_a_card_is_swapped() -> None:
    cards = [say.pair_card(BY_ID[f"P{n:02d}"]) for n in range(9, 20)]
    chosen, swapped = say.choose_pairs(cards)
    assert swapped == [("P07", "P20")]  # "an A in your course" and "your naproxen course"
    assert [r["id"] for r in chosen] == ["P01", "P02", "P03", "P04", "P05", "P06", "P20", "P08"]


def test_your_and_numbers_do_not_count_as_shared_words() -> None:
    chosen, swapped = say.choose_pairs([_card(thing="your 400 m freestyle", fact="took 7:58 on 2026-11-02")])
    assert swapped == []


def test_a_pair_with_no_unused_replacement_is_dropped() -> None:
    cards = [say.pair_card(r) for r in PAIRS if r["id"] >= "P09"] + [_card(id="X1", thing="your essay course")]
    chosen, swapped = say.choose_pairs(cards)
    assert ("P03", None) in swapped and ("P07", None) in swapped
    assert "P03" not in [r["id"] for r in chosen]


def test_the_user_message_holds_only_the_cards() -> None:
    msg = say.user_message([say.pair_card(BY_ID["P05"]), say.pair_card(BY_ID["P11"])])
    assert msg == ("Cards:\nP05\tkind=todo | thing=you | do=book a locker for your winter clothes\n"
                   "P11\tkind=state | thing=your naproxen course | fact=ended at 7 days | "
                   "so=diclofenac gel on the spot is enough from here")


def test_the_answer_is_read_by_card_id() -> None:
    lines = say.parse_answer("Here you go:\nC01\tYour gym runs until 2027-01-31.\nC02: You must still renew it.\n"
                             "C09\tA card nobody sent.", ["C01", "C02"])
    assert lines == {"C01": "Your gym runs until 2027-01-31.", "C02": "You must still renew it."}


# ---- the line checks -------------------------------------------------------------

P11 = say.pair_card(BY_ID["P11"])
P15 = say.pair_card(BY_ID["P15"])
P05 = say.pair_card(BY_ID["P05"])


def _fails(line: str, card: dict) -> list[str]:
    return say.check_line(line, card, say.PROMPT.read_text(encoding="utf-8"))[0]


def test_the_accepted_lines_of_the_test_pairs_pass() -> None:
    for n in range(9, 20):
        row = BY_ID[f"P{n:02d}"]
        assert _fails(row["line"], say.pair_card(row)) == [], row["id"]


def test_a_lost_number_or_name_fails() -> None:
    assert _fails("Your four frozen samples at Bom Clinic run out of storage soon: you pay or lose them.", P15)
    assert _fails("Your four frozen samples run out of storage on 2026-11-11: you pay 450000 won "
                  "for another year or the sample is discarded.", P15)


def test_an_added_number_or_name_fails() -> None:
    assert _fails("Your naproxen course ended at 7 days on 2026-11-10, and diclofenac gel on the spot "
                  "is enough from here.", P11)
    assert _fails("Your naproxen course from Bom Clinic ended at 7 days, and diclofenac gel on the spot "
                  "is enough from here.", P11)


def test_an_obligation_the_card_does_not_hold_fails() -> None:
    assert _fails("Your naproxen course ended at 7 days, so you must use diclofenac gel on the spot.", P11)
    assert _fails("Use diclofenac gel on the spot: your naproxen course ended at 7 days.", P11)
    assert _fails("You must still book a locker for your winter clothes.", P05) == []


def test_a_line_copied_from_the_prompt_fails() -> None:
    card = _card(kind="todo", thing="you", do="book a locker for your winter coats")
    assert any("copies" in f for f in _fails("You must still book a locker for your winter clothes.", card))


def test_a_lint_flag_fails_and_a_warn_is_only_reported() -> None:
    card = _card(thing="your Mapo gym membership", fact="runs until 2027-01-31")
    fails, warns = say.check_line("Your Mapo gym membership runs until 2027-01-31, a robust deal.", card,
                                  say.PROMPT.read_text(encoding="utf-8"))
    assert fails
    p13 = say.pair_card(BY_ID["P13"])
    fails, warns = say.check_line(BY_ID["P13"]["line"], p13, say.PROMPT.read_text(encoding="utf-8"))
    assert fails == [] and warns


# ---- the line the script writes when the call fails twice ---------------------

def test_the_script_line_of_each_kind() -> None:
    assert say.script_line(P05) == "You must still book a locker for your winter clothes."
    assert say.script_line(_card(kind="instr", thing="you", do="leave the knee brace at home")) == \
        "Leave the knee brace at home."
    assert say.script_line(say.pair_card(BY_ID["P14"])) == \
        "If you have a November date that goes well, you can stay in Seoul into December."
    assert say.script_line(P11) == \
        "Your naproxen course ended at 7 days, so diclofenac gel on the spot is enough from here."
    assert say.script_line(say.pair_card(BY_ID["P16"])) == BY_ID["P16"]["line"]


# ---- the whole call with a stand-in model ------------------------------------------

def test_say_retries_once_then_writes_the_line_itself(monkeypatch) -> None:
    cards = [P11, P15, P05]
    answers = iter([
        # first request: P11 adds an obligation, P15 drops its number, P05 is right
        "P11\tYour naproxen course ended at 7 days, so you must use the gel.\n"
        "P15\tYour four frozen samples at Bom Clinic run out of storage: you pay or lose them.\n"
        "P05\tYou must still book a locker for your winter clothes.",
        # retry of P11: right; retry of P15: wrong again
        "P11\tYour naproxen course ended at 7 days, and from here diclofenac gel on the spot is enough.",
        "P15\tYour vials run out.",
    ])
    sent = []

    def fake(messages, model=None, max_tokens=0, temperature=0.0):
        sent.append(messages)
        return next(answers)

    monkeypatch.setattr(say, "complete", fake)
    report = say.say(cards, workers=1)
    assert report["how"] == {"P11": "retry", "P15": "script", "P05": "model"}
    assert report["lines"]["P15"] == say.script_line(P15)
    assert report["calls"] == 3
    assert all("Cards:" in m[-1]["content"] for m in sent)
    assert "P05" not in sent[1][-1]["content"] and "P05" not in sent[2][-1]["content"]


# ---- step 4: the literal question ----------------------------------------------------

def test_cannot_say_is_read_from_the_answer() -> None:
    assert say.cannot_say("cannot say")
    assert say.cannot_say("Cannot say.")
    assert say.cannot_say('"cannot say"')
    assert not say.cannot_say("Your 400 m time fell from 8:08 to 8:04.")
    assert not say.cannot_say("The line says the plan buys a calm week, which I cannot say literally.")


def test_the_literal_question_is_the_spec_text() -> None:
    q = say.LITERAL.read_text(encoding="utf-8").strip()
    assert q.startswith("Say in your own plain words what literally happens")
    assert q.endswith("answer exactly: cannot say.")
