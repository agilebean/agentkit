"""Shared test settings.

note_build.py asks a model, at each PASS, what literally happens in every line
of the note (step 4 of the 2026-11-17 wording build). No test may call a
model, so the check is off here; a test that covers it turns it on and stands
in for the model.

Two host conditions keep a test out of the Linux run: Hanji.app is a macOS app,
and the ENML converter and the wording data live in Chaehan's private socrates
checkout. Such a test carries the marker `macos` or `private`, and the workflow
deselects both (`-m "not macos and not private"`), so a skip line in a CI log
always means a skip nobody declared. On a machine that lacks the dependency the
marker skips its tests here, with its reason. `tests/test_ci_selection.py`
holds the rule.
"""
import os
import shutil
import time
from pathlib import Path

import pytest

# The runner is UTC, Chaehan's Mac is KST. The suite sees one zone everywhere,
# so a test that formats a timestamp cannot pass here and fail there (the
# usage-report export did, on 2026-11-21). A test that needs another zone sets it.
os.environ["TZ"] = "UTC"
if hasattr(time, "tzset"):
    time.tzset()

HANJI = "/Applications/Hanji.app/Contents/MacOS/hanji"
SOCRATES = Path(os.environ.get("NOTE_BUILD_SOCRATES") or Path.home() / "Software" / "Prototypes" / "socrates")
DATA = Path(os.environ.get("HUMAN_QUALITY_DATA") or SOCRATES / "docs" / "human quality" / "data")
DATA_TESTS = {"test_wording_eval", "test_say"}


def _host_missing(item) -> str | None:
    """The reason this machine cannot run the test; None when it can."""
    if item.get_closest_marker("macos"):
        binary = os.environ.get("HANJI_BIN") or shutil.which("hanji") or HANJI
        if not Path(binary).is_file():
            return "Hanji.app is not installed"
    if item.get_closest_marker("private"):
        if item.module.__name__ in DATA_TESTS:
            if not (DATA / "wording_cases.tsv").is_file() or not (DATA / "wording_pairs.tsv").is_file():
                return "the wording data is Chaehan's private data, kept in socrates"
        elif not (SOCRATES / "projects/evernote/src/enml.py").is_file():
            return "socrates's ENML converter is not checked out"
    return None


def pytest_runtest_setup(item):
    reason = _host_missing(item)
    if reason:
        pytest.skip(reason)


@pytest.fixture(autouse=True)
def _no_literal_check(monkeypatch):
    monkeypatch.setenv("NOTE_BUILD_LITERAL", "0")
