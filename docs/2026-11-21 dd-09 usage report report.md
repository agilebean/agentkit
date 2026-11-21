stopped at T2.1: 225 socrates runs where the runbook expects 542, and no session from 2026-11-12 to 2026-11-14

| What changed | Before | After | Evidence |
|---|---|---|---|
| `scripts/usage_report.py` and `tests/test_usage_report.py` | 2 untracked files | committed as `ca82a5d` and pushed | `pytest -q tests/test_usage_report.py` printed `5 passed` |
| the tests workflow on `ca82a5d` | none | success after 36s | `gh run view 44904361050` reads `"conclusion":"success"` |
| the month's table in socrates | written with 110 runs | removed, 3 days absent from the database | `ls "docs/2026-11 deepseek usage.md"` in socrates prints nothing |
| socrates runs in the plan's window | 542 runs in the plan | 225 runs measured | `python3 scripts/usage_report.py --since 2026-10-01 --until "2026-11-20 23:08:25"` printed `\| socrates \| 225 \| 1 \| 0 \| 37.35 \|` |
| runs in the other repositories | 45 runs in the plan | 37 runs measured | that run's rows for `swim`, `email-digest`, `invoice-admin`, `other` and `virtualfriend` hold `22`, `8`, `3`, `2` and `2` runs |
| DeepSeek cost in October | $56.72 in the plan | $40.52 measured | `--month 2026-10` printed `\| Total \| 168 \| 2 \| 0 \| 40.52 \|` |
| commits in swim | 47 commits in the plan | 40 commits in the runbook's window, 47 commits over the plan's 60 days | `git -C ~/Software/Prototypes/swim log --since=2026-09-21 --until=2026-11-20 --format=%H` printed 47 lines against 40 from `--since=2026-10-01` |
| commits in email-digest, invoice-admin and local-chat | 23 commits in the plan | 21 commits in the runbook's window, 23 commits over the plan's 60 days | `git -C ~/Software/Prototypes/invoice-admin log --since=2026-09-21 --until=2026-11-20 --format=%H` printed 9 lines against 7 from `--since=2026-10-01` |
| the window of the plan's commit column | 2026-09-21 to 2026-11-20 | 9 days earlier than the runbook's window | `git -C ~/Software/Prototypes/swim log --since=2026-09-21` printed 47 lines, so the plan's figures fit its own 60 days |
| runs, probes and cost of November | 602 runs, 127 probes and $8.17 in the plan | 110 runs, 3 probes and $2.26 measured | `--month 2026-11` printed `\| Total \| 106 \| 1 \| 3 \| 2.26 \|` |

| Open item | Who decides | By when |
|---|---|---|
| the sessions of 2026-11-12 to 2026-11-14 missing from the database | Chaehan | 2026-11-24 |
| T2.1's expected figures against a database of 400 sessions | the frontier session | 2026-11-24 |
| T2.1's commit figures, which fit the plan's 60 days and not its own window | the frontier session | 2026-11-24 |
| the plan's 602 runs, 127 probes and $8.17 against 110 runs, 3 probes and $2.26 measured | the frontier session | 2026-11-24 |
| the month's table in socrates, withheld until the loose sessions are explained | Chaehan | 2026-11-24 |
| the monthly schedule, which only Chaehan can set up | Chaehan | 2026-11-28 |
| the DD-09 row on the board after this stop | the dispatcher | 2026-11-21 |
