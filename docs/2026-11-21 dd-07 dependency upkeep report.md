done: 11 of 11 acceptance tests pass

| What changed | Before | After | Evidence |
|---|---|---|---|
| the `email-digest` environment | 16 advisories | 0 advisories and `315 passed` | `pip-audit --path $SP --format json` prints `No known vulnerabilities found` |
| the `invoice-admin` environment | 14 advisories | 0 advisories and `225 passed, 5 skipped` | `pip-audit --path $SP --format json` prints `No known vulnerabilities found` |
| the `localai` environment | 10 advisories | 0 advisories and smoke check `ok` | `pip-audit --path $SP --format json` prints `No known vulnerabilities found` |
| the `socrates` environment | 20 advisories | 0 advisories and `612 passed`, `202 passed` | `pip-audit --path $SP --format json` prints `No known vulnerabilities found` |
| the `sentence-transformers` floor in email-digest | `>=3.0.0` in two files | `>=5.6.0` | commit `76724d4` on `main` of `agilebean/email-digest` |
| the `pypdf` floor in invoice-admin | `>=5.0` | `>=6.21.4` | commit `528db65` on `main` of `agilebean/invoice-admin` |
| the email-digest test workflow on `76724d4` | none for this commit | success | `gh run list -R agilebean/email-digest --limit 1` reads `success` |
| the invoice-admin CI workflow on `528db65` | none for this commit | success | `gh run list -R agilebean/invoice-admin --limit 1` reads `success` |
| the agentkit test workflow on `21e0823` | none for this commit | success | `gh run list --commit 21e0823` reads `success` |

| Open item | Who decides | By when |
|---|---|---|
