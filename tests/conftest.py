"""Shared test settings.

note_build.py asks a model, at each PASS, what literally happens in every line
of the note (step 4 of the 2026-11-17 wording build). No test may call a
model, so the check is off here; a test that covers it turns it on and stands
in for the model.
"""
import pytest


@pytest.fixture(autouse=True)
def _no_literal_check(monkeypatch):
    monkeypatch.setenv("NOTE_BUILD_LITERAL", "0")
