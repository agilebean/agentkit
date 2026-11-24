"""tools/rules_ledger.py: RULES.md as a ledger of sentences, so a redesign can prove nothing was lost.

Phase 0 of docs/2026-11-23 rules redesign plan.md. Every sentence gets an identifier and a class;
`check` names each sentence that stands in none of the destination files.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("rules_ledger", ROOT / "tools" / "rules_ledger.py")
ledger = importlib.util.module_from_spec(_spec)
sys.modules["rules_ledger"] = ledger  # a dataclass resolves its module by name
_spec.loader.exec_module(ledger)

SOURCE = """# Agent Rules

A preamble sentence. A second one.

## Section

### 3. A rule title

A rule states behaviour, e.g. the cache stays. Chaehan, 2026-10-01: "keep it. and never drop it from the record." (failure 12).
Test: `scripts/x.py` flags it.

- A bullet sentence.

```
code line. another.
```

| a | b |
|---|---|

### 4. Next rule

A plain principle.
"""


def units():
    return ledger.split(SOURCE)


def test_the_split_is_lossless():
    joined = " ".join(u.text for u in units())
    assert ledger.norm(joined) == ledger.norm(SOURCE)


def test_identifiers_name_the_rule_or_the_section():
    ids = [u.id for u in units()]
    assert ids[0] == "S0.001"
    assert any(i.startswith("R3.") for i in ids) and any(i.startswith("R4.") for i in ids)
    assert len(ids) == len(set(ids))


def test_a_quote_with_an_inner_period_stays_in_one_unit():
    quoted = [u for u in units() if '"keep it. and never drop it from the record."' in u.text]
    assert len(quoted) == 1


def test_an_abbreviation_does_not_split_a_sentence():
    assert any(u.text.startswith("A rule states behaviour, e.g. the cache stays.") for u in units())


def test_a_code_block_and_a_table_are_one_unit_each():
    kinds = [u.kind for u in units()]
    assert kinds.count("code") == 1
    assert kinds.count("table") == 2


def test_the_classes():
    by_text = {u.text: u.kind for u in units()}
    assert by_text['Chaehan, 2026-10-01: "keep it. and never drop it from the record." (failure 12).'] == "incident"
    assert by_text["Test: `scripts/x.py` flags it."] == "test"
    assert by_text["A rule states behaviour, e.g. the cache stays."] == "example"
    assert by_text["A plain principle."] == "principle"


def test_an_incident_carries_its_dates_and_failure_numbers():
    u = next(u for u in units() if u.kind == "incident")
    assert u.dates == ["2026-10-01"] and u.failures == ["12"]


def test_check_names_a_sentence_missing_from_every_destination(tmp_path):
    rows = tmp_path / "ledger.tsv"
    ledger.write(units(), rows)
    rules = tmp_path / "RULES.md"
    register = tmp_path / "failures.md"
    rules.write_text(SOURCE.replace("A plain principle.", ""), encoding="utf-8")
    register.write_text("nothing here", encoding="utf-8")
    missing = ledger.check(ledger.read(rows), [rules, register])
    assert [u.text for u in missing] == ["A plain principle."]
    register.write_text("Moved: A plain principle.", encoding="utf-8")
    assert ledger.check(ledger.read(rows), [rules, register]) == []


def test_the_ledger_round_trips(tmp_path):
    rows = tmp_path / "ledger.tsv"
    ledger.write(units(), rows)
    assert [(u.id, u.kind, u.text) for u in ledger.read(rows)] == [(u.id, u.kind, u.text) for u in units()]


def test_quote_coverage_counts_quotes_found_in_the_register():
    found, total = ledger.quote_coverage(units(), 'He said "keep it. and never drop it from the record." once.')
    assert (found, total) == (1, 1)


RULES = """# Agent Rules

Preamble.

## Rules

### 5. Keep the cache

A rule sentence. Chaehan, 2026-10-01: "keep the cache warm at all times please" (failure 12). It broke the build.

Instance: `agent/failures.md` failure 12.

### 6. Quote the user

