import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills" / "evernote" / "scripts" / "note_test.py"
_spec = importlib.util.spec_from_file_location("note_test", _p)
nt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nt)


def test_next_output_is_classified() -> None:
    assert nt.classify_next("Assembled x\n\nPASS. The note text is stamped. Write it")[0] == "pass"
    assert nt.classify_next("Ask Chaehan with the question tool\n- Maps and links\n") == ("ask", ["- Maps and links"])
    kind, lines = nt.classify_next("Fix new.tsv:\n- D2 summary line uses a contrast\n- D3 heading has 9 words\n")
    assert kind == "fix" and len(lines) == 2
    assert nt.classify_next("Step 2 of 3: labels.\n\n- not a failure\n") == ("step", [])


def test_two_rounds_without_progress_on_the_same_failure_are_stuck() -> None:
    r = nt.Rounds()
    for n in (2, 2):
        r.add(0, "fix", [f"- T12 8 list items at one level in 'Getting around'"] * n)
    assert r.stuck() is None
    r.add(0, "fix", ["- T12 9 list items at one level in 'Getting around'"] * 2)
    assert r.stuck()


def test_a_falling_count_or_a_new_failure_is_progress() -> None:
    r = nt.Rounds()
    r.add(0, "fix", ["- a", "- b", "- c"])
    r.add(0, "fix", ["- a", "- b"])
    r.add(0, "fix", ["- a", "- b"])
    assert r.stuck() is None
    r2 = nt.Rounds()
    for first in ("- new.tsv D1", "- titles.tsv 5", "- edits.tsv 3"):
        r2.add(0, "fix", [first])
    assert r2.stuck() is None
    r2.add(0, "step", [])
    assert r2.fixes == []


def test_a_spent_quota_is_a_provider_error() -> None:
    assert nt.PROVIDER_ERROR.search('{"type": "provider.quota", "message": "Go usage limit exceeded", "status": 429}')
    assert nt.PROVIDER_ERROR.search("Upstream request failed: Model is unavailable.")
    assert not nt.PROVIDER_ERROR.search("note_build.py: no heading contains 'Swim'")
