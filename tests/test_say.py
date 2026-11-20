"""The writing call (scripts/say.py), build spec steps 3 and 4.

say.py turns the cards of one section into lines: one request with
wording_writer_prompt.md and the examples from socrates as the system message and the cards as the user
message, then a check of each line against its card, one retry, and a line
the script writes itself when the retry fails too. No test here calls a model.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("say", ROOT / "scripts" / "say.py")
say = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(say)

if not say.PAIRS.exists():
    pytest.skip("the card and line pairs are Chaehan's private data, kept in socrates", allow_module_level=True)

PAIRS = say.load_pairs()
BY_ID = {r["id"]: r for r in PAIRS}


def _card(**kw) -> dict:
    base = {"section": "Health", "id": "C01", "kind": "state", "thing": "", "fact": "", "so": "", "do": "",
            "said": "", "src": ""}
    return base | kw


# ---- the prompt ----------------------------------------------------------------

def test_the_prompt_rebuilt_from_pairs_p01_to_p08_is_the_tested_file() -> None:
    head, ids, groups = say.split_prompt()
    assert ids == [f"P0{i}" for i in range(1, 9)]
    assert groups.count("line: ") == 3
    assert say.build_prompt(head, [BY_ID[i] for i in ids], groups) == say.prompt_text()


def test_a_pair_that_shares_a_word_with_a_card_is_swapped() -> None:
    cards = [say.pair_card(BY_ID[f"P{n:02d}"]) for n in range(9, 20)]
    chosen, swapped = say.choose_pairs(cards)
    assert swapped == [("P07", "P20")]  # two pairs that share the word "course"
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
    p05, p11 = BY_ID["P05"], BY_ID["P11"]
    msg = say.user_message([say.pair_card(p05), say.pair_card(p11)])
    assert msg == (f"Cards:\nP05\tkind={p05['kind']} | thing={p05['thing']} | do={p05['do']}\n"
                   f"P11\tkind={p11['kind']} | thing={p11['thing']} | fact={p11['fact']} | so={p11['so']}")


def test_the_answer_is_read_by_card_id() -> None:
    lines = say.parse_answer("Here you go:\nC01\tYour gym runs until 2027-01-31.\nC02: You must still renew it.\n"
                             "C09\tA card nobody sent.", ["C01", "C02"])
    assert lines == {"C01": "Your gym runs until 2027-01-31.", "C02": "You must still renew it."}


# ---- the line checks -------------------------------------------------------------

P11 = say.pair_card(BY_ID["P11"])
P15 = say.pair_card(BY_ID["P15"])
P05 = say.pair_card(BY_ID["P05"])


def _fails(line: str, card: dict) -> list[str]:
    return say.check_line(line, card, say.prompt_text())[0]


def test_the_accepted_lines_of_the_test_pairs_pass() -> None:
    for n in range(9, 20):
        row = BY_ID[f"P{n:02d}"]
        assert _fails(row["line"], say.pair_card(row)) == [], row["id"]


def test_a_lost_number_or_name_fails() -> None:
    line = BY_ID["P15"]["line"]
    assert _fails(re.sub(r"\b\d+\b", "", line, count=1), P15)            # the number dropped
    assert _fails(re.sub(r"(?<=\s)[A-Z]\w+", "", line, count=1), P15)    # the name dropped


def test_an_added_number_or_name_fails() -> None:
    line, p11 = BY_ID["P11"]["line"], BY_ID["P11"]
    assert _fails(line.replace(p11["fact"], p11["fact"] + " on 2026-11-10"), P11)   # number added
    thing = p11["thing"].capitalize()
    assert _fails(line.replace(thing, thing + " at Bom Clinic"), P11)                # name added


def test_an_obligation_the_card_does_not_hold_fails() -> None:
    p11 = BY_ID["P11"]
    assert _fails(f"{p11['thing']} {p11['fact']}, so you must use the gel.", P11)
    assert _fails(f"Use the gel: {p11['thing']} {p11['fact']}.", P11)
    assert _fails("You must still book a locker for your winter clothes.", P05) == []


def test_a_line_copied_from_the_prompt_fails() -> None:
    card = _card(kind="todo", thing="you", do="book a locker for your winter coats")
    assert any("copies" in f for f in _fails("You must still book a locker for your winter clothes.", card))


def test_a_lint_flag_fails_and_a_warn_is_only_reported() -> None:
    card = _card(thing="your Mapo gym membership", fact="runs until 2027-01-31")
    fails, warns = say.check_line("Your Mapo gym membership runs until 2027-01-31, a robust deal.", card,
                                  say.prompt_text())
    assert fails
    p13 = say.pair_card(BY_ID["P13"])
    fails, warns = say.check_line(BY_ID["P13"]["line"], p13, say.prompt_text())
    assert fails == [] and warns


# ---- the line the script writes when the call fails twice ---------------------

def test_the_script_line_of_each_kind() -> None:
    assert say.script_line(P05) == "You must still book a locker for your winter clothes."
    assert say.script_line(_card(kind="instr", thing="you", do="leave the knee brace at home")) == \
        "Leave the knee brace at home."
    assert say.script_line(say.pair_card(BY_ID["P14"])) == \
        "If you have a November date that goes well, you can stay in Seoul into December."
    row = BY_ID["P11"]
    expected = f"{row['thing']} {row['fact']}, so {row['so']}."
    assert say.script_line(P11) == expected[0].upper() + expected[1:]
    assert say.script_line(say.pair_card(BY_ID["P16"])) == BY_ID["P16"]["line"]


# ---- the whole call with a stand-in model ------------------------------------------

def test_say_retries_once_then_writes_the_line_itself(monkeypatch) -> None:
    cards = [P11, P15, P05]
    answers = iter([
        # first request: P11 adds an obligation, P15 drops its number, P05 is right
        f"P11\t{BY_ID['P11']['thing']} {BY_ID['P11']['fact']}, so you must use the gel.\n"
        f"P15\t{BY_ID['P15']['thing']} run out: you pay or lose them.\n"
        "P05\tYou must still book a locker for your winter clothes.",
        # retry of P11: right; retry of P15: wrong again
        f"P11\t{BY_ID['P11']['line']}",
        "P15\tYour storage runs out.",
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


def test_a_failed_literal_call_is_one_unanswered_line(monkeypatch) -> None:
    def fake(messages, model=None, max_tokens=0, temperature=0.0):
        if "broken" in messages[-1]["content"]:
            raise RuntimeError("stream ended empty")
        return "cannot say"

    monkeypatch.setattr(say, "complete", fake)
    answers = say.literal_answers(["The plan buys a week.", "A broken line."], workers=1)
    assert say.cannot_say(answers[0]) and say.unanswered(answers[1]) and not say.cannot_say(answers[1])


# ---- one line from several cards (2026-11-20) ------------------------------------------

def test_cards_that_share_a_line_id_go_out_under_it() -> None:
    a = say.pair_card(BY_ID["P16"]) | {"id": "C87", "line": "L5"}
    b = _card(id="C89", kind="state", thing="your furniture", fact="has no recorded arrival", line="L5")
    assert say.user_message([a, b]).splitlines()[1:] == [f"L5\t{say.card_text(a)}", f"L5\t{say.card_text(b)}"]


def test_a_line_is_checked_against_all_its_cards() -> None:
    a = _card(id="C1", thing="your furniture", fact="was due between 2026-10-25 and 2026-11-09", line="L1")
    b = _card(id="C2", thing="your furniture", fact="has no recorded arrival", line="L1")
    prompt = say.prompt_text()
    assert say.check_line("Your furniture was due between 2026-10-25 and 2026-11-09, and no arrival is recorded.",
                          [a, b], prompt)[0] == []
    assert say.check_line("Your furniture was due by 2026-11-09, and no arrival is recorded.", [a, b], prompt)[0]


def test_say_writes_one_line_for_cards_that_share_an_id(monkeypatch) -> None:
    a = _card(id="C1", thing="your furniture", fact="was due between 2026-10-25 and 2026-11-09", line="L1")
    b = _card(id="C2", thing="your furniture", fact="has no recorded arrival", line="L1")
    c = say.pair_card(BY_ID["P11"])
    monkeypatch.setattr(say, "complete", lambda m, **kw:
                        "L1\tYour furniture was due between 2026-10-25 and 2026-11-09, and no arrival is recorded.\n"
                        f"P11\t{BY_ID['P11']['line']}")
    report = say.say([a, b, c], workers=1)
    assert list(report["lines"]) == ["L1", "P11"] and report["how"] == {"L1": "model", "P11": "model"}


def test_the_script_line_of_a_failed_group_holds_each_card(monkeypatch) -> None:
    a = _card(id="C1", thing="your furniture", fact="was due between 2026-10-25 and 2026-11-09", line="L1")
    b = _card(id="C2", thing="your furniture", fact="has no recorded arrival", line="L1")
    monkeypatch.setattr(say, "complete", lambda m, **kw: "L1\tYour furniture arrived.")
    report = say.say([a, b], workers=1)
    assert report["how"] == {"L1": "script"}
    assert report["lines"]["L1"] == ("Your furniture was due between 2026-10-25 and 2026-11-09. "
                                     "Your furniture has no recorded arrival.")