A principle first. On 2026-10-02 the agent paraphrased: "never paraphrase what i said to you". The paraphrase lost the point.
"""

REGISTER = """# failures

## Purpose & context

The register.

## Key learnings & principles

### Failure 12: Cache (x, 2026-10-01)

**Principle.** Keep it.

### Failure 13: Other

Text.
"""


def plan():
    return {u.text: (d, dest) for u, d, dest in ledger.evidence_plan(ledger.split(RULES), REGISTER)}


def test_evidence_plan_copies_from_the_first_incident_and_routes_a_single_cited_failure():
    p = plan()
    assert p["A rule sentence."] == ("rule", "")
    assert p['Chaehan, 2026-10-01: "keep the cache warm at all times please" (failure 12).'] == ("copied", "failure 12")
    assert p["It broke the build."] == ("copied", "failure 12")
    assert p["Instance: `agent/failures.md` failure 12."] == ("pointer", "")
    assert p["A principle first."] == ("rule", "")
    assert p["The paraphrase lost the point."] == ("copied", "evidence R6")


def test_evidence_plan_skips_a_sentence_the_register_holds():
    register = REGISTER.replace("Text.", "It broke the build.")
    rows = ledger.evidence_plan(ledger.split(RULES), register)
    assert {u.text: d for u, d, _ in rows}["It broke the build."] == "in register"


def test_apply_writes_every_copy_word_for_word_and_keeps_every_line():
    units = ledger.split(RULES)
    rows = ledger.evidence_plan(units, REGISTER)
    new = ledger.apply(units, rows, REGISTER, "T")
    for u, d, _ in rows:
        if d == "copied":
            assert ledger.norm(u.text) in ledger.norm(new)
    old_lines = [ln for ln in REGISTER.splitlines() if ln.strip()]
    it = iter(new.splitlines())
    assert all(any(ln == x for x in it) for ln in old_lines)
    assert ledger.quote_coverage(units, new) == (2, 2)


def test_apply_places_the_cited_paragraph_in_its_failure_and_the_rest_in_the_rule_entry():
    units = ledger.split(RULES)
    new = ledger.apply(units, ledger.evidence_plan(units, REGISTER), REGISTER, "T")
    f12 = new.split("### Failure 12:")[1].split("### Failure 13:")[0]
    assert "**From RULES.md rule 5**, RULES.md at `T`, line 9:" in f12 and "It broke the build." in f12
    section = new.split(ledger.EVIDENCE)[1].split(ledger.BEFORE)[0]
    assert "### Evidence for rule 6: Quote the user" in section
    assert "RULES.md at `T`, line 15." in section and "The paraphrase lost the point." in section
    assert new.index(ledger.EVIDENCE) < new.index(ledger.BEFORE)


def test_apply_twice_changes_nothing():
    units = ledger.split(RULES)
    once = ledger.apply(units, ledger.evidence_plan(units, REGISTER), REGISTER, "T")
    assert ledger.apply(units, ledger.evidence_plan(units, REGISTER), once, "T") == once


CARDS = """# Agent Rules

## Rules

### 7. Wrap the long rule

- **A bound head.** The rule states the
  behaviour. On 2026-10-03 the agent broke
  it twice. The behaviour holds next time.
- **Second bullet.** It stays (Chaehan, 2026-10-04: "keep the citation out of the rule text please").

Failure mode: 2026-10-05, a whole paragraph about one day. The user: "this paragraph is only the instance and goes away".

### 8. Next rule

