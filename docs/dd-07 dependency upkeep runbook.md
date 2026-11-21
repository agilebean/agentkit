# DD-07 dependency and security upkeep, run as a test-first delivery

Task DD-07 of the [DeepSeek delegation plan](<deepseek delegation plan.md>): every dependency that a known advisory names is upgraded to its fixed version in the environment of agentkit, email-digest, invoice-admin and local-chat, with their tests green. Written 2026-11-21 by Claude Opus 5.5; DeepSeek V4.1 Flash runs it in opencode under the runbook skill (`skills/runbook/SKILL.md`).

Board: `docs/deepseek delegation plan.md`, task DD-07. Report: `docs/2026-11-21 dd-07 dependency upkeep report.md`.

State: not started.
Resume: run the *Resume checks* below and continue at the first test whose row in the *Test log* is not `pass`.

## Delivery rules

- Work in the folder `/private/tmp/dd07`; create it with `mkdir -p /private/tmp/dd07`. The auditor lives there: `python3 -m venv /private/tmp/dd07/pa && /private/tmp/dd07/pa/bin/pip install -q pip-audit`.
- One environment at a time, in the order of the stories. Before any upgrade in an environment, save its versions: `/Users/chaehan/Software/miniforge3/envs/<env>/bin/python -m pip list --format=freeze > /private/tmp/dd07/<env>-before.txt`. That file is the rollback: `.../bin/python -m pip install "<name>==<version from it>"`.
- Install with that environment's own pip, `/Users/chaehan/Software/miniforge3/envs/<env>/bin/python -m pip install -U ...`, never with `mamba install` and never into another environment.
- In the repositories you change only the dependency floors named in T6.1, this runbook's *State* line and *Test log*, the DD-07 row of the board (the claim only), and the report. Stage each file by its name, and leave every file `git status --short` shows that this runbook does not list.
- An advisory with no released fix (an empty fix version in the audit) stays open, and the report names it so.
- Other sessions use the socrates environment while you work, so Story 1 runs last.

## What exists today (measured 2026-11-21)

| Environment | Serves | Tests, all green on 2026-11-21 | Packages with an advisory |
|---|---|---|---|
| `email-digest` | `~/Software/Prototypes/email-digest` | `mamba run -n email-digest python -m pytest -q` in the repository: 315 passed (it downloads a model from huggingface.co) | 16: aiohttp, anyio, certifi, cryptography, filelock, fsspec, httplib2, multidict, oauthlib, pip, pyasn1, sentence-transformers, setuptools, torch, transformers, urllib3 |
| `invoice-admin` | `~/Software/Prototypes/invoice-admin` | `mamba run -n invoice-admin python -m pytest -q`: 225 passed, 5 skipped | 14: aiohttp, bleach, certifi, cryptography, filelock, httplib2, lxml, multidict, oauthlib, pip, pyasn1, pypdf, setuptools, urllib3 |
| `localai` | `~/Software/Prototypes/local-chat`, which has no test file | the smoke check of T4.1 | 10: anyio, certifi, filelock, fsspec, msgpack, pip, setuptools, torch, transformers, urllib3 |
| `socrates` | agentkit and the socrates repository | agentkit: `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q $(git ls-files 'tests/*test_*.py')`: 606 passed; socrates: `mamba run -n socrates python -m pytest -q --ignore=.claude` in its folder: 202 passed | 20: aiohttp, anyio, brotli, certifi, cryptography, filelock, fsspec, httplib2, idna, msgpack, multidict, oauthlib, pillow, pip, pyasn1, pypdf, setuptools, thrift, transformers, urllib3 |

The audit command for one environment, which prints JSON whose `dependencies[].vulns[]` hold each advisory's `id` and `fix_versions`:

```bash
SP=$(/Users/chaehan/Software/miniforge3/envs/<env>/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
/private/tmp/dd07/pa/bin/pip-audit --path "$SP" --format json --progress-spinner off > /private/tmp/dd07/<env>-<before|after>.json
```

The target version of a package is the highest of its advisories' fix versions. Several targets are a new major version (cryptography 48 to 50, pillow 12 to 13, oauthlib 3 to 4, filelock 3 to 4), so a red test after an upgrade is expected and handled by T2.2.

Direct dependencies with an advisory, whose floors the repositories raise in T6.1: `sentence-transformers` in email-digest (`pyproject.toml` and `environment.yml`), `pypdf` in invoice-admin (`pyproject.toml`). Every other package with an advisory is transitive and changes only in the environment.

