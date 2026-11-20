stopped at T5.1: the run on main printed 4 failed and 521 passed, `markitdown not found on PATH`

| What changed | Before | After | Evidence |
|---|---|---|---|
| the red test in `tests/test_en_to_hanji.py` | `1 failed` | `0 failed` | `NOTE_BUILD_SOCRATES=~ mamba run -n socrates python -m pytest -q tests/test_en_to_hanji.py` printed `8 passed` |
| the 14 socrates tests in `tests/test_note_build.py` | `14 failed` without socrates | `14 skipped` without socrates | `NOTE_BUILD_SOCRATES=$(mktemp -d) mamba run -n socrates python -m pytest -q -rs tests/test_note_build.py` printed `42 passed, 14 skipped` |
| the marker for a test that opens a port in `pyproject.toml` | `0 markers` registered | `2 tests` have `local_port` | `python -m pytest -q --strict-markers -m local_port --collect-only` listed `tests/test_browser.py::TestChromeDriverAttach::test_attaches_with_resolved_driver` and the bridge test |
| the workflow `.github/workflows/tests.yml` | no workflow file | one workflow file with `macos-latest` and `timeout-minutes: 15` | `python -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"` printed `parsed` |
| the suite as the runner runs it | `0 runs` on GitHub | `failure` in run `44754080168` on `2e9d2ca` | `gh run view 44754080168 --log-failed` printed `4 failed, 521 passed, 43 skipped` |

| Open item | Who decides | By when |
|---|---|---|
| whether `tests/pdf/test_cli.py` gets `markitdown` installed on the runner | the frontier session | 2026-11-27 |
| whether the probe of T5.2 and T5.3 runs after a green main | the frontier session | 2026-11-27 |
