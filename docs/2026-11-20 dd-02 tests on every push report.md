done: 12 of 12 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the red test in `tests/test_en_to_hanji.py` | `1 failed` | `0 failed` | `mamba run -n socrates python -m pytest -q tests/test_en_to_hanji.py` printed `8 passed` |
| the 14 socrates tests in `tests/test_note_build.py` | `14 failed` without socrates | `14 skipped` without socrates | `pytest -q -rs tests/test_note_build.py` printed `42 passed, 14 skipped` |
| the `local_port` marker in `pyproject.toml` | `0 markers` registered | `2 tests` have the marker | `pytest -q -m local_port --collect-only` listed the `test_attaches_with_resolved_driver` and bridge tests |
| the pdf CLI tests in `tests/pdf/test_cli.py` | `4 failed` on a bare `PATH` | `0 failed` on a bare `PATH` | the `env -i` venv run printed `540 passed, 28 skipped` |
| the workflow `.github/workflows/tests.yml` | no workflow file | one workflow on every push | `yaml.safe_load` on the file printed `parsed` |
| the run on `main` | `4 failed` in run `44754080168` | `success` in run `44757340752` | `gh run list --branch main --json conclusion,headSha,databaseId` showed `"conclusion":"success"` for `e290af9` |
| the probe run on `dd-02-red-probe` | no probe run | `failure` in run `44757514076` | `gh run view 44757514076 --log-failed` named `test_red_probe` with `1 failed, 525 passed, 43 skipped` |
| the probe branch `dd-02-red-probe` | on origin and locally | absent from both | `git ls-remote origin dd-02-red-probe` printed nothing |

| Open item | Who decides | By when |
|---|---|---|
| the board's DD-02 status after this report | the frontier session | 2026-11-27 |
