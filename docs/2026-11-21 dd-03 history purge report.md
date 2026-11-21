done: 17 of 17 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the tree's hits against the private list | 80 hits | 0 hits | `python3 scripts/history_check.py --rules "$HQ/history replacements.txt" --tree "$PWD"` printed `history_check: 0 hits` |
| the 12 Markdown and test files of T1.2 | terms of the list | the list's replacement in each | `git show --stat c6e9a70` reads `12 files changed` |
| the history of agentkit | 630 commits, 12 moved paths | 625 commits, 0 moved paths | `history_check.py --repo "$TMPDIR/dd03/agentkit.git"` printed `history_check: 0 hits` |
| `main` | `c6e9a70` | `432a82a` | `git ls-remote origin refs/heads/main` printed `432a82a` |
| the tags `v0.4.0` and `v0.4.1` | `2704392` and `90cf326` | `5229592` and `6d90e56` | `git ls-remote --tags` matches the mirror |
| the tests workflow on the new `main` | no result | success in 1 min | `gh run view 44889426298` reads `success` |
| the backup of the old history | none | a mirror under `~/Software/archive` | `git -C ~/Software/archive/agentkit-mirror-2026-11-21.git rev-parse main` printed `c6e9a70` |
| the shared checkout | HEAD `c6e9a70` | HEAD `432a82a` with the same status | `git -C "$AK" status --short` shows the same 2 untracked files |

| Open item | Who decides | By when |
|---|---|---|
| the old commit `c6e9a70` answers `503` on three requests | Chaehan | 2026-11-28 |
