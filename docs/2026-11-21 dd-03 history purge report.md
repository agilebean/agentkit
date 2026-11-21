stopped at T1.3: 5 hits in scripts or skill data

| What changed | Before | After | Evidence |
|---|---|---|---|
| the tree's hits against the private list | 90 hits in 18 files | 85 hits in 14 files | `python3 scripts/history_check.py --rules "$HQ/history replacements.txt" --tree "$PWD"` printed `history_check: 85 hits` |
| the runbook's test log | T1.3 named four files | T1.3 names the two transcript scripts that remain | `docs/dd-03 history purge runbook.md` holds the new row |
| the test workflow on `3687eef` | no result for this commit | success in 1 min | `gh run view 44888613914` reads `success` |

| Open item | Who decides | By when |
|---|---|---|
| `skills/date-analysis/scripts/md_turns.py` holds a rule 22 hit | the frontier session | 2026-11-28 |
| `skills/date-analysis/scripts/mw_transcript.py` holds rule 21 and rule 22 hits | the frontier session | 2026-11-28 |
