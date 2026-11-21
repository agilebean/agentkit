"""RULES.md rule 2: every phrase the user called robotic is caught or declared.

common_sense.md inventories each wording correction. A row whose rejection cell
says "robotic" is either found by the shared marker list (robot_markers.tsv, run
by scripts/wording_lint.py) or named below as a writer's pass: a one-off
sentence, a heading style or a layout that no expression can find again. A new
robotic row in neither place fails this test, so the marker row is written in
the turn the correction arrives (classes 6 and 18 of the 2026-11-21 session
harvest: flagged phrases that reached the inventory but never the checker).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("wording_lint", ROOT / "scripts" / "wording_lint.py")
assert _spec and _spec.loader
wording = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wording)

SECTIONS = ("## The wording instances", "## What the user had to call common sense")

# The flagged cell of each robotic row the checker cannot find again, verbatim.
WRITERS_PASS = {
    'Every summary line and section opener an instruction ("Stop oral naproxen ...", "Start daily isometric holds now ...", "Swim without the pull ...")',
    'noun-stack headings: "Learning over polish", "Content and delivery", "Fixed scope"',
    '"the routine of someone living alone who wants to keep one"',
    'robotic wording recurring',
    'note structure around decisions',
    'swim note tone',
    '"what is a commitment sold to you as a feeling? no idea"; "which card?"; "what drift?"',
    'shorthand options in a question',
    'subheaders and clauses',
    '"each one produces what the next uses"; "blocked/stays open"',
    '"one surprise"',
    'the whole tickets and passes answer, many tables and fragments piled on one screen',
    '"Fraud requires intent and €240 is not a referral"',
    '"The address does not route a report; the self-certification does"',
    '"The tier and the NAV scaling are out of the way"',
    '"The cost of that gap is written in their help page"',
    "\"so the session only reaches tomorrow's set\"",
    '"That window is narrow, and it picks the agent out of the list"',
    "\"The end state is the goal's\"",
    '"The task side is not left with only the verb + object"',
    'the "no" clause after a dash ("no ... you can only aim at it"); "it follows"; "its steps are its own steps"',
    '"scores the same as a blank page"',
    '"You gave it 8.5 hours, lunch into night, and took no exit."',
    'a five-column table of components ("credential table", "injected plugin"), with "falsified" and "layer"',
    '"that ends it", "wrong paths", "a picture built on a file", "wording settles it", "words the same failure"',
    'the swim entry after two trims: "not the kick", "the elbow takes the pull", "no crossover", "threshold times a little slower"',
    '"a PDF that is one revision behind the sheet is the failure this whole pass keeps hitting"',
    '"not an act you choose"',
}


def robotic_rows() -> list[tuple[int, str]]:
    """(line number, flagged cell) of every inventory row rejected as robotic."""
    rows, section = [], None
    for lineno, line in enumerate((ROOT / "common_sense.md").read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## "):
            section = line.strip()
        if section not in SECTIONS or not line.startswith("| ") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.search(r"robotic", cells[2], re.I):
            rows.append((lineno, cells[1]))
    return rows


def caught(flagged: str, rules) -> bool:
    phrases = re.findall(r'"([^"]+)"', flagged) or [flagged]
    return any(wording.lint_text(p, rules) for p in phrases)


def test_the_inventory_has_robotic_rows() -> None:
    assert len(robotic_rows()) >= 50


def test_every_robotic_phrase_is_a_marker_or_a_declared_pass() -> None:
    rules = wording.load_robot_markers()
    missing = [f"common_sense.md:{n} {flagged}" for n, flagged in robotic_rows()
               if not caught(flagged, rules) and flagged not in WRITERS_PASS]
    assert not missing, (
        "a phrase the user called robotic is in neither robot_markers.tsv nor WRITERS_PASS; "
        "add a marker row with his repair as the fix, or declare it here:\n" + "\n".join(missing))


def test_the_pass_list_names_only_live_uncaught_rows() -> None:
    rules = wording.load_robot_markers()
    live = {flagged for _n, flagged in robotic_rows()}
    stale = sorted(WRITERS_PASS - live)
    now_caught = sorted(f for f in WRITERS_PASS & live if caught(f, rules))
    assert not stale, "WRITERS_PASS names rows no longer in common_sense.md: " + "; ".join(stale)
    assert not now_caught, "a marker now catches these; drop them from WRITERS_PASS: " + "; ".join(now_caught)


def test_the_new_markers_catch_their_phrases() -> None:
    rules = wording.load_robot_markers()
    for phrase in ("the walls stand next to your table", "the evidence trail",
                   "eight essays now pay nothing", "she filed it as undecided",
                   "Where the work shines"):
        assert wording.lint_text(phrase, rules), phrase
