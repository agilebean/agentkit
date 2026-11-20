"""The decision test for a whole note (scripts/decision_eval.py), human quality plan HQ-01.

No test here calls a model: `complete` is replaced by a stub, and the gold rows and notes are invented.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("decision_eval", ROOT / "scripts" / "decision_eval.py")
dec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dec)

GOLD_TSV = """# an invented household, for the tests
id\tdecision\tdeadline\toptions\tdepends\tsource
G1\tRenew the boat licence at the harbour office\t2026-03-10\trenew / let it lapse\tthe summer sailing plan\tnotes.md:3
G2\tChoose a school for the autumn term\t2026-04-01\tthe village school / the city school\tthe move\tnotes.md:9
G3\tSell the old van\tnone\tnone\tnone\tnotes.md:12
G4\tBook the dentist check for the cracked molar\t2026-03-10\tnone\tnone\tnotes.md:15
G5\tPay the overdue water bill\t2026-02-20\tnone\tnone\tnotes.md:18
"""

NOTE = """# 2026-03-01 Spring Overview, version X: built by the card path

## Takeaway

- Your boat licence runs out on 2026-03-10: renew it at the harbour office or let it lapse.
- The school for the autumn term is still open, and the city school closes its list on 2026-04-01.

| Item | State |
| --- | --- |
| Van | for sale |

## Home

