done: 6 of 6 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the sweep `scripts/repo_sweep.py` | absent | 162 lines that run six read-only git commands | `mamba run -n socrates python scripts/repo_sweep.py --help` prints `--out FILE` and `--days DAYS` |
| the test `tests/test_repo_sweep.py` | 3 failed | 3 passed | `pytest -q tests/test_repo_sweep.py` printed `3 passed in 0.74s` |
| the sweep of 2026-11-21 in socrates | no file | 10 repositories, 15 worktrees, 5 stale, 19 uncommitted files, 0 unpushed commits | `docs/2026-11-21 repository sweep.md` in socrates holds `15` worktree rows |
| agentkit's workflow for `49d3946` | none | success in 33 s | `gh run view 44861734494` reads `conclusion success` with `551 passed, 43 skipped` |
| the DD-08 row of the board | in progress by Claude Opus 5.5 | in progress by DeepSeek V4.1 Flash | commit `6ae7ba7` |

| Open item | Who decides | By when |
|---|---|---|
| the weekly schedule that runs the sweep | Chaehan | 2026-11-28 |
| the removal of the 5 stale worktrees, which this run never touches | Chaehan | 2026-11-28 |
