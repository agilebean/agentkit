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
