"""The CI selection rule.

Every Linux run until 2026-11-21 ended on the same 43 skips, so a planned gap
and a real one looked alike; the run that was red, 44864516426, read "2 failed,
552 passed, 43 skipped" and the two failures were tests reading the host's
platform. A test that cannot run on the runner now carries `macos` or
`private`, the workflow deselects both, and these tests keep a host skip from
coming back.
"""
from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
HOST_MARKERS = ("macos", "private")

# A skip that stays: a tool the runner may lack, named by the test itself.
ALLOWED_SKIPS = {"node is not installed"}


def _skips(path: Path) -> list[tuple[int, str]]:
    """The skip calls and skipif reasons of one test file, with their lines."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call):
            continue
        called = ast.unparse(node.func)
        if called in {"pytest.skip", "skip"} and node.args and isinstance(node.args[0], ast.Constant):
            found.append((node.lineno, node.args[0].value))
        elif called.endswith("mark.skipif"):
            for kw in node.keywords:
                if kw.arg == "reason" and isinstance(kw.value, ast.Constant):
                    found.append((node.lineno, kw.value.value))
    return found


def test_no_test_skips_for_a_condition_the_host_markers_cover() -> None:
    offenders = [f"{p.relative_to(ROOT)}:{line} skips for {reason!r}; mark the test macos or private"
                 for p in sorted(TESTS.rglob("test_*.py"))
                 for line, reason in _skips(p) if reason not in ALLOWED_SKIPS]
    assert offenders == [], "\n".join(offenders)


def test_the_workflow_selects_out_both_host_markers() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"""-m\s+["']not macos and not private["']""", workflow), workflow


def test_both_host_markers_are_registered() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    names = {m.split(":", 1)[0].strip() for m in config["tool"]["pytest"]["ini_options"]["markers"]}
    assert set(HOST_MARKERS) <= names, names


def test_a_host_without_the_dependency_skips_by_the_same_marker() -> None:
    conftest = (TESTS / "conftest.py").read_text(encoding="utf-8")
    for marker in HOST_MARKERS:
        assert f'get_closest_marker("{marker}")' in conftest, marker
