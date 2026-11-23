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
    assert "**From RULES.md rule 5**, tag `T`, line 9:" in f12 and "It broke the build." in f12
    section = new.split(ledger.EVIDENCE)[1].split(ledger.BEFORE)[0]
    assert "### Evidence for rule 6: Quote the user" in section
    assert "Tag `T`, RULES.md line 15." in section and "The paraphrase lost the point." in section
    assert new.index(ledger.EVIDENCE) < new.index(ledger.BEFORE)


def test_apply_twice_changes_nothing():
    units = ledger.split(RULES)
    once = ledger.apply(units, ledger.evidence_plan(units, REGISTER), REGISTER, "T")
    assert ledger.apply(units, ledger.evidence_plan(units, REGISTER), once, "T") == once