## Story 0: the baseline

- [ ] T0.1 Given the four environments, when each is saved to `<env>-before.txt` and audited to `<env>-before.json`, then the four JSON files exist and the number of packages with an advisory is 16, 14, 10 and 20, or the report's first change row states the new numbers.

## Story 2: email-digest

- [ ] T2.1 Given `email-digest-before.json`, when every package with a released fix is installed at its target in one call, `python -m pip install -U "aiohttp>=3.14.4" ...`, then the repository's tests print `315 passed` or more and no `failed`.
- [ ] T2.2 Given a red test in T2.1, when the packages with a major-version target are put back to their `-before.txt` version one at a time, each followed by the tests, then the first one whose rollback turns the tests green stays at its old version as an open item with the failing test's name, and every other package keeps its target. Two rollbacks in a row that leave the same tests red stop the story.
- [ ] T2.3 Given T2.1 or T2.2, when the environment is audited to `email-digest-after.json`, then every remaining advisory is one without a released fix or one of T2.2's open items.

## Story 3: invoice-admin

- [ ] T3.1 to T3.3 as T2.1 to T2.3, with the environment `invoice-admin`, its tests (`225 passed, 5 skipped` or more passed) and the files `invoice-admin-*.json`.

## Story 4: local-chat, which has no tests

- [ ] T4.1 Given `localai`, when its packages with a released fix are installed at their targets, then this smoke check prints `ok` and nothing else, and the audit to `localai-after.json` keeps only advisories without a released fix:

  ```bash
  cd ~/Software/Prototypes/local-chat
  /Users/chaehan/Software/miniforge3/envs/localai/bin/python -c "import mlx, mlx_lm, numpy, rich, soundfile, sounddevice; print('ok')"
  /Users/chaehan/Software/miniforge3/envs/localai/bin/python -m py_compile $(git ls-files '*.py') && echo compiled
  ```

  A failure of the smoke check rolls back as T2.2 does.

## Story 1: the socrates environment, last

- [ ] T1.1 to T1.3 as T2.1 to T2.3, with the environment `socrates`, and both suites of its row green (agentkit `606 passed` or more, socrates `202 passed` or more).

## Story 6: the floors, commits and the report

- [ ] T6.1 Given T2 and T3 green, when email-digest's `pyproject.toml` and `environment.yml` read `sentence-transformers>=5.6.0` and invoice-admin's `pyproject.toml` reads `pypdf>=6.21.4` (or the target the audit gave, if higher), then each repository's tests stay green, and a commit per repository, `DD-07: <package> floor at its fixed version`, is pushed to its `main`.
- [ ] T6.2 Given T6.1, when the workflow of each pushed repository finishes (`gh run list -R agilebean/<repo> --limit 1 --json conclusion,headSha,databaseId`, waited for in the foreground), then each shows `success` for the pushed commit, or the report names the failure as an open item.
- [ ] T6.3 Given all stories, when the report is written in the form of the runbook skill, then `python3 scripts/report_check.py "docs/2026-11-21 dd-07 dependency upkeep report.md"` prints `report_check: PASS`. The table of changes has one row per environment with its advisory counts before and after, and one row per floor; each advisory left open with a released fix is an open item with its failing test.

## When to stop

- Two rollbacks in a row in one environment that leave the same tests red.
- A step that would install into an environment this runbook does not name, change a file the delivery rules do not list, or push with a red test.
- pip that cannot resolve a target: the package stays at its version as an open item with pip's error line, and the story goes on.

## Resume checks

| Check | Reads | Means |
|---|---|---|
| `ls /private/tmp/dd07/*-before.txt /private/tmp/dd07/*-after.json` | the files that exist | Story 0 and the stories with an `-after.json` are done |
| `git -C ~/Software/Prototypes/<repo> log --oneline -3 --grep DD-07` | a floor commit | T6.1 done for that repository |
| `ls "docs/2026-11-21 dd-07 dependency upkeep report.md"` | the file exists | T6.3 begun |

## Test log

| ID | Date | Result | Evidence |
|---|---|---|---|
| T0.1 | 2026-11-21 | pass | `pip-audit --path ... --format json` over the four environments: 16, 14, 10 and 20 packages with an advisory, 4 `-before.json` files written |