A plain principle.
"""


def decide(*rows):
    return [dict(zip(ledger.TRIM_FIELDS, r)) for r in rows]


def cards_decisions():
    by_text = {u.text: u for u in ledger.split(CARDS)}
    def row(action, text, span="", reason="r"):
        return (by_text[text].id, action, span, reason, text)
    return decide(
        row("cut", "On 2026-10-03 the agent broke it twice."),
        row("strip", 'It stays (Chaehan, 2026-10-04: "keep the citation out of the rule text please").',
            span=' (Chaehan, 2026-10-04: "keep the citation out of the rule text please")'),
        row("cut", "Failure mode: 2026-10-05, a whole paragraph about one day."),
        row("cut", 'The user: "this paragraph is only the instance and goes away".'),
        ("R7", "append", "Evidence: failure 12.", "card", ""),
    )


def test_trim_cuts_inside_a_wrapped_bullet_and_keeps_its_other_lines():
    new = ledger.trim(CARDS, cards_decisions())
    assert "- **A bound head.** The rule states the\n  behaviour. The behaviour holds next time.\n" in new
    assert "On 2026-10-03" not in new


def test_trim_strips_only_the_span():
    new = ledger.trim(CARDS, cards_decisions())
    assert "- **Second bullet.** It stays.\n" in new


def test_trim_removes_a_paragraph_cut_whole_with_one_blank_line():
    new = ledger.trim(CARDS, cards_decisions())
    assert "Failure mode" not in new and "\n\n\n" not in new


def test_trim_appends_the_card_line_at_the_rule_end():
    new = ledger.trim(CARDS, cards_decisions())
    assert "time.\n- **Second bullet.** It stays.\n\nEvidence: failure 12.\n\n### 8. Next rule" in new


def test_trim_refuses_a_decision_made_for_other_text():
    rows = cards_decisions()
    rows[0]["text"] = "On 2026-10-03 the agent broke it once."
    try:
        ledger.trim(CARDS, rows)
    except ValueError as e:
        assert "not this unit" in str(e)
    else:
        raise AssertionError("the trim ran on a stale decision")


def test_trim_refuses_to_orphan_a_bullet():
    head = next(u for u in ledger.split(CARDS) if u.text == "- **A bound head.**")
    try:
        ledger.trim(CARDS, decide((head.id, "cut", "", "r", head.text)))
    except ValueError as e:
        assert "first sentence" in str(e)
    else:
        raise AssertionError("the bullet lost its marker")


def test_trim_cuts_the_first_sentence_of_a_plain_paragraph():
    first = next(u for u in ledger.split(CARDS) if u.text.startswith("Failure mode: 2026-10-05"))
    new = ledger.trim(CARDS, decide((first.id, "cut", "", "r", first.text)))
    assert '\nThe user: "this paragraph is only the instance and goes away".\n' in new


def test_to_register_copies_a_cut_unit_the_register_lacks_and_the_check_passes():
    units, rows = ledger.split(CARDS), cards_decisions()
    register = ledger.to_register(units, rows, REGISTER, "T")
    assert "### Evidence for rule 7: Wrap the long rule" in register
    assert ledger.trim_check(units, rows, ledger.trim(CARDS, rows), register) == []


def test_trim_check_names_a_kept_sentence_that_left_and_a_cut_one_the_register_lacks():
    units, rows = ledger.split(CARDS), cards_decisions()
    damaged = ledger.trim(CARDS, rows).replace("The behaviour holds next time.", "")
    problems = ledger.trim_check(units, rows, damaged, REGISTER)
    assert any("is kept but" in p for p in problems)
    assert any("is cut but" in p for p in problems)


def test_evidence_plan_reads_a_card_line_as_a_pointer():
    trimmed = ledger.trim(CARDS, cards_decisions())
    rows = {u.text: d for u, d, _ in ledger.evidence_plan(ledger.split(trimmed), REGISTER)}
    assert rows["Evidence: failure 12."] == "pointer"


def test_review_strikes_the_cut_text_adds_the_card_and_folds_the_rest():
    page = ledger.review(CARDS, ledger.trim(CARDS, cards_decisions()), ["7", "8"], "Batch T")
    rule7 = page.split("<h2>Rule 7")[1].split("<h2>Rule 8")[0]
    assert "<del>On 2026-10-03 the agent broke\n  it twice. </del>The behaviour holds next time." in rule7
    assert "<ins>Evidence: failure 12.</ins>" in rule7
    assert "<summary>2 unchanged paragraphs</summary>" in page.split("<h2>Rule 8")[1]
