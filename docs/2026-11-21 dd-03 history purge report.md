stopped at T1.3: 5 hits in scripts or skill data

| What changed | Before | After | Evidence |
|---|---|---|---|
| the checker `scripts/history_check.py` | not present | counts a list's hits in a tree or a history, never printing a term | `python3 scripts/history_check.py --rules "$HQ/history replacements.txt" --tree "$PWD"` printed `history_check: 90 hits` |
| `tests/test_history_check.py` | not present | 5 tests over a two-commit repository of invented terms | `mamba run -n socrates python -m pytest -q tests/test_history_check.py` printed `5 passed` |
| the tree's hits against the private list | not measured | 90 hits in 18 committed files | the same check printed `history_check: 90 hits` with `exit=1` |
| the test workflow on the last commit | no result | success in 1 min | `gh run view 44888202841` reads `success` |
| the DD-19 row of the board | `ready` | `in progress, 2026-11-21, DeepSeek V4.1 Flash` | `git log -1 --format=%s 55907bf` reads `DD-19 claimed` |

| Open item | Who decides | By when |
|---|---|---|
| `scripts/instruction_lint.py` holds a rule 26 hit | the frontier session | 2026-11-28 |
| `scripts/memory_lint.py` holds a rule 26 hit | the frontier session | 2026-11-28 |
| `skills/life-overview/scripts/overview_gate.py` holds a rule 26 hit | the frontier session | 2026-11-28 |
| `skills/date-analysis/date_markers.tsv` holds rule 21 and rule 22 hits | the frontier session | 2026-11-28 |
