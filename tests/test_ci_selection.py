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
import os
import re
import subprocess
import sys
import time
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


def test_the_suite_collects_without_the_private_checkout(tmp_path) -> None:
    """A test file reads its private data at import, and a collection error is red before any marker can skip it."""
    env = os.environ | {"NOTE_BUILD_SOCRATES": str(tmp_path / "socrates"),
                        "HUMAN_QUALITY_DATA": str(tmp_path / "data"),
                        "HANJI_BIN": str(tmp_path / "hanji")}
    run = subprocess.run([sys.executable, "-m", "pytest", "-q", "--collect-only", "--strict-markers",
                          "-p", "no:cacheprovider", "-m", "not macos and not private"],
                         cwd=ROOT, env=env, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout[-2000:] + run.stderr[-2000:]


def test_no_workflow_condition_reads_a_secret() -> None:
    """GitHub rejects `secrets` inside `if`, and the run it then records has no job at all (24cc538, 2026-11-21)."""
    offenders = [f"{p.name}:{line} reads a secret in an if; GitHub rejects the file and the run has no job"
                 for p in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
                 for line, text in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
                 if re.match(r"\s*if\s*:.*secrets\.", text)]
    assert offenders == [], "\n".join(offenders)


def test_the_suite_runs_in_one_timezone() -> None:
    """conftest pins UTC, the runner's zone, so a timestamp test cannot pass on the KST Mac and fail there."""
    assert time.strftime("%z") == "+0000", "tests/conftest.py must pin TZ=UTC before the suite runs"