- You still want to sell the old van.
- The garden fence was mended on 2026-02-20.
"""

WHOLE = ("Renew the boat licence\t2026-03-10\trenew / let it lapse\t- Your boat licence runs out on 2026-03-10: renew it at "
         "the harbour office or let it lapse.\n"
         "Pick the school for the autumn term\t2026-04-02\tthe village school / the city school\t- The school for the autumn "
         "term is still open, and the city school closes its list on 2026-04-01.\n"
         "Sell the old van\tnone\tnone\t- You still want to sell the old van.\n"
         "Repaint the garden fence\tnone\tnone\t- The garden fence was mended on 2026-02-20.\n")
TAKEAWAY = ("Renew the boat licence or let it lapse\t2026-03-10\trenew / let it lapse\tYour boat licence runs out on "
            "2026-03-10: renew it at the harbour office or let it lapse.\n")


def _gold(tmp_path: Path) -> list[dict]:
    path = tmp_path / "gold.tsv"
    path.write_text(GOLD_TSV, encoding="utf-8")
    return dec.load_gold(path)


def _reader(calls: list[list[dict]], whole: str = WHOLE, tk: str = TAKEAWAY, same: set[tuple[str, str]] | None = None):
    """A stub for complete: the reading call answers from the text it gets, the judge from `same`."""
    def complete(messages, model=None, **kw):
        calls.append(messages)
        if messages[0]["content"] == dec.JUDGE_PROMPT:
            first, second = messages[1]["content"].split("\n\n", 1)
            key = (first.splitlines()[0].removeprefix("First: "), second.splitlines()[0].removeprefix("Second: "))
            return "same" if same and key in same else "different"
        return tk if messages[1]["content"].split("\n\n", 1)[1].startswith("## Takeaway") and "## Home" not in messages[1]["content"] else whole
    return complete


def test_the_gold_list_skips_comments_and_reads_none_as_no_deadline(tmp_path) -> None:
    gold = _gold(tmp_path)
    assert [g["id"] for g in gold] == ["G1", "G2", "G3", "G4", "G5"]
    assert gold[0]["deadline"] == "2026-03-10" and gold[2]["deadline"] is None and gold[2]["options"] == ""


def test_the_takeaway_runs_to_the_next_section_and_keeps_its_subsections() -> None:
    assert dec.takeaway(NOTE).splitlines()[0] == "## Takeaway"
    assert "## Home" not in dec.takeaway(NOTE) and "sell the old van" not in dec.takeaway(NOTE)
    summary = "# T\n\n## Summary\n\nOne line.\n\n### By group\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n\n## Stocks\n\nx\n"
    assert dec.lines_of(dec.takeaway(summary)) == ["One line.", "| a | b |", "| 1 | 2 |"]
    assert dec.takeaway("# T\n\n## Home\n\n- a\n") == ""


def test_a_reader_counts_bullets_and_table_rows_but_no_heading_or_rule() -> None:
    assert len(dec.lines_of(dec.takeaway(NOTE))) == 4


def test_the_reader_never_sees_the_title_that_names_the_build() -> None:
    assert "version X" not in dec.body(NOTE) and dec.body(NOTE).startswith("## Takeaway")


def test_the_answer_becomes_rows_and_a_header_or_chatter_is_skipped() -> None:
    text = "decision\tdeadline\toptions\tfirst line\nHere are the decisions:\n1. Sell the van\tbefore 2026-05-01\tnone\t- line\n"
    rows = dec.parse_rows(text)
    assert rows == [{"decision": "Sell the van", "deadline": "2026-05-01", "options": "", "line": "- line"}]
    assert dec.parse_rows("Sell the van | none | sell / keep | - line")[0]["options"] == "sell / keep"
    table = "| decision | deadline | options | first line |\n|---|---|---|---|\n---\t---\n| **Sell the van** | none | none | x |"
    assert [r["decision"] for r in dec.parse_rows(table)] == ["Sell the van"]


def test_a_copied_line_is_found_and_a_stranger_is_not() -> None:
    lines = dec.lines_of(dec.takeaway(NOTE))
    assert dec.locate("Your boat licence runs out on 2026-03-10", lines) == 0
    assert dec.locate("- The school for the autumn term is still open and the city school closes its list", lines) == 1
    assert dec.locate("The garden fence was mended", lines) is None


def test_shared_words_pair_one_gold_row_with_one_note_row(tmp_path) -> None:
    gold = _gold(tmp_path)
    rows = dec.parse_rows(WHOLE)
    pairs = dec.match_words(gold, rows)
    assert pairs == {0: 0, 1: 1, 2: 2}
    assert 3 not in pairs.values()


def test_the_judge_sees_one_pair_at_a_time_and_only_the_closest_rows(tmp_path, monkeypatch) -> None:
    gold = _gold(tmp_path)
    rows = dec.parse_rows(WHOLE)
    calls: list[list[dict]] = []
    same = {("Choose a school for the autumn term", "Pick the school for the autumn term")}
    monkeypatch.setattr(dec, "complete", _reader(calls, same=same))
    pairs, judged = dec.match_judge(gold, rows, None, candidates=2, workers=1)
    assert pairs == {1: 1}
    assert len(judged) == len(calls) == 2 * len(gold)
    assert ["G2", 1, "same"] in judged and all(j[2] in ("same", "different") for j in judged)
    assert all(len(c) == 2 and c[0]["content"] == dec.JUDGE_PROMPT for c in calls)
    assert all("Depends on: " in c[1]["content"].split("\n\n")[0] for c in calls)


def test_a_failed_judge_call_is_counted_as_failed_never_as_different(tmp_path, monkeypatch) -> None:
    gold = _gold(tmp_path)

    def complete(messages, model=None, **kw):
        if messages[0]["content"] == dec.JUDGE_PROMPT:
            raise RuntimeError("route down")
        return TAKEAWAY if "## Home" not in messages[1]["content"] else WHOLE
    monkeypatch.setattr(dec, "complete", complete)
    r = dec.evaluate(NOTE, gold, "2026-03-01", methods=("judge",), candidates=1)
    judged = r["by"]["judge"]["judged_whole"] + r["by"]["judge"]["judged_takeaway"]
    assert judged and all(j[2] == "failed" for j in judged)
    assert r["failed"] == len(judged) and r["by"]["judge"]["recall"] == 0


def test_a_rate_limit_refusal_waits_and_tries_again(monkeypatch) -> None:
    answers = iter([RuntimeError("HTTP 429: rate_limit_error"), RuntimeError("HTTP 429: rate_limit_error"), "same"])
    waits: list[float] = []

    def complete(messages, model=None, **kw):
        a = next(answers)
        if isinstance(a, Exception):
            raise a
        return a
    monkeypatch.setattr(dec, "complete", complete)
    monkeypatch.setattr(dec.time, "sleep", waits.append)
    assert dec._call([{"role": "user", "content": "x"}], None) == ("same", "")
    assert waits == [15, 30]


def test_one_run_reads_the_note_and_the_takeaway_in_fresh_calls(tmp_path, monkeypatch) -> None:
    gold = _gold(tmp_path)
    calls: list[list[dict]] = []
    monkeypatch.setattr(dec, "complete", _reader(calls))
    r = dec.evaluate(NOTE, gold, "2026-03-01", methods=("words",))
    reads = [c for c in calls if c[0]["content"] == dec.READ_PROMPT]
    assert len(reads) == 2 and all(len(c) == 2 for c in reads)
    assert reads[0][1]["content"].startswith("The note is dated 2026-03-01.\n\n## Takeaway")
    assert "## Home" in reads[0][1]["content"] and "## Home" not in reads[1][1]["content"]
    m = r["by"]["words"]
    assert (m["recall"], m["takeaway"], m["gold"]) == (3, 1, 5)
    assert (m["due"], m["due_in_takeaway"]) == (3, 1)
    assert m["invented"] == ["Repaint the garden fence"]
    assert m["wrong_deadline"] == [["G2", "2026-04-02", "2026-04-01"]] and m["no_deadline"] == []
    assert m["soonest"] == {"G1": 1, "G4": "absent"}
    assert "recall 3 of 5, Takeaway 1 of 5 (due within 30 days 1 of 3)" in dec.summary(m)


def test_the_soonest_decision_is_the_next_one_due_and_the_oldest_when_all_have_passed() -> None:
    gold = [{"id": "A", "deadline": "2026-02-20"}, {"id": "B", "deadline": "2026-03-10"}, {"id": "C", "deadline": None}]
    assert dec.soonest(gold, "2026-03-01") == [1]
    assert dec.soonest(gold, "2026-04-01") == [0]
    assert dec.soonest(gold, None) == [0]


def test_a_failed_call_gives_no_rows_and_says_why(monkeypatch) -> None:
    def broken(messages, model=None, **kw):
        raise RuntimeError("route down")
    monkeypatch.setattr(dec, "complete", broken)
    monkeypatch.setattr(dec.time, "sleep", lambda s: None)
    rows, raw, failed = dec.read("## Takeaway\n\n- x\n", None, None)
    assert rows == [] and failed and raw.startswith("no answer (route down")


def _pairs(tmp_path: Path, rejected_takeaway: str, control: bool = False) -> Path:
    (tmp_path / "gold.tsv").write_text(GOLD_TSV, encoding="utf-8")
    (tmp_path / "good.md").write_text(NOTE, encoding="utf-8")
    (tmp_path / "bad.md").write_text(NOTE.replace("## Takeaway", "## Takeaway\n\n" + rejected_takeaway, 1), encoding="utf-8")
    path = tmp_path / "pairs.tsv"
    rows = "pair\tdate\tpreferred\trejected\tgold\trole\nhome\t2026-03-01\tgood.md\tbad.md\tgold.tsv\tacceptance\n"
    if control:
        rows += "same\t2026-03-01\tgood.md\tgood.md\tgold.tsv\tcontrol\n"
    path.write_text(rows, encoding="utf-8")
    return path


def test_the_pairs_pass_only_when_the_preferred_build_leads_in_every_run(tmp_path, monkeypatch, capsys) -> None:
    def complete(messages, model=None, **kw):
        text = messages[1]["content"]
        if "## Home" in text:
            return WHOLE
        return "" if "Nothing is open." in text else TAKEAWAY
    monkeypatch.setattr(dec, "complete", complete)
    assert dec.main(["--pairs", str(_pairs(tmp_path, "Nothing is open.")), "--runs", "2", "--match", "words"]) == 0
    assert "Takeaway recall 1 of 5 against 0, preferred above" in capsys.readouterr().out
    assert dec.main(["--pairs", str(_pairs(tmp_path, "A tie.")), "--runs", "2", "--match", "words"]) == 1
    assert "tie" in capsys.readouterr().out


def test_a_control_pair_is_reported_but_never_decides_and_a_failed_call_makes_the_run_incomplete(
        tmp_path, monkeypatch, capsys) -> None:
    def complete(messages, model=None, **kw):
        text = messages[1]["content"]
        if "## Home" in text:
            return WHOLE
        return "" if "Nothing is open." in text else TAKEAWAY
    monkeypatch.setattr(dec, "complete", complete)
    assert dec.main(["--pairs", str(_pairs(tmp_path, "Nothing is open.", control=True)), "--runs", "1",
                     "--match", "words"]) == 0
    out = capsys.readouterr().out
    assert "control: the Takeaways are one text and must tie" in out and "separated: words 1 of 1" in out

    def broken(messages, model=None, **kw):
        if "Nothing is open." in messages[1]["content"]:
            raise RuntimeError("route down")
        return complete(messages, model)
    monkeypatch.setattr(dec, "complete", broken)
    assert dec.main(["--pairs", str(_pairs(tmp_path, "Nothing is open.")), "--runs", "1", "--match", "words"]) == 2
    assert "incomplete: 1 pair-runs had a failed call" in capsys.readouterr().out


def test_saved_reads_are_scored_again_when_a_preference_changes_with_no_call(tmp_path, monkeypatch, capsys) -> None:
    def complete(messages, model=None, **kw):
        text = messages[1]["content"]
        if "## Home" in text:
            return WHOLE
        return "" if "Nothing is open." in text else TAKEAWAY
    monkeypatch.setattr(dec, "complete", complete)
    pairs, saved = _pairs(tmp_path, "Nothing is open."), tmp_path / "runs.json"
    assert dec.main(["--pairs", str(pairs), "--runs", "2", "--match", "words", "--out", str(saved)]) == 0
    capsys.readouterr()

    def no_call(messages, model=None, **kw):
        raise AssertionError("a saved run makes no call")
    monkeypatch.setattr(dec, "complete", no_call)
    pairs.write_text(pairs.read_text(encoding="utf-8").replace("good.md\tbad.md", "bad.md\tgood.md"), encoding="utf-8")
    assert dec.main(["--pairs", str(pairs), "--from", str(saved), "--match", "words"]) == 1
    out = capsys.readouterr().out
    assert out.count("Takeaway recall 0 of 5 against 1, rejected above") == 2
